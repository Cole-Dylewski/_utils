# PowerShell virtual environment activation script for Windows

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvDir = Join-Path $scriptDir ".venv"
$activateScript = Join-Path $venvDir "Scripts\Activate.ps1"

if (-not (Test-Path $venvDir)) {
    Write-Host "Error: Virtual environment not found at $venvDir" -ForegroundColor Red
    Write-Host "Run 'python setup-venv.py' to create it." -ForegroundColor Yellow
    exit 1
}

if (Test-Path $activateScript) {
    & $activateScript
    Write-Host "✓ Virtual environment activated" -ForegroundColor Green
} else {
    Write-Host "Error: Could not find activation script at $activateScript" -ForegroundColor Red
    exit 1
}

