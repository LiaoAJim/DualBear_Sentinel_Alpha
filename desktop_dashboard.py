import sys
import os
import threading
import subprocess
import time
import ctypes


# ═══════════════════════════════════════════
# 💡 自檢機制：依賴完整性保護
# 說明：確保所有必要模組已安裝，若缺失則自動安裝。
# 為何使用：避免在新環境執行時直接崩潰。
# ═══════════════════════════════════════════
def _get_file_hash(filepath):
    """計算檔案的 SHA256 hash"""
    import hashlib
    with open(filepath, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def _get_record_path():
    """取得紀錄檔路徑"""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), ".sentinel_deps")

def _load_record():
    """讀取依賴檢查紀錄"""
    record_file = _get_record_path()
    if not os.path.exists(record_file):
        return {}
    try:
        import json
        with open(record_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def _save_record(req_hash):
    """儲存依賴檢查紀錄"""
    import json
    from datetime import datetime
    record_file = _get_record_path()
    with open(record_file, "w", encoding="utf-8") as f:
        json.dump({
            "requirements_hash": req_hash,
            "last_check": datetime.now().isoformat()
        }, f, indent=2)

def ensure_dependencies():
    """自動檢查並安裝 requirements.txt 中缺失的套件（智慧快取）"""
    req_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "requirements.txt")
    if not os.path.exists(req_file):
        return
    
    # 計算目前 requirements.txt 的 hash
    current_hash = _get_file_hash(req_file)
    record = _load_record()
    
    # 比對 hash：若相同表示套件無需重新檢查
    if record.get("requirements_hash") == current_hash:
        return  # 跳過，直接啟動
    
    # hash 不同或有新電腦 → 執行依賴檢查
    print("📦 檢查依賴套件...")
    with open(req_file, "r", encoding="utf-8") as f:
        packages = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    
    for pkg in packages:
        pip_name = pkg.split("==")[0]
        try:
            __import__(pip_name.replace("-", "_").replace(".", "_"))
        except ImportError:
            print(f"   安裝缺失套件: {pkg} ...")
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", pkg, "--quiet"],
                stdout=subprocess.DEVNULL
            )
            print(f"   ✅ {pkg} 安裝完成")
    
    # 更新紀錄
    _save_record(current_hash)
    print("✅ 依賴檢查完成")

ensure_dependencies()


# 依賴檢查通過後，再安全地載入 UI 模組
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QFrame, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt, QUrl, QPoint, QSize
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtGui import QIcon, QColor, QPainter

# ═══════════════════════════════════════════
# 💡 概念：AppUserModelID (正名協議)
# 說明：這是在 Windows 任務欄正確顯示應用程式身份的關鍵。
# 為何使用：避免工作列將我們的工具誤認為一般的 pythonw.exe，確保釘選功能正常。
# ═══════════════════════════════════════════
myappid = 'dualbear.sentinel.v1.0'
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

# ═══════════════════════════════════════════
# 💡 概念：無邊框 Web 封裝 (Frameless Web Wrapper)
# 說明：這是一個桌面容器，將我們的 HTML UI 封裝成原生 EXE。
# 為何使用：滿足使用者「不要伺服器感」的需求，提供一鍵點擊開啟的體驗。
# 注意事項：需要背景啟動 dashboard_server.py 並將視窗導向該位址。
# ═══════════════════════════════════════════

class AppTheme:
    BG = "#0a0c10"
    BORDER = "#1e293b"
    ACCENT = "#00d2ff"
    HEADER_BG = "rgba(10, 12, 16, 0.9)"

