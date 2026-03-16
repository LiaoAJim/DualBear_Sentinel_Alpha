import json, requests

class SentimentEngine:
    def __init__(self, api_key):
        self.api_key = api_key
        self.url = "https://api.openai.com/v1/chat/completions"

    def analyze(self, title):
        prompt = f"分析台股標題情緒(含反串辨識): '{title}'。輸出JSON: {{'score': -1.0 to 1.0, 'flavor': '簡短分析'}}"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {"model": "gpt-4o-mini", "messages": [{"role": "user", "content": prompt}], "response_format": {"type": "json_object"}}
        try:
            res = requests.post(self.url, headers=headers, json=payload)
            return json.loads(res.json()['choices'][0]['message']['content'])
        except: return {"score": 0, "flavor": "分析失敗"}