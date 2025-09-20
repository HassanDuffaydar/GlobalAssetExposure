# -*- coding: utf-8 -*-
import dataiku
import pandas as pd
import numpy as np

# Read recipe inputs
Florida_hex_population_GPWv411_first = dataiku.Dataset("Florida_hex_population_GPWv411_first")
Florida_hex_population_GPWv411_first_df = Florida_hex_population_GPWv411_first.get_dataframe()

flo_7 = dataiku.Dataset("flo_7")
flo_7_df = flo_7.get_dataframe()

# --- Add sequential index to both ---
Florida_hex_population_GPWv411_first_df = Florida_hex_population_GPWv411_first_df.reset_index(drop=True)
Florida_hex_population_GPWv411_first_df["join_idx"] = Florida_hex_population_GPWv411_first_df.index

flo_7_df = flo_7_df.reset_index(drop=True)
flo_7_df["join_idx"] = flo_7_df.index

# --- Left join flo_7 with population data ---
merged = flo_7_df.merge(
    Florida_hex_population_GPWv411_first_df[["join_idx", "pop_sum"]],  # adjust column name if different
    on="join_idx",
    how="left"
)

# --- Add log(pop_sum+1) ---
merged["log_pop_sum"] = np.log1p(merged["pop_sum"])  # log(pop+1)

# Compute recipe outputs
florida_plot_df = merged

# Write recipe outputs
florida_plot = dataiku.Dataset("florida_plot")
florida_plot.write_with_schema(florida_plot_df)
