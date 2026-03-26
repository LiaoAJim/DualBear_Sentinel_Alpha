import math

class SentinelAlpha:
    """
    🛡️ 哨兵策略精算師 (SentinelAlpha) - L18 籌碼聯動版
    負責將蒐集到的市場情緒 (Sentiment) 與量化籌碼 (Quant) 轉化為戰術執行內容。
    """
    def __init__(self, risk_level="medium"):
        self.risk_level = risk_level
        self.profiles = {
            "conservative": {
                "label": "保守版",
                "base_positions": [15, 50, 40, 60, 80],
                "margin_low": 136,
                "margin_low_adj": 10,
                "margin_high": 165,
                "margin_high_adj": -15,
                "retail_hot": 30,
                "retail_cold": -30,
                "retail_hot_adj": -20,
                "retail_cold_adj": 10,
                "vix_high": 24,
                "vix_high_adj": 5,
                "vix_low": 14,
                "vix_low_adj": -10
            },
            "balanced": {
                "label": "平衡版",
                "base_positions": [25, 65, 50, 75, 95],
                "margin_low": 138,
                "margin_low_adj": 15,
                "margin_high": 168,
                "margin_high_adj": -10,
                "retail_hot": 35,
                "retail_cold": -35,
                "retail_hot_adj": -15,
                "retail_cold_adj": 15,
                "vix_high": 25,
                "vix_high_adj": 10,
                "vix_low": 15,
                "vix_low_adj": -5
            },
            "contrarian": {
                "label": "反向極端版",
                "base_positions": [35, 75, 55, 85, 100],
                "margin_low": 140,
                "margin_low_adj": 20,
                "margin_high": 170,
                "margin_high_adj": -10,
                "retail_hot": 35,
                "retail_cold": -35,
                "retail_hot_adj": -10,
                "retail_cold_adj": 20,
                "vix_high": 25,
                "vix_high_adj": 15,
                "vix_low": 15,
                "vix_low_adj": 0
            }
        }

    def calculate_position(self, sentiment_score, quant_data=None, profile="balanced"):
        """
        核心精算邏輯：
        - 基礎權重：來自 AI 新聞情緒判讀 (-1.0 to 1.0)
        - 修正權重：來自量化籌碼指標 (Quant Indicators)
        """
        profile_config = self.profiles.get(profile, self.profiles["balanced"])
        base_positions = profile_config["base_positions"]
        
        # 1. 基礎情緒判定與說明
        if sentiment_score is None:
            # 即使 AI 失敗，也給予中性基礎倉位 (50%)，但標記為分析失敗
            score = 0.0
            base_action, base_notes, base_pos = "分析失敗", "⚠️ AI 語意引擎失效", base_positions[2]
            ai_calc_str = f"AI失敗 ({base_pos}%)"
        else:
            score = sentiment_score
            if score >= 0.7:
                base_action, base_notes, base_pos = "減碼", "⚠️ 市場新聞過於燥熱", base_positions[0]
            elif score >= 0.2:
                base_action, base_notes, base_pos = "續抱", "✅ 市場氣氛偏多", base_positions[1]
            elif score > -0.2:
                base_action, base_notes, base_pos = "持平", "☕ 市場情緒中性", base_positions[2]
            elif score > -0.7:
                base_action, base_notes, base_pos = "試探佈局", "📉 市場氣氛轉趨悲觀", base_positions[3]
            else:
                base_action, base_notes, base_pos = "強勢介入", "🔥 市場進入極度恐慌", base_positions[4]
            ai_calc_str = f"AI {score:.2f} ({base_pos}%)"

        # 2. 量化修正邏輯 (反向指標)
        adjustment = 0
        quant_notes = []
        breakdown_parts = [ai_calc_str]
        
        def format_adj(adj):
            if adj == 0: return "0%"
            return f"{adj:+}%"

        if quant_data:
            # (A) 大盤融資維持率
            margin_market = quant_data.get('margin_maintenance_ratio_market', {})
            margin = margin_market.get('market')  # 使用處理後的整合值
            
            # 支援直接傳入數值的模式 (回報產生器可能直接傳入 display_quant_data)
            if margin is None:
                margin = quant_data.get('margin_maintenance_ratio')
            
            m_adj = 0
            m_str = "融維失敗"
            if isinstance(margin, (int, float)):
                if margin < profile_config["margin_low"]: 
                    m_adj = profile_config["margin_low_adj"]
                    quant_notes.append(f"🛡️ 融維低於低標 ({margin}%)")
                elif margin > profile_config["margin_high"]: 
                    m_adj = profile_config["margin_high_adj"]
                    quant_notes.append(f"⚠️ 融資槓桿偏高 ({margin}%)")
                # 如果是整數，去掉小數點
                m_val_str = f"{margin:g}"
                m_str = f"融維 {m_val_str}%"
            elif margin == "失敗":
                m_str = "融維失敗"
            
            adjustment += m_adj
            breakdown_parts.append(f"{m_str} ({format_adj(m_adj)})")

            # (B) 微台指散戶多空比
            retail = quant_data.get('retail_long_short_ratio')
            r_adj = 0
            r_str = "散戶失敗"
            if isinstance(retail, (int, float)):
                if retail > profile_config["retail_hot"]: 
                    r_adj = profile_config["retail_hot_adj"]
                    quant_notes.append(f"🚫 散戶多單過熱 ({retail})")
                elif retail < profile_config["retail_cold"]: 
                    r_adj = profile_config["retail_cold_adj"]
                    quant_notes.append(f"🚀 散戶空單群聚 ({retail})")
                r_str = f"散戶 {retail:g}%"
            elif retail == "失敗":
                r_str = "散戶失敗"
                
            adjustment += r_adj
            breakdown_parts.append(f"{r_str} ({format_adj(r_adj)})")

            # (C) VIXTWN (控慌指數)
            vix = quant_data.get('vixtwn')
            v_adj = 0
            v_str = "台VIX失敗"
            if isinstance(vix, (int, float)):
                if vix > profile_config["vix_high"]: 
                    v_adj = profile_config["vix_high_adj"]
                    quant_notes.append(f"😨 VIX 恐慌飆升 ({vix})")
                elif vix < profile_config["vix_low"]: 
                    v_adj = profile_config["vix_low_adj"]
                    quant_notes.append(f"💎 VIX 過度樂觀 ({vix})")
                v_str = f"台VIX {vix:g}"
            elif vix == "失敗":
                v_str = "台VIX失敗"
                
            adjustment += v_adj
            breakdown_parts.append(f"{v_str} ({format_adj(v_adj)})")
        else:
            # 沒有 quant_data 時補上失敗佔位符
            breakdown_parts.extend(["融維失敗 (0%)", "散戶失敗 (0%)", "台VIX失敗 (0%)"])

        # 3. 綜合精算
        final_pos_val = max(0, min(100, base_pos + adjustment))
        recon_notes = f"{base_notes} (AI:{score:.2f})。 " if sentiment_score is not None else f"{base_notes}。 "
        if quant_notes:
            recon_notes += "【籌碼監控】： " + " ".join(quant_notes)
        else:
            recon_notes += "量化籌碼處於常規區間。"

        # 建立完整計算過程字串
        calculation_breakdown = " + ".join(breakdown_parts) + f" = {final_pos_val}%"

        return {
            "action": base_action if adjustment == 0 else f"{base_action} (已修正)",
            "target_position": f"{final_pos_val}%",
            "calculation_breakdown": calculation_breakdown,
            "recon_notes": recon_notes,
            "risk_status": "HIGH" if abs(score) > 0.8 or abs(adjustment) > 20 else "NORMAL",
            "quant_adjustment": adjustment,
            "strategy_profile": profile,
            "strategy_label": profile_config["label"]
        }

    def calculate_variants(self, sentiment_score, quant_data=None):
        return {
            profile: self.calculate_position(sentiment_score, quant_data=quant_data, profile=profile)
            for profile in self.profiles
        }
