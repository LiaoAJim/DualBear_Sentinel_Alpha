import os
import json
import requests
import time
from datetime import datetime
from dotenv import load_dotenv

from core.analyzer import SentimentAnalyzer
from core.ptt_scout import PttStockScout # 修正導入路徑，改用專用 PTT 爬蟲
# AnueScout 現在由 run_news_recon 自動調度，無需在此導入
from core.sentinel import SentinelAlpha # 導入 哨兵策略精算師 (L11)
from news_recon_runner import run_news_recon
from quant_recon_runner import run_quant_recon

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
def _format_report_metric(value, suffix=""):
    if value is None or value == "":
        return "失敗"
    if isinstance(value, float):
        return f"{value:.2f}{suffix}"
    return f"{value}{suffix}"


def build_display_quant_data(quant_data=None):
    quant_data = quant_data or {}
    status = quant_data.get("_status", {}) if isinstance(quant_data, dict) else {}

    def normalize(field):
        value = quant_data.get(field) if isinstance(quant_data, dict) else None
        # 有實際值就返回
        if value is not None:
            return value
        # 沒有值：失敗顯示「失敗」，其他返回 None
        if status.get(field) == "failed":
            return "失敗"
        return None

    return {
        # 優先使用 quant_scout 計算好的顯示值（含 'XQ未開' 狀態標籤）
        "margin_maintenance_ratio": quant_data.get("margin_display") if quant_data.get("margin_display") is not None else normalize("margin_maintenance_ratio"),
        "retail_long_short_ratio": normalize("retail_long_short_ratio"),
        "vixtwn": normalize("vixtwn"),
        "vixus": normalize("vixus")
    }


def build_report_guidance(decision, quant_data=None, mode="report"):
    quant_data = quant_data or {}
    action = decision.get("action", "")
    sentiment_score = decision.get("sentiment_score")
    failed_sources = decision.get("failed_sources") or []
    vixtwn = quant_data.get("vixtwn")
    vixus = quant_data.get("vixus")
    calculation_breakdown = decision.get("calculation_breakdown", "")

    score_neutral = sentiment_score is None or abs(sentiment_score) < 0.2
    high_vix = any(
        isinstance(v, (int, float)) and v >= 25
        for v in [vixtwn, vixus]
    )

    if failed_sources:
        text = (
            "本次資料存在缺口，較適合用於風險提醒，不適合單獨作為選股或槓桿依據。 "
            "建議用途：降低風險、排除弱勢、觀察逆勢強股。"
        )
    elif action in {"持平", "持平 (已修正)"} or (score_neutral and high_vix):
        text = (
            "本報告較適合用於風險過濾與倉位控制，不適合單獨作為積極進場依據。"
        )
    elif action.startswith("減碼"):
        text = (
            "本報告偏向風險降溫訊號，較適合降低追價與重倉風險，不宜單靠單日敘事進場。"
        )
    else:
        text = (
            "本報告可作為觀察強弱與調整倉位的依據，但仍不建議單靠情緒分數進行槓桿交易。"
        )

    if mode == "history":
        return text
    if mode == "line":
        # 如果 text 已經包含「建議用途」，就不重複加了
        if "建議用途" in text:
            return text
        return text + " 建議用途：降低風險、排除弱勢、觀察逆勢強股。"
    
    if "建議用途" in text:
        return text
    return (
        text + "\n"
        "建議用途：降低追高與重倉風險、排除明顯轉弱族群、觀察震盪中仍相對強勢的標的。"
    )


