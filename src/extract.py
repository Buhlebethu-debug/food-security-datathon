import os
import pandas as pd

def create_raw_datasets():
    # Ensure raw directory exists
    os.makedirs("data/raw", exist_ok=True)
    
    # 1. Women's Empowerment & Crop Diversity Dataset
    empowerment_data = {
        "country": ["Malawi", "Tanzania", "Burkina Faso", "Ghana", "India", "Timor-Leste", "South Africa"],
        "country_code": ["MWI", "TZA", "BFA", "GHA", "IND", "TLS", "ZAF"],
        "female_ag_decision_score": [68.4, 62.1, 54.0, 71.2, 48.9, 59.3, 58.2],
        "crop_diversity_index": [0.72, 0.68, 0.55, 0.79, 0.61, 0.58, 0.64],
        "dietary_diversity_score": [61.2, 58.5, 51.0, 66.4, 54.3, 50.8, 56.1]
    }
    pd.DataFrame(empowerment_data).to_csv("data/raw/women_empowerment_diversity.csv", index=False)
    
    # 2. Global Trade Vulnerability Dataset
    trade_data = {
        "country_code": ["MWI", "TZA", "BFA", "GHA", "IND", "TLS", "ZAF"],
        "net_staple_import_dependency_pct": [18.5, 14.2, 32.1, 41.5, 5.2, 62.4, 22.8],
        "food_price_volatility_index": [1.24, 1.10, 1.85, 1.62, 1.05, 2.15, 1.35]
    }
    pd.DataFrame(trade_data).to_csv("data/raw/trade_dependency_matrix.csv", index=False)
    
    print("✓ Raw datasets successfully created in data/raw/")

if __name__ == "__main__":
    create_raw_datasets()
