import os
import pandas as pd

RAW_DIR = "data/raw"
PROCESSED_PATH = "data/processed/integrated_eat_trade_matrix.csv"


def transform_all():
    emp_df = pd.read_csv(f"{RAW_DIR}/women_empowerment_diversity.csv")
    trade_df = pd.read_csv(f"{RAW_DIR}/trade_dependency_matrix.csv")
    dbm_df = pd.read_csv(f"{RAW_DIR}/dbm_by_country.csv")

    for df in (emp_df, trade_df, dbm_df):
        df.columns = [c.lower().strip() for c in df.columns]

    merged = dbm_df.merge(emp_df, on="country_code", how="inner", suffixes=("", "_dup"))
    merged = merged.drop(columns=[c for c in merged.columns if c.endswith("_dup")])
    final_df = merged.merge(trade_df, on="country_code", how="inner", suffixes=("", "_dup"))
    final_df = final_df.drop(columns=[c for c in final_df.columns if c.endswith("_dup")])

    required = ["female_decision_score", "crop_diversity_index", "net_staple_import_dependency_pct"]
    incomplete = final_df[final_df[required].isnull().any(axis=1)]
    if not incomplete.empty:
        print(f"\u26a0\ufe0f Dropping {len(incomplete)} countries with incomplete data: {incomplete['country'].tolist()}")
    final_df = final_df.dropna(subset=required)

    # Data-vintage transparency: source years differ across indicators
    # (DHS surveys, FAOSTAT years, DBM classification year). Kept visible
    # rather than hidden, so it can be disclosed honestly in the presentation.
    year_cols = [c for c in final_df.columns if c.endswith("_data_year")]
    if year_cols:
        final_df["source_years"] = final_df[year_cols].astype("Int64").astype(str).agg(", ".join, axis=1)
        final_df["data_years_mismatched"] = final_df[year_cols].nunique(axis=1) > 1

    # NRI computed from the 3 variables with continuous, real sources.
    # DBM is deliberately NOT folded in — it's categorical (0-3), not a
    # percentage, and is reported alongside NRI rather than inside it.
    final_df["nutritional_resilience_index"] = (
        (final_df["female_decision_score"] * 0.4)
        + (final_df["crop_diversity_index"] * 100 * 0.4)
        - (final_df["net_staple_import_dependency_pct"] * 0.2)
    ).round(2)

    final_df = final_df.sort_values("nutritional_resilience_index", ascending=False).reset_index(drop=True)
    return final_df


def save_transformed():
    df = transform_all()
    os.makedirs(os.path.dirname(PROCESSED_PATH), exist_ok=True)
    df.to_csv(PROCESSED_PATH, index=False)
    print(f"\u2713 Transformed data written to {PROCESSED_PATH}")
    return df


if __name__ == "__main__":
    transformed = save_transformed()
    cols = ["country", "nutritional_resilience_index", "dbm_category", "dbm_score",
            "female_decision_score", "crop_diversity_index",
            "net_staple_import_dependency_pct", "source_years"]
    print(transformed[cols].to_string(index=False))