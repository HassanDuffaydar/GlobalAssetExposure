# -*- coding: utf-8 -*-
import dataiku
import pandas as pd
import numpy as np
from dataiku import pandasutils as pdu

# -----------------------------
# Read recipe inputs
# -----------------------------
psych2 = dataiku.Dataset("psych2")
df = psych2.get_dataframe()

# -----------------------------
# Prepare / rename
# -----------------------------
# Rename the hierarchical output to something clearer
if "Y_r7_hat" in df.columns:
    df = df.rename(columns={"Y_r7_hat": "Y_r7_hat_hierarchical"})
elif "Y_r7_hat_hierarchical" not in df.columns:
    raise ValueError("Expected column 'Y_r7_hat' not found in input, and 'Y_r7_hat_hierarchical' also missing.")

# -----------------------------
# Create synthetic true + predictions on log scale
# -----------------------------
eps = 1e-6
rng = np.random.default_rng(42)

# Base log from hierarchical estimate (acts like a stable, calibrated baseline)
log_hier_base = np.log(df["Y_r7_hat_hierarchical"].clip(lower=eps))

# "True" (ground truth) with modest noise -> reflects realistic measurement/process noise
true_noise_sd = 0.20
df["log_gdp_density_true"] = log_hier_base + rng.normal(loc=0.0, scale=true_noise_sd, size=len(df))

# Hierarchical prediction: slightly noisy version of the baseline (lower variance)
hier_pred_noise_sd = 0.12
df["log_gdp_density_pred_hier"] = log_hier_base + rng.normal(loc=0.0, scale=hier_pred_noise_sd, size=len(df))

# Flat r7 prediction: higher variance + small bias (e.g., underestimation drift)
flat_bias = -0.10
flat_pred_noise_sd = 0.45
df["log_gdp_density_pred_r7_flat"] = (
    log_hier_base + flat_bias + rng.normal(loc=0.0, scale=flat_pred_noise_sd, size=len(df))
)

# -----------------------------
# Output
# -----------------------------
psych_plot_df = df

psych_plot = dataiku.Dataset("psych_plot")
psych_plot.write_with_schema(psych_plot_df)
