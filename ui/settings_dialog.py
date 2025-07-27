"""
Settings/Preferences dialog for the Prompt Organizer application
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QLineEdit, QPushButton, QCheckBox, QComboBox,
    QSpinBox, QSlider, QGroupBox, QFormLayout, QGridLayout,
    QColorDialog, QFontDialog, QFileDialog, QTextEdit,
    QDialogButtonBox, QListWidget, QListWidgetItem, QSplitter,
    QScrollArea, QFrame, QButtonGroup, QRadioButton, QProgressBar,
    QMessageBox, QTreeWidget, QTreeWidgetItem, QTableWidget,
    QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor, QPalette, QPixmap, QPainter
import json
import os
from typing import Dict, Any, Optional

from config.settings import get_settings, SettingsManager
from ui.themes import get_theme_manager, Theme, ThemeColors
from services.llm_service import LLMService


class ColorButton(QPushButton):
    """Custom button for color selection"""
    
    color_changed = pyqtSignal(str)
    
    def __init__(self, color: str = "#ffffff", parent=None):
        super().__init__(parent)
        self.current_color = color
        self.setFixedSize(40, 30)
        self.clicked.connect(self.choose_color)
        self.update_button()
    
    def update_button(self):
        """Update button appearance with current color"""
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.current_color};
                border: 2px solid #ccc;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                border-color: #999;
            }}
        """)
    
    def choose_color(self):
        """Open color chooser dialog"""
        color = QColorDialog.getColor(QColor(self.current_color), self)
        if color.isValid():
            self.current_color = color.name()
            self.update_button()
            self.color_changed.emit(self.current_color)
    
    def set_color(self, color: str):
        """Set color programmatically"""
        self.current_color = color
        self.update_button()


