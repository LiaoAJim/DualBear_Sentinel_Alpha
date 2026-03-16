import os
import requests
import json
from dotenv import load_dotenv

# 1. 載入全新的金鑰與識別碼
load_dotenv()
ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
USER_ID = os.getenv("YOUR_USER_ID")

def test_communication():
    if not ACCESS_TOKEN or not USER_ID or ACCESS_TOKEN == "your_new_...":
        print("❌ 錯誤：找不到金鑰或 User ID，請檢查 .env 檔案。")
        return

    # 2. 修改 API 網址為 Messaging API 的傳送訊息路徑
    url = "https://api.line.me/v2/bot/message/push"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ACCESS_TOKEN}" # 使用全新的 Bearer 認證
    }
    
    # 3. 修改資料格式，Messaging API 需要 JSON 格式並包含 UserId 與訊息內容
    data = {
        "to": USER_ID,
        "messages": [
            {
                "type": "text",
                "text": "🚀 DualBear Sentinel 測試：Messaging API 通訊頻道運作正常！"
            }
        ]
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        if response.status_code == 200:
            print("✅ 測試成功！請檢查您的 LINE。")
        else:
            print(f"❌ 測試失敗，狀態碼：{response.status_code}")
            print(f"回應內容：{response.text}")
    except Exception as e:
        print(f"❌ 發生錯誤：{e}")

if __name__ == "__main__":
    test_communication()