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
  --add-data "frontend;frontend" `
  main.py

Copy-Item ".env.example" "dist\DataLens\.env.example" -Force

if (Test-Path "DataLens-windows.zip") {
  Remove-Item "DataLens-windows.zip" -Force
}

Compress-Archive -Path "dist\DataLens\*" -DestinationPath "DataLens-windows.zip" -Force

Write-Host "Built dist\DataLens\DataLens.exe"
Write-Host "Created DataLens-windows.zip"
