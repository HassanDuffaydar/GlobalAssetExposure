# -------------------------------------------------------------------------------- NOTEBOOK-CELL: CODE
# -*- coding: utf-8 -*-
import dataiku
import geopandas as gpd
import numpy as np
import pandas as pd
import ee
from shapely import wkt

ee.Authenticate(auth_mode='notebook')

# === Initialize EE with your correct project ID ===
ee.Initialize(project="diss2-466311")

# -------------------------------------------------------------------------------- NOTEBOOK-CELL: CODE


# === Load DSS input: USA hexes ===
# Dataset USA_h3_3 renamed to moz_h3_3 by admin on 2025-07-18 11:12:57
# Dataset moz_h3_3 renamed to moz_h3_4 by admin on 2025-07-23 23:14:08
usa_h3_3 = dataiku.Dataset("moz_h3_4")
df = usa_h3_3.get_dataframe()

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

# === Load Microsoft Building Footprints for USA ===
# Dataset: https://planetarycomputer.microsoft.com/dataset/ms-buildings
# EE path for USA: 'projects/sat-io/open-datasets/MSBuildings/US'
buildings_fc = ee.FeatureCollection('projects/sat-io/open-datasets/MSBuildings/Mozambique')

# === Count buildings intersecting each hex ===
def count_buildings_in_hex(hex_feature):
    hex_geom = hex_feature.geometry()
    buildings_in_hex = buildings_fc.filterBounds(hex_geom)
    building_count = buildings_in_hex.size()
    return hex_feature.set({'building_count': building_count})

# Apply function to each hex
results_fc = hex_fc.map(count_buildings_in_hex)

# === Bring results back to Python ===
results = results_fc.getInfo()
results_gdf = gpd.GeoDataFrame.from_features(results['features'], crs="EPSG:4326")

# === Convert geometry to WKT for DSS output ===
results_gdf["geometry"] = results_gdf["geometry"].apply(lambda g: g.wkt)
usa_buildings_df = pd.DataFrame(results_gdf)

# === Write results to DSS dataset ===
# Dataset usa_buildings renamed to mozambique_buildings by admin on 2025-07-18 11:12:57
# Dataset mozambique_buildings renamed to mozambique_buildings_1 by admin on 2025-07-23 23:14:08
usa_buildings = dataiku.Dataset("mozambique_buildings_1")
usa_buildings.write_with_schema(usa_buildings_df)