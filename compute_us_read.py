# -*- coding: utf-8 -*-
import dataiku
import pandas as pd
import json
import io
from shapely.geometry import shape
from shapely.wkt import dumps as wkt_dumps

# --- Path to your Florida file in the managed folder ---
FL_FILE = "Florida.geojson"

# Read the raw JSON from folder
us = dataiku.Folder("PU90ow7l")
with us.get_download_stream(FL_FILE) as stream:
    text = io.TextIOWrapper(stream, encoding="utf-8", errors="replace").read()
geojson = json.loads(text)

# Normalize into a list of features
if geojson.get("type") == "FeatureCollection":
    features = geojson.get("features", [])
elif geojson.get("type") == "Feature":
    features = [geojson]
else:
    raise ValueError(f"Unexpected GeoJSON type: {geojson.get('type')}")

# Build rows: properties + geometry WKT
rows = []
for feat in features:
    props = (feat.get("properties") or {}).copy()
    geom = feat.get("geometry")
    if geom:
        try:
            props["geometry_wkt"] = wkt_dumps(shape(geom))
        except Exception:
            props["geometry_wkt"] = None
    rows.append(props)

# Make DataFrame
us_read_df = pd.DataFrame(rows)

# --- Write to output dataset ---
us_read = dataiku.Dataset("us_read")
us_read.write_with_schema(us_read_df)
