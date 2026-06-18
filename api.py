import os
import sys
import json
import base64
import html
import io
import mimetypes
from pathlib import Path
import pandas as pd
import numpy as np
import webview
from dotenv import load_dotenv

from core.file_loader import load_file
from core.data_cleaner import clean_data
from core.column_detector import detect_columns
from core.kpi_calculator import calculate_kpis
from core.chart_generator import generate_charts
from core.insights_generator import generate_insights
from core.gemini_insights import get_gemini_insight
from core.forecast import forecast_primary_metric
from core.report_generator import generate_report
from core.anomaly_detector import detect_anomalies
from core.chat_engine import ask_data_question
from database.db import (
    save_analysis_history, 
    load_analysis_history, 
    register_user, 
    verify_user, 
    get_user_settings, 
    save_user_settings,
    save_dataset,
    get_saved_datasets,
    delete_saved_dataset,
    is_user_admin,
    get_all_users,
    admin_delete_user,
    admin_reset_password,
    create_password_reset_token,
    reset_password_with_token
)

import smtplib
from email.utils import formataddr
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib.parse import quote

PROJECT_ROOT = Path(__file__).resolve().parent

def _runtime_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return PROJECT_ROOT

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

def _load_environment():
    for env_path in (
        PROJECT_ROOT / ".env",
        _runtime_dir() / ".env",
        _app_data_dir() / ".env",
    ):
        if env_path.exists():
            load_dotenv(env_path, override=False)

_load_environment()

def _app_env_path():
    return _app_data_dir() / ".env"

def _env_file_value(value):
    safe_value = str(value or "").replace("\r", "").replace("\n", "").strip()
    if not safe_value:
        return ""
    if any(ch.isspace() for ch in safe_value) or "#" in safe_value:
        safe_value = safe_value.replace('"', '\\"')
        return f'"{safe_value}"'
    return safe_value

def _write_app_env_values(updates):
    env_path = _app_env_path()
    env_path.parent.mkdir(parents=True, exist_ok=True)
    existing_lines = env_path.read_text(encoding="utf-8").splitlines() if env_path.exists() else []
    output_lines = []
    written = set()

    for line in existing_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            output_lines.append(line)
            continue

        key = stripped.split("=", 1)[0].strip()
        if key in updates:
            output_lines.append(f"{key}={_env_file_value(updates[key])}")
            written.add(key)
        else:
            output_lines.append(line)

    for key, value in updates.items():
        if key not in written:
            output_lines.append(f"{key}={_env_file_value(value)}")

    env_path.write_text("\n".join(output_lines).rstrip() + "\n", encoding="utf-8")

def _to_bool(value, default=True):
    if value is None:
        return default
    return str(value).strip().lower() not in ("0", "false", "no", "off")

def _smtp_settings():
    try:
        port = int(os.getenv("SMTP_PORT", "587"))
    except ValueError:
        port = 587

    return {
        "host": (os.getenv("SMTP_HOST") or "").strip(),
        "port": port,
        "user": (os.getenv("SMTP_USER") or "").strip(),
        "password": os.getenv("SMTP_PASS") or "",
        "from_name": (os.getenv("SMTP_FROM_NAME") or "DataLens").strip(),
        "use_tls": _to_bool(os.getenv("SMTP_TLS"), True),
    }

def _smtp_public_status():
    settings = _smtp_settings()
    return {
        "host": settings["host"],
        "port": settings["port"],
        "user": settings["user"],
        "from_name": settings["from_name"],
        "use_tls": settings["use_tls"],
        "password_set": bool(settings["password"]),
        "configured": bool(settings["host"] and settings["user"] and settings["password"]),
        "config_path": str(_app_env_path()),
    }

REPORTS_DIR = _app_data_dir() / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
MAX_UPLOAD_BYTES = 50 * 1024 * 1024
ALLOWED_DATA_EXTENSIONS = {".csv", ".xls", ".xlsx"}
ALLOWED_LOGO_EXTENSIONS = {".png", ".jpg", ".jpeg"}

