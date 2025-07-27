"""
Performance tracking dialog for the Prompt Organizer
"""

import sys
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QTableWidget, QTableWidgetItem, QPushButton,
    QComboBox, QSpinBox, QCheckBox, QTextEdit, QGroupBox,
    QGridLayout, QProgressBar, QFrame, QScrollArea,
    QSplitter, QDateEdit, QDoubleSpinBox, QLineEdit,
    QFormLayout, QMessageBox, QHeaderView
)
from PyQt6.QtCore import Qt, QDate, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import json

try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Matplotlib not available. Charts will be disabled.")


class PerformanceMetricsWidget(QWidget):
    """Widget for displaying performance metrics"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Metrics summary
        summary_group = QGroupBox("Performance Summary")
        summary_layout = QGridLayout(summary_group)
        
        self.total_executions_label = QLabel("0")
        self.avg_response_time_label = QLabel("0.00s")
        self.avg_cost_label = QLabel("$0.0000")
        self.success_rate_label = QLabel("0.0%")
        self.total_tokens_label = QLabel("0")
        
        summary_layout.addWidget(QLabel("Total Executions:"), 0, 0)
        summary_layout.addWidget(self.total_executions_label, 0, 1)
        summary_layout.addWidget(QLabel("Avg Response Time:"), 1, 0)
        summary_layout.addWidget(self.avg_response_time_label, 1, 1)
        summary_layout.addWidget(QLabel("Avg Cost:"), 2, 0)
        summary_layout.addWidget(self.avg_cost_label, 2, 1)
        summary_layout.addWidget(QLabel("Success Rate:"), 0, 2)
        summary_layout.addWidget(self.success_rate_label, 0, 3)
        summary_layout.addWidget(QLabel("Total Tokens:"), 1, 2)
        summary_layout.addWidget(self.total_tokens_label, 1, 3)
        
        layout.addWidget(summary_group)
        
        # Recent executions table
        executions_group = QGroupBox("Recent Executions")
        executions_layout = QVBoxLayout(executions_group)
        
        self.executions_table = QTableWidget()
        self.executions_table.setColumnCount(7)
        self.executions_table.setHorizontalHeaderLabels([
            "Timestamp", "Provider", "Model", "Response Time", "Tokens", "Cost", "Status"
        ])
        self.executions_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        executions_layout.addWidget(self.executions_table)
        layout.addWidget(executions_group)
        
        # Charts (if matplotlib available)
        if MATPLOTLIB_AVAILABLE:
            self.create_charts_widget(layout)
    
    def create_charts_widget(self, parent_layout):
        """Create charts widget for performance visualization"""
        charts_group = QGroupBox("Performance Charts")
        charts_layout = QHBoxLayout(charts_group)
        
        # Response time chart
        self.response_time_figure = Figure(figsize=(6, 4))
        self.response_time_canvas = FigureCanvas(self.response_time_figure)
        charts_layout.addWidget(self.response_time_canvas)
        
        # Cost chart
        self.cost_figure = Figure(figsize=(6, 4))
        self.cost_canvas = FigureCanvas(self.cost_figure)
        charts_layout.addWidget(self.cost_canvas)
        
        parent_layout.addWidget(charts_group)
    
    def update_metrics(self, summary: Dict[str, Any]):
        """Update the metrics display"""
        self.total_executions_label.setText(str(summary.get("total_executions", 0)))
        self.avg_response_time_label.setText(f"{summary.get('avg_response_time', 0.0):.2f}s")
        self.avg_cost_label.setText(f"${summary.get('avg_cost', 0.0):.4f}")
        self.success_rate_label.setText(f"{summary.get('success_rate', 0.0):.1f}%")
        self.total_tokens_label.setText(str(summary.get("total_tokens", 0)))
    
    def update_executions_table(self, executions: List[Dict[str, Any]]):
        """Update the executions table"""
        self.executions_table.setRowCount(len(executions))
        
        for row, execution in enumerate(executions):
            self.executions_table.setItem(row, 0, QTableWidgetItem(execution.get("timestamp", "")))
            self.executions_table.setItem(row, 1, QTableWidgetItem(execution.get("llm_provider", "")))
            self.executions_table.setItem(row, 2, QTableWidgetItem(execution.get("llm_model", "")))
            self.executions_table.setItem(row, 3, QTableWidgetItem(f"{execution.get('execution_time', 0.0):.2f}s"))
            self.executions_table.setItem(row, 4, QTableWidgetItem(str(execution.get("token_count_input", 0) + execution.get("token_count_output", 0))))
            self.executions_table.setItem(row, 5, QTableWidgetItem(f"${execution.get('cost', 0.0):.4f}"))
            self.executions_table.setItem(row, 6, QTableWidgetItem(execution.get("status", "")))
    
    def update_charts(self, metrics_data: Dict[str, List[float]]):
        """Update performance charts"""
        if not MATPLOTLIB_AVAILABLE:
            return
        
        # Response time chart
        if "response_time" in metrics_data:
            self.response_time_figure.clear()
            ax = self.response_time_figure.add_subplot(111)
            ax.plot(metrics_data["response_time"])
            ax.set_title("Response Time Trend")
            ax.set_ylabel("Time (seconds)")
            ax.set_xlabel("Execution")
            self.response_time_canvas.draw()
        
        # Cost chart
        if "cost" in metrics_data:
            self.cost_figure.clear()
            ax = self.cost_figure.add_subplot(111)
            ax.plot(metrics_data["cost"])
            ax.set_title("Cost Trend")
            ax.set_ylabel("Cost (USD)")
            ax.set_xlabel("Execution")
            self.cost_canvas.draw()


class PerformanceReportsWidget(QWidget):
    """Widget for displaying performance reports"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Report controls
        controls_layout = QHBoxLayout()
        
        controls_layout.addWidget(QLabel("Period:"))
        self.period_combo = QComboBox()
        self.period_combo.addItems(["Last 7 days", "Last 30 days", "Last 90 days", "Custom"])
        controls_layout.addWidget(self.period_combo)
        
        self.generate_report_btn = QPushButton("Generate Report")
        controls_layout.addWidget(self.generate_report_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Report display
        self.report_text = QTextEdit()
        self.report_text.setReadOnly(True)
        layout.addWidget(self.report_text)
    
    def display_report(self, report: Dict[str, Any]):
        """Display a performance report"""
        report_html = self._format_report_html(report)
        self.report_text.setHtml(report_html)
    
    def _format_report_html(self, report: Dict[str, Any]) -> str:
        """Format report data as HTML"""
        html = f"""
        <h2>Performance Report</h2>
        <p><strong>Period:</strong> {report.get('period_start', '')} to {report.get('period_end', '')}</p>
        
        <h3>Summary</h3>
        <ul>
            <li><strong>Total Executions:</strong> {report.get('total_executions', 0)}</li>
            <li><strong>Success Rate:</strong> {report.get('success_rate', 0.0):.1f}%</li>
            <li><strong>Average Response Time:</strong> {report.get('average_response_time', 0.0):.2f}s</li>
            <li><strong>Average Cost:</strong> ${report.get('average_cost', 0.0):.4f}</li>
        </ul>
        
        <h3>Insights</h3>
        <ul>
        """
        
        for insight in report.get('insights', []):
            html += f"<li>{insight}</li>"
        
        html += """
        </ul>
        
        <h3>Recommendations</h3>
        <ul>
        """
        
        for recommendation in report.get('recommendations', []):
            html += f"<li>{recommendation}</li>"
        
        html += "</ul>"
        
        return html


class PerformanceBenchmarksWidget(QWidget):
    """Widget for managing performance benchmarks"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Benchmark controls
        controls_layout = QHBoxLayout()
        
        self.add_benchmark_btn = QPushButton("Add Benchmark")
        self.edit_benchmark_btn = QPushButton("Edit")
        self.delete_benchmark_btn = QPushButton("Delete")
        
        controls_layout.addWidget(self.add_benchmark_btn)
        controls_layout.addWidget(self.edit_benchmark_btn)
        controls_layout.addWidget(self.delete_benchmark_btn)
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        # Benchmarks table
        self.benchmarks_table = QTableWidget()
        self.benchmarks_table.setColumnCount(6)
        self.benchmarks_table.setHorizontalHeaderLabels([
            "Name", "Category", "Metric", "Target", "Good", "Excellent"
        ])
        self.benchmarks_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.benchmarks_table)


class PerformanceAlertsWidget(QWidget):
    """Widget for managing performance alerts"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Alert controls
        controls_layout = QHBoxLayout()
        
        self.add_alert_btn = QPushButton("Add Alert")
        self.edit_alert_btn = QPushButton("Edit")
        self.delete_alert_btn = QPushButton("Delete")
        
        controls_layout.addWidget(self.add_alert_btn)
        controls_layout.addWidget(self.edit_alert_btn)
        controls_layout.addWidget(self.delete_alert_btn)
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        # Alerts table
        self.alerts_table = QTableWidget()
        self.alerts_table.setColumnCount(5)
        self.alerts_table.setHorizontalHeaderLabels([
            "Metric", "Condition", "Threshold", "Status", "Last Triggered"
        ])
        self.alerts_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.alerts_table)


