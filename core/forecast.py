import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np


def forecast_primary_metric(df, columns):
    """
    Perform a simple linear regression forecast on the primary numeric column over time.
    Returns:
        tuple (future_months_list, forecasted_values_list) or None if forecasting is not possible.
    """

    date_col = columns.get("primary_date")
    num_col = columns.get("primary_numeric")

    # We need both a date and a numeric column to forecast
    if not date_col or not num_col or date_col not in df.columns or num_col not in df.columns:
        return None

    # Work on a copy
    forecast_df = df.copy()

    # Convert safely
    forecast_df[date_col] = pd.to_datetime(forecast_df[date_col], errors="coerce")
    forecast_df[num_col] = pd.to_numeric(forecast_df[num_col], errors="coerce")

    # Drop missing
    forecast_df = forecast_df.dropna(subset=[date_col, num_col])

    if forecast_df.empty:
        return None

    # Group by month
    monthly_data = (
        forecast_df.groupby(forecast_df[date_col].dt.to_period("M"))[num_col]
        .sum()
        .reset_index()
    )

    # Need at least 2 data points (months) to draw a trend line
    if len(monthly_data) < 2:
        return None

    # Prepare data for regression
    # Convert Period to a numeric value (months since epoch) for linear regression
    monthly_data["month_num"] = monthly_data[date_col].apply(lambda x: x.year * 12 + x.month)
    monthly_data = monthly_data.sort_values("month_num")

    X = monthly_data[["month_num"]]
    y = monthly_data[num_col]

    model = LinearRegression()
    model.fit(X, y)

    # Generate next 6 months
    last_month_num = monthly_data["month_num"].max()
    future_month_nums = [last_month_num + i for i in range(1, 7)]

    # We also need formatted date strings for the chart
    last_period = monthly_data[date_col].max()
    future_months = []
    for i in range(1, 7):
        next_period = last_period + i
        future_months.append(str(next_period))

    # Predict
    X_future = pd.DataFrame({"month_num": future_month_nums})
    predictions = model.predict(X_future)

    # Prevent negative predictions if it doesn't make business sense (for general numbers it might, but usually we cap at 0)
    # If the original data had no negatives, we cap at 0.
    if y.min() >= 0:
        predictions = np.maximum(predictions, 0)

    # Convert to standard Python float for JSON serialization
    forecasted_values = [round(float(val), 2) for val in predictions]

    return future_months, forecasted_values
