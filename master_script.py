import os
import json
import requests
import time
from datetime import datetime
from dotenv import load_dotenv

# --- [關鍵修復]：從 core 模組導入所有需要的特工與腦部 ---
from core.crawler import DataScout
from core.analyzer import SentimentAnalyzer
from core.scout import PttStockScout # 修正導入路徑
from core.anue_scout import AnueScout # 導入 鉅亨特工
from core.sentinel import SentinelAlpha # 導入 哨兵策略精算師 (L11)
from core.quant_scout import QuantSentimentScout # 導入 籌碼情報員

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
                print("[OK] LINE 訊息發送成功！")
                return True
            else:
                print(f"[FAIL] LINE 訊息發送失敗，狀態碼: {response.status_code}")
                print(f"回應內容: {response.text}")
                return False
        except Exception as e:
            print(f"[ERROR] 傳送過程發生錯誤：{e}")
            return False

# --- [優化]：將報告建構函數搬到外部，並優化時間處理 ---
def construct_report(decision, intelligence_count):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    if decision:
        sentiment_score = decision.get('sentiment_score')
        
        # 安全處理 None 的 sentiment_score
        if sentiment_score is not None:
            score_text = f"{sentiment_score:.2f}"
            sentiment_label = "利多" if sentiment_score > 0 else "利空" if sentiment_score < 0 else "中性"
        else:
            score_text = "N/A"
            sentiment_label = "分析失敗"
        
        return (
            f"📊 DualBear 今日戰略報告\n\n"
            f"🕒 時間: {now}\n"
            f"📡 偵察情報數: {intelligence_count} 則\n"
            f"💡 最終情緒: {score_text} ({sentiment_label})\n\n"
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

    def send_analysis_stats(self, total, success, failure):
        self.notify("analysis_stats", {
            "total": total,
            "success": success,
            "failure": failure
        })

def get_test_news():
    """當爬蟲模組失敗時的備用測試數據。返回一個空列表或模擬數據。"""
    print("[WARN] 使用測試數據。")
    return [] 

def main():
    # 1. 載入環境變數：對齊 Messaging API 規格
    load_dotenv()
    line_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    user_id = os.getenv("YOUR_USER_ID") # 從 .env 讀取正確的 User ID
    google_api_key = os.getenv("GOOGLE_API_KEY")
    manus_api_key  = os.getenv("Manus_API_KEY")
    nvidia_api_key = os.getenv("NVIDIA_NIM_API_KEY")

    # 條列所有有效 Key，預設優先順序：NVIDIA > Manus > Gemini (Gemini 排最後)
    api_keys = [k for k in [nvidia_api_key, manus_api_key, google_api_key] if k]

    import argparse
    parser = argparse.ArgumentParser(description="DualBear Sentinel Alpha")
    parser.add_argument("--port", type=int, default=8005, help="Dashboard server port")
    parser.add_argument("--preferred-provider", type=str, default="auto",
                        choices=["auto", "gemini", "nvidia", "manus", "rule"],
                        help="指定優先使用的 AI 引擎 (rule=規則引擎)")
    args = parser.parse_args()
    
    # 儲存使用者選擇的引擎
    preferred_engine = args.preferred_provider
    use_rule_only = (preferred_engine == "rule")
    
    # 🔍 調試：確保傳入的值正確
    print(f"[DEBUG] 收到的 preferred_provider: {preferred_engine}")
    print(f"[DEBUG] use_rule_only: {use_rule_only}")
    print(f"[DEBUG] api_keys count: {len(api_keys)}")
    
    db_notifier = DashboardNotifier(port=args.port) # 初始化儀表板通知器
    db_notifier.status("idle")
    db_notifier.log("🚀 DualBear Sentinel Alpha 系統啟動...", "system")
    db_notifier.log(f"📋 引擎模式: {preferred_engine}", "system")
    
    # 如果選擇規則引擎，則不需要 API Key
    if not line_token or not user_id:
        db_notifier.log("找不到 LINE_CHANNEL_ACCESS_TOKEN 或 YOUR_USER_ID", "error")
        print("[ERROR] 錯誤：找不到 LINE_CHANNEL_ACCESS_TOKEN 或 YOUR_USER_ID。")
        return
    if not api_keys and not use_rule_only:
        db_notifier.log("找不到任何有效的 API Key (GOOGLE_API_KEY / NVIDIA_NIM_API_KEY)", "warning")
        print("[WARN] 警告：找不到 API Key，將只使用規則引擎。")
        use_rule_only = True
    
    if use_rule_only:
        db_notifier.log("📋 使用規則引擎模式 (本地分析，零成本)", "system")
        print("[INFO] 使用規則引擎模式。")
    else:
        print(f"[INFO] 已載入 {len(api_keys)} 組 API Key，支援自動輪換。")

    notifier = LineNotifier(line_token, user_id)
    
    # --- ⚔️ PHASE: Wide Recon (廣域偵察) ---
    db_notifier.status("scouting")
    db_notifier.log("📡 啟動 DualBear 廣域偵察網：對接 TWSE、Yahoo、UDN、PTT & 鉅亨...", "scout")
    print("[START] DualBear Sentinel Alpha 啟動「官網級」真實偵察任務...")
    
    all_intelligence = []
    quant_data = None
    
    # --- [全域統計計數器]：在所有 try 區塊之前初始化，確保一定可以存到歷史 ---
    total_count = 0
    success_count = 0
    failure_count = 0
    total_score = 0
    
    try:
        # (A) 輿情採集：廣域偵察
        from core.crawler import DataScout
        news_agent = DataScout()
        all_intelligence = news_agent.fetch_all_news()
        
        # 📊 來源來源分析
        sources = {}
        for item in all_intelligence:
            src = item.get('source', '其他')
            sources[src] = sources.get(src, 0) + 1
        src_info = ", ".join([f"{k}({v})" for k,v in sources.items()])
        
        db_notifier.log(f"✅ 廣域採集完畢：共 {len(all_intelligence)} 則 ({src_info})", "success")
        
        # 即時更新至儀表板
        for item in all_intelligence:
            db_notifier.notify("intelligence", {"content": item})
        
        # (B) 籌碼採集：真理偵察
        db_notifier.log("🕵️ 籌碼情報員開始採集官網量化指標 (VIX/融資/散戶)...", "scout")
        quant_agent = QuantSentimentScout()
        quant_data = quant_agent.fetch_all_indicators()
        db_notifier.notify("quant_data", quant_data) 
        
        # (C) VIX 恐慌指數偵測
        db_notifier.log("📊 正在取得美國 VIX 恐慌指數...", "scout")
        try:
            from core.vix_scout import VIXScout
            vix_scout = VIXScout()
            vix_data = vix_scout.fetch()
            if vix_data.get("status") == "success":
                db_notifier.notify("vix_data", vix_data)
                db_notifier.log(f"📈 VIX: {vix_data.get('value', 'N/A')} ({vix_data.get('interpretation', 'N/A')})", "scout")
            else:
                db_notifier.log(f"⚠️ VIX 取得失敗: {vix_data.get('message', '未知錯誤')}", "warning")
        except Exception as e:
            db_notifier.log(f"⚠️ VIX 模組載入失敗: {str(e)}", "warning")
        
    except Exception as e:
        db_notifier.log(f"❌ 偵察階段發生嚴重錯誤: {str(e)}", "error")
        print(f"[WARN] 偵察失敗：{e}")

    intelligence_count = len(all_intelligence)
    if not all_intelligence:
        db_notifier.log("今日未抓取到任何有效市場情報，任務終止。", "warning")
        db_notifier.status("idle")
        notifier.send_text("⚠️ 今日偵察報告: 未抓取到有效情報。請檢查官網連線。")
        return

    # --- Block 2: AI Analysis & Sentinel Decision ---
    db_notifier.status("analyzing")
    db_notifier.log(f"🧠 正在呼叫 DualBear AI 矩陣 (已載入 {len(api_keys)} 組大腦) 进行情緒判讀...", "ai")
    
    try:
        from core.analyzer import ERR_RATE_LIMIT, ERR_ALL_KEYS_FAIL, ERR_SAFETY_FILTER, ERR_PARSE_FAIL
        analyzer = SentimentAnalyzer(api_keys, preferred_provider=preferred_engine)
        
        # 初始化分析統計（現在這些在全域作用域，不需要重複定義）
        total_count = len(all_intelligence)
        
        for i, intelligence in enumerate(all_intelligence):
            try:
                # 🕯️ 在分析前先取得下一位預計執行的大腦（僅供顯示）
                p_hint = analyzer.providers[analyzer.current_provider_index].key_hint

                # 通知儀表板開始分析
                db_notifier.notify("analysis_start", {"title": intelligence['title']})
                
                src = intelligence.get('source', '未知')
                db_notifier.log(f"[{i+1}/{total_count}] [{src}] AI 特工連線中...", "ai")
                
                result = analyzer.analyze(intelligence['title'])
                ai_name = result.get('provider', p_hint)
                
                if result and not result.get('error') and 'score' in result:
                    # 分析成功
                    score = result['score']
                    flavor = result.get('flavor', '中性')
                    total_score += score
                    success_count += 1
                    db_notifier.log(f"   L [{ai_name}] 判定: {score} ({flavor})", "info")
                elif result and result.get('error'):
                    # 分析失敗：根據錯誤類型顯示不同訊息
                    failure_count += 1
                    err_type = result.get('error_type', 'UNKNOWN')
                    err_msg  = result.get('msg', '')
                    
                    if err_type == ERR_ALL_KEYS_FAIL:
                        db_notifier.log(f"   L [!] AI 全滅 ({ai_name})，跳過此條。", "error")
                    elif err_type == ERR_RATE_LIMIT:
                        db_notifier.log(f"   L [!] {ai_name} 配額耗盡，正在切換...", "warning")
                    elif err_type == ERR_SAFETY_FILTER:
                        db_notifier.log(f"   L [!] {ai_name} 被安全過濾器攔截。", "warning")
                    elif err_type == ERR_PARSE_FAIL:
                        db_notifier.log(f"   L [!] {ai_name} 回傳格式異常，正在重試...", "warning")
                    else:
                        db_notifier.log(f"   L [!] {ai_name} 失敗 [{err_type}]: {err_msg[:50]}", "warning")
                    
                    # 💡 修正：即使全滅，也不要中斷「整個」程序，跳過這條去分析下一條
                    continue
                else:
                    failure_count += 1
                    db_notifier.log(f"   L AI 回傳為空或格式未知", "warning")
                
                # 即時更新統計數據至儀表板
                db_notifier.send_analysis_stats(total_count, success_count, failure_count)
                
            except Exception as e:
                failure_count += 1
                db_notifier.send_analysis_stats(total_count, success_count, failure_count)
                db_notifier.log(f"[!] 迴圈分析發生異常: {str(e)}", "warning")

        # 精算最終的情緒分數
        if success_count > 0:
            final_sentiment_score = total_score / success_count
        else:
            # 🚨 重要：如果全數失敗，設為 None 讓精算師知道要顯示「分析失敗」
            final_sentiment_score = None
        
        if final_sentiment_score is not None:
            db_notifier.log(f"✅ AI 集體判讀完成。最終情緒指數: {final_sentiment_score:.2f}", "success")
        else:
            db_notifier.log("❌ AI 全數分析失敗，無法計算情緒指數。", "error")

        # --- [關鍵聯動]：策略精算師 ---
        db_notifier.log("🛡️ 正在計算最終策略佈置...", "system")
        sentinel = SentinelAlpha()
        decision = sentinel.calculate_position(final_sentiment_score, quant_data=quant_data)
        
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
            
        # 🚀 檔名升級：加入時間戳避免覆蓋
        timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
        today_file = os.path.join(history_dir, f"{timestamp}.json")
        
        # 取得分析統計（現在全域可見，不再需要 try/except）
        stats_total = total_count
        stats_success = success_count
        stats_failure = failure_count
        
        history_data = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "intelligence_count": intelligence_count,
            "analysis_stats": {
                "total": stats_total,
                "success": stats_success,
                "failure": stats_failure
            },
            "intelligence": all_intelligence,
            "decision": final_decision,
            "quant_data": quant_data  # 加入量化數據（包含 VIX、融資、散戶比）
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