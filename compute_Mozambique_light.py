# -*- coding: utf-8 -*-
import dataiku
import pandas as pd, numpy as np
from dataiku import pandasutils as pdu

# Read recipe inputs
Mozambique_gdp = dataiku.Dataset("Mozambique_gdp")
Mozambique_gdp_df = Mozambique_gdp.get_dataframe()


# Compute recipe outputs from inputs
# TODO: Replace this part by your actual code that computes the output, as a Pandas dataframe
# NB: DSS also supports other kinds of APIs for reading and writing data. Please see doc.

Mozambique_light_df = Mozambique_gdp_df # For this sample code, simply copy input to output


# Write recipe outputs
Mozambique_light = dataiku.Dataset("Mozambique_light")
Mozambique_light.write_with_schema(Mozambique_light_df)
