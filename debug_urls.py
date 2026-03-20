import requests

urls = [
    "https://www.ptt.cc/bbs/Stock/index.html",
    "https://api.cnyes.com/media/api/v1/newslist/category/tw_stock?limit=10",
    "https://tw.stock.yahoo.com/news/",
    "https://news.cnyes.com/api/v1/newslist/category/tw_stock?limit=10"
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

for u in urls:
    try:
        res = requests.get(u, headers=headers, timeout=5)
        print(f"{u} -> {res.status_code}")
    except Exception as e:
        print(f"{u} -> ERROR: {e}")
