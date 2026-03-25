import requests
from bs4 import BeautifulSoup
from datetime import datetime

class DataScout:
    """
    🛡️ 初始情報偵察特工 (DataScout) - 廣域偵察升級版
    負責從 PTT, 鉅亨, Yahoo, 經濟日報 採集原始輿情。
    """
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.ptt_cookies = {'over18': '1'}
        self.last_source_status = {}

    def _set_source_status(self, source_key, success, error=None, count=0):
        self.last_source_status[source_key] = {
            'success': success,
            'error': error,
            'count': count
        }

    def get_ptt_stock(self, limit=10):
        url = "https://www.ptt.cc/bbs/Stock/index.html"
        articles = []
        try:
            print(f"[爬蟲] 嘗試連接 PTT Stock...")
            res = requests.get(url, headers=self.headers, cookies=self.ptt_cookies, timeout=5)
            soup = BeautifulSoup(res.text, 'html.parser')
            for item in soup.select('.r-ent')[:limit]:
                title_tag = item.select('.title a')
                if title_tag:
                    articles.append({
                        'title': title_tag[0].text.strip(), 
                        'url': "https://www.ptt.cc" + title_tag[0]['href'], 
                        'category': 'social',
                        'source': 'PTT Stock'
                    })
            print(f"[成功] PTT 獲取 {len(articles)} 條")
            self._set_source_status('ptt', True, count=len(articles))
            return articles
        except Exception as e: 
            print(f"[錯誤] PTT 失敗: {e}")
            self._set_source_status('ptt', False, error=str(e), count=0)
            return []

    def get_anue_news(self, limit=10):
        url = f"https://api.cnyes.com/media/api/v1/newslist/category/tw_stock?limit={limit}"
        try:
            print(f"[爬蟲] 嘗試連接 鉅亨網 (Anue)...")
            res = requests.get(url, headers=self.headers, timeout=10)
            raw = res.json()
            items = []
            
            # 新版 API: items.data 包含新聞列表
            items_data = raw.get('items', {})
            if isinstance(items_data, dict) and 'data' in items_data:
                items = items_data['data']
            elif isinstance(items_data, list):
                items = items_data
            
            out = [{
                'title': item['title'], 
                'url': f"https://news.cnyes.com/news/id/{item['newsId']}", 
                'category': 'news',
                'source': '鉅亨網 ANUE'
            } for item in items if 'title' in item]
            print(f"[成功] 鉅亨 獲取 {len(out)} 條")
            self._set_source_status('anue', True, count=len(out))
            return out
        except Exception as e:
            print(f"[錯誤] 鉅亨 失敗: {e}")
            self._set_source_status('anue', False, error=str(e), count=0)
            return []

    def get_yahoo_news(self, limit=10):
        """偵察 Yahoo 奇摩股市最新新聞"""
        url = "https://tw.stock.yahoo.com/news/"
        articles = []
        try:
            res = requests.get(url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # 嘗試多個可能的選擇器
            seen_titles = set()
            for a in soup.find_all('a', href=True):
                href = a['href']
                if '/news/' in str(href) or 'yahoo.com.tw' in str(href):
                    text = a.get_text(strip=True)
                    # 過濾太短或重複的標題
                    if len(text) > 15 and text not in seen_titles:
                        seen_titles.add(text)
                        full_url = href if href.startswith('http') else f"https://tw.stock.yahoo.com{href}"
                        articles.append({
                            'title': text,
                            'url': full_url,
                            'category': 'news',
                            'source': 'Yahoo 股市'
                        })
                        if len(articles) >= limit:
                            break
            
            print(f"[成功] Yahoo 獲取 {len(articles)} 條")
            self._set_source_status('yahoo', True, count=len(articles[:limit]))
            return articles[:limit]
        except Exception as e:
            print(f"[錯誤] Yahoo 失敗: {e}")
            self._set_source_status('yahoo', False, error=str(e), count=0)
            return []

    def get_udn_news(self, limit=10):
        """偵察 經濟日報 (UDN Money) 最新台股新聞"""
        url = "https://money.udn.com/money/category/5586/5607"
        articles = []
        try:
            res = requests.get(url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(res.text, 'html.parser')
            
            seen_titles = set()
            # UDN 新聞連結選擇器
            for a in soup.select('.story__content a, .headline a, article a'):
                href = a.get('href', '')
                text = a.get_text(strip=True)
                
                if len(text) > 15 and text not in seen_titles:
                    seen_titles.add(text)
                    full_url = href if href.startswith('http') else f"https://money.udn.com{href}"
                    articles.append({
                        'title': text,
                        'url': full_url,
                        'category': 'news',
                        'source': '經濟日報 UDN'
                    })
                    if len(articles) >= limit:
                        break
            
            print(f"[成功] UDN 獲取 {len(articles)} 條")
            self._set_source_status('udn', True, count=len(articles))
            return articles
        except Exception as e:
            print(f"[錯誤] UDN 失敗: {e}")
            self._set_source_status('udn', False, error=str(e), count=0)
            return []

    def fetch_all_news(self):
        """一鍵啟動全網域偵察計畫"""
        print("[START] 廣域偵察計畫啟動...")
        self.last_source_status = {}
        all_news = []
        all_news.extend(self.get_ptt_stock(6))
        all_news.extend(self.get_anue_news(8))
        all_news.extend(self.get_yahoo_news(6))
        all_news.extend(self.get_udn_news(6))
        print(f"[OK] 廣域偵察完畢：共獲取 {len(all_news)} 則跨平台情報。")
        return all_news

if __name__ == "__main__":
    scout = DataScout()
    news = scout.fetch_all_news()
    for n in news:
        print(f"[{n['source']}] {n['title']}")