def _valid_password(password):
    return isinstance(password, str) and len(password) >= 8

def _safe_existing_file(path, allowed_extensions=None, max_bytes=None):
    try:
        target = Path(path).resolve()
        if not target.is_file():
            return False
        if allowed_extensions and target.suffix.lower() not in allowed_extensions:
            return False
        if max_bytes is not None and target.stat().st_size > max_bytes:
            return False
        return True
    except Exception:
        return False

def _send_reset_email(to_email, reset_link):
    settings = _smtp_settings()
    host = settings["host"]
    port = settings["port"]
    user = settings["user"]
    password = settings["password"]
    
    if not host or not user or not password:
        print("Password reset email was not sent because SMTP settings are not configured.")
        return False, "smtp_not_configured"
        
    try:
        msg = MIMEMultipart("alternative")
        msg['From'] = formataddr((settings["from_name"], user))
        msg['To'] = to_email
        msg['Subject'] = 'DataLens Password Reset'
        
        token = reset_link.split('token=')[-1]
        app_url = reset_link
        local_url = f"http://127.0.0.1:5050/reset?token={quote(token)}"
        escaped_token = html.escape(token)
        escaped_app_url = html.escape(app_url, quote=True)
        escaped_local_url = html.escape(local_url, quote=True)
        
        html_body = f"""
        <html>
          <body style="font-family: Arial, sans-serif; padding: 20px; color: #334155;">
            <h2 style="color: #0f172a;">Password Reset Request</h2>
            <p>You requested to reset your password for DataLens.</p>
            <p>Click the button below to open DataLens and choose a new password:</p>
            <p>
              <a href="{escaped_local_url}" style="display: inline-block; padding: 12px 24px; background-color: #0ea5e9; color: white; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 16px 0;">Reset Password</a>
            </p>
            <p style="font-size: 14px;">If the button does not open the app, try this direct app link:</p>
            <p style="font-size: 14px;"><a href="{escaped_app_url}" style="color: #0ea5e9;">Open DataLens reset screen</a></p>
            <p style="font-size: 14px;">Or copy this token into the reset screen:</p>
            <p style="background: #f1f5f9; padding: 10px; border-radius: 6px; font-family: monospace; font-size: 14px;">
              {escaped_token}
            </p>
            <p style="color: #94a3b8; font-size: 12px; margin-top: 40px;">If you didn't request this, you can safely ignore this email.</p>
          </body>
        </html>
        """
        
        text_body = f"""Password Reset Request

You requested to reset your password for DataLens.

Open DataLens reset link:
{local_url}

If that does not work, open:
{app_url}

Reset token:
{token}

If you didn't request this, you can safely ignore this email.
"""

        msg.attach(MIMEText(text_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))
        
        if port == 465:
            server = smtplib.SMTP_SSL(host, port, timeout=20)
        else:
            server = smtplib.SMTP(host, port, timeout=20)
            if settings["use_tls"]:
                server.starttls()
        with server:
            server.login(user, password)
            server.send_message(msg)
        return True, None
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False, str(e)


def _has_groq_key():
    return bool(os.getenv("GROQ_API_KEY"))


def _format_preview_value(value):
    if value is None:
        return "N/A"
    if isinstance(value, float):
        return f"{value:,.2f}"
    return str(value)


def _business_preview_sentence(text):
    text = str(text).replace("**", "").strip(" -*")
    if ":" in text:
        label, value = text.split(":", 1)
        label = label.strip()
        value = value.strip()
        if label and value:
            return f"{label} is {value}."
    return text


