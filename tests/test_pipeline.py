"""
Lightweight smoke tests for the extract/transform layers — no live
Postgres connection required, so these can run in CI on every push.
The load layer is exercised separately in etl.py against a real database.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from extract_household import extract_dbm_data, extract_sa_province_data
from transform_household import build_analysis_tables
from extract_household import extract_empowerment_data, extract_trade_data


def test_extract_dbm_data_has_22_countries():
    df = extract_dbm_data()
    assert len(df) == 22


def test_extract_sa_province_data_not_empty():
    df = extract_sa_province_data()
    assert len(df) > 0


def test_transform_produces_expected_tables():
    dbm_raw = extract_dbm_data()
    sa_raw = extract_sa_province_data()
    empowerment_raw = extract_empowerment_data()
    trade_raw = extract_trade_data()
    tables = build_analysis_tables(dbm_raw, sa_raw, empowerment_raw, trade_raw)
    assert set(tables.keys()) == {
        "country_nutritional_resilience",
        "dbm_by_country",
        "sa_food_insecurity_by_province",
    }


def test_dbm_risk_tier_values_are_valid():
    dbm_raw = extract_dbm_data()
    sa_raw = extract_sa_province_data()
    empowerment_raw = extract_empowerment_data()
    trade_raw = extract_trade_data()
    tables = build_analysis_tables(dbm_raw, sa_raw, empowerment_raw, trade_raw)
    valid_tiers = {"low", "moderate", "high"}
    assert set(tables["dbm_by_country"]["dbm_risk_tier"].unique()) <= valid_tiers


def test_lesotho_flagged_high_risk():
    # Lesotho has the highest DBM prevalence in the source data (18.1%) —
    # a regression here would signal a broken transform.
    dbm_raw = extract_dbm_data()
    sa_raw = extract_sa_province_data()
    empowerment_raw = extract_empowerment_data()
    trade_raw = extract_trade_data()
    tables = build_analysis_tables(dbm_raw, sa_raw, empowerment_raw, trade_raw)
    row = tables["dbm_by_country"].query("country == 'Lesotho'").iloc[0]
    assert row["dbm_risk_tier"] == "high"