# -*- coding: utf-8 -*-
import dataiku
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
from shapely import wkt

# === 1. Load exposure dataset ===
# Dataset Exposure_res_moz renamed to Exposure_Res_Florida by admin on 2025-07-21 17:35:55
exposure_ds = dataiku.Dataset("Exposure_Res_Florida")  # <-- Replace with your dataset name
exposure_df = exposure_ds.get_dataframe()

# === 2. Convert lat/lon to GeoDataFrame ===
geometry = [Point(xy) for xy in zip(exposure_df["LONGITUDE"], exposure_df["LATITUDE"])]
gdf_clipped = gpd.GeoDataFrame(exposure_df, geometry=geometry, crs="EPSG:4326")

# === 3. Load H3 hex grid ===
# Dataset moz_h3_3 renamed to flo_h3_3 by admin on 2025-07-21 17:35:55
hex_ds = dataiku.Dataset("flo_h3_3")
hex_df = hex_ds.get_dataframe()
hexgrid = gpd.GeoDataFrame(
    hex_df,
    geometry=hex_df["geometry"].apply(wkt.loads),
    crs="EPSG:4326"
)

# === 4. Spatial join: assign points to hex ===
joined = gpd.sjoin(gdf_clipped, hexgrid, how="inner", predicate="within")

# === 5. Aggregate total replacement cost per hex ===
agg = joined.groupby('cell_id')['TOTAL_REPL_COST_USD'].sum().reset_index()

# === 6. Merge totals back into hex grid ===
hexgrid = hexgrid.merge(agg, on="cell_id", how="left")
hexgrid["TOTAL_REPL_COST_USD"] = hexgrid["TOTAL_REPL_COST_USD"].fillna(0)

# === 7. Compute GDP density (USD/km²) ===
hex_area_km2 = 1054.2  # Approximate area for H3 res 3
hexgrid["gdp_density"] = hexgrid["TOTAL_REPL_COST_USD"] / hex_area_km2

# === 8. Convert geometry to WKT for DSS ===
hexgrid["geometry"] = hexgrid["geometry"].apply(lambda g: g.wkt)
output_df = pd.DataFrame(hexgrid)

# === 9. Write to DSS output dataset ===
# Dataset moz_totalrep renamed to flo_totalrep by admin on 2025-07-21 17:35:55
output = dataiku.Dataset("flo_totalrep")  # <-- Replace with your output dataset name
output.write_with_schema(output_df)
