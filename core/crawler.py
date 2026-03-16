import requests
from bs4 import BeautifulSoup

class DataScout:
    def __init__(self):
        self.headers = {'User-Agent': 'Mozilla/5.0'}
        self.ptt_cookies = {'over18': '1'}

    def get_ptt_stock(self, limit=10):
        url = "https://www.ptt.cc/bbs/Stock/index.html"
        articles = []
        try:
            res = requests.get(url, headers=self.headers, cookies=self.ptt_cookies)
            soup = BeautifulSoup(res.text, 'html.parser')
            for item in soup.select('.r-ent')[:limit]:
                title_tag = item.select('.title a')
                if title_tag:
                    articles.append({'title': title_tag[0].text.strip(), 'url': "https://www.ptt.cc" + title_tag[0]['href'], 'category': 'social'})
            return articles
        except: return []

    def get_anue_news(self, limit=10):
        url = f"https://api.cnyes.com/media/api/v1/newslist/category/tw_stock?limit={limit}"
        try:
            res = requests.get(url)
            return [{'title': item['title'], 'url': f"https://news.cnyes.com/news/id/{item['newsId']}", 'category': 'news'} for item in res.json()['items']['data']]
        except: return []