import json

from core.quant_scout import QuantSentimentScout


def run_quant_recon():
    """Step 3 量化偵察獨立 runner。"""
    quant_agent = QuantSentimentScout()
    quant_data = quant_agent.fetch_all_indicators()
    quant_status = (quant_data or {}).get("_status", {})

    decision_failures = []
    if quant_status.get("margin_maintenance_ratio") != "success":
        decision_failures.append("融資")
    if quant_status.get("retail_long_short_ratio") != "success":
        decision_failures.append("散戶")
    if quant_status.get("vixtwn") != "success":
        decision_failures.append("台灣VIX")
    if quant_status.get("vixus") != "success":
        decision_failures.append("美國VIX")

    return {
        "quant_data": quant_data,
        "decision_failures": decision_failures
    }


if __name__ == "__main__":
    print(json.dumps(run_quant_recon(), ensure_ascii=False))
