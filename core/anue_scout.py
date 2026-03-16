import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import time

class AnueScout:
    """
    專門偵察鉅亨網 (Anue) 財經新聞的機構情報員。
    它能抓取最新的台股新聞，標準化輸出標題、連結與日期，供 AI 腦部分析。
    """
    def __init__(self):
        self.base_url = "https://news.cnyes.com"
        # 鉅亨網台股新聞分類網址，這是我們主要的偵察戰線
        self.market_url = "https://news.cnyes.com/news/cat/tw_stock" 
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7'
        }

    def scrape_latest_news(self, limit=20):
        """
        抓取最新的鉅亨網台股新聞。
        :param limit: 抓取的文章數量上限（預設 20 則，對齊 Gemini 免費層級限制）
        :return: 包含標題、連結、來源、日期的標準化情報列表
        """
        recon_results = []
        print(f"📡 鉅亨偵察員：開始偵察鉅亨網最新台股新聞 (預計抓取 {limit} 則)...")

        try:
            response = requests.get(self.market_url, headers=self.headers, timeout=10)
            if response.status_code != 200:
                print(f"⚠️ 偵察失敗：無法存取鉅亨網 (狀態碼: {response.status_code})")
                return []

            # 使用 lxml 解析庫 (速度較快，若未安裝請 pip install lxml)
            soup = BeautifulSoup(response.text, 'lxml')

            # --- 1. 尋找新聞列表容器 ---
            # 鉅亨網的網頁結構經常變動，這裡使用一個較為robust的屬性選擇器
            # 我們尋找包含新聞連結的特定 <a> 標籤
            # 注意：這裡使用了一個常見的 class 名稱作為範例，若網頁結構改變需更新
            news_items = soup.select('a[class*="_1ZPy"]') 

            if not news_items:
                print("⚠️ 警告：無法在頁面上找到新聞項目。這通常意味著鉅亨網修改了網頁結構 (CSS Selector 需更新)。")
                return []

            count = 0
            for item in news_items:
                if count >= limit:
                    break

                # --- 2. 提取標題與連結 ---
                title = item.get('title') # 鉅亨網通常將完整標題放在 title 屬性中
                if not title:
                    # 如果 title 屬性不存在，嘗試抓取其內部的文本
                    title_element = item.select_one('h3') # 有時標題在 <h3> 裡
                    if title_element:
                        title = title_element.text.strip()
                    else:
                        title = item.text.strip() # 最後的手段

                href = item.get('href')
                if not href or not title:
                    continue

                # 補全完整的 URL
                link = self.base_url + href if href.startswith('/') else href

                # --- 3. 提取時間 (如果有) ---
                # 鉅亨網通常在列表頁有 <time> 標籤，包含 datetime 屬性
                time_element = item.select_one('time')
                date_str = ""
                if time_element:
                    # 嘗試獲取 ISO 格式的 datetime 屬性
                    date_str = time_element.get('datetime')
                    if not date_str:
                        date_str = time_element.text.strip()
                else:
                    # 如果找不到時間，預設為當下時間
                    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")

                # --- 4. 戰略封裝 (標準化輸出格式) ---
                recon_results.append({
                    'source': 'Anue',
                    'title': title,
                    'link': link,
                    'date': date_str,
                    # 可以選擇性地加入分類，例如從 URL 解析
                    'category': '台股'
                })
                count += 1

        except Exception as e:
            print(f"❌ 鉅亨偵察過程中發生嚴重錯誤：{e}")

        print(f"✅ 鉅亨偵察完成！成功抓取 {len(recon_results)} 則法人端情報。")
        return recon_results

if __name__ == "__main__":
    # 這是檔案直執行的測試區
    scout = AnueScout()
    # 測試抓取最新 5 則
    results = scout.scrape_latest_news(limit=5) 
    print("\n--- 測試抓取結果 ---")
    for res in results:
        print(f"[{res['source']}] {res['title']} ({res['date']})")
        # print(f"   Link: {res['link']}")