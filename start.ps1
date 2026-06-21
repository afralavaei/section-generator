# Nomadic Engine startup script
# Starts: FastAPI (8000) + Streamlit (8501) + React UI (5173)
# Run with:
#   powershell -ExecutionPolicy Bypass -File "d:\Bartlett\RC 5\Studio\Term 3\1\sections\start.ps1"

$PYTHON    = "C:\Users\Afra Lavaei\AppData\Local\Python\pythoncore-3.14-64\python.exe"
$STREAMLIT = "C:\Users\Afra Lavaei\AppData\Local\Python\pythoncore-3.14-64\Scripts\streamlit.exe"
$NPM       = "C:\Program Files\nodejs\npm.cmd"
$BACKEND   = "d:\Bartlett\RC 5\Studio\Term 3\1\sections"
$FRONTEND  = "d:\Bartlett\RC 5\Studio\Term 3\1\sections\nomadic-dwell-engine"


# ── Helpers ───────────────────────────────────────────────────

function Clear-Port($port) {
    $lines = netstat -ano 2>$null | Select-String ":$port\s"
    $pids  = $lines | ForEach-Object {
        $parts = ($_ -split '\s+') | Where-Object { $_ -ne '' }
        $parts[-1]
    } | Where-Object { $_ -match '^\d+$' } | Sort-Object -Unique
    foreach ($p in $pids) {
        Stop-Process -Id ([int]$p) -Force -ErrorAction SilentlyContinue
    }
}

function Test-Http($url) {
    try {
        $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
        return ($r.StatusCode -ge 200 -and $r.StatusCode -lt 400)
    } catch {
        return $false
    }
}

function Wait-Http($url, $timeoutSec = 40) {
    $deadline = (Get-Date).AddSeconds($timeoutSec)
    while ((Get-Date) -lt $deadline) {
        if (Test-Http $url) { return $true }
        Start-Sleep -Seconds 2
    }
    return $false
}

function Test-PortListening($port) {
    $hit = netstat -ano 2>$null | Select-String ":$port\s.*LISTENING"
    return ($null -ne $hit)
}

function Wait-Port($port, $timeoutSec = 60) {
    $deadline = (Get-Date).AddSeconds($timeoutSec)
    while ((Get-Date) -lt $deadline) {
        if (Test-PortListening $port) { return $true }
        Start-Sleep -Seconds 2
    }
    return $false
}

function Show-Status($ok, $label, $url) {
    if ($ok) {
        Write-Host ("  [OK]   " + $label.PadRight(24) + $url) -ForegroundColor Green
    } else {
        Write-Host ("  [FAIL] " + $label) -ForegroundColor Red
    }
}


# ── Banner ────────────────────────────────────────────────────

Write-Host ""
Write-Host "  Nomadic Engine - Starting services" -ForegroundColor Cyan
Write-Host "  -----------------------------------" -ForegroundColor DarkGray
Write-Host ""


# ── FastAPI (port 8000) ───────────────────────────────────────

Write-Host "  Checking FastAPI  (port 8000) ..." -ForegroundColor Gray
$apiOk = Test-Http "http://localhost:8000/health"

if (-not $apiOk) {
    Write-Host "  Not running - starting ..." -ForegroundColor Gray
    Clear-Port 8000
    Start-Sleep 1
    Start-Process -FilePath $PYTHON `
        -ArgumentList "-m", "uvicorn", "api:app", "--port", "8000" `
        -WorkingDirectory $BACKEND -WindowStyle Hidden
    $apiOk = Wait-Http "http://localhost:8000/health" 40
}

Show-Status $apiOk "FastAPI" "http://localhost:8000"
if (-not $apiOk) {
    Write-Host "         Check api.py for import errors." -ForegroundColor DarkRed
}


# ── Streamlit (port 8501) ─────────────────────────────────────

Write-Host "  Checking Streamlit (port 8501) ..." -ForegroundColor Gray
$stOk = Test-Http "http://localhost:8501/_stcore/health"

if (-not $stOk) {
    Write-Host "  Not running - starting ..." -ForegroundColor Gray
    Clear-Port 8501
    Start-Sleep 1
    Start-Process -FilePath $STREAMLIT `
        -ArgumentList "run", "app.py", "--server.port", "8501" `
        -WorkingDirectory $BACKEND -WindowStyle Hidden
    $stOk = Wait-Http "http://localhost:8501/_stcore/health" 40
}

Show-Status $stOk "Streamlit (debug)" "http://localhost:8501"
if (-not $stOk) {
    Write-Host "         Check app.py for errors." -ForegroundColor DarkRed
}


# ── React UI (port 5173) ──────────────────────────────────────

Write-Host "  Checking React UI (port 5173) ..." -ForegroundColor Gray
$reactOk = Test-PortListening 5173

if (-not $reactOk) {
    Write-Host "  Not running - starting ..." -ForegroundColor Gray
    Clear-Port 5173

    if (-not (Test-Path (Join-Path $FRONTEND "node_modules"))) {
        Write-Host "  node_modules missing - running npm install (first time only) ..." -ForegroundColor Yellow
        Start-Process -FilePath $NPM -ArgumentList "install" `
            -WorkingDirectory $FRONTEND -WindowStyle Hidden -PassThru -Wait | Out-Null
    }

    Start-Process -FilePath $NPM -ArgumentList "run", "dev", "--", "--port", "5173" `
        -WorkingDirectory $FRONTEND -WindowStyle Hidden
    $reactOk = Wait-Port 5173 60
}

Show-Status $reactOk "React UI" "http://localhost:5173"
if (-not $reactOk) {
    Write-Host "         Try running npm install manually in nomadic-dwell-engine/." -ForegroundColor DarkRed
}


# ── Summary ───────────────────────────────────────────────────

Write-Host ""
Write-Host "  -----------------------------------" -ForegroundColor DarkGray

if ($reactOk -and $apiOk) {
    Write-Host "  All services running. Open in your browser:" -ForegroundColor White
    Write-Host ""
    Write-Host "    http://localhost:5173" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  (Streamlit debug: http://localhost:8501)" -ForegroundColor DarkGray
} elseif ($stOk -and $apiOk) {
    Write-Host "  React failed. Use Streamlit for now:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "    http://localhost:8501" -ForegroundColor Cyan
} else {
    Write-Host "  One or more services failed. Fix errors above and re-run." -ForegroundColor Red
}

Write-Host "  -----------------------------------" -ForegroundColor DarkGray
Write-Host ""
