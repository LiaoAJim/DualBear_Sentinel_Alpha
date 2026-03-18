@echo off
setlocal
cd /d "%~dp0"
echo [RUNNING] DualBear EXE Forge...
echo.

:: 1. Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found.
    pause
    exit /b
)

:: 2. Execute
python build_exe.py

if %errorlevel% neq 0 (
    echo.
    echo [FAILED] Error code: %errorlevel%
    pause
) else (
    echo.
    echo [SUCCESS] Done!
    timeout /t 3
)

endlocal
exit
