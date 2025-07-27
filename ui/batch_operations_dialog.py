"""
Batch Operations Dialog for the Prompt Organizer application
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget,
    QListWidgetItem, QGroupBox, QComboBox, QCheckBox, QProgressBar,
    QTextEdit, QMessageBox, QDialogButtonBox, QFormLayout, QLineEdit,
    QScrollArea, QWidget, QFrame, QSplitter
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QIcon
from typing import List, Dict, Optional, Callable
import json
from datetime import datetime


class BatchOperationWorker(QThread):
    """Worker thread for performing batch operations"""
    
    progress_updated = pyqtSignal(int, str)  # progress, status message
    operation_completed = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, operation_func: Callable, prompt_ids: List[int], **kwargs):
        super().__init__()
        self.operation_func = operation_func
        self.prompt_ids = prompt_ids
        self.kwargs = kwargs
        self.is_cancelled = False
    
    def run(self):
        """Execute the batch operation"""
        try:
            total = len(self.prompt_ids)
            success_count = 0
            
            for i, prompt_id in enumerate(self.prompt_ids):
                if self.is_cancelled:
                    break
                
                try:
                    # Execute operation for this prompt
                    result = self.operation_func(prompt_id, **self.kwargs)
                    if result:
                        success_count += 1
                    
                    # Update progress
                    progress = int((i + 1) / total * 100)
                    self.progress_updated.emit(progress, f"Processing prompt {i + 1} of {total}")
                    
                except Exception as e:
                    print(f"Error processing prompt {prompt_id}: {e}")
            
            if not self.is_cancelled:
                message = f"Completed: {success_count}/{total} prompts processed successfully"
                self.operation_completed.emit(True, message)
            else:
                self.operation_completed.emit(False, "Operation cancelled")
                
        except Exception as e:
            self.operation_completed.emit(False, f"Batch operation failed: {str(e)}")
    
    def cancel(self):
        """Cancel the operation"""
        self.is_cancelled = True


class BatchTagDialog(QDialog):
    """Dialog for batch tag operations"""
    
    def __init__(self, available_tags: List[Dict], parent=None):
        super().__init__(parent)
        self.available_tags = available_tags
        self.setWindowTitle("Batch Tag Operations")
        self.setModal(True)
        self.resize(400, 300)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout()
        
        # Operation type
        operation_group = QGroupBox("Operation")
        operation_layout = QVBoxLayout()
        
        self.add_tags_radio = QCheckBox("Add tags to selected prompts")
        self.add_tags_radio.setChecked(True)
        self.remove_tags_radio = QCheckBox("Remove tags from selected prompts")
        
        operation_layout.addWidget(self.add_tags_radio)
        operation_layout.addWidget(self.remove_tags_radio)
        operation_group.setLayout(operation_layout)
        layout.addWidget(operation_group)
        
        # Tag selection
        tags_group = QGroupBox("Select Tags")
        tags_layout = QVBoxLayout()
        
        self.tag_list = QListWidget()
        self.tag_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        
        for tag in self.available_tags:
            item = QListWidgetItem(f"{tag['name']} ({tag['color']})")
            item.setData(Qt.ItemDataRole.UserRole, tag['id'])
            self.tag_list.addItem(item)
        
        tags_layout.addWidget(self.tag_list)
        
        # New tag option
        new_tag_layout = QHBoxLayout()
        self.new_tag_edit = QLineEdit()
        self.new_tag_edit.setPlaceholderText("Or enter new tag name...")
        self.add_new_tag_btn = QPushButton("Add New Tag")
        self.add_new_tag_btn.clicked.connect(self.add_new_tag)
        
        new_tag_layout.addWidget(self.new_tag_edit)
        new_tag_layout.addWidget(self.add_new_tag_btn)
        tags_layout.addLayout(new_tag_layout)
        
        tags_group.setLayout(tags_layout)
        layout.addWidget(tags_group)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def add_new_tag(self):
        """Add a new tag to the list"""
        tag_name = self.new_tag_edit.text().strip()
        if tag_name:
            # Add to list with a default color
            item = QListWidgetItem(f"{tag_name} (#007bff)")
            item.setData(Qt.ItemDataRole.UserRole, -1)  # -1 indicates new tag
            item.setData(Qt.ItemDataRole.UserRole + 1, tag_name)  # Store name separately
            self.tag_list.addItem(item)
            item.setSelected(True)
            self.new_tag_edit.clear()
    
    def get_operation_data(self):
        """Get the operation data"""
        selected_items = self.tag_list.selectedItems()
        tag_data = []
        
        for item in selected_items:
            tag_id = item.data(Qt.ItemDataRole.UserRole)
            if tag_id == -1:  # New tag
                tag_name = item.data(Qt.ItemDataRole.UserRole + 1)
                tag_data.append({'id': -1, 'name': tag_name, 'color': '#007bff'})
            else:
                # Find existing tag
                tag = next((t for t in self.available_tags if t['id'] == tag_id), None)
                if tag:
                    tag_data.append(tag)
        
        return {
            'operation': 'add' if self.add_tags_radio.isChecked() else 'remove',
            'tags': tag_data
        }


class BatchMoveDialog(QDialog):
    """Dialog for batch move operations"""
    
    def __init__(self, available_folders: List[Dict], parent=None):
        super().__init__(parent)
        self.available_folders = available_folders
        self.setWindowTitle("Move Prompts to Folder")
        self.setModal(True)
        self.resize(300, 200)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout()
        
        # Folder selection
        form_layout = QFormLayout()
        
        self.folder_combo = QComboBox()
        self.folder_combo.addItem("Root", None)
        
        for folder in self.available_folders:
            if folder['parent_id'] is not None:  # Skip root folder
                self.folder_combo.addItem(folder['name'], folder['id'])
        
        form_layout.addRow("Target Folder:", self.folder_combo)
        layout.addLayout(form_layout)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def get_target_folder_id(self):
        """Get the selected folder ID"""
        return self.folder_combo.currentData()


class BatchExportDialog(QDialog):
    """Dialog for batch export operations"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Batch Export Prompts")
        self.setModal(True)
        self.resize(400, 250)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout()
        
        # Export format
        format_group = QGroupBox("Export Format")
        format_layout = QVBoxLayout()
        
        self.json_radio = QCheckBox("JSON (structured data)")
        self.json_radio.setChecked(True)
        self.text_radio = QCheckBox("Text files (one per prompt)")
        self.combined_text_radio = QCheckBox("Single text file (all prompts)")
        
        format_layout.addWidget(self.json_radio)
        format_layout.addWidget(self.text_radio)
        format_layout.addWidget(self.combined_text_radio)
        format_group.setLayout(format_layout)
        layout.addWidget(format_group)
        
        # Export options
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout()
        
        self.include_metadata_cb = QCheckBox("Include metadata (tags, dates, etc.)")
        self.include_metadata_cb.setChecked(True)
        self.include_content_cb = QCheckBox("Include prompt content")
        self.include_content_cb.setChecked(True)
        
        options_layout.addWidget(self.include_metadata_cb)
        options_layout.addWidget(self.include_content_cb)
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def get_export_options(self):
        """Get export options"""
        format_type = 'json'
        if self.text_radio.isChecked():
            format_type = 'text'
        elif self.combined_text_radio.isChecked():
            format_type = 'combined_text'
        
        return {
            'format': format_type,
            'include_metadata': self.include_metadata_cb.isChecked(),
            'include_content': self.include_content_cb.isChecked()
        }


