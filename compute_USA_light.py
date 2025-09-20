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
# Dataset moz_h3_3 renamed to USA_h3_3 by admin on 2025-07-17 22:25:18
usa_h3_3 = dataiku.Dataset("USA_h3_3")
df = usa_h3_3.get_dataframe()

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
# Dataset moz_light renamed to USA_light by admin on 2025-07-17 22:25:18
nightlights_img = ee.ImageCollection('NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG') \
    .filterDate('2021-01-01', '2021-12-31') \
    .select('avg_rad') \
    .mean()

# === Reduce nightlight mean per hex ===
zone_stats = nightlights_img.reduceRegions(
    collection=hex_fc,
    reducer=ee.Reducer.mean(),
    scale=500,
    tileScale=1
).getInfo()

# === Convert to GeoDataFrame ===
zone_stats_gdf = gpd.GeoDataFrame.from_features(zone_stats['features'], crs="EPSG:4326")
zone_stats_gdf = zone_stats_gdf.rename(columns={"mean": "mean_light"})




#df_output["geometry"] = df_output["geometry"].apply(lambda g: g.wkt)
usa_h3_3_df = pd.DataFrame(zone_stats_gdf)

# === Write to DSS output dataset ===
usa_h3_3 = dataiku.Dataset("USA_light")
usa_h3_3.write_with_schema(usa_h3_3_df)