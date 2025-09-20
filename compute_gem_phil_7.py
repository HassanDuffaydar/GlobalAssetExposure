# -*- coding: utf-8 -*-
import dataiku
import pandas as pd, numpy as np
from dataiku import pandasutils as pdu

import geopandas as gpd
from shapely import wkt as shapely_wkt

# --------- config (adjust names if needed) ----------
POINT_WKT_COL = "GEOPOINT_WKT"             # in combined_phi
HEX_WKT_CANDIDATES = ["GEOM_WKT", "WKT", "geometry", "GEOMETRY"]  # in philip_7
HEX_ID_CANDIDATES  = ["HEX_ID", "hex_id", "h3", "h3_index", "id", "ID"]
# ----------------------------------------------------

def pick_col(df, candidates):
    for c in candidates:
        if c in df.columns:
            return c
    # fallback: first object-like col
    for c in df.columns:
        if pd.api.types.is_object_dtype(df[c]) or pd.api.types.is_string_dtype(df[c]):
            return c
    raise ValueError("Could not find a suitable column from: " + ",".join(candidates))

def scrub(df):
    for c in ["index_left", "index_right"]:
        if c in df.columns:
            df = df.drop(columns=[c])
    return df

# ----- read inputs -----
combined_phi = dataiku.Dataset("combined_phi")
combined_phi_df = combined_phi.get_dataframe()

philip_7 = dataiku.Dataset("philip_7")
philip_7_df = philip_7.get_dataframe()

# ----- build GeoDataFrames -----
# Points
if POINT_WKT_COL not in combined_phi_df.columns:
    # fall back if the column has a different name
    POINT_WKT_COL = pick_col(combined_phi_df, [POINT_WKT_COL])

pts = combined_phi_df.dropna(subset=[POINT_WKT_COL]).copy()
pts["geometry"] = pts[POINT_WKT_COL].astype(str).apply(shapely_wkt.loads)
gpts = gpd.GeoDataFrame(scrub(pts), geometry="geometry", crs="EPSG:4326").reset_index(drop=True)

# Hex polygons
HEX_WKT_COL = pick_col(philip_7_df, HEX_WKT_CANDIDATES)
hexes = philip_7_df.dropna(subset=[HEX_WKT_COL]).copy()
hexes["geometry"] = hexes[HEX_WKT_COL].astype(str).apply(shapely_wkt.loads)

hex_id_col = None
for c in HEX_ID_CANDIDATES:
    if c in hexes.columns:
        hex_id_col = c
        break
if hex_id_col is None:
    hex_id_col = "HEX_ID"
    hexes[hex_id_col] = np.arange(len(hexes))

ghex = gpd.GeoDataFrame(scrub(hexes), geometry="geometry", crs="EPSG:4326").reset_index(drop=True)

# Fix invalid polygons (if any)
ghex["geometry"] = ghex["geometry"].buffer(0)

# ----- project to metric for nearest (distance in meters) -----
gpts_3857 = gpts.to_crs(3857)
ghex_3857 = ghex.to_crs(3857)

# ----- nearest-hex join: EVERY point gets a hex -----
# distance_col is optional; useful for QA
joined = gpd.sjoin_nearest(
    gpts_3857,
    ghex_3857[[hex_id_col, "geometry"]],
    how="left",
    distance_col="nearest_m"
)

# sanity: all points should be assigned
assigned = joined[hex_id_col].notna().sum()
total = len(joined)
print(f"Assigned {assigned}/{total} points to nearest hex.")

# bring back to WGS84 for any downstream geometry needs
joined = joined.to_crs(4326)

# ----- aggregates per hex -----
joined["TOTAL_REPL_COST_USD"] = pd.to_numeric(joined.get("TOTAL_REPL_COST_USD", np.nan), errors="coerce")
joined["OCCUPANCY"] = pd.to_numeric(joined.get("OCCUPANCY", np.nan), errors="coerce")

agg = (joined
       .groupby(hex_id_col, dropna=False)
       .agg(
           POINT_COUNT=("geometry", "count"),
           AVG_OCCUPANCY=("OCCUPANCY", "mean"),
           SUM_TOTAL_REPL_COST_USD=("TOTAL_REPL_COST_USD", "sum"),
           AVG_TOTAL_REPL_COST_USD=("TOTAL_REPL_COST_USD", "mean")
       )
       .reset_index())

# attach all hex rows so empty ones appear with zeros
out = ghex[[hex_id_col, "geometry"]].merge(agg, on=hex_id_col, how="left")
out["GEOM_WKT"] = out["geometry"].apply(lambda g: g.wkt)

# fill empties
for c in ["POINT_COUNT"]:
    out[c] = out[c].fillna(0).astype(int)
for c in ["AVG_OCCUPANCY", "SUM_TOTAL_REPL_COST_USD", "AVG_TOTAL_REPL_COST_USD"]:
    out[c] = out[c].fillna(0.0)

gem_phil_7_df = out[[hex_id_col, "GEOM_WKT", "POINT_COUNT",
                     "AVG_OCCUPANCY", "SUM_TOTAL_REPL_COST_USD",
                     "AVG_TOTAL_REPL_COST_USD"]].copy()

# ----- write output -----
gem_phil_7 = dataiku.Dataset("gem_phil_7")
gem_phil_7.write_with_schema(gem_phil_7_df)

# (optional) write points-with-hex for QA
try:
    pts_with_hex = joined[[hex_id_col, "nearest_m"]].copy()
    # back to original rows
    pts_with_hex = pd.concat([gpts.reset_index(drop=True), pts_with_hex.reset_index(drop=True)], axis=1)
    ds = dataiku.Dataset("points_with_nearest_hex_debug")
    ds.write_with_schema(pts_with_hex.drop(columns=[c for c in ["index_right","index_left"] if c in pts_with_hex.columns]))
except Exception as e:
    print(f"[Info] Skipped writing 'points_with_nearest_hex_debug': {e}")
