import requests
from bs4 import BeautifulSoup
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def test_source(name, url, is_json=True):
    print(f"\n--- 測試來源: {name} ---")
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        print(f"Status Code: {res.status_code}")
        if is_json:
            data = res.json()
            print(f"JSON Keys: {list(data.keys())}")
            # 偵測鉅亨網特定層級
            if 'data' in data: print(f"  - data keys: {list(data['data'].keys())}")
            if 'items' in data: print(f"  - items type: {type(data['items'])}")
        else:
            soup = BeautifulSoup(res.text, 'html.parser')
            print(f"HTML Length: {len(res.text)}")
            # 測試 PTT 結構
            if "ptt.cc" in url:
                titles = soup.select('.r-ent .title a')
                print(f"  - PTT Titles Found: {len(titles)}")
            # 測試 Yahoo 結構
            if "yahoo" in url:
                titles = soup.select('ul > li.Py\(14px\) a')
                print(f"  - Yahoo Titles Found: {len(titles)}")
    except Exception as e:
        print(f"FAILED: {e}")

test_source("CNYE (鉅亨)", "https://news.cnyes.com/api/v1/newslist/category/tw_stock?limit=5")
test_source("PTT Stock", "https://www.ptt.cc/bbs/Stock/index.html", is_json=False)
test_source("Yahoo (股市)", "https://tw.stock.yahoo.com/news/", is_json=False)
