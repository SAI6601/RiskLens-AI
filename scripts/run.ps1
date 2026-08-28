$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot

if (-not (Test-Path -LiteralPath "artifacts\model.joblib")) {
    Write-Host "No local model artifact found. Training RiskLens AI..."
    python scripts\train_model.py
}

python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

