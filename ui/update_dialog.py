#!/usr/bin/env python3
"""
Update dialog for the Prompt Organizer application.
Provides UI for checking, downloading, and installing updates from GitHub.
"""

import os
import sys
from typing import Optional
from datetime import datetime

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QTextEdit, QPushButton, QProgressBar,
    QGroupBox, QFrame, QScrollArea, QWidget,
    QMessageBox, QCheckBox, QSplitter
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QFont, QColor, QPalette, QIcon, QPixmap

from services.update_service import UpdateManager, UpdateInfo


class UpdateCheckThread(QThread):
    """Thread for checking updates without blocking UI"""
    
    update_found = pyqtSignal(object)  # UpdateInfo
    no_update = pyqtSignal()
    error_occurred = pyqtSignal(str)
    
    def __init__(self, update_manager: UpdateManager, include_prereleases: bool = False):
        super().__init__()
        self.update_manager = update_manager
        self.include_prereleases = include_prereleases
    
    def run(self):
        """Check for updates in background thread"""
        try:
            update_info = self.update_manager.check_and_notify_updates(self.include_prereleases)
            if update_info:
                self.update_found.emit(update_info)
            else:
                self.no_update.emit()
        except Exception as e:
            self.error_occurred.emit(str(e))


class UpdateDownloadThread(QThread):
    """Thread for downloading updates without blocking UI"""
    
    download_progress = pyqtSignal(int)  # Progress percentage
    download_complete = pyqtSignal(bool, str)  # Success, message/path
    
    def __init__(self, update_manager: UpdateManager, update_info: UpdateInfo):
        super().__init__()
        self.update_manager = update_manager
        self.update_info = update_info
    
    def run(self):
        """Download update in background thread"""
        try:
            success, result = self.update_manager.download_and_prepare_update(self.update_info)
            self.download_complete.emit(success, result)
        except Exception as e:
            self.download_complete.emit(False, str(e))


