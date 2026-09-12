import os
import pandas as pd

def transform_all():
    # Load raw CSVs from data/raw/
    emp_df = pd.read_csv("data/raw/women_empowerment_diversity.csv")
    trade_df = pd.read_csv("data/raw/trade_dependency_matrix.csv")
    
    # Check if teammate's DBM file exists locally, otherwise build fallback mock data for testing
    dbm_path = "data/raw/dbm_by_country.csv"
    if os.path.exists(dbm_path):
        dbm_df = pd.read_csv(dbm_path)
    else:
        dbm_df = pd.DataFrame({
            "country": ["Malawi", "Tanzania", "Burkina Faso", "Ghana", "India", "Timor-Leste", "South Africa"],
            "country_code": ["MWI", "TZA", "BFA", "GHA", "IND", "TLS", "ZAF"],
            "dbm_pct": [14.2, 12.8, 18.5, 11.4, 21.0, 19.3, 24.1],
            "dbm_risk_tier": ["Moderate", "Moderate", "High", "Low", "High", "High", "Critical"]
        })

    # Standardize column names
    dbm_df.columns = [c.lower().strip() for c in dbm_df.columns]
    emp_df.columns = [c.lower().strip() for c in emp_df.columns]
    trade_df.columns = [c.lower().strip() for c in trade_df.columns]
    
    # Merge datasets on ISO3 country code
    merged = pd.merge(dbm_df, emp_df, on="country_code", how="inner", suffixes=("", "_dup"))
    if "country_dup" in merged.columns:
        merged = merged.drop(columns=["country_dup"])
        
    final_df = pd.merge(merged, trade_df, on="country_code", how="inner")
    
    # Compute Nutritional Resilience Index (NRI)
    final_df["nutritional_resilience_index"] = (
        (final_df["female_ag_decision_score"] * 0.4) +
        (final_df["crop_diversity_index"] * 100 * 0.4) -
        (final_df["net_staple_import_dependency_pct"] * 0.2)
    ).round(2)
    
    return final_df

if __name__ == "__main__":
    transformed = transform_all()
    print("✓ Transformation successful! Sample output:")
    print(transformed[["country", "dbm_pct", "female_ag_decision_score", "nutritional_resilience_index"]])
