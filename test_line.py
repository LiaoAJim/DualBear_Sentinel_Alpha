import os
import requests
from dotenv import load_dotenv

# 1. 載入金鑰
load_dotenv()
TOKEN = os.getenv("LINE_NOTIFY_TOKEN")

def test_communication():
    if not TOKEN or TOKEN == "your_line_notify_token_here":
        print("❌ 錯誤：找不到 LINE_NOTIFY_TOKEN，請檢查 .env 檔案。")
        return

    url = "https://notify-api.line.me/api/notify"
    headers = {"Authorization": f"Bearer {TOKEN}"}
    data = {"message": "\n🚀 DualBear Sentinel 測試：通訊頻道運作正常！"}

    try:
        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 200:
            print("✅ 測試成功！請檢查你的 LINE。")
        else:
            print(f"❌ 測試失敗，狀態碼：{response.status_code}")
            print(f"回應內容：{response.text}")
    except Exception as e:
        print(f"❌ 發生錯誤：{e}")

if __name__ == "__main__":
    test_communication()