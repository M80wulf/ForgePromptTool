"""
Performance tracking models for the Prompt Organizer
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum


class MetricType(Enum):
    """Types of performance metrics"""
    RESPONSE_TIME = "response_time"
    TOKEN_COUNT = "token_count"
    COST = "cost"
    QUALITY_SCORE = "quality_score"
    SUCCESS_RATE = "success_rate"
    USER_RATING = "user_rating"
    COMPLETION_RATE = "completion_rate"
    ERROR_RATE = "error_rate"
    RELEVANCE_SCORE = "relevance_score"
    CREATIVITY_SCORE = "creativity_score"


class PerformanceStatus(Enum):
    """Status of performance tracking"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class MetricAggregation(Enum):
    """Types of metric aggregation"""
    AVERAGE = "average"
    SUM = "sum"
    COUNT = "count"
    MIN = "min"
    MAX = "max"
    MEDIAN = "median"
    PERCENTILE_95 = "percentile_95"


@dataclass
class PerformanceMetric:
    """Individual performance metric"""
    id: Optional[int] = None
    execution_id: Optional[int] = None
    metric_type: MetricType = MetricType.RESPONSE_TIME
    value: float = 0.0
    unit: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class PromptExecution:
    """Record of a prompt execution"""
    id: Optional[int] = None
    prompt_id: int = 0
    prompt_version: str = "1.0"
    input_text: str = ""
    output_text: str = ""
    llm_provider: str = ""
    llm_model: str = ""
    execution_time: float = 0.0
    token_count_input: int = 0
    token_count_output: int = 0
    cost: float = 0.0
    status: PerformanceStatus = PerformanceStatus.ACTIVE
    error_message: Optional[str] = None
    user_id: str = ""
    session_id: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class PerformanceReport:
    """Performance analysis report"""
    id: Optional[int] = None
    prompt_id: int = 0
    report_type: str = "summary"
    period_start: str = ""
    period_end: str = ""
    total_executions: int = 0
    success_rate: float = 0.0
    average_response_time: float = 0.0
    average_cost: float = 0.0
    average_quality_score: float = 0.0
    metrics_summary: Dict[str, Any] = field(default_factory=dict)
    insights: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class PerformanceBenchmark:
    """Performance benchmark for comparison"""
    id: Optional[int] = None
    name: str = ""
    description: str = ""
    prompt_category: str = ""
    metric_type: MetricType = MetricType.RESPONSE_TIME
    target_value: float = 0.0
    threshold_good: float = 0.0
    threshold_excellent: float = 0.0
    unit: str = ""
    is_active: bool = True
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class PerformanceAlert:
    """Performance alert configuration"""
    id: Optional[int] = None
    prompt_id: int = 0
    metric_type: MetricType = MetricType.RESPONSE_TIME
    condition: str = "greater_than"  # greater_than, less_than, equals, percentage_change
    threshold_value: float = 0.0
    is_active: bool = True
    notification_email: str = ""
    last_triggered: Optional[str] = None
    trigger_count: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class PerformanceComparison:
    """Comparison between different prompts or versions"""
    id: Optional[int] = None
    name: str = ""
    description: str = ""
    prompt_ids: List[int] = field(default_factory=list)
    metric_types: List[MetricType] = field(default_factory=list)
    comparison_period: str = "last_30_days"
    results: Dict[str, Any] = field(default_factory=dict)
    winner_prompt_id: Optional[int] = None
    confidence_score: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class PerformanceOptimization:
    """Performance optimization suggestion"""
    id: Optional[int] = None
    prompt_id: int = 0
    optimization_type: str = ""  # token_reduction, clarity_improvement, structure_optimization
    current_metric_value: float = 0.0
    predicted_improvement: float = 0.0
    confidence: float = 0.0
    suggestion: str = ""
    implementation_effort: str = "low"  # low, medium, high
    priority: str = "medium"  # low, medium, high, critical
    status: str = "pending"  # pending, applied, rejected
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class PerformanceSession:
    """Performance tracking session"""
    id: Optional[int] = None
    session_id: str = ""
    user_id: str = ""
    start_time: str = field(default_factory=lambda: datetime.now().isoformat())
    end_time: Optional[str] = None
    total_executions: int = 0
    total_cost: float = 0.0
    total_tokens: int = 0
    session_metadata: Optional[Dict[str, Any]] = None


@dataclass
class PerformanceConfig:
    """Performance tracking configuration"""
    enabled: bool = True
    auto_track_executions: bool = True
    track_costs: bool = True
    track_quality: bool = True
    retention_days: int = 90
    alert_email: str = ""
    benchmark_enabled: bool = True
    optimization_suggestions: bool = True
    export_format: str = "json"
    aggregation_interval: str = "daily"  # hourly, daily, weekly, monthly