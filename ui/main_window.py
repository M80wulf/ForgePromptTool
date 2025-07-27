"""
Main window for the Prompt Organizer application
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QMenuBar, QToolBar, QStatusBar, QTreeWidget, QTreeWidgetItem,
    QListWidget, QListWidgetItem, QTextEdit, QLineEdit, QPushButton,
    QLabel, QFrame, QScrollArea, QGroupBox, QCheckBox, QComboBox,
    QMessageBox, QFileDialog, QInputDialog, QDialog, QDialogButtonBox,
    QFormLayout, QColorDialog, QApplication
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize
from PyQt6.QtGui import (
    QAction, QIcon, QFont, QColor, QPalette, QKeySequence,
    QTextCharFormat, QSyntaxHighlighter, QTextDocument
)
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters import get_formatter_by_name
from pygments.util import ClassNotFound
import sys
import os
import json
import re
from datetime import datetime
from typing import List, Dict, Optional

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import DatabaseManager
from models.data_models import Prompt, Folder, Tag, SearchFilter
from ui.themes import get_theme_manager
from ui.settings_dialog import SettingsDialog
from ui.llm_dialog import LLMFeaturesDialog
from ui.analytics_dialog import AnalyticsDashboard
from ui.advanced_search_dialog import AdvancedSearchDialog
from ui.sharing_dialog import SharingDialog, ShareLinkViewerDialog
from config.settings import get_settings
from services.analytics_service import AnalyticsService
from services.sharing_service import SharingService
from services.performance_service import PerformanceService
from services.plugin_service import PluginManager
from models.analytics import EventType
from models.search_models import AdvancedSearchEngine
from ui.performance_dialog import PerformanceDialog
from ui.plugin_dialog import PluginDialog
from ui.batch_operations_dialog import BatchOperationsDialog
from ui.template_dialog import TemplateManagerDialog, TemplateUsageDialog, TemplateEditorDialog
from services.template_service import TemplateService
from ui.ai_suggestion_dialog import AISuggestionDialog, AISuggestionStatsDialog, AIPromptGeneratorDialog
from services.ai_suggestion_service import AISuggestionService
from ui.export_dialog import ExportDialog
from services.export_service import ExportService
from ui.community_dialog import CommunityBrowserDialog, SharePromptDialog
from services.community_service import CommunityService
from ui.update_dialog import UpdateDialog
from services.update_service import UpdateManager
from config.update_config import get_repo_config


class PromptSyntaxHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for prompts with basic formatting"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_highlighting_rules()
    
    def setup_highlighting_rules(self):
        """Setup highlighting rules for common prompt patterns"""
        self.highlighting_rules = []
        
        # Headers (lines starting with #)
        header_format = QTextCharFormat()
        header_format.setForeground(QColor("#0066cc"))
        header_format.setFontWeight(QFont.Weight.Bold)
        self.highlighting_rules.append((r'^#{1,6}\s.*$', header_format))
        
        # Bold text (**text**)
        bold_format = QTextCharFormat()
        bold_format.setFontWeight(QFont.Weight.Bold)
        self.highlighting_rules.append((r'\*\*([^*]+)\*\*', bold_format))
        
        # Italic text (*text*)
        italic_format = QTextCharFormat()
        italic_format.setFontItalic(True)
        self.highlighting_rules.append((r'\*([^*]+)\*', italic_format))
        
        # Code blocks (`code`)
        code_format = QTextCharFormat()
        code_format.setForeground(QColor("#d63384"))
        code_format.setBackground(QColor("#f8f9fa"))
        code_format.setFontFamily("Consolas")
        self.highlighting_rules.append((r'`([^`]+)`', code_format))
        
        # Variables/placeholders {variable}
        variable_format = QTextCharFormat()
        variable_format.setForeground(QColor("#6f42c1"))
        variable_format.setFontWeight(QFont.Weight.Bold)
        self.highlighting_rules.append((r'\{([^}]+)\}', variable_format))
    
    def highlightBlock(self, text):
        """Apply highlighting rules to text block"""
        import re
        
        for pattern, format_obj in self.highlighting_rules:
            for match in re.finditer(pattern, text, re.MULTILINE):
                start = match.start()
                length = match.end() - start
                self.setFormat(start, length, format_obj)


class TagWidget(QWidget):
    """Custom widget for displaying and managing tags"""
    
    tag_clicked = pyqtSignal(int)  # Emits tag ID when clicked
    tag_removed = pyqtSignal(int)  # Emits tag ID when removed
    
    def __init__(self, tag: Tag, removable=True, parent=None):
        super().__init__(parent)
        self.tag = tag
        self.removable = removable
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the tag widget UI"""
        layout = QHBoxLayout()
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(2)
        
        # Tag label
        self.label = QLabel(self.tag.name)
        self.label.setStyleSheet(f"""
            QLabel {{
                background-color: {self.tag.color};
                color: white;
                padding: 2px 6px;
                border-radius: 10px;
                font-size: 11px;
            }}
        """)
        self.label.mousePressEvent = self.on_tag_clicked
        layout.addWidget(self.label)
        
        # Remove button
        if self.removable:
            self.remove_btn = QPushButton("×")
            self.remove_btn.setFixedSize(16, 16)
            self.remove_btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(255, 255, 255, 0.3);
                    border: none;
                    border-radius: 8px;
                    color: white;
                    font-weight: bold;
                    font-size: 10px;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.5);
                }
            """)
            self.remove_btn.clicked.connect(lambda: self.tag_removed.emit(self.tag.id))
            layout.addWidget(self.remove_btn)
        
        self.setLayout(layout)
    
    def on_tag_clicked(self, event):
        """Handle tag click"""
        self.tag_clicked.emit(self.tag.id)


class TagDialog(QDialog):
    """Dialog for creating/editing tags"""
    
    def __init__(self, tag: Tag = None, parent=None):
        super().__init__(parent)
        self.tag = tag
        self.setWindowTitle("Edit Tag" if tag else "Create Tag")
        self.setModal(True)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout()
        
        # Form layout
        form_layout = QFormLayout()
        
        # Name field
        self.name_edit = QLineEdit()
        if self.tag:
            self.name_edit.setText(self.tag.name)
        form_layout.addRow("Name:", self.name_edit)
        
        # Color field
        color_layout = QHBoxLayout()
        self.color_edit = QLineEdit()
        self.color_edit.setText(self.tag.color if self.tag else "#007bff")
        self.color_btn = QPushButton("Choose Color")
        self.color_btn.clicked.connect(self.choose_color)
        color_layout.addWidget(self.color_edit)
        color_layout.addWidget(self.color_btn)
        form_layout.addRow("Color:", color_layout)
        
        layout.addLayout(form_layout)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def choose_color(self):
        """Open color chooser dialog"""
        color = QColorDialog.getColor(QColor(self.color_edit.text()), self)
        if color.isValid():
            self.color_edit.setText(color.name())
    
    def get_tag_data(self):
        """Get tag data from dialog"""
        return {
            'name': self.name_edit.text().strip(),
            'color': self.color_edit.text().strip()
        }


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.current_prompt = None
        self.unsaved_changes = False
        self.search_filter = SearchFilter()
        
        # Initialize settings and theme management
        self.settings = get_settings()
        self.theme_manager = get_theme_manager()
        
        # Initialize analytics service
        db_path = self.settings.get_database_path()
        self.analytics = AnalyticsService(db_path)
        
        # Initialize advanced search engine
        self.advanced_search_engine = AdvancedSearchEngine(self.db)
        
        # Initialize sharing service
        self.sharing_service = SharingService(db_path)
        
        # Initialize performance service
        self.performance_service = PerformanceService(db_path)
        
        # Initialize plugin manager
        self.plugin_manager = PluginManager(self, self.db, self.settings)
        self.plugin_manager.set_services(self.analytics, self.performance_service, self.sharing_service)
        
        # Initialize template service
        self.template_service = TemplateService(self.db)
        
        # Initialize AI suggestion service
        self.ai_suggestion_service = AISuggestionService(self.db)
        
        # Initialize export service
        self.export_service = ExportService(self.db)
        
        # Initialize community service
        self.community_service = CommunityService(self.db)
        
        # Initialize update manager
        repo_config = get_repo_config()
        self.update_manager = UpdateManager(
            repo_owner=repo_config["owner"],
            repo_name=repo_config["name"],
            current_version=repo_config["current_version"]
        )
        
        self.setWindowTitle("Prompt Organizer")
        self.setGeometry(100, 100, 1200, 800)
        
        self.setup_ui()
        self.setup_menus()
        self.setup_toolbar()
        self.setup_status_bar()
        self.setup_shortcuts()
        
        # Apply theme
        self.apply_current_theme()
        
        # Connect theme change signal
        self.theme_manager.theme_changed.connect(self.on_theme_changed)
        
        # Load initial data
        self.refresh_folders()
        self.refresh_prompts()
        self.refresh_tags()
        
        # Setup auto-save timer
        config = self.settings.get_config()
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self.auto_save)
        if config.auto_save:
            self.auto_save_timer.start(config.auto_save_interval * 1000)
        
        # Load window geometry
        self.load_window_state()
        
        # Load plugins
        self.load_plugins()
    
    def setup_ui(self):
        """Setup the main UI layout"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Create main splitter
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.main_splitter)
        
        # Left panel (folders and tags)
        self.setup_left_panel()
        
        # Center panel (prompt list and search)
        self.setup_center_panel()
        
        # Right panel (editor and metadata)
        self.setup_right_panel()
        
        # Set splitter proportions
        self.main_splitter.setSizes([250, 400, 550])
    
    def setup_left_panel(self):
        """Setup the left panel with folders and tags"""
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_widget.setLayout(left_layout)
        
        # Folders section
        folders_group = QGroupBox("Folders")
        folders_layout = QVBoxLayout()
        
        # Folder tree
        self.folder_tree = QTreeWidget()
        self.folder_tree.setHeaderLabel("Folders")
        self.folder_tree.itemClicked.connect(self.on_folder_selected)
        self.folder_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.folder_tree.customContextMenuRequested.connect(self.show_folder_context_menu)
        folders_layout.addWidget(self.folder_tree)
        
        # Folder buttons
        folder_btn_layout = QHBoxLayout()
        self.add_folder_btn = QPushButton("Add")
        self.add_folder_btn.clicked.connect(self.add_folder)
        self.rename_folder_btn = QPushButton("Rename")
        self.rename_folder_btn.clicked.connect(self.rename_folder)
        self.delete_folder_btn = QPushButton("Delete")
        self.delete_folder_btn.clicked.connect(self.delete_folder)
        
        folder_btn_layout.addWidget(self.add_folder_btn)
        folder_btn_layout.addWidget(self.rename_folder_btn)
        folder_btn_layout.addWidget(self.delete_folder_btn)
        folders_layout.addLayout(folder_btn_layout)
        
        folders_group.setLayout(folders_layout)
        left_layout.addWidget(folders_group)
        
        # Tags section
        tags_group = QGroupBox("Tags")
        tags_layout = QVBoxLayout()
        
        # Tag scroll area
        self.tag_scroll = QScrollArea()
        self.tag_scroll.setWidgetResizable(True)
        self.tag_scroll.setMaximumHeight(200)
        self.tag_widget = QWidget()
        self.tag_layout = QVBoxLayout()
        self.tag_widget.setLayout(self.tag_layout)
        self.tag_scroll.setWidget(self.tag_widget)
        tags_layout.addWidget(self.tag_scroll)
        
        # Tag buttons
        tag_btn_layout = QHBoxLayout()
        self.add_tag_btn = QPushButton("Add Tag")
        self.add_tag_btn.clicked.connect(self.add_tag)
        self.manage_tags_btn = QPushButton("Manage")
        self.manage_tags_btn.clicked.connect(self.manage_tags)
        
        tag_btn_layout.addWidget(self.add_tag_btn)
        tag_btn_layout.addWidget(self.manage_tags_btn)
        tags_layout.addLayout(tag_btn_layout)
        
        tags_group.setLayout(tags_layout)
        left_layout.addWidget(tags_group)
        
        # Add stretch to push everything to top
        left_layout.addStretch()
        
        self.main_splitter.addWidget(left_widget)
    
    def setup_center_panel(self):
        """Setup the center panel with prompt list and search"""
        center_widget = QWidget()
        center_layout = QVBoxLayout()
        center_widget.setLayout(center_layout)
        
        # Search section
        search_group = QGroupBox("Search & Filter")
        search_layout = QVBoxLayout()
        
        # Search bar
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search prompts...")
        self.search_edit.textChanged.connect(self.on_search_changed)
        search_layout.addWidget(self.search_edit)
        
        # Filter options
        filter_layout = QHBoxLayout()
        
        self.favorites_cb = QCheckBox("Favorites")
        self.favorites_cb.stateChanged.connect(self.on_filter_changed)
        filter_layout.addWidget(self.favorites_cb)
        
        self.templates_cb = QCheckBox("Templates")
        self.templates_cb.stateChanged.connect(self.on_filter_changed)
        filter_layout.addWidget(self.templates_cb)
        
        self.clear_filters_btn = QPushButton("Clear")
        self.clear_filters_btn.clicked.connect(self.clear_filters)
        filter_layout.addWidget(self.clear_filters_btn)
        
        search_layout.addLayout(filter_layout)
        search_group.setLayout(search_layout)
        center_layout.addWidget(search_group)
        
        # Prompt list
        prompts_group = QGroupBox("Prompts")
        prompts_layout = QVBoxLayout()
        
        self.prompt_list = QListWidget()
        self.prompt_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)  # Enable multi-selection
        self.prompt_list.itemClicked.connect(self.on_prompt_selected)
        self.prompt_list.itemSelectionChanged.connect(self.on_prompt_selection_changed)
        self.prompt_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.prompt_list.customContextMenuRequested.connect(self.show_prompt_context_menu)
        prompts_layout.addWidget(self.prompt_list)
        
        # Prompt buttons
        prompt_btn_layout = QHBoxLayout()
        self.new_prompt_btn = QPushButton("New")
        self.new_prompt_btn.clicked.connect(self.new_prompt)
        self.duplicate_prompt_btn = QPushButton("Duplicate")
        self.duplicate_prompt_btn.clicked.connect(self.duplicate_prompt)
        self.delete_prompt_btn = QPushButton("Delete")
        self.delete_prompt_btn.clicked.connect(self.delete_prompt)
        
        prompt_btn_layout.addWidget(self.new_prompt_btn)
        prompt_btn_layout.addWidget(self.duplicate_prompt_btn)
        prompt_btn_layout.addWidget(self.delete_prompt_btn)
        prompts_layout.addLayout(prompt_btn_layout)
        
        # Batch operations section (initially hidden)
        self.batch_operations_frame = QFrame()
        self.batch_operations_frame.setFrameStyle(QFrame.Shape.Box)
        self.batch_operations_frame.setStyleSheet("QFrame { background-color: #f0f0f0; border: 1px solid #ccc; }")
        self.batch_operations_frame.setVisible(False)
        
        batch_layout = QVBoxLayout()
        self.batch_operations_frame.setLayout(batch_layout)
        
        # Batch operations header
        batch_header_layout = QHBoxLayout()
        self.batch_info_label = QLabel("0 prompts selected")
        self.batch_info_label.setFont(QFont("", 9, QFont.Weight.Bold))
        batch_header_layout.addWidget(self.batch_info_label)
        batch_header_layout.addStretch()
        
        self.clear_selection_btn = QPushButton("Clear Selection")
        self.clear_selection_btn.clicked.connect(self.clear_prompt_selection)
        batch_header_layout.addWidget(self.clear_selection_btn)
        batch_layout.addLayout(batch_header_layout)
        
        # Quick batch operations
        quick_batch_layout = QHBoxLayout()
        self.batch_operations_btn = QPushButton("Batch Operations...")
        self.batch_operations_btn.clicked.connect(self.show_batch_operations)
        self.quick_delete_btn = QPushButton("Delete All")
        self.quick_delete_btn.setStyleSheet("QPushButton { background-color: #dc3545; color: white; }")
        self.quick_delete_btn.clicked.connect(self.quick_batch_delete)
        self.quick_copy_btn = QPushButton("Copy All")
        self.quick_copy_btn.clicked.connect(self.quick_batch_copy)
        
        quick_batch_layout.addWidget(self.batch_operations_btn)
        quick_batch_layout.addWidget(self.quick_copy_btn)
        quick_batch_layout.addWidget(self.quick_delete_btn)
        quick_batch_layout.addStretch()
        batch_layout.addLayout(quick_batch_layout)
        
        prompts_layout.addWidget(self.batch_operations_frame)
        
        prompts_group.setLayout(prompts_layout)
        center_layout.addWidget(prompts_group)
        
        self.main_splitter.addWidget(center_widget)
    
    def setup_right_panel(self):
        """Setup the right panel with editor and metadata"""
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_widget.setLayout(right_layout)
        
        # Editor section
        editor_group = QGroupBox("Editor")
        editor_layout = QVBoxLayout()
        
        # Title row (moved to its own row for more space)
        title_row_layout = QHBoxLayout()
        title_row_layout.addWidget(QLabel("Title:"))
        
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Prompt title...")
        self.title_edit.textChanged.connect(self.on_content_changed)
        title_row_layout.addWidget(self.title_edit)
        
        editor_layout.addLayout(title_row_layout)
        
        # Controls row (checkboxes and buttons)
        controls_layout = QHBoxLayout()
        
        self.favorite_cb = QCheckBox("Favorite")
        self.favorite_cb.stateChanged.connect(self.on_content_changed)
        controls_layout.addWidget(self.favorite_cb)
        
        self.template_cb = QCheckBox("Template")
        self.template_cb.stateChanged.connect(self.on_content_changed)
        controls_layout.addWidget(self.template_cb)
        
        controls_layout.addStretch()  # Add space between checkboxes and buttons
        
        # AI Prompt Generator button
        self.generate_prompt_btn = QPushButton("Generate Prompt")
        self.generate_prompt_btn.clicked.connect(self.show_ai_prompt_generator)
        self.generate_prompt_btn.setToolTip("Generate a complete prompt from a short description")
        controls_layout.addWidget(self.generate_prompt_btn)
        
        # Template actions
        self.create_template_btn = QPushButton("Create Template")
        self.create_template_btn.clicked.connect(self.create_template_from_prompt)
        self.create_template_btn.setToolTip("Create a template from this prompt")
        controls_layout.addWidget(self.create_template_btn)
        
        # AI Suggestions button
        self.ai_suggestions_btn = QPushButton("AI Suggestions")
        self.ai_suggestions_btn.clicked.connect(self.show_ai_suggestions)
        self.ai_suggestions_btn.setToolTip("Get AI-powered suggestions for this prompt")
        controls_layout.addWidget(self.ai_suggestions_btn)
        
        editor_layout.addLayout(controls_layout)
        
        # Text editor
        self.text_editor = QTextEdit()
        self.text_editor.setFont(QFont("Consolas", 11))
        self.text_editor.textChanged.connect(self.on_content_changed)
        
        # Setup syntax highlighter
        self.highlighter = PromptSyntaxHighlighter(self.text_editor.document())
        
        editor_layout.addWidget(self.text_editor)
        
        # Editor buttons
        editor_btn_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_prompt)
        self.save_btn.setEnabled(False)
        
        self.copy_btn = QPushButton("Copy")
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        
        self.copy_modified_btn = QPushButton("Copy Modified")
        self.copy_modified_btn.clicked.connect(self.copy_modified_to_clipboard)
        
        editor_btn_layout.addWidget(self.save_btn)
        editor_btn_layout.addWidget(self.copy_btn)
        editor_btn_layout.addWidget(self.copy_modified_btn)
        
        # Template button
        self.use_template_btn = QPushButton("Use Template")
        self.use_template_btn.clicked.connect(self.show_template_usage)
        self.use_template_btn.setToolTip("Use a template to generate content")
        editor_btn_layout.addWidget(self.use_template_btn)
        
        editor_btn_layout.addStretch()
        
        editor_layout.addLayout(editor_btn_layout)
        editor_group.setLayout(editor_layout)
        right_layout.addWidget(editor_group)
        
        # Tags section
        tags_group = QGroupBox("Tags")
        tags_layout = QVBoxLayout()
        
        # Current prompt tags
        self.prompt_tags_scroll = QScrollArea()
        self.prompt_tags_scroll.setWidgetResizable(True)
        self.prompt_tags_scroll.setMaximumHeight(100)
        self.prompt_tags_widget = QWidget()
        self.prompt_tags_layout = QVBoxLayout()
        self.prompt_tags_widget.setLayout(self.prompt_tags_layout)
        self.prompt_tags_scroll.setWidget(self.prompt_tags_widget)
        tags_layout.addWidget(self.prompt_tags_scroll)
        
        # Add tag to prompt
        add_tag_layout = QHBoxLayout()
        self.tag_combo = QComboBox()
        self.tag_combo.setEditable(True)
        self.add_tag_to_prompt_btn = QPushButton("Add Tag")
        self.add_tag_to_prompt_btn.clicked.connect(self.add_tag_to_prompt)
        
        add_tag_layout.addWidget(self.tag_combo)
        add_tag_layout.addWidget(self.add_tag_to_prompt_btn)
        tags_layout.addLayout(add_tag_layout)
        
        tags_group.setLayout(tags_layout)
        right_layout.addWidget(tags_group)
        
        # Metadata section
        metadata_group = QGroupBox("Metadata")
        metadata_layout = QFormLayout()
        
        self.created_label = QLabel("-")
        self.updated_label = QLabel("-")
        self.folder_label = QLabel("-")
        
        metadata_layout.addRow("Created:", self.created_label)
        metadata_layout.addRow("Updated:", self.updated_label)
        metadata_layout.addRow("Folder:", self.folder_label)
        
        metadata_group.setLayout(metadata_layout)
        right_layout.addWidget(metadata_group)
        
        self.main_splitter.addWidget(right_widget)
    
    def setup_menus(self):
        """Setup application menus"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        new_action = QAction("New Prompt", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self.new_prompt)
        file_menu.addAction(new_action)
        
        file_menu.addSeparator()
        
        import_action = QAction("Import...", self)
        import_action.triggered.connect(self.import_data)
        file_menu.addAction(import_action)
        
        export_action = QAction("Export...", self)
        export_action.triggered.connect(self.show_export_dialog)
        file_menu.addAction(export_action)
        
        export_selected_action = QAction("Export Selected...", self)
        export_selected_action.triggered.connect(self.export_selected_prompts)
        file_menu.addAction(export_selected_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("Edit")
        
        copy_action = QAction("Copy", self)
        copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        copy_action.triggered.connect(self.copy_to_clipboard)
        edit_menu.addAction(copy_action)
        
        save_action = QAction("Save", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_prompt)
        edit_menu.addAction(save_action)
        
        edit_menu.addSeparator()
        
        # Selection submenu
        selection_menu = edit_menu.addMenu("Selection")
        
        select_all_action = QAction("Select All Prompts", self)
        select_all_action.setShortcut("Ctrl+A")
        select_all_action.triggered.connect(self.select_all_prompts)
        selection_menu.addAction(select_all_action)
        
        invert_selection_action = QAction("Invert Selection", self)
        invert_selection_action.setShortcut("Ctrl+I")
        invert_selection_action.triggered.connect(self.invert_prompt_selection)
        selection_menu.addAction(invert_selection_action)
        
        clear_selection_action = QAction("Clear Selection", self)
        clear_selection_action.setShortcut("Escape")
        clear_selection_action.triggered.connect(self.clear_prompt_selection)
        selection_menu.addAction(clear_selection_action)
        
        edit_menu.addSeparator()
        
        # Batch operations submenu
        batch_menu = edit_menu.addMenu("Batch Operations")
        
        batch_operations_action = QAction("Batch Operations...", self)
        batch_operations_action.setShortcut("Ctrl+B")
        batch_operations_action.triggered.connect(self.show_batch_operations)
        batch_menu.addAction(batch_operations_action)
        
        batch_menu.addSeparator()
        
        batch_copy_action = QAction("Copy All Selected", self)
        batch_copy_action.setShortcut("Ctrl+Shift+C")
        batch_copy_action.triggered.connect(self.quick_batch_copy)
        batch_menu.addAction(batch_copy_action)
        
        batch_delete_action = QAction("Delete All Selected", self)
        batch_delete_action.setShortcut("Ctrl+Shift+Delete")
        batch_delete_action.triggered.connect(self.quick_batch_delete)
        batch_menu.addAction(batch_delete_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        refresh_action = QAction("Refresh", self)
        refresh_action.setShortcut(QKeySequence.StandardKey.Refresh)
        refresh_action.triggered.connect(self.refresh_all)
        view_menu.addAction(refresh_action)
        
        view_menu.addSeparator()
        
        advanced_search_action = QAction("Advanced Search...", self)
        advanced_search_action.setShortcut("Ctrl+Shift+F")
        advanced_search_action.triggered.connect(self.show_advanced_search)
        view_menu.addAction(advanced_search_action)
        
        analytics_action = QAction("Analytics Dashboard...", self)
        analytics_action.setShortcut("Ctrl+Shift+A")
        analytics_action.triggered.connect(self.show_analytics_dashboard)
        view_menu.addAction(analytics_action)
        
        performance_action = QAction("Performance Tracking...", self)
        performance_action.setShortcut("Ctrl+Shift+P")
        performance_action.triggered.connect(self.show_performance_tracking)
        view_menu.addAction(performance_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("Tools")
        
        manage_tags_action = QAction("Manage Tags", self)
        manage_tags_action.triggered.connect(self.manage_tags)
        tools_menu.addAction(manage_tags_action)
        
        tools_menu.addSeparator()
        
        # LLM Features submenu
        llm_menu = tools_menu.addMenu("LLM Features")
        
        llm_features_action = QAction("Open LLM Assistant...", self)
        llm_features_action.setShortcut("Ctrl+L")
        llm_features_action.triggered.connect(self.show_llm_features)
        llm_menu.addAction(llm_features_action)
        
        llm_menu.addSeparator()
        
        rewrite_action = QAction("Rewrite Prompt", self)
        rewrite_action.setShortcut("Ctrl+R")
        rewrite_action.triggered.connect(self.quick_rewrite)
        llm_menu.addAction(rewrite_action)
        
        explain_action = QAction("Explain Prompt", self)
        explain_action.triggered.connect(self.quick_explain)
        llm_menu.addAction(explain_action)
        
        improve_action = QAction("Suggest Improvements", self)
        improve_action.triggered.connect(self.quick_improve)
        llm_menu.addAction(improve_action)
        
        auto_tag_action = QAction("Generate Tags", self)
        auto_tag_action.triggered.connect(self.quick_auto_tag)
        llm_menu.addAction(auto_tag_action)
        
        tools_menu.addSeparator()
        
        # AI Suggestions submenu
        ai_menu = tools_menu.addMenu("AI Suggestions")
        
        ai_suggestions_action = QAction("Analyze Current Prompt...", self)
        ai_suggestions_action.setShortcut("Ctrl+Shift+I")
        ai_suggestions_action.triggered.connect(self.show_ai_suggestions)
        ai_menu.addAction(ai_suggestions_action)
        
        ai_stats_action = QAction("Suggestion Statistics...", self)
        ai_stats_action.triggered.connect(self.show_ai_suggestion_stats)
        ai_menu.addAction(ai_stats_action)
        
        tools_menu.addSeparator()
        
        # Sharing submenu
        sharing_menu = tools_menu.addMenu("Sharing & Collaboration")
        
        share_prompt_action = QAction("Share Current Prompt...", self)
        share_prompt_action.setShortcut("Ctrl+Shift+S")
        share_prompt_action.triggered.connect(self.share_current_prompt)
        sharing_menu.addAction(share_prompt_action)
        
        view_shared_action = QAction("View Shared Prompt...", self)
        view_shared_action.triggered.connect(self.view_shared_prompt)
        sharing_menu.addAction(view_shared_action)
        
        my_shares_action = QAction("My Shared Prompts...", self)
        my_shares_action.triggered.connect(self.show_my_shared_prompts)
        sharing_menu.addAction(my_shares_action)
        
        tools_menu.addSeparator()
        
        # Plugin management
        plugin_manager_action = QAction("Plugin Manager...", self)
        plugin_manager_action.setShortcut("Ctrl+Shift+P")
        plugin_manager_action.triggered.connect(self.show_plugin_manager)
        tools_menu.addAction(plugin_manager_action)
        
        tools_menu.addSeparator()
        
        settings_action = QAction("Settings...", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)
        
        tools_menu.addSeparator()
        
        # Template submenu
        template_menu = tools_menu.addMenu("Templates")
        
        template_manager_action = QAction("Template Manager...", self)
        template_manager_action.setShortcut("Ctrl+T")
        template_manager_action.triggered.connect(self.show_template_manager)
        template_menu.addAction(template_manager_action)
        
        new_template_action = QAction("New Template...", self)
        new_template_action.setShortcut("Ctrl+Shift+T")
        new_template_action.triggered.connect(self.new_template)
        template_menu.addAction(new_template_action)
        
        template_menu.addSeparator()
        
        use_template_action = QAction("Use Template...", self)
        use_template_action.setShortcut("Ctrl+U")
        use_template_action.triggered.connect(self.show_template_usage)
        template_menu.addAction(use_template_action)
        
        create_from_prompt_action = QAction("Create Template from Current Prompt", self)
        create_from_prompt_action.triggered.connect(self.create_template_from_prompt)
        template_menu.addAction(create_from_prompt_action)
        
        tools_menu.addSeparator()
        
        # Community submenu
        community_menu = tools_menu.addMenu("Community Library")
        
        browse_community_action = QAction("Browse Community Prompts...", self)
        browse_community_action.setShortcut("Ctrl+Shift+B")
        browse_community_action.triggered.connect(self.show_community_browser)
        community_menu.addAction(browse_community_action)
        
        share_to_community_action = QAction("Share Current Prompt...", self)
        share_to_community_action.setShortcut("Ctrl+Shift+H")
        share_to_community_action.triggered.connect(self.share_prompt_to_community)
        community_menu.addAction(share_to_community_action)
        
        community_menu.addSeparator()
        
        my_shared_prompts_action = QAction("My Shared Prompts", self)
        my_shared_prompts_action.triggered.connect(self.show_my_community_prompts)
        community_menu.addAction(my_shared_prompts_action)
        
        community_stats_action = QAction("Community Statistics", self)
        community_stats_action.triggered.connect(self.show_community_stats)
        community_menu.addAction(community_stats_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        # Update actions
        check_updates_action = QAction("Check for Updates...", self)
        check_updates_action.setShortcut("Ctrl+U")
        check_updates_action.triggered.connect(self.show_update_dialog)
        help_menu.addAction(check_updates_action)
        
        help_menu.addSeparator()
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_toolbar(self):
        """Setup application toolbar"""
        toolbar = self.addToolBar("Main")
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        
        # New prompt
        new_action = QAction("New", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self.new_prompt)
        toolbar.addAction(new_action)
        
        # Save
        save_action = QAction("Save", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_prompt)
        toolbar.addAction(save_action)
        
        toolbar.addSeparator()
        
        # Copy
        copy_action = QAction("Copy", self)
        copy_action.triggered.connect(self.copy_to_clipboard)
        toolbar.addAction(copy_action)
        
        toolbar.addSeparator()
        
        # LLM Features
        llm_action = QAction("LLM", self)
        llm_action.setShortcut("Ctrl+L")
        llm_action.triggered.connect(self.show_llm_features)
        llm_action.setToolTip("Open LLM Assistant")
        toolbar.addAction(llm_action)
        
        toolbar.addSeparator()
        
        # Advanced Search
        search_action = QAction("Search", self)
        search_action.setShortcut("Ctrl+Shift+F")
        search_action.triggered.connect(self.show_advanced_search)
        search_action.setToolTip("Advanced Search")
        toolbar.addAction(search_action)
        
        # Refresh
        refresh_action = QAction("Refresh", self)
        refresh_action.triggered.connect(self.refresh_all)
        toolbar.addAction(refresh_action)
        
        toolbar.addSeparator()
        
        # Templates
        template_action = QAction("Templates", self)
        template_action.setShortcut("Ctrl+T")
        template_action.triggered.connect(self.show_template_manager)
        template_action.setToolTip("Template Manager")
        toolbar.addAction(template_action)
        
        # AI Suggestions
        ai_action = QAction("AI Suggestions", self)
        ai_action.setShortcut("Ctrl+Shift+I")
        ai_action.triggered.connect(self.show_ai_suggestions)
        ai_action.setToolTip("AI-powered prompt analysis and suggestions")
        toolbar.addAction(ai_action)
        
        # Export
        export_action = QAction("Export", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self.show_export_dialog)
        export_action.setToolTip("Export prompts to various formats")
        toolbar.addAction(export_action)
        
        toolbar.addSeparator()
        
        # Community
        community_action = QAction("Community", self)
        community_action.setShortcut("Ctrl+Shift+B")
        community_action.triggered.connect(self.show_community_browser)
        community_action.setToolTip("Browse and share prompts with the community")
        toolbar.addAction(community_action)
    
    def setup_status_bar(self):
        """Setup status bar"""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")
        
        # Add permanent widgets
        self.prompt_count_label = QLabel("0 prompts")
        self.status_bar.addPermanentWidget(self.prompt_count_label)
    
    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        # Additional shortcuts beyond menu ones
        pass
    
    # Event handlers
    def on_folder_selected(self, item):
        """Handle folder selection"""
        folder_id = item.data(0, Qt.ItemDataRole.UserRole)
        self.search_filter.folder_id = folder_id
        self.refresh_prompts()
    
    def on_prompt_selected(self, item):
        """Handle prompt selection"""
        if self.unsaved_changes:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "You have unsaved changes. Do you want to save them?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.save_prompt()
            elif reply == QMessageBox.StandardButton.Cancel:
                return
        
        prompt_id = item.data(Qt.ItemDataRole.UserRole)
        self.load_prompt(prompt_id)
        
        # Track prompt view
        self.analytics.track_event(EventType.PROMPT_VIEWED, prompt_id)
    
    def on_search_changed(self):
        """Handle search text change"""
        search_term = self.search_edit.text()
        self.search_filter.search_term = search_term
        
        # Use advanced search if the term contains special syntax
        if search_term.strip() and self.is_advanced_search_query(search_term):
            self.perform_advanced_search(search_term)
        else:
            self.refresh_prompts()

        # Track search events (only for non-empty searches)
        if search_term.strip():
            self.analytics.track_event(EventType.SEARCH_PERFORMED, metadata={'search_term': search_term})
    
    def is_advanced_search_query(self, query: str) -> bool:
        """Check if the query contains advanced search syntax"""
        advanced_patterns = [
            r'title:', r'content:', r'tags:', r'folder:',  # Field searches
            r'AND', r'OR', r'NOT',  # Boolean operators
            r'regex:', r'/.*/',  # Regex patterns
            r'".*"',  # Quoted strings
            r'-\w+',  # Negation
        ]
        
        for pattern in advanced_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return True
        return False
    
    def perform_advanced_search(self, query: str):
        """Perform advanced search using the search engine"""
        try:
            # Get current folder context
            folder_id = self.search_filter.folder_id
            
            # Perform search
            results = self.advanced_search_engine.search(query, folder_id=folder_id)
            
            # Update prompt list with results
            self.prompt_list.clear()
            for result in results:
                item = QListWidgetItem(result.title)
                item.setData(Qt.ItemDataRole.UserRole, result.id)
                
                # Add enhanced tooltip with search context
                tooltip_parts = []
                if result.tags:
                    tooltip_parts.append(f"Tags: {result.tags}")
                if hasattr(result, 'score') and result.score is not None:
                    tooltip_parts.append(f"Relevance: {result.score:.2f}")
                if result.highlights:
                    tooltip_parts.append(f"Matches: {', '.join(result.highlights)}")
                
                if tooltip_parts:
                    item.setToolTip('\n'.join(tooltip_parts))
                
                self.prompt_list.addItem(item)
                
        except Exception as e:
            # Fallback to regular search on error
            print(f"Advanced search failed: {e}")
            self.refresh_prompts()
    
    def on_filter_changed(self):
        """Handle filter change"""
        self.search_filter.is_favorite = self.favorites_cb.isChecked() if self.favorites_cb.isChecked() else None
        self.search_filter.is_template = self.templates_cb.isChecked() if self.templates_cb.isChecked() else None
        self.refresh_prompts()
    
    def on_content_changed(self):
        """Handle content change in editor"""
        self.unsaved_changes = True
        self.save_btn.setEnabled(True)
        self.setWindowTitle("Prompt Organizer *")
        
        # Track favorite/unfavorite events
        if self.current_prompt and hasattr(self, '_last_favorite_state'):
            current_favorite = self.favorite_cb.isChecked()
            if current_favorite != self._last_favorite_state:
                event_type = EventType.PROMPT_FAVORITED if current_favorite else EventType.PROMPT_UNFAVORITED
                self.analytics.track_event(event_type, self.current_prompt['id'])
                self._last_favorite_state = current_favorite
    
    # Data operations
    def refresh_folders(self):
        """Refresh folder tree"""
        self.folder_tree.clear()
        folders = self.db.get_all_folders()
        
        # Build folder tree
        folder_items = {}
        root_items = []
        
        for folder in folders:
            item = QTreeWidgetItem([folder['name']])
            item.setData(0, Qt.ItemDataRole.UserRole, folder['id'])
            folder_items[folder['id']] = item
            
            if folder['parent_id'] is None:
                root_items.append(item)
            else:
                parent_item = folder_items.get(folder['parent_id'])
                if parent_item:
                    parent_item.addChild(item)
        
        self.folder_tree.addTopLevelItems(root_items)
        self.folder_tree.expandAll()
    
    def refresh_prompts(self):
        """Refresh prompt list"""
        self.prompt_list.clear()
        
        prompts = self.db.get_prompts(
            folder_id=self.search_filter.folder_id,
            search_term=self.search_filter.search_term,
            tag_ids=self.search_filter.tag_ids,
            is_favorite=self.search_filter.is_favorite,
            is_template=self.search_filter.is_template
        )
        
        for prompt in prompts:
            item = QListWidgetItem(prompt['title'])
            item.setData(Qt.ItemDataRole.UserRole, prompt['id'])
            
            # Add visual indicators
            if prompt['is_favorite']:
                item.setText(f"⭐ {prompt['title']}")
            if prompt['is_template']:
                item.setText(f"📋 {prompt['title']}")
            
            self.prompt_list.addItem(item)
        
        # Update status
        self.prompt_count_label.setText(f"{len(prompts)} prompts")
    
    def refresh_tags(self):
        """Refresh tags display"""
        # Clear existing tag widgets
        for i in reversed(range(self.tag_layout.count())):
            self.tag_layout.itemAt(i).widget().setParent(None)
        
        # Add tag widgets
        tags = self.db.get_tags()
        for tag in tags:
            tag_obj = Tag(tag['id'], tag['name'], tag['color'])
            tag_widget = TagWidget(tag_obj, removable=False)
            tag_widget.tag_clicked.connect(self.filter_by_tag)
            self.tag_layout.addWidget(tag_widget)
        
        # Update tag combo
        self.tag_combo.clear()
        for tag in tags:
            self.tag_combo.addItem(tag['name'], tag['id'])
    
    def refresh_all(self):
        """Refresh all data"""
        self.refresh_folders()
        self.refresh_prompts()
        self.refresh_tags()
        self.status_bar.showMessage("Refreshed", 2000)
    
    def load_prompt(self, prompt_id: int):
        """Load a prompt into the editor"""
        prompt = self.db.get_prompt(prompt_id)
        if not prompt:
            return
        
        self.current_prompt = prompt
        self.unsaved_changes = False
        
        # Load content
        self.title_edit.setText(prompt['title'])
        self.text_editor.setPlainText(prompt['content'])
        self.favorite_cb.setChecked(prompt['is_favorite'])
        self.template_cb.setChecked(prompt['is_template'])
        
        # Initialize favorite state tracking
        self._last_favorite_state = prompt['is_favorite']
        
        # Load metadata
        self.created_label.setText(prompt['created_at'])
        self.updated_label.setText(prompt['updated_at'])
        
        # Load folder info
        if prompt['folder_id']:
            folders = self.db.get_all_folders()
            folder = next((f for f in folders if f['id'] == prompt['folder_id']), None)
            self.folder_label.setText(folder['name'] if folder else "Unknown")
        else:
            self.folder_label.setText("Root")
        
        # Load tags
        self.refresh_prompt_tags()
        
        self.save_btn.setEnabled(False)
        self.setWindowTitle("Prompt Organizer")
    
    def refresh_prompt_tags(self):
        """Refresh tags for current prompt"""
        if not self.current_prompt:
            return
        
        # Clear existing tag widgets
        for i in reversed(range(self.prompt_tags_layout.count())):
            self.prompt_tags_layout.itemAt(i).widget().setParent(None)
        
        # Add tag widgets
        tags = self.db.get_prompt_tags(self.current_prompt['id'])
        for tag in tags:
            tag_obj = Tag(tag['id'], tag['name'], tag['color'])
            tag_widget = TagWidget(tag_obj, removable=True)
            tag_widget.tag_removed.connect(self.remove_tag_from_prompt)
            self.prompt_tags_layout.addWidget(tag_widget)
    
    # Action methods
    def new_prompt(self):
        """Create a new prompt"""
        if self.unsaved_changes:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "You have unsaved changes. Do you want to save them?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.save_prompt()
            elif reply == QMessageBox.StandardButton.Cancel:
                return
        
        # Clear editor
        self.current_prompt = None
        self.title_edit.clear()
        self.text_editor.clear()
        self.favorite_cb.setChecked(False)
        self.template_cb.setChecked(False)
        
        # Clear metadata
        self.created_label.setText("-")
        self.updated_label.setText("-")
        self.folder_label.setText("-")
        
        # Clear tags
        for i in reversed(range(self.prompt_tags_layout.count())):
            self.prompt_tags_layout.itemAt(i).widget().setParent(None)
        
        self.unsaved_changes = False
        self.save_btn.setEnabled(False)
        self.setWindowTitle("Prompt Organizer")
        self.title_edit.setFocus()
    
    def save_prompt(self):
        """Save the current prompt"""
        title = self.title_edit.text().strip()
        content = self.text_editor.toPlainText()
        
        if not title:
            QMessageBox.warning(self, "Warning", "Please enter a title for the prompt.")
            return
        
        try:
            if self.current_prompt:
                # Update existing prompt
                self.db.update_prompt(
                    self.current_prompt['id'],
                    title=title,
                    content=content,
                    folder_id=self.search_filter.folder_id,
                    is_favorite=self.favorite_cb.isChecked(),
                    is_template=self.template_cb.isChecked()
                )
                self.current_prompt['title'] = title
                self.current_prompt['content'] = content
                
                # Track prompt edit
                self.analytics.track_event(EventType.PROMPT_EDITED, self.current_prompt['id'])
            else:
                # Create new prompt
                prompt_id = self.db.create_prompt(
                    title=title,
                    content=content,
                    folder_id=self.search_filter.folder_id,
                    is_favorite=self.favorite_cb.isChecked(),
                    is_template=self.template_cb.isChecked()
                )
                self.current_prompt = self.db.get_prompt(prompt_id)
                
                # Track prompt creation
                self.analytics.track_event(EventType.PROMPT_CREATED, prompt_id)
            
            self.unsaved_changes = False
            self.save_btn.setEnabled(False)
            self.setWindowTitle("Prompt Organizer")
            self.refresh_prompts()
            self.status_bar.showMessage("Prompt saved", 2000)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save prompt: {str(e)}")
    
    def duplicate_prompt(self):
        """Duplicate the selected prompt"""
        current_item = self.prompt_list.currentItem()
        if not current_item:
            QMessageBox.information(self, "Info", "Please select a prompt to duplicate.")
            return
        
        prompt_id = current_item.data(Qt.ItemDataRole.UserRole)
        prompt = self.db.get_prompt(prompt_id)
        
        if prompt:
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
            
            self.refresh_prompts()
            self.status_bar.showMessage("Prompt duplicated", 2000)
    
    def delete_prompt(self):
        """Delete the selected prompt"""
        current_item = self.prompt_list.currentItem()
        if not current_item:
            QMessageBox.information(self, "Info", "Please select a prompt to delete.")
            return
        
        reply = QMessageBox.question(
            self, "Confirm Delete",
            "Are you sure you want to delete this prompt?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            prompt_id = current_item.data(Qt.ItemDataRole.UserRole)
            if self.db.delete_prompt(prompt_id):
                # Track prompt deletion
                self.analytics.track_event(EventType.PROMPT_DELETED, prompt_id)
                
                if self.current_prompt and self.current_prompt['id'] == prompt_id:
                    self.new_prompt()  # Clear editor
                self.refresh_prompts()
                self.status_bar.showMessage("Prompt deleted", 2000)
    
    def copy_to_clipboard(self):
        """Copy current prompt content to clipboard"""
        if self.current_prompt:
            content = self.current_prompt['content']
        else:
            content = self.text_editor.toPlainText()
        
        if content:
            clipboard = QApplication.clipboard()
            clipboard.setText(content)
            self.status_bar.showMessage("Copied to clipboard", 2000)
            
            # Track copy event
            prompt_id = self.current_prompt['id'] if self.current_prompt else None
            self.analytics.track_event(EventType.PROMPT_COPIED, prompt_id)
    
    def copy_modified_to_clipboard(self):
        """Copy modified content to clipboard without saving"""
        content = self.text_editor.toPlainText()
        if content:
            clipboard = QApplication.clipboard()
            clipboard.setText(content)
            self.status_bar.showMessage("Modified content copied to clipboard", 2000)
    
    def auto_save(self):
        """Auto-save current prompt if there are changes"""
        if self.unsaved_changes and self.current_prompt and self.title_edit.text().strip():
            self.save_prompt()
    
    # Folder operations
    def add_folder(self):
        """Add a new folder"""
        name, ok = QInputDialog.getText(self, "New Folder", "Folder name:")
        if ok and name.strip():
            current_item = self.folder_tree.currentItem()
            parent_id = current_item.data(0, Qt.ItemDataRole.UserRole) if current_item else None
            
            folder_id = self.db.create_folder(name.strip(), parent_id)
            self.refresh_folders()
            self.status_bar.showMessage("Folder created", 2000)
    
    def rename_folder(self):
        """Rename selected folder"""
        current_item = self.folder_tree.currentItem()
        if not current_item:
            QMessageBox.information(self, "Info", "Please select a folder to rename.")
            return
        
        current_name = current_item.text(0)
        name, ok = QInputDialog.getText(self, "Rename Folder", "New name:", text=current_name)
        if ok and name.strip() and name.strip() != current_name:
            folder_id = current_item.data(0, Qt.ItemDataRole.UserRole)
            if self.db.update_folder(folder_id, name.strip()):
                self.refresh_folders()
                self.status_bar.showMessage("Folder renamed", 2000)
    
    def delete_folder(self):
        """Delete selected folder"""
        current_item = self.folder_tree.currentItem()
        if not current_item:
            QMessageBox.information(self, "Info", "Please select a folder to delete.")
            return
        
        folder_name = current_item.text(0)
        if folder_name == "Root":
            QMessageBox.warning(self, "Warning", "Cannot delete the root folder.")
            return
        
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete the folder '{folder_name}'?\nIts contents will be moved to the parent folder.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            folder_id = current_item.data(0, Qt.ItemDataRole.UserRole)
            if self.db.delete_folder(folder_id):
                self.refresh_folders()
                self.refresh_prompts()
                self.status_bar.showMessage("Folder deleted", 2000)
    
    # Tag operations
    def add_tag(self):
        """Add a new tag"""
        dialog = TagDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            tag_data = dialog.get_tag_data()
            if tag_data['name']:
                tag_id = self.db.create_tag(tag_data['name'], tag_data['color'])
                self.refresh_tags()
                self.status_bar.showMessage("Tag created", 2000)
    
    def manage_tags(self):
        """Open tag management dialog"""
        # This would open a more comprehensive tag management dialog
        # For now, just refresh tags
        self.refresh_tags()
    
    def add_tag_to_prompt(self):
        """Add selected tag to current prompt"""
        if not self.current_prompt:
            QMessageBox.information(self, "Info", "Please select a prompt first.")
            return
        
        tag_text = self.tag_combo.currentText().strip()
        if not tag_text:
            return
        
        # Check if tag exists or create new one
        tags = self.db.get_tags()
        tag = next((t for t in tags if t['name'].lower() == tag_text.lower()), None)
        
        if not tag:
            # Create new tag
            tag_id = self.db.create_tag(tag_text)
            self.refresh_tags()
        else:
            tag_id = tag['id']
        
        # Add tag to prompt
        if self.db.add_tag_to_prompt(self.current_prompt['id'], tag_id):
            self.refresh_prompt_tags()
            self.status_bar.showMessage("Tag added", 2000)
        else:
            QMessageBox.information(self, "Info", "Tag is already added to this prompt.")
    
    def remove_tag_from_prompt(self, tag_id: int):
        """Remove tag from current prompt"""
        if self.current_prompt and self.db.remove_tag_from_prompt(self.current_prompt['id'], tag_id):
            self.refresh_prompt_tags()
            self.status_bar.showMessage("Tag removed", 2000)
    
    def filter_by_tag(self, tag_id: int):
        """Filter prompts by tag"""
        if tag_id in self.search_filter.tag_ids:
            self.search_filter.tag_ids.remove(tag_id)
        else:
            self.search_filter.tag_ids.append(tag_id)
        self.refresh_prompts()
    
    def clear_filters(self):
        """Clear all filters"""
        self.search_filter = SearchFilter()
        self.search_edit.clear()
        self.favorites_cb.setChecked(False)
        self.templates_cb.setChecked(False)
        self.refresh_prompts()
    
    # Import/Export
    def import_data(self):
        """Import data from file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Data", "", "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if self.db.import_data(data):
                    # Track import event
                    self.analytics.track_event(EventType.IMPORT_PERFORMED, metadata={'file_path': file_path})
                    
                    self.refresh_all()
                    QMessageBox.information(self, "Success", "Data imported successfully.")
                else:
                    QMessageBox.critical(self, "Error", "Failed to import data.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to import data: {str(e)}")
    
    def export_data(self):
        """Export data to file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Data", "prompts_export.json", "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                data = self.db.export_data()
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                # Track export event
                self.analytics.track_event(EventType.EXPORT_PERFORMED, metadata={'file_path': file_path})
                
                QMessageBox.information(self, "Success", "Data exported successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export data: {str(e)}")
    
    # Context menus
    def show_folder_context_menu(self, position):
        """Show context menu for folder tree"""
        item = self.folder_tree.itemAt(position)
        if item:
            menu = self.folder_tree.createStandardContextMenu()
            menu.addSeparator()
            
            rename_action = menu.addAction("Rename")
            rename_action.triggered.connect(self.rename_folder)
            
            delete_action = menu.addAction("Delete")
            delete_action.triggered.connect(self.delete_folder)
            
            menu.exec(self.folder_tree.mapToGlobal(position))
    
    def show_prompt_context_menu(self, position):
        """Show context menu for prompt list"""
        item = self.prompt_list.itemAt(position)
        selected_items = self.prompt_list.selectedItems()
        
        if item:
            menu = self.prompt_list.createStandardContextMenu()
            menu.addSeparator()
            
            if len(selected_items) == 1:
                # Single item context menu
                duplicate_action = menu.addAction("Duplicate")
                duplicate_action.triggered.connect(self.duplicate_prompt)
                
                delete_action = menu.addAction("Delete")
                delete_action.triggered.connect(self.delete_prompt)
            
            elif len(selected_items) > 1:
                # Multi-selection context menu
                menu.addAction(f"{len(selected_items)} prompts selected").setEnabled(False)
                menu.addSeparator()
                
                batch_operations_action = menu.addAction("Batch Operations...")
                batch_operations_action.triggered.connect(self.show_batch_operations)
                
                menu.addSeparator()
                
                batch_copy_action = menu.addAction("Copy All Selected")
                batch_copy_action.triggered.connect(self.quick_batch_copy)
                
                batch_delete_action = menu.addAction("Delete All Selected")
                batch_delete_action.triggered.connect(self.quick_batch_delete)
                
                menu.addSeparator()
                
                clear_selection_action = menu.addAction("Clear Selection")
                clear_selection_action.triggered.connect(self.clear_prompt_selection)
            
            menu.exec(self.prompt_list.mapToGlobal(position))
    
    # Utility methods
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self, "About Prompt Organizer",
            "Prompt Organizer v1.0\n\n"
            "A desktop application for organizing and managing prompts.\n\n"
            "Features:\n"
            "• Hierarchical folder organization\n"
            "• Tag-based categorization\n"
            "• Search and filtering\n"
            "• Syntax highlighting\n"
            "• Version history\n"
            "• Import/Export functionality\n"
            "• Copy without saving\n"
            "• Template system"
        )
    
    def closeEvent(self, event):
        """Handle application close"""
        if self.unsaved_changes:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "You have unsaved changes. Do you want to save them before closing?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.save_prompt()
                event.accept()
            elif reply == QMessageBox.StandardButton.No:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
        
        # Save window state
        if event.isAccepted():
            self.save_window_state()
    
    # Theme and Settings Methods
    def apply_current_theme(self):
        """Apply the current theme to the application"""
        app = QApplication.instance()
        if app:
            self.theme_manager.apply_theme_to_app(app)
    
    def on_theme_changed(self, theme_name: str):
        """Handle theme change"""
        self.apply_current_theme()
        
        # Update syntax highlighter with new theme colors
        if hasattr(self, 'highlighter'):
            theme = self.theme_manager.get_current_theme()
            self.highlighter.setup_highlighting_rules()
    
    def show_settings(self):
        """Show settings dialog"""
        dialog = SettingsDialog(self)
        dialog.settings_changed.connect(self.on_settings_changed)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.on_settings_changed()
    
    def on_settings_changed(self):
        """Handle settings changes"""
        config = self.settings.get_config()
        
        # Update auto-save timer
        if config.auto_save:
            self.auto_save_timer.start(config.auto_save_interval * 1000)
        else:
            self.auto_save_timer.stop()
        
        # Apply theme changes
        self.apply_current_theme()
        
        # Update editor settings
        ui_config = config.ui
        if ui_config.word_wrap:
            self.text_editor.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        else:
            self.text_editor.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        
        # Update font
        font = QFont(ui_config.font_family, ui_config.font_size)
        self.text_editor.setFont(font)
    
    def load_window_state(self):
        """Load window geometry and state"""
        geometry = self.settings.load_window_geometry()
        if geometry:
            self.restoreGeometry(geometry)
        
        splitter_state = self.settings.load_splitter_state()
        if splitter_state:
            self.main_splitter.restoreState(splitter_state)
    
    def save_window_state(self):
        """Save window geometry and state"""
        self.settings.save_window_geometry(self.saveGeometry())
        self.settings.save_splitter_state(self.main_splitter.saveState())
    
    # LLM Feature Methods
    def show_llm_features(self):
        """Show LLM features dialog"""
        current_content = self.text_editor.toPlainText()
        dialog = LLMFeaturesDialog(current_content, self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # If user made changes, ask if they want to apply them
            new_content = dialog.get_current_prompt()
            if new_content != current_content and new_content.strip():
                reply = QMessageBox.question(
                    self, "Apply Changes",
                    "Do you want to apply the modified prompt to the editor?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self.text_editor.setPlainText(new_content)
                    self.on_content_changed()
    
    def quick_rewrite(self):
        """Quick rewrite current prompt"""
        content = self.text_editor.toPlainText().strip()
        if not content:
            QMessageBox.information(self, "Info", "Please enter a prompt to rewrite.")
            return
        
        # Track LLM rewrite event
        prompt_id = self.current_prompt['id'] if self.current_prompt else None
        self.analytics.track_event(EventType.LLM_REWRITE, prompt_id)
        
        dialog = LLMFeaturesDialog(content, self)
        dialog.rewrite_prompt()  # Automatically start rewrite
        dialog.exec()
    
    def quick_explain(self):
        """Quick explain current prompt"""
        content = self.text_editor.toPlainText().strip()
        if not content:
            QMessageBox.information(self, "Info", "Please enter a prompt to explain.")
            return
        
        # Track LLM explain event
        prompt_id = self.current_prompt['id'] if self.current_prompt else None
        self.analytics.track_event(EventType.LLM_EXPLAIN, prompt_id)
        
        dialog = LLMFeaturesDialog(content, self)
        dialog.explain_prompt()  # Automatically start explain
        dialog.exec()
    
    def quick_improve(self):
        """Quick improve current prompt"""
        content = self.text_editor.toPlainText().strip()
        if not content:
            QMessageBox.information(self, "Info", "Please enter a prompt to improve.")
            return
        
        # Track LLM improve event
        prompt_id = self.current_prompt['id'] if self.current_prompt else None
        self.analytics.track_event(EventType.LLM_IMPROVE, prompt_id)
        
        dialog = LLMFeaturesDialog(content, self)
        dialog.improve_prompt()  # Automatically start improve
        dialog.exec()
    
    def quick_auto_tag(self):
        """Quick auto-tag current prompt"""
        content = self.text_editor.toPlainText().strip()
        if not content:
            QMessageBox.information(self, "Info", "Please enter a prompt to generate tags for.")
            return
        
        if not self.current_prompt:
            QMessageBox.information(self, "Info", "Please save the prompt first before generating tags.")
            return
        
        # Track LLM generate tags event
        self.analytics.track_event(EventType.LLM_GENERATE_TAGS, self.current_prompt['id'])
        
        dialog = LLMFeaturesDialog(content, self)
        dialog.auto_tag_prompt()  # Automatically start auto-tag
        
        # If dialog completes successfully, offer to apply tags
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Get generated tags from dialog
            tags_widget = dialog.tags_result
            generated_tags = []
            for i in range(tags_widget.count()):
                tag_text = tags_widget.item(i).text().replace('#', '').strip()
                if tag_text:
                    generated_tags.append(tag_text)
            
            if generated_tags:
                reply = QMessageBox.question(
                    self, "Apply Tags",
                    f"Apply {len(generated_tags)} generated tags to this prompt?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    self.apply_generated_tags(generated_tags)
    
    def apply_generated_tags(self, tag_names: list):
        """Apply generated tags to current prompt"""
        if not self.current_prompt:
            return
        
        added_count = 0
        for tag_name in tag_names:
            # Check if tag exists, create if not
            existing_tags = self.db.get_tags()
            tag = next((t for t in existing_tags if t['name'].lower() == tag_name.lower()), None)
            
            if not tag:
                # Create new tag with random color
                import random
                colors = ["#007bff", "#28a745", "#dc3545", "#ffc107", "#17a2b8", "#6f42c1", "#e83e8c"]
                tag_id = self.db.create_tag(tag_name, random.choice(colors))
            else:
                tag_id = tag['id']
            
            # Add tag to prompt
            if self.db.add_tag_to_prompt(self.current_prompt['id'], tag_id):
                added_count += 1
        
        if added_count > 0:
            self.refresh_tags()
            self.refresh_prompt_tags()
            self.status_bar.showMessage(f"Added {added_count} tags", 2000)
    
    # Analytics Methods
    def show_analytics_dashboard(self):
        """Show analytics dashboard"""
        dashboard = AnalyticsDashboard(self.analytics, self)
        dashboard.show()
    
    # Performance Tracking Methods
    def show_performance_tracking(self):
        """Show performance tracking dialog"""
        try:
            dialog = PerformanceDialog(self.performance_service, self.db, self)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error opening performance tracking: {str(e)}")
    
    # Plugin Management Methods
    def load_plugins(self):
        """Load and initialize plugins"""
        try:
            loaded_count = self.plugin_manager.load_all_plugins()
            activated_count = self.plugin_manager.auto_activate_plugins()
            
            print(f"Loaded {loaded_count} plugins, activated {activated_count}")
            
            if loaded_count > 0:
                self.status_bar.showMessage(f"Loaded {loaded_count} plugins", 3000)
                
        except Exception as e:
            print(f"Error loading plugins: {e}")
    
    def show_plugin_manager(self):
        """Show plugin manager dialog"""
        try:
            dialog = PluginDialog(self.plugin_manager, self)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error opening plugin manager: {str(e)}")
    
    def execute_plugin_processor(self, processor_id: str, prompt_content: str):
        """Execute a prompt processor plugin"""
        try:
            result = self.plugin_manager.execute_prompt_processor(processor_id, prompt_content)
            if result:
                return result
            else:
                QMessageBox.warning(self, "Plugin Error", f"Failed to execute plugin processor: {processor_id}")
                return prompt_content
        except Exception as e:
            QMessageBox.critical(self, "Plugin Error", f"Error executing plugin: {str(e)}")
            return prompt_content
    
    # Advanced Search Methods
    def show_advanced_search(self):
        """Show advanced search dialog"""
        dialog = AdvancedSearchDialog(self.db, self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Get search results from dialog
            results = dialog.get_search_results()
            if results is not None:
                # Update prompt list with search results
                self.prompt_list.clear()
                for result in results:
                    item = QListWidgetItem(result.title)
                    item.setData(Qt.ItemDataRole.UserRole, result.id)
                    
                    # Add enhanced tooltip with search context
                    tooltip_parts = []
                    if result.tags:
                        tooltip_parts.append(f"Tags: {result.tags}")
                    if hasattr(result, 'score') and result.score is not None:
                        tooltip_parts.append(f"Relevance: {result.score:.2f}")
                    if result.highlights:
                        tooltip_parts.append(f"Matches: {', '.join(result.highlights)}")
                    
                    if tooltip_parts:
                        item.setToolTip('\n'.join(tooltip_parts))
                    
                    self.prompt_list.addItem(item)
                
                # Update status
                self.prompt_count_label.setText(f"{len(results)} search results")
                self.status_bar.showMessage(f"Advanced search completed: {len(results)} results", 3000)
                
                # Track advanced search event
                self.analytics.track_event(EventType.SEARCH_PERFORMED, metadata={
                    'search_type': 'advanced',
                    'results_count': len(results)
                })
    
    # Sharing Methods
    def share_current_prompt(self):
        """Share the currently selected prompt"""
        if not self.current_prompt:
            QMessageBox.information(self, "Info", "Please select a prompt to share.")
            return
        
        try:
            dialog = SharingDialog(
                self.current_prompt['id'],
                self.current_prompt['title'],
                self.sharing_service,
                self
            )
            dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error opening sharing dialog: {str(e)}")
    
    def view_shared_prompt(self):
        """View a shared prompt using a share token"""
        from PyQt6.QtWidgets import QInputDialog
        
        token, ok = QInputDialog.getText(
            self, "View Shared Prompt",
            "Enter the share token or link:",
            QLineEdit.EchoMode.Normal
        )
        
        if ok and token.strip():
            # Extract token from URL if full link was provided
            if "shared/" in token:
                token = token.split("shared/")[-1]
            
            try:
                dialog = ShareLinkViewerDialog(token.strip(), self.sharing_service, self)
                dialog.exec()
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error viewing shared prompt: {str(e)}")
    
    def show_my_shared_prompts(self):
        """Show all prompts shared by the current user"""
        try:
            # This would show a dialog listing all shared prompts
            # For now, just show a simple message
            shared_prompts = self.sharing_service.get_shared_prompts_by_user("current_user")
            
            if not shared_prompts:
                QMessageBox.information(self, "My Shared Prompts", "You haven't shared any prompts yet.")
                return
            
            # Create a simple list dialog
            from PyQt6.QtWidgets import QListWidget, QVBoxLayout, QDialog, QPushButton
            
            dialog = QDialog(self)
            dialog.setWindowTitle("My Shared Prompts")
            dialog.resize(500, 400)
            
            layout = QVBoxLayout()
            dialog.setLayout(layout)
            
            list_widget = QListWidget()
            for shared_prompt in shared_prompts:
                # Get prompt title
                prompt = self.db.get_prompt(shared_prompt.prompt_id)
                if prompt:
                    item_text = f"{prompt['title']} - {shared_prompt.permission.value} - {shared_prompt.access_count} uses"
                    list_widget.addItem(item_text)
            
            layout.addWidget(list_widget)
            
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(dialog.accept)
            layout.addWidget(close_btn)
            
            dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading shared prompts: {str(e)}")
    
    # Batch Operations Methods
    def on_prompt_selection_changed(self):
        """Handle prompt selection change for batch operations"""
        selected_items = self.prompt_list.selectedItems()
        selected_count = len(selected_items)
        
        if selected_count > 1:
            # Show batch operations UI
            self.batch_operations_frame.setVisible(True)
            self.batch_info_label.setText(f"{selected_count} prompts selected")
            
            # Update status bar
            self.status_bar.showMessage(f"{selected_count} prompts selected for batch operations")
        else:
            # Hide batch operations UI
            self.batch_operations_frame.setVisible(False)
            
            # Update status bar with normal prompt count
            prompts = self.db.get_prompts(
                folder_id=self.search_filter.folder_id,
                search_term=self.search_filter.search_term,
                tag_ids=self.search_filter.tag_ids,
                is_favorite=self.search_filter.is_favorite,
                is_template=self.search_filter.is_template
            )
            self.prompt_count_label.setText(f"{len(prompts)} prompts")
    
    def get_selected_prompts(self) -> List[Dict]:
        """Get data for all selected prompts"""
        selected_items = self.prompt_list.selectedItems()
        selected_prompts = []
        
        for item in selected_items:
            prompt_id = item.data(Qt.ItemDataRole.UserRole)
            prompt = self.db.get_prompt(prompt_id)
            if prompt:
                selected_prompts.append(prompt)
        
        return selected_prompts
    
    def clear_prompt_selection(self):
        """Clear all prompt selections"""
        self.prompt_list.clearSelection()
    
    def show_batch_operations(self):
        """Show the batch operations dialog"""
        selected_prompts = self.get_selected_prompts()
        
        if not selected_prompts:
            QMessageBox.information(self, "Info", "Please select prompts for batch operations.")
            return
        
        try:
            dialog = BatchOperationsDialog(selected_prompts, self.db, self.analytics, self)
            dialog.exec()
            
            # Refresh the prompt list after batch operations
            self.refresh_prompts()
            self.refresh_tags()  # Tags might have been modified
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error opening batch operations: {str(e)}")
    
    def quick_batch_delete(self):
        """Quick batch delete selected prompts"""
        selected_prompts = self.get_selected_prompts()
        
        if not selected_prompts:
            QMessageBox.information(self, "Info", "Please select prompts to delete.")
            return
        
        reply = QMessageBox.question(
            self, "Confirm Batch Delete",
            f"Are you sure you want to delete {len(selected_prompts)} selected prompts?\n\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success_count = 0
            for prompt in selected_prompts:
                if self.db.delete_prompt(prompt['id']):
                    success_count += 1
                    # Track deletion
                    self.analytics.track_event(EventType.PROMPT_DELETED, prompt['id'])
            
            # Clear current prompt if it was deleted
            if self.current_prompt and self.current_prompt['id'] in [p['id'] for p in selected_prompts]:
                self.new_prompt()
            
            self.refresh_prompts()
            self.status_bar.showMessage(f"Deleted {success_count}/{len(selected_prompts)} prompts", 3000)
            
            # Track batch delete event
            self.analytics.track_event(EventType.PROMPT_DELETED, metadata={
                'batch_operation': True,
                'count': success_count
            })
    
    def quick_batch_copy(self):
        """Quick copy all selected prompt content to clipboard"""
        selected_prompts = self.get_selected_prompts()
        
        if not selected_prompts:
            QMessageBox.information(self, "Info", "Please select prompts to copy.")
            return
        
        content_parts = []
        for prompt in selected_prompts:
            content_parts.append(f"=== {prompt['title']} ===\n{prompt['content']}\n")
        
        combined_content = '\n'.join(content_parts)
        
        clipboard = QApplication.clipboard()
        clipboard.setText(combined_content)
        
        self.status_bar.showMessage(f"Copied {len(selected_prompts)} prompts to clipboard", 3000)
        
        # Track batch copy event
        self.analytics.track_event(EventType.PROMPT_COPIED, metadata={
            'batch_operation': True,
            'count': len(selected_prompts)
        })
    
    def select_all_prompts(self):
        """Select all prompts in the current view"""
        self.prompt_list.selectAll()
    
    def invert_prompt_selection(self):
        """Invert the current prompt selection"""
        for i in range(self.prompt_list.count()):
            item = self.prompt_list.item(i)
            item.setSelected(not item.isSelected())
    
    # Template Methods
    def show_template_manager(self):
        """Show template manager dialog"""
        try:
            dialog = TemplateManagerDialog(self.template_service, self)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error opening template manager: {str(e)}")
    
    def new_template(self):
        """Create a new template"""
        try:
            dialog = TemplateEditorDialog(template_service=self.template_service, parent=self)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error creating template: {str(e)}")
    
    def show_template_usage(self):
        """Show template usage dialog"""
        try:
            # Get available templates
            templates = self.template_service.get_templates()
            if not templates:
                QMessageBox.information(self, "Info", "No templates available. Create a template first.")
                return
            
            # Show template selection dialog
            template_names = [f"{t.title} ({t.category})" for t in templates]
            template_name, ok = QInputDialog.getItem(
                self, "Select Template", "Choose a template to use:",
                template_names, 0, False
            )
            
            if ok and template_name:
                # Find selected template
                selected_index = template_names.index(template_name)
                selected_template = templates[selected_index]
                
                # Show usage dialog
                dialog = TemplateUsageDialog(
                    template=selected_template,
                    template_service=self.template_service,
                    parent=self
                )
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    # Refresh prompts if a new prompt was created
                    self.refresh_prompts()
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error using template: {str(e)}")
    
    def create_template_from_prompt(self):
        """Create a template from the current prompt"""
        if not self.current_prompt:
            QMessageBox.information(self, "Info", "Please select or create a prompt first.")
            return
        
        try:
            # Get template details from user
            title, ok = QInputDialog.getText(
                self, "Create Template",
                "Template title:",
                text=f"{self.current_prompt['title']} Template"
            )
            
            if not ok or not title.strip():
                return
            
            description, ok = QInputDialog.getText(
                self, "Create Template",
                "Template description (optional):"
            )
            
            if not ok:
                return
            
            # Create template
            template_id = self.template_service.create_template_from_prompt(
                prompt_id=self.current_prompt['id'],
                template_title=title.strip(),
                template_description=description.strip()
            )
            
            QMessageBox.information(self, "Success", f"Template '{title}' created successfully!")
            
            # Ask if user wants to edit the template
            reply = QMessageBox.question(
                self, "Edit Template",
                "Would you like to edit the template variables and settings?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                template = self.template_service.get_template(template_id)
                if template:
                    dialog = TemplateEditorDialog(
                        template=template,
                        template_service=self.template_service,
                        parent=self
                    )
                    dialog.exec()
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create template: {str(e)}")
    
    def use_template_for_current_prompt(self, template_id: int):
        """Use a template to replace current prompt content"""
        try:
            template = self.template_service.get_template(template_id)
            if not template:
                QMessageBox.critical(self, "Error", "Template not found.")
                return
            
            dialog = TemplateUsageDialog(
                template=template,
                template_service=self.template_service,
                parent=self
            )
            
            # Modify dialog to not create a new prompt but replace current content
            dialog.create_prompt_cb.setChecked(False)
            dialog.create_prompt_cb.setVisible(False)
            dialog.prompt_title_edit.setVisible(False)
            
            if dialog.exec() == QDialog.DialogCode.Accepted:
                # Get the generated content and set it in the editor
                substitutions = dialog.get_substitutions()
                content = template.substitute_variables(substitutions)
                
                self.text_editor.setPlainText(content)
                self.on_content_changed()
                
                QMessageBox.information(self, "Success", "Template content applied to current prompt!")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to use template: {str(e)}")
    
    # AI Suggestion Methods
    def show_ai_suggestions(self):
        """Show AI suggestions dialog for current prompt"""
        if not self.current_prompt:
            # Check if there's content in the editor
            content = self.text_editor.toPlainText().strip()
            if not content:
                QMessageBox.information(self, "Info", "Please select a prompt or enter content to analyze.")
                return
            
            # Create a temporary prompt for analysis
            title = self.title_edit.text().strip() or "Untitled Prompt"
            reply = QMessageBox.question(
                self, "Analyze Content",
                "Would you like to save this prompt first before analyzing it?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.save_prompt()
                if not self.current_prompt:
                    return
            elif reply == QMessageBox.StandardButton.Cancel:
                return
            else:
                # Analyze without saving - use temporary ID
                prompt_id = None
        else:
            content = self.current_prompt['content']
            prompt_id = self.current_prompt['id']
        
        try:
            dialog = AISuggestionDialog(
                ai_service=self.ai_suggestion_service,
                prompt_id=prompt_id,
                prompt_content=content,
                parent=self
            )
            dialog.exec()
            
            # Track AI suggestion usage
            if prompt_id:
                self.analytics.track_event(EventType.LLM_IMPROVE, prompt_id)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error opening AI suggestions: {str(e)}")
    
    def show_ai_suggestion_stats(self):
        """Show AI suggestion statistics"""
        try:
            dialog = AISuggestionStatsDialog(self.ai_suggestion_service, self)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error opening suggestion statistics: {str(e)}")
    
    def show_ai_prompt_generator(self):
        """Show AI Prompt Generator dialog"""
        try:
            dialog = AIPromptGeneratorDialog(self.ai_suggestion_service, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                # Get the generated prompt content
                generated_content = dialog.get_generated_prompt()
                if generated_content:
                    # Ask user if they want to replace current content or create new prompt
                    if self.text_editor.toPlainText().strip():
                        reply = QMessageBox.question(
                            self, "Replace Content",
                            "Do you want to replace the current content with the generated prompt?",
                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
                        )
                        if reply == QMessageBox.StandardButton.Yes:
                            self.text_editor.setPlainText(generated_content)
                            self.on_content_changed()
                        elif reply == QMessageBox.StandardButton.No:
                            # Create new prompt
                            self.new_prompt()
                            self.text_editor.setPlainText(generated_content)
                            self.on_content_changed()
                    else:
                        # No current content, just set the generated content
                        self.text_editor.setPlainText(generated_content)
                        self.on_content_changed()
                    
                    self.status_bar.showMessage("AI-generated prompt applied", 3000)
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error opening AI Prompt Generator: {str(e)}")
    
    # Export Methods
    def show_export_dialog(self):
        """Show export dialog for all prompts"""
        try:
            dialog = ExportDialog(self.export_service, parent=self)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error opening export dialog: {str(e)}")
    
    # Community Methods
    def show_community_browser(self):
        """Show community browser dialog"""
        try:
            dialog = CommunityBrowserDialog(self.community_service, self)
            dialog.exec()
            
            # Refresh prompts in case user downloaded any
            self.refresh_prompts()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error opening community browser: {str(e)}")
    
    def share_prompt_to_community(self):
        """Share current prompt to community"""
        if not self.current_prompt:
            QMessageBox.information(self, "Info", "Please select a prompt to share.")
            return
        
        try:
            dialog = SharePromptDialog(
                local_prompt_id=self.current_prompt['id'],
                community_service=self.community_service,
                parent=self
            )
            dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error sharing prompt: {str(e)}")
    
    def show_my_community_prompts(self):
        """Show prompts shared by current user"""
        try:
            if not self.community_service.current_user_id:
                QMessageBox.information(
                    self, "Info",
                    "Please set up your community profile first.\nUse the Community Browser to get started."
                )
                return
            
            user_prompts = self.community_service.get_user_prompts(self.community_service.current_user_id)
            
            if not user_prompts:
                QMessageBox.information(self, "My Shared Prompts", "You haven't shared any prompts yet.")
                return
            
            # Create a simple list dialog
            from PyQt6.QtWidgets import QListWidget, QVBoxLayout, QDialog, QPushButton, QLabel
            
            dialog = QDialog(self)
            dialog.setWindowTitle("My Shared Prompts")
            dialog.resize(600, 400)
            
            layout = QVBoxLayout()
            dialog.setLayout(layout)
            
            # Header
            header_label = QLabel(f"You have shared {len(user_prompts)} prompts to the community:")
            header_label.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
            layout.addWidget(header_label)
            
            # List widget
            list_widget = QListWidget()
            for prompt in user_prompts:
                item_text = f"{prompt.title} - {prompt.category.value} - ⭐{prompt.rating_average:.1f} ({prompt.rating_count} reviews) - 📥{prompt.download_count} downloads"
                list_widget.addItem(item_text)
            
            layout.addWidget(list_widget)
            
            # Close button
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(dialog.accept)
            layout.addWidget(close_btn)
            
            dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading shared prompts: {str(e)}")
    
    def show_community_stats(self):
        """Show community statistics"""
        try:
            stats = self.community_service.get_community_stats()
            
            # Create stats dialog
            from PyQt6.QtWidgets import QVBoxLayout, QDialog, QPushButton, QLabel, QGridLayout
            
            dialog = QDialog(self)
            dialog.setWindowTitle("Community Statistics")
            dialog.resize(500, 400)
            
            layout = QVBoxLayout()
            dialog.setLayout(layout)
            
            # Title
            title_label = QLabel("Community Library Statistics")
            title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 15px;")
            layout.addWidget(title_label)
            
            # Stats grid
            stats_layout = QGridLayout()
            
            # Overall stats
            stats_layout.addWidget(QLabel("Total Prompts:"), 0, 0)
            stats_layout.addWidget(QLabel(str(stats['total_prompts'])), 0, 1)
            
            stats_layout.addWidget(QLabel("Total Users:"), 1, 0)
            stats_layout.addWidget(QLabel(str(stats['total_users'])), 1, 1)
            
            stats_layout.addWidget(QLabel("Total Downloads:"), 2, 0)
            stats_layout.addWidget(QLabel(str(stats['total_downloads'])), 2, 1)
            
            stats_layout.addWidget(QLabel("Total Reviews:"), 3, 0)
            stats_layout.addWidget(QLabel(str(stats['total_reviews'])), 3, 1)
            
            stats_layout.addWidget(QLabel("Average Rating:"), 4, 0)
            stats_layout.addWidget(QLabel(f"{stats['average_rating']:.1f} ⭐"), 4, 1)
            
            layout.addLayout(stats_layout)
            
            # Category breakdown
            if stats['by_category']:
                layout.addWidget(QLabel("\nPrompts by Category:"))
                category_layout = QGridLayout()
                row = 0
                for category, count in stats['by_category'].items():
                    category_layout.addWidget(QLabel(f"{category}:"), row, 0)
                    category_layout.addWidget(QLabel(str(count)), row, 1)
                    row += 1
                layout.addLayout(category_layout)
            
            # Top authors
            if stats['top_authors']:
                layout.addWidget(QLabel("\nTop Contributors:"))
                authors_layout = QGridLayout()
                row = 0
                for author in stats['top_authors'][:5]:  # Show top 5
                    authors_layout.addWidget(QLabel(f"{author['display_name']}:"), row, 0)
                    authors_layout.addWidget(QLabel(f"{author['prompts_shared']} prompts"), row, 1)
                    row += 1
                layout.addLayout(authors_layout)
            
            # Close button
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(dialog.accept)
            layout.addWidget(close_btn)
            
            dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading community statistics: {str(e)}")
    
    def export_selected_prompts(self):
        """Export currently selected prompts"""
        selected_prompts = self.get_selected_prompts()
        
        if not selected_prompts:
            QMessageBox.information(self, "Info", "Please select prompts to export.")
            return
        
        try:
            dialog = ExportDialog(self.export_service, selected_prompts, parent=self)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error opening export dialog: {str(e)}")
    
    # Update Methods
    def show_update_dialog(self):
        """Show the update dialog"""
        try:
            dialog = UpdateDialog(
                repo_owner=self.update_manager.update_service.repo_owner,
                repo_name=self.update_manager.update_service.repo_name,
                current_version=self.update_manager.update_service.current_version,
                parent=self
            )
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error opening update dialog: {str(e)}")
    
    def check_for_updates_on_startup(self):
        """Check for updates automatically on startup (if enabled)"""
        try:
            # This could be called during application startup
            # You might want to add a setting to enable/disable this
            update_info = self.update_manager.check_and_notify_updates(include_prereleases=False)
            
            if update_info:
                reply = QMessageBox.question(
                    self, "Update Available",
                    f"A new version ({update_info.version_tag}) is available!\n\n"
                    f"Would you like to check it out?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    self.show_update_dialog()
        
        except Exception as e:
            # Silently fail on startup - don't bother user with update check errors
            print(f"Startup update check failed: {e}")
    
    def export_current_prompt(self):
        """Export the currently loaded prompt"""
        if not self.current_prompt:
            QMessageBox.information(self, "Info", "Please select a prompt to export.")
            return
        
        try:
            dialog = ExportDialog(self.export_service, [self.current_prompt], parent=self)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error opening export dialog: {str(e)}")