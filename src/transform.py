"""
transform.py
------------
Transformation layer of the ETL pipeline.

Mirrors the pattern from the "Introduction to Data Engineering" course
structure: a cleaning step, an aggregation/derived-metrics step, and a
final step that produces the analysis-ready table the load layer writes
to Postgres.
"""

import pandas as pd


def clean_dbm_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the DBM country table.
    - Strip survey-round suffixes so repeated countries (e.g. two Malawi
      DHS rounds in the source table) are labelled consistently.
    - Drop rows with missing core metrics rather than silently imputing,
      since a fabricated value here would misrepresent a health statistic.
    """
    df = df.copy()
    df["country_clean"] = (
        df["country"]
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
    """
    Derive a categorical risk tier from dbm_pct so downstream consumers
    (e.g. a dashboard) don't need to re-derive thresholds themselves.
    Tiers follow the terciles used in the datathon's own chart work:
    low (<6.7%, the 22-country mean), moderate (6.7-10%), high (>10%).
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


def clean_sa_province_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the SA provincial table: keep the latest survey year (2023) per
    province as the primary comparison row, since that's what the rest of
    the datathon's charts use.
    """
    df = df.copy()
    latest = df.sort_values("year").groupby("province", as_index=False).tail(1)
    return latest.reset_index(drop=True)


def transform_gender_gap(sa_df: pd.DataFrame) -> pd.DataFrame:
    """
    Where a female-headed-household figure exists, compute the gap against
    the all-household rate for that province/year. Rows without a
    female-headed figure (most provinces only had the national breakdown
    at the time this pipeline was built) are kept with gap = NaN rather
    than dropped, so the table still reports total food insecurity for
    every province.
    """
    df = sa_df.copy()
    df["female_headed_gap_pp"] = (
        df["pct_food_insecure_female_headed"] - df["pct_food_insecure_all"]
    )
    return df


def build_analysis_table(dbm_df: pd.DataFrame, sa_df: pd.DataFrame) -> dict:
    """
    Final transform step, analogous to `transform_courses_to_recommend` /
    `transform_recommendations` in the course pattern: produces the
    analysis-ready tables that get loaded to Postgres.

    Returns a dict of {table_name: DataFrame} since this pipeline loads
    two related but structurally different tables, not one.
    """
    dbm_clean = flag_dbm_risk_tier(clean_dbm_data(dbm_df))
    sa_clean = transform_gender_gap(clean_sa_province_data(sa_df))
    return {
        "dbm_by_country": dbm_clean[
            ["country_clean", "n", "stunting_pct", "overweight_mother_pct",
             "dbm_pct", "dbm_risk_tier"]
        ].rename(columns={"country_clean": "country"}),
        "sa_food_insecurity_by_province": sa_clean[
            ["province", "year", "pct_food_insecure_all",
             "pct_food_insecure_female_headed", "female_headed_gap_pp"]
        ],
    }


if __name__ == "__main__":
    from extract import extract_dbm_data, extract_sa_province_data

    tables = build_analysis_table(extract_dbm_data(), extract_sa_province_data())
    for name, df in tables.items():
        print(f"\n=== {name} ({len(df)} rows) ===")
        print(df)
