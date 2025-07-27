#!/usr/bin/env python3
"""
Export dialog for the Prompt Organizer application.
Provides UI for exporting prompts to various formats.
"""

import sys
import os
from typing import List, Dict, Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QLabel, QPushButton, QComboBox, QCheckBox, QLineEdit, QTextEdit,
    QGroupBox, QFileDialog, QMessageBox, QProgressBar, QListWidget,
    QListWidgetItem, QSplitter, QTabWidget, QWidget, QSpinBox,
    QRadioButton, QButtonGroup, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QIcon, QPixmap

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.export_service import ExportService, ExportFormat, ExportOptions, ExportResult


class ExportWorker(QThread):
    """Worker thread for export operations"""
    
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    export_completed = pyqtSignal(object)  # ExportResult
    
    def __init__(self, export_service: ExportService, prompt_ids: List[int], 
                 output_path: str, options: ExportOptions):
        super().__init__()
        self.export_service = export_service
        self.prompt_ids = prompt_ids
        self.output_path = output_path
        self.options = options
    
    def run(self):
        """Run the export operation"""
        try:
            self.status_updated.emit("Starting export...")
            self.progress_updated.emit(10)
            
            self.status_updated.emit("Preparing data...")
            self.progress_updated.emit(30)
            
            self.status_updated.emit("Generating export file...")
            self.progress_updated.emit(50)
            
            # Perform the actual export
            result = self.export_service.export_prompts(
                self.prompt_ids, self.output_path, self.options
            )
            
            self.progress_updated.emit(90)
            self.status_updated.emit("Finalizing...")
            
            self.progress_updated.emit(100)
            self.status_updated.emit("Export completed!")
            
            self.export_completed.emit(result)
            
        except Exception as e:
            result = ExportResult(
                success=False,
                error_message=f"Export failed: {str(e)}"
            )
            self.export_completed.emit(result)


class ExportPreviewWidget(QWidget):
    """Widget for previewing export content"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the preview widget UI"""
        layout = QVBoxLayout(self)
        
        # Preview label
        preview_label = QLabel("Export Preview")
        preview_font = QFont()
        preview_font.setBold(True)
        preview_font.setPointSize(12)
        preview_label.setFont(preview_font)
        layout.addWidget(preview_label)
        
        # Preview text area
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setFont(QFont("Consolas", 10))
        layout.addWidget(self.preview_text)
        
        # Preview info
        self.preview_info = QLabel("Select prompts and format to see preview")
        self.preview_info.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(self.preview_info)
    
    def update_preview(self, prompts_data: List[Dict], options: ExportOptions):
        """Update the preview content"""
        try:
            if not prompts_data:
                self.preview_text.setPlainText("No prompts selected for export")
                self.preview_info.setText("Select prompts to see preview")
                return
            
            # Generate preview based on format
            if options.format == ExportFormat.HTML:
                preview_content = self._generate_html_preview(prompts_data, options)
                self.preview_text.setHtml(preview_content)
            elif options.format == ExportFormat.MARKDOWN:
                preview_content = self._generate_markdown_preview(prompts_data, options)
                self.preview_text.setPlainText(preview_content)
            elif options.format == ExportFormat.JSON:
                preview_content = self._generate_json_preview(prompts_data, options)
                self.preview_text.setPlainText(preview_content)
            else:
                preview_content = self._generate_text_preview(prompts_data, options)
                self.preview_text.setPlainText(preview_content)
            
            # Update info
            self.preview_info.setText(f"Preview for {len(prompts_data)} prompts in {options.format.value.upper()} format")
            
        except Exception as e:
            self.preview_text.setPlainText(f"Preview error: {str(e)}")
            self.preview_info.setText("Error generating preview")
    
    def _generate_html_preview(self, prompts_data: List[Dict], options: ExportOptions) -> str:
        """Generate HTML preview (limited)"""
        if not prompts_data:
            return "<p>No prompts to preview</p>"
        
        # Show first few prompts
        preview_prompts = prompts_data[:3]
        html_parts = ["<h2>Export Preview</h2>"]
        
        for prompt in preview_prompts:
            html_parts.extend([
                f"<h3>{prompt['title']}</h3>",
                f"<div style='background-color: #f8f9fa; padding: 10px; border-radius: 4px;'>{prompt['content']}</div>",
                "<br>"
            ])
        
        if len(prompts_data) > 3:
            html_parts.append(f"<p><i>... and {len(prompts_data) - 3} more prompts</i></p>")
        
        return "".join(html_parts)
    
    def _generate_markdown_preview(self, prompts_data: List[Dict], options: ExportOptions) -> str:
        """Generate Markdown preview (limited)"""
        if not prompts_data:
            return "No prompts to preview"
        
        preview_prompts = prompts_data[:3]
        md_parts = ["# Export Preview\n"]
        
        for prompt in preview_prompts:
            md_parts.extend([
                f"## {prompt['title']}\n",
                "```",
                prompt['content'],
                "```\n"
            ])
        
        if len(prompts_data) > 3:
            md_parts.append(f"*... and {len(prompts_data) - 3} more prompts*")
        
        return "\n".join(md_parts)
    
    def _generate_json_preview(self, prompts_data: List[Dict], options: ExportOptions) -> str:
        """Generate JSON preview (limited)"""
        import json
        
        if not prompts_data:
            return '{"prompts": []}'
        
        # Show structure with first prompt
        preview_data = {
            "title": options.custom_title or "Prompt Collection",
            "total_prompts": len(prompts_data),
            "prompts": prompts_data[:1] if prompts_data else []
        }
        
        if len(prompts_data) > 1:
            preview_data["note"] = f"Preview showing 1 of {len(prompts_data)} prompts"
        
        return json.dumps(preview_data, indent=2)
    
    def _generate_text_preview(self, prompts_data: List[Dict], options: ExportOptions) -> str:
        """Generate text preview (limited)"""
        if not prompts_data:
            return "No prompts to preview"
        
        preview_prompts = prompts_data[:3]
        txt_parts = ["EXPORT PREVIEW", "=" * 14, ""]
        
        for prompt in preview_prompts:
            txt_parts.extend([
                prompt['title'],
                "-" * len(prompt['title']),
                prompt['content'],
                ""
            ])
        
        if len(prompts_data) > 3:
            txt_parts.append(f"... and {len(prompts_data) - 3} more prompts")
        
        return "\n".join(txt_parts)


