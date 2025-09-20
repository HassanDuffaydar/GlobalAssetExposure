# -*- coding: utf-8 -*-
import dataiku
import pandas as pd
import geopandas as gpd
from dataiku import pandasutils as pdu

# Read recipe inputs - managed folder containing shapefile components (.shp, .dbf, .shx, etc.)
world_heights_folder = dataiku.Folder("DOKCcawK")
folder_path = world_heights_folder.get_path()

# Path to the .shp file in the folder
# Replace 'your_file.shp' with the actual filename in the managed folder
shapefile_path = folder_path + "/world_grid.shp"

# Read shapefile into GeoDataFrame
gdf = gpd.read_file(shapefile_path)

# (Optional) Convert geometry to WKT for storage in Dataiku dataset
gdf["geometry"] = gdf["geometry"].apply(lambda geom: geom.wkt)

# Create Pandas DataFrame
world_height_df = pd.DataFrame(gdf)

# Write recipe outputs
world_height = dataiku.Dataset("world_height")
world_height.write_with_schema(world_height_df)
