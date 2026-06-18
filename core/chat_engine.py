from groq import Groq


def _safe_dataset_summary(df):
    row_count = len(df)
    column_count = len(df.columns)
    columns = []

    for column in df.columns[:30]:
        series = df[column]
        item = {
            "name": str(column),
            "dtype": str(series.dtype),
            "missing": int(series.isna().sum()),
        }

        if hasattr(series, "nunique"):
            item["unique"] = int(series.nunique(dropna=True))

        if series.dtype.kind in "biufc":
            item["min"] = float(series.min()) if series.notna().any() else None
            item["max"] = float(series.max()) if series.notna().any() else None
            item["mean"] = float(series.mean()) if series.notna().any() else None
            item["sum"] = float(series.sum()) if series.notna().any() else None
        else:
            top_values = series.dropna().astype(str).value_counts().head(5)
            item["top_values"] = top_values.to_dict()

        columns.append(item)

    sample = df.head(5).astype(str).to_dict(orient="records")
    return {
        "rows": row_count,
        "columns": column_count,
        "column_summary": columns,
        "sample_rows": sample,
    }


def ask_data_question(df, query, api_key, lang='en'):
    if not api_key:
        return "Please set your Groq API Key in Settings first." if lang == 'en' else "الرجاء تعيين مفتاح Groq API في الإعدادات أولا."

    try:
        client = Groq(api_key=api_key)
        summary = _safe_dataset_summary(df)

        if lang == 'ar':
            system_prompt = """أنت مساعد تحليل بيانات. أجب باللغة العربية فقط.
استخدم ملخص البيانات المقدم فقط. إذا كان السؤال يحتاج حسابا غير موجود في الملخص، قل إن الإجابة تحتاج تحليلا أعمق داخل التطبيق.
لا تكتب أو تطلب تنفيذ كود."""
        else:
            system_prompt = """You are a data analysis assistant.
Answer using only the provided dataset summary. If the question needs a calculation that is not present in the summary, say it needs deeper in-app analysis.
Do not write or request code execution."""

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Dataset summary: {summary}\n\nQuestion: {query}"}
            ],
            temperature=0.2,
            max_tokens=350
        )

        return completion.choices[0].message.content.strip()

    except Exception as e:
        return f"Error: {str(e)}"