def construct_report(decision, intelligence_count, quant_data=None):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    if decision:
        sentiment_score = decision.get('sentiment_score')
        failed_sources = decision.get('failed_sources') or []
        failure_line = f"⚠️ 失敗來源: {'、'.join(failed_sources)}\n" if failed_sources else ""
        
        # 安全處理 None 的 sentiment_score
        if sentiment_score is not None:
            score_text = f"{sentiment_score:.2f}"
            sentiment_label = "利多" if sentiment_score > 0 else "利空" if sentiment_score < 0 else "中性"
        else:
            score_text = "N/A"
            sentiment_label = "分析失敗"
        
        quant_data = quant_data or {}
        margin_text = _format_report_metric(quant_data.get('margin_maintenance_ratio'), " %")
        retail_text = _format_report_metric(quant_data.get('retail_long_short_ratio'))
        vixtwn_text = _format_report_metric(quant_data.get('vixtwn'))
        vixus_text = _format_report_metric(quant_data.get('vixus'))
        guidance_text = build_report_guidance(decision, quant_data, mode="line")

        calculation_breakdown = decision.get("calculation_breakdown", "")
        calc_line = f"精算過程：{calculation_breakdown}\n" if calculation_breakdown else ""

        report_text = (
            f"📊 DualBear 哨兵正式戰報\n\n"
            f"🕒 時間: {now}\n"
            f"📡 偵察情報數: {intelligence_count} 則\n"
            f"💡 最終情緒: {score_text} ({sentiment_label})\n\n"
            f"【決策摘要】\n"
            f"🛡️ 建議操作: {decision.get('action', 'N/A')}\n"
            f"🎯 建議倉位: {decision.get('target_position', 'N/A')}\n"
            f"{calc_line}\n"
            f"【量化指標】\n"
            f"💳 融資維持率: {margin_text}\n"
            f"👥 散戶多空比: {retail_text}\n"
            f"🇹🇼 台灣 VIX: {vixtwn_text}\n"
            f"🇺🇸 美國 VIX: {vixus_text}\n\n"
            f"【戰略理由】\n"
            f"{decision.get('recon_notes', 'N/A')}\n"
            f"{failure_line}\n"
            f"【使用建議】\n"
            f"{guidance_text}\n\n"
            f"DualBear Sentinel Alpha"
        )
        
        # 將 guidance 同步存入 decision 本體，方便 UI 顯示
        decision["report_guidance"] = guidance_text
        decision["report_text"] = report_text
        
        return report_text
    else:
        return (
            f"📊 DualBear 哨兵正式戰報\n\n"
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

def construct_crawl_failure_decision(failures):
    failure_text = "、".join(failures) if failures else "未知來源"
    return {
        "action": "爬蟲失敗",
        "target_position": "失敗",
        "recon_notes": f"⚠️ 爬蟲或量化資料抓取失敗：{failure_text}。本次不產生建議，避免使用錯誤預設值。",
        "failed_sources": failures or [],
        "risk_status": "ERROR",
        "quant_adjustment": None,
        "sentiment_score": None
    }


def build_failure_variants(failures, sentiment_score=None):
    variants = {}
    for profile, label in {
        "conservative": "保守版",
        "balanced": "平衡版",
        "contrarian": "反向極端版"
    }.items():
        decision = construct_crawl_failure_decision(failures)
        decision["strategy_profile"] = profile
        decision["strategy_label"] = label
        decision["sentiment_score"] = sentiment_score
        variants[profile] = decision
    return variants

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
    db_notifier.log("📡 啟動 DualBear 廣域偵察網：對接 TWSE、Yahoo、UDN、PTT、鉅亨 & 玩股網...", "scout")
    print("[START] DualBear Sentinel Alpha 啟動「官網級」真實偵察任務...")
    
    all_intelligence = []
    quant_data = None
    source_failures = []
    decision_failures = []
    decision_variants = {}
    report_variants = {}
    selected_variant = "balanced"
    
    # --- [全域統計計數器]：在所有 try 區塊之前初始化，確保一定可以存到歷史 ---
    total_count = 0
    success_count = 0
    failure_count = 0
    total_score = 0
    analysis_details = []
    
    try:
        # (A) 輿情採集：廣域偵察
        news_result = run_news_recon()
        all_intelligence = news_result.get("intelligence", [])
        source_status = news_result.get("source_status", {})
        source_failures = news_result.get("source_failures", [])
        for source_key, status in source_status.items():
            # 只有確定有爬到資料 (count > 0) 才顯示成功 (✓)，否則顯示失敗 (✕)
            is_really_success = status.get("success") and status.get("count", 0) > 0
            db_notifier.notify("source_status", {
                "source": source_key, 
                "status": "success" if is_really_success else "failed"
            })
        
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

        if source_failures:
            db_notifier.log(f"⚠️ Step 1 情報來源不完整：{'、'.join(source_failures)}", "warning")
        
    except Exception as e:
        db_notifier.log(f"❌ 偵察階段發生嚴重錯誤: {str(e)}", "error")
        print(f"[WARN] 偵察失敗：{e}")

    intelligence_count = len(all_intelligence)
    if not all_intelligence:
        db_notifier.log("今日未抓取到任何有效市場情報，任務終止。", "warning")
        db_notifier.status("idle")
        failure_quant = {
            "margin_maintenance_ratio": "失敗",
            "retail_long_short_ratio": "失敗",
            "vixtwn": "失敗",
            "vixus": "失敗"
        }
        db_notifier.notify("quant_data", failure_quant)
        decision_variants = build_failure_variants(["市場情報"])
        report_variants = {
            profile: construct_report(decision, intelligence_count, failure_quant)
            for profile, decision in decision_variants.items()
        }
        failure_decision = decision_variants[selected_variant]
        db_notifier.notify("decision", failure_decision)
        notifier.send_text(report_variants[selected_variant])
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
                    analysis_details.append({
                        "title": intelligence.get("title", ""),
                        "source": src,
                        "status": "success",
                        "provider": ai_name,
                        "score": score,
                        "flavor": flavor
                    })
                    db_notifier.log(f"   L [{ai_name}] 判定: {score} ({flavor})", "info")
                elif result and result.get('error'):
                    # 分析失敗：根據錯誤類型顯示不同訊息
                    failure_count += 1
                    err_type = result.get('error_type', 'UNKNOWN')
                    err_msg  = result.get('msg', '')
                    analysis_details.append({
                        "title": intelligence.get("title", ""),
                        "source": src,
                        "status": "failed",
                        "provider": ai_name,
                        "error_type": err_type,
                        "message": err_msg
                    })
                    
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
                    analysis_details.append({
                        "title": intelligence.get("title", ""),
                        "source": src,
                        "status": "failed",
                        "provider": ai_name,
                        "error_type": "UNKNOWN",
                        "message": "AI 回傳為空或格式未知"
                    })
                    db_notifier.log(f"   L AI 回傳為空或格式未知", "warning")
                
                # 即時更新統計數據至儀表板
                db_notifier.send_analysis_stats(total_count, success_count, failure_count)
                
            except Exception as e:
                failure_count += 1
                db_notifier.send_analysis_stats(total_count, success_count, failure_count)
                analysis_details.append({
                    "title": intelligence.get("title", ""),
                    "source": intelligence.get("source", "未知"),
                    "status": "failed",
                    "provider": "unknown",
                    "error_type": "EXCEPTION",
                    "message": str(e)
                })
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

        db_notifier.notify("analysis_result", {"final_score": final_sentiment_score})
        
    except Exception as e:
        db_notifier.log(f"❌ 分析決策階段發生錯誤: {str(e)}", "error")
        final_decision = None
        final_sentiment_score = None

    # --- Block 3: Step 3 Quant + Sentinel Decision ---
    db_notifier.status("reporting")
    db_notifier.log("🛡️ Step 3 哨兵決策判斷啟動：正在採集融資 / 散戶 / 台美 VIX...", "system")

    try:
        quant_result = run_quant_recon()
        quant_data = quant_result.get("quant_data")
        decision_failures = quant_result.get("decision_failures", [])
        quant_errors = (quant_data or {}).get("_errors", {})
        for field_name, error_message in quant_errors.items():
            if error_message:
                db_notifier.log(f"⚠️ Step 3 {field_name} 失敗原因: {error_message}", "warning")
    except Exception as e:
        db_notifier.log(f"❌ Step 3 數值偵察失敗: {str(e)}", "error")
        decision_failures.extend(["融資", "散戶", "台灣VIX", "美國VIX"])
        quant_data = {
            "_status": {
                "margin_maintenance_ratio": "failed",
                "retail_long_short_ratio": "failed",
                "vixtwn": "failed",
                "vixus": "failed"
            },
            "_errors": {
                "margin_maintenance_ratio": str(e),
                "retail_long_short_ratio": str(e),
                "vixtwn": str(e),
                "vixus": str(e)
            }
        }

    display_quant_data = build_display_quant_data(quant_data)
    # 附帶各指標的資料所屬日期（來自 quant_scout 的 _data_dates）
    push_quant = {
        **display_quant_data,
        "_data_dates": (quant_data or {}).get("_data_dates", {})
    }
    db_notifier.notify("quant_data", push_quant)

    if decision_failures:
        db_notifier.log(f"⚠️ Step 3 決策資料不完整：{'、'.join(decision_failures)}，將以可用參數繼續精算。", "warning")

    try:
        db_notifier.log("🛡️ 正在計算最終策略佈置...", "system")
        sentinel = SentinelAlpha()
        decision_variants = sentinel.calculate_variants(final_sentiment_score, quant_data=quant_data)
        for variant in decision_variants.values():
            variant['sentiment_score'] = final_sentiment_score
            variant['failed_sources'] = (variant.get('failed_sources') or []) + decision_failures
        report_variants = {
            profile: construct_report(decision, intelligence_count, display_quant_data)
            for profile, decision in decision_variants.items()
        }
        final_decision = decision_variants[selected_variant]
        
        # 確保 final_decision 包含精算過程與建議文字，讓 UI 能直接渲染
        final_decision["report_guidance"] = build_report_guidance(final_decision, display_quant_data, mode="history")
        
        db_notifier.notify("decision", final_decision)
        db_notifier.log(
            "🧾 三版決策已生成："
            + " / ".join(
                f"{decision_variants[p]['strategy_label']}={decision_variants[p]['action']} {decision_variants[p]['target_position']}"
                for p in ["conservative", "balanced", "contrarian"]
            ),
            "system"
        )
        db_notifier.log(f"🎯 哨兵策略生成：建議【{final_decision['action']}】", "success")
    except Exception as e:
        db_notifier.log(f"❌ Step 3 決策生成失敗: {str(e)}", "error")
        final_decision = None

    # --- Block 4: Final Report Construction ---
    db_notifier.log("📊 正在建構與發送最終戰略報告...", "system")
    
    report = report_variants.get(selected_variant) or construct_report(final_decision, intelligence_count, display_quant_data)
    
    # --- Block 5: Final Reporting (LINE) ---
    try:
        notifier.send_text(report)
        db_notifier.log("✅ LINE 戰略通報已送達 comandante 終端。", "success")
    except Exception as e:
        db_notifier.log(f"❌ LINE 發送失敗: {str(e)}", "error")

    # --- Block 6: Persistence (Save History) ---
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
            "analysis_details": analysis_details,
            "intelligence": all_intelligence,
            "decision": final_decision,
            "selected_variant": selected_variant,
            "decision_variants": decision_variants,
            "quant_data": display_quant_data,  # UI / 歷史快照使用可視化值，失敗欄位直接標示為失敗
            "report": report,
            "report_variants": report_variants,
            "report_guidance": build_report_guidance(final_decision or {}, display_quant_data, mode="history")
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
