# -*- coding: utf-8 -*-
import dataiku
import geopandas as gpd
import h3
import pandas as pd
from pathlib import Path

# ---- Path to boundary GeoJSON exported from GEE ----
boundary_path = Path("/home/hid24/dss_data/managed_folders/DISSERTATION/1jRHdqAb/philippines_lsib_2017.geojson")

# ---- Read boundary and ensure WGS84 ----
gdf = gpd.read_file(boundary_path).to_crs("EPSG:4326")

# ---- Merge to a single (Multi)Polygon ----
geom = gdf.unary_union
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
        cells = h3.geo_to_cells(simple_poly, res=resolution)  # uses your existing API
        print(f"  Generated {len(cells)} hexes in part {i+1}")
        all_cells.update(cells)
    except Exception as e:
        print(f"  Failed part {i+1}: {e}")

if not all_cells:
    raise RuntimeError("No hexes generated. Try reducing resolution or adjusting geometry.")

# ---- Convert H3 indexes to polygon shapes ----
hex_shapes = [h3.cells_to_h3shape([h]) for h in all_cells]

# ---- Build output GeoDataFrame ----
df_output = gpd.GeoDataFrame(
    {"cell_id": list(all_cells), "geometry": hex_shapes},
    crs="EPSG:4326"
)

# ---- Write to DSS output dataset ----
out_df = pd.DataFrame(df_output)  # DSS dataset expects a pandas DF
out_ds = dataiku.Dataset("philip_7")
out_ds.write_with_schema(out_df)
