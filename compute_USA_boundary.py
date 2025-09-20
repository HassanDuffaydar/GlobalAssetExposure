# -------------------------------------------------------------------------------- NOTEBOOK-CELL: CODE
#pip install geopandas

# -------------------------------------------------------------------------------- NOTEBOOK-CELL: CODE
# -*- coding: utf-8 -*-
import dataiku
import pandas as pd
import geopandas as gpd
import os

# Set path directly based on your note
shapefile_path = "/home/hid24/dss_data/managed_folders/DISSERTATION/wHowFVsB"

# Load the shapefile using GeoPandas
gdf = gpd.read_file(shapefile_path)
# If needed, convert (e.g., to WGS84 - EPSG:4326)
gdf = gdf.to_crs(epsg=4326)
# Hardcoded country filter
country_name = "United States"

# Replace column names as appropriate for your shapefile
filtered = gdf[
    (gdf["COUNTRY"] == country_name) &
    (gdf["LAND_TYPE"] == "Primary land")
]

USA_boundary_df=filtered
# Write to DSS output dataset
USA_boundary = dataiku.Dataset("USA_boundary")
USA_boundary.write_with_schema(USA_boundary_df)