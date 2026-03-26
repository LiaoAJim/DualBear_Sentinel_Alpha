import json
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
from core.vix_scout import VIXScout

try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None

class QuantSentimentScout:
    """
    🛡️ 籌碼情報員 (QuantSentimentScout) - 官網真理對接版
    負責從 TWSE (交易所) 與可靠財經平台抓取真實量化指標。
    """
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.last_errors = {}
        self.last_attempts = {}
        self.last_margin_market = {}
        self.last_data_dates = {}  # 各指標的「資料所屬日期」（非採集時刻）
        self.xq_margin_codes = {
            "listed": "TSE.TW-FinanceMaintenRatio",
        }
        self.margin_xpaths = {
            "pscnet": {
                "listed": "/html/body/div[1]/div/div[1]/div[2]/div[2]/div/div[3]/div/div/div/div/div[2]/div/div/div[2]/div[2]/table/tbody/tr[2]/td[6]",
                "otc": "/html/body/div[1]/div/div[1]/div[2]/div[2]/div/div[3]/div/div/div/div/div[2]/div/div/div[2]/div[2]/table/tbody/tr[2]/td[6]",
            },
            "kgi": {
                "listed": "/html/body/div[1]/div/div[1]/div[2]/div[2]/div/div[3]/div/div/div/div/div[2]/div/div/div[2]/div[2]/table/tbody/tr[2]/td[6]",
                "otc": "/html/body/div[1]/div/div[1]/div[2]/div[2]/div/div[3]/div/div/div/div/div[2]/div/div/div[2]/div[2]/table/tbody/tr[2]/td[6]",
            }
        }

    def fetch_all_indicators(self):
        print("[START] 籌碼情報員：啟動「官網真理」採集程序...")
        self.last_errors = {}
        self.last_attempts = {}
        self.last_margin_market = {}
        self.last_data_dates = {}
        indicators = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M"),
            'margin_maintenance_ratio': None,
            'margin_maintenance_ratio_market': {
                'listed': None,
                'otc': None,
                'market': None,
                'source': None,
                'method': 'unavailable',
                'note': '尚未取得上市 / 上櫃明細，無法判定大盤融資維持率組成。'
            },
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
            '_attempts': {},
            # 各指標的原始資料日期（爬到的那筆資料是哪一天的）
            '_data_dates': {
                'vixtwn': None,
                'vixus': None,
                'margin_maintenance_ratio': None,
                'retail_long_short_ratio': None,
            }
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
                # 唯一來源：透過 win32com 讀取 Excel 中 XQ DDE 即時值
                # 若 XQ 未開啟或 DDE 刷新失敗，直接顯示 XQ未開，不使用舊快照
                ('xq_excel_live', self._get_xq_excel_live),
            ]
        )
        indicators['_status']['margin_maintenance_ratio'] = 'success' if indicators['margin_maintenance_ratio'] is not None else 'failed'
        indicators['margin_maintenance_ratio_market'] = self._build_margin_market_breakdown(indicators)

        # 顯示用欄位：成功時用數值，失敗時明確告知 XQ 未開啟
        # （保留 margin_maintenance_ratio 為 None 給 sentinel 決策邏輯用）
        indicators['margin_display'] = (
            indicators['margin_maintenance_ratio']
            if indicators['margin_maintenance_ratio'] is not None
            else 'XQ未開'
        )

        indicators['retail_long_short_ratio'], indicators['_sources']['retail_long_short_ratio'] = self._fetch_with_fallback(
            'retail_long_short_ratio',
            [
                # 主要來源：台期所官方三大法人未平倉量，自行計算散戶部位，不依賴第三方網站。
                # 商品代碼 TMF = 微型臺指期貨（微台指）
                ('taifex_tmf_institutional_oi', self._get_taifex_retail_ls),
            ]
        )
        indicators['_status']['retail_long_short_ratio'] = 'success' if indicators['retail_long_short_ratio'] is not None else 'failed'
        indicators['_errors'] = dict(self.last_errors)
        indicators['_attempts'] = dict(self.last_attempts)
        # 填入各指標的資料日期（從各 fetcher 記錄的 last_data_dates 彙整）
        indicators['_data_dates'].update(self.last_data_dates)

        print("[OK] 全量化指標採集完成。")
        return indicators

    def _get_xq_excel_live(self):
        """
        XQ Excel DDE 即時橋接層（方案 B - 全自動版）：
        - 若 Excel 已開著且有目標活頁簿 → 直接讀取，不干擾使用者工作
        - 若 Excel 未開著 → 在背景靜默啟動 Excel、開啟橋接檔、
          等待 XQ DDE 刷新後讀取 B2，完成後靜默關閉
        前提：pywin32 已安裝、XQ 軟體正在運行。
        """
        import os
        import time

        excel_filename = "xq_margin_bridge_template.xlsx"
        excel_filepath = os.path.abspath(os.path.join("logs", excel_filename))

        # 嘗試 import pywin32，若未安裝則靜默跳過
        try:
            import win32com.client
        except ImportError:
            self.last_errors['margin_maintenance_ratio'] = (
                'pywin32 未安裝，跳過 XQ Excel 即時讀取。'
                '可執行 pip install pywin32 啟用此功能。'
            )
            return None

        # 確認橋接檔存在
        if not os.path.exists(excel_filepath):
            self.last_errors['margin_maintenance_ratio'] = (
                f'找不到 Excel 橋接檔: {excel_filepath}，'
                '請確認 logs/xq_margin_bridge_template.xlsx 存在。'
            )
            return None

        excel = None
        wb = None
        opened_by_us = False  # 記錄是否由本程式開啟，決定事後是否關閉

        try:
            # ── 步驟 1：嘗試接上已開啟的 Excel 實例 ──────────────────
            excel_already_open = False
            try:
                excel = win32com.client.GetActiveObject("Excel.Application")
                excel_already_open = True
            except Exception:
                pass  # Excel 未開啟，之後建立新實例

            if excel_already_open:
                # 在現有 Excel 中尋找目標活頁簿
                target_wb = None
                for i in range(1, excel.Workbooks.Count + 1):
                    wb_item = excel.Workbooks.Item(i)
                    if excel_filename.lower() in wb_item.Name.lower():
                        target_wb = wb_item
                        break

                if target_wb is not None:
                    # 目標活頁簿已開著，直接使用
                    wb = target_wb
                    opened_by_us = False
                    print("   ∟ [XQ Excel Live] 接上現有 Excel（檔案已開啟）")
                else:
                    # Excel 開著但目標活頁簿未開，在現有 Excel 裡開啟
                    wb = excel.Workbooks.Open(excel_filepath, UpdateLinks=True)
                    opened_by_us = True
                    print("   ∟ [XQ Excel Live] 在現有 Excel 中開啟橋接檔")
            else:
                # ── Excel 完全未開啟，建立靜默背景實例 ──────────────
                excel = win32com.client.Dispatch("Excel.Application")
                excel.Visible = False        # 背景靜默，不顯示 Excel 視窗
                excel.DisplayAlerts = False  # 關閉一切彈窗警示（如 DDE 連結警告）
                wb = excel.Workbooks.Open(excel_filepath, UpdateLinks=True)
                opened_by_us = True
                print("   ∟ [XQ Excel Live] 背景靜默啟動 Excel 並開啟橋接檔")

            # ── 步驟 2：等待 XQ DDE 刷新（逐秒重試，最多 5 次）────────
            ws = wb.Sheets(1)
            value = None
            max_retries = 5
            dde_wait_sec = 1.0

            for attempt in range(1, max_retries + 1):
                excel.Calculate()  # 強制觸發公式重算，催促 DDE 更新
                raw_value = ws.Range("B2").Value
                print(f"   ∟ [XQ Excel Live] DDE 刷新第 {attempt}/{max_retries} 次，B2 = {raw_value}")

                candidate = self._extract_first_float(str(raw_value)) if raw_value is not None else None
                if self._looks_like_margin_ratio(candidate):
                    value = candidate
                    break

                if attempt < max_retries:
                    time.sleep(dde_wait_sec)

            # ── 步驟 3：回傳結果 ─────────────────────────────────────
            if self._looks_like_margin_ratio(value):
                print(f"   ∟ [XQ Excel Live] 融資維持率 (B2): {value}%")
                self._record_margin_market_values(
                    'xq_excel_live',
                    market_values={"listed": value},
                    aggregate=value
                )
                # XQ DDE 為即時資料，記錄今日日期
                self.last_data_dates['margin_maintenance_ratio'] = datetime.now().strftime('%Y/%m/%d')
                return value

            self.last_errors['margin_maintenance_ratio'] = (
                f'XQ DDE 在 {max_retries} 次刷新後 B2 仍無合理融資維持率，'
                '請確認 XQ 軟體已連線且 DDE 公式正確。'
            )

        except Exception as e:
            self.last_errors['margin_maintenance_ratio'] = f'XQ Excel DDE 讀取失敗: {str(e)}'
            print(f"[FAIL] XQ Excel DDE 讀取失敗: {e}")

        finally:
            # ── 清理：若活頁簿是由本程式開啟的，讀完後靜默關閉 ──────
            try:
                if opened_by_us and wb is not None:
                    wb.Close(SaveChanges=False)
                # 若 Excel 是由本程式啟動且現在沒有其他活頁簿，整個退出
                if opened_by_us and excel is not None and excel.Workbooks.Count == 0:
                    excel.Quit()
            except Exception:
                pass  # 清理失敗時靜默處理，不影響主流程

        return None



    def _fetch_with_fallback(self, key, fetchers):
        attempts = []
        self.last_errors.pop(key, None)

        for source_name, fetcher in fetchers:
            value = fetcher()
            if value is not None:
                attempts.append({'source': source_name, 'status': 'success'})
                self.last_errors.pop(key, None)
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
                        # 檔名為 8 位日期（如 20260325），解析為 YYYY/MM/DD
                        if len(file_name) == 8:
                            self.last_data_dates['vixtwn'] = (
                                f"{file_name[:4]}/{file_name[4:6]}/{file_name[6:]}"
                            )
                        print(f"   ∟ [Taifex] 台灣 VIX: {value}")
                        return value

            for line in reversed(lines):
                value = self._extract_last_float(line)
                if value is not None:
                    if len(file_name) == 8:
                        self.last_data_dates['vixtwn'] = (
                            f"{file_name[:4]}/{file_name[4:6]}/{file_name[6:]}"
                        )
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
                raw_date = data['data'][0][0]  # 例: '114/03/25'（民國年）或 '2026/03/25'
                vix_val = float(data['data'][0][1])
                self.last_data_dates['vixtwn'] = raw_date
                print(f"   ∟ [TWSE] 恐慌指數 (VIX): {vix_val}")
                return vix_val
            self.last_errors['vixtwn'] = f"TWSE stat={data.get('stat', 'UNKNOWN')}"
        except Exception as e:
            self.last_errors['vixtwn'] = str(e)
            print(f"[FAIL] TWSE VIX 採集失敗: {e}")
        return None

    def _get_taifex_retail_ls(self):
        """
        從台期所官方資料計算「微型臺指期貨 (TMF)」散戶多空比。

        計算公式：
          散戶多單 = 全市場總未平倉量 - 三大法人多單
          散戶空單 = 全市場總未平倉量 - 三大法人空單
          散戶淨部位 = 散戶多單 - 散戶空單
          散戶多空比(%) = 散戶淨部位 / 全市場總未平倉量 × 100

        資料來源：
          1. 三大法人未平倉：https://www.taifex.com.tw/cht/3/futContractsDate (TMF)
          2. 全市場總未平倉：https://www.taifex.com.tw/cht/3/futDailyMarketReport (TMF)
        """
        from datetime import datetime, timedelta

        commodity_id = 'TMF'  # 微型臺指期貨

        # 逐日回溯：今天 → 昨天 → 前天（應對假日與盤中尚未更新的情況）
        today = datetime.now()
        dates_to_try = [
            today.strftime('%Y/%m/%d'),
            (today - timedelta(days=1)).strftime('%Y/%m/%d'),
            (today - timedelta(days=2)).strftime('%Y/%m/%d'),
            (today - timedelta(days=3)).strftime('%Y/%m/%d'),
        ]

        for query_date in dates_to_try:
            result = self._fetch_taifex_tmf_ls(query_date, commodity_id)
            if result is not None:
                return result

        self.last_errors['retail_long_short_ratio'] = (
            f'台期所 {commodity_id} 散戶多空比資料：'
            f'連續 {len(dates_to_try)} 個交易日均無法完整解析（法人或市場總量缺失）'
        )
        return None

    def _fetch_taifex_total_oi(self, query_date, commodity_id):
        """
        從「期貨每日交易行情」頁面獲取特定商品的全市場總未平倉量 (Total OI)。
        微台 (TMF) 專用。
        """
        url = 'https://www.taifex.com.tw/cht/3/futDailyMarketReport'
        try:
            # 優先使用 GET 以模擬瀏覽器首選跳轉，若無效再試 POST
            params = {
                'queryDate': query_date,
                'commodityId': commodity_id,
                'MarketCode': '0',
            }
            res = self.session.post(url, data=params, timeout=10)
            if res.status_code != 200:
                print(f"   ∟ [FAIL] market_report http status: {res.status_code}")
                return None
            
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # 尋找包含「小計」的最後一個表格橫列
            target_row = None
            rows = soup.find_all('tr')
            for row in reversed(rows):
                text = row.get_text(" ", strip=True)
                if '小計' in text or '合計' in text:
                    target_row = row
                    break
            
            if target_row:
                cells = [td.get_text(" ", strip=True).replace(',', '') for td in target_row.find_all(['td', 'th'])]
                # 未平倉契約量 (OI) 在微台指表格中通常是最後一個數字 (合計)
                for val_str in reversed(cells):
                    val = self._extract_first_float(val_str)
                    if val is not None and val > 100:
                        return val
            
            # 備援：若小計行解析失敗，嘗試尋找所有 TMF 資料列並加總
            # (在 Daily Market Report 中通常只有 TMF 相關列)
            print(f"   ∟ [WARN] TAIFEX {commodity_id} 小計行解析異常，嘗試備援方案")
            return None
        except Exception as e:
            print(f"   ∟ [FAIL] market_report error: {e}")
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
                            self._record_margin_market_values('wantgoo_margin_page', aggregate=val)
                            print(f"   ∟ [WantGoo] 融資維持率: {val}%")
                            return val

            # 備援：直接從頁面全文找「融資維持率」附近的百分比
            text = soup.get_text(" ", strip=True)
            val = self._extract_context_float(text, r'融資維持率', suffix='%')
            if val is not None:
                self._record_margin_market_values('wantgoo_margin_page', aggregate=val)
                print(f"   ∟ [WantGoo] 融資維持率(備援): {val}%")
                return val
            self.last_errors['margin_maintenance_ratio'] = '頁面可載入，但解析不到融資維持率'
        except Exception as e:
            self.last_errors['margin_maintenance_ratio'] = str(e)
            print(f"[FAIL] 玩股網融資維持率採集失敗: {e}")

        print("[WARN] 融資維持率未能解析，返回 None")
        return None


    def _fetch_taifex_tmf_ls(self, query_date, commodity_id):
        """
        整合三大法人資料與全市場總量，計算散戶多空比。
        """
        # 1. 獲取全市場總未平倉量 (Total Market OI)
        total_market_oi = self._fetch_taifex_total_oi(query_date, commodity_id)
        if total_market_oi is None:
            # 可能是該日無行情資料
            return None

        # 2. 獲獲三大法人未平倉量
        url = 'https://www.taifex.com.tw/cht/3/futContractsDate'
        try:
            params = {
                'queryDate': query_date,
                'commodityId': commodity_id,
            }
            res = self.session.post(url, data=params, timeout=12)
            if res.status_code != 200:
                return None

            soup = BeautifulSoup(res.text, 'html.parser')

            institutional_long = None
            institutional_short = None

            for table in soup.find_all('table'):
                for row in table.find_all('tr'):
                    cells = [
                        td.get_text(' ', strip=True).replace(',', '')
                        for td in row.find_all(['td', 'th'])
                    ]
                    if len(cells) < 4:
                        continue

                    # 檢查是否為「合計」列
                    row_text = row.get_text(" ", strip=True)
                    if '合計' in row_text:
                        # 在三大法人表格中:
                        # 身份別 | 多方口數 | 契約金額 | 空方口數 | 契約金額 | 淨額口數 ...
                        # 合計   | index 1 | index 2 | index 3 | index 4 | index 5
                        l_val = self._extract_first_float(cells[1])
                        s_val = self._extract_first_float(cells[3]) if len(cells) > 3 else None
                        if l_val is not None and s_val is not None:
                            institutional_long = l_val
                            institutional_short = s_val
                            break
                if institutional_long is not None:
                    break

            if institutional_long is not None and institutional_short is not None:
                # 3. 計算散戶部位
                # 在期貨市場，總多單 = 總空單 = 總未平倉量 (Total Market OI)
                retail_long = total_market_oi - institutional_long
                retail_short = total_market_oi - institutional_short
                retail_net = retail_long - retail_short
                
                ratio = round(retail_net / total_market_oi * 100, 2)
                
                print(
                    f'   ∟ [Taifex-TMF] 2024微台散戶多空比 ({query_date}): '
                    f'法人淨={institutional_long-institutional_short:,.0f} '
                    f'全市場OI={total_market_oi:,.0f} '
                    f'散戶淨={retail_net:,.0f} '
                    f'= {ratio:+.2f}%'
                )
                
                self.last_data_dates['retail_long_short_ratio'] = query_date
                return ratio

            return None

        except Exception as e:
            self.last_errors['retail_long_short_ratio'] = f'台期所 TMF 解析失敗: {str(e)}'
            print(f'[FAIL] 台期所散戶多空比採集失敗: {e}')
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

    def _get_psc_margin_playwright(self):
        """統一證券信用交易頁 Playwright 備援，處理 JS 動態渲染的表格"""
        url = "https://www.pscnet.com.tw/pscnetStock/menuContent.do?main_id=386032846c000000ccd145898ac293b6&sub_id=38d642081a00000099f12672f4cf7d6e"
        if sync_playwright is None:
            self.last_errors['margin_maintenance_ratio'] = 'Playwright 未安裝，無法啟用瀏覽器備援'
            return None

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, wait_until='networkidle', timeout=30000)

                market_values = self._extract_margin_market_with_xpaths(page, self.margin_xpaths["pscnet"])
                if market_values:
                    self._record_margin_market_values('pscnet_credit_playwright', market_values=market_values)
                value = self._choose_margin_market_value(market_values)
                if self._looks_like_margin_ratio(value):
                    browser.close()
                    print(f"   ∟ [PSC Playwright] 融資維持率: {value}%")
                    return value

                # 備援 0: 掃描可疑表格儲存格
                candidate_texts = page.locator("td.text-right.undefined, td[class*='text-right']").all_inner_texts()
                for text in candidate_texts:
                    value = self._extract_first_float(text)
                    if self._looks_like_margin_ratio(value):
                        browser.close()
                        print(f"   ∟ [PSC Playwright] 融資維持率(表格欄位): {value}%")
                        return value

                # 備援 1: 從渲染後的 HTML 找標籤附近數字
                content = page.content()
                soup = BeautifulSoup(content, 'html.parser')
                value = self._extract_margin_from_html(soup)
                if self._looks_like_margin_ratio(value):
                    browser.close()
                    print(f"   ∟ [PSC Playwright] 融資維持率(標籤): {value}%")
                    return value

                # 備援 2: 從整頁文字中找合理範圍的浮點數
                page_text = page.locator('body').inner_text()
                value = self._extract_margin_from_text(page_text)
                browser.close()
                if self._looks_like_margin_ratio(value):
                    print(f"   ∟ [PSC Playwright] 融資維持率(全文): {value}%")
                    return value

                self.last_errors['margin_maintenance_ratio'] = '統一證券頁已渲染，但仍解析不到融資維持率'
        except Exception as e:
            self.last_errors['margin_maintenance_ratio'] = f"統一證券 Playwright 備援失敗: {str(e)}"
        return None

    def _get_kgi_margin_snapshot(self):
        """凱基市場頁備援探測，目前僅做靜態頁與關鍵字探測"""
        url = "https://www.kgi.com.tw/zh-tw/product-market/stock-market-overview/tw-stock-market/tw-stock-market-detail?a=B658010E71E243C4A1D6B5F7BE914BDC&b=5D48401A7CE148CD8ABAC965F9B5AFBF"
        return self._probe_margin_snapshot_page(
            url,
            error_key='margin_maintenance_ratio',
            source_label='凱基頁面',
            api_hint='/api/client/KGISDropdownList/GetDropdownList 與頁面下拉選單相關，未見融資維持率 API'
        )

    def _get_kgi_margin_playwright(self):
        """凱基大盤動態頁 Playwright 備援，使用已知 XPath 抓融資相關欄位"""
        url = "https://www.kgi.com.tw/zh-tw/product-market/stock-market-overview/tw-stock-market/tw-stock-market-detail?a=B658010E71E243C4A1D6B5F7BE914BDC&b=5D48401A7CE148CD8ABAC965F9B5AFBF"

        if sync_playwright is None:
            self.last_errors['margin_maintenance_ratio'] = 'Playwright 未安裝，無法啟用凱基瀏覽器備援'
            return None

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, wait_until='networkidle', timeout=30000)

                market_values = self._extract_margin_market_with_xpaths(page, self.margin_xpaths["kgi"])
                if market_values:
                    self._record_margin_market_values('kgi_market_playwright', market_values=market_values)
                value = self._choose_margin_market_value(market_values)
                if self._looks_like_margin_ratio(value):
                    browser.close()
                    print(f"   ∟ [KGI Playwright] 融資維持率: {value}%")
                    return value

                # 備援 1: 搜尋表格內合理範圍的欄位
                candidate_texts = page.locator("table td, table th").all_inner_texts()
                for text in candidate_texts:
                    value = self._extract_first_float(text)
                    if self._looks_like_margin_ratio(value):
                        browser.close()
                        print(f"   ∟ [KGI Playwright] 融資維持率(表格): {value}%")
                        return value

                # 備援 2: 從渲染後 HTML 搜尋標籤附近數字
                content = page.content()
                soup = BeautifulSoup(content, 'html.parser')
                value = self._extract_margin_from_html(soup)
                if self._looks_like_margin_ratio(value):
                    browser.close()
                    print(f"   ∟ [KGI Playwright] 融資維持率(標籤): {value}%")
                    return value

                browser.close()
                self.last_errors['margin_maintenance_ratio'] = '凱基頁已渲染，但仍解析不到融資維持率'
        except Exception as e:
            self.last_errors['margin_maintenance_ratio'] = f"凱基 Playwright 備援失敗: {str(e)}"
        return None

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
                self._record_margin_market_values(source_label, aggregate=value)
                print(f"   ∟ [{source_label}] 融資維持率: {value}%")
                return value

            self.last_errors[error_key] = f"{source_label} 可載入，但未找到融資維持率或公開 API；目前僅確認 {api_hint}"
        except Exception as e:
            self.last_errors[error_key] = f"{source_label} {str(e)}"
        return None

    # _get_wantgoo_retail_ls 與 _get_macromicro_retail_ls 已移除。
    # 改用 _get_taifex_retail_ls (台期所官方) 直接計算，不再依賴第三方平台。

    def _get_us_vix(self):
        """從現有 VIXScout 取得美國 VIX"""
        try:
            scout = VIXScout()
            result = scout.fetch()
            if result.get("status") == "success" and result.get("value") is not None:
                vix_val = float(result["value"])
                # CBOE VIX 為即時資料，記錄今日日期
                self.last_data_dates['vixus'] = datetime.now().strftime('%Y/%m/%d')
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

    def _looks_like_margin_ratio(self, value):
        return value is not None and 100 <= value <= 250

    def _extract_margin_from_html(self, soup):
        label = soup.find(string=re.compile(r'融資維持率'))
        if label:
            parent = getattr(label, 'parent', None)
            if parent:
                sibling = parent.find_next_sibling()
                if sibling:
                    return self._extract_first_float(sibling.get_text(" ", strip=True))
                row = parent.find_parent('tr')
                if row:
                    cells = row.find_all(['td', 'th'])
                    for cell in cells:
                        value = self._extract_first_float(cell.get_text(" ", strip=True))
                        if self._looks_like_margin_ratio(value):
                            return value
        return None

    def _extract_margin_from_text(self, text):
        # 優先從"融資維持率"標籤附近提取（使用更多上下文保證精確）
        patterns = [
            r'融資維持率[：:\s]+(\d+(?:\.\d+)?)\s*%',  # 「融資維持率」冒號 數字
            r'融資維持率[\s]*(\d+(?:\.\d+)?)\s*%',      # 「融資維持率」直接連數字
            r'Maintenance\s+Ratio[：:\s]+(\d+(?:\.\d+)?)\s*%',  # 英文版本
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                value = float(match.group(1))
                if self._looks_like_margin_ratio(value):
                    return value
        
        # 備援：如果上述都失敗，才從全文中找第一個符合範圍的數字
        candidates = [float(match) for match in re.findall(r'\d+(?:\.\d+)?', text.replace(',', ''))]
        for value in candidates:
            if self._looks_like_margin_ratio(value):
                return value
        return None

    def _extract_margin_market_with_xpaths(self, page, xpath_map):
        market_values = {}
        for market_name, xpath in xpath_map.items():
            try:
                locator = page.locator(f"xpath={xpath}")
                if locator.count() == 0:
                    continue
                raw_text = locator.first.inner_text().strip()
                value = self._extract_first_float(raw_text)
                if self._looks_like_margin_ratio(value):
                    print(f"   ∟ [XPath:{market_name}] 命中 {raw_text}")
                    market_values[market_name] = value
            except Exception:
                continue
        return market_values

    def _choose_margin_market_value(self, market_values):
        if not market_values:
            return None
        # 目前尚未取得上市 / 上櫃融資餘額，因此先不做加權平均。
        # 若兩邊都有值且相同，直接採用；若不同，先取 listed 為主並保留細項。
        if market_values.get('listed') is not None:
            return market_values['listed']
        if market_values.get('otc') is not None:
            return market_values['otc']
        return None

    def _record_margin_market_values(self, source_name, market_values=None, aggregate=None):
        market_values = market_values or {}
        if market_values:
            self.last_margin_market['listed'] = market_values.get('listed')
            self.last_margin_market['otc'] = market_values.get('otc')
        if aggregate is not None:
            self.last_margin_market['aggregate'] = aggregate
        self.last_margin_market['source'] = source_name

    def _build_margin_market_breakdown(self, indicators):
        current = indicators.get('margin_maintenance_ratio')
        listed = self.last_margin_market.get('listed')
        otc = self.last_margin_market.get('otc')
        aggregate = self.last_margin_market.get('aggregate')
        source = self.last_margin_market.get('source')

        if aggregate is not None:
            return {
                'listed': listed,
                'otc': otc,
                'market': aggregate,
                'source': source,
                'method': 'source_aggregate',
                'note': '來源直接提供單一大盤融資維持率，未拆上市 / 上櫃權重。'
            }

        if listed is not None and otc is not None:
            if listed == otc:
                return {
                    'listed': listed,
                    'otc': otc,
                    'market': listed,
                    'source': source,
                    'method': 'markets_equal',
                    'note': '上市與上櫃數值相同，直接採用該值。'
                }
            return {
                'listed': listed,
                'otc': otc,
                'market': current,
                'source': source,
                'method': 'proxy_listed_priority',
                'note': '尚未取得上市 / 上櫃融資餘額，暫以上市值作為主顯示，不視為加權大盤值。'
            }
                
        if listed is not None:
            return {
                'listed': listed,
                'otc': otc,
                'market': listed,
                'source': source,
                'method': 'listed_only',
                'note': '僅取得上市融資維持率，無法計算加權大盤值。'
            }

        if otc is not None:
            return {
                'listed': listed,
                'otc': otc,
                'market': otc,
                'source': source,
                'method': 'otc_only',
                'note': '僅取得上櫃融資維持率，無法計算加權大盤值。'
            }

        return {
            'listed': None,
            'otc': None,
            'market': current,
            'source': source,
            'method': 'main_only',
            'note': '目前只有單一主值，尚未取得上市 / 上櫃明細。'
        }

if __name__ == "__main__":
    scout = QuantSentimentScout()
    print(scout.fetch_all_indicators())
