"""
Template dialogs for the Prompt Organizer application
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget,
    QListWidgetItem, QGroupBox, QComboBox, QCheckBox, QProgressBar,
    QTextEdit, QMessageBox, QDialogButtonBox, QFormLayout, QLineEdit,
    QScrollArea, QWidget, QFrame, QSplitter, QTabWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QSpinBox, QDateEdit, QPlainTextEdit,
    QTreeWidget, QTreeWidgetItem, QInputDialog
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QDate
from PyQt6.QtGui import QFont, QIcon, QTextCharFormat, QSyntaxHighlighter
from typing import List, Dict, Optional
import json
from datetime import datetime

from models.template_models import PromptTemplate, TemplateVariable, TemplateCategory, DEFAULT_CATEGORIES
from services.template_service import TemplateService


class TemplateVariableHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for template variables"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_highlighting_rules()
    
    def setup_highlighting_rules(self):
        """Setup highlighting rules for template variables"""
        # Variables/placeholders {variable}
        self.variable_format = QTextCharFormat()
        self.variable_format.setForeground(Qt.GlobalColor.blue)
        self.variable_format.setFontWeight(QFont.Weight.Bold)
        
        # Invalid variables (empty braces, etc.)
        self.invalid_format = QTextCharFormat()
        self.invalid_format.setForeground(Qt.GlobalColor.red)
        self.invalid_format.setBackground(Qt.GlobalColor.yellow)
    
    def highlightBlock(self, text):
        """Apply highlighting rules to text block"""
        import re
        
        # Highlight valid variables
        for match in re.finditer(r'\{([^}]+)\}', text):
            start = match.start()
            length = match.end() - start
            var_name = match.group(1).strip()
            
            if var_name and re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', var_name):
                self.setFormat(start, length, self.variable_format)
            else:
                self.setFormat(start, length, self.invalid_format)
        
        # Highlight invalid patterns
        for match in re.finditer(r'\{\s*\}', text):
            start = match.start()
            length = match.end() - start
            self.setFormat(start, length, self.invalid_format)


class VariableEditDialog(QDialog):
    """Dialog for editing template variables"""
    
    def __init__(self, variable: TemplateVariable = None, parent=None):
        super().__init__(parent)
        self.variable = variable or TemplateVariable(name="")
        self.setWindowTitle("Edit Variable" if variable else "Add Variable")
        self.setModal(True)
        self.resize(500, 400)
        self.setup_ui()
        self.load_variable_data()
    
    def setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout()
        
        # Basic info
        basic_group = QGroupBox("Basic Information")
        basic_layout = QFormLayout()
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("variable_name")
        basic_layout.addRow("Name:", self.name_edit)
        
        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("Description of what this variable represents")
        basic_layout.addRow("Description:", self.description_edit)
        
        self.default_value_edit = QLineEdit()
        self.default_value_edit.setPlaceholderText("Default value (optional)")
        basic_layout.addRow("Default Value:", self.default_value_edit)
        
        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)
        
        # Type and validation
        type_group = QGroupBox("Type and Validation")
        type_layout = QFormLayout()
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["text", "number", "boolean", "choice", "date"])
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        type_layout.addRow("Type:", self.type_combo)
        
        self.required_cb = QCheckBox("Required")
        self.required_cb.setChecked(True)
        type_layout.addRow("", self.required_cb)
        
        # Choices (for choice type)
        self.choices_edit = QTextEdit()
        self.choices_edit.setMaximumHeight(80)
        self.choices_edit.setPlaceholderText("Enter choices, one per line")
        self.choices_label = QLabel("Choices:")
        type_layout.addRow(self.choices_label, self.choices_edit)
        
        # Validation pattern
        self.validation_edit = QLineEdit()
        self.validation_edit.setPlaceholderText("Regular expression pattern (optional)")
        self.validation_label = QLabel("Validation Pattern:")
        type_layout.addRow(self.validation_label, self.validation_edit)
        
        type_group.setLayout(type_layout)
        layout.addWidget(type_group)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
        
        # Initial type setup
        self.on_type_changed()
    
    def on_type_changed(self):
        """Handle variable type change"""
        var_type = self.type_combo.currentText()
        
        # Show/hide choices based on type
        show_choices = var_type == "choice"
        self.choices_label.setVisible(show_choices)
        self.choices_edit.setVisible(show_choices)
        
        # Show/hide validation pattern for text types
        show_validation = var_type == "text"
        self.validation_label.setVisible(show_validation)
        self.validation_edit.setVisible(show_validation)
        
        # Set appropriate placeholders
        if var_type == "number":
            self.default_value_edit.setPlaceholderText("0")
        elif var_type == "boolean":
            self.default_value_edit.setPlaceholderText("true or false")
        elif var_type == "date":
            self.default_value_edit.setPlaceholderText("YYYY-MM-DD")
        else:
            self.default_value_edit.setPlaceholderText("Default value (optional)")
    
    def load_variable_data(self):
        """Load variable data into the form"""
        if not self.variable.name:
            return
        
        self.name_edit.setText(self.variable.name)
        self.description_edit.setText(self.variable.description)
        self.default_value_edit.setText(self.variable.default_value)
        self.type_combo.setCurrentText(self.variable.variable_type)
        self.required_cb.setChecked(self.variable.required)
        
        if self.variable.choices:
            self.choices_edit.setPlainText('\n'.join(self.variable.choices))
        
        if self.variable.validation_pattern:
            self.validation_edit.setText(self.variable.validation_pattern)
    
    def get_variable(self) -> TemplateVariable:
        """Get the variable from the form"""
        choices = []
        if self.type_combo.currentText() == "choice":
            choices_text = self.choices_edit.toPlainText().strip()
            if choices_text:
                choices = [line.strip() for line in choices_text.split('\n') if line.strip()]
        
        return TemplateVariable(
            name=self.name_edit.text().strip(),
            description=self.description_edit.text().strip(),
            default_value=self.default_value_edit.text().strip(),
            variable_type=self.type_combo.currentText(),
            choices=choices,
            required=self.required_cb.isChecked(),
            validation_pattern=self.validation_edit.text().strip()
        )
    
    def accept(self):
        """Validate and accept the dialog"""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Variable name is required.")
            return
        
        # Validate name format
        import re
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
            QMessageBox.warning(self, "Validation Error", 
                              "Variable name must start with a letter or underscore and contain only letters, numbers, and underscores.")
            return
        
        # Validate choices for choice type
        if self.type_combo.currentText() == "choice":
            choices_text = self.choices_edit.toPlainText().strip()
            if not choices_text:
                QMessageBox.warning(self, "Validation Error", "Choices are required for choice type variables.")
                return
        
        super().accept()


class TemplateUsageDialog(QDialog):
    """Dialog for using a template with variable substitution"""
    
    def __init__(self, template: PromptTemplate, template_service: TemplateService, parent=None):
        super().__init__(parent)
        self.template = template
        self.template_service = template_service
        self.variable_widgets = {}
        
        self.setWindowTitle(f"Use Template: {template.title}")
        self.setModal(True)
        self.resize(600, 500)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout()
        
        # Template info
        info_group = QGroupBox("Template Information")
        info_layout = QVBoxLayout()
        
        title_label = QLabel(f"<b>{self.template.title}</b>")
        title_label.setFont(QFont("", 12, QFont.Weight.Bold))
        info_layout.addWidget(title_label)
        
        if self.template.description:
            desc_label = QLabel(self.template.description)
            desc_label.setWordWrap(True)
            info_layout.addWidget(desc_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Variables
        if self.template.variables:
            variables_group = QGroupBox("Variables")
            variables_layout = QFormLayout()
            
            for variable in self.template.variables:
                widget = self.create_variable_widget(variable)
                self.variable_widgets[variable.name] = widget
                
                label_text = variable.name
                if variable.required:
                    label_text += " *"
                if variable.description:
                    label_text += f" ({variable.description})"
                
                variables_layout.addRow(label_text, widget)
            
            variables_group.setLayout(variables_layout)
            layout.addWidget(variables_group)
        
        # Preview
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout()
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(150)
        preview_layout.addWidget(self.preview_text)
        
        update_preview_btn = QPushButton("Update Preview")
        update_preview_btn.clicked.connect(self.update_preview)
        preview_layout.addWidget(update_preview_btn)
        
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        # Options
        options_group = QGroupBox("Options")
        options_layout = QFormLayout()
        
        self.create_prompt_cb = QCheckBox("Create new prompt")
        self.create_prompt_cb.setChecked(True)
        self.create_prompt_cb.stateChanged.connect(self.on_create_prompt_changed)
        options_layout.addRow("", self.create_prompt_cb)
        
        self.prompt_title_edit = QLineEdit()
        self.prompt_title_edit.setText(f"{self.template.title} - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        options_layout.addRow("Prompt Title:", self.prompt_title_edit)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.use_btn = QPushButton("Use Template")
        self.use_btn.clicked.connect(self.use_template)
        self.use_btn.setDefault(True)
        
        self.copy_btn = QPushButton("Copy to Clipboard")
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.use_btn)
        button_layout.addWidget(self.copy_btn)
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # Initial preview
        self.update_preview()
    
    def create_variable_widget(self, variable: TemplateVariable):
        """Create appropriate widget for variable type"""
        if variable.variable_type == "choice":
            widget = QComboBox()
            widget.setEditable(True)
            if variable.choices:
                widget.addItems(variable.choices)
            if variable.default_value:
                widget.setCurrentText(variable.default_value)
            return widget
        
        elif variable.variable_type == "boolean":
            widget = QComboBox()
            widget.addItems(["true", "false"])
            if variable.default_value:
                widget.setCurrentText(variable.default_value.lower())
            return widget
        
        elif variable.variable_type == "number":
            widget = QSpinBox()
            widget.setRange(-999999, 999999)
            if variable.default_value:
                try:
                    widget.setValue(int(float(variable.default_value)))
                except ValueError:
                    pass
            return widget
        
        elif variable.variable_type == "date":
            widget = QDateEdit()
            widget.setCalendarPopup(True)
            widget.setDate(QDate.currentDate())
            if variable.default_value:
                try:
                    date = QDate.fromString(variable.default_value, "yyyy-MM-dd")
                    if date.isValid():
                        widget.setDate(date)
                except:
                    pass
            return widget
        
        else:  # text
            widget = QLineEdit()
            if variable.default_value:
                widget.setText(variable.default_value)
            return widget
    
    def get_variable_value(self, variable: TemplateVariable) -> str:
        """Get value from variable widget"""
        widget = self.variable_widgets[variable.name]
        
        if variable.variable_type == "choice":
            return widget.currentText()
        elif variable.variable_type == "boolean":
            return widget.currentText()
        elif variable.variable_type == "number":
            return str(widget.value())
        elif variable.variable_type == "date":
            return widget.date().toString("yyyy-MM-dd")
        else:  # text
            return widget.text()
    
    def get_substitutions(self) -> Dict[str, str]:
        """Get all variable substitutions"""
        substitutions = {}
        for variable in self.template.variables:
            substitutions[variable.name] = self.get_variable_value(variable)
        return substitutions
    
    def update_preview(self):
        """Update the preview text"""
        try:
            substitutions = self.get_substitutions()
            preview = self.template.get_preview(substitutions)
            self.preview_text.setPlainText(preview)
        except Exception as e:
            self.preview_text.setPlainText(f"Preview error: {str(e)}")
    
    def on_create_prompt_changed(self):
        """Handle create prompt checkbox change"""
        enabled = self.create_prompt_cb.isChecked()
        self.prompt_title_edit.setEnabled(enabled)
    
    def use_template(self):
        """Use the template with current substitutions"""
        try:
            substitutions = self.get_substitutions()
            create_prompt = self.create_prompt_cb.isChecked()
            prompt_title = self.prompt_title_edit.text().strip() if create_prompt else None
            
            content, prompt_id = self.template_service.use_template(
                template_id=self.template.id,
                substitutions=substitutions,
                create_prompt=create_prompt,
                prompt_title=prompt_title
            )
            
            if create_prompt:
                QMessageBox.information(self, "Success", f"Template used successfully!\nNew prompt created: {prompt_title}")
            else:
                QMessageBox.information(self, "Success", "Template processed successfully!\nContent copied to clipboard.")
                
                # Copy to clipboard
                from PyQt6.QtWidgets import QApplication
                clipboard = QApplication.clipboard()
                clipboard.setText(content)
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to use template: {str(e)}")
    
    def copy_to_clipboard(self):
        """Copy current preview to clipboard"""
        try:
            substitutions = self.get_substitutions()
            content = self.template.substitute_variables(substitutions)
            
            from PyQt6.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            clipboard.setText(content)
            
            QMessageBox.information(self, "Success", "Content copied to clipboard!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to copy content: {str(e)}")


class TemplateEditorDialog(QDialog):
    """Dialog for creating and editing templates"""
    
    def __init__(self, template: PromptTemplate = None, template_service: TemplateService = None, parent=None):
        super().__init__(parent)
        self.template = template or PromptTemplate()
        self.template_service = template_service
        self.is_editing = template is not None
        
        self.setWindowTitle("Edit Template" if self.is_editing else "Create Template")
        self.setModal(True)
        self.resize(800, 600)
        self.setup_ui()
        self.load_template_data()
    
    def setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout()
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Basic info tab
        self.setup_basic_tab()
        
        # Variables tab
        self.setup_variables_tab()
        
        # Preview tab
        self.setup_preview_tab()
        
        layout.addWidget(self.tab_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("Save Template")
        self.save_btn.clicked.connect(self.save_template)
        self.save_btn.setDefault(True)
        
        self.validate_btn = QPushButton("Validate")
        self.validate_btn.clicked.connect(self.validate_template)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.validate_btn)
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def setup_basic_tab(self):
        """Setup the basic information tab"""
        basic_widget = QWidget()
        layout = QVBoxLayout()
        
        # Basic info
        info_group = QGroupBox("Basic Information")
        info_layout = QFormLayout()
        
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Template title")
        info_layout.addRow("Title:", self.title_edit)
        
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        self.description_edit.setPlaceholderText("Description of what this template does")
        info_layout.addRow("Description:", self.description_edit)
        
        self.category_combo = QComboBox()
        self.category_combo.setEditable(True)
        categories = [cat.name for cat in DEFAULT_CATEGORIES]
        self.category_combo.addItems(categories)
        info_layout.addRow("Category:", self.category_combo)
        
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("Tags separated by commas")
        info_layout.addRow("Tags:", self.tags_edit)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Content
        content_group = QGroupBox("Template Content")
        content_layout = QVBoxLayout()
        
        # Help text
        help_label = QLabel("Use {variable_name} syntax for variables. Variables will be highlighted.")
        help_label.setStyleSheet("color: #666; font-style: italic;")
        content_layout.addWidget(help_label)
        
        self.content_edit = QPlainTextEdit()
        self.content_edit.setPlaceholderText("Enter your template content here...\n\nExample:\nHello {name}, welcome to {company}!")
        
        # Setup syntax highlighter
        self.highlighter = TemplateVariableHighlighter(self.content_edit.document())
        
        content_layout.addWidget(self.content_edit)
        
        # Auto-detect button
        auto_detect_btn = QPushButton("Auto-detect Variables")
        auto_detect_btn.clicked.connect(self.auto_detect_variables)
        content_layout.addWidget(auto_detect_btn)
        
        content_group.setLayout(content_layout)
        layout.addWidget(content_group)
        
        basic_widget.setLayout(layout)
        self.tab_widget.addTab(basic_widget, "Basic Info")
    
    def setup_variables_tab(self):
        """Setup the variables tab"""
        variables_widget = QWidget()
        layout = QVBoxLayout()
        
        # Variables list
        variables_group = QGroupBox("Template Variables")
        variables_layout = QVBoxLayout()
        
        # Variables table
        self.variables_table = QTableWidget()
        self.variables_table.setColumnCount(5)
        self.variables_table.setHorizontalHeaderLabels(["Name", "Type", "Required", "Default", "Description"])
        
        header = self.variables_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        
        variables_layout.addWidget(self.variables_table)
        
        # Variable buttons
        var_btn_layout = QHBoxLayout()
        
        self.add_var_btn = QPushButton("Add Variable")
        self.add_var_btn.clicked.connect(self.add_variable)
        
        self.edit_var_btn = QPushButton("Edit Variable")
        self.edit_var_btn.clicked.connect(self.edit_variable)
        
        self.remove_var_btn = QPushButton("Remove Variable")
        self.remove_var_btn.clicked.connect(self.remove_variable)
        
        var_btn_layout.addWidget(self.add_var_btn)
        var_btn_layout.addWidget(self.edit_var_btn)
        var_btn_layout.addWidget(self.remove_var_btn)
        var_btn_layout.addStretch()
        
        variables_layout.addLayout(var_btn_layout)
        variables_group.setLayout(variables_layout)
        layout.addWidget(variables_group)
        
        variables_widget.setLayout(layout)
        self.tab_widget.addTab(variables_widget, "Variables")
    
    def setup_preview_tab(self):
        """Setup the preview tab"""
        preview_widget = QWidget()
        layout = QVBoxLayout()
        
        # Preview
        preview_group = QGroupBox("Template Preview")
        preview_layout = QVBoxLayout()
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        preview_layout.addWidget(self.preview_text)
        
        update_preview_btn = QPushButton("Update Preview")
        update_preview_btn.clicked.connect(self.update_preview)
        preview_layout.addWidget(update_preview_btn)
        
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        # Validation results
        validation_group = QGroupBox("Validation Results")
        validation_layout = QVBoxLayout()
        
        self.validation_text = QTextEdit()
        self.validation_text.setReadOnly(True)
        self.validation_text.setMaximumHeight(150)
        validation_layout.addWidget(self.validation_text)
        
        validation_group.setLayout(validation_layout)
        layout.addWidget(validation_group)
        
        preview_widget.setLayout(layout)
        self.tab_widget.addTab(preview_widget, "Preview")
    
    def load_template_data(self):
        """Load template data into the form"""
        if not self.is_editing:
            return
        
        self.title_edit.setText(self.template.title)
        self.description_edit.setPlainText(self.template.description)
        self.category_combo.setCurrentText(self.template.category)
        self.tags_edit.setText(', '.join(self.template.tags))
        self.content_edit.setPlainText(self.template.content)
        
        self.refresh_variables_table()
        self.update_preview()
    
    def refresh_variables_table(self):
        """Refresh the variables table"""
        self.variables_table.setRowCount(len(self.template.variables))
        
        for row, variable in enumerate(self.template.variables):
            self.variables_table.setItem(row, 0, QTableWidgetItem(variable.name))
            self.variables_table.setItem(row, 1, QTableWidgetItem(variable.variable_type))
            self.variables_table.setItem(row, 2, QTableWidgetItem("Yes" if variable.required else "No"))
            self.variables_table.setItem(row, 3, QTableWidgetItem(variable.default_value))
            self.variables_table.setItem(row, 4, QTableWidgetItem(variable.description))
    
    def auto_detect_variables(self):
        """Auto-detect variables from content"""
        if not self.template_service:
            QMessageBox.warning(self, "Warning", "Template service not available for auto-detection.")
            return
        
        content = self.content_edit.toPlainText()
        if not content.strip():
            QMessageBox.information(self, "Info", "Please enter template content first.")
            return
        
        detected_vars = self.template_service.auto_detect_variables(content)
        
        if not detected_vars:
            QMessageBox.information(self, "Info", "No variables detected in the content.")
            return
        
        # Add detected variables that don't already exist
        added_count = 0
        for var in detected_vars:
            if not self.template.get_variable(var.name):
                self.template.add_variable(var)
                added_count += 1
        
        if added_count > 0:
            self.refresh_variables_table()
            QMessageBox.information(self, "Success", f"Added {added_count} variables.")
        else:
            QMessageBox.information(self, "Info", "All detected variables already exist.")
    
    def add_variable(self):
        """Add a new variable"""
        dialog = VariableEditDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            variable = dialog.get_variable()
            
            # Check if variable already exists
            if self.template.get_variable(variable.name):
                QMessageBox.warning(self, "Warning", f"Variable '{variable.name}' already exists.")
                return
            
            self.template.add_variable(variable)
            self.refresh_variables_table()
    
    def edit_variable(self):
        """Edit selected variable"""
        current_row = self.variables_table.currentRow()
        if current_row < 0:
            QMessageBox.information(self, "Info", "Please select a variable to edit.")
            return
        
        variable = self.template.variables[current_row]
        dialog = VariableEditDialog(variable, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_variable = dialog.get_variable()
            self.template.variables[current_row] = updated_variable
            self.refresh_variables_table()
    
    def remove_variable(self):
        """Remove selected variable"""
        current_row = self.variables_table.currentRow()
        if current_row < 0:
            QMessageBox.information(self, "Info", "Please select a variable to remove.")
            return
        
        variable = self.template.variables[current_row]
        reply = QMessageBox.question(
            self, "Confirm Remove",
            f"Are you sure you want to remove variable '{variable.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.template.variables.pop(current_row)
            self.refresh_variables_table()
    
    def update_preview(self):
        """Update the preview"""
        # Update template from form
        self.update_template_from_form()
        
        try:
            preview = self.template.get_preview()
            self.preview_text.setPlainText(preview)
        except Exception as e:
            self.preview_text.setPlainText(f"Preview error: {str(e)}")
    
    def validate_template(self):
        """Validate the template"""
        self.update_template_from_form()
        
        if not self.template_service:
            self.validation_text.setPlainText("Template service not available for validation.")
            return
        
        try:
            issues = self.template_service.validate_template(self.template)
            suggestions = self.template_service.suggest_improvements(self.template)
            
            result_text = ""
            
            if issues:
                result_text += "Issues Found:\n"
                for issue in issues:
                    result_text += f"• {issue}\n"
                result_text += "\n"
            
            if suggestions:
                result_text += "Suggestions:\n"
                for suggestion in suggestions:
                    result_text += f"• {suggestion}\n"
                result_text += "\n"
            
            if not issues and not suggestions:
                result_text = "✓ Template validation passed with no issues!"
            
            self.validation_text.setPlainText(result_text)
            
        except Exception as e:
            self.validation_text.setPlainText(f"Validation error: {str(e)}")
    
    def update_template_from_form(self):
        """Update template object from form data"""
        self.template.title = self.title_edit.text().strip()
        self.template.description = self.description_edit.toPlainText().strip()
        self.template.category = self.category_combo.currentText().strip()
        self.template.content = self.content_edit.toPlainText()
        
        # Parse tags
        tags_text = self.tags_edit.text().strip()
        if tags_text:
            self.template.tags = [tag.strip() for tag in tags_text.split(',') if tag.strip()]
        else:
            self.template.tags = []
    
    def save_template(self):
        """Save the template"""
        self.update_template_from_form()
        
        # Validate required fields
        if not self.template.title:
            QMessageBox.warning(self, "Validation Error", "Template title is required.")
            return
        
        if not self.template.content:
            QMessageBox.warning(self, "Validation Error", "Template content is required.")
            return
        
        if not self.template_service:
            QMessageBox.critical(self, "Error", "Template service not available.")
            return
        
        try:
            if self.is_editing:
                success = self.template_service.update_template(self.template)
                if success:
                    QMessageBox.information(self, "Success", "Template updated successfully!")
                    self.accept()
                else:
                    QMessageBox.critical(self, "Error", "Failed to update template.")
            else:
                template_id = self.template_service.create_template(self.template)
                if template_id:
                    QMessageBox.information(self, "Success", "Template created successfully!")
                    self.accept()
                else:
                    QMessageBox.critical(self, "Error", "Failed to create template.")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save template: {str(e)}")


class TemplateManagerDialog(QDialog):
    """Dialog for managing templates"""
    
    def __init__(self, template_service: TemplateService, parent=None):
        super().__init__(parent)
        self.template_service = template_service
        self.setWindowTitle("Template Manager")
        self.setModal(True)
        self.resize(900, 600)
        self.setup_ui()
        self.refresh_templates()
    
    def setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout()
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        self.new_template_btn = QPushButton("New Template")
        self.new_template_btn.clicked.connect(self.new_template)
        
        self.edit_template_btn = QPushButton("Edit Template")
        self.edit_template_btn.clicked.connect(self.edit_template)
        
        self.use_template_btn = QPushButton("Use Template")
        self.use_template_btn.clicked.connect(self.use_template)
        
        self.delete_template_btn = QPushButton("Delete Template")
        self.delete_template_btn.clicked.connect(self.delete_template)
        
        toolbar_layout.addWidget(self.new_template_btn)
        toolbar_layout.addWidget(self.edit_template_btn)
        toolbar_layout.addWidget(self.use_template_btn)
        toolbar_layout.addWidget(self.delete_template_btn)
        toolbar_layout.addStretch()
        
        # Search and filter
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search templates...")
        self.search_edit.textChanged.connect(self.filter_templates)
        
        self.category_filter = QComboBox()
        self.category_filter.addItem("All Categories")
        categories = self.template_service.get_categories()
        for category in categories:
            self.category_filter.addItem(category.name)
        self.category_filter.currentTextChanged.connect(self.filter_templates)
        
        toolbar_layout.addWidget(QLabel("Search:"))
        toolbar_layout.addWidget(self.search_edit)
        toolbar_layout.addWidget(QLabel("Category:"))
        toolbar_layout.addWidget(self.category_filter)
        
        layout.addLayout(toolbar_layout)
        
        # Templates list
        self.templates_tree = QTreeWidget()
        self.templates_tree.setHeaderLabels(["Title", "Category", "Variables", "Usage", "Updated"])
        self.templates_tree.itemDoubleClicked.connect(self.use_template)
        
        # Set column widths
        header = self.templates_tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(self.templates_tree)
        
        # Template details
        details_group = QGroupBox("Template Details")
        details_layout = QVBoxLayout()
        
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setMaximumHeight(150)
        details_layout.addWidget(self.details_text)
        
        details_group.setLayout(details_layout)
        layout.addWidget(details_group)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
        
        # Connect selection change
        self.templates_tree.itemSelectionChanged.connect(self.on_template_selected)
    
    def refresh_templates(self):
        """Refresh the templates list"""
        self.templates_tree.clear()
        
        try:
            templates = self.template_service.get_templates()
            
            for template in templates:
                item = QTreeWidgetItem([
                    template.title,
                    template.category,
                    str(len(template.variables)),
                    str(template.usage_count),
                    template.updated_at.strftime("%Y-%m-%d") if template.updated_at else ""
                ])
                item.setData(0, Qt.ItemDataRole.UserRole, template.id)
                self.templates_tree.addTopLevelItem(item)
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load templates: {str(e)}")
    
    def filter_templates(self):
        """Filter templates based on search and category"""
        search_text = self.search_edit.text().lower()
        category = self.category_filter.currentText()
        
        for i in range(self.templates_tree.topLevelItemCount()):
            item = self.templates_tree.topLevelItem(i)
            
            # Check search text
            title_match = search_text in item.text(0).lower()
            
            # Check category
            category_match = (category == "All Categories" or
                            category == item.text(1))
            
            # Show/hide item
            item.setHidden(not (title_match and category_match))
    
    def on_template_selected(self):
        """Handle template selection"""
        current_item = self.templates_tree.currentItem()
        if not current_item:
            self.details_text.clear()
            return
        
        template_id = current_item.data(0, Qt.ItemDataRole.UserRole)
        try:
            template = self.template_service.get_template(template_id)
            if template:
                details = f"Title: {template.title}\n"
                details += f"Category: {template.category}\n"
                details += f"Description: {template.description}\n\n"
                
                if template.variables:
                    details += "Variables:\n"
                    for var in template.variables:
                        details += f"• {var.name} ({var.variable_type})"
                        if var.required:
                            details += " *"
                        if var.description:
                            details += f" - {var.description}"
                        details += "\n"
                
                self.details_text.setPlainText(details)
        
        except Exception as e:
            self.details_text.setPlainText(f"Error loading template details: {str(e)}")
    
    def new_template(self):
        """Create a new template"""
        dialog = TemplateEditorDialog(template_service=self.template_service, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_templates()
    
    def edit_template(self):
        """Edit selected template"""
        current_item = self.templates_tree.currentItem()
        if not current_item:
            QMessageBox.information(self, "Info", "Please select a template to edit.")
            return
        
        template_id = current_item.data(0, Qt.ItemDataRole.UserRole)
        try:
            template = self.template_service.get_template(template_id)
            if template:
                dialog = TemplateEditorDialog(template=template, template_service=self.template_service, parent=self)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    self.refresh_templates()
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load template: {str(e)}")
    
    def use_template(self):
        """Use selected template"""
        current_item = self.templates_tree.currentItem()
        if not current_item:
            QMessageBox.information(self, "Info", "Please select a template to use.")
            return
        
        template_id = current_item.data(0, Qt.ItemDataRole.UserRole)
        try:
            template = self.template_service.get_template(template_id)
            if template:
                dialog = TemplateUsageDialog(template=template, template_service=self.template_service, parent=self)
                dialog.exec()
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load template: {str(e)}")
    
    def delete_template(self):
        """Delete selected template"""
        current_item = self.templates_tree.currentItem()
        if not current_item:
            QMessageBox.information(self, "Info", "Please select a template to delete.")
            return
        
        template_title = current_item.text(0)
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete template '{template_title}'?\n\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            template_id = current_item.data(0, Qt.ItemDataRole.UserRole)
            try:
                if self.template_service.delete_template(template_id):
                    self.refresh_templates()
                    QMessageBox.information(self, "Success", "Template deleted successfully.")
                else:
                    QMessageBox.critical(self, "Error", "Failed to delete template.")
            
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete template: {str(e)}")