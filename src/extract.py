import os
import numpy as np
import pandas as pd

TARGET_COUNTRIES = {
    "Malawi": "MWI",
    "United Republic of Tanzania": "TZA",
    "Burkina Faso": "BFA",
    "Ghana": "GHA",
    "India": "IND",
    "Timor-Leste": "TLS",
    "South Africa": "ZAF",
}

RAW_DIR = "data/external"
OUT_DIR = "data/raw"

DBM_SCORE_MAP = {
    "No DBM": 0,
    "DBM at >20% overweight prevalence": 1,
    "DBM at >30% overweight prevalence": 2,
    "DBM at >40% overweight prevalence": 3,
}

# FAOSTAT QCL includes livestock/animal products alongside crops.
# Excluded here so crop_diversity_index measures crop diversity specifically,
# matching the claim made in the presentation ("domestic crop diversity").
LIVESTOCK_AND_PROCESSED_KEYWORDS = [
    "meat of", "fat,", "fat of", "milk", "cheese", "butter", "ghee", "cream",
    "whey", "eggs", "edible offal", "hides and skins", "wool", "beeswax",
    "honey", "game meat", "horse meat", "silk-worm", "raw silk", "oil of",
    " oil,", "beer of", "wine", "molasses", "margarine", "tallow",
]


def _require(path):
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Missing real data file: {path}. "
            "See README.md 'Data Sources' section for download instructions. "
            "No mock/synthetic fallback is used."
        )
    return path


def load_import_dependency():
    """Source: FAOSTAT via Food Systems Dashboard (Cereal import dependency ratio)."""
    df = pd.read_csv(_require(f"{RAW_DIR}/faostat_import_dependency.csv"))
    df = df.sort_values("End Year").groupby("ISO3").tail(1)
    df = df.rename(columns={
        "Country": "country",
        "ISO3": "country_code",
        "Value": "net_staple_import_dependency_pct",
        "End Year": "import_data_year",
    })
    return df[["country", "country_code", "net_staple_import_dependency_pct", "import_data_year"]]


def load_female_decision_score():
    """Source: World Bank WDI, indicator SG.DMK.ALLD.FN.ZS (DHS-based).

    NOTE: measures women's participation in the three household decisions
    (own health care, major household purchases, visits to family) —
    general household decision-making, NOT agriculture-specific.
    """
    df = pd.read_csv(_require(f"{RAW_DIR}/worldbank_decision_index.csv"), skiprows=4)
    target_codes = list(TARGET_COUNTRIES.values())
    df = df[df["Country Code"].isin(target_codes)]
    year_cols = [c for c in df.columns if c.isdigit()]

    records = []
    for _, row in df.iterrows():
        valid = [(int(y), row[y]) for y in year_cols if pd.notna(row[y])]
        if not valid:
            continue
        latest_year, latest_val = max(valid, key=lambda x: x[0])
        records.append({
            "country": row["Country Name"],
            "country_code": row["Country Code"],
            "female_decision_score": latest_val,
            "decision_data_year": latest_year,
        })
    return pd.DataFrame(records)


def load_dbm():
    """Source: Food Systems Dashboard, 'Double burden of malnutrition'
    (Popkin et al. 2020). Categorical, NOT a percentage — country
    classifications are based on 2010 survey data (dataset's most recent
    published year). This limitation should be disclosed in the presentation.
    """
    df = pd.read_csv(_require(f"{RAW_DIR}/dbm_by_country.csv"))
    df = df.rename(columns={
        "Country": "country",
        "ISO3": "country_code",
        "Value": "dbm_category",
        "End Year": "dbm_data_year",
    })
    df = df[df["country_code"].isin(TARGET_COUNTRIES.values())]
    df["dbm_score"] = df["dbm_category"].map(DBM_SCORE_MAP)
    return df[["country", "country_code", "dbm_category", "dbm_score", "dbm_data_year"]]


def compute_crop_diversity():
    """Source: FAOSTAT QCL (Crops and livestock products), Production element.
    Livestock/animal/processed items excluded. Shannon index is normalized
    by ln(item count) into an evenness score (0-1) so it combines sensibly
    with the other 0-100-scale NRI inputs.
    """
    df = pd.read_csv(_require(f"{RAW_DIR}/faostat_crop_production.csv"))
    df = df[df["Element"] == "Production"]
    df["country_code"] = df["Area"].map(lambda a: TARGET_COUNTRIES.get(a))
    df = df[df["country_code"].notna()]

    item_lower = df["Item"].str.lower()
    exclude_mask = item_lower.str.contains("|".join(LIVESTOCK_AND_PROCESSED_KEYWORDS))
    df = df[~exclude_mask]

    latest_year = df["Year"].max()
    df = df[df["Year"] == latest_year]

    results = []
    for code, group in df.groupby("country_code"):
        totals = group.groupby("Item")["Value"].sum()
        totals = totals[totals > 0]
        p = totals / totals.sum()
        shannon = -(p * np.log(p)).sum()
        max_shannon = np.log(len(totals)) if len(totals) > 1 else 1
        evenness = shannon / max_shannon
        results.append({
            "country_code": code,
            "crop_diversity_index": round(evenness, 4),
            "crop_item_count": len(totals),
            "crop_data_year": int(latest_year),
        })
    return pd.DataFrame(results)


def create_raw_datasets():
    """Builds analytical input tables from real downloaded sources.
    No synthetic fallback — fails loudly if a source file is missing.
    """
    os.makedirs(OUT_DIR, exist_ok=True)

    decision = load_female_decision_score()
    diversity = compute_crop_diversity()
    empowerment = decision.merge(diversity, on="country_code", how="inner")
    empowerment.to_csv(f"{OUT_DIR}/women_empowerment_diversity.csv", index=False)

    trade = load_import_dependency()
    trade.to_csv(f"{OUT_DIR}/trade_dependency_matrix.csv", index=False)

    dbm = load_dbm()
    dbm.to_csv(f"{OUT_DIR}/dbm_by_country.csv", index=False)

    print("\u2713 Real raw datasets built from FAOSTAT / World Bank / Food Systems Dashboard sources")


if __name__ == "__main__":
    create_raw_datasets()