def _file_to_data_url(path):
    if not path or not os.path.exists(path):
        return None

    mime_type, _ = mimetypes.guess_type(path)
    if not mime_type or not mime_type.startswith("image/"):
        return None

    try:
        from PIL import Image

        with Image.open(path) as image:
            image.thumbnail((360, 180))
            output = io.BytesIO()
            image_format = "PNG" if image.mode in ("RGBA", "LA") else "JPEG"
            if image_format == "JPEG" and image.mode != "RGB":
                image = image.convert("RGB")
            image.save(output, format=image_format, optimize=True, quality=85)
            encoded = base64.b64encode(output.getvalue()).decode("ascii")
            return f"data:image/{image_format.lower()};base64,{encoded}"
    except Exception:
        with open(path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode("ascii")
        return f"data:{mime_type};base64,{encoded}"


class Api:
    def __init__(self, startup_token=None):
        self._df = None
        self._cleaned_df = None
        self._columns = None
        self._kpis = None
        self._charts = None
        self._insights = None
        self._ai_insight = None
        self._cleaning_summary = None
        self._current_user_id = None
        self._file_name = None
        self._current_file_paths = None
        self._current_use_case = "General"
        self._startup_token = startup_token
        self._lang = "en"
        
        # Load user's default language safely
        try:
            from database.db import get_user_settings
            # We don't have user_id yet, but keep this mechanism for later
        except:
            pass

    def get_startup_token(self):
        """Returns the token if the app was launched from a datalens:// link, then clears it."""
        token = self._startup_token
        self._startup_token = None
        return json.dumps({"token": token} if token else {"token": None})

    def set_startup_token(self, token):
        self._startup_token = token
        return json.dumps({"status": "ok"})

    def check_session(self):
        """Check if user is logged in."""
        logged_in = self._current_user_id is not None
        is_admin = is_user_admin(self._current_user_id) if logged_in else False
        return json.dumps({"logged_in": logged_in, "is_admin": is_admin})

    def login(self, username, password):
        user_id, use_case = verify_user(username, password)
        if user_id:
            self._current_user_id = user_id
            self._current_use_case = use_case or "General"
            return json.dumps({"status": "ok", "use_case": self._current_use_case})
        return json.dumps({"error": "Invalid username or password"})

    def register(self, username, password, first_name='', last_name='', email='', use_case='General'):
        username = (username or '').strip()
        email = (email or '').strip().lower()
        if not username:
            return json.dumps({"error": "Username is required"})
        if not _valid_password(password):
            return json.dumps({"error": "Password must be at least 8 characters"})
        user_id, error = register_user(username, password, first_name, last_name, email, use_case)
        if user_id:
            self._current_user_id = user_id
            self._current_use_case = use_case
            return json.dumps({"status": "ok"})
        return json.dumps({"error": error})

    def request_password_reset(self, email):
        email = (email or '').strip().lower()
        token, error = create_password_reset_token(email)
        if error:
            return json.dumps({"status": "ok"})
            
        # Create a mock internal URL or deep link. We'll use a placeholder format the frontend can parse.
        reset_link = f"datalens://reset-password?token={token}"
        
        success, send_error = _send_reset_email(email, reset_link)
        if success:
            return json.dumps({"status": "ok"})
        if send_error == "smtp_not_configured":
            return json.dumps({
                "error": "Password reset email is not set up yet. Ask the DataLens admin to configure Email Setup.",
                "code": "smtp_not_configured"
            })
        return json.dumps({
            "error": "The reset email could not be sent. Check the Email Setup in the Admin Panel.",
            "code": "smtp_send_failed"
        })

    def reset_password(self, token, new_password):
        if not _valid_password(new_password):
            return json.dumps({"error": "Password must be at least 8 characters"})
        success, error = reset_password_with_token(token, new_password)
        if success:
            return json.dumps({"status": "ok"})
        return json.dumps({"error": error})

    def logout(self):
        self._current_user_id = None
        self._df = None
        self._cleaned_df = None
        self._columns = None
        self._kpis = None
        return json.dumps({"status": "ok"})

    def open_file_dialog(self):
        """Open native file dialog and return selected file path."""
        file_types = ('Data Files (*.csv;*.xlsx;*.xls)', 'All files (*.*)')
        result = webview.windows[0].create_file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=True,
            file_types=file_types
        )
        if result and len(result) > 0:
            return result
        return None

    def open_logo_dialog(self):
        """Open native image picker for report branding logos."""
        file_types = ('Image Files (*.png;*.jpg;*.jpeg)', 'All files (*.*)')
        result = webview.windows[0].create_file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=False,
            file_types=file_types
        )
        if result and len(result) > 0:
            return result[0]
        return None

    def upload_file(self, file_paths):
        """Load file(s), concatenate if multiple, clean data, detect columns, calculate everything. Return JSON."""
        if self._current_user_id is None:
            return json.dumps({"error": "Please log in first."})
        try:
            if isinstance(file_paths, str):
                file_paths = [file_paths]

            self._current_file_paths = file_paths

            # We'll just use the first file's name for history/display purposes, or joined
            if len(file_paths) == 1:
                self._file_name = os.path.basename(file_paths[0])
            else:
                self._file_name = f"{len(file_paths)} merged files"

            dfs = []
            for path in file_paths:
                if not _safe_existing_file(path, ALLOWED_DATA_EXTENSIONS, MAX_UPLOAD_BYTES):
                    return json.dumps({"error": "Invalid or too large data file."})
                suffix = Path(path).suffix.lower()
                if suffix == '.csv':
                    try:
                        df = pd.read_csv(path, engine='c', on_bad_lines='skip', low_memory=False)
                    except Exception:
                        df = pd.read_csv(path, engine='python', on_bad_lines='skip')
                elif suffix in ('.xls', '.xlsx'):
                    df = pd.read_excel(path)
                else:
                    return json.dumps({"error": f"Unsupported file type: {path}"})
                dfs.append(df)

            if not dfs:
                return json.dumps({"error": "No valid files loaded"})

            self._df = pd.concat(dfs, ignore_index=True)

            # Clean data
            self._cleaned_df, self._cleaning_summary = clean_data(self._df)
            
            return self._generate_analysis_response(save_history=True)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return json.dumps({"error": str(e)})

    def _generate_analysis_response(self, save_history=False):
        try:
            # Detect columns
            self._columns = detect_columns(self._cleaned_df)

            # Calculate KPIs and insights
            self._kpis = calculate_kpis(self._cleaned_df, self._columns, use_case=self._current_use_case, lang=self._lang)
            self._insights = generate_insights(self._kpis)

            # Generate charts and apply dark theme before converting to HTML
            raw_charts = generate_charts(self._cleaned_df, self._columns, use_case=self._current_use_case)
            self._charts = {}
            for name, fig in raw_charts.items():
                fig.update_layout(
                    template='plotly_dark',
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color='#94a3b8'
                )
                self._charts[name] = fig.to_html(
                    include_plotlyjs='cdn',
                    full_html=False,
                    config={'responsive': True}
                )

            # Generate forecast
            forecast_result = forecast_primary_metric(self._cleaned_df, self._columns)
            forecast_html = None
            if forecast_result is not None:
                import plotly.graph_objects as go
                future_months, forecasted_values = forecast_result
                num_col_name = self._columns.get("primary_numeric", "Metric")
                
                forecast_fig = go.Figure()
                forecast_fig.add_trace(go.Scatter(
                    x=future_months,
                    y=forecasted_values,
                    mode='lines+markers',
                    name=f'Forecasted {num_col_name}',
                    line=dict(dash='dash', color='#0ea5e9')
                ))
                forecast_fig.update_layout(
                    title=f'6-Month {num_col_name} Forecast',
                    xaxis_title='Time',
                    yaxis_title=num_col_name,
                    template='plotly_dark',
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color='#94a3b8'
                )
                forecast_html = forecast_fig.to_html(
                    include_plotlyjs='cdn',
                    full_html=False,
                    config={'responsive': True}
                )

            # Get filter options (categorical columns)
            filters = {}
            if self._columns.get('categorical_columns'):
                for col in self._columns['categorical_columns']:
                    # Only send if < 50 unique values
                    if 1 < self._df[col].nunique() <= 50:
                        filters[col] = [str(x) for x in self._df[col].dropna().unique().tolist()]

            # Get data preview (first 10 rows)
            preview = self._cleaned_df.head(10)

            # Handle NaN/Infinity for JSON serialization
            def safe_value(v):
                if v is None:
                    return None
                if isinstance(v, float) and (np.isnan(v) or np.isinf(v)):
                    return None
                return v

            safe_kpis = {k: safe_value(v) for k, v in self._kpis.items()}

            # Detect anomalies
            anomalies = detect_anomalies(self._cleaned_df, self._columns, lang=self._lang)

            response = {
                "data_info": {
                    "rows": len(self._cleaned_df),
                    "columns": len(self._cleaned_df.columns),
                    "missing_values": int(self._cleaned_df.isnull().sum().sum()),
                    "duplicate_rows": int(self._cleaned_df.duplicated().sum()),
                    "column_names": list(self._cleaned_df.columns),
                    "preview": json.loads(
                        preview.to_json(orient='records', date_format='iso', default_handler=str)
                    ),
                },
                "cleaning_summary": self._cleaning_summary,
                "detected_columns": self._columns,
                "kpis": safe_kpis,
                "charts": self._charts,
                "insights": self._insights,
                "forecast": forecast_html,
                "filters": filters,
                "anomalies": anomalies,
                "ai": {
                    "enabled": _has_groq_key(),
                    "mode": "ai" if _has_groq_key() else "offline"
                }
            }

            if save_history:
                # Save to history
                try:
                    # Try to get the total sum for history if it exists
                    history_val = None
                    if self._columns and self._columns.get("primary_numeric"):
                        num_col = self._columns.get("primary_numeric")
                        total_key = f"Total {num_col}"
                        if total_key in self._kpis:
                            history_val = self._kpis[total_key]
                            
                    save_analysis_history(
                        self._current_user_id,
                        self._file_name,
                        len(self._cleaned_df),
                        len(self._cleaned_df.columns),
                        history_val,
                        None  # report path will be set later
                    )
                except Exception:
                    pass

            return json.dumps(response, default=str)

        except Exception as e:
            import traceback
            traceback.print_exc()
            return json.dumps({"error": str(e)})

    def apply_filter(self, filter_col, filter_val):
        """Filter the dataframe and regenerate analysis."""
        if self._current_user_id is None:
            return json.dumps({"error": "Please log in first."})
        if self._df is None:
            return json.dumps({"error": "No data loaded"})
            
        try:
            if filter_val == "ALL":
                # Reset to full dataset
                self._cleaned_df, self._cleaning_summary = clean_data(self._df)
            else:
                # Filter the original dataframe
                filtered_df = self._df[self._df[filter_col].astype(str) == filter_val].copy()
                self._cleaned_df, self._cleaning_summary = clean_data(filtered_df)
                
            return self._generate_analysis_response(save_history=False)
        except Exception as e:
            return json.dumps({"error": str(e)})

    def get_ai_insight(self):
        """Get AI business explanation using Groq."""
        if self._current_user_id is None:
            return "Please log in first."
        if not self._kpis or not self._columns:
            return "No data loaded yet. Please upload a file first."

        try:
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                self._ai_insight = self._build_offline_insight()
                return self._ai_insight

            self._ai_insight = get_gemini_insight(
                self._kpis, self._columns, self._charts, self._insights, api_key, use_case=self._current_use_case, lang=self._lang
            )
            return self._ai_insight
        except Exception as e:
            self._ai_insight = self._build_offline_insight(
                prefix=f"AI service is unavailable right now ({e}). Showing offline insights instead."
            )
            return self._ai_insight

    def _build_offline_insight(self, prefix=None):
        """Create useful rule-based insights when no AI provider is configured."""
        if self._lang == 'ar':
            intro = prefix or "Offline mode is active. These insights are generated locally without AI."
            empty = "There are not enough calculated metrics to generate detailed insights."
        else:
            intro = prefix or "Offline mode is active. These insights are generated locally without AI."
            empty = "There are not enough calculated metrics to generate detailed insights."

        lines = [f"**{intro}**"]
        source_insights = self._insights or []

        if source_insights:
            for insight in source_insights[:5]:
                lines.append(f"- {insight}")
        elif self._kpis:
            for key, value in list(self._kpis.items())[:5]:
                lines.append(f"- {key}: {value}")
        else:
            lines.append(f"- {empty}")

        return "\n".join(lines)

    def _build_report_preview_html(self, report_path, settings):
        """Build a reliable in-app report preview without relying on a PDF plugin."""
        brand_color = settings.get("brand_color") or "#0ea5e9"
        if not isinstance(brand_color, str) or not brand_color.startswith("#"):
            brand_color = "#0ea5e9"

        logo_data_url = _file_to_data_url(settings.get("logo_path"))
        logo_html = ""
        if logo_data_url:
            logo_html = f'<img class="logo" src="{logo_data_url}" alt="Company logo" />'

        kpi_items = ""
        for key, value in (self._kpis or {}).items():
            kpi_items += (
                f"<div class=\"kpi\"><span>{html.escape(str(key))}</span>"
                f"<strong>{html.escape(_format_preview_value(value))}</strong></div>"
            )

        insight_items = ""
        for insight in (self._insights or []):
            insight_items += f"<li>{html.escape(_business_preview_sentence(insight))}</li>"

        report_name = html.escape(os.path.basename(report_path))

        return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    :root {{ --brand: {html.escape(brand_color)}; }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: #e5e7eb;
      color: #111827;
      font-family: Inter, Segoe UI, Arial, sans-serif;
      line-height: 1.55;
    }}
    .page {{
      width: min(820px, calc(100% - 32px));
      min-height: 1050px;
      margin: 24px auto;
      padding: 44px 48px;
      background: #fff;
      box-shadow: 0 12px 34px rgba(15, 23, 42, 0.18);
    }}
    header {{
      display: flex;
      justify-content: space-between;
      gap: 24px;
      align-items: flex-start;
      padding-bottom: 24px;
      border-bottom: 4px solid var(--brand);
    }}
    h1 {{
      margin: 0 0 8px;
      color: var(--brand);
      font-size: 28px;
      line-height: 1.15;
    }}
    h2 {{
      margin: 28px 0 12px;
      color: var(--brand);
      font-size: 17px;
    }}
    p {{ margin: 0 0 8px; }}
    .muted {{ color: #6b7280; font-size: 12px; }}
    .logo {{
      max-width: 150px;
      max-height: 74px;
      object-fit: contain;
    }}
    .summary {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 12px;
      margin-top: 14px;
    }}
    .summary div, .kpi {{
      border: 1px solid #d1d5db;
      border-radius: 8px;
      padding: 12px;
      background: #f9fafb;
    }}
    .summary span, .kpi span, dt {{
      display: block;
      color: #6b7280;
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
    }}
    .summary strong, .kpi strong, dd {{
      display: block;
      margin: 4px 0 0;
      color: #111827;
      font-size: 18px;
    }}
    .kpis {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 12px;
    }}
    ul {{ margin: 0; padding-left: 20px; }}
    li {{ margin-bottom: 6px; }}
  </style>
