# PrepAI - Run Backend + Frontend locally
# Run in two separate terminals, or use: .\run-local.ps1

Write-Host "Starting PrepAI..." -ForegroundColor Cyan
Write-Host ""
Write-Host "Terminal 1 - Backend:" -ForegroundColor Yellow
Write-Host "  cd backend"
Write-Host "  .\venv\Scripts\activate"
Write-Host "  python app.py"
Write-Host ""
Write-Host "Terminal 2 - Frontend:" -ForegroundColor Yellow
Write-Host "  cd frontend"
Write-Host "  npm run dev"
Write-Host ""
Write-Host "Backend:  http://localhost:5000" -ForegroundColor Green
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Green
