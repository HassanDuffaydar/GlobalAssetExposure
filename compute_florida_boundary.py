# -------------------------------------------------------------------------------- NOTEBOOK-CELL: CODE
#pip install geopandas

# -------------------------------------------------------------------------------- NOTEBOOK-CELL: CODE
# -*- coding: utf-8 -*-
import dataiku
import pandas as pd
import geopandas as gpd
import os

# Set path directly based on your note
shapefile_path = "/home/hid24/dss_data/managed_folders/DISSERTATION/1VEEioVC"

# Load the shapefile using GeoPandas
gdf = gpd.read_file(shapefile_path)
gdf.set_crs(epsg=26917, inplace=True)
# If needed, convert (e.g., to WGS84 - EPSG:4326)
gdf = gdf.to_crs(epsg=4326)
# Hardcoded country filter



# Write to DSS output dataset
# Dataset USA_boundary renamed to florida_boundary by admin on 2025-07-21 15:26:53
USA_boundary = dataiku.Dataset("florida_boundary")
USA_boundary.write_with_schema(gdf)