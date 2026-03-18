import os, json, requests
import time # 🚀 新增這一行：導入 time 模組！
import google.generativeai as genai # 導入新的 SDK

class SentimentAnalyzer:
    def __init__(self, api_key):
        # 1. 初始化 Google AI Studio
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash') # 🚀 採用 2.5-Flash 核心

    def analyze(self, title):
        # 2. 修改 Prompt
        prompt = f"""
        你是一位台股分析師。請分析以下標題情緒(含反串辨識): '{title}'。
        情緒分數範圍：-1.0 (極度悲觀) 到 1.0 (極度樂觀)。
        輸出 JSON 格式: {{"score": 數值, "flavor": "繁體中文簡短分析"}}
        """
        
        response = None
        try:
            response = self.model.generate_content(prompt)
            
            # 💡 防禦性處理：處理可能帶有 Markdown 代碼塊的 JSON 回傳
            raw_text = response.text
            clean_text = raw_text.replace('```json', '').replace('```', '').strip()
            
            result = json.loads(clean_text)
            
            # ✅ 分析完成後，強迫程式暫停 12 秒，符合免費層級規定
            time.sleep(12) 
            
            return result
        except Exception as e:
            print(f"❌ AI 分析過程中發生錯誤: {e}")
            if response and hasattr(response, 'text'):
                print(f"   [原始回傳]: {response.text[:100]}...")
            
            # 若失敗，也建議暫停一下，避免連續報錯
            time.sleep(5) 
            return {"score": 0, "flavor": "分析失敗"}