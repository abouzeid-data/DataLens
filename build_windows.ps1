param(
  [string]$Python = "python"
)

$ErrorActionPreference = "Stop"

& $Python -m pip install --upgrade pip
& $Python -m pip install -r requirements.txt pyinstaller

if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }

& $Python -m PyInstaller `
  --noconfirm `
  --clean `
  --windowed `
  --name DataLens `
  --icon "frontend\assets\DataLens.ico" `
  --add-data "frontend;frontend" `
  main.py

Copy-Item ".env.example" "dist\DataLens\.env.example" -Force
@"
DataLens for Windows

Run DataLens.exe to start the app.

Password reset emails require SMTP settings.
To enable them:
1. Copy .env.example to .env in this folder, or create %APPDATA%\DataLens\.env
2. Fill in SMTP_HOST, SMTP_PORT, SMTP_USER, and SMTP_PASS
3. Restart DataLens

Do not publish your .env file.
"@ | Set-Content -Path "dist\DataLens\README-download.txt" -Encoding UTF8

if (Test-Path "DataLens-windows.zip") {
  Remove-Item "DataLens-windows.zip" -Force
}

Compress-Archive -Path "dist\DataLens\*" -DestinationPath "DataLens-windows.zip" -Force

Write-Host "Built dist\DataLens\DataLens.exe"
Write-Host "Created DataLens-windows.zip"
