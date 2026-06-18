import pandas as pd
import numpy as np

def detect_anomalies(df, columns, lang='en'):
    """
    Detect statistical anomalies in the primary numeric column.
    Uses Z-score to find extreme highs and lows.
    Returns a list of string warnings.
    """
    anomalies = []
    is_ar = lang == 'ar'
    
    date_col = columns.get("primary_date")
    num_col = columns.get("primary_numeric")
    
    if not num_col or num_col not in df.columns:
        return anomalies
        
    num_data = pd.to_numeric(df[num_col], errors='coerce').dropna()
    
    if len(num_data) < 10:
        return anomalies # Need enough data points for statistics
        
    mean = num_data.mean()
    std = num_data.std()
    
    if std == 0:
        return anomalies
        
    # Find rows where Z-score > 2.5 (significant anomaly)
    z_scores = (num_data - mean) / std
    outliers_high = df.loc[num_data[z_scores > 2.5].index]
    outliers_low = df.loc[num_data[z_scores < -2.5].index]
    
    # We only report up to 3 anomalies to avoid spamming the UI
    count = 0
    
    # High anomalies
    for idx, row in outliers_high.head(2).iterrows():
        val = row[num_col]
        date_str = str(row[date_col])[:10] if date_col and date_col in row else f"Row {idx}"
        
        if is_ar:
            anomalies.append(f"ارتفاع غير طبيعي: قيمة {num_col} بلغت {val:,.2f} في {date_str}، وهو أعلى بكثير من المتوسط ({mean:,.2f}).")
        else:
            anomalies.append(f"Unusual Spike: {num_col} reached {val:,.2f} on {date_str}, which is significantly higher than the average ({mean:,.2f}).")
        count += 1
        
    # Low anomalies
    for idx, row in outliers_low.head(2).iterrows():
        val = row[num_col]
        date_str = str(row[date_col])[:10] if date_col and date_col in row else f"Row {idx}"
        
        if is_ar:
            anomalies.append(f"انخفاض غير طبيعي: قيمة {num_col} هبطت إلى {val:,.2f} في {date_str}، وهو أقل بكثير من المتوسط ({mean:,.2f}).")
        else:
            anomalies.append(f"Unusual Drop: {num_col} dropped to {val:,.2f} on {date_str}, which is significantly lower than the average ({mean:,.2f}).")
        count += 1
        
    return anomalies
