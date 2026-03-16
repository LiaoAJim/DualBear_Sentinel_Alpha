import math

class SentinelAlpha:
    """
    🛡️ 哨兵策略精算師 (SentinelAlpha) - L11 規範實作版
    負責將蒐集到的市場情緒 (Sentiment) 轉化為具體的戰術執行建議。
    """
    def __init__(self, risk_level="medium"):
        self.risk_level = risk_level

    def calculate_position(self, sentiment_score):
        """
        核心精算邏輯：
        - 本系統採用的戰術是「逆向情緒規律 + 趨勢權重」。
        - 1.0 (極度樂觀): 可能是過熱訊號，持倉不宜過高。
        - -1.0 (極度悲觀): 可能是超跌區，具備進場價值。
        """
        score = sentiment_score
        
        # 🛡️ 戰術計算：基於雙熊 L11 精算公式
        # 我們假設情緒分數 -1 到 1 代表市場呼吸節奏。
        if score >= 0.7:
            action = "減碼 / 出脫"
            recon_notes = "⚠️ 市場情過於燥熱 (得分: {:.2f})，多數標題呈現追價情緒，規律提示此處不宜追高。".format(score)
            target_pos = "20-30%"
        elif score >= 0.2:
            action = "續抱 / 觀察"
            recon_notes = "✅ 市場氣氛偏多 (得分: {:.2f})，情緒平穩發展，屬健康趨勢。".format(score)
            target_pos = "50-70%"
        elif score > -0.2:
            action = "持平 / 觀望"
            recon_notes = "☕ 市場情緒中性 (得分: {:.2f})，多空資訊交雜，建議靜待規律表態。".format(score)
            target_pos = "50%"
        elif score > -0.7:
            action = "試探性分批佈局"
            recon_notes = "📉 市場氣氛轉趨悲觀 (得分: {:.2f})，規律顯示恐慌正在蔓延，是尋找優質資產的時機。".format(score)
            target_pos = "60-80%"
        else:
            action = "強勢介入 / 重倉"
            recon_notes = "🔥 市場進入極度恐慌區 (得分: {:.2f})，偵察顯示市場已出現非理性拋售，規律覺醒，勇敢進場。".format(score)
            target_pos = "90%+"

        return {
            "action": action,
            "target_position": target_pos,
            "recon_notes": recon_notes,
            "risk_status": "HIGH" if abs(score) > 0.8 else "NORMAL"
        }