class UpdateDialog(QDialog):
    """Dialog for managing application updates"""
    
    def __init__(self, repo_owner: str, repo_name: str, current_version: str = "1.0.0", parent=None):
        super().__init__(parent)
        self.update_manager = UpdateManager(repo_owner, repo_name, current_version)
        self.current_update_info = None
        self.prepared_update_path = None
        
        self.setWindowTitle("Check for Updates")
        self.setModal(True)
        self.resize(700, 500)
        
        self.setup_ui()
        self.load_version_info()
    
    def setup_ui(self):
        """Setup the update dialog UI"""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Application Updates")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Current version info
        self.setup_version_info_section(layout)
        
        # Update check section
        self.setup_update_check_section(layout)
        
        # Update details section
        self.setup_update_details_section(layout)
        
        # Progress section
        self.setup_progress_section(layout)
        
        # Action buttons
        self.setup_action_buttons(layout)
        
        # Status label
        self.status_label = QLabel("Ready to check for updates")
        self.status_label.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(self.status_label)
    
    def setup_version_info_section(self, layout):
        """Setup current version information section"""
        version_group = QGroupBox("Current Version")
        version_layout = QGridLayout(version_group)
        
        # Version info labels
        self.current_version_label = QLabel("Loading...")
        self.git_branch_label = QLabel("Loading...")
        self.git_commit_label = QLabel("Loading...")
        self.repo_url_label = QLabel("Loading...")
        
        version_layout.addWidget(QLabel("Version:"), 0, 0)
        version_layout.addWidget(self.current_version_label, 0, 1)
        
        version_layout.addWidget(QLabel("Git Branch:"), 1, 0)
        version_layout.addWidget(self.git_branch_label, 1, 1)
        
        version_layout.addWidget(QLabel("Git Commit:"), 2, 0)
        version_layout.addWidget(self.git_commit_label, 2, 1)
        
        version_layout.addWidget(QLabel("Repository:"), 3, 0)
        version_layout.addWidget(self.repo_url_label, 3, 1)
        
        layout.addWidget(version_group)
    
    def setup_update_check_section(self, layout):
        """Setup update checking section"""
        check_group = QGroupBox("Check for Updates")
        check_layout = QHBoxLayout(check_group)
        
        self.check_updates_btn = QPushButton("Check for Updates")
        self.check_updates_btn.clicked.connect(self.check_for_updates)
        self.check_updates_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px 16px;
                font-weight: bold;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        check_layout.addWidget(self.check_updates_btn)
        
        self.include_prereleases_cb = QCheckBox("Include pre-releases")
        check_layout.addWidget(self.include_prereleases_cb)
        
        check_layout.addStretch()
        
        self.auto_check_cb = QCheckBox("Check automatically on startup")
        check_layout.addWidget(self.auto_check_cb)
        
        layout.addWidget(check_group)
    
    def setup_update_details_section(self, layout):
        """Setup update details section"""
        self.details_group = QGroupBox("Update Details")
        details_layout = QVBoxLayout(self.details_group)
        
        # Update header
        header_layout = QHBoxLayout()
        
        self.update_version_label = QLabel("No update available")
        update_font = QFont()
        update_font.setPointSize(12)
        update_font.setBold(True)
        self.update_version_label.setFont(update_font)
        header_layout.addWidget(self.update_version_label)
        
        header_layout.addStretch()
        
        self.update_date_label = QLabel("")
        self.update_date_label.setStyleSheet("color: gray;")
        header_layout.addWidget(self.update_date_label)
        
        details_layout.addLayout(header_layout)
        
        # Release notes
        self.release_notes = QTextEdit()
        self.release_notes.setReadOnly(True)
        self.release_notes.setMaximumHeight(150)
        self.release_notes.setPlainText("No update information available")
        details_layout.addWidget(self.release_notes)
        
        # Hide initially
        self.details_group.setVisible(False)
        
        layout.addWidget(self.details_group)
    
    def setup_progress_section(self, layout):
        """Setup progress section"""
        self.progress_group = QGroupBox("Download Progress")
        progress_layout = QVBoxLayout(self.progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("Ready to download")
        progress_layout.addWidget(self.progress_label)
        
        # Hide initially
        self.progress_group.setVisible(False)
        
        layout.addWidget(self.progress_group)
    
    def setup_action_buttons(self, layout):
        """Setup action buttons"""
        buttons_layout = QHBoxLayout()
        
        self.download_btn = QPushButton("Download Update")
        self.download_btn.clicked.connect(self.download_update)
        self.download_btn.setEnabled(False)
        self.download_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 16px;
                font-weight: bold;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        buttons_layout.addWidget(self.download_btn)
        
        self.install_btn = QPushButton("Install & Restart")
        self.install_btn.clicked.connect(self.install_update)
        self.install_btn.setEnabled(False)
        self.install_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                padding: 8px 16px;
                font-weight: bold;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        buttons_layout.addWidget(self.install_btn)
        
        buttons_layout.addStretch()
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(self.close_btn)
        
        layout.addLayout(buttons_layout)
    
    def load_version_info(self):
        """Load and display current version information"""
        try:
            version_info = self.update_manager.get_version_info()
            
            self.current_version_label.setText(version_info.get("current_version", "Unknown"))
            self.git_branch_label.setText(version_info.get("branch", "Not in git repo"))
            self.git_commit_label.setText(version_info.get("commit", "Unknown"))
            self.repo_url_label.setText(version_info.get("repo_url", "Unknown"))
            
            # Make repo URL clickable if available
            if "repo_url" in version_info and version_info["repo_url"] != "Unknown":
                self.repo_url_label.setText(f'<a href="{version_info["repo_url"]}">{version_info["repo_url"]}</a>')
                self.repo_url_label.setOpenExternalLinks(True)
            
        except Exception as e:
            self.status_label.setText(f"Error loading version info: {str(e)}")
    
    def check_for_updates(self):
        """Check for available updates"""
        self.check_updates_btn.setEnabled(False)
        self.check_updates_btn.setText("Checking...")
        self.status_label.setText("Checking for updates...")
        
        # Start update check in background thread
        self.update_thread = UpdateCheckThread(
            self.update_manager, 
            self.include_prereleases_cb.isChecked()
        )
        self.update_thread.update_found.connect(self.on_update_found)
        self.update_thread.no_update.connect(self.on_no_update)
        self.update_thread.error_occurred.connect(self.on_update_error)
        self.update_thread.start()
    
    @pyqtSlot(object)
    def on_update_found(self, update_info: UpdateInfo):
        """Handle when an update is found"""
        self.current_update_info = update_info
        
        # Show update details
        self.details_group.setVisible(True)
        self.update_version_label.setText(f"Update Available: {update_info.version_tag}")
        self.update_version_label.setStyleSheet("color: green; font-weight: bold;")
        
        # Format date
        try:
            pub_date = datetime.fromisoformat(update_info.published_at.replace('Z', '+00:00'))
            self.update_date_label.setText(f"Released: {pub_date.strftime('%Y-%m-%d %H:%M')}")
        except:
            self.update_date_label.setText(f"Released: {update_info.published_at}")
        
        # Show release notes
        self.release_notes.setPlainText(update_info.description)
        
        # Enable download button
        self.download_btn.setEnabled(True)
        
        self.status_label.setText(f"Update {update_info.version_tag} is available!")
        self._reset_check_button()
    
    @pyqtSlot()
    def on_no_update(self):
        """Handle when no update is available"""
        self.details_group.setVisible(False)
        self.status_label.setText("You have the latest version!")
        self._reset_check_button()
    
    @pyqtSlot(str)
    def on_update_error(self, error_message: str):
        """Handle update check error"""
        self.status_label.setText(f"Error checking for updates: {error_message}")
        QMessageBox.warning(self, "Update Check Failed", f"Failed to check for updates:\n{error_message}")
        self._reset_check_button()
    
    def _reset_check_button(self):
        """Reset the check button to normal state"""
        self.check_updates_btn.setEnabled(True)
        self.check_updates_btn.setText("Check for Updates")
    
    def download_update(self):
        """Download the available update"""
        if not self.current_update_info:
            return
        
        self.download_btn.setEnabled(False)
        self.download_btn.setText("Downloading...")
        self.progress_group.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_label.setText("Downloading update...")
        
        # Start download in background thread
        self.download_thread = UpdateDownloadThread(self.update_manager, self.current_update_info)
        self.download_thread.download_complete.connect(self.on_download_complete)
        self.download_thread.start()
    
    @pyqtSlot(bool, str)
    def on_download_complete(self, success: bool, result: str):
        """Handle download completion"""
        if success:
            self.prepared_update_path = result
            self.progress_bar.setValue(100)
            self.progress_label.setText("Download complete!")
            self.install_btn.setEnabled(True)
            self.status_label.setText("Update downloaded and ready to install")
        else:
            self.progress_label.setText(f"Download failed: {result}")
            self.status_label.setText("Download failed")
            QMessageBox.critical(self, "Download Failed", f"Failed to download update:\n{result}")
        
        self.download_btn.setEnabled(True)
        self.download_btn.setText("Download Update")
    
    def install_update(self):
        """Install the downloaded update"""
        if not self.prepared_update_path:
            QMessageBox.warning(self, "No Update", "No update has been downloaded yet.")
            return
        
        reply = QMessageBox.question(
            self, "Install Update",
            "This will install the update and restart the application.\n\n"
            "Make sure to save any unsaved work before proceeding.\n\n"
            "Continue with installation?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.status_label.setText("Installing update...")
                self.install_btn.setEnabled(False)
                self.install_btn.setText("Installing...")
                
                # Install update
                success, message = self.update_manager.install_update(self.prepared_update_path, create_backup=True)
                
                if success:
                    QMessageBox.information(
                        self, "Update Installed",
                        "Update installed successfully!\n\nThe application will now restart."
                    )
                    
                    # Clean up and restart
                    self.update_manager.cleanup_temp_files()
                    self.update_manager.update_service.restart_application()
                else:
                    QMessageBox.critical(self, "Installation Failed", f"Failed to install update:\n{message}")
                    self.status_label.setText("Installation failed")
            
            except Exception as e:
                QMessageBox.critical(self, "Installation Error", f"Error during installation:\n{str(e)}")
                self.status_label.setText("Installation error")
            
            finally:
                self.install_btn.setEnabled(True)
                self.install_btn.setText("Install & Restart")
    
    def closeEvent(self, event):
        """Handle dialog close"""
        # Clean up any running threads
        if hasattr(self, 'update_thread') and self.update_thread.isRunning():
            self.update_thread.quit()
            self.update_thread.wait()
        
        if hasattr(self, 'download_thread') and self.download_thread.isRunning():
            self.download_thread.quit()
            self.download_thread.wait()
        
        event.accept()


# Test the dialog
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Example configuration - replace with your actual GitHub repo
    dialog = UpdateDialog("your-username", "prompt-organizer", "1.0.0")
    dialog.show()
    
    sys.exit(app.exec())