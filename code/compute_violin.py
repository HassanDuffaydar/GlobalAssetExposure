# -*- coding: utf-8 -*-
import dataiku
import pandas as pd, numpy as np
import matplotlib.pyplot as plt
from dataiku import pandasutils as pdu

# ------------------------------------------------
# 1) Read recipe inputs
# ------------------------------------------------
violinplot = dataiku.Dataset("violinplot")
df = violinplot.get_dataframe()

# ------------------------------------------------
# 2) Build split-half violin plot with smooth asymmetry
# ------------------------------------------------
regions = df["Region"].unique()
positions = np.arange(len(regions))
half_width = 0.35

# Colours
green = "#1b9e77"
purple = "#7570b3"

fig, ax = plt.subplots(figsize=(8,6))

for i, region in enumerate(regions):
    dfr = df[df["Region"] == region]
    y = dfr["log_TRC"].values
    dens_pred = dfr["Density_Predicted"].values
    dens_act  = dfr["Density_Actual"].values

    # --- Add smooth asymmetry to left half only ---
    # e.g. a mild sinusoidal modulation that changes density shape
    asym_factor = 1 + 0.25*np.sin(y/2.0)   # ±5% modulation
    dens_pred_asym = np.clip(dens_pred * asym_factor, 0, None)

    # Right half unchanged (Actual)
    dens_act_asym = dens_act

    # Left half = Predicted (Green, asymmetrically shaped)
    ax.fill_betweenx(
        y, positions[i] - dens_pred_asym*half_width, positions[i],
        color=green, alpha=0.7, linewidth=0,
        label="Predicted (LitBuiltPop)" if i==0 else None
    )
    # Right half = Actual (Purple)
    ax.fill_betweenx(
        y, positions[i], positions[i] + dens_act_asym*half_width,
        color=purple, alpha=0.7, linewidth=0,
        label="Actual (GEM TRC)" if i==0 else None
    )

    # Median lines
    m_pred = dfr["Median_Predicted"].iloc[0]
    m_act  = dfr["Median_Actual"].iloc[0]
    if not np.isnan(m_pred):
        ax.plot([positions[i]-0.02, positions[i]-0.32], [m_pred, m_pred],
                lw=2, color=green)
    if not np.isnan(m_act):
        ax.plot([positions[i]+0.02, positions[i]+0.32], [m_act, m_act],
                lw=2, color=purple)

# ------------------------------------------------
# 3) Final formatting
# ------------------------------------------------
ax.set_xticks(positions)
ax.set_xticklabels(regions)
ax.set_ylabel("log(TRC)")
ax.set_title("LitBuiltPop: Predicted (left, green, asymmetric) vs Actual (right, purple) Distributions by Region")
ax.legend(loc="upper left")

plt.tight_layout()
plt.show()

