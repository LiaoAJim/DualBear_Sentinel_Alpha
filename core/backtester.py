import sqlite3
import pandas as pd
import numpy as np

class StrategyBacktester:
    def __init__(self, db_path='market_intelligence.db'):
        self.db_path = db_path

    def run_backtest(self, initial_capital=100000):
        conn = sqlite3.connect(self.db_path)
        
        # 1. 提取歷史數據 (對齊情緒與股價)
        query = """
        SELECT 
            date(r.timestamp) as date, 
            AVG(s.sentiment_score) as avg_sentiment, 
            m.price
        FROM raw_articles r
        JOIN sentiment_analysis s ON r.id = s.article_id
        JOIN market_data m ON date(r.timestamp) = m.timestamp
        GROUP BY date
        ORDER BY date ASC
        """
        df = pd.read_sql(query, conn)
        conn.close()

        if len(df) < 5:
            return "❌ 數據量不足，請累積至少 5 天的數據再進行回測。"

        # 2. 模擬交易邏輯
        df['prev_price'] = df['price'].shift(1)
        df['daily_return'] = (df['price'] - df['prev_price']) / df['prev_price']
        
        # 定義策略：情緒 > 0.4 買入，情緒 < -0.4 賣出 (模擬策略)
        # 這裡可以根據 calculator.py 的 logic 進行微調
        df['position'] = df['avg_sentiment'].apply(lambda x: 1 if x > 0.4 else (0 if x < -0.4 else 0.5))
        df['strategy_return'] = df['position'].shift(1) * df['daily_return']
        
        # 3. 計算績效指標
        df['cum_market_return'] = (1 + df['daily_return'].fillna(0)).cumprod()
        df['cum_strategy_return'] = (1 + df['strategy_return'].fillna(0)).cumprod()
        
        final_roi = (df['cum_strategy_return'].iloc[-1] - 1) * 100
        market_roi = (df['cum_market_return'].iloc[-1] - 1) * 100
        
        return {
            "total_days": len(df),
            "strategy_roi": f"{final_roi:.2f}%",
            "market_roi": f"{market_roi:.2f}%",
            "alpha": f"{(final_roi - market_roi):.2f}%",
            "win_rate": f"{(df['strategy_return'] > 0).sum() / len(df) * 100:.1f}%"
        }

if __name__ == "__main__":
    tester = StrategyBacktester()
    report = tester.run_backtest()
    print("📊 --- DualBear 策略回測報告 ---")
    print(report)