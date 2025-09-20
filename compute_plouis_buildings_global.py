# -*- coding: utf-8 -*-
import dataiku
import ee

# Authenticate and initialize Earth Engine
ee.Authenticate(auth_mode='notebook')
ee.Initialize(project="diss2-466311")

# === 1. Load Mauritius boundary from DSS ===
mauritius = dataiku.Dataset("mauritius")
mauritius_df = mauritius.get_dataframe()

# Take the first geometry (assuming one boundary)
import geopandas as gpd
from shapely import wkt

mauritius_gdf = gpd.GeoDataFrame(mauritius_df, geometry=mauritius_df["geometry"].apply(wkt.loads), crs="EPSG:4326")
# Convert to Earth Engine geometry
mauritius_geom = mauritius_gdf.unary_union 
mauritius_ee_geom = ee.Geometry.Polygon(list(mauritius_geom.exterior.coords))
# === 2. Load building datasets ===
google_buildings = ee.FeatureCollection("GOOGLE/Research/open-buildings/v3/polygons").filterBounds(mauritius_ee_geom)
microsoft_buildings = ee.FeatureCollection("projects/sat-io/open-datasets/MSBuildings/Mauritius").filterBounds(mauritius_ee_geom)

# === 3. Add source flag ===
google_buildings = google_buildings.map(lambda f: f.set("source", "google"))
microsoft_buildings = microsoft_buildings.map(lambda f: f.set("source", "microsoft"))

# === 4. Merge the two datasets ===
all_buildings = google_buildings.merge(microsoft_buildings)

# === 5. Export to Google Drive ===
task = ee.batch.Export.table.toDrive(
    collection=all_buildings,
    description="Mauritius_Buildings_Export",
    folder="EarthEngine_Exports",  # Your Google Drive folder
    fileNamePrefix="mauritius_buildings",
    fileFormat="GeoJSON"
)
task.start()

print("Export started. Check your Google Drive in 'EarthEngine_Exports' folder.")

