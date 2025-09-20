# -*- coding: utf-8 -*-
import dataiku
import geopandas as gpd
from shapely import wkt
import h3
import matplotlib.pyplot as plt
import pandas as pd
from shapely.geometry import Polygon

def latlngpoly_to_shapely(latlng_poly):
    """Convert H3 LatLngPoly to shapely Polygon"""
    return Polygon([(lng, lat) for lat, lng in latlng_poly.boundary])
from shapely.geometry import Polygon

def h3_to_shapely(h3_cell):
    """Convert H3 cell to shapely Polygon by reversing (lat, lng) to (lng, lat)"""
    boundary = h3.cell_to_boundary(h3_cell)  # Returns list of (lat, lng)
    return Polygon([(lng, lat) for lat, lng in boundary])


# === Read DSS input dataset ===
moz_boundary = dataiku.Dataset("buzi_boundary")
moz_boundary_df = moz_boundary.get_dataframe()

# === Convert WKT to geometry (if needed) ===
gdf = gpd.GeoDataFrame(moz_boundary_df, geometry=moz_boundary_df["geometry"].apply(wkt.loads), crs="EPSG:4326")

# === Combine all geometries if more than one row ===
geom = gdf.unary_union
geoms = [geom] if geom.geom_type == "Polygon" else list(geom.geoms)

# === Set H3 resolutions ===
res_fine = 7
res_coarse = 3
all_cells_fine = set()

print(f"Processing {len(geoms)} geometry part(s) for H3 resolution {res_fine}...")

for i, poly in enumerate(geoms):
    simple_poly = poly.simplify(tolerance=0.01, preserve_topology=True)

    if simple_poly.is_empty or not simple_poly.is_valid:
        print(f"  Skipping part {i+1}: empty or invalid after simplification.")
        continue

    try:
        cells = h3.geo_to_cells(simple_poly, res=res_fine)
        print(f"  Generated {len(cells)} hexes in part {i+1}")
        all_cells_fine.update(cells)
    except Exception as e:
        print(f"  Failed part {i+1}: {e}")

if not all_cells_fine:
    raise RuntimeError("No hexes generated. Try reducing resolution or adjusting geometry.")

# === Create list of records with res=7 + res=3 + both geometries ===
# === Create list of records with res=7 + res=3 + both geometries ===
records = []
for h7 in all_cells_fine:
    h3_res3 = h3.cell_to_parent(h7, res_coarse)

    geom_res7 = h3_to_shapely(h7)
    geom_res3 = h3_to_shapely(h3_res3)

    records.append({
        "h3_res_7": h7,
        "geometry_res_7": geom_res7,
        "h3_res_3": h3_res3,
        "geometry_res_3": geom_res3
    })




# === Create GeoDataFrame with both geometries ===
# === Create GeoDataFrame with specified geometry column ===
df_output = gpd.GeoDataFrame(records, geometry="geometry_res_7", crs="EPSG:4326")


# === Optional: convert geometries to WKT if outputting to Dataiku DSS table
df_output["geometry_res_7"] = df_output["geometry_res_7"].apply(lambda g: g.wkt)
df_output["geometry_res_3"] = df_output["geometry_res_3"].apply(lambda g: g.wkt)

# === Write to DSS output dataset ===
moz_h3_combined = dataiku.Dataset("moz_superimposed")
moz_h3_combined.write_with_schema(df_output)


