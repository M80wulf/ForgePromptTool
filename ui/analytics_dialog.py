"""
Analytics dashboard dialog for displaying prompt usage statistics
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QTableWidget, QTableWidgetItem, QPushButton,
    QDialogButtonBox, QGroupBox, QFormLayout, QComboBox,
    QProgressBar, QScrollArea, QFrame, QGridLayout,
    QListWidget, QListWidgetItem, QSplitter, QTextEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPainter, QPen, QBrush, QColor, QPalette
# Try to import QtCharts, fall back to simple charts if not available
try:
    from PyQt6.QtCharts import QChart, QChartView, QLineSeries, QPieSeries, QBarSeries, QBarSet
    from PyQt6.QtCharts import QValueAxis, QDateTimeAxis, QBarCategoryAxis
    CHARTS_AVAILABLE = True
except ImportError:
    CHARTS_AVAILABLE = False
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from services.analytics_service import AnalyticsService
from models.analytics import UsageStats, PromptStats, TrendData, EventType


class SimpleChartWidget(QWidget):
    """Simple chart widget for basic visualizations when QtCharts is not available"""
    
    def __init__(self, trend_data: TrendData, parent=None):
        super().__init__(parent)
        self.trend_data = trend_data
        self.setMinimumSize(400, 300)
    
    def paintEvent(self, event):
        """Paint a simple chart"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Get widget dimensions
        width = self.width() - 40
        height = self.height() - 60
        margin_left = 30
        margin_bottom = 40
        
        # Draw background
        painter.fillRect(self.rect(), QColor(250, 250, 250))
        
        # Draw title
        painter.setPen(QPen(QColor(0, 0, 0)))
        painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        painter.drawText(10, 20, self.trend_data.title)
        
        if not self.trend_data.values or max(self.trend_data.values) == 0:
            painter.drawText(width // 2, height // 2, "No data available")
            return
        
        # Calculate scales
        max_value = max(self.trend_data.values)
        x_step = width / max(1, len(self.trend_data.values) - 1)
        y_scale = height / max_value if max_value > 0 else 1
        
        if self.trend_data.chart_type == "pie":
            self._draw_pie_chart(painter, width, height, margin_left, margin_bottom)
        elif self.trend_data.chart_type == "bar":
            self._draw_bar_chart(painter, width, height, margin_left, margin_bottom, x_step, y_scale)
        else:  # line chart
            self._draw_line_chart(painter, width, height, margin_left, margin_bottom, x_step, y_scale)
    
    def _draw_line_chart(self, painter, width, height, margin_left, margin_bottom, x_step, y_scale):
        """Draw a line chart"""
        # Draw axes
        painter.setPen(QPen(QColor(100, 100, 100), 2))
        painter.drawLine(margin_left, height + 30, margin_left + width, height + 30)  # X-axis
        painter.drawLine(margin_left, 30, margin_left, height + 30)  # Y-axis
        
        # Draw data points and lines
        painter.setPen(QPen(QColor(0, 120, 215), 3))
        points = []
        
        for i, value in enumerate(self.trend_data.values):
            x = margin_left + (i * x_step)
            y = height + 30 - (value * y_scale)
            points.append((x, y))
            
            # Draw point
            painter.setBrush(QBrush(QColor(0, 120, 215)))
            painter.drawEllipse(int(x - 3), int(y - 3), 6, 6)
        
        # Draw lines between points
        for i in range(len(points) - 1):
            x1, y1 = points[i]
            x2, y2 = points[i + 1]
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
    
    def _draw_bar_chart(self, painter, width, height, margin_left, margin_bottom, x_step, y_scale):
        """Draw a bar chart"""
        # Draw axes
        painter.setPen(QPen(QColor(100, 100, 100), 2))
        painter.drawLine(margin_left, height + 30, margin_left + width, height + 30)  # X-axis
        painter.drawLine(margin_left, 30, margin_left, height + 30)  # Y-axis
        
        # Draw bars
        bar_width = max(10, x_step * 0.6)
        colors = [QColor(0, 120, 215), QColor(255, 140, 0), QColor(40, 167, 69), 
                 QColor(220, 53, 69), QColor(108, 117, 125)]
        
        for i, value in enumerate(self.trend_data.values):
            x = margin_left + (i * x_step) - (bar_width / 2)
            y = height + 30 - (value * y_scale)
            bar_height = value * y_scale
            
            color = colors[i % len(colors)]
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(color.darker(120), 1))
            painter.drawRect(int(x), int(y), int(bar_width), int(bar_height))
    
    def _draw_pie_chart(self, painter, width, height, margin_left, margin_bottom):
        """Draw a pie chart"""
        center_x = margin_left + width // 2
        center_y = height // 2
        radius = min(width, height) // 3
        
        total = sum(self.trend_data.values)
        if total == 0:
            return
        
        colors = [QColor(0, 120, 215), QColor(255, 140, 0), QColor(40, 167, 69), 
                 QColor(220, 53, 69), QColor(108, 117, 125), QColor(255, 193, 7)]
        
        start_angle = 0
        for i, value in enumerate(self.trend_data.values):
            if value == 0:
                continue
                
            span_angle = int((value / total) * 360 * 16)  # Qt uses 1/16th degrees
            
            color = colors[i % len(colors)]
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(color.darker(120), 2))
            
            painter.drawPie(center_x - radius, center_y - radius, 
                          radius * 2, radius * 2, start_angle, span_angle)
            
            start_angle += span_angle


