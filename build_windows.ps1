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

For the easiest install:
1. Download DataLens-Setup.exe from GitHub Actions.
2. Open it.
3. Keep the desktop shortcut selected.

If you downloaded the zip instead, unzip it first and run DataLens.exe.
"@ | Set-Content -Path "dist\DataLens\README-download.txt" -Encoding UTF8

if (Test-Path "DataLens-windows.zip") {
  Remove-Item "DataLens-windows.zip" -Force
}

Compress-Archive -Path "dist\DataLens\*" -DestinationPath "DataLens-windows.zip" -Force

if (Test-Path "DataLens-Setup.exe") {
  Remove-Item "DataLens-Setup.exe" -Force
}

$InnoCompiler = Get-Command "iscc.exe" -ErrorAction SilentlyContinue
if (-not $InnoCompiler) {
  $DefaultInnoCompiler = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
  if (Test-Path $DefaultInnoCompiler) {
    $InnoCompiler = Get-Item $DefaultInnoCompiler
  }
}

if ($InnoCompiler) {
  & $InnoCompiler.Source "installer\DataLens.iss"
  Copy-Item "dist\DataLens-Setup.exe" "DataLens-Setup.exe" -Force
  Write-Host "Created DataLens-Setup.exe"
} else {
  Write-Host "Inno Setup was not found, so the installer was skipped."
}

Write-Host "Built dist\DataLens\DataLens.exe"
Write-Host "Created DataLens-windows.zip"
