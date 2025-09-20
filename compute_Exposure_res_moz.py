# -*- coding: utf-8 -*-
import dataiku
import pandas as pd, numpy as np
from dataiku import pandasutils as pdu

# Read recipe inputs
Exposure_Res_Mozambique = dataiku.Dataset("Exposure_Res_Mozambique")
Exposure_Res_Mozambique_df = Exposure_Res_Mozambique.get_dataframe()


# Compute recipe outputs from inputs
# TODO: Replace this part by your actual code that computes the output, as a Pandas dataframe
# NB: DSS also supports other kinds of APIs for reading and writing data. Please see doc.

Exposure_res_moz_df = Exposure_Res_Mozambique_df # For this sample code, simply copy input to output


# Write recipe outputs
Exposure_res_moz = dataiku.Dataset("Exposure_res_moz")
Exposure_res_moz.write_with_schema(Exposure_res_moz_df)
