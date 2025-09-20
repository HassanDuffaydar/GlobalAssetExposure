# -*- coding: utf-8 -*-
import dataiku
import pandas as pd, numpy as np
import geopandas as gpd
from shapely import wkt

# === Load datasets ===
# Building footprints (us_read) -> contains geometry of buildings
# Dataset us_read renamed to al_read by admin on 2025-08-17 14:29:38
# Dataset al_read renamed to us_read by admin on 2025-08-17 14:48:44
us_read = dataiku.Dataset("us_read")
us_read_df = us_read.get_dataframe()

# Hex grid (res 7 hexes)
USA_7 = dataiku.Dataset("USA_7")
USA_7_df = USA_7.get_dataframe()

# === Convert to GeoDataFrames ===
# Building footprints
buildings_gdf = gpd.GeoDataFrame(
    us_read_df,
    geometry=gpd.GeoSeries.from_wkt(us_read_df["geometry"]),
    crs="EPSG:4326"
)

# Hexes
hexes_gdf = gpd.GeoDataFrame(
    USA_7_df,
    geometry=gpd.GeoSeries.from_wkt(USA_7_df["geometry"]),
    crs="EPSG:4326"
)

# === Spatial join: count buildings per hex ===
# Ensure buildings fall inside hexes
join = gpd.sjoin(buildings_gdf, hexes_gdf, how="left", predicate="within")

# Count buildings per hex_id
bld_counts = join.groupby("cell_id").size().reset_index(name="bld_count")

# Merge counts back to hex polygons
hex_with_counts = hexes_gdf.merge(bld_counts, on="cell_id", how="left")

# Replace NaN counts with 0 (hexes that had no buildings)
hex_with_counts["bld_count"] = hex_with_counts["bld_count"].fillna(0).astype(int)

# === Drop building-level geometry, keep only hex geometry ===
usa_plot_df = pd.DataFrame(hex_with_counts.drop(columns=["geometry"]))
usa_plot_df["geometry"] = hex_with_counts["geometry"].apply(lambda g: g.wkt)

# === Write recipe outputs ===
# Dataset usa_plot renamed to florida-gem by admin on 2025-08-17 14:48:44
usa_plot = dataiku.Dataset("florida-gem")
usa_plot.write_with_schema(usa_plot_df)
