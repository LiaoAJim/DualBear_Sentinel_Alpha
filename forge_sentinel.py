import os
import subprocess
import sys

# 🚀 雙熊鍛造爐 - Sentinel Alpha 專版
proj_dir = os.path.dirname(os.path.abspath(__file__))
# 使用 line.png 作為圖示來源
base_png = os.path.join(proj_dir, "line.png")
ico_file = os.path.join(proj_dir, "icon.ico")
exe_file = os.path.join(proj_dir, "DualBear_Sentinel.exe")
cs_file = os.path.join(proj_dir, "Launcher.cs")

# 🛠️ 核心工具路徑
forge_script = r"e:\Google Drive\_DualBear\_Dev\.agent\skills\skill-png-to-ico-cli\icon_forge.py"
csc_path_64 = r"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe"
csc_path_32 = r"C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe"
csc_exe = csc_path_64 if os.path.exists(csc_path_64) else csc_path_32

print("--- DualBear Forge [Sentinel Alpha] ---")

# 1. 圖示鍛造 (PNG -> ICO)
if os.path.exists(base_png):
    print(">>> [STEP 1] Generating high-quality icon...")
    try:
        subprocess.run([sys.executable, forge_script, base_png, "-o", ico_file], check=True)
        print(f"ICO Created: {ico_file}")
    except Exception as e:
        print(f"Icon Forge Failed: {e}")
else:
    print(f"Warning: PNG not found at {base_png}, skipping icon forge.")

# 2. EXE 鍛造 (C# Compile)
if os.path.exists(csc_exe) and os.path.exists(cs_file):
    print(">>> [STEP 2] Compiling Windows Native Launcher...")
    cmd = [
        csc_exe,
        "/target:winexe",
        f"/out:{exe_file}",
        f"/win32icon:{ico_file}" if os.path.exists(ico_file) else "",
        "/r:System.Windows.Forms.dll,System.Drawing.dll,System.dll",
        cs_file
    ]
    # Filter empty strings
    cmd = [c for c in cmd if c]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Success! Native EXE generated: {exe_file}")
        else:
            print(f"Compile Error:\n{result.stderr}")
    except Exception as e:
        print(f"Compile Failed: {e}")
else:
    print("Files missing for compilation (csc.exe or Launcher.cs).")

print("\n--- Done ---")
