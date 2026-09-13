import os
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd
import seaborn as sns
from transform import transform_all

# 1. Get transformed analytical matrix
df = transform_all()

# 2. Sort by Nutritional Resilience Index
df = df.sort_values("nutritional_resilience_index", ascending=False)

# 3. Create chart layout
sns.set_theme(style="whitegrid")
fig, ax1 = plt.subplots(figsize=(11, 6))

# 4. Bar Chart — Nutritional Resilience Index (Teal HEX)
bar_color = "#008080"
ax1.set_xlabel("Country", fontsize=12, fontweight="bold")
ax1.set_ylabel("Nutritional Resilience Index (NRI)", color=bar_color, fontsize=12, fontweight="bold")
bars = ax1.bar(df["country"], df["nutritional_resilience_index"], color=bar_color, alpha=0.85)
ax1.tick_params(axis="y", labelcolor=bar_color)


for bar in bars:
    yval = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width() / 2, yval + 1.2, f"{yval:.1f}",
              ha="center", va="bottom", fontsize=10, fontweight="bold")

# 5. DBM shown as discrete category markers, NOT a connected line —
# dbm_score is ordinal (0-3), not continuous, so a line implies false precision.
dbm_colors = {0: "#5CB85C", 1: "#F0AD4E", 2: "#D9534F", 3: "#8B0000"}
ax2 = ax1.twinx()
ax2.set_ylabel("Double Burden of Malnutrition (category)", fontsize=12, fontweight="bold")
ax2.set_ylim(-0.5, 3.5)
ax2.set_yticks([0, 1, 2, 3])
ax2.set_yticklabels(["No DBM", ">20% overweight", ">30% overweight", ">40% overweight"])

for i, (_, row) in enumerate(df.iterrows()):
    ax2.scatter(i, row["dbm_score"], color=dbm_colors[row["dbm_score"]], s=180,
                edgecolor="black", linewidth=1.2, zorder=5)

# 6. Formatting & Save
plt.title(
    "Nutritional Resilience Index vs. Double Burden of Malnutrition by Country\n"
    "(Eat + Trade Multi-Track Analysis — Real Data: FAOSTAT, World Bank, Food Systems Dashboard)",
    fontsize=13, fontweight="bold", pad=20,
)
fig.text(0.5, 0.01,
          "DBM classification based on 2010 survey data (most recent published year). "
          "Other indicators reflect most recent available year per country (2016-2022).",
          ha="center", fontsize=8, style="italic")
plt.tight_layout(rect=[0, 0.03, 1, 1])

os.makedirs("data", exist_ok=True)
plt.savefig("data/nri_vs_dbm_chart.png", dpi=300)
print("✓ Chart rendered and saved successfully to data/nri_vs_dbm_chart.png!")
plt.show()