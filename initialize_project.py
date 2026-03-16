import os

def create_file(path, content):
    directory = os.path.dirname(path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
        
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip())
    print(f"✅ 已建立檔案: {path}")

# --- 1. 定義各模組內容 ---

crawler_code = """
import requests
from bs4 import BeautifulSoup

class DataScout:
    def __init__(self):
        self.headers = {'User-Agent': 'Mozilla/5.0'}
        self.ptt_cookies = {'over18': '1'}

    def get_ptt_stock(self, limit=10):
        url = "https://www.ptt.cc/bbs/Stock/index.html"
        articles = []
        try:
            res = requests.get(url, headers=self.headers, cookies=self.ptt_cookies)
            soup = BeautifulSoup(res.text, 'html.parser')
            for item in soup.select('.r-ent')[:limit]:
                title_tag = item.select('.title a')
                if title_tag:
                    articles.append({'title': title_tag[0].text.strip(), 'url': "https://www.ptt.cc" + title_tag[0]['href'], 'category': 'social'})
            return articles
        except: return []

    def get_anue_news(self, limit=10):
        url = f"https://api.cnyes.com/media/api/v1/newslist/category/tw_stock?limit={limit}"
        try:
            res = requests.get(url)
            return [{'title': item['title'], 'url': f"https://news.cnyes.com/news/id/{item['newsId']}", 'category': 'news'} for item in res.json()['items']['data']]
        except: return []
"""

analyzer_code = """
import json, requests

class SentimentEngine:
    def __init__(self, api_key):
        self.api_key = api_key
        self.url = "https://api.openai.com/v1/chat/completions"

    def analyze(self, title):
        prompt = f"分析台股標題情緒(含反串辨識): '{title}'。輸出JSON: {{'score': -1.0 to 1.0, 'flavor': '簡短分析'}}"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {"model": "gpt-4o-mini", "messages": [{"role": "user", "content": prompt}], "response_format": {"type": "json_object"}}
        try:
            res = requests.post(self.url, headers=headers, json=payload)
            return json.loads(res.json()['choices'][0]['message']['content'])
        except: return {"score": 0, "flavor": "分析失敗"}
"""

calculator_code = """
class StrategyCalculator:
    def __init__(self, weights={'news': 0.3, 'social': 0.5, 'macro': 0.2}):
        self.weights = weights

    def get_weighted_score(self, scores_list):
        if not scores_list: return 0
        total_w, final_s = 0, 0
        for item in scores_list:
            w = self.weights.get(item['category'], 0.1)
            final_s += item['score'] * w
            total_w += w
        return final_s / total_w if total_w > 0 else 0

    def generate_signal(self, score):
        if score > 0.7: return 0.1, "🔥 極度亢奮：建議減碼"
        if score < -0.7: return 1.0, "🚀 極度恐慌：建議重倉"
        return round((score+1)/2, 2), f"☕ 平穩期：建議持倉 {(score+1)*50:.0f}%"
"""

master_code = """
import os
from dotenv import load_dotenv
from core.crawler import DataScout
from core.analyzer import SentimentEngine
from core.calculator import StrategyCalculator

# 載入 .env 檔案中的環境變數
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")

def main():
    if not API_KEY or API_KEY == "your_openai_api_key_here":
        print("❌ 錯誤：請在 .env 檔案中填入正確的 OPENAI_API_KEY。")
        return
        
    scout = DataScout()
    engine = SentimentEngine(API_KEY)
    calc = StrategyCalculator()
    
    print("🚀 DualBear Sentinel Alpha 啟動偵察...")
    data = scout.get_anue_news(5) + scout.get_ptt_stock(5)
    
    results = []
    for item in data:
        res = engine.analyze(item['title'])
        results.append({'category': item['category'], 'score': res['score']})
        print(f"  - {item['title'][:20]}... [Score: {res['score']}]")
        
    final_score = calc.get_weighted_score(results)
    pos, msg = calc.generate_signal(final_score)
    print(f"\\n🎯 最終戰略建議：{msg}")

if __name__ == "__main__":
    main()
"""

dotenv_content = """
OPENAI_API_KEY=your_openai_api_key_here
LINE_NOTIFY_TOKEN=your_line_notify_token_here
"""

# --- 2. 執行建立任務 ---

print("🏗️ 開始建立 DualBear_Sentinel_Alpha 專案結構...")

create_file("core/crawler.py", crawler_code)
create_file("core/analyzer.py", analyzer_code)
create_file("core/calculator.py", calculator_code)
create_file("master_script.py", master_code)
create_file(".env", dotenv_content)
create_file("requirements.txt", "requests\nbeautifulsoup4\nyfinance\nopenai\npandas\npython-dotenv")

print("\n✨ 初始化完成！")
print("👉 下一步：")
print("1. 執行 'pip install -r requirements.txt'")
print("2. 開啟 '.env' 檔案並填入你的 API Key")
print("3. 執行 'python master_script.py'")