# -*- coding: utf-8 -*-
import dataiku
import pandas as pd, numpy as np
from dataiku import pandasutils as pdu
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm

# Read recipe inputs
# Dataset combined_phi renamed to combined_moz by admin on 2025-08-16 18:45:47
combined_phi = dataiku.Dataset("combined_moz")
combined_phi_df = combined_phi.get_dataframe()

# --- Extract lon/lat from WKT ---
# WKT format: "POINT (lon lat)"
def parse_wkt(wkt):
    try:
        coords = wkt.replace("POINT (", "").replace(")", "").split()
        lon, lat = map(float, coords)
        return lon, lat
    except Exception:
        return np.nan, np.nan

combined_phi_df[["LONGITUDE_EX", "LATITUDE_EX"]] = combined_phi_df["GEOPOINT_WKT"].apply(
    lambda w: pd.Series(parse_wkt(w))
)

# --- Build plot dataframe ---
plot_df = combined_phi_df.dropna(subset=["LONGITUDE_EX", "LATITUDE_EX", "TOTAL_REPL_COST_USD"]).copy()

# Plot
plt.figure(figsize=(8, 6))
sc = plt.scatter(
    plot_df["LONGITUDE_EX"],
    plot_df["LATITUDE_EX"],
    c=plot_df["TOTAL_REPL_COST_USD"],
    cmap="viridis",
    norm=LogNorm(),   # log scale
    s=4,
    alpha=0.7
)
plt.colorbar(sc, label="Total Replacement Cost (USD, log scale)")
plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.title("Mozambique Exposure - Replacement Cost (Log Scale)")
plt.show()
