# -*- coding: utf-8 -*-
import dataiku
import pandas as pd
import geopandas as gpd
import os

# === 1. Load GeoJSON file ===
shapefile_path = "/home/hid24/dss_data/managed_folders/DISSERTATION/Bt3K0JtY/geoBoundaries-TUV-ADM3_simplified.shp"
gdf = gpd.read_file(shapefile_path)

# Ensure CRS is WGS84
gdf = gdf.to_crs(epsg=4326)

# === 2. Filter for Funafuti (check shapeName column) ===
filtered = gdf[gdf["shapeName"].str.contains("Funafuti", case=False, na=False)]

# === 3. Write to Dataiku output dataset ===
funafuti_boundary = dataiku.Dataset("Funafati")
funafuti_boundary.write_with_schema(gdf)

