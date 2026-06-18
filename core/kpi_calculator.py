import pandas as pd
import numpy as np


def calculate_kpis(df, columns, use_case='General', lang='en'):
    """
    Calculate generic business KPIs safely, tailored by use_case.
    """

    kpis = {}
    is_ar = lang == 'ar'

    primary_numeric = columns.get("primary_numeric")
    primary_category = columns.get("primary_category")

    # Translation prefixes tailored by use_case
    if use_case == 'Finance':
        t_total = "إجمالي القيمة المالية" if is_ar else "Total Value"
        t_avg = "متوسط القيمة" if is_ar else "Average Value"
    elif use_case == 'Healthcare':
        t_total = "إجمالي الحالات" if is_ar else "Total Records/Patients"
        t_avg = "المتوسط" if is_ar else "Average"
    elif use_case == 'E-Commerce':
        t_total = "إجمالي المبيعات" if is_ar else "Total Sales"
        t_avg = "متوسط قيمة الطلب" if is_ar else "Average Order Value"
    else:
        t_total = "إجمالي" if is_ar else "Total"
        t_avg = "متوسط" if is_ar else "Average"

    t_highest = "أعلى" if is_ar else "Highest"
    t_lowest = "أدنى" if is_ar else "Lowest"
    t_most_frequent = "الأكثر تكراراً في" if is_ar else "Most Frequent"
    t_unique = "عدد فريد من" if is_ar else "Unique"

    # Numeric KPIs
    if primary_numeric and primary_numeric in df.columns:
        num_col = pd.to_numeric(df[primary_numeric], errors="coerce").dropna()
        if not num_col.empty:
            kpis[f"{t_total} {primary_numeric}"] = round(float(num_col.sum()), 2)
            kpis[f"{t_avg} {primary_numeric}"] = round(float(num_col.mean()), 2)
            kpis[f"{t_highest} {primary_numeric}"] = round(float(num_col.max()), 2)
            kpis[f"{t_lowest} {primary_numeric}"] = round(float(num_col.min()), 2)

    # Categorical KPIs
    if primary_category and primary_category in df.columns:
        cat_col = df[primary_category].dropna()
        if not cat_col.empty:
            kpis[f"{t_most_frequent} {primary_category}"] = str(cat_col.mode().iloc[0])
            kpis[f"{t_unique} {primary_category}"] = int(cat_col.nunique())

    return kpis
