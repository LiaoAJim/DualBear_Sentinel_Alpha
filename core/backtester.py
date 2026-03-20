"""
📊 規則引擎回測驗證器 (Rule Engine Backtester)

用於驗證「情緒分數是否能預測隔日股價走勢」。

基於 GEM Opal 的 Jade 精算邏輯設計：
- 取得歷史情緒分數
- 取得對應日期的股價數據
- 計算勝率與平均報酬
"""

import os
import json
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import subprocess
import sys

# 嘗試載入 yfinance
try:
    import yfinance as yf
    _HAS_YFINANCE = True
except ImportError:
    _HAS_YFINANCE = False
    print("[警告] yfinance 未安裝，將使用模擬數據")


class SentimentBacktester:
    """
    情緒分數回測器
    
    用法：
    ```python
    bt = SentimentBacktester()
    result = bt.run_backtest(symbol="2330.TW")  # 台積電
    print(result)
    ```
    """
    
    def __init__(self, history_dir: Optional[str] = None):
        if history_dir is None:
            base_dir = Path(__file__).parent.parent
            self.history_dir = base_dir / "logs" / "history"
        else:
            self.history_dir = Path(history_dir)
        
        self.symbols = {
            "台積電": "2330.TW",
            "鴻海": "2317.TW",
            "聯發科": "2454.TW",
            "大盤": "^TWII",  # 台灣加權指數
            "櫃買": "^TAIEX",  # 預設
        }
    
    def load_history(self) -> List[Dict]:
        """載入所有歷史情緒數據"""
        if not self.history_dir.exists():
            return []
        
        history_files = sorted(
            [f for f in os.listdir(self.history_dir) if f.endswith('.json')],
            reverse=True
        )
        
        all_data = []
        for filename in history_files:
            try:
                with open(self.history_dir / filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    data['_filename'] = filename
                    all_data.append(data)
            except Exception as e:
                print(f"[警告] 無法讀取 {filename}: {e}")
        
        return all_data
    
    def get_next_trading_day(self, date: datetime, exchange: str = "TW") -> datetime:
        """取得下一個交易日（跳過週末）"""
        next_day = date + timedelta(days=1)
        
        # 簡單的週末排除
        while next_day.weekday() >= 5:  # 5=Saturday, 6=Sunday
            next_day += timedelta(days=1)
        
        return next_day
    
    def get_stock_price(self, symbol: str, start_date: datetime, end_date: datetime) -> Optional[pd.DataFrame]:
        """取得股價數據"""
        if not _HAS_YFINANCE:
            return None
        
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date)
            return df if not df.empty else None
        except Exception as e:
            print(f"[警告] 無法取得 {symbol} 股價: {e}")
            return None
    
    def calculate_returns(self, prices: pd.DataFrame) -> pd.Series:
        """計算日報酬率"""
        if prices is None or prices.empty:
            return pd.Series()
        
        # 使用收盤價計算報酬
        closes = prices['Close']
        return closes.pct_change()
    
    def run_backtest(self, symbol: str = "^TWII", sentiment_threshold: float = 0.1) -> Dict:
        """
        執行回測
        
        Args:
            symbol: 股票/指數代碼 (預設: ^TWII 台灣加權指數)
            sentiment_threshold: 情緒分數閾值 (預設: 0.1)
        
        Returns:
            回測結果字典
        """
        if not _HAS_YFINANCE:
            return {
                "status": "error",
                "message": "yfinance 未安裝，無法取得股價數據",
                "install_command": "pip install yfinance"
            }
        
        history_data = self.load_history()
        
        if not history_data:
            return {
                "status": "error",
                "message": "找不到歷史情緒數據，請先執行幾次分析任務"
            }
        
        print(f"[回測] 已載入 {len(history_data)} 筆歷史數據")
        print(f"[回測] 目標: {symbol}")
        
        # 檢查是否有足夠的歷史天數
        unique_dates = set()
        for record in history_data:
            filename = record.get('_filename', '')
            date_str = filename.replace('.json', '').split('_')[0]
            unique_dates.add(date_str)
        
        if len(unique_dates) < 2:
            return {
                "status": "insufficient_data",
                "message": f"歷史資料不足：只有 {len(unique_dates)} 天資料。需要至少 2 天的歷史才能進行回測。",
                "unique_dates": list(unique_dates),
                "total_records": len(history_data),
                "suggestion": "請持續使用系統幾天後再進行回測驗證"
            }
        
        # 分析結果
        bullish_trades = []  # 情緒正向的交易
        bearish_trades = []  # 情緒負向的交易
        neutral_trades = []  # 情緒中性的交易
        
        for record in history_data:
            try:
                # 取得情緒分數
                sentiment = record.get('decision', {}).get('sentiment_score')
                if sentiment is None:
                    continue
                
                # 解析日期 (2026-03-19_174628 -> 2026-03-19)
                filename = record.get('_filename', '')
                date_str = filename.replace('.json', '').split('_')[0]
                sentiment_date = datetime.strptime(date_str, "%Y-%m-%d")
                
                # 取得隔日交易資料
                next_day = self.get_next_trading_day(sentiment_date)
                
                # 取得股價
                price_df = self.get_stock_price(
                    symbol,
                    sentiment_date,
                    next_day + timedelta(days=2)
                )
                
                if price_df is None or len(price_df) < 2:
                    continue
                
                # 計算隔日報酬
                closes = price_df['Close']
                
                # 找到 sentiment_date 和 next_day 對應的價格
                sentiment_close = None
                next_close = None
                
                for idx in closes.index:
                    # 移除時區資訊進行比較
                    idx_date = idx.tz_localize(None).date() if idx.tzinfo else idx.date()
                    if idx_date == sentiment_date.date():
                        sentiment_close = closes[idx]
                    elif idx_date == next_day.date():
                        next_close = closes[idx]
                
                if sentiment_close is None or next_close is None:
                    # 除錯：印出可用的日期
                    available_dates = [str(idx) for idx in closes.index]
                    print(f"[回測] {date_str} - 無法匹配價格。可用日期: {available_dates[:3]}")
                    continue
                
                daily_return = (next_close - sentiment_close) / sentiment_close
                
                trade = {
                    'date': date_str,
                    'sentiment': sentiment,
                    'entry_price': sentiment_close,
                    'exit_price': next_close,
                    'return': daily_return
                }
                
                # 根據情緒分數分類
                if sentiment > sentiment_threshold:
                    bullish_trades.append(trade)
                elif sentiment < -sentiment_threshold:
                    bearish_trades.append(trade)
                else:
                    neutral_trades.append(trade)
                    
            except Exception as e:
                print(f"[警告] 處理記錄失敗: {e}")
                continue
        
        # 計算統計數據
        results = {
            "status": "success",
            "symbol": symbol,
            "total_records": len(history_data),
            "valid_trades": len(bullish_trades) + len(bearish_trades) + len(neutral_trades),
            "sentiment_threshold": sentiment_threshold,
            "bullish": self._calc_stats(bullish_trades),
            "bearish": self._calc_stats(bearish_trades),
            "neutral": self._calc_stats(neutral_trades),
            "trades": {
                "bullish": bullish_trades,
                "bearish": bearish_trades,
                "neutral": neutral_trades
            }
        }
        
        return results
    
    def _calc_stats(self, trades: List[Dict]) -> Dict:
        """計算交易統計"""
        if not trades:
            return {
                "count": 0,
                "win_rate": 0,
                "avg_return": 0,
                "total_return": 0,
                "max_return": 0,
                "min_return": 0
            }
        
        returns = [t['return'] for t in trades]
        wins = sum(1 for r in returns if r > 0)
        
        return {
            "count": len(trades),
            "win_rate": wins / len(trades) * 100 if trades else 0,
            "avg_return": sum(returns) / len(returns) * 100 if returns else 0,
            "total_return": sum(returns) * 100,
            "max_return": max(returns) * 100 if returns else 0,
            "min_return": min(returns) * 100 if returns else 0
        }
    
    def run_comparison(self, symbols: List[str] = None) -> Dict:
        """對多個標的執行回測比較"""
        if symbols is None:
            symbols = ["^TWII", "2330.TW"]
        
        results = {}
        for symbol in symbols:
            results[symbol] = self.run_backtest(symbol)
        
        return results