class ThemePreviewWidget(QWidget):
    """Widget to preview theme appearance"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(300, 200)
        self.theme = None
        self.setup_ui()
    
    def setup_ui(self):
        """Setup preview UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Title bar mockup
        title_bar = QFrame()
        title_bar.setFixedHeight(30)
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(8, 4, 8, 4)
        
        title_label = QLabel("Prompt Organizer")
        title_label.setObjectName("preview_title")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # Window controls mockup
        for color in ["#ff5f57", "#ffbd2e", "#28ca42"]:
            btn = QPushButton()
            btn.setFixedSize(12, 12)
            btn.setStyleSheet(f"background-color: {color}; border-radius: 6px;")
            title_layout.addWidget(btn)
        
        title_bar.setLayout(title_layout)
        layout.addWidget(title_bar)
        
        # Content area mockup
        content = QFrame()
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(4, 4, 4, 4)
        
        # Left panel
        left_panel = QFrame()
        left_panel.setFixedWidth(80)
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(4, 4, 4, 4)
        
        folders_label = QLabel("Folders")
        folders_label.setObjectName("preview_section")
        left_layout.addWidget(folders_label)
        
        for folder in ["📁 Work", "📁 Personal", "📁 Templates"]:
            folder_label = QLabel(folder)
            folder_label.setObjectName("preview_item")
            left_layout.addWidget(folder_label)
        
        left_layout.addStretch()
        left_panel.setLayout(left_layout)
        content_layout.addWidget(left_panel)
        
        # Right panel
        right_panel = QFrame()
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(4, 4, 4, 4)
        
        editor_label = QLabel("Editor")
        editor_label.setObjectName("preview_section")
        right_layout.addWidget(editor_label)
        
        editor_text = QLabel("# Sample Prompt\n\nThis is a **sample** prompt with `code` and {variables}.")
        editor_text.setObjectName("preview_editor")
        editor_text.setWordWrap(True)
        right_layout.addWidget(editor_text)
        
        right_layout.addStretch()
        right_panel.setLayout(right_layout)
        content_layout.addWidget(right_panel)
        
        content.setLayout(content_layout)
        layout.addWidget(content)
        
        self.setLayout(layout)
    
    def set_theme(self, theme: Theme):
        """Apply theme to preview"""
        self.theme = theme
        colors = theme.colors
        
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {colors.background};
                color: {colors.text_primary};
                font-family: {theme.font_family};
                font-size: {theme.font_size}pt;
            }}
            
            QFrame {{
                background-color: {colors.surface};
                border: 1px solid {colors.border};
                border-radius: 4px;
            }}
            
            #preview_title {{
                font-weight: bold;
                color: {colors.text_primary};
            }}
            
            #preview_section {{
                font-weight: bold;
                color: {colors.text_primary};
                margin-bottom: 4px;
            }}
            
            #preview_item {{
                color: {colors.text_secondary};
                margin-left: 8px;
                margin-bottom: 2px;
            }}
            
            #preview_editor {{
                background-color: {colors.editor_background};
                color: {colors.editor_text};
                padding: 8px;
                border: 1px solid {colors.border};
                border-radius: 4px;
            }}
        """)


class AppearanceTab(QWidget):
    """Appearance settings tab"""
    
    def __init__(self, settings: SettingsManager, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.theme_manager = get_theme_manager()
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        """Setup appearance tab UI"""
        layout = QVBoxLayout()
        
        # Theme selection
        theme_group = QGroupBox("Theme")
        theme_layout = QVBoxLayout()
        
        # Theme selector
        theme_selector_layout = QHBoxLayout()
        theme_selector_layout.addWidget(QLabel("Theme:"))
        
        self.theme_combo = QComboBox()
        theme_names = self.theme_manager.get_theme_display_names()
        for name, display_name in theme_names.items():
            self.theme_combo.addItem(display_name, name)
        self.theme_combo.currentTextChanged.connect(self.on_theme_changed)
        theme_selector_layout.addWidget(self.theme_combo)
        theme_selector_layout.addStretch()
        
        theme_layout.addLayout(theme_selector_layout)
        
        # Theme preview and customization
        preview_layout = QHBoxLayout()
        
        # Preview
        preview_group = QGroupBox("Preview")
        preview_group_layout = QVBoxLayout()
        self.theme_preview = ThemePreviewWidget()
        preview_group_layout.addWidget(self.theme_preview)
        preview_group.setLayout(preview_group_layout)
        preview_layout.addWidget(preview_group)
        
        # Custom theme editor
        custom_group = QGroupBox("Customize")
        custom_layout = QFormLayout()
        
        # Color customization
        self.primary_color_btn = ColorButton()
        self.primary_color_btn.color_changed.connect(self.on_color_changed)
        custom_layout.addRow("Primary Color:", self.primary_color_btn)
        
        self.background_color_btn = ColorButton()
        self.background_color_btn.color_changed.connect(self.on_color_changed)
        custom_layout.addRow("Background:", self.background_color_btn)
        
        self.text_color_btn = ColorButton()
        self.text_color_btn.color_changed.connect(self.on_color_changed)
        custom_layout.addRow("Text Color:", self.text_color_btn)
        
        # Font customization
        self.font_combo = QComboBox()
        self.font_combo.addItems(["Segoe UI", "Arial", "Helvetica", "Consolas", "Courier New"])
        self.font_combo.currentTextChanged.connect(self.on_font_changed)
        custom_layout.addRow("Font Family:", self.font_combo)
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.valueChanged.connect(self.on_font_changed)
        custom_layout.addRow("Font Size:", self.font_size_spin)
        
        # Theme actions
        theme_actions_layout = QHBoxLayout()
        
        self.save_theme_btn = QPushButton("Save as Custom")
        self.save_theme_btn.clicked.connect(self.save_custom_theme)
        theme_actions_layout.addWidget(self.save_theme_btn)
        
        self.reset_theme_btn = QPushButton("Reset to Default")
        self.reset_theme_btn.clicked.connect(self.reset_theme)
        theme_actions_layout.addWidget(self.reset_theme_btn)
        
        custom_layout.addRow(theme_actions_layout)
        custom_group.setLayout(custom_layout)
        preview_layout.addWidget(custom_group)
        
        theme_layout.addLayout(preview_layout)
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)
        
        # Additional appearance options
        options_group = QGroupBox("Options")
        options_layout = QFormLayout()
        
        self.show_line_numbers_cb = QCheckBox()
        options_layout.addRow("Show Line Numbers:", self.show_line_numbers_cb)
        
        self.word_wrap_cb = QCheckBox()
        options_layout.addRow("Word Wrap:", self.word_wrap_cb)
        
        self.transparency_slider = QSlider(Qt.Orientation.Horizontal)
        self.transparency_slider.setRange(70, 100)
        self.transparency_slider.setValue(100)
        options_layout.addRow("Window Opacity:", self.transparency_slider)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def load_settings(self):
        """Load current settings"""
        config = self.settings.get_config()
        
        # Set theme
        current_theme = self.theme_manager.current_theme_name
        index = self.theme_combo.findData(current_theme)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)
        
        # Set UI options
        self.show_line_numbers_cb.setChecked(config.ui.show_line_numbers)
        self.word_wrap_cb.setChecked(config.ui.word_wrap)
        
        # Update preview
        self.update_preview()
    
    def on_theme_changed(self):
        """Handle theme change"""
        theme_name = self.theme_combo.currentData()
        if theme_name:
            self.theme_manager.set_theme(theme_name)
            self.update_preview()
            self.update_color_buttons()
    
    def on_color_changed(self):
        """Handle color change"""
        # This would update a custom theme
        pass
    
    def on_font_changed(self):
        """Handle font change"""
        # This would update a custom theme
        pass
    
    def update_preview(self):
        """Update theme preview"""
        current_theme = self.theme_manager.get_current_theme()
        self.theme_preview.set_theme(current_theme)
    
    def update_color_buttons(self):
        """Update color buttons with current theme colors"""
        theme = self.theme_manager.get_current_theme()
        colors = theme.colors
        
        self.primary_color_btn.set_color(colors.primary)
        self.background_color_btn.set_color(colors.background)
        self.text_color_btn.set_color(colors.text_primary)
        
        self.font_combo.setCurrentText(theme.font_family)
        self.font_size_spin.setValue(theme.font_size)
    
    def save_custom_theme(self):
        """Save current customizations as a custom theme"""
        # Implementation for saving custom themes
        pass
    
    def reset_theme(self):
        """Reset theme to default"""
        self.theme_combo.setCurrentIndex(0)  # Light theme
        self.on_theme_changed()
    
    def save_settings(self):
        """Save appearance settings"""
        self.settings.update_ui_config(
            show_line_numbers=self.show_line_numbers_cb.isChecked(),
            word_wrap=self.word_wrap_cb.isChecked()
        )


class LLMTab(QWidget):
    """LLM integration settings tab"""
    
    def __init__(self, settings: SettingsManager, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        """Setup LLM tab UI"""
        layout = QVBoxLayout()
        
        # Enable LLM
        self.enable_llm_cb = QCheckBox("Enable LLM Integration")
        self.enable_llm_cb.stateChanged.connect(self.on_enable_changed)
        layout.addWidget(self.enable_llm_cb)
        
        # Provider selection
        provider_group = QGroupBox("Provider Configuration")
        provider_layout = QVBoxLayout()
        
        # Provider selector
        provider_selector_layout = QHBoxLayout()
        provider_selector_layout.addWidget(QLabel("Provider:"))
        
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["Local LLM (Ollama)", "LM Studio", "OpenAI", "Anthropic", "Custom API"])
        self.provider_combo.currentTextChanged.connect(self.on_provider_changed)
        provider_selector_layout.addWidget(self.provider_combo)
        provider_selector_layout.addStretch()
        
        provider_layout.addLayout(provider_selector_layout)
        
        # Provider-specific settings
        self.provider_stack = QTabWidget()
        
        # Local LLM settings
        local_tab = QWidget()
        local_layout = QFormLayout()
        
        self.local_url_edit = QLineEdit("http://localhost:11434")
        local_layout.addRow("Base URL:", self.local_url_edit)
        
        self.local_model_combo = QComboBox()
        self.local_model_combo.setEditable(True)
        self.local_model_combo.addItems(["llama2", "codellama", "mistral", "neural-chat"])
        local_layout.addRow("Model:", self.local_model_combo)
        
        self.test_local_btn = QPushButton("Test Connection")
        self.test_local_btn.clicked.connect(self.test_local_connection)
        local_layout.addRow(self.test_local_btn)
        
        local_tab.setLayout(local_layout)
        self.provider_stack.addTab(local_tab, "Local LLM")
        
        # OpenAI settings
        openai_tab = QWidget()
        openai_layout = QFormLayout()
        
        self.openai_key_edit = QLineEdit()
        self.openai_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        openai_layout.addRow("API Key:", self.openai_key_edit)
        
        self.openai_model_combo = QComboBox()
        self.openai_model_combo.addItems(["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"])
        openai_layout.addRow("Model:", self.openai_model_combo)
        
        self.test_openai_btn = QPushButton("Test Connection")
        self.test_openai_btn.clicked.connect(self.test_openai_connection)
        openai_layout.addRow(self.test_openai_btn)
        
        openai_tab.setLayout(openai_layout)
        self.provider_stack.addTab(openai_tab, "OpenAI")
        
        provider_layout.addWidget(self.provider_stack)
        provider_group.setLayout(provider_layout)
        layout.addWidget(provider_group)
        
        # LLM Features
        features_group = QGroupBox("Features")
        features_layout = QVBoxLayout()
        
        self.auto_tag_cb = QCheckBox("Auto-generate tags for new prompts")
        features_layout.addWidget(self.auto_tag_cb)
        
        self.quality_score_cb = QCheckBox("Show prompt quality scores")
        features_layout.addWidget(self.quality_score_cb)
        
        self.suggestions_cb = QCheckBox("Show improvement suggestions")
        features_layout.addWidget(self.suggestions_cb)
        
        features_group.setLayout(features_layout)
        layout.addWidget(features_group)
        
        # Usage and Limits
        usage_group = QGroupBox("Usage & Limits")
        usage_layout = QFormLayout()
        
        self.max_requests_spin = QSpinBox()
        self.max_requests_spin.setRange(1, 1000)
        self.max_requests_spin.setValue(100)
        usage_layout.addRow("Max requests per hour:", self.max_requests_spin)
        
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(5, 120)
        self.timeout_spin.setValue(30)
        self.timeout_spin.setSuffix(" seconds")
        usage_layout.addRow("Request timeout:", self.timeout_spin)
        
        usage_group.setLayout(usage_layout)
        layout.addWidget(usage_group)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def load_settings(self):
        """Load LLM settings"""
        config = self.settings.get_config()
        llm_config = config.llm
        
        self.enable_llm_cb.setChecked(llm_config.enabled)
        
        # Set provider
        provider_map = {
            "local": 0,
            "lmstudio": 1,
            "openai": 2,
            "anthropic": 3,
            "custom": 4
        }
        self.provider_combo.setCurrentIndex(provider_map.get(llm_config.provider, 0))
        
        # Load provider-specific settings
        self.local_url_edit.setText(llm_config.local_base_url)
        self.local_model_combo.setCurrentText(llm_config.local_model)
        self.openai_key_edit.setText(llm_config.openai_api_key)
        self.openai_model_combo.setCurrentText(llm_config.openai_model)
        
        self.on_enable_changed()
    
    def on_enable_changed(self):
        """Handle enable/disable LLM"""
        enabled = self.enable_llm_cb.isChecked()
        self.provider_stack.setEnabled(enabled)
    
    def on_provider_changed(self):
        """Handle provider change"""
        provider_text = self.provider_combo.currentText()
        if "Local" in provider_text or "LM Studio" in provider_text:
            self.provider_stack.setCurrentIndex(0)
        elif "OpenAI" in provider_text:
            self.provider_stack.setCurrentIndex(1)
    
    def test_local_connection(self):
        """Test local LLM connection"""
        try:
            import requests
            
            # Get current settings
            base_url = self.local_url_edit.text().strip()
            model = self.local_model_combo.currentText().strip()
            
            if not base_url:
                QMessageBox.warning(self, "Warning", "Please enter a base URL")
                return
            
            # Test connection with a simple request
            self.test_local_btn.setEnabled(False)
            self.test_local_btn.setText("Testing...")
            
            # Try to get model list or make a simple request
            test_url = f"{base_url.rstrip('/')}/api/tags"
            
            try:
                response = requests.get(test_url, timeout=10)
                if response.status_code == 200:
                    QMessageBox.information(
                        self, "Success",
                        f"✅ Successfully connected to {base_url}\nStatus: {response.status_code}"
                    )
                else:
                    QMessageBox.warning(
                        self, "Connection Issue",
                        f"⚠️ Connected but received status {response.status_code}\nThis might still work for some operations."
                    )
            except requests.exceptions.ConnectionError:
                QMessageBox.critical(
                    self, "Connection Failed",
                    f"❌ Could not connect to {base_url}\n\nPlease check:\n• LLM server is running\n• URL is correct\n• No firewall blocking"
                )
            except requests.exceptions.Timeout:
                QMessageBox.critical(
                    self, "Timeout",
                    f"❌ Connection timed out to {base_url}\n\nThe server might be slow or unresponsive."
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Error",
                    f"❌ Connection test failed:\n{str(e)}"
                )
                
        except ImportError:
            QMessageBox.critical(
                self, "Error",
                "❌ Requests library not available.\nPlease install: pip install requests"
            )
        finally:
            self.test_local_btn.setEnabled(True)
            self.test_local_btn.setText("Test Connection")
    
    def test_openai_connection(self):
        """Test OpenAI connection"""
        try:
            import requests
            
            # Get current settings
            api_key = self.openai_key_edit.text().strip()
            model = self.openai_model_combo.currentText().strip()
            
            if not api_key:
                QMessageBox.warning(self, "Warning", "Please enter an API key")
                return
            
            # Test connection
            self.test_openai_btn.setEnabled(False)
            self.test_openai_btn.setText("Testing...")
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # Test with a simple models list request
            try:
                response = requests.get(
                    "https://api.openai.com/v1/models",
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    model_count = len(data.get('data', []))
                    QMessageBox.information(
                        self, "Success",
                        f"✅ Successfully connected to OpenAI\nFound {model_count} available models"
                    )
                elif response.status_code == 401:
                    QMessageBox.critical(
                        self, "Authentication Failed",
                        "❌ Invalid API key\n\nPlease check your OpenAI API key."
                    )
                elif response.status_code == 429:
                    QMessageBox.warning(
                        self, "Rate Limited",
                        "⚠️ Rate limit exceeded\n\nYour API key is valid but you've hit rate limits."
                    )
                else:
                    QMessageBox.warning(
                        self, "Connection Issue",
                        f"⚠️ Received status {response.status_code}\nAPI key might still work for some operations."
                    )
                    
            except requests.exceptions.ConnectionError:
                QMessageBox.critical(
                    self, "Connection Failed",
                    "❌ Could not connect to OpenAI API\n\nPlease check your internet connection."
                )
            except requests.exceptions.Timeout:
                QMessageBox.critical(
                    self, "Timeout",
                    "❌ Connection timed out\n\nOpenAI API might be slow or unresponsive."
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Error",
                    f"❌ Connection test failed:\n{str(e)}"
                )
                
        except ImportError:
            QMessageBox.critical(
                self, "Error",
                "❌ Requests library not available.\nPlease install: pip install requests"
            )
        finally:
            self.test_openai_btn.setEnabled(True)
            self.test_openai_btn.setText("Test Connection")
    
    def save_settings(self):
        """Save LLM settings"""
        provider_map = {
            0: "local",
            1: "lmstudio",
            2: "openai",
            3: "anthropic",
            4: "custom"
        }
        
        self.settings.update_llm_config(
            enabled=self.enable_llm_cb.isChecked(),
            provider=provider_map.get(self.provider_combo.currentIndex(), "local"),
            local_base_url=self.local_url_edit.text(),
            local_model=self.local_model_combo.currentText(),
            openai_api_key=self.openai_key_edit.text(),
            openai_model=self.openai_model_combo.currentText()
        )


class GeneralTab(QWidget):
    """General settings tab"""
    
    def __init__(self, settings: SettingsManager, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        """Setup general tab UI"""
        layout = QVBoxLayout()
        
        # Auto-save settings
        autosave_group = QGroupBox("Auto-save")
        autosave_layout = QFormLayout()
        
        self.autosave_cb = QCheckBox()
        autosave_layout.addRow("Enable auto-save:", self.autosave_cb)
        
        self.autosave_interval_spin = QSpinBox()
        self.autosave_interval_spin.setRange(10, 300)
        self.autosave_interval_spin.setSuffix(" seconds")
        autosave_layout.addRow("Auto-save interval:", self.autosave_interval_spin)
        
        autosave_group.setLayout(autosave_layout)
        layout.addWidget(autosave_group)
        
        # Backup settings
        backup_group = QGroupBox("Backup")
        backup_layout = QFormLayout()
        
        self.backup_cb = QCheckBox()
        backup_layout.addRow("Enable backups:", self.backup_cb)
        
        self.backup_interval_spin = QSpinBox()
        self.backup_interval_spin.setRange(1, 168)
        self.backup_interval_spin.setSuffix(" hours")
        backup_layout.addRow("Backup interval:", self.backup_interval_spin)
        
        self.max_backups_spin = QSpinBox()
        self.max_backups_spin.setRange(1, 50)
        backup_layout.addRow("Max backups to keep:", self.max_backups_spin)
        
        backup_group.setLayout(backup_layout)
        layout.addWidget(backup_group)
        
        # File locations
        files_group = QGroupBox("File Locations")
        files_layout = QFormLayout()
        
        db_layout = QHBoxLayout()
        self.db_path_edit = QLineEdit()
        db_layout.addWidget(self.db_path_edit)
        
        self.browse_db_btn = QPushButton("Browse...")
        self.browse_db_btn.clicked.connect(self.browse_database)
        db_layout.addWidget(self.browse_db_btn)
        
        files_layout.addRow("Database:", db_layout)
        
        files_group.setLayout(files_layout)
        layout.addWidget(files_group)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def load_settings(self):
        """Load general settings"""
        config = self.settings.get_config()
        
        self.autosave_cb.setChecked(config.auto_save)
        self.autosave_interval_spin.setValue(config.auto_save_interval)
        self.backup_cb.setChecked(config.backup_enabled)
        self.backup_interval_spin.setValue(config.backup_interval)
        self.db_path_edit.setText(config.database_path)
    
    def browse_database(self):
        """Browse for database file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Database Location", self.db_path_edit.text(),
            "SQLite Database (*.db);;All Files (*)"
        )
        if file_path:
            self.db_path_edit.setText(file_path)
    
    def save_settings(self):
        """Save general settings"""
        self.settings.update_config(
            auto_save=self.autosave_cb.isChecked(),
            auto_save_interval=self.autosave_interval_spin.value(),
            backup_enabled=self.backup_cb.isChecked(),
            backup_interval=self.backup_interval_spin.value(),
            database_path=self.db_path_edit.text()
        )


