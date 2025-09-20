# -------------------------------------------------------------------------------- NOTEBOOK-CELL: CODE
import geopandas as gpd
from io import StringIO
import ee
import pandas as pd
import dataiku
ee.Authenticate()

# -------------------------------------------------------------------------------- NOTEBOOK-CELL: CODE
# -*- coding: utf-8 -*-
import dataiku
import geopandas as gpd
import numpy as np
import pandas as pd
import ee
from shapely import wkt

# === Initialize Earth Engine ===
ee.Initialize(project="diss-463806")

# === Load DSS input: hexes ===
# Dataset phi_h3_3 renamed to moz_h3_3 by admin on 2025-07-18 10:57:18
# Dataset moz_h3_3 renamed to mau_h3_3 by admin on 2025-07-20 20:13:02
moz_h3_3 = dataiku.Dataset("mau_h3_3")
df = moz_h3_3.get_dataframe()

# === Convert WKT strings to shapely geometries ===
gdf = gpd.GeoDataFrame(df, geometry=df["geometry"].apply(wkt.loads), crs="EPSG:4326")

# === Convert GeoDataFrame to Earth Engine FeatureCollection ===
def get_ee_feature(row):
    x, y = row.geometry.exterior.coords.xy
    coords = np.dstack((x, y)).tolist()
    geom = ee.Geometry.Polygon(coords)
    return ee.Feature(geom, {"cell_id": row.cell_id})

features = [get_ee_feature(row) for _, row in gdf.iterrows()]
hex_fc = ee.FeatureCollection(features)

# === Load WorldPop 2020 population count image ===
# Dataset phi_pop renamed to moz_pop by admin on 2025-07-18 10:57:18
# Dataset moz_pop renamed to mau_pop by admin on 2025-07-20 20:13:02
pop_img = ee.ImageCollection("CIESIN/GPWv411/GPW_Population_Count") \
    .filterDate("2020-01-01", "2020-12-31") \
    .mean()

# === Reduce to total population per hex ===
zone_stats = pop_img.reduceRegions(
    collection=hex_fc,
    reducer=ee.Reducer.sum(),
    scale=1000,       # WorldPop resolution ~1km
    tileScale=1
).getInfo()

# === Convert results to GeoDataFrame ===
zone_stats_gdf = gpd.GeoDataFrame.from_features(zone_stats["features"], crs="EPSG:4326")
zone_stats_gdf = zone_stats_gdf.rename(columns={"sum": "total_population"})

# === Convert geometry back to WKT for DSS output ===
zone_stats_gdf["geometry"] = zone_stats_gdf["geometry"].apply(lambda g: g.wkt)
moz_pop_df = pd.DataFrame(zone_stats_gdf)

# === Write result to DSS dataset ===
moz_pop = dataiku.Dataset("mau_pop")
moz_pop.write_with_schema(moz_pop_df)