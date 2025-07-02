"""
Analytics Database Interface

SQLite-based database interface for storing and retrieving negotiation analytics data.
Provides high-performance queries for real-time monitoring and historical analysis.
"""

import sqlite3
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from contextlib import contextmanager

from .data_models import (
    NegotiationAnalytics,
    AgentPerformance,
    TacticEffectiveness,
    PersonalityInsights,
    SystemMetrics,
    AnalyticsEvent,
    AnalyticsSummary,
    AnalyticsEventType,
    PerformanceLevel
)


class AnalyticsDatabase:
    """
    High-performance analytics database for negotiation data.
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize analytics database.
        
        Args:
            db_path: Path to SQLite database file. If None, uses default location.
        """
        if db_path is None:
            db_path = Path("analytics.db")
        
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize database schema."""
        with self._get_connection() as conn:
            # Negotiation analytics table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS negotiation_analytics (
                    id TEXT PRIMARY KEY,
                    negotiation_id TEXT NOT NULL,
                    started_at TIMESTAMP NOT NULL,
                    ended_at TIMESTAMP NOT NULL,
                    duration_seconds REAL NOT NULL,
                    agent1_id TEXT NOT NULL,
                    agent2_id TEXT NOT NULL,
                    agent1_personality TEXT NOT NULL,
                    agent2_personality TEXT NOT NULL,
                    agent1_tactics TEXT NOT NULL,
                    agent2_tactics TEXT NOT NULL,
                    agreement_reached BOOLEAN NOT NULL,
                    total_turns INTEGER NOT NULL,
                    total_rounds INTEGER NOT NULL,
                    success_score REAL NOT NULL,
                    efficiency_score REAL NOT NULL,
                    agreement_quality REAL,
                    mutual_satisfaction REAL,
                    zopa_utilization TEXT NOT NULL,
                    zopa_violations INTEGER DEFAULT 0,
                    final_agreement TEXT,
                    product_category TEXT NOT NULL,
                    market_condition TEXT NOT NULL,
                    baseline_values TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Agent performance table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_performance (
                    id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    period_start TIMESTAMP NOT NULL,
                    period_end TIMESTAMP NOT NULL,
                    total_negotiations INTEGER NOT NULL,
                    successful_negotiations INTEGER NOT NULL,
                    success_rate REAL NOT NULL,
                    average_turns REAL NOT NULL,
                    average_duration REAL NOT NULL,
                    average_agreement_quality REAL NOT NULL,
                    personality_profile TEXT NOT NULL,
                    personality_effectiveness TEXT NOT NULL,
                    tactics_used TEXT NOT NULL,
                    tactic_success_rates TEXT NOT NULL,
                    adaptability_score REAL NOT NULL,
                    consistency_score REAL NOT NULL,
                    learning_trend REAL NOT NULL,
                    zopa_compliance_rate REAL NOT NULL,
                    average_zopa_utilization REAL NOT NULL,
                    performance_level TEXT NOT NULL,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tactic effectiveness table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tactic_effectiveness (
                    id TEXT PRIMARY KEY,
                    tactic_id TEXT NOT NULL,
                    tactic_name TEXT NOT NULL,
                    period_start TIMESTAMP NOT NULL,
                    period_end TIMESTAMP NOT NULL,
                    times_used INTEGER NOT NULL,
                    successful_uses INTEGER NOT NULL,
                    success_rate REAL NOT NULL,
                    effectiveness_by_personality TEXT NOT NULL,
                    effectiveness_by_market TEXT NOT NULL,
                    effectiveness_by_product TEXT NOT NULL,
                    average_agreement_quality REAL NOT NULL,
                    average_negotiation_duration REAL NOT NULL,
                    risk_score REAL NOT NULL,
                    effective_combinations TEXT NOT NULL,
                    conflicting_tactics TEXT NOT NULL,
                    recommended_contexts TEXT NOT NULL,
                    optimization_suggestions TEXT NOT NULL,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Personality insights table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS personality_insights (
                    id TEXT PRIMARY KEY,
                    period_start TIMESTAMP NOT NULL,
                    period_end TIMESTAMP NOT NULL,
                    sample_size INTEGER NOT NULL,
                    trait_effectiveness TEXT NOT NULL,
                    optimal_trait_ranges TEXT NOT NULL,
                    successful_combinations TEXT NOT NULL,
                    problematic_combinations TEXT NOT NULL,
                    trait_effectiveness_by_role TEXT NOT NULL,
                    trait_effectiveness_by_market TEXT NOT NULL,
                    complementary_personalities TEXT NOT NULL,
                    conflicting_personalities TEXT NOT NULL,
                    personality_recommendations TEXT NOT NULL,
                    optimization_opportunities TEXT NOT NULL,
                    confidence_level REAL NOT NULL,
                    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # System metrics table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id TEXT PRIMARY KEY,
                    period_start TIMESTAMP NOT NULL,
                    period_end TIMESTAMP NOT NULL,
                    total_negotiations INTEGER NOT NULL,
                    successful_negotiations INTEGER NOT NULL,
                    failed_negotiations INTEGER NOT NULL,
                    negotiations_per_hour REAL NOT NULL,
                    average_response_time REAL NOT NULL,
                    average_negotiation_duration REAL NOT NULL,
                    api_call_efficiency REAL NOT NULL,
                    cpu_usage_avg REAL NOT NULL,
                    memory_usage_avg REAL NOT NULL,
                    storage_usage REAL NOT NULL,
                    error_rate REAL NOT NULL,
                    timeout_rate REAL NOT NULL,
                    api_error_rate REAL NOT NULL,
                    average_agreement_quality REAL NOT NULL,
                    user_satisfaction_score REAL NOT NULL,
                    critical_alerts INTEGER DEFAULT 0,
                    performance_warnings INTEGER DEFAULT 0,
                    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Analytics events table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS analytics_events (
                    id TEXT PRIMARY KEY,
                    negotiation_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    turn_number INTEGER,
                    round_number INTEGER,
                    agent_id TEXT,
                    event_data TEXT NOT NULL,
                    performance_impact REAL,
                    source TEXT DEFAULT 'system'
                )
            """)
            
            # Analytics summaries table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS analytics_summaries (
                    id TEXT PRIMARY KEY,
                    period_start TIMESTAMP NOT NULL,
                    period_end TIMESTAMP NOT NULL,
                    total_negotiations INTEGER NOT NULL,
                    success_rate REAL NOT NULL,
                    average_quality REAL NOT NULL,
                    average_duration REAL NOT NULL,
                    top_personalities TEXT NOT NULL,
                    top_tactics TEXT NOT NULL,
                    success_trend REAL NOT NULL,
                    quality_trend REAL NOT NULL,
                    efficiency_trend REAL NOT NULL,
                    key_insights TEXT NOT NULL,
                    recommendations TEXT NOT NULL,
                    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_negotiation_analytics_date ON negotiation_analytics(created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_negotiation_analytics_agent ON negotiation_analytics(agent1_id, agent2_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_agent_performance_agent ON agent_performance(agent_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tactic_effectiveness_tactic ON tactic_effectiveness(tactic_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_analytics_events_negotiation ON analytics_events(negotiation_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_analytics_events_type ON analytics_events(event_type)")
            
            conn.commit()
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with proper cleanup."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def _serialize_json(self, data: Any) -> str:
        """Serialize data to JSON string."""
        return json.dumps(data, default=str)
    
    def _deserialize_json(self, data: str) -> Any:
        """Deserialize JSON string to data."""
        return json.loads(data)
    
    # Negotiation Analytics Methods
    
    def save_negotiation_analytics(self, analytics: NegotiationAnalytics) -> bool:
        """Save negotiation analytics to database."""
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO negotiation_analytics (
                        id, negotiation_id, started_at, ended_at, duration_seconds,
                        agent1_id, agent2_id, agent1_personality, agent2_personality,
                        agent1_tactics, agent2_tactics, agreement_reached, total_turns,
                        total_rounds, success_score, efficiency_score, agreement_quality,
                        mutual_satisfaction, zopa_utilization, zopa_violations,
                        final_agreement, product_category, market_condition,
                        baseline_values, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    analytics.id, analytics.negotiation_id, analytics.started_at,
                    analytics.ended_at, analytics.duration_seconds, analytics.agent1_id,
                    analytics.agent2_id, self._serialize_json(analytics.agent1_personality),
                    self._serialize_json(analytics.agent2_personality),
                    self._serialize_json(analytics.agent1_tactics),
                    self._serialize_json(analytics.agent2_tactics),
                    analytics.agreement_reached, analytics.total_turns,
                    analytics.total_rounds, analytics.success_score,
                    analytics.efficiency_score, analytics.agreement_quality,
                    analytics.mutual_satisfaction, self._serialize_json(analytics.zopa_utilization),
                    analytics.zopa_violations, self._serialize_json(analytics.final_agreement),
                    analytics.product_category, analytics.market_condition,
                    self._serialize_json(analytics.baseline_values), analytics.created_at
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error saving negotiation analytics: {e}")
            return False
    
    def get_negotiation_analytics(self, negotiation_id: str) -> Optional[NegotiationAnalytics]:
        """Get negotiation analytics by negotiation ID."""
        try:
            with self._get_connection() as conn:
                row = conn.execute(
                    "SELECT * FROM negotiation_analytics WHERE negotiation_id = ?",
                    (negotiation_id,)
                ).fetchone()
                
                if row:
                    return NegotiationAnalytics(
                        id=row['id'],
                        negotiation_id=row['negotiation_id'],
                        started_at=datetime.fromisoformat(row['started_at']),
                        ended_at=datetime.fromisoformat(row['ended_at']),
                        duration_seconds=row['duration_seconds'],
                        agent1_id=row['agent1_id'],
                        agent2_id=row['agent2_id'],
                        agent1_personality=self._deserialize_json(row['agent1_personality']),
                        agent2_personality=self._deserialize_json(row['agent2_personality']),
                        agent1_tactics=self._deserialize_json(row['agent1_tactics']),
                        agent2_tactics=self._deserialize_json(row['agent2_tactics']),
                        agreement_reached=bool(row['agreement_reached']),
                        total_turns=row['total_turns'],
                        total_rounds=row['total_rounds'],
                        success_score=row['success_score'],
                        efficiency_score=row['efficiency_score'],
                        agreement_quality=row['agreement_quality'],
                        mutual_satisfaction=row['mutual_satisfaction'],
                        zopa_utilization=self._deserialize_json(row['zopa_utilization']),
                        zopa_violations=row['zopa_violations'],
                        final_agreement=self._deserialize_json(row['final_agreement']) if row['final_agreement'] else None,
                        product_category=row['product_category'],
                        market_condition=row['market_condition'],
                        baseline_values=self._deserialize_json(row['baseline_values']),
                        created_at=datetime.fromisoformat(row['created_at'])
                    )
                return None
        except Exception as e:
            print(f"Error getting negotiation analytics: {e}")
            return None
    
    def get_recent_negotiations(self, limit: int = 50) -> List[NegotiationAnalytics]:
        """Get recent negotiation analytics."""
        try:
            with self._get_connection() as conn:
                rows = conn.execute(
                    "SELECT * FROM negotiation_analytics ORDER BY created_at DESC LIMIT ?",
                    (limit,)
                ).fetchall()
                
                return [self._row_to_negotiation_analytics(row) for row in rows]
        except Exception as e:
            print(f"Error getting recent negotiations: {e}")
            return []
    
    def _row_to_negotiation_analytics(self, row) -> NegotiationAnalytics:
        """Convert database row to NegotiationAnalytics object."""
        return NegotiationAnalytics(
            id=row['id'],
            negotiation_id=row['negotiation_id'],
            started_at=datetime.fromisoformat(row['started_at']),
            ended_at=datetime.fromisoformat(row['ended_at']),
            duration_seconds=row['duration_seconds'],
            agent1_id=row['agent1_id'],
            agent2_id=row['agent2_id'],
            agent1_personality=self._deserialize_json(row['agent1_personality']),
            agent2_personality=self._deserialize_json(row['agent2_personality']),
            agent1_tactics=self._deserialize_json(row['agent1_tactics']),
            agent2_tactics=self._deserialize_json(row['agent2_tactics']),
            agreement_reached=bool(row['agreement_reached']),
            total_turns=row['total_turns'],
            total_rounds=row['total_rounds'],
            success_score=row['success_score'],
            efficiency_score=row['efficiency_score'],
            agreement_quality=row['agreement_quality'],
            mutual_satisfaction=row['mutual_satisfaction'],
            zopa_utilization=self._deserialize_json(row['zopa_utilization']),
            zopa_violations=row['zopa_violations'],
            final_agreement=self._deserialize_json(row['final_agreement']) if row['final_agreement'] else None,
            product_category=row['product_category'],
            market_condition=row['market_condition'],
            baseline_values=self._deserialize_json(row['baseline_values']),
            created_at=datetime.fromisoformat(row['created_at'])
        )
    
    # Analytics Events Methods
    
    def save_analytics_event(self, event: AnalyticsEvent) -> bool:
        """Save analytics event to database."""
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT INTO analytics_events (
                        id, negotiation_id, event_type, timestamp, turn_number,
                        round_number, agent_id, event_data, performance_impact, source
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event.id, event.negotiation_id, event.event_type.value,
                    event.timestamp, event.turn_number, event.round_number,
                    event.agent_id, self._serialize_json(event.event_data),
                    event.performance_impact, event.source
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error saving analytics event: {e}")
            return False
    
    def get_negotiation_events(self, negotiation_id: str) -> List[AnalyticsEvent]:
        """Get all events for a specific negotiation."""
        try:
            with self._get_connection() as conn:
                rows = conn.execute(
                    "SELECT * FROM analytics_events WHERE negotiation_id = ? ORDER BY timestamp",
                    (negotiation_id,)
                ).fetchall()
                
                events = []
                for row in rows:
                    events.append(AnalyticsEvent(
                        id=row['id'],
                        negotiation_id=row['negotiation_id'],
                        event_type=AnalyticsEventType(row['event_type']),
                        timestamp=datetime.fromisoformat(row['timestamp']),
                        turn_number=row['turn_number'],
                        round_number=row['round_number'],
                        agent_id=row['agent_id'],
                        event_data=self._deserialize_json(row['event_data']),
                        performance_impact=row['performance_impact'],
                        source=row['source']
                    ))
                return events
        except Exception as e:
            print(f"Error getting negotiation events: {e}")
            return []
    
    # Query Methods
    
    def get_success_rate_by_period(self, days: int = 30) -> float:
        """Get success rate for the last N days."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            with self._get_connection() as conn:
                row = conn.execute("""
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN agreement_reached = 1 THEN 1 ELSE 0 END) as successful
                    FROM negotiation_analytics 
                    WHERE created_at >= ?
                """, (cutoff_date,)).fetchone()
                
                if row['total'] > 0:
                    return row['successful'] / row['total']
                return 0.0
        except Exception as e:
            print(f"Error calculating success rate: {e}")
            return 0.0
    
    def get_average_quality_by_period(self, days: int = 30) -> float:
        """Get average agreement quality for the last N days."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            with self._get_connection() as conn:
                row = conn.execute("""
                    SELECT AVG(agreement_quality) as avg_quality
                    FROM negotiation_analytics 
                    WHERE created_at >= ? AND agreement_quality IS NOT NULL
                """, (cutoff_date,)).fetchone()
                
                return row['avg_quality'] or 0.0
        except Exception as e:
            print(f"Error calculating average quality: {e}")
            return 0.0
    
    def get_top_performing_tactics(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top performing tactics by success rate."""
        try:
            with self._get_connection() as conn:
                # This is a simplified query - in practice, you'd want more sophisticated analysis
                rows = conn.execute("""
                    SELECT 
                        tactic_id,
                        tactic_name,
                        success_rate,
                        times_used
                    FROM tactic_effectiveness 
                    ORDER BY success_rate DESC, times_used DESC
                    LIMIT ?
                """, (limit,)).fetchall()
                
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error getting top tactics: {e}")
            return []
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        try:
            with self._get_connection() as conn:
                stats = {}
                
                # Count records in each table
                tables = [
                    'negotiation_analytics',
                    'agent_performance', 
                    'tactic_effectiveness',
                    'personality_insights',
                    'system_metrics',
                    'analytics_events',
                    'analytics_summaries'
                ]
                
                for table in tables:
                    row = conn.execute(f"SELECT COUNT(*) as count FROM {table}").fetchone()
                    stats[f"{table}_count"] = row['count']
                
                # Database size
                stats['database_size_mb'] = self.db_path.stat().st_size / (1024 * 1024) if self.db_path.exists() else 0
                
                return stats
        except Exception as e:
            print(f"Error getting database stats: {e}")
            return {}
    
    def cleanup_old_data(self, days_to_keep: int = 90) -> bool:
        """Clean up old analytics data."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            with self._get_connection() as conn:
                # Clean up old events (keep more recent data for other tables)
                conn.execute(
                    "DELETE FROM analytics_events WHERE timestamp < ?",
                    (cutoff_date,)
                )
                
                # Clean up old summaries
                conn.execute(
                    "DELETE FROM analytics_summaries WHERE generated_at < ?",
                    (cutoff_date,)
                )
                
                conn.commit()
                return True
        except Exception as e:
            print(f"Error cleaning up old data: {e}")
            return False
