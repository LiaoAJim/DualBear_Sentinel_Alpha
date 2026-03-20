import os, json, requests, re
import time

# --- 導入規則引擎 ---
from core.rule_analyzer import RuleProvider

# --- 新版 Google GenAI SDK ---
try:
    from google import genai
    _USE_NEW_SDK = True
except ImportError:
    _USE_NEW_SDK = False
    import google.generativeai as genai

# --- 錯誤類型常數 ---
ERR_RATE_LIMIT    = "RATE_LIMIT"     # API 速率超限 / 當日配額耗盡
ERR_SAFETY_FILTER = "SAFETY_FILTER"  # 被安全性過濾器攔截
ERR_PARSE_FAIL    = "PARSE_FAIL"     # JSON 解析失敗
ERR_API_ERROR     = "API_ERROR"      # 其他 API 呼叫錯誤
ERR_ALL_KEYS_FAIL = "ALL_KEYS_FAIL"  # 所有 API Key 均已失敗

def _extract_json_from_text(text: str) -> dict:
    """雙熊智慧 JSON 提取器：從 AI 雜亂的回傳值中精準撈取 JSON。"""
    if not text or not isinstance(text, str):
        return None
    
    # 🕵️ 策略 1：優先尋找 Markdown JSON 區塊
    md_match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
    if md_match:
        try:
            return json.loads(md_match.group(1))
        except:
            pass

    # 🕵️ 策略 2：尋找最外層的 { } 符號
    # 📖 說明：從第一個 { 到最後一個 }，這能過濾掉 AI 前後的贅詞
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1 and end > start:
        json_str = text[start:end+1]
        try:
            # ℹ️ 注意：不要用 .replace('\n',''), 那會破壞含有換行的正常字串
            return json.loads(json_str)
        except:
            # 🕵️ 策略 3：如果還是失敗，嘗試清理掉可能的無效字元
            try:
                cleaned = re.sub(r'[\x00-\x1F\x7F]', '', json_str) # 清除控制字元
                return json.loads(cleaned)
            except:
                pass
    return None

def _safe_parse_json(content):
    """安全解析 JSON (處理已是 dict 或 string 的情況)"""
    if isinstance(content, dict):
        return content
    
    parsed = _extract_json_from_text(content)
    if parsed:
        return parsed
        
    return {"error": True, "error_type": ERR_PARSE_FAIL, "msg": f"格式異常: {str(content)[:60]}..."}

def _is_rate_limit_error(e: Exception) -> bool:
    msg = str(e).lower()
    return any(kw in msg for kw in ["429", "resource_exhausted", "quota", "rate limit", "too many requests"])

class LLMProvider:
    """抽象提供者介面"""
    def analyze(self, title: str) -> dict:
        raise NotImplementedError

class GeminiProvider(LLMProvider):
    def __init__(self, api_key):
        if _USE_NEW_SDK:
            self.client = genai.Client(api_key=api_key)
        else:
            genai.configure(api_key=api_key)
            self.model_obj = genai.GenerativeModel('gemini-2.5-flash')
        self.key_hint = f"Gemini ({api_key[:6]}...)"

    def analyze(self, title: str) -> dict:
        # 🧪 強化的提示詞：強制 AI 遵守 JSON 格式
        prompt = f"""請精準分析以下台股新聞標題的情緒權重。
標題：'{title}'
要求：
1. 僅回傳一個 JSON 格式，不准有任何前言或結語。
2. 結構：{{"score": 0.0到1.0之間, "flavor": "繁中情緒金句"}}
"""
        try:
            if _USE_NEW_SDK:
                response = self.client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt
                )
                text = response.text
            else:
                response = self.model_obj.generate_content(prompt)
                text = response.text
            
            if not text:
                return {"error": True, "error_type": ERR_SAFETY_FILTER, "msg": "被過濾器攔截"}
            
            parsed = _extract_json_from_text(text)
            if parsed: return parsed
            return {"error": True, "error_type": ERR_PARSE_FAIL, "msg": f"解析失敗: {text[:60]}"}
            
        except Exception as e:
            if _is_rate_limit_error(e):
                return {"error": True, "error_type": ERR_RATE_LIMIT, "msg": str(e)}
            return {"error": True, "error_type": ERR_API_ERROR, "msg": str(e)}

