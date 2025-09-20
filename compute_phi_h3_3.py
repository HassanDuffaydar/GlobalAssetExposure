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
phi_boundary = dataiku.Dataset("philippines_boundary")
phi_boundary_df = phi_boundary.get_dataframe()

# === Convert WKT to geometry (if needed) ===
# DSS datasets store geometries as WKT strings, so we convert to shapely objects
gdf = gpd.GeoDataFrame(phi_boundary_df, geometry=phi_boundary_df["geometry"].apply(wkt.loads), crs="EPSG:4326")

# === Combine all geometries if more than one row ===
geom = gdf.unary_union  # single (Multi)Polygon

# === Decompose MultiPolygon or use Polygon directly ===
geoms = [geom] if geom.geom_type == "Polygon" else list(geom.geoms)

resolution = 3
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
phi_h3_3_df = pd.DataFrame(df_output)

# === Write to DSS output dataset ===
phi_h3_3 = dataiku.Dataset("phi_h3_3")
phi_h3_3.write_with_schema(phi_h3_3_df)