import os
import uvicorn
import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List

app = FastAPI(title="DualBear Sentinel Dashboard")

# 設置靜態檔案與模板
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

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

# 用於接收 master_script 資料的正向代理 API (如果需要的話)
@app.post("/api/update")
async def update_data(data: dict):
    await manager.broadcast(data)
    return {"status": "success"}

# --- 歷史數據 API ---
HISTORY_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", "history")

@app.get("/api/history")
async def list_history():
    """回傳所有可用的歷史日期清單"""
    if not os.path.exists(HISTORY_DIR):
        return {"dates": []}
    
    files = [f.replace(".json", "") for f in os.listdir(HISTORY_DIR) if f.endswith(".json")]
    return {"dates": sorted(files, reverse=True)}

@app.get("/api/history/{date}")
async def get_history_by_date(date: str):
    """讀取特定日期的詳細數據"""
    file_path = os.path.join(HISTORY_DIR, f"{date}.json")
    if not os.path.exists(file_path):
        return {"error": "Date not found"}
    
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

# 全域變數追蹤當前偵察進程
current_recon_process = None

@app.post("/api/run")
async def run_recon():
    """立即執行市場偵察任務"""
    global current_recon_process
    try:
        # 如果已有在執行的進程，先嘗試停止它
        if current_recon_process and current_recon_process.poll() is None:
            current_recon_process.terminate()

        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "master_script.py")
        port = args.port if 'args' in globals() else 8005
        
        # 使用 subprocess.DEVNULL 避免 Pipe 阻塞導致進程卡死
        # 使用 python 執行，並傳遞 --port 參數確保通訊對位
        current_recon_process = subprocess.Popen(
            ["python", script_path, "--port", str(port)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        return {"status": "started", "pid": current_recon_process.pid}
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

import subprocess

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="DualBear Sentinel Dashboard Server")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    args = parser.parse_args()
    
    print(f"🚀 DualBear Dashboard Server starting on port {args.port}...")
    uvicorn.run(app, host="0.0.0.0", port=args.port, log_level="info")