class NvidiaProvider(LLMProvider):
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://integrate.api.nvidia.com/v1/chat/completions"
        self.model   = "nvidia/llama-3.1-nemotron-ultra-253b-v1"
        self.key_hint = f"NVIDIA NIM ({api_key[:8]}...)"

    def analyze(self, title: str) -> dict:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        prompt = f"""請分析此台股新聞標題並回傳 JSON：
標題：{title}
只需回傳 JSON：{{"score": 0到1之間的分數, "flavor": "一個繁體中文字的情緒描述"}}
不要有任何其他文字。"""
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "你是一位專業的台股情緒分析師。只回傳包含 score (FLOAT) 與 flavor (STRING) 的 JSON 字串，沒有任何前言或結語。"},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 100,
            "temperature": 0.1
        }
        try:
            resp = requests.post(self.base_url, headers=headers, json=payload, timeout=20)
            if resp.status_code == 429:
                return {"error": True, "error_type": ERR_RATE_LIMIT, "msg": "NVIDIA NIM 速率限制"}
            if resp.status_code != 200:
                return {"error": True, "error_type": ERR_API_ERROR,
                        "msg": f"HTTP {resp.status_code}: {resp.text[:80]}"}
            data = resp.json()
            # 優先取 content，若為 null 再取 reasoning_content
            content = data['choices'][0]['message'].get('content')
            if not content:
                content = data['choices'][0]['message'].get('reasoning_content', '')
            
            result = _safe_parse_json(content)
            if result.get("error"):
                return result
            if "score" not in result:
                return {"error": True, "error_type": ERR_PARSE_FAIL, "msg": f"欄位缺失: {str(content)[:60]}"}
            return result
        except Exception as e:
            return {"error": True, "error_type": ERR_API_ERROR, "msg": str(e)}

class ManusProvider(LLMProvider):
    def __init__(self, api_key):
        self.api_key = api_key
        # Manus API endpoint (可能已失效，跳過檢查)
        self.base_url = "https://api.manus.ai/v1/chat/completions"
        self.model   = "manus-v1"
        self.key_hint = f"Manus ({api_key[:6]}...)"
        self._enabled = True  # 可被停用

    def analyze(self, title: str) -> dict:
        if not self._enabled:
            return {"error": True, "error_type": ERR_API_ERROR, "msg": "Manus API 已停用"}
            
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "你是一位股市情緒分析師。只回傳 JSON 格式：{\"score\": 數值, \"flavor\": \"分析\"}"},
                {"role": "user", "content": f"分析此標題：{title}"}
            ],
            "response_format": {"type": "json_object"}
        }
        try:
            resp = requests.post(self.base_url, headers=headers, json=payload, timeout=15)
            if resp.status_code == 429:
                return {"error": True, "error_type": ERR_RATE_LIMIT, "msg": "Manus 速率限制"}
            if resp.status_code == 404:
                self._enabled = False  # 停用這個 provider
                return {"error": True, "error_type": ERR_API_ERROR, "msg": "Manus API 端點不存在"}
            if resp.status_code != 200:
                return {"error": True, "error_type": ERR_API_ERROR, "msg": f"HTTP {resp.status_code}: {resp.text}"}
            
            data = resp.json()
            content = data['choices'][0]['message']['content']
            result = _safe_parse_json(content)
            if result.get("error"):
                return result
            return result
        except Exception as e:
            return {"error": True, "error_type": ERR_API_ERROR, "msg": str(e)}