</head>
<body>
  <article class="page">
    <header>
      <div>
        <h1>DataLens - Business Performance Report</h1>
        <p class="muted">Preview for {report_name}</p>
      </div>
      {logo_html}
    </header>

    <section>
      <h2>Business Snapshot</h2>
      <div class="summary">
        <div><span>Records Reviewed</span><strong>{len(self._cleaned_df):,}</strong></div>
        <div><span>Business Fields</span><strong>{len(self._cleaned_df.columns):,}</strong></div>
        <div><span>Data Gaps Found</span><strong>{int(self._cleaned_df.isnull().sum().sum()):,}</strong></div>
      </div>
    </section>

    <section>
      <h2>Performance Highlights</h2>
      <div class="kpis">{kpi_items or '<p class="muted">No KPIs were calculated.</p>'}</div>
    </section>

    <section>
      <h2>Business Takeaways</h2>
      <ul>{insight_items or '<li>No insights were generated.</li>'}</ul>
    </section>
  </article>
</body>
</html>"""

    def ask_chat_question(self, query):
        """Ask a natural language question about the dataset."""
        if self._current_user_id is None:
            return "Please log in first."
        if self._df is None:
            return "No data loaded yet."
        try:
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                return (
                    "Offline mode is active, so chat questions that require AI are disabled. "
                    "You can still use the KPIs, charts, anomalies, forecast, filters, and PDF report."
                )
            return ask_data_question(self._df, query, api_key, lang=self._lang)
        except Exception as e:
            return f"Error: {e}"

    def generate_report(self):
        """Generate PDF report and return path."""
        if self._current_user_id is None:
            return json.dumps({"error": "Please log in first."})
        if self._cleaned_df is None or self._kpis is None:
            return json.dumps({"error": "No data loaded"})

        try:
            settings = get_user_settings(self._current_user_id)
            self._ai_insight = get_gemini_insight(
                kpis=self._kpis,
                columns=self._columns,
                charts=self._charts,
                insights=self._insights,
                use_case=self._current_use_case,
                lang=self._lang
            )
            report_path = generate_report(
                self._cleaned_df,
                self._kpis,
                self._insights,
                charts=None,
                columns=self._columns,
                gemini_insight=self._ai_insight,
                lang=self._lang,
                logo_path=settings.get("logo_path"),
                brand_color=settings.get("brand_color")
            )

            return json.dumps({
                "path": report_path,
                "preview_html": self._build_report_preview_html(report_path, settings)
            })
        except Exception as e:
            return json.dumps({"error": str(e)})

    def open_report(self, path):
        """Open PDF report in system default viewer."""
        try:
            reports_dir = str(REPORTS_DIR.resolve())
            target_path = str(Path(path).resolve())
            if not target_path.lower().endswith(".pdf"):
                return "Error: Only PDF reports can be opened."
            if os.path.commonpath([reports_dir, target_path]) != reports_dir:
                return "Error: Report path is not allowed."
            if not os.path.exists(target_path):
                return "Error: Report not found."
            os.startfile(target_path)
            return "ok"
        except Exception as e:
            return f"Error: {e}"

    def get_history(self):
        """Get analysis history."""
        if self._current_user_id is None:
            return json.dumps([])
        try:
            history = load_analysis_history(self._current_user_id)
            return json.dumps(history, default=str)
        except Exception as e:
            return json.dumps([])

    def set_language(self, lang):
        """Set the current language for reports."""
        self._lang = lang if lang in ('en', 'ar') else 'en'
        return "ok"

    def get_settings(self):
        if self._current_user_id is None:
            return json.dumps({"logo_path": None, "brand_color": "#0ea5e9"})
        return json.dumps(get_user_settings(self._current_user_id))

    def save_settings(self, logo_path, brand_color):
        if self._current_user_id is None:
            return json.dumps({"error": "Not logged in"})
        if brand_color and (not isinstance(brand_color, str) or not brand_color.startswith("#") or len(brand_color) not in (4, 7)):
            brand_color = "#0ea5e9"
        if logo_path:
            mime_type, _ = mimetypes.guess_type(logo_path)
            if not mime_type or not mime_type.startswith("image/"):
                return json.dumps({"error": "Logo must be an image file."})
            if not _safe_existing_file(logo_path, ALLOWED_LOGO_EXTENSIONS, 8 * 1024 * 1024):
                return json.dumps({"error": "Logo must be a PNG/JPG image under 8 MB."})
        save_user_settings(self._current_user_id, logo_path, brand_color)
        return json.dumps({"status": "ok"})

    def get_email_settings(self):
        if not self._current_user_id or not is_user_admin(self._current_user_id):
            return json.dumps({"error": "Unauthorized"})
        return json.dumps(_smtp_public_status())

    def save_email_settings(self, host, port, user, password, from_name="DataLens", use_tls=True):
        if not self._current_user_id or not is_user_admin(self._current_user_id):
            return json.dumps({"error": "Unauthorized"})

        host = (host or "").strip()
        user = (user or "").strip()
        from_name = (from_name or "DataLens").strip()
        password = (password or "").strip()

        try:
            port = int(port)
        except (TypeError, ValueError):
            return json.dumps({"error": "SMTP port must be a number"})

        if not host or not user:
            return json.dumps({"error": "SMTP host and email user are required"})
        if port < 1 or port > 65535:
            return json.dumps({"error": "SMTP port is not valid"})
        if not password and not os.getenv("SMTP_PASS"):
            return json.dumps({"error": "SMTP password or app password is required"})

        updates = {
            "SMTP_HOST": host,
            "SMTP_PORT": str(port),
            "SMTP_USER": user,
            "SMTP_FROM_NAME": from_name,
            "SMTP_TLS": "true" if _to_bool(use_tls, True) else "false",
        }
        if password:
            updates["SMTP_PASS"] = password

        _write_app_env_values(updates)
        for key, value in updates.items():
            os.environ[key] = str(value)

        return json.dumps({"status": "ok", "settings": _smtp_public_status()})

    def save_current_dataset(self, name):
        if self._current_user_id is None:
            return json.dumps({"error": "Not logged in"})
        if not self._current_file_paths:
            return json.dumps({"error": "No files currently loaded."})
        name = str(name or '').strip()[:80]
        if not name:
            return json.dumps({"error": "Dataset name is required."})
        
        try:
            save_dataset(self._current_user_id, name, json.dumps(self._current_file_paths))
            return json.dumps({"status": "ok"})
        except Exception as e:
            return json.dumps({"error": str(e)})

    def get_saved_datasets(self):
        if self._current_user_id is None:
            return json.dumps([])
        try:
            datasets = get_saved_datasets(self._current_user_id)
            result = [{"id": d[0], "name": d[1], "file_paths": json.loads(d[2]), "created_at": d[3]} for d in datasets]
            return json.dumps(result, default=str)
        except Exception as e:
            return json.dumps([])

    def load_saved_dataset(self, dataset_id):
        if self._current_user_id is None:
            return json.dumps({"error": "Not logged in"})
        try:
            datasets = get_saved_datasets(self._current_user_id)
            for d in datasets:
                if d[0] == dataset_id:
                    file_paths = json.loads(d[2])
                    return self.upload_file(file_paths)
            return json.dumps({"error": "Dataset not found"})
        except Exception as e:
            return json.dumps({"error": str(e)})

    def delete_saved_dataset(self, dataset_id):
        if self._current_user_id is None:
            return json.dumps({"error": "Not logged in"})
        try:
            delete_saved_dataset(dataset_id, self._current_user_id)
            return json.dumps({"status": "ok"})
        except Exception as e:
            return json.dumps({"error": str(e)})

    # ---- Admin Endpoints ----
    def admin_get_users(self):
        if not self._current_user_id or not is_user_admin(self._current_user_id):
            return json.dumps({"error": "Unauthorized"})
        try:
            users = get_all_users()
            result = [{"id": u[0], "username": u[1], "is_admin": bool(u[2]), "created_at": u[3]} for u in users]
            return json.dumps(result, default=str)
        except Exception as e:
            return json.dumps({"error": str(e)})

    def admin_delete_user_api(self, user_id):
        if not self._current_user_id or not is_user_admin(self._current_user_id):
            return json.dumps({"error": "Unauthorized"})
        try:
            # Don't let admin delete themselves
            if user_id == self._current_user_id:
                return json.dumps({"error": "Cannot delete your own account."})
            admin_delete_user(user_id)
            return json.dumps({"status": "ok"})
        except Exception as e:
            return json.dumps({"error": str(e)})

    def admin_reset_password_api(self, user_id, new_password):
        if not self._current_user_id or not is_user_admin(self._current_user_id):
            return json.dumps({"error": "Unauthorized"})
        if not _valid_password(new_password):
            return json.dumps({"error": "Password must be at least 8 characters"})
        try:
            admin_reset_password(user_id, new_password)
            return json.dumps({"status": "ok"})
        except Exception as e:
            return json.dumps({"error": str(e)})
