"""
Plugin management dialog for the Prompt Organizer
"""

import sys
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QTableWidget, QTableWidgetItem, QPushButton,
    QComboBox, QCheckBox, QTextEdit, QGroupBox, QGridLayout,
    QProgressBar, QFrame, QScrollArea, QSplitter, QLineEdit,
    QFormLayout, QMessageBox, QHeaderView, QFileDialog,
    QListWidget, QListWidgetItem, QTreeWidget, QTreeWidgetItem,
    QSpinBox, QSlider, QColorDialog
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QFont, QPalette, QColor, QIcon
from datetime import datetime
from typing import Optional, Dict, List, Any
import json

from models.plugin_models import (
    PluginInfo, PluginStatus, PluginType, PluginPermission,
    PluginManifest, PluginConfig
)


class PluginListWidget(QWidget):
    """Widget for displaying plugin list"""
    
    plugin_selected = pyqtSignal(str)  # plugin_id
    plugin_toggled = pyqtSignal(str, bool)  # plugin_id, enabled
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Filter controls
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("Type:"))
        self.type_filter = QComboBox()
        self.type_filter.addItem("All Types", None)
        for plugin_type in PluginType:
            self.type_filter.addItem(plugin_type.value.replace('_', ' ').title(), plugin_type)
        self.type_filter.currentTextChanged.connect(self.filter_plugins)
        filter_layout.addWidget(self.type_filter)
        
        filter_layout.addWidget(QLabel("Status:"))
        self.status_filter = QComboBox()
        self.status_filter.addItem("All Status", None)
        for status in PluginStatus:
            self.status_filter.addItem(status.value.title(), status)
        self.status_filter.currentTextChanged.connect(self.filter_plugins)
        filter_layout.addWidget(self.status_filter)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Plugin table
        self.plugin_table = QTableWidget()
        self.plugin_table.setColumnCount(6)
        self.plugin_table.setHorizontalHeaderLabels([
            "Name", "Version", "Type", "Status", "Enabled", "Actions"
        ])
        self.plugin_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.plugin_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.plugin_table.itemSelectionChanged.connect(self.on_selection_changed)
        
        layout.addWidget(self.plugin_table)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.install_btn = QPushButton("Install Plugin...")
        self.install_btn.clicked.connect(self.install_plugin)
        button_layout.addWidget(self.install_btn)
        
        self.reload_btn = QPushButton("Reload")
        self.reload_btn.clicked.connect(self.reload_plugins)
        button_layout.addWidget(self.reload_btn)
        
        self.uninstall_btn = QPushButton("Uninstall")
        self.uninstall_btn.clicked.connect(self.uninstall_plugin)
        self.uninstall_btn.setEnabled(False)
        button_layout.addWidget(self.uninstall_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        self.plugins = {}
    
    def update_plugins(self, plugins: List[PluginInfo]):
        """Update the plugin list"""
        self.plugins = {p.manifest.id: p for p in plugins}
        self.refresh_table()
    
    def refresh_table(self):
        """Refresh the plugin table"""
        # Apply filters
        filtered_plugins = list(self.plugins.values())
        
        type_filter = self.type_filter.currentData()
        if type_filter:
            filtered_plugins = [p for p in filtered_plugins if p.manifest.plugin_type == type_filter]
        
        status_filter = self.status_filter.currentData()
        if status_filter:
            filtered_plugins = [p for p in filtered_plugins if p.status == status_filter]
        
        # Update table
        self.plugin_table.setRowCount(len(filtered_plugins))
        
        for row, plugin in enumerate(filtered_plugins):
            # Name
            name_item = QTableWidgetItem(plugin.manifest.name)
            name_item.setData(Qt.ItemDataRole.UserRole, plugin.manifest.id)
            self.plugin_table.setItem(row, 0, name_item)
            
            # Version
            self.plugin_table.setItem(row, 1, QTableWidgetItem(plugin.manifest.version))
            
            # Type
            type_text = plugin.manifest.plugin_type.value.replace('_', ' ').title()
            self.plugin_table.setItem(row, 2, QTableWidgetItem(type_text))
            
            # Status
            status_item = QTableWidgetItem(plugin.status.value.title())
            if plugin.status == PluginStatus.ACTIVE:
                status_item.setBackground(QColor("#d4edda"))
            elif plugin.status == PluginStatus.ERROR:
                status_item.setBackground(QColor("#f8d7da"))
            elif plugin.status == PluginStatus.INACTIVE:
                status_item.setBackground(QColor("#fff3cd"))
            self.plugin_table.setItem(row, 3, status_item)
            
            # Enabled checkbox
            enabled_cb = QCheckBox()
            enabled_cb.setChecked(plugin.enabled)
            enabled_cb.stateChanged.connect(
                lambda state, pid=plugin.manifest.id: self.plugin_toggled.emit(pid, state == Qt.CheckState.Checked)
            )
            self.plugin_table.setCellWidget(row, 4, enabled_cb)
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            
            if plugin.status == PluginStatus.INACTIVE:
                activate_btn = QPushButton("Activate")
                activate_btn.clicked.connect(lambda _, pid=plugin.manifest.id: self.activate_plugin(pid))
                actions_layout.addWidget(activate_btn)
            elif plugin.status == PluginStatus.ACTIVE:
                deactivate_btn = QPushButton("Deactivate")
                deactivate_btn.clicked.connect(lambda _, pid=plugin.manifest.id: self.deactivate_plugin(pid))
                actions_layout.addWidget(deactivate_btn)
            
            self.plugin_table.setCellWidget(row, 5, actions_widget)
    
    def filter_plugins(self):
        """Apply filters to plugin list"""
        self.refresh_table()
    
    def on_selection_changed(self):
        """Handle selection change"""
        current_row = self.plugin_table.currentRow()
        if current_row >= 0:
            name_item = self.plugin_table.item(current_row, 0)
            if name_item:
                plugin_id = name_item.data(Qt.ItemDataRole.UserRole)
                self.plugin_selected.emit(plugin_id)
                self.uninstall_btn.setEnabled(True)
        else:
            self.uninstall_btn.setEnabled(False)
    
    def activate_plugin(self, plugin_id: str):
        """Activate plugin signal"""
        # This would be connected to the plugin manager
        pass
    
    def deactivate_plugin(self, plugin_id: str):
        """Deactivate plugin signal"""
        # This would be connected to the plugin manager
        pass
    
    def install_plugin(self):
        """Install new plugin"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Install Plugin", "", "Plugin Archives (*.zip);;All Files (*)"
        )
        if file_path:
            # This would handle plugin installation
            QMessageBox.information(self, "Install Plugin", f"Plugin installation from {file_path} would be implemented here.")
    
    def reload_plugins(self):
        """Reload plugins"""
        # This would trigger plugin reload
        pass
    
    def uninstall_plugin(self):
        """Uninstall selected plugin"""
        current_row = self.plugin_table.currentRow()
        if current_row >= 0:
            name_item = self.plugin_table.item(current_row, 0)
            if name_item:
                plugin_id = name_item.data(Qt.ItemDataRole.UserRole)
                plugin = self.plugins.get(plugin_id)
                if plugin:
                    reply = QMessageBox.question(
                        self, "Uninstall Plugin",
                        f"Are you sure you want to uninstall '{plugin.manifest.name}'?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    if reply == QMessageBox.StandardButton.Yes:
                        # This would handle plugin uninstallation
                        QMessageBox.information(self, "Uninstall", "Plugin uninstallation would be implemented here.")


class PluginDetailsWidget(QWidget):
    """Widget for displaying plugin details"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_plugin = None
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Plugin info
        info_group = QGroupBox("Plugin Information")
        info_layout = QFormLayout(info_group)
        
        self.name_label = QLabel("-")
        self.version_label = QLabel("-")
        self.author_label = QLabel("-")
        self.description_label = QLabel("-")
        self.type_label = QLabel("-")
        self.status_label = QLabel("-")
        
        info_layout.addRow("Name:", self.name_label)
        info_layout.addRow("Version:", self.version_label)
        info_layout.addRow("Author:", self.author_label)
        info_layout.addRow("Type:", self.type_label)
        info_layout.addRow("Status:", self.status_label)
        info_layout.addRow("Description:", self.description_label)
        
        layout.addWidget(info_group)
        
        # Permissions
        permissions_group = QGroupBox("Permissions")
        permissions_layout = QVBoxLayout(permissions_group)
        
        self.permissions_list = QListWidget()
        permissions_layout.addWidget(self.permissions_list)
        
        layout.addWidget(permissions_group)
        
        # Settings
        settings_group = QGroupBox("Settings")
        settings_layout = QVBoxLayout(settings_group)
        
        self.settings_scroll = QScrollArea()
        self.settings_widget = QWidget()
        self.settings_layout = QFormLayout(self.settings_widget)
        self.settings_scroll.setWidget(self.settings_widget)
        self.settings_scroll.setWidgetResizable(True)
        settings_layout.addWidget(self.settings_scroll)
        
        self.save_settings_btn = QPushButton("Save Settings")
        self.save_settings_btn.clicked.connect(self.save_settings)
        self.save_settings_btn.setEnabled(False)
        settings_layout.addWidget(self.save_settings_btn)
        
        layout.addWidget(settings_group)
        
        # Error log
        error_group = QGroupBox("Error Log")
        error_layout = QVBoxLayout(error_group)
        
        self.error_text = QTextEdit()
        self.error_text.setReadOnly(True)
        self.error_text.setMaximumHeight(100)
        error_layout.addWidget(self.error_text)
        
        layout.addWidget(error_group)
    
    def show_plugin_details(self, plugin: PluginInfo):
        """Show details for the selected plugin"""
        self.current_plugin = plugin
        
        # Update info
        self.name_label.setText(plugin.manifest.name)
        self.version_label.setText(plugin.manifest.version)
        self.author_label.setText(f"{plugin.manifest.author} <{plugin.manifest.author_email}>")
        self.type_label.setText(plugin.manifest.plugin_type.value.replace('_', ' ').title())
        self.status_label.setText(plugin.status.value.title())
        self.description_label.setText(plugin.manifest.description)
        
        # Update permissions
        self.permissions_list.clear()
        for permission in plugin.manifest.permissions:
            item = QListWidgetItem(permission.value.replace('_', ' ').title())
            self.permissions_list.addItem(item)
        
        # Update settings
        self.update_settings_ui(plugin)
        
        # Update error log
        if plugin.error_message:
            self.error_text.setText(plugin.error_message)
        else:
            self.error_text.clear()
    
    def update_settings_ui(self, plugin: PluginInfo):
        """Update settings UI based on plugin schema"""
        # Clear existing settings
        for i in reversed(range(self.settings_layout.count())):
            self.settings_layout.itemAt(i).widget().setParent(None)
        
        schema = plugin.manifest.settings_schema
        current_settings = plugin.settings
        
        self.setting_widgets = {}
        
        for key, setting_def in schema.items():
            setting_type = setting_def.get('type', 'string')
            label = setting_def.get('label', key)
            default_value = setting_def.get('default', '')
            current_value = current_settings.get(key, default_value)
            
            if setting_type == 'string':
                widget = QLineEdit()
                widget.setText(str(current_value))
            elif setting_type == 'integer':
                widget = QSpinBox()
                widget.setRange(setting_def.get('min', 0), setting_def.get('max', 1000))
                widget.setValue(int(current_value) if current_value else 0)
            elif setting_type == 'boolean':
                widget = QCheckBox()
                widget.setChecked(bool(current_value))
            elif setting_type == 'choice':
                widget = QComboBox()
                choices = setting_def.get('choices', [])
                for choice in choices:
                    widget.addItem(choice)
                if current_value in choices:
                    widget.setCurrentText(str(current_value))
            elif setting_type == 'color':
                widget = QPushButton()
                widget.setText(str(current_value))
                widget.clicked.connect(lambda _, w=widget: self.choose_color(w))
            else:
                widget = QLineEdit()
                widget.setText(str(current_value))
            
            self.setting_widgets[key] = widget
            self.settings_layout.addRow(f"{label}:", widget)
        
        self.save_settings_btn.setEnabled(len(self.setting_widgets) > 0)
    
    def choose_color(self, button):
        """Choose color for color setting"""
        color = QColorDialog.getColor(QColor(button.text()), self)
        if color.isValid():
            button.setText(color.name())
    
    def save_settings(self):
        """Save plugin settings"""
        if not self.current_plugin:
            return
        
        new_settings = {}
        for key, widget in self.setting_widgets.items():
            if isinstance(widget, QLineEdit):
                new_settings[key] = widget.text()
            elif isinstance(widget, QSpinBox):
                new_settings[key] = widget.value()
            elif isinstance(widget, QCheckBox):
                new_settings[key] = widget.isChecked()
            elif isinstance(widget, QComboBox):
                new_settings[key] = widget.currentText()
            elif isinstance(widget, QPushButton):
                new_settings[key] = widget.text()
        
        # This would update the plugin settings
        QMessageBox.information(self, "Settings", "Plugin settings saved successfully!")


class PluginStoreWidget(QWidget):
    """Widget for browsing and installing plugins from store"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Search and filters
        search_layout = QHBoxLayout()
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search plugins...")
        search_layout.addWidget(self.search_edit)
        
        self.category_combo = QComboBox()
        self.category_combo.addItem("All Categories")
        for plugin_type in PluginType:
            self.category_combo.addItem(plugin_type.value.replace('_', ' ').title())
        search_layout.addWidget(self.category_combo)
        
        self.search_btn = QPushButton("Search")
        search_layout.addWidget(self.search_btn)
        
        layout.addLayout(search_layout)
        
        # Plugin store list
        self.store_list = QListWidget()
        layout.addWidget(self.store_list)
        
        # Add some example plugins
        self.add_example_plugins()
    
    def add_example_plugins(self):
        """Add example plugins to the store"""
        example_plugins = [
            {
                "name": "Markdown Exporter",
                "description": "Export prompts to Markdown format",
                "author": "Community",
                "version": "1.0.0",
                "type": "Export Format"
            },
            {
                "name": "CSV Importer",
                "description": "Import prompts from CSV files",
                "author": "Community",
                "version": "1.2.0",
                "type": "Import Format"
            },
            {
                "name": "OpenAI GPT Provider",
                "description": "Connect to OpenAI GPT models",
                "author": "OpenAI Team",
                "version": "2.1.0",
                "type": "LLM Provider"
            },
            {
                "name": "Prompt Validator",
                "description": "Validate prompt syntax and structure",
                "author": "Community",
                "version": "1.0.5",
                "type": "Prompt Processor"
            }
        ]
        
        for plugin in example_plugins:
            item = QListWidgetItem()
            item.setText(f"{plugin['name']} v{plugin['version']}\n{plugin['description']}\nBy: {plugin['author']}")
            item.setData(Qt.ItemDataRole.UserRole, plugin)
            self.store_list.addItem(item)


class PluginDialog(QDialog):
    """Main plugin management dialog"""
    
    def __init__(self, plugin_manager, parent=None):
        super().__init__(parent)
        self.plugin_manager = plugin_manager
        self.init_ui()
        self.load_plugins()
    
    def init_ui(self):
        self.setWindowTitle("Plugin Manager")
        self.setModal(True)
        self.resize(900, 600)
        
        layout = QVBoxLayout(self)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        
        # Installed plugins tab
        self.plugins_widget = PluginListWidget()
        self.plugins_widget.plugin_selected.connect(self.on_plugin_selected)
        self.plugins_widget.plugin_toggled.connect(self.on_plugin_toggled)
        self.tab_widget.addTab(self.plugins_widget, "Installed Plugins")
        
        # Plugin details tab
        self.details_widget = PluginDetailsWidget()
        self.tab_widget.addTab(self.details_widget, "Plugin Details")
        
        # Plugin store tab
        self.store_widget = PluginStoreWidget()
        self.tab_widget.addTab(self.store_widget, "Plugin Store")
        
        layout.addWidget(self.tab_widget)
        
        # Status bar
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.load_plugins)
        button_layout.addWidget(self.refresh_btn)
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
    
    def load_plugins(self):
        """Load plugins from plugin manager"""
        try:
            plugins = self.plugin_manager.get_plugins()
            self.plugins_widget.update_plugins(plugins)
            
            stats = self.plugin_manager.get_plugin_statistics()
            status_text = f"Loaded {stats['total_plugins']} plugins ({stats['active_plugins']} active)"
            self.status_label.setText(status_text)
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load plugins: {str(e)}")
    
    def on_plugin_selected(self, plugin_id: str):
        """Handle plugin selection"""
        plugin = self.plugin_manager.get_plugin(plugin_id)
        if plugin:
            self.details_widget.show_plugin_details(plugin)
            self.tab_widget.setCurrentIndex(1)  # Switch to details tab
    
    def on_plugin_toggled(self, plugin_id: str, enabled: bool):
        """Handle plugin enable/disable toggle"""
        try:
            plugin = self.plugin_manager.get_plugin(plugin_id)
            if plugin:
                plugin.enabled = enabled
                if enabled and plugin.status == PluginStatus.INACTIVE:
                    self.plugin_manager.activate_plugin(plugin_id)
                elif not enabled and plugin.status == PluginStatus.ACTIVE:
                    self.plugin_manager.deactivate_plugin(plugin_id)
                
                self.load_plugins()  # Refresh the list
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to toggle plugin: {str(e)}")


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Mock plugin manager for testing
    class MockPluginManager:
        def get_plugins(self):
            from models.plugin_models import PluginInfo, PluginManifest, PluginStatus, PluginType
            
            plugins = []
            for i in range(3):
                manifest = PluginManifest(
                    id=f"plugin_{i}",
                    name=f"Test Plugin {i+1}",
                    version="1.0.0",
                    description=f"This is test plugin number {i+1}",
                    author="Test Author",
                    plugin_type=list(PluginType)[i % len(PluginType)]
                )
                
                plugin_info = PluginInfo(
                    manifest=manifest,
                    status=list(PluginStatus)[i % len(PluginStatus)],
                    enabled=i % 2 == 0
                )
                plugins.append(plugin_info)
            
            return plugins
        
        def get_plugin(self, plugin_id):
            plugins = self.get_plugins()
            return next((p for p in plugins if p.manifest.id == plugin_id), None)
        
        def get_plugin_statistics(self):
            return {
                "total_plugins": 3,
                "active_plugins": 1,
                "inactive_plugins": 1,
                "error_plugins": 1
            }
        
        def activate_plugin(self, plugin_id):
            return True
        
        def deactivate_plugin(self, plugin_id):
            return True
    
    dialog = PluginDialog(MockPluginManager())
    dialog.show()
    
    sys.exit(app.exec())