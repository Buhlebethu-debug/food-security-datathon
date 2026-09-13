"""
Transformation layer of the ETL pipeline.

This module:
1. Cleans the extracted datasets.
2. Standardizes country identifiers.
3. Derives DBM risk tiers.
4. Calculates the gender food-insecurity gap.
5. Merges the country-level datasets.
6. Calculates the Nutritional Resilience Index (NRI).
7. Produces analysis-ready tables for the load layer.
"""

import pandas as pd


# ---------------------------------------------------------------------------
# 1. DBM transformations
# ---------------------------------------------------------------------------

def clean_dbm_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the DBM country table.

    - Strip survey-round suffixes from country names.
    - Drop rows with missing core DBM metrics.
    """

    df = df.copy()

    df["country_clean"] = (
        df["country"]
        .str.replace(r"\s*\(.*\)", "", regex=True)
        .str.strip()
    )

    before = len(df)

    df = df.dropna(
        subset=[
            "stunting_pct",
            "overweight_mother_pct",
            "dbm_pct"
        ]
    )

    dropped = before - len(df)

    if dropped:
        print(
            f"clean_dbm_data: dropped "
            f"{dropped} row(s) with missing core metrics"
        )

    return df


def flag_dbm_risk_tier(df: pd.DataFrame) -> pd.DataFrame:
    """
    Categorize countries according to DBM prevalence.

    low:       < 6.7%
    moderate:  6.7% - 10%
    high:      > 10%
    """

    df = df.copy()

    def tier(pct):
        if pct > 10:
            return "high"
        elif pct >= 6.7:
            return "moderate"
        return "low"

    df["dbm_risk_tier"] = df["dbm_pct"].apply(tier)

    return df


# ---------------------------------------------------------------------------
# 2. South Africa provincial food insecurity transformations
# ---------------------------------------------------------------------------

def clean_sa_province_data(
    df: pd.DataFrame
) -> pd.DataFrame:
    """
    Keep the latest available survey year for each South African province.
    """

    df = df.copy()

    latest = (
        df.sort_values("year")
        .groupby("province", as_index=False)
        .tail(1)
    )

    return latest.reset_index(drop=True)


def transform_gender_gap(
    df: pd.DataFrame
) -> pd.DataFrame:
    """
    Calculate the percentage-point gap between female-headed households
    and all households.

    If female-headed household data is unavailable, the resulting value
    remains NaN.
    """

    df = df.copy()

    # Only calculate the gap when the female-headed column exists.
    if "pct_food_insecure_female_headed" in df.columns:
        df["female_headed_gap_pp"] = (
            df["pct_food_insecure_female_headed"]
            - df["pct_food_insecure_all"]
        )
    else:
        df["female_headed_gap_pp"] = pd.NA

    return df


# ---------------------------------------------------------------------------
# 3. Women's empowerment transformations
# ---------------------------------------------------------------------------

def clean_empowerment_data(
    df: pd.DataFrame
) -> pd.DataFrame:
    """
    Clean women's empowerment and crop diversity data.
    """

    df = df.copy()

    df.columns = [
        column.lower().strip()
        for column in df.columns
    ]

    expected_cols = {
        "country",
        "country_code",
        "female_ag_decision_score",
        "crop_diversity_index",
        "dietary_diversity_score"
    }

    missing = expected_cols - set(df.columns)

    if missing:
        raise ValueError(
            f"clean_empowerment_data: missing expected columns {missing}"
        )

    return df.dropna(
        subset=[
            "country_code",
            "female_ag_decision_score",
            "crop_diversity_index",
            "dietary_diversity_score"
        ]
    )


# ---------------------------------------------------------------------------
# 4. Trade vulnerability transformations
# ---------------------------------------------------------------------------

def clean_trade_data(
    df: pd.DataFrame
) -> pd.DataFrame:
    """
    Clean staple import dependency and food price volatility data.
    """

    df = df.copy()

    df.columns = [
        column.lower().strip()
        for column in df.columns
    ]

    expected_cols = {
        "country_code",
        "net_staple_import_dependency_pct",
        "food_price_volatility_index"
    }

    missing = expected_cols - set(df.columns)

    if missing:
        raise ValueError(
            f"clean_trade_data: missing expected columns {missing}"
        )

    return df.dropna(
        subset=[
            "country_code",
            "net_staple_import_dependency_pct",
            "food_price_volatility_index"
        ]
    )


# ---------------------------------------------------------------------------
# 5. Nutritional Resilience Index
# ---------------------------------------------------------------------------

def calculate_nri(
    df: pd.DataFrame
) -> pd.DataFrame:
    """
    Calculate the Nutritional Resilience Index (NRI).

    NRI =
        40% Women's agricultural decision-making
      + 40% Crop diversity
      - 20% Staple import dependency

    Crop diversity is converted from a 0-1 index to a 0-100 scale
    before combining it with the other percentage-based indicators.
    """

    df = df.copy()

    df["nutritional_resilience_index"] = (
        (df["female_ag_decision_score"] * 0.4)
        + (df["crop_diversity_index"] * 100 * 0.4)
        - (df["net_staple_import_dependency_pct"] * 0.2)
    ).round(2)

    return df


# ---------------------------------------------------------------------------
# 6. Build country-level analysis table
# ---------------------------------------------------------------------------

def build_country_analysis_table(
    dbm_df: pd.DataFrame,
    empowerment_df: pd.DataFrame,
    trade_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Build the final country-level analysis table by merging:

    - Double Burden of Malnutrition
    - Women's empowerment and crop diversity
    - Trade dependency and food price volatility

    All datasets are joined using ISO3 country codes.
    """

    # Clean datasets
    dbm_clean = flag_dbm_risk_tier(
        clean_dbm_data(dbm_df)
    )

    empowerment_clean = clean_empowerment_data(
        empowerment_df
    )

    trade_clean = clean_trade_data(
        trade_df
    )

    # Standardize DBM country code if available
    dbm_clean.columns = [
        column.lower().strip()
        for column in dbm_clean.columns
    ]

    # Make sure country_code exists
    if "country_code" not in dbm_clean.columns:
        raise ValueError(
            "build_country_analysis_table: "
            "DBM dataset must contain 'country_code' "
            "to merge with the other country datasets."
        )

    # Merge DBM + empowerment
    merged = pd.merge(
        dbm_clean,
        empowerment_clean,
        on="country_code",
        how="inner",
        suffixes=("", "_empowerment")
    )

    # Remove duplicate country column created by the merge
    if "country_empowerment" in merged.columns:
        merged = merged.drop(
            columns=["country_empowerment"]
        )

    # Merge trade data
    final_df = pd.merge(
        merged,
        trade_clean,
        on="country_code",
        how="inner"
    )

    # Calculate NRI
    final_df = calculate_nri(final_df)

    return final_df


