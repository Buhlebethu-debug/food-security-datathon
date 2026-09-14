import os

import matplotlib.pyplot as plt
import pandas as pd

from extract import (
    extract_dbm_data,
    extract_sa_province_data,
    extract_empowerment_data,
    extract_trade_data,
)
from transform import build_analysis_tables


OUTPUT_DIR = "data/visualizations"


def get_analysis_tables():
    """
    Run the existing extraction and transformation pipeline
    and return the analytical tables used for visualization.
    """

    dbm_raw = extract_dbm_data()
    sa_raw = extract_sa_province_data()
    empowerment_raw = extract_empowerment_data()
    trade_raw = extract_trade_data()

    return build_analysis_tables(
        dbm_raw,
        sa_raw,
        empowerment_raw,
        trade_raw,
    )


def save_figure(fig, filename):
    """
    Save a figure to the visualization output directory.
    """

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    filepath = os.path.join(OUTPUT_DIR, filename)

    fig.tight_layout()
    fig.savefig(filepath, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"✓ Saved: {filepath}")


def plot_nri_vs_dbm(tables):
    """
    Compare Nutritional Resilience Index with
    Double Burden Malnutrition.
    """

    nri = tables["country_nutritional_resilience"].copy()
    dbm = tables["dbm_by_country"].copy()

    # DBM contains two survey observations for Malawi.
    # Aggregate to one country-level value for this comparison.
    dbm_country = (
        dbm.groupby("country", as_index=False)
        .agg(
            dbm_pct=("dbm_pct", "mean"),
        )
    )

    merged = pd.merge(
        nri,
        dbm_country,
        on="country",
        how="inner",
    )

    fig, ax = plt.subplots(figsize=(9, 6))

    ax.scatter(
        merged["nutritional_resilience_index"],
        merged["dbm_pct"],
        s=100,
        alpha=0.8,
    )

    for _, row in merged.iterrows():
        ax.annotate(
            row["country"],
            (
                row["nutritional_resilience_index"],
                row["dbm_pct"],
            ),
            xytext=(6, 6),
            textcoords="offset points",
            fontsize=9,
        )

    ax.set_xlabel("Nutritional Resilience Index")
    ax.set_ylabel("Double Burden Malnutrition (%)")
    ax.set_title(
        "Nutritional Resilience vs. Double Burden Malnutrition"
    )

    ax.grid(True, alpha=0.3)

    save_figure(fig, "nri_vs_dbm.png")


def plot_empowerment_vs_dietary_diversity(tables):
    """
    Compare women's agricultural decision-making power
    with dietary diversity.
    """

    df = tables["country_nutritional_resilience"].copy()

    fig, ax = plt.subplots(figsize=(9, 6))

    ax.scatter(
        df["female_ag_decision_score"],
        df["dietary_diversity_score"],
        s=100,
        alpha=0.8,
    )

    for _, row in df.iterrows():
        ax.annotate(
            row["country"],
            (
                row["female_ag_decision_score"],
                row["dietary_diversity_score"],
            ),
            xytext=(6, 6),
            textcoords="offset points",
            fontsize=9,
        )

    ax.set_xlabel("Female Agricultural Decision-Making Score")
    ax.set_ylabel("Dietary Diversity Score")
    ax.set_title(
        "Women's Empowerment vs. Dietary Diversity"
    )

    ax.grid(True, alpha=0.3)

    save_figure(
        fig,
        "empowerment_vs_dietary_diversity.png",
    )


def plot_trade_vulnerability(tables):
    """
    Compare staple import dependency with food price volatility.
    """

    df = tables["country_nutritional_resilience"].copy()

    fig, ax = plt.subplots(figsize=(9, 6))

    ax.scatter(
        df["net_staple_import_dependency_pct"],
        df["food_price_volatility_index"],
        s=100,
        alpha=0.8,
    )

    for _, row in df.iterrows():
        ax.annotate(
            row["country"],
            (
                row["net_staple_import_dependency_pct"],
                row["food_price_volatility_index"],
            ),
            xytext=(6, 6),
            textcoords="offset points",
            fontsize=9,
        )

    ax.set_xlabel("Net Staple Import Dependency (%)")
    ax.set_ylabel("Food Price Volatility Index")
    ax.set_title(
        "Trade Dependency vs. Food Price Volatility"
    )

    ax.grid(True, alpha=0.3)

    save_figure(fig, "trade_vulnerability.png")


def plot_sa_food_insecurity(tables):
    """
    Rank South African provinces by food insecurity.
    """

    df = tables["sa_food_insecurity_by_province"].copy()

    df = df.sort_values(
        "pct_food_insecure_all",
        ascending=True,
    )

    fig, ax = plt.subplots(figsize=(9, 6))

    ax.barh(
        df["province"],
        df["pct_food_insecure_all"],
    )

    ax.set_xlabel("Food Insecurity (%)")
    ax.set_ylabel("Province")
    ax.set_title(
        "Food Insecurity Across South African Provinces"
    )

    for i, value in enumerate(df["pct_food_insecure_all"]):
        if pd.notna(value):
            ax.text(
                value + 0.3,
                i,
                f"{value:.1f}%",
                va="center",
                fontsize=9,
            )

    ax.grid(
        axis="x",
        alpha=0.3,
    )

    save_figure(fig, "sa_food_insecurity.png")


def plot_northern_cape_gender_gap(tables):
    """
    Show the change in the Northern Cape food insecurity
    gender gap over time.
    """

    # The cleaned provincial table contains the latest year
    # for each province, so use the raw data for the
    # Northern Cape time-series visualization.
    sa_raw = extract_sa_province_data()

    northern_cape = sa_raw[
        sa_raw["province"].str.strip().eq("Northern Cape")
    ].copy()

    northern_cape = northern_cape.sort_values("year")

    northern_cape["gender_gap"] = (
        northern_cape["pct_food_insecure_female_headed"]
        - northern_cape["pct_food_insecure_all"]
    )

    fig, ax = plt.subplots(figsize=(9, 6))

    ax.plot(
        northern_cape["year"],
        northern_cape["gender_gap"],
        marker="o",
        linewidth=2,
    )

    for _, row in northern_cape.iterrows():
        ax.annotate(
            f"{row['gender_gap']:.1f} pp",
            (
                row["year"],
                row["gender_gap"],
            ),
            xytext=(5, 6),
            textcoords="offset points",
            fontsize=9,
        )

    ax.set_xlabel("Year")
    ax.set_ylabel("Gender Gap (percentage points)")
    ax.set_title(
        "Northern Cape Food Insecurity Gender Gap"
    )

    ax.grid(True, alpha=0.3)

    save_figure(fig, "northern_cape_gender_gap.png")


def main():
    print("Building analytical tables...")

    tables = get_analysis_tables()

    print("Creating visualizations...")

    plot_nri_vs_dbm(tables)
    plot_empowerment_vs_dietary_diversity(tables)
    plot_trade_vulnerability(tables)
    plot_sa_food_insecurity(tables)
    plot_northern_cape_gender_gap(tables)

    print("\n✓ All visualizations created successfully.")


if __name__ == "__main__":
    main()