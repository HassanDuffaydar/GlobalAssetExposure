# -*- coding: utf-8 -*-
import dataiku
import pandas as pd
import json

# Read recipe inputs
florida_bld = dataiku.Folder("ssDEGfwO")

# Find a .geojson file in the folder (use the first one found)
all_paths = florida_bld.list_paths_in_partition()
geojson_paths = [p for p in all_paths if p.lower().endswith(".geojson")]
if not geojson_paths:
    raise RuntimeError("No .geojson file found in the managed folder.")

geojson_path = geojson_paths[0]

# Load the GeoJSON and build rows, skipping problematic features
rows = []
with florida_bld.get_download_stream(geojson_path) as stream:
    data = json.load(stream)

features = data.get("features", [])
for i, feat in enumerate(features):
    try:
        props = feat.get("properties", {})
        geom = feat.get("geometry", None)

        # Basic validation; raise to skip this feature if malformed
        if not isinstance(props, dict) or geom is None:
            raise ValueError("Missing properties or geometry")

        row = dict(props)  # flatten properties
        # Store geometry as GeoJSON string (keeps it portable; avoids extra deps)
        row["_geometry_geojson"] = json.dumps(geom)
        row["_feature_index"] = i
        row["_source_path"] = geojson_path
        rows.append(row)

    except Exception:
        # Skip any row that causes issues
        continue

# Create the dataframe (empty if all features failed validation)
florida_raw_bld_df = pd.DataFrame(rows)

# Write recipe outputs
florida_raw_bld = dataiku.Dataset("florida_raw_bld")
florida_raw_bld.write_with_schema(florida_raw_bld_df)
