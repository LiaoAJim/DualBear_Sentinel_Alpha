import os
import sys
import subprocess

# ═══════════════════════════════════════════
# 💡 防禦性開發：自動安裝相依套件
# 說明：確保 Pillow (PIL) 已安裝，若無則自動下載，避免「沒反應」。
# ═══════════════════════════════════════════
try:
    from PIL import Image
except ImportError:
    print("[📦] 正在安裝必要套件 (Pillow)...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pillow"])
    from PIL import Image

def run_forge():
    print("==========================================")
    print("   🐻 DUALBEAR SENTINEL - EXE 鍛造程序")
    print("==========================================")
    
    try:
        # 0. 確保工作目錄正確
        app_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(app_dir)
        print(f"[📂] 工作目錄: {app_dir}")

        # 1. 圖示鍛造 (PNG -> ICO)
        input_png = "line.png"
        output_ico = "icon.ico"
        if os.path.exists(input_png):
            print(f"[🎨] 正在生成高品質圖示: {output_ico}...")
            img = Image.open(input_png)
            # 標準 Windows 圖示尺寸組合
            icon_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
            img.save(output_ico, sizes=icon_sizes)
            print("[✅] 圖示鍛造成功。")
        else:
            print(f"[⚠️] 警告：找不到 {input_png}，將不使用自定義圖示。")

        # 2. EXE 鍛造 (C# 編譯)
        # 尋找系統中的 C# 編譯器 (csc.exe)
        csc_64 = r"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe"
        csc_32 = r"C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe"
        csc = csc_64 if os.path.exists(csc_64) else csc_32
        
        if not os.path.exists(csc):
            raise Exception("找不到系統 C# 編譯器 (csc.exe)，請確保已安裝 .NET Framework 4.0+")

        if not os.path.exists("Launcher.cs"):
            raise Exception("找不到 Launcher.cs 原始碼文件。")

        print(f"[🔨] 正在編譯原生執行檔 (DualBear_Sentinel.exe)...")
        cmd = [
            csc, 
            "/target:winexe", 
            "/out:DualBear_Sentinel.exe", 
            f"/win32icon:{output_ico}" if os.path.exists(output_ico) else "",
            "/r:System.Windows.Forms.dll,System.Drawing.dll,System.dll", 
            "Launcher.cs"
        ]
        # 過濾空字串
        cmd = [c for c in cmd if c]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("[💎] EXE 鍛造成功！")
            print("---")
            print("💡 現在您可以將 'DualBear_Sentinel.exe' 釘選到任務列了。")
        else:
            print("[❌] 編譯失敗！")
            print(f"錯誤訊息：\n{result.stderr}")
            with open("forge_error.log", "w", encoding="utf-8") as f:
                f.write(result.stderr)

    except Exception as e:
        print(f"\n[🔥] 發生嚴重錯誤: {e}")
    
    print("\n==========================================")
    input("按 Enter 鍵結束程式...")

if __name__ == "__main__":
    run_forge()
