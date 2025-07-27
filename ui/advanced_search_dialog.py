"""
Advanced search dialog for the Prompt Organizer application
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QLineEdit, QPushButton, QTextEdit, QComboBox,
    QDialogButtonBox, QGroupBox, QFormLayout, QCheckBox,
    QListWidget, QListWidgetItem, QSplitter, QScrollArea,
    QFrame, QGridLayout, QSpinBox, QDateEdit, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QFont, QSyntaxHighlighter, QTextCharFormat, QColor
from typing import List, Dict, Optional, Any
import re

from models.search_models import (
    AdvancedSearchEngine, SearchQueryParser, SearchField, 
    SearchOperator, SEARCH_EXAMPLES, SEARCH_HELP_TEXT
)


class SearchSyntaxHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for search queries"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_highlighting_rules()
    
    def setup_highlighting_rules(self):
        """Setup highlighting rules for search syntax"""
        self.highlighting_rules = []
        
        # Field names (field:)
        field_format = QTextCharFormat()
        field_format.setForeground(QColor("#0066cc"))
        field_format.setFontWeight(QFont.Weight.Bold)
        self.highlighting_rules.append((r'\b\w+:', field_format))
        
        # Quoted strings
        quoted_format = QTextCharFormat()
        quoted_format.setForeground(QColor("#d63384"))
        self.highlighting_rules.append((r'"[^"]*"', quoted_format))
        
        # Regex patterns
        regex_format = QTextCharFormat()
        regex_format.setForeground(QColor("#6f42c1"))
        regex_format.setFontItalic(True)
        self.highlighting_rules.append((r'/[^/]+/', regex_format))
        
        # Operators
        operator_format = QTextCharFormat()
        operator_format.setForeground(QColor("#e83e8c"))
        operator_format.setFontWeight(QFont.Weight.Bold)
        self.highlighting_rules.append((r'\b(AND|OR|NOT)\b', operator_format))
        
        # Negation
        negation_format = QTextCharFormat()
        negation_format.setForeground(QColor("#dc3545"))
        negation_format.setFontWeight(QFont.Weight.Bold)
        self.highlighting_rules.append((r'-\w+', negation_format))
    
    def highlightBlock(self, text):
        """Apply highlighting rules to text block"""
        for pattern, format_obj in self.highlighting_rules:
            for match in re.finditer(pattern, text):
                start = match.start()
                length = match.end() - start
                self.setFormat(start, length, format_obj)


class QueryBuilderWidget(QWidget):
    """Visual query builder widget"""
    
    query_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.query_parts = []
    
    def setup_ui(self):
        """Setup the query builder UI"""
        layout = QVBoxLayout()
        
        # Query parts list
        self.parts_list = QListWidget()
        self.parts_list.setMaximumHeight(150)
        layout.addWidget(QLabel("Query Parts:"))
        layout.addWidget(self.parts_list)
        
        # Add new part section
        add_group = QGroupBox("Add Search Term")
        add_layout = QFormLayout()
        
        # Field selection
        self.field_combo = QComboBox()
        self.field_combo.addItems([
            "All Fields", "Title", "Content", "Tags", 
            "Folder", "Created Date", "Updated Date"
        ])
        add_layout.addRow("Search In:", self.field_combo)
        
        # Search value
        self.value_edit = QLineEdit()
        self.value_edit.setPlaceholderText("Enter search term...")
        add_layout.addRow("Search For:", self.value_edit)
        
        # Options
        options_layout = QHBoxLayout()
        
        self.exact_cb = QCheckBox("Exact Match")
        self.regex_cb = QCheckBox("Regex")
        self.negate_cb = QCheckBox("Exclude")
        
        options_layout.addWidget(self.exact_cb)
        options_layout.addWidget(self.regex_cb)
        options_layout.addWidget(self.negate_cb)
        options_layout.addStretch()
        
        add_layout.addRow("Options:", options_layout)
        
        # Operator for next term
        self.operator_combo = QComboBox()
        self.operator_combo.addItems(["AND", "OR"])
        add_layout.addRow("Next Operator:", self.operator_combo)
        
        # Add button
        self.add_btn = QPushButton("Add Term")
        self.add_btn.clicked.connect(self.add_term)
        add_layout.addRow("", self.add_btn)
        
        add_group.setLayout(add_layout)
        layout.addWidget(add_group)
        
        # Control buttons
        btn_layout = QHBoxLayout()
        
        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.clicked.connect(self.clear_all)
        btn_layout.addWidget(self.clear_btn)
        
        self.remove_btn = QPushButton("Remove Selected")
        self.remove_btn.clicked.connect(self.remove_selected)
        btn_layout.addWidget(self.remove_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def add_term(self):
        """Add a new search term"""
        field_text = self.field_combo.currentText()
        value = self.value_edit.text().strip()
        
        if not value:
            return
        
        # Map field text to field code
        field_map = {
            "All Fields": "",
            "Title": "title:",
            "Content": "content:",
            "Tags": "tags:",
            "Folder": "folder:",
            "Created Date": "created:",
            "Updated Date": "updated:"
        }
        
        field_prefix = field_map.get(field_text, "")
        
        # Build the term string
        term_parts = []
        
        if self.negate_cb.isChecked():
            term_parts.append("-")
        
        if field_prefix:
            term_parts.append(field_prefix)
        
        if self.regex_cb.isChecked():
            term_parts.append(f"/{value}/")
        elif self.exact_cb.isChecked():
            term_parts.append(f'"{value}"')
        else:
            term_parts.append(value)
        
        term_string = "".join(term_parts)
        
        # Add operator if not the first term
        if self.query_parts:
            operator = self.operator_combo.currentText()
            term_string = f" {operator} {term_string}"
        
        self.query_parts.append(term_string)
        self.update_display()
        
        # Clear the input
        self.value_edit.clear()
        self.exact_cb.setChecked(False)
        self.regex_cb.setChecked(False)
        self.negate_cb.setChecked(False)
    
    def remove_selected(self):
        """Remove the selected term"""
        current_row = self.parts_list.currentRow()
        if current_row >= 0 and current_row < len(self.query_parts):
            self.query_parts.pop(current_row)
            self.update_display()
    
    def clear_all(self):
        """Clear all terms"""
        self.query_parts.clear()
        self.update_display()
    
    def update_display(self):
        """Update the display of query parts"""
        self.parts_list.clear()
        
        for part in self.query_parts:
            item = QListWidgetItem(part.strip())
            self.parts_list.addItem(item)
        
        # Emit the complete query
        query = "".join(self.query_parts)
        self.query_changed.emit(query)
    
    def set_query(self, query: str):
        """Set the query from a string"""
        # This is a simplified version - in practice you'd parse the query
        self.query_parts = [query] if query.strip() else []
        self.update_display()


class AdvancedSearchDialog(QDialog):
    """Advanced search dialog"""
    
    search_requested = pyqtSignal(str, dict)  # query, filters
    
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.search_engine = AdvancedSearchEngine(db_manager)
        self.parser = SearchQueryParser()
        
        self.setWindowTitle("Advanced Search")
        self.setModal(False)
        self.resize(800, 600)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout()
        
        # Main tabs
        self.tabs = QTabWidget()
        
        # Text search tab
        self.text_tab = self.create_text_search_tab()
        self.tabs.addTab(self.text_tab, "Text Search")
        
        # Visual builder tab
        self.builder_tab = self.create_builder_tab()
        self.tabs.addTab(self.builder_tab, "Visual Builder")
        
        # Examples tab
        self.examples_tab = self.create_examples_tab()
        self.tabs.addTab(self.examples_tab, "Examples & Help")
        
        layout.addWidget(self.tabs)
        
        # Additional filters
        filters_group = QGroupBox("Additional Filters")
        filters_layout = QFormLayout()
        
        # Folder filter
        self.folder_combo = QComboBox()
        self.folder_combo.addItem("All Folders", None)
        self.populate_folders()
        filters_layout.addRow("Folder:", self.folder_combo)
        
        # Tag filter
        self.tag_combo = QComboBox()
        self.tag_combo.addItem("All Tags", None)
        self.populate_tags()
        filters_layout.addRow("Tag:", self.tag_combo)
        
        # Other filters
        filter_options_layout = QHBoxLayout()
        
        self.favorites_cb = QCheckBox("Favorites Only")
        self.templates_cb = QCheckBox("Templates Only")
        
        filter_options_layout.addWidget(self.favorites_cb)
        filter_options_layout.addWidget(self.templates_cb)
        filter_options_layout.addStretch()
        
        filters_layout.addRow("Options:", filter_options_layout)
        
        filters_group.setLayout(filters_layout)
        layout.addWidget(filters_group)
        
        # Buttons
        buttons = QDialogButtonBox()
        
        self.search_btn = QPushButton("Search")
        self.search_btn.clicked.connect(self.perform_search)
        self.search_btn.setDefault(True)
        buttons.addButton(self.search_btn, QDialogButtonBox.ButtonRole.ActionRole)
        
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear_search)
        buttons.addButton(self.clear_btn, QDialogButtonBox.ButtonRole.ResetRole)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        buttons.addButton(close_btn, QDialogButtonBox.ButtonRole.RejectRole)
        
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def create_text_search_tab(self) -> QWidget:
        """Create the text search tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Query input
        query_group = QGroupBox("Search Query")
        query_layout = QVBoxLayout()
        
        self.query_edit = QTextEdit()
        self.query_edit.setMaximumHeight(100)
        self.query_edit.setFont(QFont("Consolas", 10))
        self.query_edit.setPlaceholderText("Enter your search query here...")
        
        # Add syntax highlighting
        self.highlighter = SearchSyntaxHighlighter(self.query_edit.document())
        
        query_layout.addWidget(self.query_edit)
        
        # Quick buttons
        quick_layout = QHBoxLayout()
        
        self.and_btn = QPushButton("AND")
        self.and_btn.clicked.connect(lambda: self.insert_text(" AND "))
        quick_layout.addWidget(self.and_btn)
        
        self.or_btn = QPushButton("OR")
        self.or_btn.clicked.connect(lambda: self.insert_text(" OR "))
        quick_layout.addWidget(self.or_btn)
        
        self.not_btn = QPushButton("NOT")
        self.not_btn.clicked.connect(lambda: self.insert_text(" NOT "))
        quick_layout.addWidget(self.not_btn)
        
        self.quote_btn = QPushButton("\" \"")
        self.quote_btn.clicked.connect(lambda: self.insert_text('""', -1))
        quick_layout.addWidget(self.quote_btn)
        
        self.regex_btn = QPushButton("/ /")
        self.regex_btn.clicked.connect(lambda: self.insert_text('//', -1))
        quick_layout.addWidget(self.regex_btn)
        
        quick_layout.addStretch()
        
        query_layout.addLayout(quick_layout)
        query_group.setLayout(query_layout)
        layout.addWidget(query_group)
        
        # Query validation
        self.validation_label = QLabel()
        self.validation_label.setStyleSheet("color: red; font-style: italic;")
        layout.addWidget(self.validation_label)
        
        # Connect validation
        self.query_edit.textChanged.connect(self.validate_query)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab
    
    def create_builder_tab(self) -> QWidget:
        """Create the visual builder tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Query builder
        self.query_builder = QueryBuilderWidget()
        self.query_builder.query_changed.connect(self.on_builder_query_changed)
        layout.addWidget(self.query_builder)
        
        # Generated query display
        generated_group = QGroupBox("Generated Query")
        generated_layout = QVBoxLayout()
        
        self.generated_query_edit = QLineEdit()
        self.generated_query_edit.setReadOnly(True)
        self.generated_query_edit.setFont(QFont("Consolas", 10))
        generated_layout.addWidget(self.generated_query_edit)
        
        generated_group.setLayout(generated_layout)
        layout.addWidget(generated_group)
        
        tab.setLayout(layout)
        return tab
    
    def create_examples_tab(self) -> QWidget:
        """Create the examples and help tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Examples
        examples_group = QGroupBox("Search Examples")
        examples_layout = QVBoxLayout()
        
        self.examples_list = QListWidget()
        
        for example in SEARCH_EXAMPLES:
            item = QListWidgetItem(f"{example['query']}\n{example['description']}")
            item.setData(Qt.ItemDataRole.UserRole, example['query'])
            self.examples_list.addItem(item)
        
        self.examples_list.itemDoubleClicked.connect(self.use_example)
        examples_layout.addWidget(self.examples_list)
        
        use_example_btn = QPushButton("Use Selected Example")
        use_example_btn.clicked.connect(self.use_selected_example)
        examples_layout.addWidget(use_example_btn)
        
        examples_group.setLayout(examples_layout)
        layout.addWidget(examples_group)
        
        # Help text
        help_group = QGroupBox("Search Syntax Help")
        help_layout = QVBoxLayout()
        
        help_text = QTextEdit()
        help_text.setPlainText(SEARCH_HELP_TEXT)
        help_text.setReadOnly(True)
        help_text.setFont(QFont("Consolas", 9))
        help_layout.addWidget(help_text)
        
        help_group.setLayout(help_layout)
        layout.addWidget(help_group)
        
        tab.setLayout(layout)
        return tab
    
    def populate_folders(self):
        """Populate the folder combo box"""
        try:
            folders = self.db.get_all_folders()
            for folder in folders:
                self.folder_combo.addItem(folder['name'], folder['id'])
        except Exception as e:
            print(f"Error loading folders: {e}")
    
    def populate_tags(self):
        """Populate the tag combo box"""
        try:
            tags = self.db.get_tags()
            for tag in tags:
                self.tag_combo.addItem(tag['name'], tag['id'])
        except Exception as e:
            print(f"Error loading tags: {e}")
    
    def insert_text(self, text: str, cursor_offset: int = 0):
        """Insert text at cursor position"""
        cursor = self.query_edit.textCursor()
        cursor.insertText(text)
        
        if cursor_offset != 0:
            position = cursor.position() + cursor_offset
            cursor.setPosition(position)
            self.query_edit.setTextCursor(cursor)
        
        self.query_edit.setFocus()
    
    def validate_query(self):
        """Validate the search query"""
        query = self.query_edit.toPlainText().strip()
        
        if not query:
            self.validation_label.clear()
            return
        
        try:
            # Try to parse the query
            parsed_query = self.parser.parse(query)
            
            # Check for regex errors
            for term in parsed_query.terms:
                if term.is_regex:
                    re.compile(term.value)
            
            self.validation_label.setText("✓ Valid query")
            self.validation_label.setStyleSheet("color: green; font-style: italic;")
            
        except re.error as e:
            self.validation_label.setText(f"✗ Regex error: {str(e)}")
            self.validation_label.setStyleSheet("color: red; font-style: italic;")
        except Exception as e:
            self.validation_label.setText(f"✗ Query error: {str(e)}")
            self.validation_label.setStyleSheet("color: red; font-style: italic;")
    
    def on_builder_query_changed(self, query: str):
        """Handle query change from builder"""
        self.generated_query_edit.setText(query)
    
    def use_example(self, item):
        """Use the double-clicked example"""
        query = item.data(Qt.ItemDataRole.UserRole)
        self.query_edit.setPlainText(query)
        self.tabs.setCurrentIndex(0)  # Switch to text search tab
    
    def use_selected_example(self):
        """Use the selected example"""
        current_item = self.examples_list.currentItem()
        if current_item:
            self.use_example(current_item)
    
    def get_current_query(self) -> str:
        """Get the current search query"""
        if self.tabs.currentIndex() == 0:  # Text search tab
            return self.query_edit.toPlainText().strip()
        elif self.tabs.currentIndex() == 1:  # Builder tab
            return self.generated_query_edit.text().strip()
        return ""
    
    def get_filters(self) -> Dict[str, Any]:
        """Get additional filters"""
        filters = {}
        
        # Folder filter
        folder_id = self.folder_combo.currentData()
        if folder_id is not None:
            filters['folder_id'] = folder_id
        
        # Tag filter
        tag_id = self.tag_combo.currentData()
        if tag_id is not None:
            filters['tag_ids'] = [tag_id]
        
        # Other filters
        if self.favorites_cb.isChecked():
            filters['is_favorite'] = True
        
        if self.templates_cb.isChecked():
            filters['is_template'] = True
        
        return filters
    
    def perform_search(self):
        """Perform the search"""
        query = self.get_current_query()
        filters = self.get_filters()
        
        if not query and not any(filters.values()):
            QMessageBox.information(
                self, "No Search Criteria", 
                "Please enter a search query or select filters."
            )
            return
        
        # Emit search signal
        self.search_requested.emit(query, filters)
    
    def clear_search(self):
        """Clear all search inputs"""
        self.query_edit.clear()
        self.query_builder.clear_all()
        self.generated_query_edit.clear()
        
        # Reset filters
        self.folder_combo.setCurrentIndex(0)
        self.tag_combo.setCurrentIndex(0)
        self.favorites_cb.setChecked(False)
        self.templates_cb.setChecked(False)
        
        self.validation_label.clear()
    
    def set_query(self, query: str):
        """Set the search query"""
        self.query_edit.setPlainText(query)
        self.query_builder.set_query(query)