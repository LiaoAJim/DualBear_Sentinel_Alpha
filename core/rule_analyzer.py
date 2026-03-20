"""
🛡️ 規則引擎情緒分析器 (Rule-based Sentiment Analyzer)
不依賴 AI API，純本地程式運算，零成本、極速、可解釋。

基於 GEM Opal 的「Jade 精算邏輯」設計：
- 詞庫加權計分 (Weighted Lexicon Scoring)
- 否定詞處理 (Negation Handling)
- 強度修飾詞 (Intensity Multipliers)
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# 嘗試載入 jieba（可選，提高分詞準確度）
try:
    import jieba
    _HAS_JIEBA = True
except ImportError:
    _HAS_JIEBA = False


class SentimentLexicon:
    """情緒詞庫管理器"""
    
    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            # 預設路徑
            base_dir = Path(__file__).parent.parent
            config_path = base_dir / "config" / "sentiment_lexicon.json"
        
        self.config_path = Path(config_path)
        self.lexicon: Dict[str, List[str]] = {}
        self.weights: Dict[str, float] = {}
        self.negators: set = set()
        self.multipliers: Dict[str, float] = {}
        self.stop_words: set = set()
        
        self.load()
    
    def load(self):
        """載入詞庫設定檔"""
        if not self.config_path.exists():
            print(f"[警告] 找不到詞庫設定檔: {self.config_path}，使用預設詞庫")
            self._load_default()
            return
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 解析各類別詞彙
            for category, data in config.get('lexicon', {}).items():
                if isinstance(data, dict):
                    weight = data.get('_weight', 1)
                    examples = data.get('_examples', [])
                else:
                    weight = 1
                    examples = data
                
                self.weights[category] = weight
                for word in examples:
                    self.lexicon[word] = weight
            
            self.negators = set(config.get('negators', []))
            self.multipliers = config.get('multipliers', {})
            self.stop_words = set(config.get('stop_words', []))
            
            # 註冊 jieba 自訂詞
            if _HAS_JIEBA:
                for word in self.lexicon.keys():
                    jieba.add_word(word)
            
            print(f"[詞庫] 已載入 {len(self.lexicon)} 個情緒詞")
            
        except Exception as e:
            print(f"[錯誤] 詞庫載入失敗: {e}")
            self._load_default()
    
    def _load_default(self):
        """載入預設詞庫（精簡版）"""
        default_lexicon = {
            "漲停": 5, "噴發": 5, "大漲": 5, "暴漲": 5,
            "買進": 3, "利多": 3, "看好": 3, "成長": 3, "獲利": 3,
            "回升": 1, "反彈": 1,
            "跌停": -5, "崩跌": -5, "血洗": -5, "斷頭": -5,
            "賣出": -3, "利空": -3, "看淡": -3, "虧損": -3, "跌破": -3,
            "整理": -1, "回檔": -1,
            "利多出盡": -2, "GG": -2,
            "填息": 2, "配息": 2, "軋空": 2
        }
        self.lexicon = default_lexicon
        self.negators = {"不", "未", "沒", "無", "非", "而非"}
        
        if _HAS_JIEBA:
            for word in self.lexicon.keys():
                jieba.add_word(word)
        
        print(f"[詞庫] 使用預設詞庫 {len(self.lexicon)} 個詞")
    
    def get_weight(self, word: str) -> float:
        """取得詞彙的權重"""
        return self.lexicon.get(word, 0)


class RuleProvider:
    """
    規則引擎情緒分析提供者
    
    特點：
    - 零成本：不需要 API Key
    - 毫秒級：本地執行，無網路延遲
    - 可解釋：每個詞的影響都清楚可見
    - 離線可用：不需要網路連線
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.lexicon = SentimentLexicon(config_path)
        self.key_hint = "規則引擎 (本地)"
    
    def analyze(self, title: str) -> dict:
        """
        分析新聞標題的情緒
        
        Args:
            title: 新聞標題
            
        Returns:
            dict: 包含 score, flavor, matched_words 等欄位
        """
        try:
            # 1. 分詞
            if _HAS_JIEBA:
                tokens = list(jieba.cut(title))
            else:
                # 簡單分詞：基於字符和常見分隔符
                tokens = self._simple_tokenize(title)
            
            # 2. 計算分數
            total_score = 0.0
            matched_words: List[Tuple[str, float, str]] = []  # (詞, 分數, 原因)
            
            i = 0
            while i < len(tokens):
                token = tokens[i]
                
                # 跳過停用詞
                if token in self.lexicon.stop_words:
                    i += 1
                    continue
                
                # 檢查修飾詞（向前看）
                multiplier = 1.0
                if i > 0 and tokens[i-1] in self.lexicon.multipliers:
                    multiplier = self.lexicon.multipliers[tokens[i-1]]
                
                # 取得詞彙分數
                base_weight = self.lexicon.get_weight(token)
                if base_weight != 0:
                    # 檢查是否被否定
                    is_negated = self._check_negation(tokens, i)
                    
                    score = base_weight * multiplier
                    if is_negated:
                        score = -score
                        reason = "否定"
                    else:
                        reason = "正向" if score > 0 else "負向"
                    
                    total_score += score
                    matched_words.append((token, score, reason))
                
                i += 1
            
            # 3. 轉換為 -1 到 1 的分數（與 AI 分數格式一致）
            # 根據 GEM Opal 的設計：規則引擎輸出 0-10 分
            # 轉換為：-1 到 1
            normalized_score = self._normalize_score(total_score)
            
            # 4. 生成情緒描述
            flavor = self._generate_flavor(total_score, matched_words)
            
            return {
                "score": normalized_score,
                "flavor": flavor,
                "provider": self.key_hint,
                "raw_score": total_score,
                "matched_words": matched_words,
                "tokens": tokens
            }
            
        except Exception as e:
            return {
                "error": True,
                "error_type": "RULE_ENGINE_ERROR",
                "msg": f"規則引擎分析失敗: {str(e)}"
            }
    
    def _simple_tokenize(self, text: str) -> List[str]:
        """簡單分詞（無 jieba 時使用）"""
        # 移除標點符號並分割
        text = re.sub(r'[，。、！？；：""''（）]', ' ', text)
        
        # 2-4 字詞滑動窗口
        tokens = []
        for length in [4, 3, 2]:
            for i in range(len(text) - length + 1):
                token = text[i:i+length].strip()
                if token and len(token) >= 2:
                    tokens.append(token)
        
        return tokens if tokens else [text]
    
    def _check_negation(self, tokens: List[str], current_idx: int) -> bool:
        """檢查是否被否定詞修飾"""
        # 向前檢查 3 個詞
        start = max(0, current_idx - 3)
        for i in range(start, current_idx):
            if tokens[i] in self.lexicon.negators:
                return True
        return False
    
    def _normalize_score(self, raw_score: float) -> float:
        """
        將原始分數正規化到 -1 到 1 的範圍
        
        設計邏輯：
        - 0 分：中性 (0.0)
        - 1-3 分：輕微正向 (0.1-0.3)
        - 4-6 分：明顯正向 (0.4-0.6)
        - 7+ 分：強烈正向 (0.7-1.0)
        負值同理
        """
        if raw_score == 0:
            return 0.0
        
        # 使用 sigmoid 類似的平滑函數
        # raw_score 範圍大約是 -15 到 +15
        normalized = raw_score / 10.0  # 簡單線性縮放
        
        # 限制在 -1 到 1 之間
        return max(-1.0, min(1.0, normalized))
    
    def _generate_flavor(self, score: float, matched_words: List[Tuple]) -> str:
        """根據分數和匹配詞彙生成情緒描述"""
        if score > 6:
            return "極度樂觀 🚀"
        elif score > 3:
            return "偏向利多 📈"
        elif score > 0:
            return "輕微樂觀 👍"
        elif score < -6:
            return "極度恐慌 💀"
        elif score < -3:
            return "偏向利空 📉"
        elif score < 0:
            return "輕微悲觀 👎"
        else:
            if matched_words:
                return "情緒複雜 ⚖️"
            return "中性 😐"


# 測試程式
if __name__ == "__main__":
    provider = RuleProvider()
    
    test_titles = [
        "台積電股價漲停，市場狂歡",
        "股市崩跌，血洗投資人",
        "利多出盡？法人悄悄撤退",
        "護盤部隊進場，股指回升",
        "GG了！半導體股價腰斬"
    ]
    
    print("\n🧪 規則引擎測試")
    print("=" * 60)
    
    for title in test_titles:
        result = provider.analyze(title)
        print(f"\n標題: {title}")
        if 'error' in result:
            print(f"  ❌ 錯誤: {result['msg']}")
        else:
            print(f"  分數: {result['score']:.2f} ({result['flavor']})")
            print(f"  原始分: {result['raw_score']:.1f}")
            if result['matched_words']:
                words = [f"{w[0]}({w[1]:+.0f})" for w in result['matched_words']]
                print(f"  命中: {', '.join(words)}")
