# -*- coding: utf-8 -*-
import dataiku
import pandas as pd
import numpy as np
from dataiku import pandasutils as pdu

# Read recipe inputs
Exposure_Res_Philippines = dataiku.Dataset("Exposure_Res_Philippines")
df = Exposure_Res_Philippines.get_dataframe()

# ---- 1) Build a geopoint column from LATITUDE / LONGITUDE ----
df["geopoint"] = (
    df["LATITUDE"].astype(str).str.strip() + "," + df["LONGITUDE"].astype(str).str.strip()
)

# ---- 2) Compute centroid per SETTLEMENT (urban / rural) ----
centroids = (
    df[["SETTLEMENT", "LATITUDE", "LONGITUDE"]]
    .dropna(subset=["SETTLEMENT", "LATITUDE", "LONGITUDE"])
    .groupby("SETTLEMENT", as_index=False)
    .agg(
        centroid_lat=("LATITUDE", "mean"),
        centroid_lon=("LONGITUDE", "mean"),
    )
)

df = df.merge(centroids, on="SETTLEMENT", how="left")

# ---- 3) Haversine distance (km) to the class centroid ----
def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0088  # km
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2.0)**2 + np.cos(lat1)*np.cos(lat2)*np.sin(dlon/2.0)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c

df["distance_to_settlement_centroid_km"] = haversine_km(
    df["LATITUDE"], df["LONGITUDE"], df["centroid_lat"], df["centroid_lon"]
)

# ---- 4) Per-settlement averages: distance & TOTAL_REPL_COST_USD ----
stats = (
    df.dropna(subset=["SETTLEMENT"])
      .groupby("SETTLEMENT", as_index=False)
      .agg(
          avg_distance_km_by_settlement=("distance_to_settlement_centroid_km", "mean"),
          avg_TOTAL_REPL_COST_USD_by_settlement=("TOTAL_REPL_COST_USD", "mean"),
      )
)

df = df.merge(stats, on="SETTLEMENT", how="left")

# Optional: order columns
front_cols = [
    "SETTLEMENT", "LATITUDE", "LONGITUDE", "geopoint",
    "distance_to_settlement_centroid_km",
    "avg_distance_km_by_settlement", "avg_TOTAL_REPL_COST_USD_by_settlement",
]
other_cols = [c for c in df.columns if c not in front_cols]
resolution_phil_df = df[front_cols + other_cols]

# ---- 5) Write recipe output ----
resolution_phil = dataiku.Dataset("resolution_phil")
resolution_phil.write_with_schema(resolution_phil_df)
