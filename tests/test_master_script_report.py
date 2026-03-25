import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from master_script import construct_report, build_display_quant_data


def test_construct_report_includes_formal_battle_report_fields():
    decision = {
        "action": "續抱",
        "target_position": "65%",
        "recon_notes": "市場波動降溫，維持部位。",
        "sentiment_score": 0.32,
        "failed_sources": []
    }
    quant_data = {
        "margin_maintenance_ratio": 148.2,
        "retail_long_short_ratio": 5.13,
        "vixtwn": 19.8,
        "vixus": 22.4
    }

    report = construct_report(decision, 12, quant_data)

    assert "建議倉位: 65%" in report
    assert "融資維持率: 148.20 %" in report
    assert "散戶多空比: 5.13" in report
    assert "台灣 VIX: 19.80" in report
    assert "美國 VIX: 22.40" in report
    assert "【使用建議】" in report


def test_construct_report_includes_failed_sources():
    decision = {
        "action": "爬蟲失敗",
        "target_position": "失敗",
        "recon_notes": "資料不完整，停止出手。",
        "sentiment_score": None,
        "failed_sources": ["情報來源:ptt", "美國VIX"]
    }
    quant_data = {
        "margin_maintenance_ratio": "失敗",
        "retail_long_short_ratio": 4.8,
        "vixtwn": 18.2,
        "vixus": "失敗"
    }

    report = construct_report(decision, 5, quant_data)

    assert "失敗來源: 情報來源:ptt、美國VIX" in report
    assert "建議倉位: 失敗" in report
    assert "美國 VIX: 失敗" in report
    assert "不適合單獨作為選股或槓桿依據" in report


def test_build_display_quant_data_marks_failed_fields():
    quant_data = {
        "margin_maintenance_ratio": 148.2,
        "retail_long_short_ratio": None,
        "vixtwn": 19.8,
        "vixus": None,
        "_status": {
            "margin_maintenance_ratio": "success",
            "retail_long_short_ratio": "failed",
            "vixtwn": "success",
            "vixus": "failed",
        }
    }

    display_quant = build_display_quant_data(quant_data)

    assert display_quant["margin_maintenance_ratio"] == 148.2
    assert display_quant["retail_long_short_ratio"] == "失敗"
    assert display_quant["vixtwn"] == 19.8
    assert display_quant["vixus"] == "失敗"