class SentimentAnalyzer:
    def __init__(self, api_keys: list, preferred_provider: str = "auto", enable_rule_fallback: bool = True):
        """
        :param api_keys: API Key 列表。
        :param preferred_provider: 'auto'|'gemini'|'nvidia'|'manus'|'rule' - 指定優先使用的提供者
        :param enable_rule_fallback: 當所有 API 都失敗時，是否使用規則引擎作為最終備援
        """
        self.providers = []
        self.rule_provider = None
        
        # 初始化規則引擎（作為通用備援）
        if enable_rule_fallback:
            try:
                self.rule_provider = RuleProvider()
                print(f"[規則] 規則引擎已就緒 (本地分析，零成本)")
            except Exception as e:
                print(f"[規則] 規則引擎初始化失敗: {e}")
        
        # 根據金鑰前綴建立對應的 Provider
        for key in api_keys:
            if not key: continue
            if key.startswith("AIza"):
                self.providers.append(GeminiProvider(key))
            elif key.startswith("nvapi-"):
                self.providers.append(NvidiaProvider(key))
            elif key.startswith("sk-"):
                self.providers.append(ManusProvider(key))
        
        # 根據使用者選擇重新排序 Provider
        if preferred_provider != "auto":
            pref_map = {
                "gemini": GeminiProvider, 
                "nvidia": NvidiaProvider, 
                "manus": ManusProvider,
                "rule": None  # 特殊處理
            }
            
            if preferred_provider == "rule":
                # 使用者選擇只使用規則引擎
                if self.rule_provider:
                    # 🛡️ 重要：清除所有 API providers，只保留規則引擎
                    self.providers = [self.rule_provider]
                    print(f"[規則] 已將規則引擎設為唯一引擎（API providers 已排除）")
                    self.current_provider_index = 0
                    self._log_status()
                    return
            else:
                pref_cls = pref_map.get(preferred_provider)
                if pref_cls:
                    preferred = [p for p in self.providers if isinstance(p, pref_cls)]
                    others    = [p for p in self.providers if not isinstance(p, pref_cls)]
                    self.providers = preferred + others
                    print(f"[AI] 使用者指定優先引擎：{preferred_provider}")

        # 如果沒有 API providers 且有規則引擎，直接使用規則引擎
        if not self.providers and self.rule_provider:
            self.providers.append(self.rule_provider)
        
        self.current_provider_index = 0
        if not self.providers:
            raise ValueError("[ERROR] 沒有可用的分析提供者（請確認 API Key 或規則引擎是否可用）")
        self._log_status()

    def _log_status(self):
        p = self.providers[self.current_provider_index]
        print(f"[AI] 當前情緒大腦：{p.key_hint}")

    def _rotate(self) -> bool:
        if self.current_provider_index + 1 < len(self.providers):
            self.current_provider_index += 1
            p = self.providers[self.current_provider_index]
            print(f"[AI] 已切換備援引擎：{p.key_hint}")
            return True
        return False

    def analyze(self, title: str) -> dict:
        """雙熊情緒分析：具備自動輪換與來源標示功能。"""
        max_retries = len(self.providers)
        attempts = 0
        while attempts < max_retries:
            attempts += 1
            p = self.providers[self.current_provider_index]
            result = p.analyze(title)
            
            if result.get("error"):
                e_type = result.get("error_type")
                e_msg  = str(result.get("msg", ""))

                # 💡 自動輪換：當發生配額耗盡、解析失敗、或是 API 4XX 錯誤時，自動換一個 AI 試試看
                # 注意：規則引擎的錯誤不應該觸發輪換（它是最後防線）
                if "RULE_ENGINE" not in e_type and (e_type == ERR_RATE_LIMIT or e_type == ERR_PARSE_FAIL or "4" in e_msg):
                    old_hint = p.key_hint
                    if self._rotate():
                        new_hint = self.providers[self.current_provider_index].key_hint
                        print(f"🔄 [AI 換手] {old_hint} 任務失敗({e_type}) -> 正由 {new_hint} 備援接手分析任務...")
                        time.sleep(1)
                        continue
                    else:
                        # 嘗試使用規則引擎
                        if self.rule_provider and self.rule_provider != p:
                            self.providers.append(self.rule_provider)
                            self.current_provider_index = len(self.providers) - 1
                            print(f"🔄 [規則] API 全滅，自動切換至規則引擎...")
                            continue
                        return {"error": True, "error_type": ERR_ALL_KEYS_FAIL, "msg": f"AI 陣容全滅 (最後一位: {old_hint})"}
                return result 
            
            # --- 🛡️ 解析成功：回傳並附帶標註分析來源 ---
            result["provider"] = p.key_hint
            time.sleep(0.5)
            return result
        return {"error": True, "error_type": ERR_ALL_KEYS_FAIL, "msg": "已嘗試所有可用分析資源，均解析失敗"}