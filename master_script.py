import os
from dotenv import load_dotenv
from core.crawler import DataScout
from core.analyzer import SentimentEngine
from core.calculator import StrategyCalculator

# 載入 .env 檔案中的環境變數
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY") # 改讀 Google Key

def main():
    if not API_KEY or API_KEY == "your_gemini_api_key_...xxxx":
        print("❌ 錯誤：請在 .env 檔案中填入正確的 GOOGLE_API_KEY。")
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
    print(f"\n🎯 最終戰略建議：{msg}")

if __name__ == "__main__":
    main()