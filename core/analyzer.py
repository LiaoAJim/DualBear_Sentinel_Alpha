import os, json, requests
import time # 🚀 新增這一行：導入 time 模組！
import google.generativeai as genai # 導入新的 SDK

class SentimentEngine:
    def __init__(self, api_key):
        # 1. 初始化 Google AI Studio
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    def analyze(self, title):
        # 2. 修改 Prompt (這可能需要根據 Gemini 的特性微調)
        prompt = f"""
        你是一位台股分析師。請分析以下標題情緒(含反串辨識): '{title}'。
        情緒分數範圍：-1.0 (極度悲觀) 到 1.0 (極度樂觀)。
        輸出 JSON 格式: {{"score": 數值, "flavor": "繁體中文簡短分析"}}
        """
        
        try:
            response = self.model.generate_content(prompt)
            result = json.loads(response.text)
            
            # ✅ 新增這行：分析完成後，強迫程式暫停 12 秒
            # 這能確保我們符合免費層級「每分鐘 5 次」的規定
            time.sleep(12) 
            
            return result
        except Exception as e:
            # ... 錯誤處理
            # 若失敗，也建議暫停一下，避免連續報錯
            time.sleep(5) 
            return {"score": 0, "flavor": "分析失敗"}