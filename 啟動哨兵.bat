@echo off
title DualBear Sentinel Alpha - Booting...
echo ==========================================================
echo    🐻 DUALBEAR SENTINEL ALPHA - 啟動中...
echo ==========================================================
echo [📋] 正在檢查執行環境...

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [❌] 錯誤：找不到 Python 環境，請先安裝 Python。
    pause
    exit /b
)

echo [✅] Python 環境偵測正常。
echo.
echo [1] 🚀 執行市場偵察 (分析 & 發送 LINE 通知)
echo [2] 📊 開啟視覺化儀表板 (Dashboard)
echo [3] 🔧 修改設定 (API 金鑰 / .env)
echo [4] 📦 安裝必要套件 (pip install)
echo [Q] 離開
echo.
set /p choice="請選擇任務 (1-4): "

if "%choice%"=="1" (
    echo [📡] 正在部署偵察特工...
    python master_script.py
    pause
    goto end
)
if "%choice%"=="2" (
    echo [📊] 啟動儀表板伺服器...
    echo [💡] 啟動後請至瀏覽器開啟 http://localhost:8000
    start http://localhost:8000
    python dashboard_server.py
    pause
    goto end
)
if "%choice%"=="3" (
    echo [🔧] 開啟設定檔...
    start notepad .env
    goto end
)
if "%choice%"=="4" (
    echo [📦] 正在安裝相依套件...
    pip install -r requirements.txt
    pause
    goto end
)
if /i "%choice%"=="q" exit

:end
exit
