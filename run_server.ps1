# =============================================================================
# MCP Lead Generation System - PowerShell Startup Script
# =============================================================================
# This script starts all services for Windows without Docker
#
# Usage:
#   .\run_server.ps1              # Start all services
#   .\run_server.ps1 -ServerOnly  # Start only MCP server
# =============================================================================

param(
    [switch]$ServerOnly,
    [switch]$FrontendOnly
)

$ErrorActionPreference = "Continue"

Write-Host @"

╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║    🚀 MCP Lead Generation System                             ║
║                                                              ║
║    Starting Services...                                      ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

"@ -ForegroundColor Cyan

# Change to project directory
Set-Location "d:\New folder"

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

# Create storage directory
if (-not (Test-Path "storage")) {
    New-Item -ItemType Directory -Path "storage" | Out-Null
    Write-Host "Created storage directory" -ForegroundColor Green
}

# Create .env if not exists
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env file" -ForegroundColor Green
}

# Function to test if port is available
function Test-PortAvailable {
    param([int]$Port)
    $connection = Test-NetConnection -ComputerName localhost -Port $Port -WarningAction SilentlyContinue
    return -not $connection.TcpTestSucceeded
}

# Start MCP Server
if (-not $FrontendOnly) {
    Write-Host "`nStarting MCP Server on port 8000..." -ForegroundColor Yellow
    
    if (Test-PortAvailable -Port 8000) {
        Start-Process powershell -ArgumentList @(
            "-NoExit",
            "-Command",
            "cd 'd:\New folder'; .\.venv\Scripts\Activate.ps1; Write-Host 'MCP Server Starting...' -ForegroundColor Cyan; python -m uvicorn backend.mcp_server.server:app --host 127.0.0.1 --port 8000"
        )
        Write-Host "   MCP Server window opened" -ForegroundColor Green
        Start-Sleep 3
    } else {
        Write-Host "   Port 8000 already in use" -ForegroundColor Yellow
    }
}

# Start Streamlit Dashboard
if (-not $ServerOnly) {
    Write-Host "`nStarting Streamlit Dashboard on port 8501..." -ForegroundColor Yellow
    
    if (Test-PortAvailable -Port 8501) {
        Start-Process powershell -ArgumentList @(
            "-NoExit",
            "-Command",
            "cd 'd:\New folder'; .\.venv\Scripts\Activate.ps1; Write-Host 'Streamlit Dashboard Starting...' -ForegroundColor Cyan; python -m streamlit run frontend/app.py --server.port 8501"
        )
        Write-Host "   Streamlit Dashboard window opened" -ForegroundColor Green
    } else {
        Write-Host "   Port 8501 already in use" -ForegroundColor Yellow
    }
}

Start-Sleep 5

# Test connections
Write-Host "`nTesting connections..." -ForegroundColor Yellow

$mcp_status = try {
    $response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -TimeoutSec 5
    "[OK] MCP Server: Running"
} catch {
    "[WAIT] MCP Server: Not responding (may still be starting...)"
}

$streamlit_status = try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:8501" -TimeoutSec 5 -UseBasicParsing
    "[OK] Streamlit: Running"
} catch {
    "[WAIT] Streamlit: Not responding (may still be starting...)"
}

Write-Host $mcp_status -ForegroundColor $(if ($mcp_status -like "*Running*") { "Green" } else { "Yellow" })
Write-Host $streamlit_status -ForegroundColor $(if ($streamlit_status -like "*Running*") { "Green" } else { "Yellow" })

# Display service URLs
Write-Host @"

╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║    🎉 System Started!                                        ║
║                                                              ║
║    Access your services:                                     ║
║    • MCP Server API:  http://localhost:8000                  ║
║    • API Docs:        http://localhost:8000/docs             ║
║    • Dashboard:       http://localhost:8501                  ║
║                                                              ║
║    Note: Services may take a few seconds to fully start      ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

"@ -ForegroundColor Green

# Open browser
Write-Host "Opening browser..." -ForegroundColor Yellow
Start-Sleep 2
Start-Process "http://localhost:8000/docs"
Start-Sleep 1
if (-not $ServerOnly) {
    Start-Process "http://localhost:8501"
}

Write-Host "`nAll services started! Close the service windows to stop them.`n" -ForegroundColor Green
