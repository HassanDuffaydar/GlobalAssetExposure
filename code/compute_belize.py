# -*- coding: utf-8 -*-
import dataiku
import pandas as pd
import geopandas as gpd
import os

# === 1. Load GeoJSON file ===
shapefile_path = "/home/hid24/dss_data/managed_folders/DISSERTATION/4SLP4WOf/blz_admbnda_adm1_gadm_20210910.shp"
gdf = gpd.read_file(shapefile_path)

# Ensure CRS is WGS84
gdf = gdf.to_crs(epsg=4326)

# === 2. Filter for Funafuti (check shapeName column) ===
filtered = gdf[gdf["ADM1_EN"].str.contains("Belize", case=False, na=False)]

# === 3. Write to Dataiku output dataset ===
# Dataset Funafati renamed to mauritius by admin on 2025-07-30 21:50:47
# Dataset mauritius renamed to belize by admin on 2025-07-30 21:54:50
funafuti_boundary = dataiku.Dataset("belize")
funafuti_boundary.write_with_schema(gdf)
