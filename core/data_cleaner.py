import pandas as pd

def clean_data(df):
    df = df.copy()
    cleaning_summary = {}

    # Remove duplicate rows
    original_rows = len(df)
    df.drop_duplicates(inplace=True)
    cleaning_summary["Duplicate Rows Removed"] = original_rows - len(df)

    # Trim spaces from text columns
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].str.strip()
    cleaning_summary["Trimmed Text Spaces"] = True

    # Convert possible numeric columns
    for col in df.columns:
        try:
            pd.to_numeric(df[col], errors='raise')
            df[col] = pd.to_numeric(df[col])
            cleaning_summary[f"Converted to Numeric: {col}"] = True
        except ValueError:
            pass

    # Detect and convert possible date columns
    for col in df.columns:
        if pd.api.types.is_string_dtype(df[col]):
            try:
                converted = pd.to_datetime(df[col], errors='coerce')
                # Only convert if more than 60% of values are valid dates
                if converted.notna().sum() > len(df) * 0.6:
                    df[col] = converted
                    cleaning_summary[f"Converted to Date: {col}"] = True
            except (ValueError, TypeError):
                pass

    return df, cleaning_summary
