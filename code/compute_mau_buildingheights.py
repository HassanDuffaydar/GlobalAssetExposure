# -*- coding: utf-8 -*-
import dataiku
import geopandas as gpd
import numpy as np
import pandas as pd
import ee
from shapely import wkt

# === Initialize Earth Engine ===
ee.Initialize(project="diss-463806")

# === Load DSS input: hexes ===
# Dataset moz_h3_3 renamed to mau_h3_3 by admin on 2025-07-20 20:13:59
moz_h3_3 = dataiku.Dataset("mau_h3_3")
df = moz_h3_3.get_dataframe()

# === Convert WKT strings to shapely geometries ===
gdf = gpd.GeoDataFrame(df, geometry=df["geometry"].apply(wkt.loads), crs="EPSG:4326")

# === Convert GeoDataFrame to Earth Engine FeatureCollection ===
def get_ee_feature(row):
    x, y = row.geometry.exterior.coords.xy
    coords = np.dstack((x, y)).tolist()
    geom = ee.Geometry.Polygon(coords)
    return ee.Feature(geom, {"cell_id": row.cell_id})

features = [get_ee_feature(row) for _, row in gdf.iterrows()]
hex_fc = ee.FeatureCollection(features)

# === Load JRC GHSL building height image for 2018 ===
height_img = ee.Image("JRC/GHSL/P2023A/GHS_BUILT_H/2018").select("built_height")

# === Compute average height per hex ===
results_fc = height_img.reduceRegions(
    collection=hex_fc,
    reducer=ee.Reducer.mean(),
    scale=100,        # GHS dataset has 100m resolution
    tileScale=1
)

# === Retrieve results from EE to Python ===
results = results_fc.getInfo()
results_gdf = gpd.GeoDataFrame.from_features(results['features'], crs="EPSG:4326")

# === Rename column for clarity ===
results_gdf = results_gdf.rename(columns={"mean": "avg_building_height_m"})

# === Convert geometry to WKT for DSS output ===
results_gdf["geometry"] = results_gdf["geometry"].apply(lambda g: g.wkt)
moz_buildingheights_df = pd.DataFrame(results_gdf)

# === Write results to DSS dataset ===
# Dataset moz_buildingheights renamed to mau_buildingheights by admin on 2025-07-20 20:13:59
moz_buildingheights = dataiku.Dataset("mau_buildingheights")
moz_buildingheights.write_with_schema(moz_buildingheights_df)