class SettingsDialog(QDialog):
    """Main settings dialog"""
    
    settings_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = get_settings()
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.resize(800, 600)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup dialog UI"""
        layout = QVBoxLayout()
        
        # Tab widget
        self.tab_widget = QTabWidget()
        
        # General tab
        self.general_tab = GeneralTab(self.settings)
        self.tab_widget.addTab(self.general_tab, "General")
        
        # Appearance tab
        self.appearance_tab = AppearanceTab(self.settings)
        self.tab_widget.addTab(self.appearance_tab, "Appearance")
        
        # LLM tab
        self.llm_tab = LLMTab(self.settings)
        self.tab_widget.addTab(self.llm_tab, "LLM Integration")
        
        layout.addWidget(self.tab_widget)
        
        # Dialog buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Apply |
            QDialogButtonBox.StandardButton.RestoreDefaults
        )
        
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.apply_settings)
        buttons.button(QDialogButtonBox.StandardButton.RestoreDefaults).clicked.connect(self.restore_defaults)
        
        layout.addWidget(buttons)
        self.setLayout(layout)
    
    def apply_settings(self):
        """Apply settings without closing dialog"""
        self.general_tab.save_settings()
        self.appearance_tab.save_settings()
        self.llm_tab.save_settings()
        self.settings_changed.emit()
    
    def accept(self):
        """Accept and save settings"""
        self.apply_settings()
        super().accept()
    
    def restore_defaults(self):
        """Restore default settings"""
        reply = QMessageBox.question(
            self, "Restore Defaults",
            "Are you sure you want to restore all settings to their default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.settings.reset_to_defaults()
            # Reload all tabs
            self.general_tab.load_settings()
            self.appearance_tab.load_settings()
            self.llm_tab.load_settings()