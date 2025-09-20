# -------------------------------------------------------------------------------- NOTEBOOK-CELL: CODE
import geopandas as gpd
from io import StringIO
import ee
import pandas as pd
import dataiku
ee.Authenticate()

# -------------------------------------------------------------------------------- NOTEBOOK-CELL: CODE

# Initialize Earth Engine (do this once per session)
# -*- coding: utf-8 -*-
import dataiku
import geopandas as gpd
import numpy as np
import pandas as pd
import ee
from shapely import wkt

# === Initialize Earth Engine with project ===
ee.Initialize(project="diss-463806")

# === Load DSS hex input ===
# Dataset phi_h3_3 renamed to moz_h3_3 by admin on 2025-07-17 22:22:52
moz_h3_3 = dataiku.Dataset("moz_h3_3")
df = moz_h3_3.get_dataframe()

# === Convert geometry column from WKT to shapely ===
gdf = gpd.GeoDataFrame(df, geometry=df["geometry"].apply(wkt.loads), crs="EPSG:4326")

# === Convert to Earth Engine FeatureCollection ===
def get_ee_feature(row):
    x, y = row.geometry.exterior.coords.xy
    coords = np.dstack((x, y)).tolist()
    geom = ee.Geometry.Polygon(coords)
    return ee.Feature(geom, {"cell_id": row.cell_id})

features = [get_ee_feature(row) for idx, row in gdf.iterrows()]
hex_fc = ee.FeatureCollection(features)

# === Load VIIRS nightlights image and compute mean ===
# Dataset phi_light renamed to moz_light by admin on 2025-07-17 22:22:52
# Dataset moz_light renamed to moz_ghsl by admin on 2025-07-23 22:48:36
# === Load GHSL Built-up Surface image for 2025 ===
# Dataset moz_ghsl renamed to moz_ghsl_landuse by admin on 2025-07-23 22:55:56
# === Load GHSL Built-up Classification image for 2018 ===
ghsl_lu_img = ee.Image('JRC/GHSL/P2023A/GHS_BUILT_C/2018')

# === Reduce majority class per hex (i.e., most common class) ===
# === Reduce histogram of land use classes (more reliable than mode) ===
landuse_stats = ghsl_lu_img.reduceRegions(
    collection=hex_fc,
    reducer=ee.Reducer.frequencyHistogram(),
    scale=100,
    tileScale=4
).getInfo()

# === Convert result to GeoDataFrame ===
landuse_stats_gdf = gpd.GeoDataFrame.from_features(landuse_stats['features'], crs="EPSG:4326")

# === Extract most frequent class, ignoring 0 ===
def get_top_class_excluding_zero(hist):
    if not isinstance(hist, dict):
        return None
    parsed = {int(k): v for k, v in hist.items()}
    non_zero = {k: v for k, v in parsed.items() if k != 0}
    return max(non_zero, key=non_zero.get) if non_zero else None

# Apply it
landuse_stats_gdf["landuse_class"] = landuse_stats_gdf["histogram"].apply(get_top_class_excluding_zero)




#df_output["geometry"] = df_output["geometry"].apply(lambda g: g.wkt)
moz_h3_3_df = pd.DataFrame(landuse_stats_gdf)

# === Write to DSS output dataset ===
phi_h3_3 = dataiku.Dataset("moz_ghsl_landuse")
phi_h3_3.write_with_schema(moz_h3_3_df)