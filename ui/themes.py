"""
Theme management system for the Prompt Organizer application
"""

from typing import Dict, Any
from dataclasses import dataclass
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtWidgets import QApplication


@dataclass
class ThemeColors:
    """Color scheme for a theme"""
    # Main colors
    primary: str = "#007bff"
    secondary: str = "#6c757d"
    success: str = "#28a745"
    warning: str = "#ffc107"
    danger: str = "#dc3545"
    info: str = "#17a2b8"
    
    # Background colors
    background: str = "#ffffff"
    surface: str = "#f8f9fa"
    card: str = "#ffffff"
    
    # Text colors
    text_primary: str = "#212529"
    text_secondary: str = "#6c757d"
    text_muted: str = "#adb5bd"
    text_disabled: str = "#dee2e6"
    
    # Border colors
    border: str = "#dee2e6"
    border_light: str = "#e9ecef"
    border_dark: str = "#adb5bd"
    
    # Interactive colors
    hover: str = "#e9ecef"
    active: str = "#dee2e6"
    focus: str = "#80bdff"
    
    # Editor colors
    editor_background: str = "#ffffff"
    editor_text: str = "#212529"
    editor_selection: str = "#b3d4fc"
    editor_line_number: str = "#6c757d"
    editor_current_line: str = "#f8f9fa"
    
    # Syntax highlighting
    syntax_keyword: str = "#0066cc"
    syntax_string: str = "#d63384"
    syntax_comment: str = "#6c757d"
    syntax_variable: str = "#6f42c1"
    syntax_function: str = "#e83e8c"


@dataclass
class Theme:
    """Complete theme definition"""
    name: str
    display_name: str
    colors: ThemeColors
    font_family: str = "Segoe UI"
    font_size: int = 9
    is_dark: bool = False
    custom: bool = False


