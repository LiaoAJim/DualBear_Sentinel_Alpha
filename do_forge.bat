@echo off
cd /d "e:\Google Drive\_DualBear\_Dev\DualBear_Sentinel_Alpha"
echo [STEP 1] Generating Icon...
python "e:\Google Drive\_DualBear\_Dev\.agent\skills\skill-png-to-ico-cli\icon_forge.py" "line.png" -o "icon.ico"
echo [STEP 2] Compiling EXE...
C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe /target:winexe /out:DualBear_Sentinel.exe /win32icon:icon.ico /r:System.Windows.Forms.dll,System.Drawing.dll,System.dll Launcher.cs
echo [DONE] Check files now.
pause
