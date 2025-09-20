"buzi_boundary"# -*- coding: utf-8 -*-
import dataiku
import geopandas as gpd
import pandas as pd
import ee
from shapely import wkt

# Authenticate and initialize Earth Engine
ee.Authenticate(auth_mode='notebook')
ee.Initialize(project="diss2-466311")

# === Load individual boundary polygons from DSS ===
boundary_ds = dataiku.Dataset("maravia_boundary")
df = boundary_ds.get_dataframe()
gdf = gpd.GeoDataFrame(df, geometry=df["geometry"].apply(wkt.loads), crs="EPSG:4326")

# === Convert each polygon to Earth Engine Feature ===
def shapely_geom_to_ee_polygon(geom):
    return ee.Geometry.Polygon(list(geom.exterior.coords))

# === Load Microsoft Building Footprints ===
buildings_fc = ee.FeatureCollection('projects/sat-io/open-datasets/MSBuildings/Mozambique')

# === Collect all buildings within any of the polygons ===
all_filtered = []
for geom in gdf.geometry:
    if geom.geom_type == 'Polygon':
        ee_geom = shapely_geom_to_ee_polygon(geom)
        filtered = buildings_fc.filterBounds(ee_geom)
        all_filtered.append(filtered)
    elif geom.geom_type == 'MultiPolygon':
        for poly in geom.geoms:
            ee_geom = shapely_geom_to_ee_polygon(poly)
            filtered = buildings_fc.filterBounds(ee_geom)
            all_filtered.append(filtered)

# === Combine all filtered buildings ===
combined_buildings = ee.FeatureCollection(all_filtered[0])
for fc in all_filtered[1:]:
    combined_buildings = combined_buildings.merge(fc)

# === Bring features back to Python ===
results = combined_buildings.getInfo()
buildings_gdf = gpd.GeoDataFrame.from_features(results['features'], crs="EPSG:4326")

# === Convert geometry to WKT for DSS output ===
buildings_gdf["geometry"] = buildings_gdf["geometry"].apply(lambda g: g.wkt)
buildings_df = pd.DataFrame(buildings_gdf)

# === Write results to DSS ===
# Dataset buzi_globalml_plot renamed to maravia_globalml_plot by admin on 2025-07-27 14:46:37
output_ds = dataiku.Dataset("maravia_globalml_plot")
output_ds.write_with_schema(buildings_df)

