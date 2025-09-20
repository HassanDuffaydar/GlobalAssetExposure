# -*- coding: utf-8 -*-
import dataiku
import pandas as pd
from shapely import wkt
from shapely.geometry import shape
import json

# Read recipe inputs
USA_7 = dataiku.Dataset("USA_7")
USA_7_df = USA_7.get_dataframe()

florida_boundary = dataiku.Dataset("florida_boundary")
florida_boundary_df = florida_boundary.get_dataframe()

# --- Parse Florida boundary ---
# Assuming only one feature in florida_boundary
geom_val = florida_boundary_df.iloc[0]["geometry"]

# Try to parse as WKT, otherwise as GeoJSON
try:
    florida_geom = wkt.loads(geom_val)
except Exception:
    florida_geom = shape(json.loads(geom_val))

# --- Parse USA_7 geometries and filter ---
def in_florida(wkt_str):
    try:
        g = wkt.loads(wkt_str)
    except Exception:
        g = shape(json.loads(wkt_str))
    return g.intersects(florida_geom)

mask = USA_7_df["geometry"].apply(in_florida)
florida_7_df = USA_7_df[mask].copy()

# Write recipe outputs
florida_7 = dataiku.Dataset("florida_7")
florida_7.write_with_schema(florida_7_df)
