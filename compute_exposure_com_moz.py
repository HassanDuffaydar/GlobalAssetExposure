# -*- coding: utf-8 -*-
import dataiku
import pandas as pd, numpy as np
from dataiku import pandasutils as pdu

# Read recipe inputs
# Dataset Exposure_Res_Mozambique renamed to Exposure_Com_Mozambique by admin on 2025-07-18 14:17:57
Exposure_Res_Mozambique = dataiku.Dataset("Exposure_Com_Mozambique")
Exposure_Res_Mozambique_df = Exposure_Res_Mozambique.get_dataframe()


# Compute recipe outputs from inputs
# TODO: Replace this part by your actual code that computes the output, as a Pandas dataframe
# NB: DSS also supports other kinds of APIs for reading and writing data. Please see doc.

Exposure_res_moz_df = Exposure_Res_Mozambique_df # For this sample code, simply copy input to output


# Write recipe outputs
# Dataset Exposure_res_moz renamed to exposure_com_moz by admin on 2025-07-18 14:17:57
Exposure_res_moz = dataiku.Dataset("exposure_com_moz")
Exposure_res_moz.write_with_schema(Exposure_res_moz_df)