class AnalyticsWorkerThread(QThread):
    """Worker thread for loading analytics data"""
    
    stats_ready = pyqtSignal(object)  # UsageStats
    trend_ready = pyqtSignal(str, object)  # chart_name, TrendData
    error_occurred = pyqtSignal(str)
    
    def __init__(self, analytics_service: AnalyticsService, days: int = 30):
        super().__init__()
        self.analytics_service = analytics_service
        self.days = days
    
    def run(self):
        """Load analytics data in background"""
        try:
            # Load usage stats
            usage_stats = self.analytics_service.get_usage_stats(self.days)
            self.stats_ready.emit(usage_stats)
            
            # Load trend data
            activity_trend = self.analytics_service.get_trend_data(days=self.days)
            self.trend_ready.emit("activity", activity_trend)
            
            # Load event distribution
            event_dist = self.analytics_service.get_event_type_distribution(self.days)
            self.trend_ready.emit("events", event_dist)
            
            # Load specific event trends
            view_trend = self.analytics_service.get_trend_data(EventType.PROMPT_VIEWED, self.days)
            self.trend_ready.emit("views", view_trend)
            
            copy_trend = self.analytics_service.get_trend_data(EventType.PROMPT_COPIED, self.days)
            self.trend_ready.emit("copies", copy_trend)
            
        except Exception as e:
            self.error_occurred.emit(str(e))


