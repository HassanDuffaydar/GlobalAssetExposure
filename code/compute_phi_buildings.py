# -*- coding: utf-8 -*-
import dataiku
import geopandas as gpd
import numpy as np
import pandas as pd
import ee
from shapely import wkt

# === Initialize Earth Engine ===
ee.Initialize(project="diss-463806")

# === Load DSS input: Philippines hexes ===
phi_h3_3 = dataiku.Dataset("phi_h3_3")
df = phi_h3_3.get_dataframe()

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

# === Load Microsoft Building Footprints for Philippines ===
# Source: https://planetarycomputer.microsoft.com/dataset/ms-buildings
# Earth Engine path:
buildings_fc = ee.FeatureCollection('projects/sat-io/open-datasets/MSBuildings/Philippines')

# === Count buildings intersecting each hex ===
def count_buildings_in_hex(hex_feature):
    hex_geom = hex_feature.geometry()
    buildings_in_hex = buildings_fc.filterBounds(hex_geom)
    building_count = buildings_in_hex.size()
    return hex_feature.set({'building_count': building_count})

# Apply the counting function to each hex
results_fc = hex_fc.map(count_buildings_in_hex)

# === Convert EE FeatureCollection to GeoDataFrame ===
results = results_fc.getInfo()
results_gdf = gpd.GeoDataFrame.from_features(results['features'], crs="EPSG:4326")

# === Convert geometry to WKT for DSS dataset compatibility ===
results_gdf["geometry"] = results_gdf["geometry"].apply(lambda g: g.wkt)
phi_buildings_df = pd.DataFrame(results_gdf)

# === Write to DSS output dataset ===
phi_buildings = dataiku.Dataset("phi_buildings")
phi_buildings.write_with_schema(phi_buildings_df)
