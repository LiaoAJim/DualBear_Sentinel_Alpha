import os
import json
import requests
import time
from datetime import datetime
from dotenv import load_dotenv

# --- [關鍵修復]：從 core 模組導入所有需要的特工與腦部 ---
from core.analyzer import SentimentAnalyzer
from core.scout import PttStockScout # 修正導入路徑
from core.anue_scout import AnueScout # 導入 鉅亨特工
from core.sentinel import SentinelAlpha # 導入 哨兵策略精算師 (L11)

# --- [關鍵定義]：在此檔案中定義 LineNotifier 類別，或從核心導入 ---
# (為了讓你能直接執行，我將我們先前設計的 LineNotifier 代碼直接放在這裡，
# 或者你也可以選擇建立 core/notifier.py 並從那裡 import。)
class LineNotifier:
    """
    雙熊 LINE 通知特工：支援 Messaging API Push 模式。
    """
    def __init__(self, token, user_id):
        self.token = token
        self.user_id = user_id
        self.api_url = "https://api.line.me/v2/bot/message/push"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }

    def send_text(self, message):
        data = {
            "to": self.user_id,
            "messages": [
                {
                    "type": "text",
                    "text": message
                }
            ]
        }
        try:
            response = requests.post(self.api_url, headers=self.headers, data=json.dumps(data))
            if response.status_code == 200:
                print("✅ LINE 訊息發送成功！")
                return True
            else:
                print(f"❌ LINE 訊息發送失敗，狀態碼: {response.status_code}")
                print(f"回應內容: {response.text}")
                return False
        except Exception as e:
            print(f"❌ 傳送過程發生錯誤：{e}")
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

# --- [新增]：儀表板通知器 ---
class DashboardNotifier:
    def __init__(self, port=8005):
        self.url = f"http://localhost:{port}/api/update"

    def notify(self, data_type, content):
        try:
            requests.post(self.url, json={"type": data_type, **content}, timeout=1)
        except:
            pass # 儀表板未開啟時忽略

    def log(self, message, level="info"):
        self.notify("log", {"content": message, "level": level})

    def status(self, step):
        self.notify("status", {"step": step})

def get_test_news():
    """當爬蟲模組失敗時的備用測試數據。返回一個空列表或模擬數據。"""
    print("⚠️ 使用測試數據。")
    return [] 

