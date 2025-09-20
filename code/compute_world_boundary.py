# -*- coding: utf-8 -*-
import dataiku
import pandas as pd
import geopandas as gpd
import os

# Path to shapefile folder (managed folder in DSS)
shapefile_path = "/home/hid24/dss_data/managed_folders/DISSERTATION/wHowFVsB"

# Load shapefile
gdf = gpd.read_file(shapefile_path)

# Reproject to WGS84
gdf = gdf.to_crs(epsg=4326)

# Optional: Filter only "Primary land" features, if needed
filtered = gdf[gdf["LAND_TYPE"] == "Primary land"]

# Rename to match output schema
all_countries_df = filtered

# Write to DSS dataset
all_countries_boundary = dataiku.Dataset("world_boundary")
all_countries_boundary.write_with_schema(all_countries_df)

