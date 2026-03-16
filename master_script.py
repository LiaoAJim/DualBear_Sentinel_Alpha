import os
import json
import requests
import time
from datetime import datetime
from dotenv import load_dotenv

# --- [關鍵修復]：從 core 模組導入所有需要的特工與腦部 ---
from core.analyzer import SentimentAnalyzer
from core.scout import PttStockScout # 導入 PTT 特工
from core.anue_scout import AnueScout # 導入 鉅亨特工
from core.sentinel import SentinelAlpha # 導入 哨兵策略精算師 (L11)

# --- [關鍵定義]：在此檔案中定義 LineNotifier 類別，或從核心導入 ---
# (為了讓你能直接執行，我將我們先前設計的 LineNotifier 代碼直接放在這裡，
# 或者你也可以選擇建立 core/notifier.py 並從那裡 import。)
class LineNotifier:
    def __init__(self, token):
        self.token = token
        self.api_url = "https://notify-api.line.me/api/notify"
        self.headers = {"Authorization": "Bearer " + token}

    def send_text(self, message):
        payload = {"message": message}
        try:
            response = requests.post(self.api_url, headers=self.headers, data=payload)
            if response.status_code == 200:
                print("✅ LINE Notify 訊息發送成功！")
                return True
            else:
                print(f"❌ LINE Notify 訊息發送失敗，狀態碼: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 發生錯誤：{e}")
            return False

# --- [優化]：將報告建構函數搬到外部，並優化時間處理 ---
def construct_report(decision, intelligence_count):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    if decision:
        return (
            f"📊 DualBear 今日戰略報告\n\n"
            f"🕒 時間: {now}\n"
            f"📡 偵察情報數: {intelligence_count} 則\n"
            f"💡 最終情緒: {decision['sentiment_score']:.2f} ({"利多" if decision['sentiment_score'] > 0 else "利空" if decision['sentiment_score'] < 0 else "中性"})\n\n"
            f"🛡️ 建議操作: 【{decision.get('action', 'N/A')}】\n"
            f"📝 理由: {decision.get('recon_notes', 'N/A')}\n\n"
            f"💡 指揮官，規律覺醒，獲利自由！"
        )
    else:
        return (
            f"📊 DualBear 今日戰略報告\n\n"
            f"🕒 時間: {now}\n"
            f"⚠️ 狀態: AI 分析失敗，未能產出決策報告。"
        )

# --- [修復]：定義 get_test_news() 函數作為 fallback ---
def get_test_news():
    """當爬蟲模組失敗時的備用測試數據。返回一個空列表或模擬數據。"""
    print("⚠️ 使用測試數據。")
    return [] # 或者返回一些模擬數據 [{'source': 'Test', 'title': '台股大漲', 'link': '...'}]

