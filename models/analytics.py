"""
Analytics data models for tracking prompt usage and statistics
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum


class EventType(Enum):
    """Types of events to track"""
    PROMPT_CREATED = "prompt_created"
    PROMPT_VIEWED = "prompt_viewed"
    PROMPT_COPIED = "prompt_copied"
    PROMPT_EDITED = "prompt_edited"
    PROMPT_DELETED = "prompt_deleted"
    PROMPT_FAVORITED = "prompt_favorited"
    PROMPT_UNFAVORITED = "prompt_unfavorited"
    LLM_REWRITE = "llm_rewrite"
    LLM_EXPLAIN = "llm_explain"
    LLM_IMPROVE = "llm_improve"
    LLM_GENERATE_TAGS = "llm_generate_tags"
    SEARCH_PERFORMED = "search_performed"
    EXPORT_PERFORMED = "export_performed"
    IMPORT_PERFORMED = "import_performed"


@dataclass
class AnalyticsEvent:
    """Individual analytics event"""
    id: Optional[int] = None
    event_type: str = ""
    prompt_id: Optional[int] = None
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}


@dataclass
class PromptStats:
    """Statistics for a specific prompt"""
    prompt_id: int
    title: str
    view_count: int = 0
    copy_count: int = 0
    edit_count: int = 0
    llm_usage_count: int = 0
    last_accessed: Optional[datetime] = None
    created_date: Optional[datetime] = None
    is_favorite: bool = False
    tag_count: int = 0
    character_count: int = 0
    word_count: int = 0


@dataclass
class UsageStats:
    """Overall usage statistics"""
    total_prompts: int = 0
    total_events: int = 0
    total_views: int = 0
    total_copies: int = 0
    total_llm_operations: int = 0
    most_used_prompts: List[PromptStats] = None
    recent_activity: List[AnalyticsEvent] = None
    daily_activity: Dict[str, int] = None
    tag_usage: Dict[str, int] = None
    
    def __post_init__(self):
        if self.most_used_prompts is None:
            self.most_used_prompts = []
        if self.recent_activity is None:
            self.recent_activity = []
        if self.daily_activity is None:
            self.daily_activity = {}
        if self.tag_usage is None:
            self.tag_usage = {}


@dataclass
class TimeRangeStats:
    """Statistics for a specific time range"""
    start_date: datetime
    end_date: datetime
    event_count: int = 0
    unique_prompts_accessed: int = 0
    most_active_day: Optional[str] = None
    most_used_event_type: Optional[str] = None
    average_daily_activity: float = 0.0


@dataclass
class TrendData:
    """Trend data for charts"""
    labels: List[str]
    values: List[int]
    title: str
    chart_type: str = "line"  # line, bar, pie