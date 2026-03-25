import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import patch

from news_recon_runner import run_news_recon
from quant_recon_runner import run_quant_recon


def test_run_news_recon_returns_news_scope_only():
    fake_intelligence = [{"title": "測試新聞", "source": "PTT"}]
    fake_status = {
        "ptt": {"success": True},
        "anue": {"success": False}
    }

    with patch("news_recon_runner.DataScout") as mock_scout:
        instance = mock_scout.return_value
        instance.fetch_all_news.return_value = fake_intelligence
        instance.last_source_status = fake_status

        result = run_news_recon()

    assert result["intelligence"] == fake_intelligence
    assert result["source_status"] == fake_status
    assert result["source_failures"] == ["情報來源:anue"]


def test_run_quant_recon_returns_quant_scope_only():
    fake_quant = {
        "margin_maintenance_ratio": None,
        "retail_long_short_ratio": 5.0,
        "vixtwn": None,
        "vixus": 24.8,
        "_status": {
            "margin_maintenance_ratio": "failed",
            "retail_long_short_ratio": "success",
            "vixtwn": "failed",
            "vixus": "success"
        }
    }

    with patch("quant_recon_runner.QuantSentimentScout") as mock_scout:
        instance = mock_scout.return_value
        instance.fetch_all_indicators.return_value = fake_quant

        result = run_quant_recon()

    assert result["quant_data"] == fake_quant
    assert result["decision_failures"] == ["融資", "台灣VIX"]
