#pip install libpysal


# -*- coding: utf-8 -*-
import dataiku
import pandas as pd, numpy as np
from dataiku import pandasutils as pdu
# Geo + spatial libs
import geopandas as gpd
from shapely import wkt
from libpysal.weights import Queen
from esda.moran import Moran_Local

# -------------------------------------------------------------------
# 1. Read recipe inputs
# -------------------------------------------------------------------
input_dataset = dataiku.Dataset("features_joined_1_prepared_scored_prepared")
df = input_dataset.get_dataframe()

# -------------------------------------------------------------------
# 2. Convert to GeoDataFrame
#    (assuming 'geometry' column in WKT format, adjust if GeoJSON)
# -------------------------------------------------------------------
if "geometry" in df.columns:
    df["geometry"] = df["geometry"].apply(wkt.loads)
    gdf = gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4326")
else:
    raise ValueError("No geometry column found in dataset")

# -------------------------------------------------------------------
# 3. Build spatial weights (Queen contiguity: touching hexagons)
# -------------------------------------------------------------------
w = Queen.from_dataframe(gdf)
w.transform = "r"

# -------------------------------------------------------------------
# 4. Run Local Moran’s I on uncertainty column
# -------------------------------------------------------------------


y = gdf["litpop_dff2"].values
lisa = Moran_Local(y, w)

# -------------------------------------------------------------------
# 5. Add LISA results to dataframe
# -------------------------------------------------------------------
gdf["lisa_I"] = lisa.Is                   # Local Moran's I values
gdf["lisa_p"] = lisa.p_sim                # p-values
gdf["lisa_cluster"] = lisa.q              # quadrant type (1=HH, 2=LH, 3=LL, 4=HL)
gdf["lisa_significant"] = lisa.p_sim < 0.05  # significance flag

# -------------------------------------------------------------------
# 6. Convert back to Pandas (drop geometry if schema doesn't support it)
# -------------------------------------------------------------------
# If Dataiku dataset schema doesn’t support geometry, export as WKT string
gdf["geometry"] = gdf["geometry"].apply(lambda geom: geom.wkt)
lisa_df = pd.DataFrame(gdf)

# -------------------------------------------------------------------
# 7. Write recipe outputs
# -------------------------------------------------------------------
output_dataset = dataiku.Dataset("lisa")
output_dataset.write_with_schema(lisa_df)
