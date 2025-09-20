# -------------------------------------------------------------------------------- NOTEBOOK-CELL: CODE
# -*- coding: utf-8 -*-
import dataiku
import geopandas as gpd
import ee
from shapely import wkt

# === Initialize Earth Engine ===
ee.Initialize(project="diss2-466311")

# === Load DSS input: Mozambique hexes ===
hex_dataset = dataiku.Dataset("moz_h3_4")
df = hex_dataset.get_dataframe()

# Convert WKT strings to shapely geometries
gdf = gpd.GeoDataFrame(df, geometry=df["geometry"].apply(wkt.loads), crs="EPSG:4326")

# === Convert hex to EE FeatureCollection ===
def get_ee_feature(row):
    return ee.Feature(ee.Geometry(row.geometry.__geo_interface__), {"cell_id": row.cell_id})

features = [get_ee_feature(row) for _, row in gdf.iterrows()]
hex_fc = ee.FeatureCollection(features)

# === Load Google Open Buildings ===
moz_geom = gdf.unary_union
moz_ee_geom = ee.Geometry(moz_geom.__geo_interface__)
buildings_fc = ee.FeatureCollection("GOOGLE/Research/open-buildings/v3/polygons").filterBounds(moz_ee_geom)

# === Count buildings per hex ===
def count_buildings_in_hex(hex_feature):
    count = buildings_fc.filterBounds(hex_feature.geometry()).size()
    return hex_feature.set({'building_count': count})

results_fc = hex_fc.map(count_buildings_in_hex)

# === Export as a table to Google Cloud Storage ===
task = ee.batch.Export.table.toDrive(
    collection=results_fc,
    description='buzi_building_count_export',
    folder="EarthEngine_Exports",  # Your Google Drive folder
    fileNamePrefix='buzi_building_count',
    fileFormat='GeoJSON'
)

# Start the export task
task.start()
print("🚀 Export task started on GEE. Check task status in the Earth Engine Task Manager.")