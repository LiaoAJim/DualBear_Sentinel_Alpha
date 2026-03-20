@echo off
title DualBear Sentinel Alpha
pushd "%~dp0"

:menu
echo.
echo ===========================================================
echo    DUALBEAR SENTINEL ALPHA - Command Center
echo ===========================================================
echo.
echo   [1] Run Market Recon (Analysis + LINE Notify)
echo   [2] Open Dashboard (http://localhost:8001/sentinel-alpha)
echo   [3] Edit Settings (.env)
echo   [4] Install / Update Packages
echo   [Q] Quit
echo.
set /p choice=Select task (1-4 / Q): 

if "%choice%"=="1" goto recon
if "%choice%"=="2" goto dashboard
if "%choice%"=="3" goto settings
if "%choice%"=="4" goto install
if /i "%choice%"=="Q" goto quit
echo [WARN] Invalid option. Try again.
goto menu

:recon
echo.
echo [START] Launching market recon agent...
python master_script.py
echo.
echo [DONE] Recon complete.
pause
goto menu

:dashboard
echo.
echo [START] Starting dashboard server...
echo [INFO]  Open browser at http://localhost:8001/sentinel-alpha
start http://localhost:8001/sentinel-alpha
python dashboard_server.py --port 8001
echo.
echo [DONE] Dashboard closed.
pause
goto menu

:settings
echo.
echo [INFO] Opening .env config file...
start notepad .env
goto menu

:install
echo.
echo [START] Installing packages...
pip install -r requirements.txt
echo.
echo [DONE] Install complete.
pause
goto menu

:quit
echo.
echo [EXIT] See you next time!
popd
exit /b