def main():
    # 1. 載入環境變數：對齊 Messaging API 規格
    load_dotenv()
    line_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    user_id = os.getenv("YOUR_USER_ID") # 從 .env 讀取正確的 User ID
    google_api_key = os.getenv("GOOGLE_API_KEY") # 從 .env 讀取正確的 API Key
    
    import argparse
    parser = argparse.ArgumentParser(description="DualBear Sentinel Alpha")
    parser.add_argument("--port", type=int, default=8005, help="Dashboard server port")
    args = parser.parse_args()

    db_notifier = DashboardNotifier(port=args.port) # 初始化儀表板通知器
    db_notifier.status("idle")
    db_notifier.log("🚀 DualBear Sentinel Alpha 系統啟動...", "system")

    if not line_token or not user_id:
        db_notifier.log("找不到 LINE_CHANNEL_ACCESS_TOKEN 或 YOUR_USER_ID", "error")
        print("❌ 錯誤：找不到 LINE_CHANNEL_ACCESS_TOKEN 或 YOUR_USER_ID。")
        return
    if not google_api_key:
        db_notifier.log("找不到 GOOGLE_API_KEY", "error")
        print("❌ 錯誤：找不到 GOOGLE_API_KEY。")
        return

    notifier = LineNotifier(line_token, user_id)
    
    # --- ⚔️ PHASE: Real Scouting ---
    db_notifier.status("scouting")
    db_notifier.log("📡 正在部署情報網：鉅亨網 & PTT Stock...", "scout")
    print("🚀 DualBear Sentinel Alpha 啟動真實偵察任務...")
    
    try:
        scouts = [AnueScout(), PttStockScout()]
        
        all_intelligence = []
        for scout in scouts:
            scout_name = scout.__class__.__name__
            db_notifier.log(f"🕵️ 特工 {scout_name} 開始作業...", "scout")
            try:
                intelligence_list = []
                if hasattr(scout, 'scrape_latest_news'):
                    intelligence_list = scout.scrape_latest_news(limit=10)
                elif hasattr(scout, 'scrape_latest_posts'):
                    intelligence_list = scout.scrape_latest_posts(pages=2, min_pushes=15)
                
                db_notifier.log(f"✅ {scout_name} 蒐集到 {len(intelligence_list)} 則情報", "success")
                
                # 即時推送到儀表板
                for item in intelligence_list:
                    db_notifier.notify("intelligence", {"content": item})
                
                all_intelligence.extend(intelligence_list)
            except Exception as e:
                db_notifier.log(f"⚠️ {scout_name} 偵察失敗: {str(e)}", "warning")
                print(f"⚠️ 偵察特工偵察失敗：{e}")
            
        intelligence_count = len(all_intelligence)
        db_notifier.log(f"📊 總計蒐集到 {intelligence_count} 則市場情報。", "info")
        print(f"✅ 成功蒐集到 {intelligence_count} 則市場情報。")
    except Exception as e:
        db_notifier.log(f"❌ 偵察階段發生嚴重錯誤: {str(e)}", "error")
        all_intelligence = []
        intelligence_count = 0

    if not all_intelligence:
        db_notifier.log("今日未抓取到任何有效市場情報，任務終止。", "warning")
        db_notifier.status("idle")
        notifier.send_text("⚠️ 今日偵察報告: 未抓取到有效情報。請檢查爬蟲模組。")
        return

    # --- Block 2: AI Analysis & Sentinel Decision ---
    db_notifier.status("analyzing")
    db_notifier.log("🧠 正在呼叫 Gemini AI 大腦進行情緒判讀...", "ai")
    
    try:
        analyzer = SentimentAnalyzer(google_api_key)
        
        total_score = 0
        analyzed_count = 0
        sentiment_flavors = []

        for i, intelligence in enumerate(all_intelligence):
            try:
                # 通知儀表板開始分析
                db_notifier.notify("analysis_start", {"title": intelligence['title']})
                db_notifier.log(f"[{i+1}/{intelligence_count}] 分析中: {intelligence['title'][:30]}...", "ai")
                
                sentiment = analyzer.analyze(intelligence['title'])
                
                if isinstance(sentiment, dict):
                    score = sentiment.get('score', 0)
                    flavor = sentiment.get('flavor', '中性')
                else: 
                    score = sentiment.score
                    flavor = sentiment.flavor

                total_score += score
                analyzed_count += 1
                db_notifier.log(f"   ∟ 分數: {score} ({flavor})", "info")
            except Exception as e:
                db_notifier.log(f"⚠️ 分析失敗: {str(e)}", "warning")

        # 精算最終的情緒分數
        if analyzed_count > 0:
            final_sentiment_score = total_score / analyzed_count
        else:
            final_sentiment_score = 0
        
        db_notifier.log(f"✅ AI 集體判讀完成。最終情緒指數: {final_sentiment_score:.2f}", "success")

        # --- [關鍵聯動]：策略精算師 ---
        db_notifier.log("🛡️ 正在計算最終策略佈置...", "system")
        sentinel = SentinelAlpha()
        decision = sentinel.calculate_position(final_sentiment_score)
        
        decision['sentiment_score'] = final_sentiment_score
        
        # 即時推送到儀表板最後結果
        db_notifier.notify("analysis_result", {"final_score": final_sentiment_score})
        db_notifier.notify("decision", decision)

        final_decision = decision
        db_notifier.log(f"🎯 哨兵策略生成：建議【{decision['action']}】", "success")
        
    except Exception as e:
        db_notifier.log(f"❌ 分析決策階段發生錯誤: {str(e)}", "error")
        final_decision = None

    # --- Block 3: Final Report Construction ---
    db_notifier.status("reporting")
    db_notifier.log("📊 正在建構與發送最終戰略報告...", "system")
    
    report = construct_report(final_decision, intelligence_count) 
    
    # --- Block 4: Final Reporting (LINE) ---
    try:
        notifier.send_text(report)
        db_notifier.log("✅ LINE 戰略通報已送達 comandante 終端。", "success")
    except Exception as e:
        db_notifier.log(f"❌ LINE 發送失敗: {str(e)}", "error")

    # --- Block 5: Persistence (Save History) ---
    db_notifier.log("💾 正在執行數據持久化...", "system")
    try:
        history_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", "history")
        if not os.path.exists(history_dir):
            os.makedirs(history_dir)
            
        today_file = os.path.join(history_dir, f"{datetime.now().strftime('%Y-%m-%d')}.json")
        
        history_data = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "intelligence_count": intelligence_count,
            "intelligence": all_intelligence,
            "decision": final_decision
        }
        
        with open(today_file, "w", encoding="utf-8") as f:
            json.dump(history_data, f, ensure_ascii=False, indent=4)
            
        db_notifier.log(f"✅ 歷史數據已儲存: {os.path.basename(today_file)}", "success")
    except Exception as e:
        db_notifier.log(f"❌ 數據持久化失敗: {str(e)}", "error")

    db_notifier.status("idle")
    db_notifier.log("🏁 任務圓滿結束，系統回歸低能耗監控模式。", "system")

if __name__ == "__main__":
    main()