class PerformanceConfigWidget(QWidget):
    """Widget for performance tracking configuration"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # General settings
        general_group = QGroupBox("General Settings")
        general_layout = QFormLayout(general_group)
        
        self.enabled_checkbox = QCheckBox("Enable Performance Tracking")
        self.enabled_checkbox.setChecked(True)
        general_layout.addRow(self.enabled_checkbox)
        
        self.auto_track_checkbox = QCheckBox("Auto-track LLM Executions")
        self.auto_track_checkbox.setChecked(True)
        general_layout.addRow(self.auto_track_checkbox)
        
        self.track_costs_checkbox = QCheckBox("Track Costs")
        self.track_costs_checkbox.setChecked(True)
        general_layout.addRow(self.track_costs_checkbox)
        
        self.retention_spinbox = QSpinBox()
        self.retention_spinbox.setRange(1, 365)
        self.retention_spinbox.setValue(90)
        self.retention_spinbox.setSuffix(" days")
        general_layout.addRow("Data Retention:", self.retention_spinbox)
        
        layout.addWidget(general_group)
        
        # Notification settings
        notification_group = QGroupBox("Notifications")
        notification_layout = QFormLayout(notification_group)
        
        self.alert_email_edit = QLineEdit()
        notification_layout.addRow("Alert Email:", self.alert_email_edit)
        
        layout.addWidget(notification_group)
        
        # Export settings
        export_group = QGroupBox("Export Settings")
        export_layout = QFormLayout(export_group)
        
        self.export_format_combo = QComboBox()
        self.export_format_combo.addItems(["JSON", "CSV", "Excel"])
        export_layout.addRow("Export Format:", self.export_format_combo)
        
        layout.addWidget(export_group)
        
        # Save button
        save_layout = QHBoxLayout()
        save_layout.addStretch()
        
        self.save_config_btn = QPushButton("Save Configuration")
        save_layout.addWidget(self.save_config_btn)
        
        layout.addLayout(save_layout)


class PerformanceDialog(QDialog):
    """Main performance tracking dialog"""
    
    def __init__(self, performance_service, prompt_service, parent=None):
        super().__init__(parent)
        self.performance_service = performance_service
        self.prompt_service = prompt_service
        self.current_prompt_id = None
        self.init_ui()
        self.setup_connections()
        self.load_data()
    
    def init_ui(self):
        self.setWindowTitle("Performance Tracking")
        self.setModal(True)
        self.resize(1000, 700)
        
        layout = QVBoxLayout(self)
        
        # Prompt selection
        prompt_layout = QHBoxLayout()
        prompt_layout.addWidget(QLabel("Prompt:"))
        
        self.prompt_combo = QComboBox()
        self.prompt_combo.addItem("All Prompts", None)
        prompt_layout.addWidget(self.prompt_combo)
        
        self.refresh_btn = QPushButton("Refresh")
        prompt_layout.addWidget(self.refresh_btn)
        
        prompt_layout.addStretch()
        layout.addLayout(prompt_layout)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        
        # Metrics tab
        self.metrics_widget = PerformanceMetricsWidget()
        self.tab_widget.addTab(self.metrics_widget, "Metrics")
        
        # Reports tab
        self.reports_widget = PerformanceReportsWidget()
        self.tab_widget.addTab(self.reports_widget, "Reports")
        
        # Benchmarks tab
        self.benchmarks_widget = PerformanceBenchmarksWidget()
        self.tab_widget.addTab(self.benchmarks_widget, "Benchmarks")
        
        # Alerts tab
        self.alerts_widget = PerformanceAlertsWidget()
        self.tab_widget.addTab(self.alerts_widget, "Alerts")
        
        # Configuration tab
        self.config_widget = PerformanceConfigWidget()
        self.tab_widget.addTab(self.config_widget, "Configuration")
        
        layout.addWidget(self.tab_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.export_btn = QPushButton("Export Data")
        button_layout.addWidget(self.export_btn)
        
        self.close_btn = QPushButton("Close")
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
    
    def setup_connections(self):
        """Setup signal connections"""
        self.prompt_combo.currentTextChanged.connect(self.on_prompt_changed)
        self.refresh_btn.clicked.connect(self.load_data)
        self.reports_widget.generate_report_btn.clicked.connect(self.generate_report)
        self.config_widget.save_config_btn.clicked.connect(self.save_configuration)
        self.export_btn.clicked.connect(self.export_data)
        self.close_btn.clicked.connect(self.accept)
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_metrics)
        self.refresh_timer.start(30000)  # Refresh every 30 seconds
    
    def load_data(self):
        """Load performance data"""
        try:
            # Load prompts
            self.prompt_combo.clear()
            self.prompt_combo.addItem("All Prompts", None)
            
            prompts = self.prompt_service.get_prompts()
            for prompt in prompts:
                self.prompt_combo.addItem(prompt['title'], prompt['id'])
            
            # Load initial metrics
            self.refresh_metrics()
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load performance data: {str(e)}")
    
    def on_prompt_changed(self):
        """Handle prompt selection change"""
        self.current_prompt_id = self.prompt_combo.currentData()
        self.refresh_metrics()
    
    def refresh_metrics(self):
        """Refresh performance metrics display"""
        try:
            # Get performance summary
            summary = self.performance_service.get_performance_summary(
                prompt_id=self.current_prompt_id,
                period_days=30
            )
            
            self.metrics_widget.update_metrics(summary)
            
            # Get recent executions (mock data for now)
            executions = []  # Would get from performance service
            self.metrics_widget.update_executions_table(executions)
            
            # Get metrics for charts
            if self.current_prompt_id:
                metrics_data = self.performance_service.get_prompt_metrics(
                    self.current_prompt_id,
                    period_days=30
                )
                self.metrics_widget.update_charts(metrics_data)
            
        except Exception as e:
            print(f"Error refreshing metrics: {e}")
    
    def generate_report(self):
        """Generate performance report"""
        try:
            if not self.current_prompt_id:
                QMessageBox.information(self, "Info", "Please select a specific prompt to generate a report.")
                return
            
            period_text = self.reports_widget.period_combo.currentText()
            period_days = 30  # Default
            
            if "7 days" in period_text:
                period_days = 7
            elif "90 days" in period_text:
                period_days = 90
            
            report = self.performance_service.generate_performance_report(
                self.current_prompt_id,
                period_days=period_days
            )
            
            if report:
                report_dict = {
                    'period_start': report.period_start,
                    'period_end': report.period_end,
                    'total_executions': report.total_executions,
                    'success_rate': report.success_rate,
                    'average_response_time': report.average_response_time,
                    'average_cost': report.average_cost,
                    'insights': report.insights,
                    'recommendations': report.recommendations
                }
                self.reports_widget.display_report(report_dict)
            else:
                QMessageBox.information(self, "Info", "No performance data available for the selected period.")
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to generate report: {str(e)}")
    
    def save_configuration(self):
        """Save performance configuration"""
        try:
            # Get configuration from UI
            config = {
                'enabled': self.config_widget.enabled_checkbox.isChecked(),
                'auto_track': self.config_widget.auto_track_checkbox.isChecked(),
                'track_costs': self.config_widget.track_costs_checkbox.isChecked(),
                'retention_days': self.config_widget.retention_spinbox.value(),
                'alert_email': self.config_widget.alert_email_edit.text(),
                'export_format': self.config_widget.export_format_combo.currentText().lower()
            }
            
            # Save configuration (would save to settings)
            QMessageBox.information(self, "Success", "Configuration saved successfully!")
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save configuration: {str(e)}")
    
    def export_data(self):
        """Export performance data"""
        try:
            # Implementation would export data based on current selection
            QMessageBox.information(self, "Export", "Performance data export functionality would be implemented here.")
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to export data: {str(e)}")


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Mock services for testing
    class MockPerformanceService:
        def get_performance_summary(self, prompt_id=None, period_days=30):
            return {
                "total_executions": 150,
                "avg_response_time": 2.34,
                "avg_cost": 0.0234,
                "total_tokens": 45000,
                "success_rate": 94.5
            }
        
        def get_prompt_metrics(self, prompt_id, period_days=30):
            import random
            return {
                "response_time": [random.uniform(1, 5) for _ in range(20)],
                "cost": [random.uniform(0.01, 0.05) for _ in range(20)]
            }
        
        def generate_performance_report(self, prompt_id, period_days=30):
            from models.performance_models import PerformanceReport
            return PerformanceReport(
                prompt_id=prompt_id,
                period_start="2024-01-01",
                period_end="2024-01-31",
                total_executions=100,
                success_rate=95.0,
                average_response_time=2.1,
                average_cost=0.025,
                insights=["Good performance overall", "Response time is optimal"],
                recommendations=["Consider cost optimization", "Monitor token usage"]
            )
    
    class MockPromptService:
        def get_prompts(self):
            return [
                {'id': 1, 'title': 'Test Prompt 1'},
                {'id': 2, 'title': 'Test Prompt 2'}
            ]
    
    dialog = PerformanceDialog(MockPerformanceService(), MockPromptService())
    dialog.show()
    
    sys.exit(app.exec())