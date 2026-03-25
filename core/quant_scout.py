import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
from core.vix_scout import VIXScout

class QuantSentimentScout:
    """
    🛡️ 籌碼情報員 (QuantSentimentScout) - 官網真理對接版
    負責從 TWSE (交易所) 與可靠財經平台抓取真實量化指標。
    """
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.twse.com.tw/'
        }
        self.last_errors = {}
        self.last_attempts = {}

    def fetch_all_indicators(self):
        print("[START] 籌碼情報員：啟動「官網真理」採集程序...")
        self.last_errors = {}
        self.last_attempts = {}
        indicators = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M"),
            'margin_maintenance_ratio': None,
            'retail_long_short_ratio': None,
            'vixtwn': None,
            'vixus': None,
            '_sources': {},
            '_status': {
                'margin_maintenance_ratio': 'failed',
                'retail_long_short_ratio': 'failed',
                'vixtwn': 'failed',
                'vixus': 'failed'
            },
            '_errors': {},
            '_attempts': {}
        }

        indicators['vixtwn'], indicators['_sources']['vixtwn'] = self._fetch_with_fallback(
            'vixtwn',
            [
                ('taifex_vix_download', self._get_taifex_vix),
                ('twse_mi_vix_api', self._get_official_vix),
            ]
        )
        indicators['_status']['vixtwn'] = 'success' if indicators['vixtwn'] is not None else 'failed'

        indicators['vixus'], indicators['_sources']['vixus'] = self._fetch_with_fallback(
            'vixus',
            [('cboe_vix_scout', self._get_us_vix)]
        )
        indicators['_status']['vixus'] = 'success' if indicators['vixus'] is not None else 'failed'

        indicators['margin_maintenance_ratio'], indicators['_sources']['margin_maintenance_ratio'] = self._fetch_with_fallback(
            'margin_maintenance_ratio',
            [
                ('wantgoo_margin_page', self._get_wantgoo_margin),
                # 券商頁目前僅保留作為研究中的靜態備援探測，
                # 詳見 docs/quant_backup_sources.md。
                ('pscnet_credit_page', self._get_psc_margin_snapshot),
                ('kgi_market_overview_page', self._get_kgi_margin_snapshot),
            ]
        )
        indicators['_status']['margin_maintenance_ratio'] = 'success' if indicators['margin_maintenance_ratio'] is not None else 'failed'

        indicators['retail_long_short_ratio'], indicators['_sources']['retail_long_short_ratio'] = self._fetch_with_fallback(
            'retail_long_short_ratio',
            [
                ('wantgoo_retail_page', self._get_wantgoo_retail_ls),
                # MacroMicro 目前常被 Cloudflare 擋下，先保留為探測來源。
                ('macromicro_chart_page', self._get_macromicro_retail_ls),
            ]
        )
        indicators['_status']['retail_long_short_ratio'] = 'success' if indicators['retail_long_short_ratio'] is not None else 'failed'
        indicators['_errors'] = dict(self.last_errors)
        indicators['_attempts'] = dict(self.last_attempts)

        print("[OK] 全量化指標採集完成。")
        return indicators

    def _fetch_with_fallback(self, key, fetchers):
        attempts = []
        self.last_errors.pop(key, None)

        for source_name, fetcher in fetchers:
            value = fetcher()
            if value is not None:
                attempts.append({'source': source_name, 'status': 'success'})
                self.last_attempts[key] = attempts
                return value, source_name

            error_message = self.last_errors.get(key, '來源未提供錯誤訊息')
            attempts.append({
                'source': source_name,
                'status': 'failed',
                'error': error_message
            })

        self.last_attempts[key] = attempts
        return None, None

    def _get_taifex_vix(self):
        """從台期所 vixMinNew 清單頁與下載檔取得最新台灣 VIX"""
        list_url = "https://www.taifex.com.tw/cht/7/vixMinNew"
        try:
            res = requests.get(list_url, headers=self.headers, timeout=10)
            if res.status_code != 200:
                self.last_errors['vixtwn'] = f"Taifex list HTTP {res.status_code}"
                return None

            matches = re.findall(r"getVixData\?filesname=(\d{8})", res.text)
            if not matches:
                self.last_errors['vixtwn'] = "Taifex 清單頁找不到 VIX 檔案連結"
                return None

            file_name = matches[0]
            data_url = f"https://www.taifex.com.tw/cht/7/getVixData?filesname={file_name}"
            data_res = requests.get(data_url, headers=self.headers, timeout=10)
            if data_res.status_code != 200:
                self.last_errors['vixtwn'] = f"Taifex data HTTP {data_res.status_code}"
                return None

            decoded = self._decode_taifex_payload(data_res.content)
            lines = [line.strip() for line in decoded.splitlines() if line.strip()]
            if not lines:
                self.last_errors['vixtwn'] = "Taifex VIX 下載檔為空"
                return None

            for line in reversed(lines):
                if "Last 1 min AVG" in line:
                    value = self._extract_last_float(line)
                    if value is not None:
                        print(f"   ∟ [Taifex] 台灣 VIX: {value}")
                        return value

            for line in reversed(lines):
                value = self._extract_last_float(line)
                if value is not None:
                    print(f"   ∟ [Taifex] 台灣 VIX(末筆): {value}")
                    return value

            self.last_errors['vixtwn'] = "Taifex 下載檔存在，但解析不到 VIX 數值"
        except Exception as e:
            self.last_errors['vixtwn'] = str(e)
            print(f"[FAIL] Taifex VIX 採集失敗: {e}")
        return None

    def _get_official_vix(self):
        """從 TWSE 官網抓取 VIX 指數（台期所失敗時的備援）"""
        # TWSE RWD API
        url = "https://www.twse.com.tw/rwd/zh/indices/MI_VIX?response=json"
        try:
            res = requests.get(url, headers=self.headers, timeout=10)
            if res.status_code != 200:
                self.last_errors['vixtwn'] = f"HTTP {res.status_code}"
                return None
            data = res.json()
            if data['stat'] == 'OK' and 'data' in data:
                # 取得最新的一筆數據 [日期, 指數]
                vix_val = float(data['data'][0][1])
                print(f"   ∟ [TWSE] 恐慌指數 (VIX): {vix_val}")
                return vix_val
            self.last_errors['vixtwn'] = f"TWSE stat={data.get('stat', 'UNKNOWN')}"
        except Exception as e:
            self.last_errors['vixtwn'] = str(e)
            print(f"[FAIL] TWSE VIX 採集失敗: {e}")
        return None

    def _get_wantgoo_margin(self):
        """從玩股網採集大盤融資維持率"""
        url = "https://www.wantgoo.com/stock/astock/margin"
        try:
            res = requests.get(url, headers=self.headers, timeout=10)
            if res.status_code != 200:
                self.last_errors['margin_maintenance_ratio'] = f"HTTP {res.status_code}"
                return None
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # 優先用明確節點抓取
            label = soup.find(string=re.compile(r'融資維持率'))
            if label:
                parent = getattr(label, 'parent', None)
                if parent:
                    sibling = parent.find_next_sibling()
                    if sibling:
                        val = self._extract_first_float(sibling.get_text(" ", strip=True))
                        if val is not None:
                            print(f"   ∟ [WantGoo] 融資維持率: {val}%")
                            return val

            # 備援：直接從頁面全文找「融資維持率」附近的百分比
            text = soup.get_text(" ", strip=True)
            val = self._extract_context_float(text, r'融資維持率', suffix='%')
            if val is not None:
                print(f"   ∟ [WantGoo] 融資維持率(備援): {val}%")
                return val
            self.last_errors['margin_maintenance_ratio'] = '頁面可載入，但解析不到融資維持率'
        except Exception as e:
            self.last_errors['margin_maintenance_ratio'] = str(e)
            print(f"[FAIL] 玩股網融資維持率採集失敗: {e}")

        print("[WARN] 融資維持率未能解析，返回 None")
        return None

    def _get_wantgoo_retail_ls(self):
        """從玩股網採集小台指散戶多空比"""
        url = "https://www.wantgoo.com/futures/retail-indicator/wtm%26"
        try:
            res = requests.get(url, headers=self.headers, timeout=10)
            if res.status_code != 200:
                self.last_errors['retail_long_short_ratio'] = f"HTTP {res.status_code}"
                return None
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # 優先從表格第一列的最後一欄讀取最新散戶多空比
            table_row = soup.select_one('table tbody tr')
            if table_row:
                cells = [cell.get_text(" ", strip=True) for cell in table_row.find_all(['td', 'th'])]
                if cells:
                    val = self._extract_first_float(cells[-1])
                    if val is not None:
                        print(f"   ∟ [WantGoo] 散戶多空比: {val}")
                        return val

            # 備援：找標題附近的百分比
            text = soup.get_text(" ", strip=True)
            val = self._extract_context_float(text, r'散戶多空比', suffix='%')
            if val is not None:
                print(f"   ∟ [WantGoo] 散戶多空比(備援): {val}")
                return val
            self.last_errors['retail_long_short_ratio'] = '頁面可載入，但解析不到散戶多空比'
        except Exception as e:
            self.last_errors['retail_long_short_ratio'] = str(e)
            print(f"[FAIL] 玩股網散戶多空比採集失敗: {e}")

        print("[WARN] 散戶多空比未能解析，返回 None")
        return None

    def _get_psc_margin_snapshot(self):
        """統一證券信用交易頁的備援探測，目前僅做靜態頁與關鍵字探測"""
        url = "https://www.pscnet.com.tw/pscnetStock/menuContent.do?main_id=386032846c000000ccd145898ac293b6&sub_id=38d642081a00000099f12672f4cf7d6e"
        return self._probe_margin_snapshot_page(
            url,
            error_key='margin_maintenance_ratio',
            source_label='統一證券頁面',
            api_hint='/pscnetStock/getSearchByKeyword.do 僅為搜尋建議，未見融資維持率 API'
        )

    def _get_kgi_margin_snapshot(self):
        """凱基市場頁備援探測，目前僅做靜態頁與關鍵字探測"""
        url = "https://www.kgi.com.tw/zh-tw/product-market/stock-market-overview/tw-stock-market/tw-stock-market-detail?a=B658010E71E243C4A1D6B5F7BE914BDC&b=5D48401A7CE148CD8ABAC965F9B5AFBF"
        return self._probe_margin_snapshot_page(
            url,
            error_key='margin_maintenance_ratio',
            source_label='凱基頁面',
            api_hint='/api/client/KGISDropdownList/GetDropdownList 與頁面下拉選單相關，未見融資維持率 API'
        )

    def _probe_margin_snapshot_page(self, url, error_key, source_label, api_hint):
        try:
            res = requests.get(url, headers=self.headers, timeout=10)
            if res.status_code != 200:
                self.last_errors[error_key] = f"{source_label} HTTP {res.status_code}"
                return None

            soup = BeautifulSoup(res.text, 'html.parser')
            text = soup.get_text(" ", strip=True)
            value = self._extract_context_float(text, r'融資維持率', suffix='%')
            if value is not None:
                print(f"   ∟ [{source_label}] 融資維持率: {value}%")
                return value

            self.last_errors[error_key] = f"{source_label} 可載入，但未找到融資維持率或公開 API；目前僅確認 {api_hint}"
        except Exception as e:
            self.last_errors[error_key] = f"{source_label} {str(e)}"
        return None

    def _get_macromicro_retail_ls(self):
        """Macromicro 圖表備援探測，若遭 Cloudflare 阻擋則回報清楚原因"""
        url = "https://www.macromicro.me/charts/110457/tw-tmf-long-to-short-ratio-of-individual-player"
        try:
            res = requests.get(url, headers=self.headers, timeout=10)
            if res.status_code != 200:
                self.last_errors['retail_long_short_ratio'] = f"Macromicro HTTP {res.status_code}"
                return None

            text = BeautifulSoup(res.text, 'html.parser').get_text(" ", strip=True)
            value = self._extract_context_float(text, r'散戶.*多空比')
            if value is not None:
                print(f"   ∟ [Macromicro] 散戶多空比: {value}")
                return value

            if 'Just a moment' in res.text or 'cf-challenge' in res.text.lower():
                self.last_errors['retail_long_short_ratio'] = 'Macromicro 遭 Cloudflare 驗證阻擋'
            else:
                self.last_errors['retail_long_short_ratio'] = 'Macromicro 可載入，但解析不到散戶多空比'
        except Exception as e:
            self.last_errors['retail_long_short_ratio'] = str(e)
        return None

    def _get_us_vix(self):
        """從現有 VIXScout 取得美國 VIX"""
        try:
            scout = VIXScout()
            result = scout.fetch()
            if result.get("status") == "success" and result.get("value") is not None:
                vix_val = float(result["value"])
                print(f"   ∟ [CBOE] 美國 VIX: {vix_val}")
                return vix_val
            self.last_errors['vixus'] = result.get('message', '未知錯誤')
            print(f"[FAIL] 美國 VIX 採集失敗: {result.get('message', '未知錯誤')}")
        except Exception as e:
            self.last_errors['vixus'] = str(e)
            print(f"[FAIL] 美國 VIX 採集失敗: {e}")
        return None

    def _extract_first_float(self, text):
        """從文字中提取第一個浮點數"""
        if not text:
            return None
        match = re.search(r'-?\d+(?:\.\d+)?', text.replace(',', ''))
        if not match:
            return None
        return float(match.group(0))

    def _extract_context_float(self, text, keyword_pattern, suffix=''):
        """從關鍵字附近抓取第一個數值"""
        if not text:
            return None
        pattern = rf'{keyword_pattern}[^-\d]{{0,30}}(-?\d+(?:\.\d+)?)\s*{re.escape(suffix)}'
        match = re.search(pattern, text)
        if not match:
            return None
        return float(match.group(1))

    def _extract_last_float(self, text):
        """從文字中提取最後一個浮點數"""
        if not text:
            return None
        matches = re.findall(r'-?\d+(?:\.\d+)?', text.replace(',', ''))
        if not matches:
            return None
        return float(matches[-1])

    def _decode_taifex_payload(self, payload):
        """台期所下載檔常用 cp950，失敗再退回 utf-8"""
        for encoding in ('cp950', 'utf-8', 'big5'):
            try:
                return payload.decode(encoding)
            except Exception:
                continue
        return payload.decode('utf-8', errors='replace')

if __name__ == "__main__":
    scout = QuantSentimentScout()
    print(scout.fetch_all_indicators())
