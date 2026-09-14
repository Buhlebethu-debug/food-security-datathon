"""
Transformation layer of the ETL pipeline.

This module:
1. Cleans the extracted datasets.
2. Standardizes country identifiers.
3. Preserves DBM survey-round information.
4. Derives DBM risk tiers.
5. Calculates the gender food-insecurity gap.
6. Merges the country-level datasets (carrying real dbm_pct through).
7. Calculates the Nutritional Resilience Index (NRI) - full 3-variable
   version (4 countries with complete data) and a simplified 2-variable
   robustness check (~14 countries, decision score + import dependency
   only, no crop diversity).
8. Produces analysis-ready tables for the load layer.
"""

import pandas as pd


def clean_dbm_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["country_original"] = df["country"].str.strip()
    df["survey_round"] = (
        df["country_original"]
        .str.extract(r"_(\d{4}[a-z]?)$", expand=False)
    )
    df["country_clean"] = (
        df["country_original"]
        .str.replace(r"_\d{4}[a-z]?$", "", regex=True)
        .str.replace(r"\s*\(.*\)", "", regex=True)
        .str.strip()
    )
    before = len(df)
    df = df.dropna(subset=["stunting_pct", "overweight_mother_pct", "dbm_pct"])
    dropped = before - len(df)
    if dropped:
        print(f"clean_dbm_data: dropped {dropped} row(s) with missing core metrics")
    return df


def flag_dbm_risk_tier(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    def tier(pct):
        if pct > 10:
            return "high"
        elif pct >= 6.7:
            return "moderate"
        return "low"
    df["dbm_risk_tier"] = df["dbm_pct"].apply(tier)
    return df


def clean_sa_province_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    latest = df.sort_values("year").groupby("province", as_index=False).tail(1)
    return latest.reset_index(drop=True)


def transform_gender_gap(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "pct_food_insecure_female_headed" in df.columns:
        df["female_headed_gap_pp"] = (
            df["pct_food_insecure_female_headed"] - df["pct_food_insecure_all"]
        )
    else:
        df["female_headed_gap_pp"] = pd.NA
    return df


def clean_empowerment_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.lower().strip() for c in df.columns]
    expected_cols = {"country", "country_code", "female_decision_score", "crop_diversity_index"}
    missing = expected_cols - set(df.columns)
    if missing:
        raise ValueError(f"clean_empowerment_data: missing expected columns {missing}")
    return df.dropna(subset=["country_code", "female_decision_score", "crop_diversity_index"])


def clean_trade_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.lower().strip() for c in df.columns]
    expected_cols = {"country_code", "net_staple_import_dependency_pct"}
    missing = expected_cols - set(df.columns)
    if missing:
        raise ValueError(f"clean_trade_data: missing expected columns {missing}")
    return df.dropna(subset=["country_code", "net_staple_import_dependency_pct"])


