#!/usr/bin/env python3
"""
Quick Start Script
==================
All-in-one script to start the MCP Lead Generation System.
"""

import os
import sys
import time
import subprocess
import argparse
from pathlib import Path


def print_banner():
    """Print startup banner."""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║    🚀 MCP Lead Generation System                             ║
║                                                              ║
║    Services:                                                 ║
║    • MCP Server (FastAPI)  →  http://localhost:8000          ║
║    • API Documentation     →  http://localhost:8000/docs     ║
║    • Streamlit Dashboard   →  http://localhost:8501          ║
║    • n8n Workflows         →  http://localhost:5678          ║
║    • Mailhog (Email Test)  →  http://localhost:8025          ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def check_python():
    """Check Python version."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print("❌ Python 3.9+ is required")
        sys.exit(1)
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")


def check_docker():
    """Check if Docker is available."""
    try:
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"✅ {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    print("⚠️  Docker not found (optional for full deployment)")
    return False


def check_requirements():
    """Check if requirements are installed."""
    try:
        import fastapi
        import uvicorn
        import streamlit
        import faker
        print("✅ Python dependencies installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e.name}")
        print("   Run: pip install -r requirements.txt")
        return False


def setup_environment():
    """Set up environment variables."""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        print("📋 Creating .env from .env.example")
        env_file.write_text(env_example.read_text())
    
    # Load environment
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip())
    
    print("✅ Environment configured")


def create_storage_dir():
    """Create storage directory."""
    storage_dir = Path("storage")
    storage_dir.mkdir(exist_ok=True)
    print("✅ Storage directory ready")


def start_mcp_server():
    """Start the MCP server."""
    print("\n🚀 Starting MCP Server...")
    
    # Change to backend directory
    backend_dir = Path(__file__).parent / "backend"
    
    cmd = [
        sys.executable, "-m", "uvicorn",
        "mcp_server.server:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload"
    ]
    
    return subprocess.Popen(
        cmd,
        cwd=str(backend_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )


def start_streamlit():
    """Start Streamlit dashboard."""
    print("🚀 Starting Streamlit Dashboard...")
    
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        "frontend/app.py",
        "--server.port", "8501",
        "--server.address", "0.0.0.0"
    ]
    
    return subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )


def wait_for_server(url, timeout=30):
    """Wait for server to be ready."""
    import urllib.request
    import urllib.error
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            urllib.request.urlopen(url, timeout=2)
            return True
        except (urllib.error.URLError, ConnectionRefusedError):
            time.sleep(1)
    return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Start MCP Lead Generation System")
    parser.add_argument("--docker", action="store_true", help="Use Docker Compose")
    parser.add_argument("--server-only", action="store_true", help="Start only MCP server")
    parser.add_argument("--check", action="store_true", help="Check dependencies only")
    args = parser.parse_args()
    
    print_banner()
    
    # Check dependencies
    print("\n📦 Checking dependencies...")
    check_python()
    has_docker = check_docker()
    has_deps = check_requirements()
    
    if args.check:
        sys.exit(0 if has_deps else 1)
    
    if args.docker and has_docker:
        print("\n🐳 Starting with Docker Compose...")
        subprocess.run(["docker-compose", "up", "-d"])
        print("\n✅ All services started!")
        print("   View logs: docker-compose logs -f")
        return
    
    if not has_deps:
        print("\n❌ Cannot start - missing dependencies")
        sys.exit(1)
    
    # Setup
    setup_environment()
    create_storage_dir()
    
    processes = []
    
    try:
        # Start MCP Server
        mcp_proc = start_mcp_server()
        processes.append(mcp_proc)
        
        # Wait for server
        print("   Waiting for server...")
        if wait_for_server("http://localhost:8000/health"):
            print("   ✅ MCP Server ready!")
        else:
            print("   ⚠️  Server taking longer than expected...")
        
        if not args.server_only:
            # Start Streamlit
            streamlit_proc = start_streamlit()
            processes.append(streamlit_proc)
            
            time.sleep(3)
            print("   ✅ Streamlit Dashboard ready!")
        
        print("\n" + "="*60)
        print("🎉 System is running!")
        print("="*60)
        print("\nPress Ctrl+C to stop all services\n")
        
        # Keep running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down...")
        for proc in processes:
            proc.terminate()
        print("✅ All services stopped")


if __name__ == "__main__":
    main()
