import os
import pandas as pd


# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------

_SRC_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SRC_DIR)

RAW_DIR = os.path.join(_PROJECT_ROOT, "data", "raw")

RAW_DBM_PATH = os.path.join(RAW_DIR, "dbm_country_table.csv")
RAW_SA_PROVINCE_PATH = os.path.join(
    RAW_DIR, "sa_province_food_insecurity.csv"
)
RAW_EMPOWERMENT_PATH = os.path.join(
    RAW_DIR, "women_empowerment_diversity.csv"
)
RAW_TRADE_PATH = os.path.join(
    RAW_DIR, "trade_dependency_matrix.csv"
)


# ---------------------------------------------------------------------------
# 1. Double Burden of Malnutrition (DBM)
# ---------------------------------------------------------------------------

def extract_dbm_data(path: str = RAW_DBM_PATH) -> pd.DataFrame:
    """
    Extract household-level Double Burden of Malnutrition (DBM) prevalence
    by country.

    Source:
    Bawuah et al. (2026), "Malnourished Child, Overweight Mother?
    Examining the Double Burden of Malnutrition in Sub-Saharan Africa",
    Maternal & Child Nutrition, 22(1), e70175.

    22 countries, 103,497 mother-child pairs, DHS data.
    """

    df = pd.read_csv(path)

    expected_cols = {
        "country",
        "n",
        "stunting_pct",
        "overweight_mother_pct",
        "dbm_pct"
    }

    missing = expected_cols - set(df.columns)

    if missing:
        raise ValueError(
            f"extract_dbm_data: missing expected columns {missing}"
        )

    return df


# ---------------------------------------------------------------------------
# 2. South Africa Provincial Food Insecurity
# ---------------------------------------------------------------------------

def extract_sa_province_data(
    path: str = RAW_SA_PROVINCE_PATH
) -> pd.DataFrame:
    """
    Extract South Africa provincial food insecurity rates.

    Source:
    Statistics South Africa, "Food Security in South Africa in 2019,
    2022 and 2023: Evidence from the General Household Survey"
    (Report 03-10-28), February 2025.
    """

    df = pd.read_csv(path)

    expected_cols = {
        "province",
        "year",
        "pct_food_insecure_all"
    }

    missing = expected_cols - set(df.columns)

    if missing:
        raise ValueError(
            f"extract_sa_province_data: missing expected columns {missing}"
        )

    return df


# ---------------------------------------------------------------------------
# 3. Women's Empowerment & Crop Diversity
# ---------------------------------------------------------------------------

def extract_empowerment_data(
    path: str = RAW_EMPOWERMENT_PATH
) -> pd.DataFrame:
    """
    Extract women's agricultural decision-making, crop diversity,
    and dietary diversity indicators.

    Source:
    Versioned CSV derived from published research.
    See README.md for source details.
    """

    df = pd.read_csv(path)

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
            f"extract_empowerment_data: missing expected columns {missing}"
        )

    return df


# ---------------------------------------------------------------------------
# 4. Global Trade Vulnerability
# ---------------------------------------------------------------------------

def extract_trade_data(
    path: str = RAW_TRADE_PATH
) -> pd.DataFrame:
    """
    Extract staple import dependency and food price volatility indicators.

    Source:
    Versioned CSV derived from published research.
    See README.md for source details.
    """

    df = pd.read_csv(path)

    expected_cols = {
        "country_code",
        "net_staple_import_dependency_pct",
        "food_price_volatility_index"
    }

    missing = expected_cols - set(df.columns)

    if missing:
        raise ValueError(
            f"extract_trade_data: missing expected columns {missing}"
        )

    return df


# ---------------------------------------------------------------------------
# Run extraction
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    dbm = extract_dbm_data()
    sa = extract_sa_province_data()
    empowerment = extract_empowerment_data()
    trade = extract_trade_data()

    print(f"DBM data: {len(dbm)} countries")
    print(dbm.head())

    print(f"\nSA province data: {len(sa)} rows")
    print(sa.head())

    print(f"\nWomen's empowerment data: {len(empowerment)} countries")
    print(empowerment.head())

    print(f"\nTrade vulnerability data: {len(trade)} countries")
    print(trade.head())

    print("\n✓ All datasets extracted successfully.")