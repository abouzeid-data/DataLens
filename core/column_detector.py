import pandas as pd
import numpy as np


def detect_columns(df):
    """
    Automatically detect generic column types for analysis.

    Returns:
    {
        "datetime_columns": list of column names,
        "numeric_columns": list of column names,
        "categorical_columns": list of column names,
        "primary_date": str or None,
        "primary_numeric": str or None,
        "primary_category": str or None
    }
    """

    columns = {
        "datetime_columns": [],
        "numeric_columns": [],
        "categorical_columns": [],
        "primary_date": None,
        "primary_numeric": None,
        "primary_category": None
    }

    for col in df.columns:
        # 1. Try to detect Datetime
        is_date = False
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            is_date = True
        elif df[col].dtype == 'object':
            try:
                sample = df[col].dropna().head(20)
                if not sample.empty:
                    converted = pd.to_datetime(sample, errors='coerce')
                    # If most of the sample converts to dates, treat as date
                    if converted.notna().sum() > len(sample) * 0.8:
                        is_date = True
            except Exception:
                pass

        if is_date:
            columns["datetime_columns"].append(col)
            continue

        # 2. Detect Numeric
        if pd.api.types.is_numeric_dtype(df[col]):
            # Sometimes IDs are numeric, we'll sort that out when picking primary
            columns["numeric_columns"].append(col)
            continue

        # 3. Detect Categorical (strings/objects)
        if pd.api.types.is_object_dtype(df[col]) or isinstance(df[col].dtype, pd.CategoricalDtype):
            columns["categorical_columns"].append(col)

    # Pick the "primary" columns for charts and main KPIs

    # Primary Date: usually the first one found
    if columns["datetime_columns"]:
        columns["primary_date"] = columns["datetime_columns"][0]

    # Primary Numeric: pick the one with the highest sum (often the most "important" metric)
    if columns["numeric_columns"]:
        best_col = None
        max_sum = -float('inf')
        for col in columns["numeric_columns"]:
            if 'id' in col.lower() and len(columns["numeric_columns"]) > 1:
                continue
            
            try:
                col_sum = float(df[col].dropna().sum())
                if col_sum > max_sum:
                    max_sum = col_sum
                    best_col = col
            except:
                pass
                
        columns["primary_numeric"] = best_col if best_col else columns["numeric_columns"][0]

    # Primary Category: pick one with reasonable unique values (good for groupings/charts)
    if columns["categorical_columns"]:
        best_cat = None
        min_unique = float('inf')
        for col in columns["categorical_columns"]:
            n_unique = df[col].nunique()
            if 1 < n_unique < min_unique and n_unique <= 100:
                min_unique = n_unique
                best_cat = col
        columns["primary_category"] = best_cat if best_cat else columns["categorical_columns"][0]

    return columns