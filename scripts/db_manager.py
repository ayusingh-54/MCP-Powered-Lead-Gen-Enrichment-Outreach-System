#!/usr/bin/env python3
"""
Database Management Script
==========================
Utilities for managing the SQLite database.
"""

import sys
import argparse
import json
from pathlib import Path
from datetime import datetime

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.storage.database import DatabaseManager


def export_data(db: DatabaseManager, output_path: str, table: str = None):
    """Export database data to JSON."""
    data = {}
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        tables = ["leads", "enrichments", "messages", "outreach_results"]
        if table:
            tables = [table]
        
        for t in tables:
            cursor.execute(f"SELECT * FROM {t}")
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            data[t] = [dict(zip(columns, row)) for row in rows]
    
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2, default=str)
    
    print(f"✅ Exported to {output_path}")
    for t, rows in data.items():
        print(f"   • {t}: {len(rows)} records")


def show_stats(db: DatabaseManager):
    """Show database statistics."""
    print("\n📊 Database Statistics\n" + "="*50)
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        # Lead counts by status
        cursor.execute("""
            SELECT status, COUNT(*) as count 
            FROM leads 
            GROUP BY status
        """)
        status_counts = cursor.fetchall()
        
        print("\nLeads by Status:")
        total = 0
        for status, count in status_counts:
            print(f"   • {status}: {count}")
            total += count
        print(f"   Total: {total}")
        
        # Enrichment stats
        cursor.execute("SELECT COUNT(*) FROM enrichments")
        enrichment_count = cursor.fetchone()[0]
        print(f"\nEnrichments: {enrichment_count}")
        
        # Message stats
        cursor.execute("""
            SELECT channel, COUNT(*) as count 
            FROM messages 
            GROUP BY channel
        """)
        message_counts = cursor.fetchall()
        
        if message_counts:
            print("\nMessages by Channel:")
            for channel, count in message_counts:
                print(f"   • {channel}: {count}")
        
        # Outreach stats
        cursor.execute("""
            SELECT status, COUNT(*) as count 
            FROM outreach_results 
            GROUP BY status
        """)
        outreach_counts = cursor.fetchall()
        
        if outreach_counts:
            print("\nOutreach Results:")
            for status, count in outreach_counts:
                print(f"   • {status}: {count}")


def reset_database(db: DatabaseManager, confirm: bool = False):
    """Reset (clear) the database."""
    if not confirm:
        response = input("⚠️  This will delete ALL data. Are you sure? (yes/no): ")
        if response.lower() != "yes":
            print("Aborted.")
            return
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM outreach_results")
        cursor.execute("DELETE FROM messages")
        cursor.execute("DELETE FROM enrichments")
        cursor.execute("DELETE FROM leads")
        conn.commit()
    
    print("✅ Database reset complete")


def backup_database(db_path: str, backup_path: str = None):
    """Create a backup of the database file."""
    import shutil
    
    source = Path(db_path)
    if not source.exists():
        print(f"❌ Database not found: {db_path}")
        return
    
    if backup_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{db_path}.backup_{timestamp}"
    
    shutil.copy2(source, backup_path)
    print(f"✅ Backup created: {backup_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Database management utilities")
    parser.add_argument(
        "--db-path",
        default="storage/leads.db",
        help="Path to database file"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Stats command
    subparsers.add_parser("stats", help="Show database statistics")
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export data to JSON")
    export_parser.add_argument("output", help="Output file path")
    export_parser.add_argument("--table", help="Specific table to export")
    
    # Reset command
    reset_parser = subparsers.add_parser("reset", help="Reset database")
    reset_parser.add_argument("--yes", action="store_true", help="Skip confirmation")
    
    # Backup command
    backup_parser = subparsers.add_parser("backup", help="Backup database")
    backup_parser.add_argument("--output", help="Backup file path")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    db = DatabaseManager(args.db_path)
    
    if args.command == "stats":
        show_stats(db)
    elif args.command == "export":
        export_data(db, args.output, args.table)
    elif args.command == "reset":
        reset_database(db, args.yes)
    elif args.command == "backup":
        backup_database(args.db_path, args.output)


if __name__ == "__main__":
    main()
