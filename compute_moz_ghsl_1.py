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
# Dataset moz_h3_3 renamed to moz_h3_4 by admin on 2025-07-23 23:14:08
moz_h3_3 = dataiku.Dataset("moz_h3_4")
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
# Dataset moz_ghsl renamed to moz_ghsl_1 by admin on 2025-07-23 23:14:08
ghsl_img = ee.Image('JRC/GHSL/P2023A/GHS_BUILT_S/2025') \
    .select('built_surface')

# === Reduce built-up area per hex ===
built_stats = ghsl_img.reduceRegions(
    collection=hex_fc,
    reducer=ee.Reducer.mean(),
    scale=100,
    tileScale=4
).getInfo()

# === Convert to GeoDataFrame ===
built_stats_gdf = gpd.GeoDataFrame.from_features(built_stats['features'], crs="EPSG:4326")
built_stats_gdf = built_stats_gdf.rename(columns={"mean": "mean_built_m2"})




#df_output["geometry"] = df_output["geometry"].apply(lambda g: g.wkt)
moz_h3_3_df = pd.DataFrame(built_stats_gdf)

# === Write to DSS output dataset ===
phi_h3_3 = dataiku.Dataset("moz_ghsl_1")
phi_h3_3.write_with_schema(moz_h3_3_df)