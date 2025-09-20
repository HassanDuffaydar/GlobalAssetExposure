# -*- coding: utf-8 -*-
import dataiku
import pandas as pd
import geopandas as gpd
import os

# Access folder containing shapefile components
moz_exp = dataiku.Folder("kNjR86sy")
folder_path = moz_exp.get_path()

# Find all .shp files (each represents a shapefile set)
shp_files = [f for f in os.listdir(folder_path) if f.lower().endswith(".shp")]

gdfs = []
for shp_file in shp_files:
    full_path = os.path.join(folder_path, shp_file)
    try:
        print(f"Reading shapefile: {shp_file}")
        gdf = gpd.read_file(full_path)
        gdf["source_file"] = shp_file  # Optional: track source
        gdfs.append(gdf)
    except Exception as e:
        print(f"Error reading {shp_file}: {e}")

# Combine all shapefiles into one dataframe
if gdfs:
    combined_gdf = pd.concat(gdfs, ignore_index=True)
else:
    combined_gdf = pd.DataFrame()

# Drop geometry column if your output dataset is non-spatial
moz_exp_2015_df = combined_gdf.drop(columns='geometry', errors='ignore')

# Write to DSS dataset
# Dataset moz_exp_2015 renamed to moz_exp_2016 by admin on 2025-07-23 23:14:08
moz_exp_2015 = dataiku.Dataset("moz_exp_2016")
moz_exp_2015.write_with_schema(moz_exp_2015_df)
