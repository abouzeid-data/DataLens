import pandas as pd

def load_file(file):
    try:
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.name.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file)
        else:
            raise ValueError("Unsupported file type")
        return df
    except Exception as e:
        raise ValueError(f"Error loading file: {e}")
