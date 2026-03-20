import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

class PttStockScout:
    """
    專門偵察 PTT Stock 板（股板）的草根情緒偵察員。
    它能處理「過 18 歲」確認，抓取最新頁面的標題、連結與推文數（爆文指標）。
    """
    def __init__(self):
        self.base_url = "https://www.ptt.cc"
        self.board_url = "https://www.ptt.cc/bbs/Stock/index.html"
        # 關鍵：設定 cookie 以跳過「過 18 歲」確認頁面
        self.cookies = {'over18': '1'}
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def scrape_latest_posts(self, pages=2, min_pushes=10):
        """
        抓取最新幾頁的 PTT 股板文章。
        :param pages: 抓取的頁數（預設 2 頁，避免請求過於頻繁）
        :param min_pushes: 篩選的最低推文數（預設 10 推以上，過濾雜訊）
        :return: 包含標題、連結、推文數、日期的列表
        """
        recon_results = []
        current_url = self.board_url

        print(f"[START] PTT 偵察員：開始偵察 PTT Stock 板 (預計抓取 {pages} 頁)...")

        import time
        for page in range(pages):
            max_retries = 3
            response = None
            for retry in range(max_retries):
                try:
                    response = requests.get(current_url, cookies=self.cookies, headers=self.headers, timeout=15)
                    if response.status_code == 200:
                        break
                    print(f"[WARN] PTT 頁面存取異常 (狀態碼: {response.status_code})，第 {retry+1} 次重試...")
                except Exception as e:
                    print(f"[WARN] PTT 連線異常 ({e})，第 {retry+1} 次重試...")
                
                if retry < max_retries - 1:
                    time.sleep(5)
                else:
                    print("[FAIL] PTT 偵察失敗：已達最大重試次數。")
                    return recon_results
            
            try:
                soup = BeautifulSoup(response.text, 'lxml')
                
                # --- 1. 抓取文章列表 ---
                posts = soup.select('div.r-ent')
                
                for post in posts:
                    # 篩選掉已被刪除的文章 (沒有 <a> 標籤)
                    title_element = post.select_one('div.title a')
                    if not title_element:
                        continue

                    title = title_element.text.strip()
                    link = self.base_url + title_element['href']
                    author = post.select_one('div.author').text.strip()
                    date_str = post.select_one('div.date').text.strip() # 格式通常是 "12/31"
                    
                    # --- 2. 處理推文數 (nrec) ---
                    # 爆 = 100+ 推, 數字 = 推文數, X = 噓文, 空白 = 0
                    nrec_element = post.select_one('div.nrec')
                    nrec_text = nrec_element.text.strip() if nrec_element else "0"
                    
                    pushes = 0
                    is_boom = False
                    if nrec_text == "爆":
                        pushes = 100
                        is_boom = True
                    elif nrec_text.startswith('X'):
                        # 噓文通常不作為利多情報，視為負面或雜訊，設為負值或 0
                        pushes = 0 
                    elif nrec_text.isdigit():
                        pushes = int(nrec_text)
                    
                    # --- 3. 戰略篩選：只保留具備草根影響力的文章 ---
                    if pushes >= min_pushes or is_boom or "[公告]" in title:
                        # 將 PTT 的 "MM/DD" 轉為完整的日期格式 (假設為今年)
                        try:
                            current_year = datetime.now().year
                            formatted_date = f"{current_year}/{date_str}"
                        except:
                            formatted_date = date_str

                        # PTT 股板的分類通常在標題 [] 裡面
                        category_match = re.search(r'\[(.*?)\]', title)
                        category = category_match.group(1) if category_match else "其他"

                        recon_results.append({
                            'source': 'PTT Stock',
                            'title': title,
                            'link': link,
                            'author': author,
                            'pushes': pushes,
                            'is_boom': is_boom,
                            'date': formatted_date,
                            'category': category,
                            'raw_nrec': nrec_text
                        })

                # --- 4. 尋找「上一頁」的連結 ---
                # PTT 的分頁是倒序的，"index.html" 是最新頁，"index1234.html" 是舊頁
                paging_elements = soup.select('div.btn-group-pull-right a')
                prev_page_link = None
                for btn in paging_elements:
                    if "‹ 上頁" in btn.text:
                        prev_page_link = self.base_url + btn['href']
                        break
                
                if not prev_page_link:
                    break
                
                current_url = prev_page_link
                
                # 戰略防護：在分頁抓取之間暫停一下，避免被 PTT 鎖 IP
                time.sleep(2) 

            except Exception as e:
                print(f"[ERROR] 偵察過程中發生嚴重錯誤：{e}")
                break

        print(f"[OK] PTT 偵察完成！成功抓取 {len(recon_results)} 則具備草根影響力的情報。")
        return recon_results

if __name__ == "__main__":
    # 這是檔案直執行的測試區
    scout = PttStockScout()
    results = scout.scrape_latest_posts(pages=1, min_pushes=5) # 測試抓取 1 頁，5 推以上
    for res in results:
        print(f"[{res['raw_nrec']}] ({res['category']}) {res['title']} - {res['author']}")