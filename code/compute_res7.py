# -*- coding: utf-8 -*-
import dataiku
import pandas as pd, numpy as np
from dataiku import pandasutils as pdu

# Read recipe inputs
moz_h3_4 = dataiku.Dataset("moz_h3_4")
moz_h3_4_df = moz_h3_4.get_dataframe()
moz_h3_7 = dataiku.Dataset("moz_h3_7")
moz_h3_7_df = moz_h3_7.get_dataframe()

# Compute recipe outputs from inputs
# TODO: Replace this part by your actual code that computes the output, as a Pandas dataframe
# NB: DSS also supports other kinds of APIs for reading and writing data. Please see doc.

res7_df = moz_h3_7_df # For this sample code, simply copy input to output


# Write recipe outputs
res7 = dataiku.Dataset("res7")
res7.write_with_schema(res7_df)
