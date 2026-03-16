class StrategyCalculator:
    def __init__(self, weights={'news': 0.3, 'social': 0.5, 'macro': 0.2}):
        self.weights = weights

    def get_weighted_score(self, scores_list):
        if not scores_list: return 0
        total_w, final_s = 0, 0
        for item in scores_list:
            w = self.weights.get(item['category'], 0.1)
            final_s += item['score'] * w
            total_w += w
        return final_s / total_w if total_w > 0 else 0

    def generate_signal(self, score):
        if score > 0.7: return 0.1, "🔥 極度亢奮：建議減碼"
        if score < -0.7: return 1.0, "🚀 極度恐慌：建議重倉"
        return round((score+1)/2, 2), f"☕ 平穩期：建議持倉 {(score+1)*50:.0f}%"