# PowerBI Genius AI — Local Development Startup Script

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " PowerBI Genius AI — Starting Services " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Check .env
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "[!] .env created from .env.example. Please fill in your OPENAI_API_KEY." -ForegroundColor Yellow
    exit 1
}

# Backend
Write-Host "`n[1/2] Starting FastAPI Backend..." -ForegroundColor Green
$backendJob = Start-Job -ScriptBlock {
    Set-Location "C:\Users\user\powerbi-genius-ai\backend"
    pip install -r requirements.txt -q
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
}

Start-Sleep -Seconds 3

# Frontend
Write-Host "[2/2] Starting Next.js Frontend..." -ForegroundColor Green
$frontendJob = Start-Job -ScriptBlock {
    Set-Location "C:\Users\user\powerbi-genius-ai\frontend"
    npm install -q
    npm run dev
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host " Services starting..." -ForegroundColor Cyan
Write-Host " Backend:  http://localhost:8000" -ForegroundColor White
Write-Host " Frontend: http://localhost:3000" -ForegroundColor White
Write-Host " API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Press Ctrl+C to stop all services." -ForegroundColor Gray
Wait-Job $backendJob, $frontendJob
