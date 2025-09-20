# -*- coding: utf-8 -*-
import dataiku
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from dataiku import pandasutils as pdu

# Read recipe inputs
moz_features_1 = dataiku.Dataset("moz_features_1")
moz_features_1_df = moz_features_1.get_dataframe()

# Keep only numeric columns
numeric_df = moz_features_1_df.select_dtypes(include=[np.number])

# Remove specific unwanted columns
columns_to_remove = ["gdp_density"]  # <<< REPLACE with your actual column names
numeric_df = numeric_df.drop(columns=columns_to_remove, errors="ignore")

# Compute correlation matrix
corr_matrix = numeric_df.corr()

# Plot correlation matrix without annotations
plt.figure(figsize=(12, 8))
sns.heatmap(corr_matrix, annot=True, cmap='coolwarm')
plt.title("Correlation Matrix (Filtered Numeric Columns)")
plt.show()

# Convert correlation matrix to DataFrame for output
moz_corr_df = corr_matrix.reset_index()

# Write recipe outputs
moz_corr = dataiku.Dataset("moz_corr")
moz_corr.write_with_schema(moz_corr_df)
