# -*- coding: utf-8 -*-
import dataiku
import pandas as pd, numpy as np
from dataiku import pandasutils as pdu
from scipy.stats import gaussian_kde

# ------------------------------------------------
# 1) Read recipe inputs
# ------------------------------------------------
litbuiltpop_pred_actual_violin_data = dataiku.Dataset("litbuiltpop_pred_actual_violin_data2")
df = litbuiltpop_pred_actual_violin_data.get_dataframe()

# ------------------------------------------------
# 2) Helper to build normalized KDE
# ------------------------------------------------
def kde_norm(vals, y_grid):
    vals = np.asarray(vals)
    if len(vals) < 10:
        return np.zeros_like(y_grid)
    kde = gaussian_kde(vals)
    dens = kde(y_grid)
    return dens / dens.max() if dens.max() > 0 else dens

# ------------------------------------------------
# 3) Build violin densities for each region
# ------------------------------------------------
regions = df["Region"].unique()
# Fixed global y-axis range for comparability
y_min, y_max = df["log_TRC"].min(), df["log_TRC"].max()
y_grid = np.linspace(y_min, y_max, 400)

rows = []
for region in regions:
    dfr = df[df["Region"] == region]
    pred = dfr[dfr["Type"] == "Predicted"]["log_TRC"].values
    act  = dfr[dfr["Type"] == "Actual"]["log_TRC"].values

    dens_pred = kde_norm(pred, y_grid)
    dens_act  = kde_norm(act,  y_grid)

    # Scale actual to match amplitude of predicted (so half-violins are comparable)
    if dens_act.max() > 0:
        dens_act *= (dens_pred.max() / dens_act.max())

    for y, dp, da in zip(y_grid, dens_pred, dens_act):
        rows.append({
            "Region": region,
            "log_TRC": y,
            "Density_Predicted": dp,
            "Density_Actual": da,
            "Median_Predicted": np.median(pred) if len(pred) else np.nan,
            "Median_Actual": np.median(act) if len(act) else np.nan
        })

violinplot_df = pd.DataFrame(rows)

# ------------------------------------------------
# 4) Write recipe outputs
# ------------------------------------------------
violinplot = dataiku.Dataset("violinplot")
violinplot.write_with_schema(violinplot_df)
