# -*- coding: utf-8 -*-
import dataiku
import pandas as pd, numpy as np
from dataiku import pandasutils as pdu

# ================= config =================
WKT_COL = "GEOPOINT_WKT"               # WKT like: "POINT (lon lat)"
SETTLEMENT_COL = "SETTLEMENT"          # contains Urban/Rural markers
COST_COL = "TOTAL_REPL_COST_USD"
EARTH_RADIUS_KM = 6371.0088
# =========================================

# -------- helpers --------
def parse_wkt_point(w):
    # WKT: "POINT (lon lat)"
    try:
        lon, lat = w.replace("POINT (", "").replace(")", "").split()
        return float(lon), float(lat)
    except Exception:
        return np.nan, np.nan

def haversine_km(lat1, lon1, lat2, lon2):
    """Vectorized haversine (km). Inputs in degrees; supports broadcasting."""
    d2r = np.pi / 180.0
    lat1, lon1, lat2, lon2 = lat1*d2r, lon1*d2r, lat2*d2r, lon2*d2r
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2.0)**2 + np.cos(lat1)*np.cos(lat2)*np.sin(dlon/2.0)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return EARTH_RADIUS_KM * c

def normalize_settlement(val):
    if pd.isna(val):
        return np.nan
    s = str(val).strip().lower()
    if "urban" in s:
        return "Urban"
    if "rural" in s:
        return "Rural"
    return np.nan

def mean_distance_to_centroid_km(lats: pd.Series, lons: pd.Series) -> float:
    """
    Fast 'good-enough' bandwidth proxy:
    1) Compute simple average latitude/longitude (centroid in degrees).
    2) Return the mean great-circle distance from all points to that centroid.
    """
    if len(lats) < 1:
        return np.nan
    lat_c = float(lats.mean())
    lon_c = float(lons.mean())
    # Vectorized distances from each point to the centroid
    d = haversine_km(
        lats.to_numpy(),
        lons.to_numpy(),
        np.full(lats.shape[0], lat_c, dtype=float),
        np.full(lons.shape[0], lon_c, dtype=float),
    )
    return float(np.mean(d)) if d.size else np.nan

# -------- read input --------
combined_phi = dataiku.Dataset("combined_phi")
combined_phi_df = combined_phi.get_dataframe()

# -------- parse coordinates --------
lonlat = combined_phi_df[WKT_COL].apply(parse_wkt_point).apply(pd.Series)
combined_phi_df["LONGITUDE_EX"] = lonlat[0]
combined_phi_df["LATITUDE_EX"]  = lonlat[1]

df = combined_phi_df.dropna(subset=["LONGITUDE_EX", "LATITUDE_EX"]).copy()
df["SETTLEMENT_NORM"] = df[SETTLEMENT_COL].apply(normalize_settlement)

# -------- compute stats (overall + by Urban/Rural) --------
def compute_block_stats(sub: pd.DataFrame):
    if len(sub) == 0:
        return {
            "Count": 0,
            "Mean_Distance_to_Centroid_km": np.nan,
            "Centroid_Lat": np.nan,
            "Centroid_Lon": np.nan,
            "Avg_Total_Repl_Cost_USD": np.nan,
        }
    lat_c = float(sub["LATITUDE_EX"].mean())
    lon_c = float(sub["LONGITUDE_EX"].mean())
    md = mean_distance_to_centroid_km(sub["LATITUDE_EX"], sub["LONGITUDE_EX"])
    avg_cost = pd.to_numeric(sub[COST_COL], errors="coerce").mean()
    return {
        "Count": int(len(sub)),
        "Mean_Distance_to_Centroid_km": md,
        "Centroid_Lat": lat_c,
        "Centroid_Lon": lon_c,
        "Avg_Total_Repl_Cost_USD": float(avg_cost) if pd.notna(avg_cost) else np.nan,
    }

rows = []

# Overall
rows.append({"Group": "Overall", **compute_block_stats(df)})

# Urban / Rural
for grp in ["Urban", "Rural"]:
    sub = df[df["SETTLEMENT_NORM"] == grp]
    rows.append({"Group": grp, **compute_block_stats(sub)})

stats_df = pd.DataFrame(
    rows,
    columns=[
        "Group", "Count",
        "Mean_Distance_to_Centroid_km",
        "Centroid_Lat", "Centroid_Lon",
        "Avg_Total_Repl_Cost_USD",
    ],
)

# -------- write output --------
stats = dataiku.Dataset("stats")
stats.write_with_schema(stats_df)

