"""
02_clean_energy_data.py
-----------------------
Cleans and processes the EirGrid quarterly hourly system data,
extracting renewable energy generation figures.

Input:
  raw/System-Data-Qtr-Hourly-2026-V4.xlsx

Output:
  output/eirgrid_renewable_2026.csv
  - One row per 15-minute interval
  - Columns: datetime, wind_mw, solar_mw, total_demand_mw,
             wind_penetration, solar_penetration, renewable_score

The renewable_score is a value between 0 and 1 representing the
share of electricity generated from wind and solar at that moment.
It is used downstream as a proxy for grid greenness.

Usage:
  python 02_clean_energy_data.py
"""

import pandas as pd
import os

os.makedirs("output", exist_ok=True)

# 1. Load the Excel file
# EirGrid publishes this as a single-sheet Excel file.
# The sheet is named 'System Data'.
print("Loading EirGrid data...")
filepath = "raw/System-Data-Qtr-Hourly-2026-V4.xlsx"

df = pd.read_excel(filepath, sheet_name="System Data")
print(f"Raw shape: {df.shape}")
print(f"Columns: {list(df.columns)}")

# 2. Keep only the rows where DateTime is a valid timestamp
# The Excel file contains some header/notes rows mixed in with the data.
# Use pd.to_datetime with errors='coerce' to convert the DateTime column:
#   - valid dates -> proper timestamps
#   - invalid rows (headers, notes) -> NaT (Not a Time)
df["DateTime"] = pd.to_datetime(df["DateTime"], errors="coerce")
# Then drop the NaT rows.
df = df.dropna(subset=["DateTime"])
print(f"Rows after dropping invalid datetime: {len(df)}")

# 3. Select and rename the columns we need
# Only keep the Ireland (IE) figures, not Northern Ireland (NI) or
# All Island (AI), because our project focuses on the Republic of Ireland.
columns_needed = {
    "DateTime":             "datetime",
    "IE Wind Generation":   "wind_mw",
    "IE Solar Generation":  "solar_mw",
    "IE Demand":            "total_demand_mw",
    "IE Wind Penetration":  "wind_penetration",
    "IE Solar Penetration": "solar_penetration",
}

# Check which columns actually exist in the file
# (column names can vary slightly between file versions)
available = {k: v for k, v in columns_needed.items() if k in df.columns}
missing = [k for k in columns_needed if k not in df.columns]
if missing:
    print(f"Warning: these expected columns were not found: {missing}")

df = df[list(available.keys())].rename(columns=available)
print(f"Columns kept: {list(df.columns)}")

# 4. Convert numeric columns and drop rows with missing values
# Some cells may contain strings or blanks, coerce them to NaN then drop.
numeric_cols = [c for c in df.columns if c != "datetime"]
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

before = len(df)
df = df.dropna()
print(f"Rows after dropping nulls: {len(df)} (dropped {before - len(df)})")

# 5. Calculate renewable_score
# renewable_score = (wind_mw + solar_mw) / total_demand_mw
# This is a value between 0 and 1 (clamped) representing the fraction
# of electricity demand met by renewable sources at each timestamp.
# It will be used as the 'renewable_score' feature in the ML dataset.
df["renewable_score"] = (df["wind_mw"] + df["solar_mw"]) / df["total_demand_mw"]

# Clamp to [0, 1] to handle any edge cases where generation > demand
df["renewable_score"] = df["renewable_score"].clip(0, 1)

# Round to 4 decimal places for cleanliness
df["renewable_score"] = df["renewable_score"].round(4)

# 6. Sort by datetime and reset index
df = df.sort_values("datetime").reset_index(drop=True)

# 7. Summary statistics
print()
print("=== Summary ===")
print(f"Date range: {df['datetime'].min()} to {df['datetime'].max()}")
print(f"Total rows: {len(df)}")
print(f"Renewable score — mean: {df['renewable_score'].mean():.3f}, "
      f"min: {df['renewable_score'].min():.3f}, "
      f"max: {df['renewable_score'].max():.3f}")
print()
print("Sample rows:")
print(df.head(5).to_string(index=False))

# 8. Export to CSV
output_path = "output/eirgrid_renewable_2026.csv"
df.to_csv(output_path, index=False)
print()
print(f"Saved: {output_path}")
print(f"Final record count: {len(df)}")
print("Next step: run 03_clean_traffic_data.py (coming in Phase 3)")