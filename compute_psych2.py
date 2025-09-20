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
    # Typical DSS scored names
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
        return np.full_like(x, 1.0/len(x))
    return ex / s

def normalise_nonneg(x: np.ndarray) -> np.ndarray:
    x = np.clip(x, 0, None)
    s = x.sum()
    if s <= 0 or not np.isfinite(s):
        return np.full_like(x, 1.0/len(x))
    return x / s

# =============================
# Read inputs (scored datasets)
# =============================
r7_df = dataiku.Dataset("features_joined_1_prepared_scored").get_dataframe()  # fine (r7)
r5_df = dataiku.Dataset("features_joined_prepared_scored").get_dataframe()    # coarse (r5)

# =============================
# Column detection
# =============================
r7_id_col   = pick_first(r7_df, ["h3_r7","r7_id","h3_index","h3","cell_id"], what="r7 id")
r5_id_col   = pick_first(r5_df, ["h3_r5","r5_id","h3_index","h3","cell_id"], what="r5 id")
r7_pred_col = guess_pred_col(r7_df)   # fine model outputs (scores or values)
r5_pred_col = guess_pred_col(r5_df)   # coarse model totals (values)
r7_geom_col = pick_first(r7_df, ["geometry","wkt","geom"], what="r7 geometry")
r5_geom_col = pick_first(r5_df, ["geometry","wkt","geom"], what="r5 geometry")

# Optional fine-level weight (kept at 1 if absent)
if "area_weight" not in r7_df.columns:
    r7_df["area_weight"] = 1.0

# =============================
# Build GeoDataFrames (assume WKT)
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

# =============================
# Reproject to equal-area CRS for accurate overlap areas
# =============================
try:
    ea_crs = r7_gdf.estimate_utm_crs()
except Exception:
    ea_crs = "EPSG:6933"  # World Equidistant Cylindrical as fallback

r7_ea = r7_gdf.to_crs(ea_crs)
r5_ea = r5_gdf.to_crs(ea_crs)

# Keep slim copies (ids + geometry)
r7_slim = r7_ea[[r7_id_col, "geometry"]].rename(columns={r7_id_col: "r7_id"})
r5_slim = r5_ea[[r5_id_col, "geometry"]].rename(columns={r5_id_col: "r5_id"})

# =============================
# Candidate (r7, r5) pairs by bbox/si join, then exact intersection
# =============================
try:
    cand = gpd.sjoin(r7_slim, r5_slim, how="inner", predicate="intersects")[["r7_id","r5_id"]].drop_duplicates()
except TypeError:
    cand = gpd.sjoin(r7_slim, r5_slim, how="inner", op="intersects")[["r7_id","r5_id"]].drop_duplicates()

cand = cand.merge(r7_slim, on="r7_id", how="left")
cand = cand.merge(r5_slim.rename(columns={"geometry":"geom_r5"}), on="r5_id", how="left")
cand = gpd.GeoDataFrame(cand, geometry="geometry", crs=ea_crs)

# Exact intersections (one row per (r7, r5))
cand["geom_int"] = cand.apply(lambda r: r["geometry"].intersection(r["geom_r5"]), axis=1)
pairs = gpd.GeoDataFrame(cand.drop(columns=["geometry"]), geometry="geom_int", crs=ea_crs)
pairs = pairs[~pairs["geom_int"].is_empty & pairs["geom_int"].notna()].copy()

# =============================
# Area fractions for partial coverage
# =============================
r7_area = r7_slim.copy()
r7_area["a_r7"] = r7_area.area
a_r7_map = r7_area.set_index("r7_id")["a_r7"]

pairs["a_int"] = pairs.area
pairs["a_r7"]  = pairs["r7_id"].map(a_r7_map)
pairs["area_frac"] = (pairs["a_int"] / pairs["a_r7"]).clip(lower=0, upper=1).fillna(0)
pairs = pairs[pairs["area_frac"] > 0].copy()

# =============================
# Bring predictions & totals
# =============================
# Fine predictions & optional weight
pairs = pairs.merge(
    r7_df[[r7_id_col, r7_pred_col, "area_weight"]].rename(columns={r7_id_col:"r7_id", r7_pred_col:"fine_pred"}),
    on="r7_id", how="left"
)

# Coarse totals map (parent mass)
coarse_map = r5_df.set_index(r5_id_col)[r5_pred_col]
pairs = pairs[pairs["r5_id"].isin(coarse_map.index)].copy()

# =============================
# CONFIG: how to interpret fine predictions
# =============================
# True  -> r7 predictions are scores/logits (can be negative/unscaled) -> softmax per parent
# False -> r7 predictions are positive values to be normalised per parent
FINE_IS_SCORE = True

# =============================
# Proportions within each r5 parent (include area_frac)
# =============================
if FINE_IS_SCORE:
    pairs["score_w"] = (pairs["fine_pred"]
                        + np.log(np.clip(pairs["area_weight"].to_numpy(), 1e-12, None))
                        + np.log(np.clip(pairs["area_frac"].to_numpy(), 1e-12, None)))
    pairs["p_hat_pair"] = pairs.groupby("r5_id")["score_w"].transform(
        lambda s: pd.Series(softmax_group(s.to_numpy()), index=s.index)
    )
else:
    pairs["w"] = np.clip(pairs["fine_pred"], 0, None) * pairs["area_weight"].clip(lower=0) * pairs["area_frac"]
    pairs["p_hat_pair"] = pairs.groupby("r5_id")["w"].transform(
        lambda s: pd.Series(normalise_nonneg(s.to_numpy()), index=s.index)
    )

# =============================
# Allocate per (r7, r5) fragment, preserve mass per r5
# =============================
pairs["Yc_hat_parent"] = pairs["r5_id"].map(coarse_map)
pairs["Y_pair_hat"]    = pairs["p_hat_pair"] * pairs["Yc_hat_parent"]

# Mass preservation check (per r5)
parent_err = (pairs.groupby("r5_id")["Y_pair_hat"].sum() - coarse_map).abs().max()
print("Max parent mass error:", float(parent_err))

# =============================
# Sum fragments back to r7 totals
# =============================
r7_alloc = pairs.groupby("r7_id", as_index=False)["Y_pair_hat"].sum().rename(columns={"Y_pair_hat":"Y_r7_hat"})

# =============================
# Output dataset (r7 totals)
# =============================
pych_df = r7_alloc.copy()   # columns: r7_id, Y_r7_hat

# If you also want proportions at r7 level, you can compute them vs sum of all r7 in each r5,
# but typically the final need is the mass-preserving Y_r7_hat.

# Dataset pych renamed to psych2 by admin on 2025-08-10 15:47:42
out = dataiku.Dataset("psych2")
out.write_with_schema(pych_df)

out = dataiku.Dataset("psych3")
out.write_with_schema(pairs)