# ---------------------------------------------------------------------------
# 7. Build South Africa provincial analysis table
# ---------------------------------------------------------------------------

def build_sa_analysis_table(
    sa_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Build the analysis-ready South African provincial food insecurity table.
    """

    sa_clean = clean_sa_province_data(sa_df)

    sa_clean = transform_gender_gap(sa_clean)

    return sa_clean[
        [
            "province",
            "year",
            "pct_food_insecure_all",
            "pct_food_insecure_female_headed",
            "female_headed_gap_pp"
        ]
    ]


# ---------------------------------------------------------------------------
# 8. Build all analysis tables
# ---------------------------------------------------------------------------

def build_analysis_tables(
    dbm_df: pd.DataFrame,
    sa_df: pd.DataFrame,
    empowerment_df: pd.DataFrame,
    trade_df: pd.DataFrame
) -> dict:
    """
    Produce all analysis-ready tables for the load layer.

    Returns:
        {
            "country_nutritional_resilience": DataFrame,
            "dbm_by_country": DataFrame,
            "sa_food_insecurity_by_province": DataFrame
        }
    """

    country_analysis = build_country_analysis_table(
        dbm_df,
        empowerment_df,
        trade_df
    )

    sa_analysis = build_sa_analysis_table(
        sa_df
    )

    dbm_analysis = flag_dbm_risk_tier(
        clean_dbm_data(dbm_df)
    )

    dbm_analysis = dbm_analysis[
        [
            "country_clean",
            "n",
            "stunting_pct",
            "overweight_mother_pct",
            "dbm_pct",
            "dbm_risk_tier"
        ]
    ].rename(
        columns={
            "country_clean": "country"
        }
    )

    return {
        "country_nutritional_resilience": country_analysis,
        "dbm_by_country": dbm_analysis,
        "sa_food_insecurity_by_province": sa_analysis
    }


# ---------------------------------------------------------------------------
# Test transformation layer
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    from extract import (
        extract_dbm_data,
        extract_sa_province_data,
        extract_empowerment_data,
        extract_trade_data
    )

    # Extract
    dbm = extract_dbm_data()
    sa = extract_sa_province_data()
    empowerment = extract_empowerment_data()
    trade = extract_trade_data()

    # Transform
    tables = build_analysis_tables(
        dbm,
        sa,
        empowerment,
        trade
    )

    # Display results
    for name, df in tables.items():
        print(f"\n=== {name} ({len(df)} rows) ===")
        print(df)

    print("\n✓ Transformation successful!")