def calculate_nri(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["nutritional_resilience_index"] = (
        (df["female_decision_score"] * 0.4)
        + (df["crop_diversity_index"] * 100 * 0.4)
        - (df["net_staple_import_dependency_pct"] * 0.2)
    ).round(2)
    return df


def calculate_nri_simplified(df: pd.DataFrame) -> pd.DataFrame:
    """2-variable robustness check: female_decision_score and import
    dependency only (no crop diversity, since that data wasn't extended
    beyond the original 7-country set). Weighted 0.5/0.5 rather than the
    full NRI's 0.4/0.4/0.2, since there's one fewer input.

    NOTE: results should be presented alongside the full 3-variable NRI,
    not as a replacement — they're not directly comparable in scale.
    """
    df = df.copy()
    df["nri_simplified"] = (
        (df["female_decision_score"] * 0.5)
        - (df["net_staple_import_dependency_pct"] * 0.5)
    ).round(2)
    return df


def build_country_analysis_table(dbm_df, empowerment_df, trade_df) -> pd.DataFrame:
    dbm_clean = flag_dbm_risk_tier(clean_dbm_data(dbm_df))
    empowerment_clean = clean_empowerment_data(empowerment_df)
    trade_clean = clean_trade_data(trade_df)

    dbm_country_level = (
        dbm_clean.groupby(["country_code", "country_clean"], as_index=False)
        .agg(dbm_pct=("dbm_pct", "mean"))
        .rename(columns={"country_clean": "country"})
    )

    merged = pd.merge(
        dbm_country_level[["country_code", "dbm_pct"]],
        empowerment_clean, on="country_code", how="inner"
    )
    trade_for_merge = trade_clean[[
        c for c in trade_clean.columns if c != "country"
    ]]
    final_df = pd.merge(merged, trade_for_merge, on="country_code", how="inner")
    final_df = calculate_nri(final_df)
    return final_df


def build_country_analysis_table_simplified(dbm_df, decision_df, import_df) -> pd.DataFrame:
    """Builds the extended (~14-country) simplified NRI table, using the
    full 21-country DBM sample against decision + import dependency data
    only (see calculate_nri_simplified for why crop diversity is excluded).
    """
    dbm_clean = flag_dbm_risk_tier(clean_dbm_data(dbm_df))
    dbm_country_level = (
        dbm_clean.groupby(["country_code", "country_clean"], as_index=False)
        .agg(dbm_pct=("dbm_pct", "mean"))
        .rename(columns={"country_clean": "country"})
    )
    merged = pd.merge(dbm_country_level, decision_df, on="country_code", how="inner")
    merged = pd.merge(merged, import_df, on="country_code", how="inner")
    return calculate_nri_simplified(merged)


def build_sa_analysis_table(sa_df: pd.DataFrame) -> pd.DataFrame:
    sa_clean = clean_sa_province_data(sa_df)
    sa_clean = transform_gender_gap(sa_clean)
    return sa_clean[["province", "year", "pct_food_insecure_all",
                      "pct_food_insecure_female_headed", "female_headed_gap_pp"]]


def build_analysis_tables(dbm_df, sa_df, empowerment_df, trade_df) -> dict:
    country_analysis = build_country_analysis_table(dbm_df, empowerment_df, trade_df)
    sa_analysis = build_sa_analysis_table(sa_df)

    dbm_analysis = flag_dbm_risk_tier(clean_dbm_data(dbm_df))
    dbm_analysis = dbm_analysis[
        ["country_clean", "survey_round", "n", "stunting_pct",
         "overweight_mother_pct", "dbm_pct", "dbm_risk_tier"]
    ].rename(columns={"country_clean": "country"})

    return {
        "country_nutritional_resilience": country_analysis,
        "dbm_by_country": dbm_analysis,
        "sa_food_insecurity_by_province": sa_analysis
    }


if __name__ == "__main__":
    from extract_household import (
        extract_dbm_data, extract_sa_province_data,
        extract_empowerment_data, extract_trade_data
    )
    from extract import load_female_decision_score_extended, load_import_dependency_extended

    dbm = extract_dbm_data()
    sa = extract_sa_province_data()
    empowerment = extract_empowerment_data()
    trade = extract_trade_data()

    tables = build_analysis_tables(dbm, sa, empowerment, trade)

    for name, df in tables.items():
        print(f"\n=== {name} ({len(df)} rows) ===")
        print(df)

    decision_ext = load_female_decision_score_extended()
    import_ext = load_import_dependency_extended()
    simplified = build_country_analysis_table_simplified(dbm, decision_ext, import_ext)
    print(f"\n=== country_nutritional_resilience_simplified ({len(simplified)} rows) ===")
    print(simplified[['country_code', 'dbm_pct', 'female_decision_score',
                       'net_staple_import_dependency_pct', 'nri_simplified']]
          .sort_values('nri_simplified', ascending=False))

    print("\n\u2713 Transformation successful!")
