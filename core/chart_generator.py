import pandas as pd
import plotly.express as px


def generate_charts(df, columns, use_case='General'):
    """
    Generate Plotly charts dynamically based on the available data types.
    """

    charts = {}

    # Work on a copy so we do not accidentally modify the original dataframe
    chart_df = df.copy()

    date_col = columns.get("primary_date")
    num_col = columns.get("primary_numeric")
    cat_col = columns.get("primary_category")

    # 1. Trend Over Time (Line Chart)
    if date_col and num_col and date_col in chart_df.columns and num_col in chart_df.columns:
        chart_df[date_col] = pd.to_datetime(chart_df[date_col], errors='coerce')
        chart_df[num_col] = pd.to_numeric(chart_df[num_col], errors='coerce')
        temp_df = chart_df.dropna(subset=[date_col, num_col])
        
        if not temp_df.empty:
            # Group by Month/Day for better visualization
            trend = temp_df.groupby(temp_df[date_col].dt.to_period("M").astype(str), as_index=False)[num_col].sum()
            if len(trend) < 3: # if fewer than 3 months, group by day
                trend = temp_df.groupby(temp_df[date_col].dt.date.astype(str), as_index=False)[num_col].sum()

            title_prefix = "Financial Trend" if use_case == "Finance" else "Sales Trend" if use_case == "E-Commerce" else "Patient Trend" if use_case == "Healthcare" else f"{num_col} Trend"

            fig = px.line(
                trend,
                x=date_col,
                y=num_col,
                title=f"{title_prefix} Over Time",
                markers=True
            )
            charts[f"{num_col} Trend"] = fig

    # 2. Distribution (Bar Chart & Pie Chart)
    if cat_col and num_col and cat_col in chart_df.columns and num_col in chart_df.columns:
        chart_df[num_col] = pd.to_numeric(chart_df[num_col], errors='coerce')
        temp_df = chart_df.dropna(subset=[cat_col, num_col])
        
        if not temp_df.empty:
            dist = temp_df.groupby(cat_col, as_index=False)[num_col].sum().sort_values(num_col, ascending=False).head(10)
            
            bar_title = f"Top {cat_col} (Financial)" if use_case == "Finance" else f"Top Selling {cat_col}" if use_case == "E-Commerce" else f"Top {cat_col} by {num_col}"

            fig_bar = px.bar(
                dist,
                x=cat_col,
                y=num_col,
                title=bar_title
            )
            charts[f"Top {cat_col}"] = fig_bar
            
            # Only do pie if we have a reasonable number of slices
            if len(dist) > 1:
                fig_pie = px.pie(
                    dist,
                    names=cat_col,
                    values=num_col,
                    title=f"{num_col} Distribution by {cat_col}"
                )
                charts[f"{cat_col} Distribution"] = fig_pie

    # 3. Histogram as fallback if we only have a numeric column
    if not charts and num_col and num_col in chart_df.columns:
        chart_df[num_col] = pd.to_numeric(chart_df[num_col], errors='coerce')
        temp_df = chart_df.dropna(subset=[num_col])
        
        if not temp_df.empty:
            fig = px.histogram(
                temp_df,
                x=num_col,
                title=f"{num_col} Distribution"
            )
            charts[f"{num_col} Histogram"] = fig

    return charts