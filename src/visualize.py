import os
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from transform import transform_all

# 1. Get transformed analytical matrix
df = transform_all()

# 2. Sort by Nutritional Resilience Index
df = df.sort_values("nutritional_resilience_index", ascending=False)

# 3. Create chart layout
sns.set_theme(style="whitegrid")
fig, ax1 = plt.subplots(figsize=(10, 6))

# 4. Bar Chart — Nutritional Resilience Index (Teal HEX)
bar_color = "#008080"
ax1.set_xlabel("Country", fontsize=12, fontweight="bold")
ax1.set_ylabel(
    "Nutritional Resilience Index (NRI)",
    color=bar_color,
    fontsize=12,
    fontweight="bold",
)
bars = ax1.bar(
    df["country"],
    df["nutritional_resilience_index"],
    color=bar_color,
    alpha=0.85,
)
ax1.tick_params(axis="y", labelcolor=bar_color)

# Add data values on top of bars
for bar in bars:
  yval = bar.get_height()
  ax1.text(
      bar.get_x() + bar.get_width() / 2,
      yval + 0.8,
      f"{yval:.1f}",
      ha="center",
      va="bottom",
      fontsize=10,
      fontweight="bold",
  )

# 5. Line Chart Overlay — DBM % (Red HEX)
ax2 = ax1.twinx()
line_color = "#D9534F"
ax2.set_ylabel(
    "Double Burden Malnutrition % (DBM)",
    color=line_color,
    fontsize=12,
    fontweight="bold",
)
ax2.plot(
    df["country"],
    df["dbm_pct"],
    color=line_color,
    marker="o",
    linewidth=2.5,
    markersize=8,
)
ax2.tick_params(axis="y", labelcolor=line_color)

# 6. Formatting & Save
plt.title(
    "Nutritional Resilience Index vs. DBM Vulnerability by Country\n(Eat +"
    " Trade Multi-Track Analysis)",
    fontsize=14,
    fontweight="bold",
    pad=20,
)
plt.tight_layout()

# Save figure in data directory
os.makedirs("data", exist_ok=True)
plt.savefig("data/nri_vs_dbm_chart.png", dpi=300)
print("✓ Chart rendered and saved successfully to data/nri_vs_dbm_chart.png!")
plt.show()