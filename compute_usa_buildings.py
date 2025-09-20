# -*- coding: utf-8 -*-
import dataiku
import geopandas as gpd
import numpy as np
import pandas as pd
import ee
from shapely import wkt

# === Initialize Earth Engine ===
ee.Initialize(project="diss-463806")

# === List of all 51 U.S. states and DC (matching EE asset folder names) ===
states = [
    "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado",
    "Connecticut", "Delaware", "District_of_Columbia", "Florida", "Georgia",
    "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky",
    "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota",
    "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada", "New_Hampshire",
    "New_Jersey", "New_Mexico", "New_York", "North_Carolina", "North_Dakota",
    "Ohio", "Oklahoma", "Oregon", "Pennsylvania", "Rhode_Island", "South_Carolina",
    "South_Dakota", "Tennessee", "Texas", "Utah", "Vermont", "Virginia",
    "Washington", "West_Virginia", "Wisconsin", "Wyoming"
]

# === Load DSS input: USA hexes ===
usa_h3_3 = dataiku.Dataset("USA_h3_3")
df = usa_h3_3.get_dataframe()

# Convert WKT strings to shapely geometries
gdf = gpd.GeoDataFrame(df, geometry=df["geometry"].apply(wkt.loads), crs="EPSG:4326")

# Convert GeoDataFrame to Earth Engine FeatureCollection
def get_ee_feature(row):
    x, y = row.geometry.exterior.coords.xy
    coords = np.dstack((x, y)).tolist()
    geom = ee.Geometry.Polygon(coords)
    return ee.Feature(geom, {"cell_id": row.cell_id})

features = [get_ee_feature(row) for _, row in gdf.iterrows()]
hex_fc = ee.FeatureCollection(features)

# === Collect results from all states ===
all_results = []

for state in states:
    try:
        print(f"Processing {state}...")

        # Load building footprints for the current state
        buildings_fc = ee.FeatureCollection(f'projects/sat-io/open-datasets/MSBuildings/US/{state}')

        # Define reducer function for this state
        def count_buildings_in_hex(hex_feature):
            hex_geom = hex_feature.geometry()
            buildings_in_hex = buildings_fc.filterBounds(hex_geom)
            building_count = buildings_in_hex.size()
            return hex_feature.set({'building_count': building_count, 'state': state})

        # Apply the function to each hex
        state_results_fc = hex_fc.map(count_buildings_in_hex)

        # Get results from Earth Engine
        state_results = state_results_fc.getInfo()
        state_gdf = gpd.GeoDataFrame.from_features(state_results['features'], crs="EPSG:4326")
        all_results.append(state_gdf)

    except Exception as e:
        print(f"Error processing {state}: {e}")

# === Combine all state results ===
if all_results:
    final_gdf = pd.concat(all_results, ignore_index=True)
    final_gdf["geometry"] = final_gdf["geometry"].apply(lambda g: g.wkt)
else:
    final_gdf = pd.DataFrame(columns=["cell_id", "building_count", "state", "geometry"])

# === Write to DSS dataset ===
usa_buildings = dataiku.Dataset("usa_buildings")
usa_buildings.write_with_schema(final_gdf)

