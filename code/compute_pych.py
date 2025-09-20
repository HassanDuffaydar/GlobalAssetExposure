
# -*- coding: utf-8 -*-
import dataiku
import pandas as pd
import numpy as np

# Geospatial
import geopandas as gpd
from shapely import wkt

# =============================
# Helpers
# =============================
def pick_first(df, candidates, required=True, what="column"):
    for c in candidates:
        if c in df.columns:
            return c
    if required:
        raise ValueError(f"Could not find {what}. Tried: {candidates}")
    return None

def guess_pred_col(df):
    # Common DSS scored names
    cands = [c for c in df.columns if (
        c.lower() == "prediction" or
        c.lower().startswith("prediction_") or
        c.lower().endswith("_prediction") or
        c.lower().endswith("_pred") or
        c.lower() in {"y_pred", "score", "pred"}
    )]
    if not cands:
        raise ValueError("Could not detect prediction column in scored dataset.")
    return cands[0]

def softmax_group(x: np.ndarray) -> np.ndarray:
    x = x - np.nanmax(x)
    ex = np.exp(x)
    s = np.nansum(ex)
    if s <= 0 or not np.isfinite(s):
        return np.full_like(x, 1.0 / len(x))
    return ex / s

def normalise_nonneg(x: np.ndarray) -> np.ndarray:
    x = np.clip(x, 0, None)
    s = x.sum()
    if s <= 0 or not np.isfinite(s):
        return np.full_like(x, 1.0 / len(x))
    return x / s

# =============================
# Read inputs (scored datasets)
# =============================
# r7 (fine) with features, target, predictions, and WKT geometry
r7_df = dataiku.Dataset("features_joined_1_prepared_scored").get_dataframe()
# r5 (coarse) with features, target, predictions, and WKT geometry
r5_df = dataiku.Dataset("features_joined_prepared_scored").get_dataframe()

# =============================
# Column detection
# =============================
# IDs (fallback to 'cell_id' if no explicit H3 ids)
r7_id_col = pick_first(r7_df, ["h3_r7", "r7_id", "h3_index", "h3", "cell_id"], what="r7 id")
r5_id_col = pick_first(r5_df, ["h3_r5", "r5_id", "h3_index", "h3", "cell_id"], what="r5 id")

# Prediction columns
r7_pred_col = guess_pred_col(r7_df)   # fine model outputs (scores or values)
r5_pred_col = guess_pred_col(r5_df)   # coarse model totals (values)

# Geometry columns (WKT assumed)
r7_geom_col = pick_first(r7_df, ["geometry", "wkt", "geom"], what="r7 geometry")
r5_geom_col = pick_first(r5_df, ["geometry", "wkt", "geom"], what="r5 geometry")

# Optional area weight at fine level
if "area_weight" not in r7_df.columns:
    r7_df["area_weight"] = 1.0

# =============================
# Convert to GeoDataFrames
# =============================
r7_gdf = gpd.GeoDataFrame(
    r7_df.copy(),
    geometry=r7_df[r7_geom_col].apply(wkt.loads),
    crs="EPSG:4326"
)
r5_gdf = gpd.GeoDataFrame(
    r5_df.copy(),
    geometry=r5_df[r5_geom_col].apply(wkt.loads),
    crs="EPSG:4326"
)

# Keep only what we need on r5 side for join: parent id + geometry
r5_gdf_for_join = r5_gdf[[r5_id_col, "geometry"]].rename(columns={r5_id_col: "r5_id"})

# =============================
# Spatial join r7 -> r5 (parent linkage)
# =============================
# Prefer modern GeoPandas API: predicate="within". If your environment is older, switch to op="within".
try:
    joined = gpd.sjoin(r7_gdf, r5_gdf_for_join, how="left", predicate="within")
except TypeError:
    # Fallback for older geopandas versions
    joined = gpd.sjoin(r7_gdf, r5_gdf_for_join, how="left", op="within")

# joined now contains an 'r5_id' column for each r7 polygon (where match was found)
missing_parent = joined["r5_id"].isna().sum()
if missing_parent > 0:
    # Drop or handle as needed; we drop them to maintain mass conservation
    joined = joined[~joined["r5_id"].isna()].copy()

# =============================
# Build parent totals map (r5)
# =============================
coarse_map = r5_df.set_index(r5_id_col)[r5_pred_col]

# Ensure we only keep r7 rows whose parent exists in r5 predictions
joined = joined[joined["r5_id"].isin(coarse_map.index)].copy()

# =============================
# CONFIG: how to interpret fine predictions
# =============================
# True  -> r7 predictions are scores/logits (can be negative/unscaled) -> softmax per parent
# False -> r7 predictions are positive values to be normalised per parent
FINE_IS_SCORE = True

# =============================
# Compute proportions within each parent (r5)
# =============================
# Standardise column names we need
joined = joined.rename(columns={
    r7_id_col: "r7_id",
    r7_pred_col: "fine_pred",
    "area_weight": "area_weight"
})

if FINE_IS_SCORE:
    joined["score_weighted"] = joined["fine_pred"] + np.log(np.clip(joined["area_weight"].to_numpy(), 1e-12, None))
    joined["p_hat"] = joined.groupby("r5_id")["score_weighted"].transform(
        lambda s: pd.Series(softmax_group(s.to_numpy()), index=s.index)
    )
else:
    joined["weight"] = np.clip(joined["fine_pred"], 0, None) * joined["area_weight"].clip(lower=0)
    joined["p_hat"] = joined.groupby("r5_id")["weight"].transform(
        lambda s: pd.Series(normalise_nonneg(s.to_numpy()), index=s.index)
    )

# =============================
# Allocate mass (ensure sums match parent)
# =============================
joined["Yc_hat_parent"] = joined["r5_id"].map(coarse_map)
joined["Y_hat"] = joined["p_hat"] * joined["Yc_hat_parent"]

# Sanity check: per-parent mass preservation
parent_sum = joined.groupby("r5_id")["Y_hat"].sum()
max_err = (parent_sum - coarse_map[parent_sum.index]).abs().max()
print("Max parent mass error:", float(max_err))

# =============================
# Output dataset
# =============================
# Keep minimal outputs (add columns if you want auditing)
pych_df = joined[["r7_id", "r5_id", "Y_hat", "p_hat"]].copy()

# Write to DSS output
out = dataiku.Dataset("pych")
out.write_with_schema(pych_df)