def quick_backtest(symbol: str = "^TWII") -> Dict:
    """快速回測（供外部呼叫）"""
    tester = SentimentBacktester()
    return tester.run_backtest(symbol=symbol)


# 測試程式
if __name__ == "__main__":
    print("=" * 60)
    print("📊 規則引擎回測驗證系統")
    print("=" * 60)
    
    bt = SentimentBacktester()
    
    # 顯示可用歷史數據
    history = bt.load_history()
    print(f"\n已載入 {len(history)} 筆歷史情緒數據")
    
    if history:
        print("\n最近 3 筆記錄：")
        for record in history[:3]:
            date = record.get('_filename', 'N/A').replace('.json', '')
            sentiment = record.get('decision', {}).get('sentiment_score', 'N/A')
            stats = record.get('analysis_stats', {})
            print(f"  {date}: 情緒={sentiment}, 成功/總數={stats.get('success', 0)}/{stats.get('total', 0)}")
    
    # 執行回測
    print("\n" + "=" * 60)
    print("🔍 執行回測分析 (大盤: ^TWII)")
    print("=" * 60)
    
    result = bt.run_backtest(symbol="^TWII")
    
    if result.get('status') == 'error':
        print(f"\n❌ 回測失敗: {result.get('message')}")
        if 'install' in result:
            print(f"💡 安裝指令: {result['install_command']}")
    else:
        print(f"\n📊 回測結果摘要:")
        print(f"   總有效交易: {result['valid_trades']} 筆")
        
        print(f"\n📈 情緒正向時 (分數 > {result['sentiment_threshold']}):")
        bullish = result['bullish']
        print(f"   交易次數: {bullish['count']}")
        print(f"   勝率: {bullish['win_rate']:.1f}%")
        print(f"   平均報酬: {bullish['avg_return']:+.2f}%")
        
        print(f"\n📉 情緒負向時 (分數 < -{result['sentiment_threshold']}):")
        bearish = result['bearish']
        print(f"   交易次數: {bearish['count']}")
        print(f"   勝率: {bearish['win_rate']:.1f}%")
        print(f"   平均報酬: {bearish['avg_return']:+.2f}%")
        
        print(f"\n⚖️ 情緒中性時:")
        neutral = result['neutral']
        print(f"   交易次數: {neutral['count']}")
        print(f"   勝率: {neutral['win_rate']:.1f}%")
        print(f"   平均報酬: {neutral['avg_return']:+.2f}%")
        
        # 總結
        print("\n" + "=" * 60)
        print("🎯 結論:")
        if bullish['count'] > 0 and bearish['count'] > 0:
            if bullish['win_rate'] > bearish['win_rate']:
                print(f"   ✅ 規則引擎有效！情緒正向時勝率({bullish['win_rate']:.1f}%) > 情緒負向時({bearish['win_rate']:.1f}%)")
            else:
                print(f"   ⚠️ 規則引擎可能需要調整！情緒正向時勝率({bullish['win_rate']:.1f}%) <= 情緒負向時({bearish['win_rate']:.1f}%)")
        else:
            print(f"   ℹ️ 數據不足，需要更多歷史記錄才能得出結論")