class BatchOperationsDialog(QDialog):
    """Main batch operations dialog"""
    
    def __init__(self, selected_prompts: List[Dict], db_manager, analytics_service=None, parent=None):
        super().__init__(parent)
        self.selected_prompts = selected_prompts
        self.db = db_manager
        self.analytics = analytics_service
        self.worker = None
        
        self.setWindowTitle(f"Batch Operations - {len(selected_prompts)} prompts selected")
        self.setModal(True)
        self.resize(600, 500)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout()
        
        # Selected prompts info
        info_group = QGroupBox("Selected Prompts")
        info_layout = QVBoxLayout()
        
        info_label = QLabel(f"{len(self.selected_prompts)} prompts selected for batch operations")
        info_label.setFont(QFont("", 10, QFont.Weight.Bold))
        info_layout.addWidget(info_label)
        
        # Show first few prompt titles
        preview_text = QTextEdit()
        preview_text.setMaximumHeight(100)
        preview_text.setReadOnly(True)
        
        preview_titles = []
        for i, prompt in enumerate(self.selected_prompts[:10]):
            preview_titles.append(f"{i+1}. {prompt['title']}")
        
        if len(self.selected_prompts) > 10:
            preview_titles.append(f"... and {len(self.selected_prompts) - 10} more")
        
        preview_text.setPlainText('\n'.join(preview_titles))
        info_layout.addWidget(preview_text)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Operations
        operations_group = QGroupBox("Available Operations")
        operations_layout = QVBoxLayout()
        
        # Delete operation
        delete_layout = QHBoxLayout()
        self.delete_btn = QPushButton("Delete All Selected")
        self.delete_btn.setStyleSheet("QPushButton { background-color: #dc3545; color: white; }")
        self.delete_btn.clicked.connect(self.batch_delete)
        delete_layout.addWidget(self.delete_btn)
        delete_layout.addStretch()
        operations_layout.addLayout(delete_layout)
        
        # Tag operations
        tag_layout = QHBoxLayout()
        self.manage_tags_btn = QPushButton("Manage Tags")
        self.manage_tags_btn.clicked.connect(self.batch_manage_tags)
        tag_layout.addWidget(self.manage_tags_btn)
        tag_layout.addStretch()
        operations_layout.addLayout(tag_layout)
        
        # Move operation
        move_layout = QHBoxLayout()
        self.move_btn = QPushButton("Move to Folder")
        self.move_btn.clicked.connect(self.batch_move)
        move_layout.addWidget(self.move_btn)
        move_layout.addStretch()
        operations_layout.addLayout(move_layout)
        
        # Copy operation
        copy_layout = QHBoxLayout()
        self.copy_btn = QPushButton("Copy All Content")
        self.copy_btn.clicked.connect(self.batch_copy)
        self.duplicate_btn = QPushButton("Duplicate All")
        self.duplicate_btn.clicked.connect(self.batch_duplicate)
        copy_layout.addWidget(self.copy_btn)
        copy_layout.addWidget(self.duplicate_btn)
        copy_layout.addStretch()
        operations_layout.addLayout(copy_layout)
        
        # Export operation
        export_layout = QHBoxLayout()
        self.export_btn = QPushButton("Export All")
        self.export_btn.clicked.connect(self.batch_export)
        export_layout.addWidget(self.export_btn)
        export_layout.addStretch()
        operations_layout.addLayout(export_layout)
        
        # Favorite/Template operations
        props_layout = QHBoxLayout()
        self.favorite_btn = QPushButton("Mark as Favorite")
        self.favorite_btn.clicked.connect(self.batch_favorite)
        self.unfavorite_btn = QPushButton("Remove Favorite")
        self.unfavorite_btn.clicked.connect(self.batch_unfavorite)
        self.template_btn = QPushButton("Mark as Template")
        self.template_btn.clicked.connect(self.batch_template)
        props_layout.addWidget(self.favorite_btn)
        props_layout.addWidget(self.unfavorite_btn)
        props_layout.addWidget(self.template_btn)
        props_layout.addStretch()
        operations_layout.addLayout(props_layout)
        
        operations_group.setLayout(operations_layout)
        layout.addWidget(operations_group)
        
        # Progress section
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("")
        progress_layout.addWidget(self.status_label)
        
        self.cancel_btn = QPushButton("Cancel Operation")
        self.cancel_btn.setVisible(False)
        self.cancel_btn.clicked.connect(self.cancel_operation)
        progress_layout.addWidget(self.cancel_btn)
        
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
    
    def start_batch_operation(self, operation_func, **kwargs):
        """Start a batch operation with progress tracking"""
        prompt_ids = [prompt['id'] for prompt in self.selected_prompts]
        
        self.worker = BatchOperationWorker(operation_func, prompt_ids, **kwargs)
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.operation_completed.connect(self.operation_completed)
        
        # Show progress UI
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.cancel_btn.setVisible(True)
        self.status_label.setText("Starting operation...")
        
        # Disable operation buttons
        self.set_operation_buttons_enabled(False)
        
        self.worker.start()
    
    def update_progress(self, progress: int, status: str):
        """Update progress display"""
        self.progress_bar.setValue(progress)
        self.status_label.setText(status)
    
    def operation_completed(self, success: bool, message: str):
        """Handle operation completion"""
        self.progress_bar.setVisible(False)
        self.cancel_btn.setVisible(False)
        self.status_label.setText(message)
        
        # Re-enable operation buttons
        self.set_operation_buttons_enabled(True)
        
        if success:
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.warning(self, "Operation Failed", message)
        
        self.worker = None
    
    def cancel_operation(self):
        """Cancel the current operation"""
        if self.worker:
            self.worker.cancel()
            self.status_label.setText("Cancelling operation...")
    
    def set_operation_buttons_enabled(self, enabled: bool):
        """Enable/disable operation buttons"""
        self.delete_btn.setEnabled(enabled)
        self.manage_tags_btn.setEnabled(enabled)
        self.move_btn.setEnabled(enabled)
        self.copy_btn.setEnabled(enabled)
        self.duplicate_btn.setEnabled(enabled)
        self.export_btn.setEnabled(enabled)
        self.favorite_btn.setEnabled(enabled)
        self.unfavorite_btn.setEnabled(enabled)
        self.template_btn.setEnabled(enabled)
    
    # Batch operation methods
    def batch_delete(self):
        """Batch delete prompts"""
        reply = QMessageBox.question(
            self, "Confirm Batch Delete",
            f"Are you sure you want to delete {len(self.selected_prompts)} prompts?\n\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.start_batch_operation(self.db.delete_prompt)
    
    def batch_manage_tags(self):
        """Batch tag management"""
        available_tags = self.db.get_tags()
        dialog = BatchTagDialog(available_tags, self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            operation_data = dialog.get_operation_data()
            
            if operation_data['operation'] == 'add':
                self.start_batch_operation(self._add_tags_to_prompt, tags=operation_data['tags'])
            else:
                self.start_batch_operation(self._remove_tags_from_prompt, tags=operation_data['tags'])
    
    def _add_tags_to_prompt(self, prompt_id: int, tags: List[Dict]) -> bool:
        """Add tags to a prompt"""
        success = True
        for tag in tags:
            if tag['id'] == -1:  # New tag
                tag_id = self.db.create_tag(tag['name'], tag['color'])
            else:
                tag_id = tag['id']
            
            if not self.db.add_tag_to_prompt(prompt_id, tag_id):
                success = False
        return success
    
    def _remove_tags_from_prompt(self, prompt_id: int, tags: List[Dict]) -> bool:
        """Remove tags from a prompt"""
        success = True
        for tag in tags:
            if tag['id'] != -1:  # Only remove existing tags
                if not self.db.remove_tag_from_prompt(prompt_id, tag['id']):
                    success = False
        return success
    
    def batch_move(self):
        """Batch move prompts"""
        available_folders = self.db.get_all_folders()
        dialog = BatchMoveDialog(available_folders, self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            target_folder_id = dialog.get_target_folder_id()
            self.start_batch_operation(self._move_prompt, folder_id=target_folder_id)
    
    def _move_prompt(self, prompt_id: int, folder_id: Optional[int]) -> bool:
        """Move a prompt to a folder"""
        return self.db.update_prompt(prompt_id, folder_id=folder_id)
    
    def batch_copy(self):
        """Copy all selected prompt content to clipboard"""
        from PyQt6.QtWidgets import QApplication
        
        content_parts = []
        for prompt in self.selected_prompts:
            content_parts.append(f"=== {prompt['title']} ===\n{prompt['content']}\n")
        
        combined_content = '\n'.join(content_parts)
        
        clipboard = QApplication.clipboard()
        clipboard.setText(combined_content)
        
        QMessageBox.information(self, "Success", f"Copied {len(self.selected_prompts)} prompts to clipboard")
    
    def batch_duplicate(self):
        """Duplicate all selected prompts"""
        self.start_batch_operation(self._duplicate_prompt)
    
    def _duplicate_prompt(self, prompt_id: int) -> bool:
        """Duplicate a prompt"""
        prompt = self.db.get_prompt(prompt_id)
        if not prompt:
            return False
        
        new_title = f"{prompt['title']} (Copy)"
        new_prompt_id = self.db.create_prompt(
            title=new_title,
            content=prompt['content'],
            folder_id=prompt['folder_id'],
            is_favorite=False,
            is_template=prompt['is_template']
        )
        
        # Copy tags
        tags = self.db.get_prompt_tags(prompt_id)
        for tag in tags:
            self.db.add_tag_to_prompt(new_prompt_id, tag['id'])
        
        return new_prompt_id is not None
    
    def batch_export(self):
        """Batch export prompts"""
        dialog = BatchExportDialog(self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            options = dialog.get_export_options()
            
            from PyQt6.QtWidgets import QFileDialog
            
            if options['format'] == 'json':
                file_path, _ = QFileDialog.getSaveFileName(
                    self, "Export Prompts", "batch_export.json", "JSON Files (*.json)"
                )
            elif options['format'] == 'combined_text':
                file_path, _ = QFileDialog.getSaveFileName(
                    self, "Export Prompts", "batch_export.txt", "Text Files (*.txt)"
                )
            else:  # text files
                file_path = QFileDialog.getExistingDirectory(self, "Select Export Directory")
            
            if file_path:
                self._export_prompts(file_path, options)
    
    def _export_prompts(self, file_path: str, options: Dict):
        """Export prompts to file(s)"""
        try:
            if options['format'] == 'json':
                export_data = []
                for prompt in self.selected_prompts:
                    prompt_data = {
                        'title': prompt['title'],
                        'content': prompt['content'] if options['include_content'] else '',
                    }
                    
                    if options['include_metadata']:
                        prompt_data.update({
                            'is_favorite': prompt['is_favorite'],
                            'is_template': prompt['is_template'],
                            'created_at': prompt['created_at'],
                            'updated_at': prompt['updated_at'],
                            'tags': self.db.get_prompt_tags(prompt['id'])
                        })
                    
                    export_data.append(prompt_data)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            elif options['format'] == 'combined_text':
                content_parts = []
                for prompt in self.selected_prompts:
                    part = f"=== {prompt['title']} ===\n"
                    if options['include_content']:
                        part += f"{prompt['content']}\n"
                    if options['include_metadata']:
                        part += f"Created: {prompt['created_at']}\n"
                        part += f"Updated: {prompt['updated_at']}\n"
                        tags = self.db.get_prompt_tags(prompt['id'])
                        if tags:
                            tag_names = [tag['name'] for tag in tags]
                            part += f"Tags: {', '.join(tag_names)}\n"
                    part += "\n"
                    content_parts.append(part)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(content_parts))
            
            else:  # individual text files
                import os
                for prompt in self.selected_prompts:
                    # Sanitize filename
                    safe_title = "".join(c for c in prompt['title'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
                    filename = f"{safe_title}.txt"
                    filepath = os.path.join(file_path, filename)
                    
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(f"Title: {prompt['title']}\n\n")
                        if options['include_content']:
                            f.write(f"{prompt['content']}\n\n")
                        if options['include_metadata']:
                            f.write(f"Created: {prompt['created_at']}\n")
                            f.write(f"Updated: {prompt['updated_at']}\n")
                            tags = self.db.get_prompt_tags(prompt['id'])
                            if tags:
                                tag_names = [tag['name'] for tag in tags]
                                f.write(f"Tags: {', '.join(tag_names)}\n")
            
            QMessageBox.information(self, "Success", f"Exported {len(self.selected_prompts)} prompts successfully")
            
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export prompts: {str(e)}")
    
    def batch_favorite(self):
        """Mark all selected prompts as favorite"""
        self.start_batch_operation(self._set_favorite, is_favorite=True)
    
    def batch_unfavorite(self):
        """Remove favorite status from all selected prompts"""
        self.start_batch_operation(self._set_favorite, is_favorite=False)
    
    def batch_template(self):
        """Mark all selected prompts as templates"""
        self.start_batch_operation(self._set_template, is_template=True)
    
    def _set_favorite(self, prompt_id: int, is_favorite: bool) -> bool:
        """Set favorite status for a prompt"""
        return self.db.update_prompt(prompt_id, is_favorite=is_favorite)
    
    def _set_template(self, prompt_id: int, is_template: bool) -> bool:
        """Set template status for a prompt"""
        return self.db.update_prompt(prompt_id, is_template=is_template)