"""
Analytics service for tracking and analyzing prompt usage
"""

import sqlite3
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict, Counter

from models.analytics import (
    AnalyticsEvent, EventType, PromptStats, UsageStats, 
    TimeRangeStats, TrendData
)


class AnalyticsService:
    """Service for collecting and analyzing prompt usage data"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.session_id = str(uuid.uuid4())
        self._init_analytics_tables()
    
    def _init_analytics_tables(self):
        """Initialize analytics tables in the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Analytics events table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analytics_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    prompt_id INTEGER,
                    timestamp TEXT NOT NULL,
                    metadata TEXT,
                    session_id TEXT,
                    FOREIGN KEY (prompt_id) REFERENCES prompts (id)
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_analytics_timestamp 
                ON analytics_events(timestamp)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_analytics_event_type 
                ON analytics_events(event_type)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_analytics_prompt_id 
                ON analytics_events(prompt_id)
            ''')
            
            conn.commit()
    
    def track_event(self, event_type: EventType, prompt_id: Optional[int] = None, 
                   metadata: Optional[Dict[str, Any]] = None):
        """Track an analytics event"""
        try:
            event = AnalyticsEvent(
                event_type=event_type.value,
                prompt_id=prompt_id,
                timestamp=datetime.now(),
                metadata=metadata or {},
                session_id=self.session_id
            )
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO analytics_events 
                    (event_type, prompt_id, timestamp, metadata, session_id)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    event.event_type,
                    event.prompt_id,
                    event.timestamp.isoformat(),
                    json.dumps(event.metadata),
                    event.session_id
                ))
                conn.commit()
                
        except Exception as e:
            print(f"Error tracking analytics event: {e}")
    
    def get_prompt_stats(self, prompt_id: int) -> Optional[PromptStats]:
        """Get statistics for a specific prompt"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get prompt basic info
                cursor.execute('''
                    SELECT title, content, created_at, is_favorite 
                    FROM prompts WHERE id = ?
                ''', (prompt_id,))
                
                prompt_data = cursor.fetchone()
                if not prompt_data:
                    return None
                
                title, content, created_at, is_favorite = prompt_data
                
                # Get event counts
                cursor.execute('''
                    SELECT event_type, COUNT(*) 
                    FROM analytics_events 
                    WHERE prompt_id = ? 
                    GROUP BY event_type
                ''', (prompt_id,))
                
                event_counts = dict(cursor.fetchall())
                
                # Get last accessed time
                cursor.execute('''
                    SELECT MAX(timestamp) 
                    FROM analytics_events 
                    WHERE prompt_id = ?
                ''', (prompt_id,))
                
                last_accessed_str = cursor.fetchone()[0]
                last_accessed = None
                if last_accessed_str:
                    last_accessed = datetime.fromisoformat(last_accessed_str)
                
                # Get tag count
                cursor.execute('''
                    SELECT COUNT(*) 
                    FROM prompt_tags 
                    WHERE prompt_id = ?
                ''', (prompt_id,))
                
                tag_count = cursor.fetchone()[0]
                
                # Calculate content stats
                word_count = len(content.split()) if content else 0
                character_count = len(content) if content else 0
                
                return PromptStats(
                    prompt_id=prompt_id,
                    title=title,
                    view_count=event_counts.get(EventType.PROMPT_VIEWED.value, 0),
                    copy_count=event_counts.get(EventType.PROMPT_COPIED.value, 0),
                    edit_count=event_counts.get(EventType.PROMPT_EDITED.value, 0),
                    llm_usage_count=sum([
                        event_counts.get(EventType.LLM_REWRITE.value, 0),
                        event_counts.get(EventType.LLM_EXPLAIN.value, 0),
                        event_counts.get(EventType.LLM_IMPROVE.value, 0),
                        event_counts.get(EventType.LLM_GENERATE_TAGS.value, 0)
                    ]),
                    last_accessed=last_accessed,
                    created_date=datetime.fromisoformat(created_at) if created_at else None,
                    is_favorite=bool(is_favorite),
                    tag_count=tag_count,
                    character_count=character_count,
                    word_count=word_count
                )
                
        except Exception as e:
            print(f"Error getting prompt stats: {e}")
            return None
    
    def get_usage_stats(self, days: int = 30) -> UsageStats:
        """Get overall usage statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get total prompts
                cursor.execute('SELECT COUNT(*) FROM prompts')
                total_prompts = cursor.fetchone()[0]
                
                # Get date range
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)
                
                # Get total events in date range
                cursor.execute('''
                    SELECT COUNT(*) FROM analytics_events 
                    WHERE timestamp >= ?
                ''', (start_date.isoformat(),))
                
                total_events = cursor.fetchone()[0]
                
                # Get event type counts
                cursor.execute('''
                    SELECT event_type, COUNT(*) 
                    FROM analytics_events 
                    WHERE timestamp >= ?
                    GROUP BY event_type
                ''', (start_date.isoformat(),))
                
                event_counts = dict(cursor.fetchall())
                
                # Get most used prompts
                cursor.execute('''
                    SELECT prompt_id, COUNT(*) as usage_count
                    FROM analytics_events 
                    WHERE prompt_id IS NOT NULL AND timestamp >= ?
                    GROUP BY prompt_id 
                    ORDER BY usage_count DESC 
                    LIMIT 10
                ''', (start_date.isoformat(),))
                
                most_used_data = cursor.fetchall()
                most_used_prompts = []
                
                for prompt_id, usage_count in most_used_data:
                    stats = self.get_prompt_stats(prompt_id)
                    if stats:
                        most_used_prompts.append(stats)
                
                # Get recent activity
                cursor.execute('''
                    SELECT event_type, prompt_id, timestamp, metadata
                    FROM analytics_events 
                    ORDER BY timestamp DESC 
                    LIMIT 20
                ''', )
                
                recent_events = []
                for event_type, prompt_id, timestamp_str, metadata_str in cursor.fetchall():
                    metadata = json.loads(metadata_str) if metadata_str else {}
                    recent_events.append(AnalyticsEvent(
                        event_type=event_type,
                        prompt_id=prompt_id,
                        timestamp=datetime.fromisoformat(timestamp_str),
                        metadata=metadata
                    ))
                
                # Get daily activity
                cursor.execute('''
                    SELECT DATE(timestamp) as date, COUNT(*) 
                    FROM analytics_events 
                    WHERE timestamp >= ?
                    GROUP BY DATE(timestamp)
                    ORDER BY date
                ''', (start_date.isoformat(),))
                
                daily_activity = dict(cursor.fetchall())
                
                # Get tag usage
                cursor.execute('''
                    SELECT t.name, COUNT(pt.prompt_id) as usage_count
                    FROM tags t
                    JOIN prompt_tags pt ON t.id = pt.tag_id
                    JOIN prompts p ON pt.prompt_id = p.id
                    GROUP BY t.id, t.name
                    ORDER BY usage_count DESC
                    LIMIT 20
                ''')
                
                tag_usage = dict(cursor.fetchall())
                
                return UsageStats(
                    total_prompts=total_prompts,
                    total_events=total_events,
                    total_views=event_counts.get(EventType.PROMPT_VIEWED.value, 0),
                    total_copies=event_counts.get(EventType.PROMPT_COPIED.value, 0),
                    total_llm_operations=sum([
                        event_counts.get(EventType.LLM_REWRITE.value, 0),
                        event_counts.get(EventType.LLM_EXPLAIN.value, 0),
                        event_counts.get(EventType.LLM_IMPROVE.value, 0),
                        event_counts.get(EventType.LLM_GENERATE_TAGS.value, 0)
                    ]),
                    most_used_prompts=most_used_prompts,
                    recent_activity=recent_events,
                    daily_activity=daily_activity,
                    tag_usage=tag_usage
                )
                
        except Exception as e:
            print(f"Error getting usage stats: {e}")
            return UsageStats()
    
    def get_trend_data(self, event_type: Optional[EventType] = None, 
                      days: int = 30) -> TrendData:
        """Get trend data for charts"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)
                
                # Build query based on event type filter
                if event_type:
                    cursor.execute('''
                        SELECT DATE(timestamp) as date, COUNT(*) 
                        FROM analytics_events 
                        WHERE timestamp >= ? AND event_type = ?
                        GROUP BY DATE(timestamp)
                        ORDER BY date
                    ''', (start_date.isoformat(), event_type.value))
                    title = f"{event_type.value.replace('_', ' ').title()} Trend"
                else:
                    cursor.execute('''
                        SELECT DATE(timestamp) as date, COUNT(*) 
                        FROM analytics_events 
                        WHERE timestamp >= ?
                        GROUP BY DATE(timestamp)
                        ORDER BY date
                    ''', (start_date.isoformat(),))
                    title = "Overall Activity Trend"
                
                data = cursor.fetchall()
                
                # Fill in missing dates with 0 values
                date_counts = dict(data)
                labels = []
                values = []
                
                current_date = start_date.date()
                while current_date <= end_date.date():
                    date_str = current_date.isoformat()
                    labels.append(date_str)
                    values.append(date_counts.get(date_str, 0))
                    current_date += timedelta(days=1)
                
                return TrendData(
                    labels=labels,
                    values=values,
                    title=title,
                    chart_type="line"
                )
                
        except Exception as e:
            print(f"Error getting trend data: {e}")
            return TrendData(labels=[], values=[], title="Error")
    
    def get_event_type_distribution(self, days: int = 30) -> TrendData:
        """Get distribution of event types for pie chart"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)
                
                cursor.execute('''
                    SELECT event_type, COUNT(*) 
                    FROM analytics_events 
                    WHERE timestamp >= ?
                    GROUP BY event_type
                    ORDER BY COUNT(*) DESC
                ''', (start_date.isoformat(),))
                
                data = cursor.fetchall()
                
                labels = [event_type.replace('_', ' ').title() for event_type, _ in data]
                values = [count for _, count in data]
                
                return TrendData(
                    labels=labels,
                    values=values,
                    title="Event Type Distribution",
                    chart_type="pie"
                )
                
        except Exception as e:
            print(f"Error getting event type distribution: {e}")
            return TrendData(labels=[], values=[], title="Error")
    
    def cleanup_old_events(self, days_to_keep: int = 365):
        """Clean up old analytics events to prevent database bloat"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cutoff_date = datetime.now() - timedelta(days=days_to_keep)
                
                cursor.execute('''
                    DELETE FROM analytics_events 
                    WHERE timestamp < ?
                ''', (cutoff_date.isoformat(),))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                return deleted_count
                
        except Exception as e:
            print(f"Error cleaning up old events: {e}")
            return 0