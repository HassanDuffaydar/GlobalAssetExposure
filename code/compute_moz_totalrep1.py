# -*- coding: utf-8 -*-
import dataiku
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
from shapely import wkt

# === 1. Load exposure dataset ===
exposure_ds = dataiku.Dataset("Exposure_res_moz")  # <-- Replace with your dataset name
exposure_df = exposure_ds.get_dataframe()

# === 2. Convert lat/lon to GeoDataFrame ===
geometry = [Point(xy) for xy in zip(exposure_df["LONGITUDE"], exposure_df["LATITUDE"])]
gdf_clipped = gpd.GeoDataFrame(exposure_df, geometry=geometry, crs="EPSG:4326")

# === 3. Load H3 hex grid ===
# Dataset moz_h3_3 renamed to moz_h3_4 by admin on 2025-07-24 20:45:05
# Dataset moz_h3_4 renamed to res7 by admin on 2025-08-10 11:48:00
hex_ds = dataiku.Dataset("res7")
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
# Dataset moz_totalrep renamed to moz_totalrep1 by admin on 2025-07-24 20:45:05
output = dataiku.Dataset("moz_totalrep1")  # <-- Replace with your output dataset name
output.write_with_schema(output_df)
