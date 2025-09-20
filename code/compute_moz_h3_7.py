# -------------------------------------------------------------------------------- NOTEBOOK-CELL: CODE
#!pip install h3

# -------------------------------------------------------------------------------- NOTEBOOK-CELL: CODE
# -*- coding: utf-8 -*-
import dataiku
import geopandas as gpd
from shapely import wkt
import h3
import matplotlib.pyplot as plt
import pandas as pd

# === Read DSS input dataset ===
moz_boundary = dataiku.Dataset("buzi_boundary")
moz_boundary_df = moz_boundary.get_dataframe()

# === Convert WKT to geometry (if needed) ===
# DSS datasets store geometries as WKT strings, so we convert to shapely objects
gdf = gpd.GeoDataFrame(moz_boundary_df, geometry=moz_boundary_df["geometry"].apply(wkt.loads), crs="EPSG:4326")

# === Combine all geometries if more than one row ===
geom = gdf.unary_union  # single (Multi)Polygon

# === Decompose MultiPolygon or use Polygon directly ===
geoms = [geom] if geom.geom_type == "Polygon" else list(geom.geoms)

resolution = 7
all_cells = set()

print(f"Processing {len(geoms)} geometry part(s) for H3 resolution {resolution}...")

for i, poly in enumerate(geoms):
    simple_poly = poly.simplify(tolerance=0.01, preserve_topology=True)

    if simple_poly.is_empty or not simple_poly.is_valid:
        print(f"  Skipping part {i+1}: empty or invalid after simplification.")
        continue

    try:
        cells = h3.geo_to_cells(simple_poly, res=resolution)
        print(f"  Generated {len(cells)} hexes in part {i+1}")
        all_cells.update(cells)
    except Exception as e:
        print(f"  Failed part {i+1}: {e}")

if not all_cells:
    raise RuntimeError("No hexes generated. Try reducing resolution or adjusting geometry.")

# === Convert H3 cells to geometries ===
hex_shapes = [h3.cells_to_h3shape([h]) for h in all_cells]

# === Create output GeoDataFrame ===
df_output = gpd.GeoDataFrame({
    "cell_id": list(all_cells),
    "geometry": hex_shapes
}, crs="EPSG:4326")

# === Convert to Pandas DataFrame for DSS output ===
# DSS datasets don't support geometry, so convert to WKT
#df_output["geometry"] = df_output["geometry"].apply(lambda g: g.wkt)
moz_h3_3_df = pd.DataFrame(df_output)

# === Write to DSS output dataset ===
# Dataset moz_h3_3 renamed to moz_h3_4 by admin on 2025-07-23 23:14:09
# Dataset moz_h3_4 renamed to moz_h3_7 by admin on 2025-08-10 11:43:35
moz_h3_3 = dataiku.Dataset("moz_h3_7")
moz_h3_3.write_with_schema(moz_h3_3_df)