# iOS Device Bridge — Download & Build on Windows 11
# Right-click -> "Run with PowerShell"

Write-Host "iOS Device Bridge — Download & Build" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

# Check Python
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) {
    Write-Host "[ERROR] Python not found! Download from: https://python.org" -ForegroundColor Red
    pause
    exit 1
}
Write-Host "[OK] Python $($py.Source)" -ForegroundColor Green

# Install deps
Write-Host "[INFO] Installing dependencies..." -ForegroundColor Yellow
pip install PyQt6 pymobiledevice3 pyinstaller 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] pip install failed" -ForegroundColor Red
    pause
    exit 1
}
Write-Host "[OK] Dependencies installed" -ForegroundColor Green

# Build
Write-Host "[BUILD] Building .exe..." -ForegroundColor Yellow
python build.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Build failed" -ForegroundColor Red
    pause
    exit 1
}

Write-Host "[OK] Build complete!" -ForegroundColor Green
Write-Host "  .exe: $PWD\dist\iOSDeviceBridge.exe" -ForegroundColor Green
Write-Host "  Size: $((Get-Item dist\iOSDeviceBridge.exe).Length / 1MB) MB" -ForegroundColor Green

pause