class ExportDialog(QDialog):
    """Dialog for exporting prompts to various formats"""
    
    def __init__(self, export_service: ExportService, selected_prompts: List[Dict] = None, parent=None):
        super().__init__(parent)
        self.export_service = export_service
        self.selected_prompts = selected_prompts or []
        self.all_prompts = []
        self.export_worker = None
        
        self.setWindowTitle("Export Prompts")
        self.setModal(True)
        self.resize(900, 700)
        
        self.setup_ui()
        self.load_prompts()
        self.update_preview()
    
    def setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Export Prompts")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Main content splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(main_splitter)
        
        # Left panel - Configuration
        config_widget = self.create_config_panel()
        main_splitter.addWidget(config_widget)
        
        # Right panel - Preview
        preview_widget = self.create_preview_panel()
        main_splitter.addWidget(preview_widget)
        
        # Set splitter proportions
        main_splitter.setSizes([400, 500])
        
        # Progress bar (initially hidden)
        self.progress_frame = QFrame()
        progress_layout = QVBoxLayout(self.progress_frame)
        
        self.progress_label = QLabel("Exporting...")
        progress_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_frame.setVisible(False)
        layout.addWidget(self.progress_frame)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.preview_button = QPushButton("Update Preview")
        self.preview_button.clicked.connect(self.update_preview)
        buttons_layout.addWidget(self.preview_button)
        
        buttons_layout.addStretch()
        
        self.export_button = QPushButton("Export")
        self.export_button.clicked.connect(self.start_export)
        self.export_button.setDefault(True)
        buttons_layout.addWidget(self.export_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)
        
        layout.addLayout(buttons_layout)
    
    def create_config_panel(self) -> QWidget:
        """Create the configuration panel"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Prompt selection
        selection_group = QGroupBox("Prompt Selection")
        selection_layout = QVBoxLayout(selection_group)
        
        # Selection options
        self.selection_group = QButtonGroup()
        
        self.selected_radio = QRadioButton("Selected prompts only")
        self.selected_radio.setChecked(bool(self.selected_prompts))
        self.selected_radio.toggled.connect(self.on_selection_changed)
        self.selection_group.addButton(self.selected_radio)
        selection_layout.addWidget(self.selected_radio)
        
        self.all_radio = QRadioButton("All prompts")
        self.all_radio.setChecked(not bool(self.selected_prompts))
        self.all_radio.toggled.connect(self.on_selection_changed)
        self.selection_group.addButton(self.all_radio)
        selection_layout.addWidget(self.all_radio)
        
        self.favorites_radio = QRadioButton("Favorites only")
        self.favorites_radio.toggled.connect(self.on_selection_changed)
        self.selection_group.addButton(self.favorites_radio)
        selection_layout.addWidget(self.favorites_radio)
        
        self.templates_radio = QRadioButton("Templates only")
        self.templates_radio.toggled.connect(self.on_selection_changed)
        self.selection_group.addButton(self.templates_radio)
        selection_layout.addWidget(self.templates_radio)
        
        layout.addWidget(selection_group)
        
        # Export format
        format_group = QGroupBox("Export Format")
        format_layout = QFormLayout(format_group)
        
        self.format_combo = QComboBox()
        supported_formats = self.export_service.get_supported_formats()
        for fmt in supported_formats:
            self.format_combo.addItem(fmt.value.upper(), fmt)
        self.format_combo.currentTextChanged.connect(self.on_format_changed)
        format_layout.addRow("Format:", self.format_combo)
        
        layout.addWidget(format_group)
        
        # Export options
        options_group = QGroupBox("Export Options")
        options_layout = QFormLayout(options_group)
        
        # Title and description
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Custom title (optional)")
        options_layout.addRow("Title:", self.title_edit)
        
        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("Custom description (optional)")
        options_layout.addRow("Description:", self.description_edit)
        
        # Include options
        self.include_metadata_cb = QCheckBox("Include metadata")
        self.include_metadata_cb.setChecked(True)
        options_layout.addRow("", self.include_metadata_cb)
        
        self.include_tags_cb = QCheckBox("Include tags")
        self.include_tags_cb.setChecked(True)
        options_layout.addRow("", self.include_tags_cb)
        
        self.include_folders_cb = QCheckBox("Include folder information")
        self.include_folders_cb.setChecked(True)
        options_layout.addRow("", self.include_folders_cb)
        
        self.include_timestamps_cb = QCheckBox("Include timestamps")
        self.include_timestamps_cb.setChecked(True)
        options_layout.addRow("", self.include_timestamps_cb)
        
        # Organization options
        self.group_by_folder_cb = QCheckBox("Group by folder")
        self.group_by_folder_cb.setChecked(True)
        options_layout.addRow("", self.group_by_folder_cb)
        
        # Sorting
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Title", "Created Date", "Updated Date"])
        options_layout.addRow("Sort by:", self.sort_combo)
        
        self.sort_order_combo = QComboBox()
        self.sort_order_combo.addItems(["Ascending", "Descending"])
        options_layout.addRow("Sort order:", self.sort_order_combo)
        
        layout.addWidget(options_group)
        
        layout.addStretch()
        
        return widget
    
    def create_preview_panel(self) -> QWidget:
        """Create the preview panel"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Preview widget
        self.preview_widget = ExportPreviewWidget()
        layout.addWidget(self.preview_widget)
        
        return widget
    
    def load_prompts(self):
        """Load prompts from database"""
        # This would typically get prompts from the database
        # For now, we'll use the selected prompts or empty list
        self.all_prompts = self.selected_prompts
        
        # Update selection info
        if self.selected_prompts:
            self.selected_radio.setText(f"Selected prompts ({len(self.selected_prompts)})")
        else:
            self.selected_radio.setText("Selected prompts (0)")
            self.selected_radio.setEnabled(False)
    
    def on_selection_changed(self):
        """Handle selection change"""
        self.update_preview()
    
    def on_format_changed(self):
        """Handle format change"""
        self.update_preview()
    
    def get_current_prompts(self) -> List[Dict]:
        """Get currently selected prompts for export"""
        if self.selected_radio.isChecked():
            return self.selected_prompts
        elif self.all_radio.isChecked():
            return self.all_prompts
        elif self.favorites_radio.isChecked():
            return [p for p in self.all_prompts if p.get('is_favorite', False)]
        elif self.templates_radio.isChecked():
            return [p for p in self.all_prompts if p.get('is_template', False)]
        else:
            return []
    
    def get_export_options(self) -> ExportOptions:
        """Get current export options"""
        format_data = self.format_combo.currentData()
        
        sort_by_map = {
            "Title": "title",
            "Created Date": "created_at",
            "Updated Date": "updated_at"
        }
        
        sort_order_map = {
            "Ascending": "asc",
            "Descending": "desc"
        }
        
        return ExportOptions(
            format=format_data,
            include_metadata=self.include_metadata_cb.isChecked(),
            include_tags=self.include_tags_cb.isChecked(),
            include_folders=self.include_folders_cb.isChecked(),
            include_timestamps=self.include_timestamps_cb.isChecked(),
            custom_title=self.title_edit.text().strip() or None,
            custom_description=self.description_edit.text().strip() or None,
            group_by_folder=self.group_by_folder_cb.isChecked(),
            sort_by=sort_by_map[self.sort_combo.currentText()],
            sort_order=sort_order_map[self.sort_order_combo.currentText()]
        )
    
    def update_preview(self):
        """Update the export preview"""
        prompts = self.get_current_prompts()
        options = self.get_export_options()
        
        self.preview_widget.update_preview(prompts, options)
        
        # Update export button state
        self.export_button.setEnabled(len(prompts) > 0)
    
    def start_export(self):
        """Start the export process"""
        prompts = self.get_current_prompts()
        if not prompts:
            QMessageBox.warning(self, "Warning", "No prompts selected for export.")
            return
        
        options = self.get_export_options()
        
        # Validate options
        issues = self.export_service.validate_export_options(options)
        if issues:
            QMessageBox.warning(self, "Export Options Error", "\n".join(issues))
            return
        
        # Get output file path
        file_extension = self.export_service.get_format_extension(options.format)
        default_filename = f"prompts_export{file_extension}"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Export File",
            default_filename,
            f"{options.format.value.upper()} Files (*{file_extension});;All Files (*)"
        )
        
        if not file_path:
            return
        
        # Start export in worker thread
        prompt_ids = [p['id'] for p in prompts]
        
        self.export_worker = ExportWorker(
            self.export_service, prompt_ids, file_path, options
        )
        self.export_worker.progress_updated.connect(self.progress_bar.setValue)
        self.export_worker.status_updated.connect(self.progress_label.setText)
        self.export_worker.export_completed.connect(self.on_export_completed)
        
        # Show progress
        self.progress_frame.setVisible(True)
        self.export_button.setEnabled(False)
        self.cancel_button.setText("Cancel Export")
        
        self.export_worker.start()
    
    def on_export_completed(self, result: ExportResult):
        """Handle export completion"""
        self.progress_frame.setVisible(False)
        self.export_button.setEnabled(True)
        self.cancel_button.setText("Close")
        
        if result.success:
            file_size_mb = result.file_size / (1024 * 1024) if result.file_size else 0
            message = f"Export completed successfully!\n\n"
            message += f"File: {result.file_path}\n"
            message += f"Exported: {result.exported_count} prompts\n"
            if result.file_size:
                message += f"Size: {file_size_mb:.2f} MB"
            
            QMessageBox.information(self, "Export Successful", message)
            self.accept()
        else:
            QMessageBox.critical(self, "Export Failed", result.error_message)
    
    def reject(self):
        """Handle dialog rejection"""
        if self.export_worker and self.export_worker.isRunning():
            reply = QMessageBox.question(
                self, "Cancel Export",
                "Export is in progress. Are you sure you want to cancel?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.export_worker.terminate()
                self.export_worker.wait()
                super().reject()
        else:
            super().reject()


# Test the dialog
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Mock export service for testing
    class MockExportService:
        def get_supported_formats(self):
            return [ExportFormat.HTML, ExportFormat.MARKDOWN, ExportFormat.JSON, ExportFormat.TXT]
        
        def get_format_extension(self, format):
            return f".{format.value}"
        
        def validate_export_options(self, options):
            return []
    
    # Mock prompts
    mock_prompts = [
        {
            'id': 1,
            'title': 'Test Prompt 1',
            'content': 'This is a test prompt content.',
            'is_favorite': True,
            'is_template': False,
            'created_at': '2024-01-01 10:00:00',
            'updated_at': '2024-01-01 10:00:00'
        },
        {
            'id': 2,
            'title': 'Test Prompt 2',
            'content': 'Another test prompt with different content.',
            'is_favorite': False,
            'is_template': True,
            'created_at': '2024-01-02 11:00:00',
            'updated_at': '2024-01-02 11:00:00'
        }
    ]
    
    dialog = ExportDialog(MockExportService(), mock_prompts)
    dialog.show()
    
    sys.exit(app.exec_())