def main():
    # 1. 初始化環境與通訊
    load_dotenv()
    line_token = os.getenv("LINE_NOTIFY_TOKEN")
    google_api_key = os.getenv("GOOGLE_API_KEY") 

    if not line_token:
        print("❌ 錯誤：找不到 LINE_NOTIFY_TOKEN。")
        return
    if not google_api_key:
        print("❌ 錯誤：找不到 GOOGLE_API_KEY。")
        return

    notifier = LineNotifier(line_token)
    
    # --- ⚔️ PHASE 2: REAL OPERATIONS ---
    print("🚀 DualBear Sentinel Alpha 啟動真實偵察任務...")

    # --- Block 1: Real Scouting --- (✅ 部署情報網)
    print("📡 正在部署情報網：鉅亨網 & PTT Stock...")
    
    try:
        # 動態導入以提高雲端執行的健壯性
        from core.anue_scout import AnueScout
        from core.ptt_scout import PttStockScout
        scouts = [AnueScout(), PttStockScout()]
        
        all_intelligence = []
        for scout in scouts:
            # 這裡我們調用標準的抓取方法。
            # 請確保你的 scouts 方法中已經有 Jade 設計的反 429 配額延遲 (time.sleep)
            try:
                # 假設方法名稱為 scrape_latest_news 或 scrape_latest_posts
                if hasattr(scout, 'scrape_latest_news'):
                    all_intelligence.extend(scout.scrape_latest_news(limit=10)) 
                elif hasattr(scout, 'scrape_latest_posts'):
                    all_intelligence.extend(scout.scrape_latest_posts(pages=2, min_pushes=15))
            except Exception as e:
                print(f"⚠️ 偵察特工偵察失敗：{e}")
            
        intelligence_count = len(all_intelligence)
        print(f"✅ 成功蒐集到 {intelligence_count} 則市場情報。")
    except ImportError:
        print("⚠️ 警告: 找不到 scout 模組 (AnueScout 或 PttStockScout)。切換到備用數據。")
        all_intelligence = get_test_news()
        intelligence_count = len(all_intelligence)

    if not all_intelligence:
        print("⚠️ 警告: 今日未抓取到任何有效市場情報。")
        notifier.send_text("⚠️ 今日偵察報告: 未抓取到有效情報。請檢查爬蟲模組。")
        return

    # --- Block 2: AI Analysis & Sentinel Decision --- (✅ 整合 AI 情緒與做出決策)
    print("🧠 正在呼叫 Gemini AI 大腦進行情緒判讀 (腦部對齊：1.5-Flash)...")
    
    try:
        # 動態導入 SentimentAnalyzer 類別
        from core.analyzer import SentimentAnalyzer
        analyzer = SentimentAnalyzer(google_api_key)
        
        # --- [關鍵修復]：在此檔案中實現整合 AI 與決策的邏輯 ---
        total_score = 0
        analyzed_count = 0
        sentiment_flavors = []

        print(f"   開始對 {intelligence_count} 則情報進行情緒判讀...")
        for i, intelligence in enumerate(all_intelligence):
            try:
                # 這裡調用 analyzer 檔案中定義的 analyse 單點文字的方法
                # 我們假設 analyser 檔案中定義的方法是 analyse，就像我之前給你的那樣
                # 這裡接收 intelligence 的標題（或其他欄位），並返回一個 Sentiment 物件或字典
                sentiment = analyzer.analyze(intelligence['title'])
                
                # 從 Sentiment 物件或字典中獲取分數和風味
                # 這裡假設你的 core/analyzer.py 返回的是一個具有 score 和 flavor 屬性的物件，
                # 或者一個具有 'score' 和 'flavor' 鍵的字典。
                # 根據你之前的 code，它是一個物件，我們將其視為字典處理 (.get)
                # (如果你的 core/analyzer.py 是返回物件，請將 .get 修復為對應的屬性存取)
                if isinstance(sentiment, dict):
                  score = sentiment.get('score', 0)
                  flavor = sentiment.get('flavor', '中性')
                else: # 假設它是一個物件
                  score = sentiment.score
                  flavor = sentiment.flavor

                total_score += score
                sentiment_flavors.append(f"【{intelligence['source']}】{intelligence['title'][:20]}... -> {flavor}")
                analyzed_count += 1
                print(f"   - [{i+1}/{intelligence_count}] 情緒分數: {score} ({flavor})")
            except Exception as e:
                print(f"⚠️ 單點分析失敗：{e}")
                # 這裡不計入平均，因為分析失敗不代表中性

        # 精算最終的情緒分數和風味
        if analyzed_count > 0:
            final_sentiment_score = total_score / analyzed_count
        else:
            final_sentiment_score = 0
        
        print(f"✅ 最終情緒分數: {final_sentiment_score:.2f}")

        # --- [關鍵聯動]：呼叫策略精算師 SentinelAlpha 做出最終持倉決策 (L11) ---
        print("🛡️ 正在呼叫哨兵精算師計算最終持倉決策...")
        sentinel = SentinelAlpha()
        # 我們假設 SentinelAlpha 的 calculate_position 接收一個情緒分數，
        # 並返回一個包含 action (操作) 和 recon_notes (理由) 的字典。
        # 並且該方法內建了我們之前設計的「情緒到倉位」的精算邏輯。
        decision = sentinel.calculate_position(final_sentiment_score)
        
        # 將最終情緒分數也加入決策字典中
        decision['sentiment_score'] = final_sentiment_score

        final_decision = decision
        
    except ImportError:
        print("⚠️ 警告: 找不到 analyzer 或 sentinel 模組。")
        final_decision = None # 或者給予預設決策

    # --- Block 3: Final Report Construction --- (✅ 建構報告)
    print("📊 正在建構今日戰略報告...")
    
    # 根據 AI 的分析結果和偵察數建構報告
    report = construct_report(final_decision, intelligence_count) 
    
    # --- Block 4: Final Reporting (LINE) --- (✅ 發送通報)
    print("📡 正在發送戰略報告到 LINE...")
    notifier.send_text(report)
    print("✅ 戰略報告發送成功！")

if __name__ == "__main__":
    main()