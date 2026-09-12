"""
extract.py
----------
Extraction layer of the ETL pipeline.

Data provenance note (important for the datathon writeup):
Both source files here are derived from published, cited research rather than
pulled live from an API. The upstream sources themselves are access-gated
(DHS/MICS microdata requires registration; some FAO endpoints are not
publicly queryable) or exist only as figures inside a published paper/report.
Extraction therefore reads from versioned CSVs in data/raw/, each of which
documents its source in a header comment. This is a deliberate design choice,
not a shortcut: it keeps the pipeline honest about what is primary vs.
secondary data. See README.md for the full source list.
"""

import os
import pandas as pd

_SRC_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SRC_DIR)

RAW_DBM_PATH = os.path.join(_PROJECT_ROOT, "data", "raw", "dbm_country_table.csv")
RAW_SA_PROVINCE_PATH = os.path.join(_PROJECT_ROOT, "data", "raw", "sa_province_food_insecurity.csv")


def extract_dbm_data(path: str = RAW_DBM_PATH) -> pd.DataFrame:
    """
    Extract household-level Double Burden of Malnutrition (DBM) prevalence
    by country.

    Source: Bawuah et al. (2026), "Malnourished Child, Overweight Mother?
    Examining the Double Burden of Malnutrition in Sub-Saharan Africa",
    Maternal & Child Nutrition, 22(1), e70175. Table 1.
    22 countries, 103,497 mother-child pairs, DHS data.
    """
    df = pd.read_csv(path)
    expected_cols = {"country", "n", "stunting_pct", "overweight_mother_pct", "dbm_pct"}
    missing = expected_cols - set(df.columns)
    if missing:
        raise ValueError(f"extract_dbm_data: missing expected columns {missing}")
    return df


def extract_sa_province_data(path: str = RAW_SA_PROVINCE_PATH) -> pd.DataFrame:
    """
    Extract South Africa provincial food insecurity rates.

    Source: Statistics South Africa, "Food Security in South Africa in 2019,
    2022 and 2023: Evidence from the General Household Survey" (Report
    03-10-28), February 2025.
    """
    df = pd.read_csv(path)
    expected_cols = {"province", "year", "pct_food_insecure_all"}
    missing = expected_cols - set(df.columns)
    if missing:
        raise ValueError(f"extract_sa_province_data: missing expected columns {missing}")
    return df


if __name__ == "__main__":
    dbm = extract_dbm_data()
    sa = extract_sa_province_data()
    print(f"DBM data: {len(dbm)} countries")
    print(dbm.head())
    print(f"\nSA province data: {len(sa)} rows")
    print(sa.head())
