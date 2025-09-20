# -*- coding: utf-8 -*-
import dataiku
import pandas as pd, numpy as np
from dataiku import pandasutils as pdu

# Read recipe inputs
# Dataset Exposure_Res_Philippines renamed to Exposure_Res_Mozambique by admin on 2025-08-16 18:44:34
# Dataset Exposure_Res_Mozambique renamed to Exposure_Res_United_States by admin on 2025-08-16 18:48:31
Exposure_Res_Philippines = dataiku.Dataset("Exposure_Res_United_States")
Exposure_Res_Philippines_df = Exposure_Res_Philippines.get_dataframe()
# Dataset Exposure_Com_Philippines renamed to Exposure_Com_Mozambique by admin on 2025-08-16 18:44:34
# Dataset Exposure_Com_Mozambique renamed to Exposure_Com_United_States by admin on 2025-08-16 18:48:31
Exposure_Com_Philippines = dataiku.Dataset("Exposure_Com_United_States")
Exposure_Com_Philippines_df = Exposure_Com_Philippines.get_dataframe()
# Dataset Exposure_Ind_Philippines renamed to Exposure_Ind_Mozambique by admin on 2025-08-16 18:44:34
# Dataset Exposure_Ind_Mozambique renamed to Exposure_Ind_United_States by admin on 2025-08-16 18:48:31
Exposure_Ind_Philippines = dataiku.Dataset("Exposure_Ind_United_States")
Exposure_Ind_Philippines_df = Exposure_Ind_Philippines.get_dataframe()

# Columns to keep
TARGET_COLS = ["LONGITUDE", "LATITUDE", "OCCUPANCY", "TOTAL_REPL_COST_USD", "SETTLEMENT"]

def to_wkt(df: pd.DataFrame) -> pd.DataFrame:
    # Ensure all target columns exist
    for col in TARGET_COLS:
        if col not in df.columns:
            df[col] = np.nan
    df = df[TARGET_COLS].copy()

    # Coerce coords to numeric
    df["LONGITUDE"] = pd.to_numeric(df["LONGITUDE"], errors="coerce")
    df["LATITUDE"]  = pd.to_numeric(df["LATITUDE"],  errors="coerce")

    # Valid rows
    mask = df["LONGITUDE"].notna() & df["LATITUDE"].notna()

    # Build WKT: POINT (lon lat)
    lon_txt = df["LONGITUDE"].map(lambda v: f"{v:.15f}")
    lat_txt = df["LATITUDE"].map(lambda v: f"{v:.15f}")
    df["GEOPOINT_WKT"] = np.where(mask, "POINT (" + lon_txt + " " + lat_txt + ")", np.nan)

    return df

# Prepare each input
res_df = to_wkt(Exposure_Res_Philippines_df)
com_df = to_wkt(Exposure_Com_Philippines_df)
ind_df = to_wkt(Exposure_Ind_Philippines_df)

# Combine
combined_phi_df = pd.concat([res_df, com_df, ind_df], ignore_index=True)

# (Optional) keep only rows with valid coordinates
combined_phi_df = combined_phi_df.dropna(subset=["LONGITUDE", "LATITUDE"])

# Write recipe output
# Dataset combined_phi renamed to combined_moz by admin on 2025-08-16 18:44:34
# Dataset combined_moz renamed to combined_us by admin on 2025-08-16 18:48:31
combined_phi = dataiku.Dataset("combined_us")
combined_phi.write_with_schema(combined_phi_df)
