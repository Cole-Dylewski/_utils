# Development environment setup script for Windows PowerShell
# 
# Note: For cross-platform setup, use: python setup-venv.py
# This script is provided for convenience on Windows.

Write-Host "Setting up _utils development environment..." -ForegroundColor Cyan

# Check Python version
$pythonVersion = python --version 2>&1 | Select-String -Pattern "(\d+\.\d+)" | ForEach-Object { $_.Matches.Groups[1].Value }
$requiredVersion = "3.10"

if ([version]$pythonVersion -lt [version]$requiredVersion) {
    Write-Host "Error: Python 3.10 or higher is required. Found: $pythonVersion" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Python version check passed: $pythonVersion" -ForegroundColor Green

# Create virtual environment if it doesn't exist
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
    Write-Host "✓ Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "✓ Virtual environment already exists" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .venv\Scripts\Activate.ps1

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install package with dev dependencies
Write-Host "Installing package with development dependencies..." -ForegroundColor Yellow
pip install -e ".[dev]"

# Install pre-commit hooks
Write-Host "Installing pre-commit hooks..." -ForegroundColor Yellow
pre-commit install

Write-Host ""
Write-Host "✓ Development environment setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "To activate the virtual environment in the future, run:" -ForegroundColor Cyan
Write-Host "  .venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host ""
Write-Host "To run tests:" -ForegroundColor Cyan
Write-Host "  pytest" -ForegroundColor White
Write-Host ""
Write-Host "To run linting:" -ForegroundColor Cyan
Write-Host "  ruff check ." -ForegroundColor White
Write-Host ""
Write-Host "To format code:" -ForegroundColor Cyan
Write-Host "  ruff format ." -ForegroundColor White
Write-Host ""

