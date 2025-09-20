# -*- coding: utf-8 -*-
import dataiku
import geopandas as gpd
import numpy as np
import pandas as pd
import ee
from shapely import wkt

# === EE Authentication ===
ee.Initialize(project="diss2-466311")

# === Load DSS input: hexes ===
# Dataset moz_h3_3 renamed to moz_h3_6 by admin on 2025-08-10 10:30:08
usa_h3_3 = dataiku.Dataset("moz_h3_6")
df = usa_h3_3.get_dataframe()
gdf = gpd.GeoDataFrame(df, geometry=df["geometry"].apply(wkt.loads), crs="EPSG:4326")

# === Convert to EE FeatureCollection ===
def get_ee_feature(row):
    x, y = row.geometry.exterior.coords.xy
    coords = np.dstack((x, y)).tolist()
    geom = ee.Geometry.Polygon(coords)
    return ee.Feature(geom, {"cell_id": row.cell_id})

features = [get_ee_feature(row) for _, row in gdf.iterrows()]
hex_fc = ee.FeatureCollection(features)

# === Load Microsoft Buildings dataset for Mozambique ===
buildings_fc = ee.FeatureCollection('projects/sat-io/open-datasets/MSBuildings/Mozambique')

# === Count buildings AND sum area in each hex ===
def summarize_buildings(hex_feature):
    hex_geom = hex_feature.geometry()
    buildings_in_hex = buildings_fc.filterBounds(hex_geom)

    building_count = buildings_in_hex.size()
    total_area = buildings_in_hex.aggregate_sum("area")  # Change "area" if needed

    return hex_feature.set({
        "building_count": building_count,
        "building_area_m2": total_area
    })

# === Apply function to each hex
results_fc = hex_fc.map(summarize_buildings)

# === Bring results to Python
results = results_fc.getInfo()
results_gdf = gpd.GeoDataFrame.from_features(results["features"], crs="EPSG:4326")

# === Convert geometry to WKT for DSS output
results_gdf["geometry"] = results_gdf["geometry"].apply(lambda g: g.wkt)
usa_buildings_df = pd.DataFrame(results_gdf)

# === Write to DSS output dataset
usa_buildings = dataiku.Dataset("mozambique_buildings")
usa_buildings.write_with_schema(usa_buildings_df)
