#!/usr/bin/env python3
"""
Health Check Script
===================
Check the health of all system components.
"""

import sys
import json
import argparse
from urllib.request import urlopen, Request
from urllib.error import URLError


def check_service(name, url, timeout=5):
    """Check if a service is healthy."""
    try:
        req = Request(url, headers={"User-Agent": "HealthCheck/1.0"})
        response = urlopen(req, timeout=timeout)
        data = response.read().decode()
        
        # Try to parse JSON
        try:
            result = json.loads(data)
            status = result.get("status", "unknown")
        except json.JSONDecodeError:
            status = "responding"
        
        print(f"✅ {name}: {status} ({url})")
        return True
        
    except URLError as e:
        print(f"❌ {name}: unreachable ({url})")
        print(f"   Error: {e.reason}")
        return False
    except Exception as e:
        print(f"❌ {name}: error ({url})")
        print(f"   Error: {str(e)}")
        return False


def main():
    """Run health checks."""
    parser = argparse.ArgumentParser(description="Check system health")
    parser.add_argument("--mcp-url", default="http://localhost:8000")
    parser.add_argument("--streamlit-url", default="http://localhost:8501")
    parser.add_argument("--n8n-url", default="http://localhost:5678")
    parser.add_argument("--mailhog-url", default="http://localhost:8025")
    parser.add_argument("--all", action="store_true", help="Check all services")
    args = parser.parse_args()
    
    print("\n🏥 Health Check\n" + "="*50 + "\n")
    
    results = []
    
    # Always check MCP server
    results.append(check_service("MCP Server", f"{args.mcp_url}/health"))
    results.append(check_service("MCP API Docs", f"{args.mcp_url}/docs"))
    
    if args.all:
        results.append(check_service("Streamlit", f"{args.streamlit_url}/_stcore/health"))
        results.append(check_service("n8n", f"{args.n8n_url}/healthz"))
        results.append(check_service("Mailhog", f"{args.mailhog_url}/api/v2/messages"))
    
    print("\n" + "="*50)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ All checks passed ({passed}/{total})")
        return 0
    else:
        print(f"⚠️  {passed}/{total} checks passed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
