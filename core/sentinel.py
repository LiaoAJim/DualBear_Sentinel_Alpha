import math

class SentinelAlpha:
    """
    🛡️ 哨兵策略精算師 (SentinelAlpha) - L18 籌碼聯動版
    負責將蒐集到的市場情緒 (Sentiment) 與量化籌碼 (Quant) 轉化為戰術執行內容。
    """
    def __init__(self, risk_level="medium"):
        self.risk_level = risk_level

    def calculate_position(self, sentiment_score, quant_data=None):
        """
        核心精算邏輯：
        - 基礎權重：來自 AI 新聞情緒判讀 (-1.0 to 1.0)
        - 修正權重：來自量化籌碼指標 (Quant Indicators)
        """
        if sentiment_score is None:
            return {
                "action": "分析失敗",
                "target_position": "--%",
                "recon_notes": "⚠️ AI 語意引擎目前無法讀取市場情緒，請檢查網路連線或 API Key 額度。",
                "risk_status": "ERROR",
                "quant_adjustment": 0
            }

        score = sentiment_score
        
        # 1. 基礎情緒判定與說明
        if score >= 0.7:
            base_action, base_notes, base_pos = "減碼", "⚠️ 市場新聞過於燥熱", 25
        elif score >= 0.2:
            base_action, base_notes, base_pos = "續抱", "✅ 市場氣氛偏多", 65
        elif score > -0.2:
            base_action, base_notes, base_pos = "持平", "☕ 市場情緒中性", 50
        elif score > -0.7:
            base_action, base_notes, base_pos = "試探佈局", "📉 市場氣氛轉趨悲觀", 75
        else:
            base_action, base_notes, base_pos = "強勢介入", "🔥 市場進入極度恐慌", 95

        # 2. 量化修正邏輯 (反向指標)
        adjustment = 0
        quant_notes = []
        
        if quant_data:
            # (A) 大盤融資維持率
            margin = quant_data.get('margin_maintenance_ratio')
            if margin:
                if margin < 138: 
                    adjustment += 15
                    quant_notes.append(f"🛡️ 融維低於低標 ({margin}%)")
                elif margin > 168: 
                    adjustment -= 10
                    quant_notes.append(f"⚠️ 融資槓桿偏高 ({margin}%)")

            # (B) 微台指散戶多空比
            retail = quant_data.get('retail_long_short_ratio')
            if retail is not None:
                if retail > 35: 
                    adjustment -= 15
                    quant_notes.append(f"🚫 散戶多單過熱 ({retail})")
                elif retail < -35: 
                    adjustment += 15
                    quant_notes.append(f"🚀 散戶空單群聚 ({retail})")

            # (C) VIXTWN (控慌指數)
            vix = quant_data.get('vixtwn')
            if vix:
                if vix > 25: 
                    adjustment += 10
                    quant_notes.append(f"😨 VIX 恐慌飆升 ({vix})")
                elif vix < 15: 
                    adjustment -= 5
                    quant_notes.append(f"💎 VIX 過度樂觀 ({vix})")

        # 3. 綜合精算
        final_pos_val = max(0, min(100, base_pos + adjustment))
        recon_notes = f"{base_notes} (AI:{score:.2f})。 "
        if quant_notes:
            recon_notes += "【籌碼監控】： " + " ".join(quant_notes)
        else:
            recon_notes += "量化籌碼處於常規區間。"

        return {
            "action": base_action if adjustment == 0 else f"{base_action} (已修正)",
            "target_position": f"{final_pos_val}%",
            "recon_notes": recon_notes,
            "risk_status": "HIGH" if abs(score) > 0.8 or abs(adjustment) > 20 else "NORMAL",
            "quant_adjustment": adjustment
        }
