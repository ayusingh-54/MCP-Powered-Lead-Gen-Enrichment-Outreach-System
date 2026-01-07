#!/usr/bin/env python3
"""
n8n Workflow Importer
=====================
Import workflow JSON into n8n via API.
"""

import sys
import json
import argparse
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError


def import_workflow(n8n_url: str, workflow_path: str, api_key: str = None):
    """Import workflow JSON into n8n."""
    # Read workflow file
    with open(workflow_path) as f:
        workflow = json.load(f)
    
    # Prepare request
    url = f"{n8n_url.rstrip('/')}/api/v1/workflows"
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    if api_key:
        headers["X-N8N-API-KEY"] = api_key
    
    data = json.dumps(workflow).encode("utf-8")
    req = Request(url, data=data, headers=headers, method="POST")
    
    try:
        response = urlopen(req, timeout=30)
        result = json.loads(response.read().decode())
        
        print(f"✅ Workflow imported successfully!")
        print(f"   ID: {result.get('id')}")
        print(f"   Name: {result.get('name')}")
        print(f"   URL: {n8n_url}/workflow/{result.get('id')}")
        
        return True
        
    except HTTPError as e:
        error_body = e.read().decode()
        print(f"❌ Import failed: HTTP {e.code}")
        print(f"   {error_body}")
        return False
        
    except URLError as e:
        print(f"❌ Connection failed: {e.reason}")
        print(f"   Make sure n8n is running at {n8n_url}")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Import workflow into n8n")
    parser.add_argument(
        "workflow",
        help="Path to workflow JSON file"
    )
    parser.add_argument(
        "--n8n-url",
        default="http://localhost:5678",
        help="n8n server URL"
    )
    parser.add_argument(
        "--api-key",
        help="n8n API key (if authentication enabled)"
    )
    
    args = parser.parse_args()
    
    print(f"\n📦 Importing workflow: {args.workflow}")
    print(f"   Target: {args.n8n_url}\n")
    
    success = import_workflow(args.n8n_url, args.workflow, args.api_key)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
