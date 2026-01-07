#!/usr/bin/env python3
"""
Pipeline Runner Script
======================
Command-line interface to run the lead generation pipeline.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.agent.pipeline_agent import PipelineAgent


def print_banner():
    """Print banner."""
    print("""
╔════════════════════════════════════════════════════════════╗
║         🎯 MCP Lead Generation Pipeline Runner             ║
╚════════════════════════════════════════════════════════════╝
    """)


async def run_pipeline(args):
    """Run the pipeline with given arguments."""
    print(f"\n📊 Configuration:")
    print(f"   • Lead Count: {args.count}")
    print(f"   • Enrichment Mode: {args.enrichment_mode}")
    print(f"   • Channels: {args.channels}")
    print(f"   • Send Mode: {args.mode}")
    print(f"   • Rate Limit: {args.rate_limit}/min")
    print(f"   • Seed: {args.seed or 'random'}")
    print()
    
    # Create agent
    agent = PipelineAgent(
        mcp_server_url=args.server,
        dry_run=(args.mode == "dry_run")
    )
    
    # Run pipeline
    print("🚀 Starting pipeline...\n")
    
    try:
        results = await agent.run_pipeline(
            lead_count=args.count,
            enrichment_mode=args.enrichment_mode,
            seed=args.seed
        )
        
        print("\n" + "="*60)
        print("✅ Pipeline completed successfully!")
        print("="*60)
        
        if args.output:
            # Save results to file
            output_path = Path(args.output)
            output_path.write_text(json.dumps(results, indent=2, default=str))
            print(f"\n📁 Results saved to: {output_path}")
        else:
            print("\n📊 Results:")
            print(json.dumps(results, indent=2, default=str))
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Pipeline failed: {str(e)}")
        return 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run the MCP Lead Generation Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with defaults (dry-run mode)
  python run_pipeline.py
  
  # Generate 100 leads and send in live mode
  python run_pipeline.py --count 100 --mode live
  
  # Use AI enrichment with specific seed
  python run_pipeline.py --enrichment-mode ai --seed 42
  
  # Save results to file
  python run_pipeline.py --output results.json
        """
    )
    
    parser.add_argument(
        "--server",
        default="http://localhost:8000",
        help="MCP server URL (default: http://localhost:8000)"
    )
    
    parser.add_argument(
        "--count",
        type=int,
        default=200,
        help="Number of leads to generate (default: 200)"
    )
    
    parser.add_argument(
        "--enrichment-mode",
        choices=["offline", "ai"],
        default="offline",
        help="Enrichment mode (default: offline)"
    )
    
    parser.add_argument(
        "--channels",
        nargs="+",
        choices=["email", "linkedin"],
        default=["email", "linkedin"],
        help="Message channels (default: email linkedin)"
    )
    
    parser.add_argument(
        "--mode",
        choices=["dry_run", "live"],
        default="dry_run",
        help="Send mode (default: dry_run)"
    )
    
    parser.add_argument(
        "--rate-limit",
        type=int,
        default=10,
        help="Messages per minute (default: 10)"
    )
    
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility"
    )
    
    parser.add_argument(
        "--output",
        "-o",
        help="Output file for results (JSON)"
    )
    
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Minimal output"
    )
    
    args = parser.parse_args()
    
    if not args.quiet:
        print_banner()
    
    # Run pipeline
    exit_code = asyncio.run(run_pipeline(args))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
