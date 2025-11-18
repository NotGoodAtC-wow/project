# Creates a Python 3.11 virtual environment in .venv and installs dependencies
param()

$ErrorActionPreference = "Stop"

Write-Host "=== Smart Inventory: venv setup (Python 3.11) ===" -ForegroundColor Cyan

# Check 'py' launcher
if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    Write-Error "Python launcher 'py' is not found. Please install Python 3.11 from microsoft store or python.org and ensure 'py' is in PATH."
}

# Ensure Python 3.11 is available
try {
    $ver = & py -3.11 -c "import sys;print(sys.version.split()[0])"
    Write-Host "Using Python $ver" -ForegroundColor Green
} catch {
    Write-Error "Python 3.11 is not available via 'py -3.11'. Install Python 3.11 first."
}

# Create venv
if (Test-Path .venv) {
    Write-Host ".venv already exists. Skipping creation." -ForegroundColor Yellow
} else {
    Write-Host "Creating virtual environment: .venv" -ForegroundColor Cyan
    & py -3.11 -m venv .venv
}

# Upgrade pip and install dependencies using the venv's interpreter
$venvPython = Join-Path (Resolve-Path .venv).Path "Scripts/python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Error "Virtual environment python not found at $venvPython"
}

Write-Host "Upgrading pip..." -ForegroundColor Cyan
& $venvPython -m pip install --upgrade pip

if (Test-Path requirements.txt) {
    Write-Host "Installing requirements from requirements.txt..." -ForegroundColor Cyan
    & $venvPython -m pip install -r requirements.txt
} else {
    Write-Warning "requirements.txt not found. Skipping dependency installation."
}

Write-Host "\nDone. To activate the virtual environment in this shell, run:" -ForegroundColor Green
Write-Host ".\.venv\Scripts\Activate.ps1" -ForegroundColor Yellow

Write-Host "Then start the server with:" -ForegroundColor Green
Write-Host "uvicorn app.main:app --reload" -ForegroundColor Yellow
