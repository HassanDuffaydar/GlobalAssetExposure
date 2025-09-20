# -*- coding: utf-8 -*-
import dataiku
import pandas as pd
import geopandas as gpd
import os

# Set path directly based on your note
shapefile_path = "/home/hid24/dss_data/managed_folders/DISSERTATION/wHowFVsB"

# Load the shapefile using GeoPandas
gdf = gpd.read_file(shapefile_path)

# Reproject to WGS84 (if needed)
gdf = gdf.to_crs(epsg=4326)

# Hardcoded country filter
country_name = "Mozambique"

# Replace column names as appropriate for your shapefile
filtered = gdf[
    (gdf["COUNTRY"] == country_name) &
    (gdf["LAND_TYPE"] == "Primary land")
]

# Assign result
moz_boundary_df = filtered

# Write to DSS output dataset
USA_boundary = dataiku.Dataset("mozambique_boundary")
USA_boundary.write_with_schema(moz_boundary_df)
