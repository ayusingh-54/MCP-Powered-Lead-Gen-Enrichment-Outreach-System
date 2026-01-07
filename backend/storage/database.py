"""
SQLite Database Manager
=======================
Handles all database operations for the lead generation system:
- Schema creation and migrations
- CRUD operations for leads, enrichments, messages
- Pipeline state management
- Metrics aggregation
"""

import sqlite3
import json
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from contextlib import contextmanager
from pathlib import Path

# Import models
import sys
sys.path.append(str(Path(__file__).parent.parent))
from mcp_server.models import (
    Lead, LeadEnrichment, GeneratedMessage, OutreachResult,
    LeadStatus, PipelineMetrics, CompanySize, EnrichmentMode
)


class DatabaseManager:
    """
    SQLite database manager for lead generation pipeline.
    Provides thread-safe database operations with connection pooling.
    """
    
    def __init__(self, db_path: str = "storage/leads.db"):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        # Ensure storage directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections.
        Ensures proper connection handling and cleanup.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like row access
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _init_database(self):
        """
        Initialize database schema.
        Creates all required tables if they don't exist.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Leads table - core lead information
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS leads (
                    id TEXT PRIMARY KEY,
                    full_name TEXT NOT NULL,
                    company_name TEXT NOT NULL,
                    role TEXT NOT NULL,
                    industry TEXT NOT NULL,
                    website TEXT NOT NULL,
                    email TEXT NOT NULL,
                    linkedin_url TEXT NOT NULL,
                    country TEXT NOT NULL,
                    status TEXT DEFAULT 'NEW',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Enrichments table - enrichment data for leads
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS enrichments (
                    id TEXT PRIMARY KEY,
                    lead_id TEXT NOT NULL UNIQUE,
                    company_size TEXT NOT NULL,
                    persona TEXT NOT NULL,
                    pain_points TEXT NOT NULL,
                    buying_triggers TEXT NOT NULL,
                    confidence_score INTEGER NOT NULL,
                    enrichment_mode TEXT NOT NULL,
                    enriched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (lead_id) REFERENCES leads(id)
                )
            """)
            
            # Messages table - generated outreach messages
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    lead_id TEXT NOT NULL,
                    channel TEXT NOT NULL,
                    variant TEXT NOT NULL,
                    subject TEXT,
                    body TEXT NOT NULL,
                    word_count INTEGER NOT NULL,
                    cta TEXT NOT NULL,
                    referenced_insight TEXT NOT NULL,
                    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (lead_id) REFERENCES leads(id)
                )
            """)
            
            # Outreach results table - send attempt tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS outreach_results (
                    id TEXT PRIMARY KEY,
                    message_id TEXT NOT NULL,
                    lead_id TEXT NOT NULL,
                    channel TEXT NOT NULL,
                    status TEXT NOT NULL,
                    attempt_count INTEGER DEFAULT 1,
                    error_message TEXT,
                    sent_at TIMESTAMP,
                    FOREIGN KEY (message_id) REFERENCES messages(id),
                    FOREIGN KEY (lead_id) REFERENCES leads(id)
                )
            """)
            
            # Pipeline runs table - track pipeline executions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pipeline_runs (
                    id TEXT PRIMARY KEY,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    status TEXT DEFAULT 'running',
                    mode TEXT NOT NULL,
                    leads_processed INTEGER DEFAULT 0,
                    messages_sent INTEGER DEFAULT 0,
                    errors TEXT
                )
            """)
            
            # Create indexes for common queries
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_lead_id ON messages(lead_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_enrichments_lead_id ON enrichments(lead_id)")
    
    # =========================================================================
    # LEAD OPERATIONS
    # =========================================================================
    
    def insert_leads(self, leads: List[Lead]) -> int:
        """
        Bulk insert leads into database.
        
        Args:
            leads: List of Lead objects to insert
            
        Returns:
            Number of leads inserted
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            inserted = 0
            
            for lead in leads:
                lead_id = lead.id or str(uuid.uuid4())
                now = datetime.utcnow().isoformat()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO leads 
                    (id, full_name, company_name, role, industry, website, 
                     email, linkedin_url, country, status, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    lead_id, lead.full_name, lead.company_name, lead.role,
                    lead.industry, lead.website, lead.email, lead.linkedin_url,
                    lead.country, lead.status, now, now
                ))
                inserted += 1
            
            return inserted
    
    def get_leads_by_status(self, status: LeadStatus, limit: int = 100) -> List[Dict]:
        """
        Get leads filtered by status.
        
        Args:
            status: Pipeline status to filter by
            limit: Maximum number of leads to return
            
        Returns:
            List of lead dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM leads WHERE status = ? LIMIT ?
            """, (status.value, limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_leads_by_ids(self, lead_ids: List[str]) -> List[Dict]:
        """
        Get specific leads by their IDs.
        
        Args:
            lead_ids: List of lead IDs to retrieve
            
        Returns:
            List of lead dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            placeholders = ",".join("?" * len(lead_ids))
            cursor.execute(f"""
                SELECT * FROM leads WHERE id IN ({placeholders})
            """, lead_ids)
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_all_leads(self, limit: int = 1000) -> List[Dict]:
        """
        Get all leads with optional limit.
        
        Args:
            limit: Maximum number of leads to return
            
        Returns:
            List of lead dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM leads ORDER BY created_at DESC LIMIT ?", (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    def update_lead_status(self, lead_id: str, status: LeadStatus) -> bool:
        """
        Update the status of a lead.
        
        Args:
            lead_id: ID of the lead to update
            status: New status to set
            
        Returns:
            True if update was successful
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE leads 
                SET status = ?, updated_at = ?
                WHERE id = ?
            """, (status.value, datetime.utcnow().isoformat(), lead_id))
            
            return cursor.rowcount > 0
    
    def bulk_update_lead_status(self, lead_ids: List[str], status: LeadStatus) -> int:
        """
        Bulk update status for multiple leads.
        
        Args:
            lead_ids: List of lead IDs to update
            status: New status to set
            
        Returns:
            Number of leads updated
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.utcnow().isoformat()
            updated = 0
            
            for lead_id in lead_ids:
                cursor.execute("""
                    UPDATE leads SET status = ?, updated_at = ? WHERE id = ?
                """, (status.value, now, lead_id))
                updated += cursor.rowcount
            
            return updated
    
    # =========================================================================
    # ENRICHMENT OPERATIONS
    # =========================================================================
    
    def insert_enrichment(self, enrichment: LeadEnrichment) -> str:
        """
        Insert enrichment data for a lead.
        
        Args:
            enrichment: LeadEnrichment object to insert
            
        Returns:
            ID of the inserted enrichment
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            enrichment_id = str(uuid.uuid4())
            
            cursor.execute("""
                INSERT OR REPLACE INTO enrichments
                (id, lead_id, company_size, persona, pain_points, buying_triggers,
                 confidence_score, enrichment_mode, enriched_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                enrichment_id,
                enrichment.lead_id,
                enrichment.company_size,
                enrichment.persona,
                json.dumps(enrichment.pain_points),
                json.dumps(enrichment.buying_triggers),
                enrichment.confidence_score,
                enrichment.enrichment_mode,
                datetime.utcnow().isoformat()
            ))
            
            return enrichment_id
    
    def get_enrichment_by_lead_id(self, lead_id: str) -> Optional[Dict]:
        """
        Get enrichment data for a specific lead.
        
        Args:
            lead_id: ID of the lead
            
        Returns:
            Enrichment dictionary or None
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM enrichments WHERE lead_id = ?
            """, (lead_id,))
            
            row = cursor.fetchone()
            if row:
                enrichment = dict(row)
                # Parse JSON fields
                enrichment["pain_points"] = json.loads(enrichment["pain_points"])
                enrichment["buying_triggers"] = json.loads(enrichment["buying_triggers"])
                return enrichment
            return None
    
    def get_leads_with_enrichment(self, status: Optional[LeadStatus] = None, limit: int = 100) -> List[Dict]:
        """
        Get leads joined with their enrichment data.
        
        Args:
            status: Optional status filter
            limit: Maximum number of results
            
        Returns:
            List of lead+enrichment dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT l.*, e.company_size, e.persona, e.pain_points, 
                       e.buying_triggers, e.confidence_score, e.enrichment_mode
                FROM leads l
                LEFT JOIN enrichments e ON l.id = e.lead_id
            """
            
            params = []
            if status:
                query += " WHERE l.status = ?"
                params.append(status.value)
            
            query += " ORDER BY l.created_at DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            
            results = []
            for row in cursor.fetchall():
                lead = dict(row)
                if lead.get("pain_points"):
                    lead["pain_points"] = json.loads(lead["pain_points"])
                if lead.get("buying_triggers"):
                    lead["buying_triggers"] = json.loads(lead["buying_triggers"])
                results.append(lead)
            
            return results
    
    # =========================================================================
    # MESSAGE OPERATIONS
    # =========================================================================
    
    def insert_message(self, message: GeneratedMessage) -> str:
        """
        Insert a generated message.
        
        Args:
            message: GeneratedMessage object to insert
            
        Returns:
            ID of the inserted message
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            message_id = message.id or str(uuid.uuid4())
            
            cursor.execute("""
                INSERT INTO messages
                (id, lead_id, channel, variant, subject, body, word_count, 
                 cta, referenced_insight, generated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                message_id, message.lead_id, message.channel, message.variant,
                message.subject, message.body, message.word_count, message.cta,
                message.referenced_insight, datetime.utcnow().isoformat()
            ))
            
            return message_id
    
    def get_messages_by_lead_id(self, lead_id: str) -> List[Dict]:
        """
        Get all messages for a specific lead.
        
        Args:
            lead_id: ID of the lead
            
        Returns:
            List of message dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM messages WHERE lead_id = ?
            """, (lead_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_messages_by_status(self, lead_status: LeadStatus, channel: Optional[str] = None, 
                                variant: str = "A", limit: int = 100) -> List[Dict]:
        """
        Get messages for leads with specific status.
        
        Args:
            lead_status: Status of leads to filter
            channel: Optional channel filter
            variant: Message variant (A or B)
            limit: Maximum number of results
            
        Returns:
            List of message dictionaries with lead info
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT m.*, l.full_name, l.email, l.linkedin_url
                FROM messages m
                JOIN leads l ON m.lead_id = l.id
                WHERE l.status = ? AND m.variant = ?
            """
            params = [lead_status.value, variant]
            
            if channel:
                query += " AND m.channel = ?"
                params.append(channel)
            
            query += " LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    # =========================================================================
    # OUTREACH RESULT OPERATIONS
    # =========================================================================
    
    def insert_outreach_result(self, result: OutreachResult) -> str:
        """
        Insert an outreach result.
        
        Args:
            result: OutreachResult object to insert
            
        Returns:
            ID of the inserted result
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            result_id = str(uuid.uuid4())
            
            cursor.execute("""
                INSERT INTO outreach_results
                (id, message_id, lead_id, channel, status, attempt_count, 
                 error_message, sent_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result_id, result.message_id, result.lead_id, result.channel,
                result.status, result.attempt_count, result.error_message,
                result.sent_at.isoformat() if result.sent_at else None
            ))
            
            return result_id
    
    def update_outreach_result(self, message_id: str, status: str, 
                                attempt_count: int, error_message: Optional[str] = None):
        """
        Update an existing outreach result.
        
        Args:
            message_id: ID of the message
            status: New status
            attempt_count: Updated attempt count
            error_message: Optional error message
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE outreach_results
                SET status = ?, attempt_count = ?, error_message = ?, 
                    sent_at = CASE WHEN ? = 'sent' THEN CURRENT_TIMESTAMP ELSE sent_at END
                WHERE message_id = ?
            """, (status, attempt_count, error_message, status, message_id))
    
    # =========================================================================
    # METRICS OPERATIONS
    # =========================================================================
    
    def get_pipeline_metrics(self) -> PipelineMetrics:
        """
        Calculate current pipeline metrics.
        
        Returns:
            PipelineMetrics object with aggregated data
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get lead counts by status
            cursor.execute("""
                SELECT status, COUNT(*) as count 
                FROM leads 
                GROUP BY status
            """)
            status_counts = {row["status"]: row["count"] for row in cursor.fetchall()}
            
            # Get total leads
            cursor.execute("SELECT COUNT(*) as total FROM leads")
            total_leads = cursor.fetchone()["total"]
            
            # Get message counts
            cursor.execute("SELECT COUNT(*) as total FROM messages")
            total_messages = cursor.fetchone()["total"]
            
            # Get outreach results
            cursor.execute("""
                SELECT status, COUNT(*) as count 
                FROM outreach_results 
                GROUP BY status
            """)
            outreach_counts = {row["status"]: row["count"] for row in cursor.fetchall()}
            
            return PipelineMetrics(
                total_leads=total_leads,
                new_leads=status_counts.get("NEW", 0),
                enriched_leads=status_counts.get("ENRICHED", 0),
                messaged_leads=status_counts.get("MESSAGED", 0),
                sent_leads=status_counts.get("SENT", 0),
                failed_leads=status_counts.get("FAILED", 0),
                total_messages=total_messages,
                messages_sent=outreach_counts.get("sent", 0),
                messages_failed=outreach_counts.get("failed", 0),
                last_updated=datetime.utcnow()
            )
    
    def clear_all_data(self):
        """
        Clear all data from the database.
        Use with caution - primarily for testing.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM outreach_results")
            cursor.execute("DELETE FROM messages")
            cursor.execute("DELETE FROM enrichments")
            cursor.execute("DELETE FROM leads")
            cursor.execute("DELETE FROM pipeline_runs")


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_database_manager(db_path: str = "storage/leads.db") -> DatabaseManager:
    """
    Get or create the global database manager instance.
    
    Args:
        db_path: Path to SQLite database file
        
    Returns:
        DatabaseManager instance
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(db_path)
    return _db_manager
