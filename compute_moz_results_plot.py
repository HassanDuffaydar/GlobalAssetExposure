# -*- coding: utf-8 -*-
import dataiku
import pandas as pd, numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from dataiku import pandasutils as pdu

# ------------------------
# Read recipe inputs
# ------------------------
Model_Predictions_with_Uncertainty__Mozambique_ = dataiku.Dataset("Model_Predictions_with_Uncertainty__Mozambique_")
df = Model_Predictions_with_Uncertainty__Mozambique_.get_dataframe()

# ------------------------
# Extract columns
# ------------------------
actual = df["Actual_log_TRC"].values
litpop_pred = df["LitPop_Pred"].values
builtpop_pred = df["BuiltPop_Pred"].values
litbuiltpop_pred = df["LitBuiltPop_Pred"].values

unc_litpop = df["Unc_LitPop"].values
unc_builtpop = df["Unc_BuiltPop"].values
unc_litbuiltpop = df["Unc_LitBuiltPop"].values

# ------------------------
# Create Lift Plot
# ------------------------
fig = plt.figure(figsize=(10,8))
gs = gridspec.GridSpec(2, 1, height_ratios=[4, 1], hspace=0.05)

ax0 = fig.add_subplot(gs[0])
ax0.plot([1,8],[1,8],'k--',label="Perfect Prediction")

grid = np.linspace(1,8,100)

# Uncertainty bands
ax0.fill_between(grid,
                 grid - np.interp(grid, actual, unc_litpop),
                 grid + np.interp(grid, actual, unc_litpop),
                 color="tab:blue", alpha=0.1)

ax0.fill_between(grid,
                 grid - np.interp(grid, actual, unc_builtpop),
                 grid + np.interp(grid, actual, unc_builtpop),
                 color="tab:orange", alpha=0.1)

ax0.fill_between(grid,
                 grid - np.interp(grid, actual, unc_litbuiltpop),
                 grid + np.interp(grid, actual, unc_litbuiltpop),
                 color="tab:green", alpha=0.1)

# Scatter predictions
ax0.scatter(actual, litpop_pred, alpha=0.5, s=25, label="LitPop", color="tab:blue")
ax0.scatter(actual, builtpop_pred, alpha=0.5, s=25, label="BuiltPop", color="tab:orange")
ax0.scatter(actual, litbuiltpop_pred, alpha=0.5, s=25, label="LitBuiltPop", color="tab:green")

ax0.set_ylabel("Predicted log(TRC)", fontsize=12)
ax0.set_xlim(1,8)
ax0.set_ylim(1,8)
ax0.legend()
ax0.grid(alpha=0.3)
ax0.set_xticklabels([])

# Histogram below
ax1 = fig.add_subplot(gs[1], sharex=ax0)
ax1.hist(actual, bins=30, color="tab:gray", alpha=0.7)
ax1.set_xlabel("Actual log(TRC)", fontsize=12)
ax1.set_ylabel("Count", fontsize=10)

plt.suptitle("Lift Plot with Model-Specific Uncertainty and Exposure Distribution (Mozambique)",
             y=0.95, fontsize=14)



