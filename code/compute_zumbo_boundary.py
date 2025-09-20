# -*- coding: utf-8 -*-
import dataiku
import pandas as pd
import geopandas as gpd
import os

# Set path directly based on your note
shapefile_path = "/home/hid24/dss_data/managed_folders/DISSERTATION/PdL5Zs7q/moz_admbnda_adm3_ine_20190607.shp"

# Load the shapefile using GeoPandas
gdf = gpd.read_file(shapefile_path)

# Reproject to WGS84 (if needed)
gdf = gdf.to_crs(epsg=4326)

# Hardcoded country filter


# Replace column names as appropriate for your shapefile
filtered = gdf[
    (gdf["ADM3_PT"] == "Chiputu") ]

# Assign result
moz_boundary_df = filtered

# Write to DSS output dataset
# Dataset mozambique_boundary renamed to buzi_boundary by admin on 2025-07-24 20:11:03
# Dataset buzi_boundary renamed to zumbo_boundary by admin on 2025-07-27 14:31:57
# Dataset zumbo_boundary renamed to maravia_boundary by admin on 2025-07-27 14:35:08
USA_boundary = dataiku.Dataset("maravia_boundary")
USA_boundary.write_with_schema(moz_boundary_df)
