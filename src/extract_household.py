import os
import pandas as pd

_SRC_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SRC_DIR)
RAW_DIR = os.path.join(_PROJECT_ROOT, "data", "raw")

RAW_DBM_PATH = os.path.join(RAW_DIR, "dbm_country_table.csv")
RAW_SA_PROVINCE_PATH = os.path.join(RAW_DIR, "sa_province_food_insecurity.csv")
RAW_EMPOWERMENT_PATH = os.path.join(RAW_DIR, "women_empowerment_diversity.csv")
RAW_TRADE_PATH = os.path.join(RAW_DIR, "trade_dependency_matrix.csv")


def extract_dbm_data(path: str = RAW_DBM_PATH) -> pd.DataFrame:
    df = pd.read_csv(path)
    expected_cols = {"country", "n", "stunting_pct", "overweight_mother_pct", "dbm_pct"}
    missing = expected_cols - set(df.columns)
    if missing:
        raise ValueError(f"extract_dbm_data: missing expected columns {missing}")
    return df


def extract_sa_province_data(path: str = RAW_SA_PROVINCE_PATH) -> pd.DataFrame:
    df = pd.read_csv(path)
    expected_cols = {"province", "year", "pct_food_insecure_all"}
    missing = expected_cols - set(df.columns)
    if missing:
        raise ValueError(f"extract_sa_province_data: missing expected columns {missing}")
    return df


def extract_empowerment_data(path: str = RAW_EMPOWERMENT_PATH) -> pd.DataFrame:
    df = pd.read_csv(path)
    expected_cols = {"country", "country_code", "female_decision_score", "crop_diversity_index"}
    missing = expected_cols - set(df.columns)
    if missing:
        raise ValueError(f"extract_empowerment_data: missing expected columns {missing}")
    return df


def extract_trade_data(path: str = RAW_TRADE_PATH) -> pd.DataFrame:
    df = pd.read_csv(path)
    expected_cols = {"country_code", "net_staple_import_dependency_pct"}
    missing = expected_cols - set(df.columns)
    if missing:
        raise ValueError(f"extract_trade_data: missing expected columns {missing}")
    return df


if __name__ == "__main__":
    dbm = extract_dbm_data()
    sa = extract_sa_province_data()
    empowerment = extract_empowerment_data()
    trade = extract_trade_data()
    print(f"DBM data: {len(dbm)} countries")
    print(f"SA province data: {len(sa)} rows")
    print(f"Empowerment data: {len(empowerment)} countries")
    print(f"Trade data: {len(trade)} countries")
    print("\u2713 All datasets extracted successfully.")
