import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.sentinel import SentinelAlpha


def test_calculate_variants_returns_three_profiles():
    sentinel = SentinelAlpha()
    quant_data = {
        "margin_maintenance_ratio": 136,
        "retail_long_short_ratio": 38,
        "vixtwn": 27
    }

    variants = sentinel.calculate_variants(-0.5, quant_data=quant_data)

    assert set(variants.keys()) == {"conservative", "balanced", "contrarian"}
    assert variants["conservative"]["strategy_label"] == "保守版"
    assert variants["balanced"]["strategy_label"] == "平衡版"
    assert variants["contrarian"]["strategy_label"] == "反向極端版"


def test_variant_positions_are_not_identical():
    sentinel = SentinelAlpha()
    quant_data = {
        "margin_maintenance_ratio": 136,
        "retail_long_short_ratio": -40,
        "vixtwn": 28
    }

    variants = sentinel.calculate_variants(-0.8, quant_data=quant_data)
    positions = {name: variant["target_position"] for name, variant in variants.items()}

    assert len(set(positions.values())) > 1


def test_calculate_variants_still_returns_decision_when_quant_missing():
    sentinel = SentinelAlpha()
    quant_data = {
        "margin_maintenance_ratio": None,
        "retail_long_short_ratio": None,
        "vixtwn": None,
        "vixus": None
    }

    variants = sentinel.calculate_variants(-0.35, quant_data=quant_data)

    assert variants["balanced"]["action"] in {"試探佈局", "試探佈局 (已修正)"}
    assert variants["balanced"]["target_position"].endswith("%")
