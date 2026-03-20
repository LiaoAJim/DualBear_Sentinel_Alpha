"""
📊 VIX 恐慌指數偵測器 (VIX Scout)

取得美國 CBOE VIX 恐慌指數，用於評估市場風險情緒。

VIX 計算方式說明：
- 由 CBOE 根據 S&P 500 選擇權報價計算
- 代表市場對未來 30 天波動率的預期
- VIX > 25 通常表示市場緊張

使用 yfinance 取得資料，無需額外 API Key。
"""

import yfinance as yf
from datetime import datetime
from typing import Dict, Optional


class VIXScout:
    """
    VIX 恐慌指數偵測器
    
    用法：
    ```python
    scout = VIXScout()
    vix_data = scout.fetch()
    print(f"VIX: {vix_data['value']:.2f}")
    ```
    """
    
    def __init__(self):
        self.symbol = "^VIX"  # 美國 VIX
        self.symbol_china = "000188.SS"  # 上海 VIX（備用）
        self.name = "CBOE VIX"
    
    def fetch(self) -> Dict:
        """
        取得 VIX 資料
        
        Returns:
            dict: 包含 value, change, change_pct, timestamp, status
        """
        result = {
            "name": self.name,
            "symbol": self.symbol,
            "value": None,
            "change": None,
            "change_pct": None,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "status": "success",
            "interpretation": "unknown"
        }
        
        try:
            ticker = yf.Ticker(self.symbol)
            df = ticker.history(period="5d")  # 取最近 5 天
            
            if df.empty:
                result["status"] = "error"
                result["message"] = "無法取得 VIX 資料"
                return result
            
            # 取得最新收盤價
            current = df['Close'].iloc[-1]
            result["value"] = round(current, 2)
            
            # 計算變動
            if len(df) >= 2:
                previous = df['Close'].iloc[-2]
                change = current - previous
                result["change"] = round(change, 2)
                result["change_pct"] = round((change / previous) * 100, 2) if previous != 0 else 0
            
            # 解讀 VIX 數值
            result["interpretation"] = self._interpret(current)
            
        except Exception as e:
            result["status"] = "error"
            result["message"] = str(e)
        
        return result
    
    def _interpret(self, value: float) -> str:
        """
        根據 VIX 數值解讀市場情緒
        
        Args:
            value: VIX 數值
            
        Returns:
            str: 情緒解讀
        """
        if value < 15:
            return "極度樂觀"
        elif value < 20:
            return "偏樂觀"
        elif value < 25:
            return "中性觀望"
        elif value < 30:
            return "輕度恐慌"
        elif value < 40:
            return "中度恐慌"
        else:
            return "高度恐慌"
    
    def get_sentiment_factor(self) -> float:
        """
        取得 VIX 情緒因子（用於決策調整）
        
        Returns:
            float: -1 到 1 的調整因子
            - 負值：市場緊張，提高倉位警覺
            - 正值：市場平靜，可以適度積極
        """
        vix = self.fetch()
        if vix["value"] is None:
            return 0.0
        
        value = vix["value"]
        
        # VIX > 30：恐慌環境，傾向保守 (-0.2)
        # VIX 25-30：緊張環境 (-0.1)
        # VIX 15-25：正常環境 (0)
        # VIX < 15：極度平靜 (+0.1)
        
        if value >= 40:
            return -0.3
        elif value >= 30:
            return -0.2
        elif value >= 25:
            return -0.1
        elif value >= 15:
            return 0.0
        else:
            return 0.1
    
    def fetch_multiple(self) -> Dict[str, Dict]:
        """
        取得多個恐慌指數
        
        Returns:
            dict: 各指數的資料
        """
        results = {}
        
        # 美國 VIX
        results["us_vix"] = self.fetch()
        
        # 嘗試中國 VIX（可能失敗）
        try:
            ticker_cn = yf.Ticker(self.symbol_china)
            df_cn = ticker_cn.history(period="5d")
            if not df_cn.empty:
                current = df_cn['Close'].iloc[-1]
                results["china_vix"] = {
                    "name": "上海 VIX",
                    "symbol": self.symbol_china,
                    "value": round(current, 2),
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "status": "success"
                }
        except:
            results["china_vix"] = {
                "name": "上海 VIX",
                "status": "unavailable",
                "message": "無法取得中國 VIX 資料"
            }
        
        return results


# 測試程式
if __name__ == "__main__":
    scout = VIXScout()
    
    print("=" * 50)
    print("📊 VIX 恐慌指數偵測")
    print("=" * 50)
    
    # 單一 VIX
    result = scout.fetch()
    
    if result["status"] == "success":
        print(f"\n指數名稱: {result['name']}")
        print(f"代碼: {result['symbol']}")
        print(f"當前數值: {result['value']:.2f}")
        print(f"變動: {result['change']:+.2f} ({result['change_pct']:+.2f}%)")
        print(f"情緒解讀: {result['interpretation']}")
        print(f"\n🧠 情緒因子: {scout.get_sentiment_factor():+.1f}")
    else:
        print(f"\n❌ 取得失敗: {result.get('message', '未知錯誤')}")
    
    # 多指數
    print("\n" + "=" * 50)
    print("🌍 多市場 VIX")
    print("=" * 50)
    
    multi = scout.fetch_multiple()
    for key, data in multi.items():
        if data["status"] == "success":
            print(f"\n{data['name']}: {data['value']:.2f}")
        else:
            print(f"\n{data['name']}: {data.get('message', '無法取得')}")
