from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_LEFT, TA_CENTER
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pathlib import Path
from datetime import datetime
import os
import re

def _app_data_dir():
    root = os.getenv("DATALENS_DATA_DIR")
    if root:
        path = Path(root)
    elif os.name == "nt" and os.getenv("APPDATA"):
        path = Path(os.getenv("APPDATA")) / "DataLens"
    else:
        path = Path.home() / ".datalens"
    path.mkdir(parents=True, exist_ok=True)
    return path

def _register_arabic_font():
    """Register an Arabic-capable font for ReportLab."""
    windows_fonts = Path(os.environ.get('WINDIR', 'C:\\Windows')) / 'Fonts'
    arabic_fonts = [
        ('Tahoma', 'tahoma.ttf', 'tahomabd.ttf'),
        ('Arial', 'arial.ttf', 'arialbd.ttf'),
    ]
    for font_name, regular, bold in arabic_fonts:
        regular_path = windows_fonts / regular
        bold_path = windows_fonts / bold
        if regular_path.exists():
            try:
                ar_regular = f'{font_name}-AR'
                ar_bold = f'{font_name}-AR-Bold'
                pdfmetrics.registerFont(TTFont(ar_regular, str(regular_path)))
                if bold_path.exists():
                    pdfmetrics.registerFont(TTFont(ar_bold, str(bold_path)))
                else:
                    ar_bold = ar_regular
                return ar_regular, ar_bold
            except Exception:
                continue
    return None, None

REPORT_LABELS = {
    'en': {
        'title': 'DataLens - Business Performance Report',
        'generated_at': 'Prepared on',
        'dataset_summary': 'Business Snapshot',
        'num_rows': 'Records Reviewed',
        'num_cols': 'Business Fields Reviewed',
        'kpis': 'Performance Highlights',
        'no_kpis': 'No business metrics were calculated.',
        'insights': 'Business Takeaways',
        'no_insights': 'No business takeaways were generated.',
    },
    'ar': {
        'title': 'DataLens - تقرير تحليل البيانات',
        'generated_at': 'تم الإنشاء في',
        'dataset_summary': 'ملخص البيانات',
        'num_rows': 'عدد الصفوف',
        'num_cols': 'عدد الأعمدة',
        'column_names': 'أسماء الأعمدة',
        'detected_columns': 'الأعمدة المكتشفة',
        'kpis': 'مؤشرات الأداء الرئيسية',
        'no_kpis': 'لم يتم حساب مؤشرات الأداء.',
        'insights': 'رؤى الأعمال',
        'no_insights': 'لم يتم إنشاء رؤى.',
        'charts': 'الرسوم البيانية',
        'charts_note': 'الرسوم البيانية معروضة في تطبيق DataLens.',
        'no_charts': 'لم يتم إنشاء رسوم بيانية.',
    }
}

KPI_LABELS_AR = {
    'Total Revenue': 'إجمالي الإيرادات',
    'Average Sale': 'متوسط البيع',
    'Max Sale': 'أعلى بيع',
    'Min Sale': 'أدنى بيع',
    'Number of Transactions': 'عدد المعاملات',
    'Best-Selling Product': 'المنتج الأكثر مبيعاً',
    'Worst-Selling Product': 'المنتج الأقل مبيعاً',
    'Best Sales Day/Month': 'أفضل يوم/شهر مبيعات',
}

COLUMN_LABELS_AR = {
    'date_column': 'عمود التاريخ',
    'sales_column': 'عمود المبيعات',
    'product_column': 'عمود المنتج',
    'quantity_column': 'عمود الكمية',
    'category_column': 'عمود الفئة',
    'price_column': 'عمود السعر',
}

def _clean_markdown(text):
    if not text:
        return text
    # Remove markdown bold/italics markers
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    return text

def _format_value(value):
    if isinstance(value, float):
        return f"{value:,.2f}"
    return str(value)

def _business_sentence(text):
    text = _clean_markdown(str(text)).strip(" -*")
    if ":" in text:
        label, value = text.split(":", 1)
        label = label.strip()
        value = value.strip()
        if label and value:
            return f"{label} is {value}."
    return text

def generate_report(df, kpis, insights, charts=None, columns=None, gemini_insight=None, lang='en', logo_path=None, brand_color=None):
    is_arabic = lang == 'ar'
    labels = REPORT_LABELS.get(lang, REPORT_LABELS['en'])

    ar_font, ar_font_bold = None, None
    if is_arabic:
        ar_font, ar_font_bold = _register_arabic_font()

    font_regular = ar_font if (is_arabic and ar_font) else 'Helvetica'
    font_bold = ar_font_bold if (is_arabic and ar_font_bold) else 'Helvetica-Bold'
    
    brand_hex = HexColor(brand_color) if brand_color else HexColor("#0ea5e9")

    reports_dir = _app_data_dir() / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = reports_dir / f"report_{timestamp}.pdf"

    doc = SimpleDocTemplate(
        str(report_path),
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    
    align_mode = TA_RIGHT if is_arabic else TA_LEFT

    style_title = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName=font_bold,
        fontSize=22,
        textColor=brand_hex,
        alignment=align_mode,
        spaceAfter=20
    )
    
    style_heading = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontName=font_bold,
        fontSize=16,
        textColor=brand_hex,
        alignment=align_mode,
        spaceAfter=10,
        spaceBefore=20
    )
    
    style_normal = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontName=font_regular,
        fontSize=11,
        leading=16,
        alignment=align_mode,
        spaceAfter=6
    )

    story = []

    def add_text(text, style):
        # Handle multiple lines
        for line in str(text).split('\n'):
            line = line.strip()
            if not line:
                continue
            if is_arabic:
                try:
                    from arabic_reshaper import reshape
                    from bidi.algorithm import get_display
                    line = get_display(reshape(line))
                except ImportError:
                    pass
            story.append(Paragraph(line, style))

    # Add Logo
    if logo_path and os.path.exists(logo_path):
        try:
            # We add it as an Image flowable aligned opposite to the text
            logo = Image(logo_path, width=120, height=60, kind='proportional')
            logo.hAlign = 'LEFT' if is_arabic else 'RIGHT'
            story.append(logo)
            story.append(Spacer(1, 20))
        except Exception:
            pass

    # Title
    add_text(labels['title'], style_title)
    add_text(f"{labels['generated_at']}: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", style_normal)

    # Business Snapshot
    add_text(labels['dataset_summary'], style_heading)
    add_text(f"{labels['num_rows']}: {len(df)}", style_normal)
    add_text(f"{labels['num_cols']}: {len(df.columns)}", style_normal)

    # Performance Highlights
    add_text(labels['kpis'], style_heading)
    if kpis:
        for k, v in kpis.items():
            label = KPI_LABELS_AR.get(k, k) if is_arabic else k
            add_text(f"{label}: {_format_value(v)}", style_normal)
    else:
        add_text(labels['no_kpis'], style_normal)

    # Business Takeaways
    add_text(labels['insights'], style_heading)
    if insights:
        for ins in insights:
            add_text(f"- {_business_sentence(ins)}", style_normal)
    else:
        add_text(labels['no_insights'], style_normal)

    # Build the PDF
    doc.build(story)
    
    return str(report_path)
