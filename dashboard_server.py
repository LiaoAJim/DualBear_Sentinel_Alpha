import os
import uvicorn
import json
import asyncio
import subprocess
import argparse
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Body
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List

app = FastAPI(title="DualBear Sentinel Dashboard")

# 設置靜態檔案與模板 (禁用緩存以便開發)
app.mount("/static", StaticFiles(directory="static", html=True), name="static")
templates = Jinja2Templates(directory="templates")

# 禁用靜態文件緩存
@app.middleware("http")
async def no_cache(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

@app.get("/")
async def root_redirect():
    return RedirectResponse(url="/sentinel-alpha")

@app.get("/SentinelAlpha")
async def legacy_redirect():
    return RedirectResponse(url="/sentinel-alpha")

@app.get("/sentinel-alpha")
async def get_dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # 保持連線開啟
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# --- 設定持久化 API (讓 QWebEngineView 也能使用) ---
SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", "user_settings.json")

@app.get("/api/settings")
async def get_settings():
    """取得使用者設定"""
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except:
        pass
    return {"cash": "500000", "stock": "500000", "longterm": "50", "provider": "auto", "leverage2": []}

@app.post("/api/settings")
async def save_settings(data: dict):
    """儲存使用者設定"""
    try:
        os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# 用於接收 master_script 資料的正向代理 API (如果需要的話)
@app.post("/api/update")
async def update_data(data: dict):
    await manager.broadcast(data)
    return {"status": "success"}

# --- 歷史數據 API ---
HISTORY_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", "history")

@app.get("/api/history")
async def list_history():
    """回傳所有可用的歷史日期清單（含統計摘要）"""
    if not os.path.exists(HISTORY_DIR):
        return {"dates": []}
    
    # 抓取檔案並按名稱逆向排序 (檔名即時間戳，確保最新優先)
    files = [f.replace(".json", "") for f in os.listdir(HISTORY_DIR) if f.endswith(".json")]
    
    # 讀取每個檔案的統計資料
    history_list = []
    for date in sorted(files, reverse=True):
        file_path = os.path.join(HISTORY_DIR, f"{date}.json")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                stats = data.get("analysis_stats", {})
                decision = data.get("decision", {}) or {}
                quant_data = data.get("quant_data", {}) or {}
                history_list.append({
                    "date": date,
                    "intelligence_count": data.get("intelligence_count", 0),
                    "analysis_stats": {
                        "total": stats.get("total", 0),
                        "success": stats.get("success", 0),
                        "failure": stats.get("failure", 0)
                    },
                    "sentiment_score": decision.get("sentiment_score"),
                    "step3": {
                        "action": decision.get("action"),
                        "target_position": decision.get("target_position"),
                        "strategy_label": decision.get("strategy_label"),
                        "risk_status": decision.get("risk_status"),
                        "margin_maintenance_ratio": quant_data.get("margin_maintenance_ratio"),
                        "retail_long_short_ratio": quant_data.get("retail_long_short_ratio"),
                        "vixtwn": quant_data.get("vixtwn"),
                        "vixus": quant_data.get("vixus")
                    }
                })
        except:
            history_list.append({"date": date})
    
    return {"dates": history_list}

@app.get("/api/history/{date}")
async def get_history_by_date(date: str):
    """讀取特定日期的詳細數據"""
    file_path = os.path.join(HISTORY_DIR, f"{date}.json")
    if not os.path.exists(file_path):
        return {"error": "Date not found"}
    
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

@app.delete("/api/history/{date}")
async def delete_history_by_date(date: str):
    """徹底刪除指定的歷史報告檔案"""
    file_path = os.path.join(HISTORY_DIR, f"{date}.json")
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return {"status": "success", "message": f"Report {date} deleted."}
        else:
            return {"status": "error", "message": "File not found"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/backtest")
async def run_backtest(symbol: str = "^TWII"):
    """執行規則引擎回測驗證"""
    try:
        from core.backtester import SentimentBacktester
        bt = SentimentBacktester()
        result = bt.run_backtest(symbol=symbol)
        return result
    except Exception as e:
        return {"status": "error", "message": str(e)}

# 全域變數追蹤當前偵察進程
current_recon_process = None

# 解析命令行參數
_parser = argparse.ArgumentParser(description="DualBear Sentinel Dashboard Server")
_parser.add_argument("--port", type=int, default=8001, help="Server port")
_args = _parser.parse_args()
_DEFAULT_PORT = _args.port

@app.post("/api/run")
async def run_recon(request: Request):
    """立即執行市場偵察任務，可選擇 AI 引擎"""
    global current_recon_process
    try:
        # 解析 JSON body（可選），取得 preferred_provider
        try:
            body = await request.json()
            preferred_provider = body.get("preferred_provider", "auto")
        except:
            preferred_provider = "auto"

        # 如果已有在執行的進程，先嘗試停止它
        if current_recon_process and current_recon_process.poll() is None:
            current_recon_process.terminate()

        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "master_script.py")
        cwd = os.path.dirname(os.path.abspath(__file__))
        
        try:
            target_port = _DEFAULT_PORT
        except:
            target_port = 8005
        
        error_log_dir = os.path.join(cwd, "logs")
        if not os.path.exists(error_log_dir):
            os.makedirs(error_log_dir)
        
        recon_err_file = open(os.path.join(error_log_dir, "recon_error.log"), "a", encoding="utf-8")
        
        current_recon_process = subprocess.Popen(
            ["python", script_path, "--port", str(target_port),
             "--preferred-provider", preferred_provider],
            stdout=subprocess.DEVNULL,
            stderr=recon_err_file,
            cwd=cwd,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        return {"status": "started", "pid": current_recon_process.pid,
                "preferred_provider": preferred_provider}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/stop")
async def stop_recon():
    """停止當前偵察任務"""
    global current_recon_process
    if current_recon_process and current_recon_process.poll() is None:
        current_recon_process.terminate()
        await manager.broadcast({"type": "log", "content": "🛑 偵察任務已被使用者強制中斷。", "level": "warning"})
        await manager.broadcast({"type": "status", "step": "idle"})
        return {"status": "stopped"}
    return {"status": "nothing_to_stop"}

# --- 詞庫管理 API ---
LEXICON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config", "sentiment_lexicon.json")
TARGETS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config", "targets.json")

@app.get("/api/targets")
async def get_targets():
    """取得觀測標的清單"""
    try:
        if not os.path.exists(TARGETS_PATH):
            return {"targets": []}
        with open(TARGETS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return {"error": str(e), "targets": []}

@app.post("/api/targets")
async def save_targets(data: dict):
    """儲存觀測標的清單"""
    try:
        print(f"[API] 收到 targets 儲存請求: {data}")
        config_dir = os.path.dirname(TARGETS_PATH)
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
        with open(TARGETS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[API] targets 已儲存到: {TARGETS_PATH}")
        return {"status": "success"}
    except Exception as e:
        print(f"[API] targets 儲存失敗: {e}")
        return {"status": "error", "message": str(e)}


@app.get("/api/lexicon")
async def get_lexicon():
    """取得情緒詞庫"""
    try:
        if not os.path.exists(LEXICON_PATH):
            return {"error": "詞庫檔案不存在", "lexicon": {}}
        
        with open(LEXICON_PATH, 'r', encoding='utf-8') as f:
            lexicon = json.load(f)
        return lexicon
    except Exception as e:
        return {"error": str(e), "lexicon": {}}

@app.get("/api/lexicon/{category}")
async def get_lexicon_category(category: str):
    """取得特定分類的詞庫"""
    try:
        if not os.path.exists(LEXICON_PATH):
            return {"error": "詞庫檔案不存在", "words": []}
        
        with open(LEXICON_PATH, 'r', encoding='utf-8') as f:
            lexicon = json.load(f)
        
        # 取得指定分類的詞彙
        cat_data = lexicon.get('lexicon', {}).get(category, {})
        if isinstance(cat_data, dict):
            return {
                "category": category,
                "weight": cat_data.get('_weight', 1),
                "words": cat_data.get('_examples', [])
            }
        elif isinstance(cat_data, list):
            return {"category": category, "weight": 1, "words": cat_data}
        else:
            return {"category": category, "weight": 1, "words": []}
    except Exception as e:
        return {"error": str(e), "words": []}

@app.post("/api/lexicon/{category}")
async def update_lexicon_category(category: str, request: Request):
    """更新特定分類的詞庫"""
    try:
        body = await request.json()
        new_words = body.get('words', [])
        
        # 讀取現有詞庫
        if os.path.exists(LEXICON_PATH):
            with open(LEXICON_PATH, 'r', encoding='utf-8') as f:
                lexicon = json.load(f)
        else:
            lexicon = {
                "version": "1.0",
                "description": "台股情緒詞庫",
                "lexicon": {}
            }
        
        # 預設權重對照表
        weight_map = {
            "bullish_extreme": 5,
            "bullish_strong": 3,
            "bullish_mild": 1,
            "bearish_extreme": -5,
            "bearish_strong": -3,
            "bearish_mild": -1,
            "sarcasm_negative": -2,
            "quant_terms": 2,
            "crisis_terms": -3
        }
        
        # 更新指定分類
        weight = weight_map.get(category, 1)
        lexicon['lexicon'][category] = {
            "_weight": weight,
            "_examples": new_words
        }
        
        # 確保 config 目錄存在
        config_dir = os.path.dirname(LEXICON_PATH)
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
        
        # 儲存更新後的詞庫
        with open(LEXICON_PATH, 'w', encoding='utf-8') as f:
            json.dump(lexicon, f, ensure_ascii=False, indent=2)
        
        # 重新整理時間戳
        lexicon['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        return {"status": "success", "message": f"已更新 {category} 分類，共 {len(new_words)} 個詞"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    print(f"[OK] DualBear Dashboard Server starting on port {_DEFAULT_PORT}...")
    uvicorn.run(app, host="0.0.0.0", port=_DEFAULT_PORT, log_level="info")
