from core.backtester import StrategyBacktester

def main():
    print("🧪 啟動歷史數據回測...")
    tester = StrategyBacktester()
    results = tester.run_backtest()
    
    if isinstance(results, dict):
        print(f"📅 測試天數：{results['total_days']} 天")
        print(f"💰 策略報酬率：{results['strategy_roi']}")
        print(f"🏛️ 市場報酬率：{results['market_roi']}")
        print(f"🚀 超額報酬 (Alpha)：{results['alpha']}")
        print(f"🏆 勝率：{results['win_rate']}")
        
        alpha_val = float(results['alpha'].replace('%', ''))
        if alpha_val > 0:
            print("\n🌟 Opal 戰略建議：當前權重配方表現優於大盤，建議維持。")
        else:
            print("\n⚠️ Jade 警示：策略表現不如大盤，建議調整 calculator.py 中的加權權重。")
    else:
        print(results)

if __name__ == "__main__":
    main()