# DataLens

DataLens is a Windows desktop app for analyzing Excel and CSV files. It loads one or more datasets, cleans the data, detects useful columns, calculates KPIs, builds charts, highlights anomalies, creates forecasts, and generates PDF reports.

## Features

1. Upload CSV, XLS, or XLSX files.
2. Merge multiple uploaded files into one analysis.
3. Show a data preview and dataset summary.
4. Clean duplicates, text spacing, numeric columns, and date columns.
5. Detect date, numeric, and categorical columns automatically.
6. Calculate KPIs from the detected primary metric and category.
7. Generate charts and visual summaries.
8. Generate rule-based business insights locally.
9. Use Groq AI explanations when `GROQ_API_KEY` is configured.
10. Fall back to offline/no-AI insights when no API key is available.
11. Forecast the primary metric when enough dated data exists.
12. Preview PDF reports inside the app before opening them.
13. Save local analysis history with SQLite.

## Installation

```bash
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and add `GROQ_API_KEY` if you want AI explanations. Add SMTP settings if you want password reset emails. The app still works without a Groq key.

For the downloadable Windows app, place `.env` next to `DataLens.exe` or create `%APPDATA%\DataLens\.env`. Password reset emails will not send until SMTP settings are configured.

## How To Run

```bash
python main.py
```

The DataLens desktop window will open. Log in or register, then upload a CSV or Excel file to start analyzing.

## Downloadable Windows Build

The GitHub Actions workflow `Build Windows App` creates two downloadable artifacts:

1. `DataLens-Setup`: a Windows installer that creates a Desktop shortcut and Start Menu shortcut.
2. `DataLens-windows`: a portable zip for users who do not want an installer.

To build locally on Windows:

```powershell
.\build_windows.ps1
```

The packaged app will be created at `dist\DataLens\DataLens.exe`, a zip file will be created as `DataLens-windows.zip`, and `DataLens-Setup.exe` will be created when Inno Setup is installed.

## Security Notes

- Do not commit `.env`, `database/app.db`, or generated reports.
- Passwords are stored with salted PBKDF2 hashes.
- Password reset links expire after one hour.
- SMTP credentials are not shipped in the public app. Configure them locally with `.env`.
- AI chat uses dataset summaries only; it does not execute AI-generated code.

## Project Structure

```text
DataLens/
|-- main.py                 # Desktop app entry point
|-- api.py                  # Python bridge for the desktop UI
|-- build_windows.ps1       # Local Windows packaging script
|-- installer/              # Windows installer setup
|-- .github/workflows/      # GitHub Actions build workflow
|-- frontend/               # HTML, CSS, and JavaScript interface
|   `-- assets/LOGO.png     # App logo
|-- core/                   # Data cleaning, KPIs, charts, insights, forecasting, reports
|-- database/               # SQLite storage
|-- reports/                # Generated PDF reports
|-- requirements.txt
`-- README.md
```
