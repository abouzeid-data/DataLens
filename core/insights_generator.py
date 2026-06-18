def generate_insights(kpis):
    """
    Generate dynamic string insights from the generic KPI dictionary.
    """
    insights = []
    
    for key, value in kpis.items():
        if value is not None:
            # Since the data is generic, we just state the fact directly.
            insights.append(f"{key}: {value}")
            
    if not insights:
        insights.append("No specific insights could be generated for this dataset.")
        
    return insights