class AnalyticsDashboard(QDialog):
    """Analytics dashboard dialog"""
    
    def __init__(self, analytics_service: AnalyticsService, parent=None):
        super().__init__(parent)
        self.analytics_service = analytics_service
        self.usage_stats = None
        self.trend_data = {}
        self.worker_thread = None
        
        self.setWindowTitle("Analytics Dashboard")
        self.setModal(False)
        self.resize(1000, 700)
        
        self.setup_ui()
        self.load_analytics_data()
    
    def setup_ui(self):
        """Setup the dashboard UI"""
        layout = QVBoxLayout()
        
        # Header with refresh button
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Analytics Dashboard")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Time range selector
        self.time_range_combo = QComboBox()
        self.time_range_combo.addItems(["Last 7 days", "Last 30 days", "Last 90 days", "Last year"])
        self.time_range_combo.setCurrentText("Last 30 days")
        self.time_range_combo.currentTextChanged.connect(self.on_time_range_changed)
        header_layout.addWidget(QLabel("Time Range:"))
        header_layout.addWidget(self.time_range_combo)
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.load_analytics_data)
        header_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Main content tabs
        self.tabs = QTabWidget()
        
        # Overview tab
        self.overview_tab = self.create_overview_tab()
        self.tabs.addTab(self.overview_tab, "Overview")
        
        # Charts tab
        self.charts_tab = self.create_charts_tab()
        self.tabs.addTab(self.charts_tab, "Charts")
        
        # Detailed stats tab
        self.details_tab = self.create_details_tab()
        self.tabs.addTab(self.details_tab, "Detailed Stats")
        
        layout.addWidget(self.tabs)
        
        # Dialog buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def create_overview_tab(self) -> QWidget:
        """Create the overview tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Key metrics cards
        metrics_layout = QGridLayout()
        
        self.total_prompts_label = self.create_metric_card("Total Prompts", "0")
        metrics_layout.addWidget(self.total_prompts_label, 0, 0)
        
        self.total_views_label = self.create_metric_card("Total Views", "0")
        metrics_layout.addWidget(self.total_views_label, 0, 1)
        
        self.total_copies_label = self.create_metric_card("Total Copies", "0")
        metrics_layout.addWidget(self.total_copies_label, 0, 2)
        
        self.llm_operations_label = self.create_metric_card("LLM Operations", "0")
        metrics_layout.addWidget(self.llm_operations_label, 1, 0)
        
        self.total_events_label = self.create_metric_card("Total Events", "0")
        metrics_layout.addWidget(self.total_events_label, 1, 1)
        
        layout.addLayout(metrics_layout)
        
        # Recent activity and most used prompts
        content_layout = QHBoxLayout()
        
        # Recent activity
        activity_group = QGroupBox("Recent Activity")
        activity_layout = QVBoxLayout()
        
        self.recent_activity_list = QListWidget()
        self.recent_activity_list.setMaximumHeight(200)
        activity_layout.addWidget(self.recent_activity_list)
        
        activity_group.setLayout(activity_layout)
        content_layout.addWidget(activity_group)
        
        # Most used prompts
        popular_group = QGroupBox("Most Used Prompts")
        popular_layout = QVBoxLayout()
        
        self.popular_prompts_table = QTableWidget()
        self.popular_prompts_table.setColumnCount(4)
        self.popular_prompts_table.setHorizontalHeaderLabels(["Title", "Views", "Copies", "LLM Uses"])
        self.popular_prompts_table.setMaximumHeight(200)
        popular_layout.addWidget(self.popular_prompts_table)
        
        popular_group.setLayout(popular_layout)
        content_layout.addWidget(popular_group)
        
        layout.addLayout(content_layout)
        layout.addStretch()
        
        tab.setLayout(layout)
        return tab
    
    def create_charts_tab(self) -> QWidget:
        """Create the charts tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Charts grid
        charts_layout = QGridLayout()
        
        # Activity trend chart
        self.activity_chart_widget = QLabel("Loading activity chart...")
        self.activity_chart_widget.setMinimumSize(400, 300)
        self.activity_chart_widget.setStyleSheet("border: 1px solid gray; background: white;")
        self.activity_chart_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        charts_layout.addWidget(self.activity_chart_widget, 0, 0)
        
        # Event distribution chart
        self.events_chart_widget = QLabel("Loading events chart...")
        self.events_chart_widget.setMinimumSize(400, 300)
        self.events_chart_widget.setStyleSheet("border: 1px solid gray; background: white;")
        self.events_chart_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        charts_layout.addWidget(self.events_chart_widget, 0, 1)
        
        # Views trend chart
        self.views_chart_widget = QLabel("Loading views chart...")
        self.views_chart_widget.setMinimumSize(400, 300)
        self.views_chart_widget.setStyleSheet("border: 1px solid gray; background: white;")
        self.views_chart_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        charts_layout.addWidget(self.views_chart_widget, 1, 0)
        
        # Copies trend chart
        self.copies_chart_widget = QLabel("Loading copies chart...")
        self.copies_chart_widget.setMinimumSize(400, 300)
        self.copies_chart_widget.setStyleSheet("border: 1px solid gray; background: white;")
        self.copies_chart_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        charts_layout.addWidget(self.copies_chart_widget, 1, 1)
        
        layout.addLayout(charts_layout)
        
        tab.setLayout(layout)
        return tab
    
    def create_details_tab(self) -> QWidget:
        """Create the detailed statistics tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Tag usage
        tag_group = QGroupBox("Tag Usage")
        tag_layout = QVBoxLayout()
        
        self.tag_usage_table = QTableWidget()
        self.tag_usage_table.setColumnCount(2)
        self.tag_usage_table.setHorizontalHeaderLabels(["Tag", "Usage Count"])
        tag_layout.addWidget(self.tag_usage_table)
        
        tag_group.setLayout(tag_layout)
        layout.addWidget(tag_group)
        
        # Daily activity breakdown
        daily_group = QGroupBox("Daily Activity")
        daily_layout = QVBoxLayout()
        
        self.daily_activity_table = QTableWidget()
        self.daily_activity_table.setColumnCount(2)
        self.daily_activity_table.setHorizontalHeaderLabels(["Date", "Events"])
        daily_layout.addWidget(self.daily_activity_table)
        
        daily_group.setLayout(daily_layout)
        layout.addWidget(daily_group)
        
        tab.setLayout(layout)
        return tab
    
    def create_metric_card(self, title: str, value: str) -> QWidget:
        """Create a metric card widget"""
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.Box)
        card.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        
        layout = QVBoxLayout()
        
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 10))
        title_label.setStyleSheet("color: #666;")
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        value_label.setStyleSheet("color: #333;")
        layout.addWidget(value_label)
        
        card.setLayout(layout)
        card.value_label = value_label  # Store reference for updates
        
        return card
    
    def on_time_range_changed(self, text: str):
        """Handle time range change"""
        self.load_analytics_data()
    
    def get_days_from_range(self) -> int:
        """Get number of days from selected range"""
        range_text = self.time_range_combo.currentText()
        if "7 days" in range_text:
            return 7
        elif "30 days" in range_text:
            return 30
        elif "90 days" in range_text:
            return 90
        elif "year" in range_text:
            return 365
        return 30
    
    def load_analytics_data(self):
        """Load analytics data in background thread"""
        if self.worker_thread and self.worker_thread.isRunning():
            return
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.refresh_btn.setEnabled(False)
        
        days = self.get_days_from_range()
        
        self.worker_thread = AnalyticsWorkerThread(self.analytics_service, days)
        self.worker_thread.stats_ready.connect(self.on_stats_ready)
        self.worker_thread.trend_ready.connect(self.on_trend_ready)
        self.worker_thread.error_occurred.connect(self.on_error_occurred)
        self.worker_thread.finished.connect(self.on_loading_finished)
        self.worker_thread.start()
    
    def on_stats_ready(self, usage_stats: UsageStats):
        """Handle loaded usage statistics"""
        self.usage_stats = usage_stats
        self.update_overview_tab()
        self.update_details_tab()
    
    def on_trend_ready(self, chart_name: str, trend_data: TrendData):
        """Handle loaded trend data"""
        self.trend_data[chart_name] = trend_data
        self.update_chart(chart_name, trend_data)
    
    def on_error_occurred(self, error_message: str):
        """Handle loading error"""
        print(f"Analytics loading error: {error_message}")
    
    def on_loading_finished(self):
        """Handle loading completion"""
        self.progress_bar.setVisible(False)
        self.refresh_btn.setEnabled(True)
        if self.worker_thread:
            self.worker_thread.deleteLater()
            self.worker_thread = None
    
    def update_overview_tab(self):
        """Update the overview tab with loaded data"""
        if not self.usage_stats:
            return
        
        # Update metric cards
        self.total_prompts_label.value_label.setText(str(self.usage_stats.total_prompts))
        self.total_views_label.value_label.setText(str(self.usage_stats.total_views))
        self.total_copies_label.value_label.setText(str(self.usage_stats.total_copies))
        self.llm_operations_label.value_label.setText(str(self.usage_stats.total_llm_operations))
        self.total_events_label.value_label.setText(str(self.usage_stats.total_events))
        
        # Update recent activity
        self.recent_activity_list.clear()
        for event in self.usage_stats.recent_activity[:10]:
            event_text = f"{event.event_type.replace('_', ' ').title()}"
            if event.timestamp:
                event_text += f" - {event.timestamp.strftime('%Y-%m-%d %H:%M')}"
            item = QListWidgetItem(event_text)
            self.recent_activity_list.addItem(item)
        
        # Update most used prompts table
        self.popular_prompts_table.setRowCount(len(self.usage_stats.most_used_prompts))
        for i, prompt_stats in enumerate(self.usage_stats.most_used_prompts):
            self.popular_prompts_table.setItem(i, 0, QTableWidgetItem(prompt_stats.title))
            self.popular_prompts_table.setItem(i, 1, QTableWidgetItem(str(prompt_stats.view_count)))
            self.popular_prompts_table.setItem(i, 2, QTableWidgetItem(str(prompt_stats.copy_count)))
            self.popular_prompts_table.setItem(i, 3, QTableWidgetItem(str(prompt_stats.llm_usage_count)))
        
        self.popular_prompts_table.resizeColumnsToContents()
    
    def update_details_tab(self):
        """Update the details tab with loaded data"""
        if not self.usage_stats:
            return
        
        # Update tag usage table
        tag_items = list(self.usage_stats.tag_usage.items())
        self.tag_usage_table.setRowCount(len(tag_items))
        for i, (tag, count) in enumerate(tag_items):
            self.tag_usage_table.setItem(i, 0, QTableWidgetItem(tag))
            self.tag_usage_table.setItem(i, 1, QTableWidgetItem(str(count)))
        
        self.tag_usage_table.resizeColumnsToContents()
        
        # Update daily activity table
        daily_items = list(self.usage_stats.daily_activity.items())
        daily_items.sort(key=lambda x: x[0], reverse=True)  # Sort by date, newest first
        
        self.daily_activity_table.setRowCount(len(daily_items))
        for i, (date, count) in enumerate(daily_items):
            self.daily_activity_table.setItem(i, 0, QTableWidgetItem(date))
            self.daily_activity_table.setItem(i, 1, QTableWidgetItem(str(count)))
        
        self.daily_activity_table.resizeColumnsToContents()
    
    def update_chart(self, chart_name: str, trend_data: TrendData):
        """Update a specific chart"""
        chart_widget = None
        
        if chart_name == "activity":
            chart_widget = self.activity_chart_widget
        elif chart_name == "events":
            chart_widget = self.events_chart_widget
        elif chart_name == "views":
            chart_widget = self.views_chart_widget
        elif chart_name == "copies":
            chart_widget = self.copies_chart_widget
        
        if chart_widget:
            # Replace label with actual chart widget
            parent = chart_widget.parent()
            if parent:
                layout = parent.layout()
                if layout:
                    # Find the position of the old widget
                    for i in range(layout.count()):
                        if layout.itemAt(i).widget() == chart_widget:
                            # Remove old widget
                            layout.removeWidget(chart_widget)
                            chart_widget.deleteLater()
                            
                            # Add new chart widget
                            new_chart = SimpleChartWidget(trend_data)
                            layout.addWidget(new_chart, i // 2, i % 2)
                            break
    
    def closeEvent(self, event):
        """Handle dialog close"""
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.terminate()
            self.worker_thread.wait()
        event.accept()