class SentinelApp(QMainWindow):
    def __init__(self):
        super().__init__()
        # --- 單實例檢查 (Single Instance Check) ---
        if self.check_existing_instance():
            sys.exit(0)

        # 啟動背景伺服器 (選用 8001 避免與 Nanobot 衝突)
        self.port = 8001
        self.start_server()
        
        self.initUI()
        self.old_pos = None
        self.is_maximized = False
        self.resizing = False
        self.resize_edge = None
        self.MARGIN = 10 
        self.setMouseTracking(True)

    def check_existing_instance(self):
        """檢查是否已有相同標題的視窗正在運行"""
        window_title = "DualBear Sentinel Desktop"
        hwnd = ctypes.windll.user32.FindWindowW(None, window_title)
        if hwnd:
            # 如果找到舊視窗，將其還原並提到最前方
            ctypes.windll.user32.ShowWindow(hwnd, 9) # SW_RESTORE
            ctypes.windll.user32.SetForegroundWindow(hwnd)
            return True
        return False

    def start_server(self):
        # 啟動背景伺服器 (不顯示黑框)
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        # 確保在正確目錄下啟動
        cwd = os.path.dirname(os.path.abspath(__file__))
        
        # 確保日誌目錄存在
        server_log_dir = os.path.join(cwd, "logs")
        if not os.path.exists(server_log_dir):
            os.makedirs(server_log_dir)
            
        def run_server():
            # 使用 sys.executable 確保與主進程使用同一個 Python 環境
            # 將錯誤輸出記錄到 logs/server_error.log 以供除錯
            with open(os.path.join(server_log_dir, "server_error.log"), "a", encoding="utf-8") as err_file:
                subprocess.Popen(
                    [sys.executable, "dashboard_server.py", "--port", str(self.port)],
                    cwd=cwd,
                    stdout=subprocess.DEVNULL,
                    stderr=err_file, # 捕捉伺服器崩潰原因
                    startupinfo=startupinfo
                )
        
        threading.Thread(target=run_server, daemon=True).start()

    def initUI(self):
        self.setWindowTitle("DualBear Sentinel Desktop")
        self.setWindowIcon(QIcon("icon.ico"))
        self.setFixedSize(1440, 780)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # 主容器
        self.main_container = QFrame(self)
        self.main_container.setObjectName("MainContainer")
        self.main_container.setStyleSheet(f"""
            QFrame#MainContainer {{
                background-color: {AppTheme.BG};
                border: 2px solid {AppTheme.BORDER};
                border-radius: 20px;
            }}
        """)
        self.setCentralWidget(self.main_container)

        self.layout = QVBoxLayout(self.main_container)
        self.layout.setContentsMargins(0, 0, 0, 20)
        self.layout.setSpacing(0)

        # 自定義標題列
        self.setup_header()

        # WebEngine 顯示區
        self.web_view = QWebEngineView()
        self.web_view.setStyleSheet("background: transparent;")
        
        # 等待伺服器啟動後載入
        time.sleep(1) 
        self.web_view.load(QUrl(f"http://localhost:{self.port}"))
        self.layout.addWidget(self.web_view)

    def setup_header(self):
        self.header = QFrame()
        self.header.setFixedHeight(50)
        self.header.setStyleSheet(f"background: {AppTheme.HEADER_BG}; border-top-left-radius: 18px; border-top-right-radius: 18px;")
        
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(20, 0, 10, 0)

        title_label = QLabel("🐻 DUALBEAR SENTINEL DESKTOP")
        title_label.setStyleSheet(f"color: {AppTheme.ACCENT}; font-weight: 900; font-size: 14px; letter-spacing: 1px;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()

        # 控制按鈕
        self.min_btn = QPushButton("—")
        self.max_btn = QPushButton("▢")
        self.close_btn = QPushButton("✕")
        
        for btn in [self.min_btn, self.max_btn, self.close_btn]:
            btn.setFixedSize(40, 40)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton { 
                    background: transparent; color: #fff; font-size: 18px; border: none; font-weight: bold;
                }
                QPushButton:hover { background: rgba(255,255,255,0.05); }
            """)
            header_layout.addWidget(btn)

        self.min_btn.clicked.connect(self.showMinimized)
        self.max_btn.clicked.connect(self.toggle_maximize)
        self.close_btn.clicked.connect(self.close)
        self.close_btn.setStyleSheet(self.close_btn.styleSheet() + "QPushButton:hover { color: #ff0055; }")

        self.layout.addWidget(self.header)

    def toggle_maximize(self):
        if self.is_maximized:
            self.showNormal()
            self.max_btn.setText("▢")
        else:
            self.showMaximized()
            self.max_btn.setText("❐")
        self.is_maximized = not self.is_maximized

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            edge = self.get_edge(event.pos())
            if edge:
                self.resizing = True
                self.resize_edge = edge
            elif self.header.underMouse():
                self.old_pos = event.globalPosition().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        pos = event.pos()
        if not self.resizing:
            edge = self.get_edge(pos)
            if edge == "left" or edge == "right":
                self.setCursor(Qt.CursorShape.SizeHorCursor)
            elif edge == "top" or edge == "bottom":
                self.setCursor(Qt.CursorShape.SizeVerCursor)
            elif edge in ["top-left", "bottom-right"]:
                self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            elif edge in ["top-right", "bottom-left"]:
                self.setCursor(Qt.CursorShape.SizeBDiagCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)

        if self.resizing:
            self.handle_resize(event.globalPosition().toPoint())
        elif self.old_pos:
            delta = QPoint(event.globalPosition().toPoint() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.old_pos = None
        self.resizing = False
        self.resize_edge = None
        super().mouseReleaseEvent(event)

    def get_edge(self, pos):
        w, h = self.width(), self.height()
        x, y = pos.x(), pos.y()
        m = self.MARGIN
        if x < m and y < m: return "top-left"
        if x > w - m and y > h - m: return "bottom-right"
        if x > w - m and y < m: return "top-right"
        if x < m and y > h - m: return "bottom-left"
        if x < m: return "left"
        if x > w - m: return "right"
        if y < m: return "top"
        if y > h - m: return "bottom"
        return None

    def handle_resize(self, global_pos):
        geom = self.geometry()
        if "left" in self.resize_edge:
            geom.setLeft(global_pos.x())
        if "right" in self.resize_edge:
            geom.setRight(global_pos.x())
        if "top" in self.resize_edge:
            geom.setTop(global_pos.y())
        if "bottom" in self.resize_edge:
            geom.setBottom(global_pos.y())
        
        if geom.width() >= self.minimumWidth() and geom.height() >= self.minimumHeight():
            self.setGeometry(geom)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SentinelApp()
    window.show()
    sys.exit(app.exec())
