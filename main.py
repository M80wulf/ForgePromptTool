#!/usr/bin/env python3
"""
Prompt Organizer - A desktop application for organizing and managing prompts
"""

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.main_window import MainWindow


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("Prompt Organizer")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("PromptOrg")
    
    # Set application icon if available
    # app.setWindowIcon(QIcon("resources/icons/app_icon.png"))
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Start the event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()