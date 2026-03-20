import requests
import json

url = "https://news.cnyes.com/api/v1/newslist/category/tw_stock?limit=3"
try:
    res = requests.get(url, timeout=10)
    data = res.json()
    print("--- 原始 JSON 概覽 ---")
    print(json.dumps(data, indent=2, ensure_ascii=False)[:1000])
    
    # 🕵️ 測試層級搜尋
    print("\n--- 結構偵察 ---")
    if 'items' in data:
        print("Found 'items'")
        if 'data' in data['items']:
            print(f"Found 'items' -> 'data' (Count: {len(data['items']['data'])})")
    elif 'data' in data:
        print("Found top-level 'data'")
        if 'items' in data['data']:
             print(f"Found 'data' -> 'items' (Count: {len(data['data']['items'])})")
except Exception as e:
    print(f"Error: {e}")
