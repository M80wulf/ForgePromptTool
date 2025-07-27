"""
LLM-powered features dialog for the Prompt Organizer application
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QTextEdit, QPushButton, QComboBox, QProgressBar,
    QDialogButtonBox, QGroupBox, QFormLayout, QSpinBox,
    QMessageBox, QSplitter, QListWidget, QListWidgetItem,
    QCheckBox, QSlider, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QTextCharFormat, QColor
import json
from typing import Dict, List, Optional

from services.llm_service import LLMService, create_llm_service
from config.settings import get_settings


class LLMWorkerThread(QThread):
    """Worker thread for LLM operations to prevent UI blocking"""
    
    result_ready = pyqtSignal(str, object)  # operation_type, result (can be str or list)
    error_occurred = pyqtSignal(str, str)  # operation_type, error_message
    progress_updated = pyqtSignal(int)  # progress percentage
    
    def __init__(self, llm_service: LLMService, operation: str, prompt: str, **kwargs):
        super().__init__()
        self.llm_service = llm_service
        self.operation = operation
        self.prompt = prompt
        self.kwargs = kwargs
    
    def run(self):
        """Execute LLM operation in background thread"""
        try:
            self.progress_updated.emit(25)
            
            if self.operation == "rewrite":
                style = self.kwargs.get('style', 'clear')
                result = self.llm_service.rewrite_prompt(self.prompt, style)
            elif self.operation == "explain":
                result = self.llm_service.explain_prompt(self.prompt)
            elif self.operation == "improve":
                result = self.llm_service.suggest_improvements(self.prompt)
            elif self.operation == "auto_tag":
                result = self.llm_service.generate_tags(self.prompt)
            else:
                raise ValueError(f"Unknown operation: {self.operation}")
            
            self.progress_updated.emit(100)
            self.result_ready.emit(self.operation, result)
            
        except Exception as e:
            self.error_occurred.emit(self.operation, str(e))


class LLMFeaturesDialog(QDialog):
    """Dialog for LLM-powered prompt operations"""
    
    def __init__(self, prompt_content: str = "", parent=None):
        super().__init__(parent)
        self.prompt_content = prompt_content
        self.settings = get_settings()
        self.llm_service = None
        self.worker_thread = None
        
        self.setWindowTitle("LLM-Powered Features")
        self.setModal(True)
        self.resize(900, 700)
        
        self.setup_ui()
        self.setup_llm_service()
    
    def setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout()
        
        # Status and connection info
        status_group = QGroupBox("LLM Status")
        status_layout = QHBoxLayout()
        
        self.status_label = QLabel("Checking connection...")
        status_layout.addWidget(self.status_label)
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.setup_llm_service)
        status_layout.addWidget(self.refresh_btn)
        
        status_layout.addStretch()
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # Main content splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Input and operations
        left_panel = self.setup_left_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - Results
        right_panel = self.setup_right_panel()
        splitter.addWidget(right_panel)
        
        splitter.setSizes([400, 500])
        layout.addWidget(splitter)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Dialog buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def setup_left_panel(self) -> QWidget:
        """Setup the left panel with input and operations"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Input prompt
        input_group = QGroupBox("Input Prompt")
        input_layout = QVBoxLayout()
        
        self.input_text = QTextEdit()
        self.input_text.setPlainText(self.prompt_content)
        self.input_text.setFont(QFont("Consolas", 10))
        self.input_text.setMaximumHeight(200)
        input_layout.addWidget(self.input_text)
        
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        # Operations
        operations_group = QGroupBox("LLM Operations")
        operations_layout = QVBoxLayout()
        
        # Rewrite section
        rewrite_frame = QFrame()
        rewrite_frame.setFrameStyle(QFrame.Shape.Box)
        rewrite_layout = QVBoxLayout()
        
        rewrite_layout.addWidget(QLabel("Rewrite Prompt:"))
        
        style_layout = QHBoxLayout()
        style_layout.addWidget(QLabel("Style:"))
        
        self.style_combo = QComboBox()
        self.style_combo.addItems([
            "clear", "concise", "detailed", "creative", 
            "professional", "casual", "technical"
        ])
        style_layout.addWidget(self.style_combo)
        style_layout.addStretch()
        
        rewrite_layout.addLayout(style_layout)
        
        self.rewrite_btn = QPushButton("Rewrite Prompt")
        self.rewrite_btn.clicked.connect(self.rewrite_prompt)
        rewrite_layout.addWidget(self.rewrite_btn)
        
        rewrite_frame.setLayout(rewrite_layout)
        operations_layout.addWidget(rewrite_frame)
        
        # Other operations
        self.explain_btn = QPushButton("Explain Prompt")
        self.explain_btn.clicked.connect(self.explain_prompt)
        operations_layout.addWidget(self.explain_btn)
        
        self.improve_btn = QPushButton("Suggest Improvements")
        self.improve_btn.clicked.connect(self.improve_prompt)
        operations_layout.addWidget(self.improve_btn)
        
        self.auto_tag_btn = QPushButton("Generate Tags")
        self.auto_tag_btn.clicked.connect(self.auto_tag_prompt)
        operations_layout.addWidget(self.auto_tag_btn)
        
        operations_group.setLayout(operations_layout)
        layout.addWidget(operations_group)
        
        # Settings
        settings_group = QGroupBox("Settings")
        settings_layout = QFormLayout()
        
        self.temperature_slider = QSlider(Qt.Orientation.Horizontal)
        self.temperature_slider.setRange(1, 20)
        self.temperature_slider.setValue(7)
        self.temperature_label = QLabel("0.7")
        self.temperature_slider.valueChanged.connect(
            lambda v: self.temperature_label.setText(f"{v/10:.1f}")
        )
        
        temp_layout = QHBoxLayout()
        temp_layout.addWidget(self.temperature_slider)
        temp_layout.addWidget(self.temperature_label)
        
        settings_layout.addRow("Temperature:", temp_layout)
        
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(50, 2000)
        self.max_tokens_spin.setValue(500)
        settings_layout.addRow("Max Tokens:", self.max_tokens_spin)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        layout.addStretch()
        panel.setLayout(layout)
        return panel
    
    def setup_right_panel(self) -> QWidget:
        """Setup the right panel with results"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Results tabs
        self.results_tabs = QTabWidget()
        
        # Rewritten prompt tab
        self.rewrite_result = QTextEdit()
        self.rewrite_result.setFont(QFont("Consolas", 10))
        self.rewrite_result.setReadOnly(True)
        self.results_tabs.addTab(self.rewrite_result, "Rewritten")
        
        # Explanation tab
        self.explain_result = QTextEdit()
        self.explain_result.setFont(QFont("Segoe UI", 10))
        self.explain_result.setReadOnly(True)
        self.results_tabs.addTab(self.explain_result, "Explanation")
        
        # Improvements tab
        self.improve_result = QListWidget()
        self.results_tabs.addTab(self.improve_result, "Improvements")
        
        # Tags tab
        self.tags_result = QListWidget()
        self.results_tabs.addTab(self.tags_result, "Generated Tags")
        
        layout.addWidget(self.results_tabs)
        
        # Result actions
        actions_layout = QHBoxLayout()
        
        self.copy_result_btn = QPushButton("Copy Result")
        self.copy_result_btn.clicked.connect(self.copy_current_result)
        actions_layout.addWidget(self.copy_result_btn)
        
        self.apply_result_btn = QPushButton("Apply to Prompt")
        self.apply_result_btn.clicked.connect(self.apply_current_result)
        actions_layout.addWidget(self.apply_result_btn)
        
        actions_layout.addStretch()
        layout.addLayout(actions_layout)
        
        panel.setLayout(layout)
        return panel
    
    def setup_llm_service(self):
        """Setup LLM service based on current settings"""
        try:
            config = self.settings.get_config()
            llm_config = config.llm
            
            print(f"[DEBUG] LLM Config - Enabled: {llm_config.enabled}")
            print(f"[DEBUG] LLM Config - Provider: {llm_config.provider}")
            
            if not llm_config.enabled:
                print("[DEBUG] LLM integration disabled in settings")
                self.status_label.setText("❌ LLM integration disabled in settings")
                self.set_buttons_enabled(False)
                return
            
            # Create LLM service configuration
            service_config = {
                'active_provider': llm_config.provider
            }
            
            if llm_config.provider == 'local':
                print(f"[DEBUG] Setting up local provider - URL: {llm_config.local_base_url}, Model: {llm_config.local_model}")
                service_config['local_llm'] = {
                    'enabled': True,
                    'base_url': llm_config.local_base_url,
                    'model': llm_config.local_model
                }
            elif llm_config.provider == 'lmstudio':
                print(f"[DEBUG] Setting up LM Studio provider - URL: {llm_config.lmstudio_base_url}, Model: {llm_config.lmstudio_model}")
                service_config['local_llm'] = {
                    'enabled': True,
                    'base_url': llm_config.lmstudio_base_url,
                    'model': llm_config.lmstudio_model
                }
            elif llm_config.provider == 'openai':
                print(f"[DEBUG] Setting up OpenAI provider - Model: {llm_config.openai_model}")
                service_config['openai'] = {
                    'enabled': True,
                    'api_key': llm_config.openai_api_key,
                    'model': llm_config.openai_model
                }
            
            print(f"[DEBUG] Service config: {service_config}")
            self.llm_service = create_llm_service(service_config)
            print(f"[DEBUG] LLM service created. Available: {self.llm_service.is_available()}")
            print(f"[DEBUG] Active provider: {self.llm_service.active_provider}")
            print(f"[DEBUG] Available providers: {self.llm_service.get_provider_names()}")
            
            if self.llm_service.is_available():
                provider_name = llm_config.provider.upper()
                self.status_label.setText(f"✅ Connected to {provider_name}")
                self.set_buttons_enabled(True)
                print(f"[DEBUG] Successfully connected to {provider_name}")
            else:
                self.status_label.setText("❌ No LLM provider available")
                self.set_buttons_enabled(False)
                print("[DEBUG] No LLM provider available")
                
        except Exception as e:
            print(f"[DEBUG] Exception in setup_llm_service: {str(e)}")
            import traceback
            traceback.print_exc()
            self.status_label.setText(f"❌ Connection error: {str(e)}")
            self.set_buttons_enabled(False)
    
    def set_buttons_enabled(self, enabled: bool):
        """Enable/disable operation buttons"""
        self.rewrite_btn.setEnabled(enabled)
        self.explain_btn.setEnabled(enabled)
        self.improve_btn.setEnabled(enabled)
        self.auto_tag_btn.setEnabled(enabled)
    
    def start_llm_operation(self, operation: str, **kwargs):
        """Start an LLM operation in background thread"""
        if not self.llm_service or not self.llm_service.is_available():
            QMessageBox.warning(
                self, "LLM Not Available",
                "LLM service is not available. Please check your settings and ensure:\n"
                "• LLM integration is enabled\n"
                "• Provider is properly configured\n"
                "• Connection test passes"
            )
            return
        
        prompt = self.input_text.toPlainText().strip()
        if not prompt:
            QMessageBox.warning(
                self, "No Input",
                "Please enter a prompt in the input field before running LLM operations."
            )
            return
        
        # Show operation starting message
        operation_names = {
            "rewrite": "Rewriting prompt",
            "explain": "Explaining prompt",
            "improve": "Generating improvements",
            "auto_tag": "Generating tags"
        }
        operation_name = operation_names.get(operation, f"Running {operation}")
        
        # Disable buttons during operation
        self.set_buttons_enabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Update status
        self.status_label.setText(f"🔄 {operation_name}...")
        
        # Start worker thread
        self.worker_thread = LLMWorkerThread(
            self.llm_service, operation, prompt, **kwargs
        )
        self.worker_thread.result_ready.connect(self.on_result_ready)
        self.worker_thread.error_occurred.connect(self.on_error_occurred)
        self.worker_thread.progress_updated.connect(self.progress_bar.setValue)
        self.worker_thread.finished.connect(self.on_operation_finished)
        self.worker_thread.start()
    
    def on_result_ready(self, operation: str, result):
        """Handle successful LLM operation result"""
        operation_names = {
            "rewrite": "Prompt rewritten successfully",
            "explain": "Prompt explanation generated",
            "improve": "Improvements generated",
            "auto_tag": "Tags generated"
        }
        
        if operation == "rewrite":
            # Result should be a string
            result_text = str(result) if not isinstance(result, str) else result
            if result_text.strip():
                self.rewrite_result.setPlainText(result_text)
                self.results_tabs.setCurrentIndex(0)
                # Show success message temporarily
                self.status_label.setText(f"✅ {operation_names[operation]}")
            else:
                self.status_label.setText("⚠️ Rewrite completed but result is empty")
                
        elif operation == "explain":
            # Result should be a string
            result_text = str(result) if not isinstance(result, str) else result
            if result_text.strip():
                self.explain_result.setPlainText(result_text)
                self.results_tabs.setCurrentIndex(1)
                self.status_label.setText(f"✅ {operation_names[operation]}")
            else:
                self.status_label.setText("⚠️ Explanation completed but result is empty")
                
        elif operation == "improve":
            self.improve_result.clear()
            items_added = 0
            
            if isinstance(result, list):
                for improvement in result:
                    if improvement and improvement.strip():
                        item = QListWidgetItem(f"• {improvement}")
                        self.improve_result.addItem(item)
                        items_added += 1
            else:
                # Handle string result by splitting into lines
                result_text = str(result)
                lines = result_text.strip().split('\n')
                for line in lines:
                    if line.strip():
                        item = QListWidgetItem(f"• {line.strip()}")
                        self.improve_result.addItem(item)
                        items_added += 1
            
            if items_added > 0:
                self.results_tabs.setCurrentIndex(2)
                self.status_label.setText(f"✅ {items_added} improvements generated")
            else:
                self.status_label.setText("⚠️ No improvements generated")
                
        elif operation == "auto_tag":
            self.tags_result.clear()
            items_added = 0
            
            if isinstance(result, list):
                for tag in result:
                    if tag and tag.strip():
                        item = QListWidgetItem(f"#{tag}")
                        self.tags_result.addItem(item)
                        items_added += 1
            else:
                # Handle string result by splitting into words/tags
                result_text = str(result)
                # Try to extract tags from text
                words = result_text.replace(',', ' ').replace(';', ' ').split()
                tags = [word.strip('[]"\'.,;:!?#').lower() for word in words
                       if len(word.strip('[]"\'.,;:!?#')) > 2]
                for tag in tags[:7]:  # Limit to 7 tags
                    if tag:
                        item = QListWidgetItem(f"#{tag}")
                        self.tags_result.addItem(item)
                        items_added += 1
            
            if items_added > 0:
                self.results_tabs.setCurrentIndex(3)
                self.status_label.setText(f"✅ {items_added} tags generated")
            else:
                self.status_label.setText("⚠️ No tags generated")
    
    def on_error_occurred(self, operation: str, error_message: str):
        """Handle LLM operation error"""
        QMessageBox.critical(
            self, "LLM Error", 
            f"Error in {operation} operation:\n{error_message}"
        )
    
    def on_operation_finished(self):
        """Handle operation completion"""
        self.progress_bar.setVisible(False)
        self.set_buttons_enabled(True)
        
        # Restore status to connection info
        if self.llm_service and self.llm_service.is_available():
            config = self.settings.get_config()
            provider_name = config.llm.provider.upper()
            self.status_label.setText(f"✅ Connected to {provider_name}")
        else:
            self.status_label.setText("❌ No LLM provider available")
        
        if self.worker_thread:
            self.worker_thread.deleteLater()
            self.worker_thread = None
    
    # Operation methods
    def rewrite_prompt(self):
        """Rewrite the prompt with selected style"""
        style = self.style_combo.currentText()
        self.start_llm_operation("rewrite", style=style)
    
    def explain_prompt(self):
        """Explain what the prompt does"""
        self.start_llm_operation("explain")
    
    def improve_prompt(self):
        """Get improvement suggestions"""
        self.start_llm_operation("improve")
    
    def auto_tag_prompt(self):
        """Generate tags for the prompt"""
        self.start_llm_operation("auto_tag")
    
    def copy_current_result(self):
        """Copy current tab result to clipboard"""
        current_index = self.results_tabs.currentIndex()
        
        if current_index == 0:  # Rewritten
            content = self.rewrite_result.toPlainText()
        elif current_index == 1:  # Explanation
            content = self.explain_result.toPlainText()
        elif current_index == 2:  # Improvements
            items = []
            for i in range(self.improve_result.count()):
                items.append(self.improve_result.item(i).text())
            content = "\n".join(items)
        elif current_index == 3:  # Tags
            items = []
            for i in range(self.tags_result.count()):
                items.append(self.tags_result.item(i).text())
            content = " ".join(items)
        else:
            content = ""
        
        if content:
            from PyQt6.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            clipboard.setText(content)
            QMessageBox.information(self, "Success", "Result copied to clipboard")
    
    def apply_current_result(self):
        """Apply current result to input prompt"""
        current_index = self.results_tabs.currentIndex()
        
        if current_index == 0:  # Rewritten
            content = self.rewrite_result.toPlainText()
            if content:
                self.input_text.setPlainText(content)
                QMessageBox.information(self, "Success", "Rewritten prompt applied to input")
        else:
            QMessageBox.information(self, "Info", "Only rewritten prompts can be applied to input")
    
    def get_current_prompt(self) -> str:
        """Get the current prompt content"""
        return self.input_text.toPlainText()
    
    def closeEvent(self, event):
        """Handle dialog close"""
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.terminate()
            self.worker_thread.wait()
        event.accept()