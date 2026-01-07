# =============================================================================
# n8n Setup and Run Script for Windows (Without Docker)
# =============================================================================
# This script helps you install and run n8n locally using npx
#
# Prerequisites:
#   - Node.js 18+ (download from https://nodejs.org)
#
# Usage:
#   .\run_n8n.ps1
# =============================================================================

$ErrorActionPreference = "Continue"

Write-Host @"

╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║    🔧 n8n Workflow Automation Setup                          ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

"@ -ForegroundColor Cyan

# Check if Node.js is installed
Write-Host "🔍 Checking for Node.js..." -ForegroundColor Yellow
$node = Get-Command node -ErrorAction SilentlyContinue

if (-not $node) {
    Write-Host @"

❌ Node.js is not installed!

To run n8n, you need Node.js 18 or higher.

Installation options:

1. Download Node.js from: https://nodejs.org
   (Choose the LTS version)

2. Or install with winget:
   winget install OpenJS.NodeJS.LTS

3. Or use Chocolatey:
   choco install nodejs-lts

After installing Node.js, restart PowerShell and run this script again.

"@ -ForegroundColor Red
    exit 1
}

$nodeVersion = node --version
Write-Host "✅ Node.js found: $nodeVersion" -ForegroundColor Green

# Check if port 5678 is available
Write-Host "`n🔍 Checking port 5678..." -ForegroundColor Yellow
$connection = Test-NetConnection -ComputerName localhost -Port 5678 -WarningAction SilentlyContinue

if ($connection.TcpTestSucceeded) {
    Write-Host "⚠️  Port 5678 is already in use. n8n may already be running." -ForegroundColor Yellow
    Write-Host "   Access it at: http://localhost:5678" -ForegroundColor Cyan
    Start-Process "http://localhost:5678"
    exit 0
}

# Set n8n environment variables
$env:N8N_PORT = "5678"
$env:N8N_PROTOCOL = "http"
$env:N8N_HOST = "localhost"
$env:WEBHOOK_URL = "http://localhost:5678/"
$env:GENERIC_TIMEZONE = "UTC"
$env:N8N_BASIC_AUTH_ACTIVE = "false"

Write-Host @"

🚀 Starting n8n...

This will:
1. Download n8n (first time only)
2. Start n8n on http://localhost:5678
3. Create data directory in: $env:USERPROFILE\.n8n

"@ -ForegroundColor Yellow

# Create workflows directory
$workflowsDir = Join-Path (Get-Location) "n8n"
if (-not (Test-Path $workflowsDir)) {
    New-Item -ItemType Directory -Path $workflowsDir | Out-Null
}

Write-Host "📂 Workflows directory: $workflowsDir" -ForegroundColor Cyan

# Start n8n
Write-Host "`n🔧 Launching n8n (this may take a moment on first run)...`n" -ForegroundColor Yellow

try {
    # Run npx n8n
    Start-Process powershell -ArgumentList @(
        "-NoExit",
        "-Command",
        "cd '$workflowsDir'; Write-Host '🚀 n8n Starting...' -ForegroundColor Cyan; npx n8n"
    )
    
    Write-Host "✅ n8n window opened" -ForegroundColor Green
    Start-Sleep 5
    
    Write-Host @"

╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║    🎉 n8n Started!                                           ║
║                                                              ║
║    Access n8n at: http://localhost:5678                      ║
║                                                              ║
║    Next steps:                                               ║
║    1. Go to http://localhost:5678                            ║
║    2. Create an account (first time only)                    ║
║    3. Import workflow from: n8n/workflow_production.json     ║
║    4. Configure environment variables in workflow            ║
║                                                              ║
║    Environment variables to set in n8n:                      ║
║    - MCP_SERVER_URL: http://localhost:8000                   ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

"@ -ForegroundColor Green

    # Wait and open browser
    Start-Sleep 5
    Write-Host "🌐 Opening n8n in browser..." -ForegroundColor Yellow
    Start-Process "http://localhost:5678"
    
} catch {
    Write-Host "`n❌ Failed to start n8n: $_" -ForegroundColor Red
    Write-Host "`nTry running manually: npx n8n" -ForegroundColor Yellow
}

Write-Host "`n✅ Setup complete! Close the n8n window to stop it.`n" -ForegroundColor Green