class ThemeManager(QObject):
    """Manages application themes"""
    
    theme_changed = pyqtSignal(str)  # Emits theme name when changed
    
    def __init__(self):
        super().__init__()
        self.themes: Dict[str, Theme] = {}
        self.current_theme_name = "light"
        self._setup_default_themes()
    
    def _setup_default_themes(self):
        """Setup default themes"""
        # Light theme
        light_colors = ThemeColors()
        self.themes["light"] = Theme(
            name="light",
            display_name="Light",
            colors=light_colors,
            is_dark=False
        )
        
        # Dark theme
        dark_colors = ThemeColors(
            primary="#0d6efd",
            secondary="#6c757d",
            success="#198754",
            warning="#ffc107",
            danger="#dc3545",
            info="#0dcaf0",
            
            background="#212529",
            surface="#343a40",
            card="#495057",
            
            text_primary="#ffffff",
            text_secondary="#adb5bd",
            text_muted="#6c757d",
            text_disabled="#495057",
            
            border="#6c757d",  # Made more visible
            border_light="#adb5bd",  # Made more visible
            border_dark="#495057",
            
            hover="#495057",
            active="#6c757d",
            focus="#80bdff",  # Made more visible
            
            editor_background="#2b2b2b",
            editor_text="#ffffff",
            editor_selection="#264f78",
            editor_line_number="#858585",
            editor_current_line="#2f2f2f",
            
            syntax_keyword="#569cd6",
            syntax_string="#ce9178",
            syntax_comment="#6a9955",
            syntax_variable="#9cdcfe",
            syntax_function="#dcdcaa"
        )
        self.themes["dark"] = Theme(
            name="dark",
            display_name="Dark",
            colors=dark_colors,
            is_dark=True
        )
        
        # High contrast theme
        high_contrast_colors = ThemeColors(
            primary="#0000ff",
            secondary="#808080",
            success="#00ff00",
            warning="#ffff00",
            danger="#ff0000",
            info="#00ffff",
            
            background="#000000",
            surface="#000000",
            card="#000000",
            
            text_primary="#ffffff",
            text_secondary="#ffffff",
            text_muted="#c0c0c0",
            text_disabled="#808080",
            
            border="#ffffff",
            border_light="#ffffff",
            border_dark="#c0c0c0",
            
            hover="#333333",
            active="#666666",
            focus="#ffff00",
            
            editor_background="#000000",
            editor_text="#ffffff",
            editor_selection="#0000ff",
            editor_line_number="#ffffff",
            editor_current_line="#333333",
            
            syntax_keyword="#00ffff",
            syntax_string="#ffff00",
            syntax_comment="#00ff00",
            syntax_variable="#ff00ff",
            syntax_function="#ffffff"
        )
        self.themes["high_contrast"] = Theme(
            name="high_contrast",
            display_name="High Contrast",
            colors=high_contrast_colors,
            is_dark=True
        )
        
        # Blue theme
        blue_colors = ThemeColors(
            primary="#0066cc",
            secondary="#4a90e2",
            success="#28a745",
            warning="#ffc107",
            danger="#dc3545",
            info="#17a2b8",
            
            background="#f0f4f8",
            surface="#e1ecf4",
            card="#ffffff",
            
            text_primary="#1a365d",
            text_secondary="#2d3748",
            text_muted="#718096",
            text_disabled="#a0aec0",
            
            border="#cbd5e0",
            border_light="#e2e8f0",
            border_dark="#a0aec0",
            
            hover="#e1ecf4",
            active="#cbd5e0",
            focus="#4299e1",
            
            editor_background="#ffffff",
            editor_text="#1a365d",
            editor_selection="#bee3f8",
            editor_line_number="#718096",
            editor_current_line="#f7fafc",
            
            syntax_keyword="#0066cc",
            syntax_string="#d53f8c",
            syntax_comment="#718096",
            syntax_variable="#805ad5",
            syntax_function="#e53e3e"
        )
        self.themes["blue"] = Theme(
            name="blue",
            display_name="Blue",
            colors=blue_colors,
            is_dark=False
        )
    
    def get_theme(self, name: str) -> Theme:
        """Get theme by name"""
        return self.themes.get(name, self.themes["light"])
    
    def get_current_theme(self) -> Theme:
        """Get current active theme"""
        return self.get_theme(self.current_theme_name)
    
    def set_theme(self, name: str):
        """Set active theme"""
        if name in self.themes:
            self.current_theme_name = name
            self.theme_changed.emit(name)
    
    def get_theme_names(self) -> list:
        """Get list of available theme names"""
        return list(self.themes.keys())
    
    def get_theme_display_names(self) -> Dict[str, str]:
        """Get mapping of theme names to display names"""
        return {name: theme.display_name for name, theme in self.themes.items()}
    
    def add_custom_theme(self, theme: Theme):
        """Add a custom theme"""
        theme.custom = True
        self.themes[theme.name] = theme
    
    def remove_custom_theme(self, name: str) -> bool:
        """Remove a custom theme"""
        if name in self.themes and self.themes[name].custom:
            del self.themes[name]
            if self.current_theme_name == name:
                self.set_theme("light")
            return True
        return False
    
    def get_stylesheet(self, theme_name: str = None) -> str:
        """Generate CSS stylesheet for theme"""
        theme = self.get_theme(theme_name or self.current_theme_name)
        colors = theme.colors
        
        return f"""
        /* Main Application Styles */
        QMainWindow {{
            background-color: {colors.background};
            color: {colors.text_primary};
            font-family: {theme.font_family};
            font-size: {theme.font_size}pt;
        }}
        
        /* Menu Bar */
        QMenuBar {{
            background-color: {colors.surface};
            color: {colors.text_primary};
            border-bottom: 1px solid {colors.border};
        }}
        
        QMenuBar::item {{
            background-color: transparent;
            padding: 4px 8px;
        }}
        
        QMenuBar::item:selected {{
            background-color: {colors.hover};
        }}
        
        QMenu {{
            background-color: {colors.card};
            color: {colors.text_primary};
            border: 1px solid {colors.border};
        }}
        
        QMenu::item {{
            padding: 4px 20px;
        }}
        
        QMenu::item:selected {{
            background-color: {colors.hover};
        }}
        
        /* Tool Bar */
        QToolBar {{
            background-color: {colors.surface};
            border: 1px solid {colors.border};
            spacing: 2px;
        }}
        
        QToolButton {{
            background-color: transparent;
            border: none;
            padding: 4px;
            margin: 1px;
        }}
        
        QToolButton:hover {{
            background-color: {colors.hover};
            border-radius: 3px;
        }}
        
        QToolButton:pressed {{
            background-color: {colors.active};
        }}
        
        /* Status Bar */
        QStatusBar {{
            background-color: {colors.surface};
            color: {colors.text_secondary};
            border-top: 1px solid {colors.border};
        }}
        
        /* Group Boxes */
        QGroupBox {{
            font-weight: bold;
            border: 1px solid {colors.border};
            border-radius: 4px;
            margin-top: 8px;
            padding-top: 4px;
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 8px;
            padding: 0 4px 0 4px;
            color: {colors.text_primary};
        }}
        
        /* Buttons */
        QPushButton {{
            background-color: {colors.primary};
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            font-weight: bold;
        }}
        
        QPushButton:hover {{
            background-color: {colors.primary}dd;
        }}
        
        QPushButton:pressed {{
            background-color: {colors.primary}bb;
        }}
        
        QPushButton:disabled {{
            background-color: {colors.text_disabled};
            color: {colors.text_muted};
        }}
        
        QPushButton[class="secondary"] {{
            background-color: {colors.secondary};
        }}
        
        QPushButton[class="success"] {{
            background-color: {colors.success};
        }}
        
        QPushButton[class="warning"] {{
            background-color: {colors.warning};
            color: {colors.text_primary};
        }}
        
        QPushButton[class="danger"] {{
            background-color: {colors.danger};
        }}
        
        /* Text Inputs */
        QLineEdit, QTextEdit, QPlainTextEdit {{
            background-color: {colors.editor_background};
            color: {colors.editor_text};
            border: 1px solid {colors.border};
            border-radius: 4px;
            padding: 4px;
            selection-background-color: {colors.editor_selection};
        }}
        
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
            border-color: {colors.focus};
            outline: none;
        }}
        
        /* Lists and Trees */
        QListWidget, QTreeWidget {{
            background-color: {colors.card};
            color: {colors.text_primary};
            border: 1px solid {colors.border};
            border-radius: 4px;
            alternate-background-color: {colors.surface};
        }}
        
        QListWidget::item, QTreeWidget::item {{
            padding: 4px;
            border-bottom: 1px solid {colors.border_light};
        }}
        
        QListWidget::item:selected, QTreeWidget::item:selected {{
            background-color: {colors.primary};
            color: white;
        }}
        
        QListWidget::item:hover, QTreeWidget::item:hover {{
            background-color: {colors.hover};
        }}
        
        /* Combo Boxes */
        QComboBox {{
            background-color: {colors.card};
            color: {colors.text_primary};
            border: 1px solid {colors.border};
            border-radius: 4px;
            padding: 4px 8px;
            min-width: 100px;
        }}
        
        QComboBox:hover {{
            border-color: {colors.focus};
        }}
        
        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}
        
        QComboBox::down-arrow {{
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 4px solid {colors.text_secondary};
        }}
        
        QComboBox QAbstractItemView {{
            background-color: {colors.card};
            color: {colors.text_primary};
            border: 1px solid {colors.border};
            selection-background-color: {colors.primary};
        }}
        
        /* Check Boxes */
        QCheckBox {{
            color: {colors.text_primary};
            spacing: 8px;
        }}
        
        QCheckBox::indicator {{
            width: 16px;
            height: 16px;
            border: 1px solid {colors.border};
            border-radius: 3px;
            background-color: {colors.card};
        }}
        
        QCheckBox::indicator:checked {{
            background-color: {colors.primary};
            border-color: {colors.primary};
        }}
        
        QCheckBox::indicator:checked::after {{
            content: "✓";
            color: white;
            font-weight: bold;
        }}
        
        /* Scroll Bars */
        QScrollBar:vertical {{
            background-color: {colors.surface};
            width: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {colors.border_dark};
            border-radius: 6px;
            min-height: 20px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {colors.text_muted};
        }}
        
        QScrollBar:horizontal {{
            background-color: {colors.surface};
            height: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:horizontal {{
            background-color: {colors.border_dark};
            border-radius: 6px;
            min-width: 20px;
        }}
        
        QScrollBar::handle:horizontal:hover {{
            background-color: {colors.text_muted};
        }}
        
        /* Splitters */
        QSplitter::handle {{
            background-color: {colors.border};
        }}
        
        QSplitter::handle:horizontal {{
            width: 2px;
        }}
        
        QSplitter::handle:vertical {{
            height: 2px;
        }}
        
        /* Tabs */
        QTabWidget::pane {{
            border: 1px solid {colors.border};
            background-color: {colors.card};
        }}
        
        QTabBar::tab {{
            background-color: {colors.surface};
            color: {colors.text_primary};
            padding: 8px 16px;
            border: 1px solid {colors.border};
            border-bottom: none;
        }}
        
        QTabBar::tab:selected {{
            background-color: {colors.card};
            border-bottom: 1px solid {colors.card};
        }}
        
        QTabBar::tab:hover {{
            background-color: {colors.hover};
        }}
        
        /* Dialog Styles */
        QDialog {{
            background-color: {colors.background};
            color: {colors.text_primary};
        }}
        
        QDialogButtonBox QPushButton {{
            min-width: 80px;
        }}
        
        /* Custom Classes */
        .tag-widget {{
            background-color: {colors.primary};
            color: white;
            border-radius: 10px;
            padding: 2px 8px;
            font-size: 11px;
        }}
        
        .status-success {{
            color: {colors.success};
        }}
        
        .status-warning {{
            color: {colors.warning};
        }}
        
        .status-error {{
            color: {colors.danger};
        }}
        
        .text-muted {{
            color: {colors.text_muted};
        }}
        
        .text-small {{
            font-size: {theme.font_size - 1}pt;
        }}
        """
    
    def apply_theme_to_app(self, app: QApplication, theme_name: str = None):
        """Apply theme to the entire application"""
        stylesheet = self.get_stylesheet(theme_name)
        app.setStyleSheet(stylesheet)
        
        # Also set the application palette for native widgets
        theme = self.get_theme(theme_name or self.current_theme_name)
        palette = QPalette()
        
        # Set palette colors
        palette.setColor(QPalette.ColorRole.Window, QColor(theme.colors.background))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(theme.colors.text_primary))
        palette.setColor(QPalette.ColorRole.Base, QColor(theme.colors.card))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(theme.colors.surface))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(theme.colors.card))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(theme.colors.text_primary))
        palette.setColor(QPalette.ColorRole.Text, QColor(theme.colors.text_primary))
        palette.setColor(QPalette.ColorRole.Button, QColor(theme.colors.surface))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(theme.colors.text_primary))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(theme.colors.text_primary))
        palette.setColor(QPalette.ColorRole.Link, QColor(theme.colors.primary))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(theme.colors.primary))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor("white"))
        
        app.setPalette(palette)


# Global theme manager instance
_theme_manager = None


def get_theme_manager() -> ThemeManager:
    """Get global theme manager instance"""
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager