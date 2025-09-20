# -*- coding: utf-8 -*-
import dataiku
import geopandas as gpd
import numpy as np
import pandas as pd
import ee
from shapely import wkt

# === Initialize Earth Engine ===
ee.Initialize(project="diss2-466311")

# === Load DSS input: Mozambique H3 hexes ===
# Dataset moz_h3_3 renamed to moz_h3_4 by admin on 2025-07-23 23:14:08
moz_h3_3 = dataiku.Dataset("moz_h3_4")
df = moz_h3_3.get_dataframe()

# === Convert WKT to shapely geometry
gdf = gpd.GeoDataFrame(df, geometry=df["geometry"].apply(wkt.loads), crs="EPSG:4326")

# === Convert GeoDataFrame to EE FeatureCollection
def get_ee_feature(row):
    x, y = row.geometry.exterior.coords.xy
    coords = np.dstack((x, y)).tolist()
    geom = ee.Geometry.Polygon(coords)
    return ee.Feature(geom, {"cell_id": row.cell_id})

features = [get_ee_feature(row) for _, row in gdf.iterrows()]
hex_fc = ee.FeatureCollection(features)

# === Load VIDA building footprints for Mozambique
buildings_fc = ee.FeatureCollection("projects/sat-io/open-datasets/VIDA_COMBINED/MOZ")

# === Function to count buildings and sum area per hex
def summarize_buildings(hex_feature):
    hex_geom = hex_feature.geometry()
    buildings_in_hex = buildings_fc.filterBounds(hex_geom)

    building_count = buildings_in_hex.size()
    building_area_sum = buildings_in_hex.aggregate_sum("area_in_meters")  # Assuming "area" is the field in m²

    return hex_feature.set({
        "building_count": building_count,
        "building_area_m2": building_area_sum
    })

# Apply the function
results_fc = hex_fc.map(summarize_buildings)

# === Retrieve results to Python
results = results_fc.getInfo()
results_gdf = gpd.GeoDataFrame.from_features(results["features"], crs="EPSG:4326")

# === Convert geometry to WKT
results_gdf["geometry"] = results_gdf["geometry"].apply(lambda g: g.wkt)
moz_buildingarea_df = pd.DataFrame(results_gdf)

# === Write to DSS output dataset
# Dataset moz_buildingarea renamed to moz_buildingarea_1 by admin on 2025-07-23 23:14:08
moz_buildingarea = dataiku.Dataset("moz_buildingarea_1")
moz_buildingarea.write_with_schema(moz_buildingarea_df)


