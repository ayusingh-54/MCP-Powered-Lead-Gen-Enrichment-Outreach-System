# =============================================================================
# Docker Compose Startup Script
# =============================================================================
# Builds and starts all services using Docker Compose
#
# Usage:
#   .\docker-start.ps1           # Start all services
#   .\docker-start.ps1 -Build    # Rebuild images and start
#   .\docker-start.ps1 -Down     # Stop and remove containers
# =============================================================================

param(
    [switch]$Build,
    [switch]$Down,
    [switch]$Logs
)

$ErrorActionPreference = "Continue"

Write-Host @"

╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║    🐳 MCP Lead Generation System - Docker                    ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

"@ -ForegroundColor Cyan

# Check if Docker is running
Write-Host "Checking Docker..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "Docker found: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Docker is not installed or not running!" -ForegroundColor Red
    Write-Host "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
    exit 1
}

# Change to project directory
Set-Location "d:\New folder"

if ($Down) {
    Write-Host "`nStopping and removing containers..." -ForegroundColor Yellow
    docker-compose down -v
    Write-Host "Services stopped and removed." -ForegroundColor Green
    exit 0
}

if ($Logs) {
    Write-Host "`nShowing logs (Ctrl+C to exit)..." -ForegroundColor Yellow
    docker-compose logs -f
    exit 0
}

# Create storage directory
if (-not (Test-Path "storage")) {
    New-Item -ItemType Directory -Path "storage" | Out-Null
    Write-Host "Created storage directory" -ForegroundColor Green
}

# Ensure .env exists
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "Created .env file from .env.example" -ForegroundColor Green
    } else {
        Write-Host "Warning: .env file not found" -ForegroundColor Yellow
    }
}

if ($Build) {
    Write-Host "`nBuilding Docker images..." -ForegroundColor Yellow
    docker-compose build --no-cache
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Build failed!" -ForegroundColor Red
        exit 1
    }
}

Write-Host "`nStarting services with Docker Compose..." -ForegroundColor Yellow
docker-compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to start services!" -ForegroundColor Red
    exit 1
}

Write-Host "`nWaiting for services to be healthy..." -ForegroundColor Yellow
Start-Sleep 10

# Check service status
Write-Host "`nService Status:" -ForegroundColor Cyan
docker-compose ps

# Test connections
Write-Host "`nTesting connections..." -ForegroundColor Yellow
Start-Sleep 5

$services = @(
    @{Name="MCP Server"; Url="http://localhost:8000/health"},
    @{Name="Streamlit"; Url="http://localhost:8501"},
    @{Name="n8n"; Url="http://localhost:5678"},
    @{Name="Mailhog"; Url="http://localhost:8025"}
)

foreach ($service in $services) {
    try {
        $response = Invoke-WebRequest -Uri $service.Url -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
        Write-Host "[OK] $($service.Name): Running" -ForegroundColor Green
    } catch {
        Write-Host "[WAIT] $($service.Name): Starting..." -ForegroundColor Yellow
    }
}

Write-Host @"

╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║    🎉 Docker Services Started!                               ║
║                                                              ║
║    Access your services:                                     ║
║    • MCP Server:      http://localhost:8000                  ║
║    • API Docs:        http://localhost:8000/docs             ║
║    • Dashboard:       http://localhost:8501                  ║
║    • n8n:             http://localhost:5678                  ║
║    • Mailhog:         http://localhost:8025                  ║
║                                                              ║
║    Useful commands:                                          ║
║    • View logs:       docker-compose logs -f                 ║
║    • Stop services:   docker-compose down                    ║
║    • Restart:         docker-compose restart                 ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

"@ -ForegroundColor Green

# Open browser
Write-Host "Opening services in browser..." -ForegroundColor Yellow
Start-Sleep 2
Start-Process "http://localhost:8000/docs"
Start-Sleep 1
Start-Process "http://localhost:8501"

Write-Host "`nServices are running in Docker!" -ForegroundColor Green
Write-Host "Use 'docker-compose logs -f' to view logs" -ForegroundColor Cyan
Write-Host "Use 'docker-compose down' to stop all services`n" -ForegroundColor Cyan
