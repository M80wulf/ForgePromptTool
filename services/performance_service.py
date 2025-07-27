"""
Performance tracking service for the Prompt Organizer
"""

import sqlite3
import json
import time
import statistics
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from models.performance_models import (
    PerformanceMetric, PromptExecution, PerformanceReport,
    PerformanceBenchmark, PerformanceAlert, PerformanceComparison,
    PerformanceOptimization, PerformanceSession, PerformanceConfig,
    MetricType, PerformanceStatus, MetricAggregation
)


class PerformanceService:
    """Service for tracking prompt performance and metrics"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.config = PerformanceConfig()
        self.current_session = None
        self._init_performance_tables()
    
    def _init_performance_tables(self):
        """Initialize performance tracking database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Prompt executions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS prompt_executions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prompt_id INTEGER NOT NULL,
                    prompt_version TEXT DEFAULT '1.0',
                    input_text TEXT NOT NULL,
                    output_text TEXT DEFAULT '',
                    llm_provider TEXT DEFAULT '',
                    llm_model TEXT DEFAULT '',
                    execution_time REAL DEFAULT 0.0,
                    token_count_input INTEGER DEFAULT 0,
                    token_count_output INTEGER DEFAULT 0,
                    cost REAL DEFAULT 0.0,
                    status TEXT DEFAULT 'active',
                    error_message TEXT,
                    user_id TEXT DEFAULT '',
                    session_id TEXT DEFAULT '',
                    timestamp TEXT NOT NULL,
                    metadata TEXT DEFAULT '{}',
                    FOREIGN KEY (prompt_id) REFERENCES prompts (id) ON DELETE CASCADE
                )
            """)
            
            # Performance metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    execution_id INTEGER NOT NULL,
                    metric_type TEXT NOT NULL,
                    value REAL NOT NULL,
                    unit TEXT DEFAULT '',
                    timestamp TEXT NOT NULL,
                    metadata TEXT DEFAULT '{}',
                    FOREIGN KEY (execution_id) REFERENCES prompt_executions (id) ON DELETE CASCADE
                )
            """)
            
            # Performance reports table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS performance_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prompt_id INTEGER NOT NULL,
                    report_type TEXT DEFAULT 'summary',
                    period_start TEXT NOT NULL,
                    period_end TEXT NOT NULL,
                    total_executions INTEGER DEFAULT 0,
                    success_rate REAL DEFAULT 0.0,
                    average_response_time REAL DEFAULT 0.0,
                    average_cost REAL DEFAULT 0.0,
                    average_quality_score REAL DEFAULT 0.0,
                    metrics_summary TEXT DEFAULT '{}',
                    insights TEXT DEFAULT '[]',
                    recommendations TEXT DEFAULT '[]',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (prompt_id) REFERENCES prompts (id) ON DELETE CASCADE
                )
            """)
            
            # Performance benchmarks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS performance_benchmarks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    prompt_category TEXT DEFAULT '',
                    metric_type TEXT NOT NULL,
                    target_value REAL NOT NULL,
                    threshold_good REAL NOT NULL,
                    threshold_excellent REAL NOT NULL,
                    unit TEXT DEFAULT '',
                    is_active BOOLEAN DEFAULT 1,
                    created_at TEXT NOT NULL
                )
            """)
            
            # Performance alerts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS performance_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prompt_id INTEGER NOT NULL,
                    metric_type TEXT NOT NULL,
                    condition TEXT NOT NULL,
                    threshold_value REAL NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    notification_email TEXT DEFAULT '',
                    last_triggered TEXT,
                    trigger_count INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (prompt_id) REFERENCES prompts (id) ON DELETE CASCADE
                )
            """)
            
            # Performance comparisons table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS performance_comparisons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    prompt_ids TEXT NOT NULL,
                    metric_types TEXT NOT NULL,
                    comparison_period TEXT DEFAULT 'last_30_days',
                    results TEXT DEFAULT '{}',
                    winner_prompt_id INTEGER,
                    confidence_score REAL DEFAULT 0.0,
                    created_at TEXT NOT NULL
                )
            """)
            
            # Performance optimizations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS performance_optimizations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prompt_id INTEGER NOT NULL,
                    optimization_type TEXT NOT NULL,
                    current_metric_value REAL NOT NULL,
                    predicted_improvement REAL NOT NULL,
                    confidence REAL NOT NULL,
                    suggestion TEXT NOT NULL,
                    implementation_effort TEXT DEFAULT 'medium',
                    priority TEXT DEFAULT 'medium',
                    status TEXT DEFAULT 'pending',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (prompt_id) REFERENCES prompts (id) ON DELETE CASCADE
                )
            """)
            
            # Performance sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS performance_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    user_id TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    total_executions INTEGER DEFAULT 0,
                    total_cost REAL DEFAULT 0.0,
                    total_tokens INTEGER DEFAULT 0,
                    session_metadata TEXT DEFAULT '{}'
                )
            """)
            
            conn.commit()
            
        except sqlite3.Error as e:
            print(f"Error initializing performance tables: {e}")
        finally:
            conn.close()
    
    def start_session(self, user_id: str, session_metadata: Optional[Dict[str, Any]] = None) -> str:
        """Start a new performance tracking session"""
        import uuid
        session_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            start_time = datetime.now().isoformat()
            metadata_json = json.dumps(session_metadata or {})
            
            cursor.execute("""
                INSERT INTO performance_sessions 
                (session_id, user_id, start_time, session_metadata)
                VALUES (?, ?, ?, ?)
            """, (session_id, user_id, start_time, metadata_json))
            
            conn.commit()
            
            self.current_session = PerformanceSession(
                session_id=session_id,
                user_id=user_id,
                start_time=start_time,
                session_metadata=session_metadata
            )
            
            return session_id
            
        except sqlite3.Error as e:
            print(f"Error starting performance session: {e}")
            return ""
        finally:
            conn.close()
    
    def end_session(self, session_id: str) -> bool:
        """End a performance tracking session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            end_time = datetime.now().isoformat()
            
            # Get session statistics
            cursor.execute("""
                SELECT COUNT(*), SUM(cost), SUM(token_count_input + token_count_output)
                FROM prompt_executions 
                WHERE session_id = ?
            """, (session_id,))
            
            stats = cursor.fetchone()
            total_executions = stats[0] or 0
            total_cost = stats[1] or 0.0
            total_tokens = stats[2] or 0
            
            # Update session
            cursor.execute("""
                UPDATE performance_sessions 
                SET end_time = ?, total_executions = ?, total_cost = ?, total_tokens = ?
                WHERE session_id = ?
            """, (end_time, total_executions, total_cost, total_tokens, session_id))
            
            conn.commit()
            
            if self.current_session and self.current_session.session_id == session_id:
                self.current_session = None
            
            return cursor.rowcount > 0
            
        except sqlite3.Error as e:
            print(f"Error ending performance session: {e}")
            return False
        finally:
            conn.close()
    
    def record_execution(self, prompt_id: int, input_text: str, output_text: str = "",
                        llm_provider: str = "", llm_model: str = "",
                        execution_time: float = 0.0, token_count_input: int = 0,
                        token_count_output: int = 0, cost: float = 0.0,
                        status: PerformanceStatus = PerformanceStatus.ACTIVE,
                        error_message: Optional[str] = None,
                        user_id: str = "", metadata: Optional[Dict[str, Any]] = None) -> Optional[PromptExecution]:
        """Record a prompt execution for performance tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            timestamp = datetime.now().isoformat()
            session_id = self.current_session.session_id if self.current_session else ""
            metadata_json = json.dumps(metadata or {})
            
            cursor.execute("""
                INSERT INTO prompt_executions 
                (prompt_id, input_text, output_text, llm_provider, llm_model,
                 execution_time, token_count_input, token_count_output, cost,
                 status, error_message, user_id, session_id, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (prompt_id, input_text, output_text, llm_provider, llm_model,
                  execution_time, token_count_input, token_count_output, cost,
                  status.value, error_message, user_id, session_id, timestamp, metadata_json))
            
            execution_id = cursor.lastrowid
            conn.commit()
            
            # Record basic metrics
            self._record_basic_metrics(execution_id, execution_time, token_count_input + token_count_output, cost)
            
            # Check alerts
            self._check_alerts(prompt_id, execution_time, cost)
            
            return PromptExecution(
                id=execution_id,
                prompt_id=prompt_id,
                input_text=input_text,
                output_text=output_text,
                llm_provider=llm_provider,
                llm_model=llm_model,
                execution_time=execution_time,
                token_count_input=token_count_input,
                token_count_output=token_count_output,
                cost=cost,
                status=status,
                error_message=error_message,
                user_id=user_id,
                session_id=session_id,
                timestamp=timestamp,
                metadata=metadata
            )
            
        except sqlite3.Error as e:
            print(f"Error recording execution: {e}")
            return None
        finally:
            conn.close()
    
    def _record_basic_metrics(self, execution_id: int, execution_time: float, 
                            token_count: int, cost: float):
        """Record basic performance metrics for an execution"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            timestamp = datetime.now().isoformat()
            
            metrics = [
                (execution_id, MetricType.RESPONSE_TIME.value, execution_time, "seconds", timestamp, "{}"),
                (execution_id, MetricType.TOKEN_COUNT.value, token_count, "tokens", timestamp, "{}"),
                (execution_id, MetricType.COST.value, cost, "USD", timestamp, "{}")
            ]
            
            cursor.executemany("""
                INSERT INTO performance_metrics 
                (execution_id, metric_type, value, unit, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, metrics)
            
            conn.commit()
            
        except sqlite3.Error as e:
            print(f"Error recording basic metrics: {e}")
        finally:
            conn.close()
    
    def add_metric(self, execution_id: int, metric_type: MetricType, value: float,
                  unit: str = "", metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Add a custom performance metric"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            timestamp = datetime.now().isoformat()
            metadata_json = json.dumps(metadata or {})
            
            cursor.execute("""
                INSERT INTO performance_metrics 
                (execution_id, metric_type, value, unit, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (execution_id, metric_type.value, value, unit, timestamp, metadata_json))
            
            conn.commit()
            return True
            
        except sqlite3.Error as e:
            print(f"Error adding metric: {e}")
            return False
        finally:
            conn.close()
    
    def get_prompt_metrics(self, prompt_id: int, metric_types: Optional[List[MetricType]] = None,
                          period_days: int = 30) -> Dict[str, List[float]]:
        """Get metrics for a specific prompt"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            since_date = (datetime.now() - timedelta(days=period_days)).isoformat()
            
            query = """
                SELECT pm.metric_type, pm.value
                FROM performance_metrics pm
                JOIN prompt_executions pe ON pm.execution_id = pe.id
                WHERE pe.prompt_id = ? AND pe.timestamp >= ?
            """
            params = [prompt_id, since_date]
            
            if metric_types:
                placeholders = ",".join("?" * len(metric_types))
                query += f" AND pm.metric_type IN ({placeholders})"
                params.extend([mt.value for mt in metric_types])
            
            cursor.execute(query, params)
            
            metrics = {}
            for row in cursor.fetchall():
                metric_type = row[0]
                value = row[1]
                
                if metric_type not in metrics:
                    metrics[metric_type] = []
                metrics[metric_type].append(value)
            
            return metrics
            
        except sqlite3.Error as e:
            print(f"Error getting prompt metrics: {e}")
            return {}
        finally:
            conn.close()
    
    def generate_performance_report(self, prompt_id: int, period_days: int = 30) -> Optional[PerformanceReport]:
        """Generate a comprehensive performance report for a prompt"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=period_days)
            
            # Get execution statistics
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_executions,
                    AVG(execution_time) as avg_response_time,
                    AVG(cost) as avg_cost,
                    SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as success_rate
                FROM prompt_executions
                WHERE prompt_id = ? AND timestamp >= ? AND timestamp <= ?
            """, (prompt_id, start_date.isoformat(), end_date.isoformat()))
            
            stats = cursor.fetchone()
            
            if not stats or stats[0] == 0:
                return None
            
            # Get detailed metrics
            metrics = self.get_prompt_metrics(prompt_id, period_days=period_days)
            
            # Calculate metrics summary
            metrics_summary = {}
            for metric_type, values in metrics.items():
                if values:
                    metrics_summary[metric_type] = {
                        "count": len(values),
                        "average": statistics.mean(values),
                        "median": statistics.median(values),
                        "min": min(values),
                        "max": max(values),
                        "std_dev": statistics.stdev(values) if len(values) > 1 else 0
                    }
            
            # Generate insights and recommendations
            insights = self._generate_insights(metrics_summary, stats)
            recommendations = self._generate_recommendations(metrics_summary, stats)
            
            # Create report
            report = PerformanceReport(
                prompt_id=prompt_id,
                period_start=start_date.isoformat(),
                period_end=end_date.isoformat(),
                total_executions=stats[0],
                success_rate=stats[3] or 0.0,
                average_response_time=stats[1] or 0.0,
                average_cost=stats[2] or 0.0,
                metrics_summary=metrics_summary,
                insights=insights,
                recommendations=recommendations
            )
            
            # Save report to database
            cursor.execute("""
                INSERT INTO performance_reports 
                (prompt_id, period_start, period_end, total_executions, success_rate,
                 average_response_time, average_cost, metrics_summary, insights, recommendations, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (prompt_id, report.period_start, report.period_end, report.total_executions,
                  report.success_rate, report.average_response_time, report.average_cost,
                  json.dumps(report.metrics_summary), json.dumps(report.insights),
                  json.dumps(report.recommendations), report.created_at))
            
            report.id = cursor.lastrowid
            conn.commit()
            
            return report
            
        except sqlite3.Error as e:
            print(f"Error generating performance report: {e}")
            return None
        finally:
            conn.close()
    
    def _generate_insights(self, metrics_summary: Dict[str, Any], stats: Tuple) -> List[str]:
        """Generate performance insights based on metrics"""
        insights = []
        
        # Response time insights
        if "response_time" in metrics_summary:
            avg_time = metrics_summary["response_time"]["average"]
            if avg_time > 5.0:
                insights.append(f"Average response time of {avg_time:.2f}s is above optimal range (< 3s)")
            elif avg_time < 1.0:
                insights.append(f"Excellent response time of {avg_time:.2f}s")
        
        # Cost insights
        if "cost" in metrics_summary:
            avg_cost = metrics_summary["cost"]["average"]
            if avg_cost > 0.1:
                insights.append(f"High average cost of ${avg_cost:.4f} per execution")
            elif avg_cost < 0.01:
                insights.append(f"Very cost-efficient at ${avg_cost:.4f} per execution")
        
        # Success rate insights
        success_rate = stats[3] or 0.0
        if success_rate < 90:
            insights.append(f"Success rate of {success_rate:.1f}% needs improvement")
        elif success_rate > 98:
            insights.append(f"Excellent success rate of {success_rate:.1f}%")
        
        # Token usage insights
        if "token_count" in metrics_summary:
            avg_tokens = metrics_summary["token_count"]["average"]
            if avg_tokens > 2000:
                insights.append(f"High token usage of {avg_tokens:.0f} tokens per execution")
        
        return insights
    
    def _generate_recommendations(self, metrics_summary: Dict[str, Any], stats: Tuple) -> List[str]:
        """Generate performance recommendations based on metrics"""
        recommendations = []
        
        # Response time recommendations
        if "response_time" in metrics_summary:
            avg_time = metrics_summary["response_time"]["average"]
            if avg_time > 5.0:
                recommendations.append("Consider optimizing prompt length or complexity to reduce response time")
                recommendations.append("Try using a faster LLM model if accuracy allows")
        
        # Cost recommendations
        if "cost" in metrics_summary:
            avg_cost = metrics_summary["cost"]["average"]
            if avg_cost > 0.1:
                recommendations.append("Consider using a more cost-effective LLM model")
                recommendations.append("Optimize prompt to reduce token usage")
        
        # Success rate recommendations
        success_rate = stats[3] or 0.0
        if success_rate < 90:
            recommendations.append("Review and improve prompt clarity and instructions")
            recommendations.append("Add more specific examples or constraints")
        
        # Token usage recommendations
        if "token_count" in metrics_summary:
            avg_tokens = metrics_summary["token_count"]["average"]
            if avg_tokens > 2000:
                recommendations.append("Reduce prompt length while maintaining effectiveness")
                recommendations.append("Remove unnecessary examples or verbose instructions")
        
        return recommendations
    
    def create_benchmark(self, name: str, description: str, prompt_category: str,
                        metric_type: MetricType, target_value: float,
                        threshold_good: float, threshold_excellent: float,
                        unit: str = "") -> Optional[PerformanceBenchmark]:
        """Create a performance benchmark"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            created_at = datetime.now().isoformat()
            
            cursor.execute("""
                INSERT INTO performance_benchmarks 
                (name, description, prompt_category, metric_type, target_value,
                 threshold_good, threshold_excellent, unit, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, description, prompt_category, metric_type.value, target_value,
                  threshold_good, threshold_excellent, unit, created_at))
            
            benchmark_id = cursor.lastrowid
            conn.commit()
            
            return PerformanceBenchmark(
                id=benchmark_id,
                name=name,
                description=description,
                prompt_category=prompt_category,
                metric_type=metric_type,
                target_value=target_value,
                threshold_good=threshold_good,
                threshold_excellent=threshold_excellent,
                unit=unit,
                created_at=created_at
            )
            
        except sqlite3.Error as e:
            print(f"Error creating benchmark: {e}")
            return None
        finally:
            conn.close()
    
    def _check_alerts(self, prompt_id: int, execution_time: float, cost: float):
        """Check if any performance alerts should be triggered"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT * FROM performance_alerts 
                WHERE prompt_id = ? AND is_active = 1
            """, (prompt_id,))
            
            alerts = cursor.fetchall()
            
            for alert in alerts:
                alert_id = alert[0]
                metric_type = alert[2]
                condition = alert[3]
                threshold = alert[4]
                
                should_trigger = False
                
                if metric_type == MetricType.RESPONSE_TIME.value:
                    should_trigger = self._evaluate_condition(execution_time, condition, threshold)
                elif metric_type == MetricType.COST.value:
                    should_trigger = self._evaluate_condition(cost, condition, threshold)
                
                if should_trigger:
                    self._trigger_alert(alert_id)
            
        except sqlite3.Error as e:
            print(f"Error checking alerts: {e}")
        finally:
            conn.close()
    
    def _evaluate_condition(self, value: float, condition: str, threshold: float) -> bool:
        """Evaluate if an alert condition is met"""
        if condition == "greater_than":
            return value > threshold
        elif condition == "less_than":
            return value < threshold
        elif condition == "equals":
            return abs(value - threshold) < 0.001
        return False
    
    def _trigger_alert(self, alert_id: int):
        """Trigger a performance alert"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            triggered_at = datetime.now().isoformat()
            
            cursor.execute("""
                UPDATE performance_alerts 
                SET last_triggered = ?, trigger_count = trigger_count + 1
                WHERE id = ?
            """, (triggered_at, alert_id))
            
            conn.commit()
            
            # Here you could add email notification logic
            print(f"Performance alert {alert_id} triggered at {triggered_at}")
            
        except sqlite3.Error as e:
            print(f"Error triggering alert: {e}")
        finally:
            conn.close()
    
    def get_performance_summary(self, prompt_id: Optional[int] = None, 
                              period_days: int = 30) -> Dict[str, Any]:
        """Get a summary of performance metrics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            since_date = (datetime.now() - timedelta(days=period_days)).isoformat()
            
            if prompt_id:
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_executions,
                        AVG(execution_time) as avg_response_time,
                        AVG(cost) as avg_cost,
                        SUM(token_count_input + token_count_output) as total_tokens,
                        SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as success_rate
                    FROM prompt_executions
                    WHERE prompt_id = ? AND timestamp >= ?
                """, (prompt_id, since_date))
            else:
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_executions,
                        AVG(execution_time) as avg_response_time,
                        AVG(cost) as avg_cost,
                        SUM(token_count_input + token_count_output) as total_tokens,
                        SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as success_rate
                    FROM prompt_executions
                    WHERE timestamp >= ?
                """, (since_date,))
            
            result = cursor.fetchone()
            
            if not result or result[0] == 0:
                return {
                    "total_executions": 0,
                    "avg_response_time": 0.0,
                    "avg_cost": 0.0,
                    "total_tokens": 0,
                    "success_rate": 0.0
                }
            
            return {
                "total_executions": result[0],
                "avg_response_time": result[1] or 0.0,
                "avg_cost": result[2] or 0.0,
                "total_tokens": result[3] or 0,
                "success_rate": result[4] or 0.0
            }
            
        except sqlite3.Error as e:
            print(f"Error getting performance summary: {e}")
            return {}
        finally:
            conn.close()