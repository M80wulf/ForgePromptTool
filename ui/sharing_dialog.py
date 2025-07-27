"""
Sharing dialog for the Prompt Organizer application
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QLineEdit, QPushButton, QTextEdit, QComboBox,
    QCheckBox, QSpinBox, QTableWidget, QTableWidgetItem,
    QMessageBox, QGroupBox, QFormLayout, QDateEdit,
    QListWidget, QListWidgetItem, QSplitter
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont, QIcon
from datetime import datetime, timedelta
from typing import Optional, List
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.sharing_models import SharePermission, ShareLink, Collaborator
from services.sharing_service import SharingService


class SharingDialog(QDialog):
    """Dialog for managing prompt sharing and collaboration"""
    
    def __init__(self, prompt_id: int, prompt_title: str, sharing_service: SharingService, parent=None):
        super().__init__(parent)
        self.prompt_id = prompt_id
        self.prompt_title = prompt_title
        self.sharing_service = sharing_service
        self.current_user_id = "current_user"  # This would come from user session
        
        self.setWindowTitle(f"Share Prompt: {prompt_title}")
        self.setModal(True)
        self.resize(600, 500)
        
        self.setup_ui()
        self.load_sharing_data()
    
    def setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Share Link tab
        self.setup_share_link_tab()
        
        # Collaborators tab
        self.setup_collaborators_tab()
        
        # Activity tab
        self.setup_activity_tab()
        
        # Dialog buttons
        button_layout = QHBoxLayout()
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        button_layout.addStretch()
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
    
    def setup_share_link_tab(self):
        """Setup the share link tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        
        # Create share link section
        create_group = QGroupBox("Create Share Link")
        create_layout = QFormLayout()
        
        # Permission selection
        self.permission_combo = QComboBox()
        self.permission_combo.addItem("Read Only", SharePermission.READ)
        self.permission_combo.addItem("Read & Write", SharePermission.WRITE)
        self.permission_combo.addItem("Admin", SharePermission.ADMIN)
        create_layout.addRow("Permission:", self.permission_combo)
        
        # Expiry settings
        self.expiry_checkbox = QCheckBox("Set expiry date")
        self.expiry_date = QDateEdit()
        self.expiry_date.setDate(QDate.currentDate().addDays(30))
        self.expiry_date.setEnabled(False)
        self.expiry_checkbox.toggled.connect(self.expiry_date.setEnabled)
        
        expiry_layout = QHBoxLayout()
        expiry_layout.addWidget(self.expiry_checkbox)
        expiry_layout.addWidget(self.expiry_date)
        create_layout.addRow("Expiry:", expiry_layout)
        
        # Max uses
        self.max_uses_checkbox = QCheckBox("Limit uses")
        self.max_uses_spin = QSpinBox()
        self.max_uses_spin.setRange(1, 1000)
        self.max_uses_spin.setValue(10)
        self.max_uses_spin.setEnabled(False)
        self.max_uses_checkbox.toggled.connect(self.max_uses_spin.setEnabled)
        
        uses_layout = QHBoxLayout()
        uses_layout.addWidget(self.max_uses_checkbox)
        uses_layout.addWidget(self.max_uses_spin)
        create_layout.addRow("Max Uses:", uses_layout)
        
        # Description
        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("Optional description for this share link")
        create_layout.addRow("Description:", self.description_edit)
        
        # Create button
        self.create_link_btn = QPushButton("Create Share Link")
        self.create_link_btn.clicked.connect(self.create_share_link)
        create_layout.addRow("", self.create_link_btn)
        
        create_group.setLayout(create_layout)
        layout.addWidget(create_group)
        
        # Existing links section
        links_group = QGroupBox("Existing Share Links")
        links_layout = QVBoxLayout()
        
        self.links_table = QTableWidget()
        self.links_table.setColumnCount(6)
        self.links_table.setHorizontalHeaderLabels([
            "Token", "Permission", "Created", "Expires", "Uses", "Actions"
        ])
        self.links_table.horizontalHeader().setStretchLastSection(True)
        links_layout.addWidget(self.links_table)
        
        links_group.setLayout(links_layout)
        layout.addWidget(links_group)
        
        self.tab_widget.addTab(tab, "Share Links")
    
    def setup_collaborators_tab(self):
        """Setup the collaborators tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        
        # Add collaborator section
        add_group = QGroupBox("Add Collaborator")
        add_layout = QFormLayout()
        
        self.collab_email = QLineEdit()
        self.collab_email.setPlaceholderText("collaborator@example.com")
        add_layout.addRow("Email:", self.collab_email)
        
        self.collab_name = QLineEdit()
        self.collab_name.setPlaceholderText("Collaborator Name")
        add_layout.addRow("Name:", self.collab_name)
        
        self.collab_permission = QComboBox()
        self.collab_permission.addItem("Read Only", SharePermission.READ)
        self.collab_permission.addItem("Read & Write", SharePermission.WRITE)
        self.collab_permission.addItem("Admin", SharePermission.ADMIN)
        add_layout.addRow("Permission:", self.collab_permission)
        
        self.add_collab_btn = QPushButton("Add Collaborator")
        self.add_collab_btn.clicked.connect(self.add_collaborator)
        add_layout.addRow("", self.add_collab_btn)
        
        add_group.setLayout(add_layout)
        layout.addWidget(add_group)
        
        # Existing collaborators
        collabs_group = QGroupBox("Current Collaborators")
        collabs_layout = QVBoxLayout()
        
        self.collabs_table = QTableWidget()
        self.collabs_table.setColumnCount(5)
        self.collabs_table.setHorizontalHeaderLabels([
            "Name", "Email", "Permission", "Added", "Actions"
        ])
        self.collabs_table.horizontalHeader().setStretchLastSection(True)
        collabs_layout.addWidget(self.collabs_table)
        
        collabs_group.setLayout(collabs_layout)
        layout.addWidget(collabs_group)
        
        self.tab_widget.addTab(tab, "Collaborators")
    
    def setup_activity_tab(self):
        """Setup the activity tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        
        # Activity list
        activity_group = QGroupBox("Recent Activity")
        activity_layout = QVBoxLayout()
        
        self.activity_list = QListWidget()
        activity_layout.addWidget(self.activity_list)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh Activity")
        refresh_btn.clicked.connect(self.load_activity)
        activity_layout.addWidget(refresh_btn)
        
        activity_group.setLayout(activity_layout)
        layout.addWidget(activity_group)
        
        self.tab_widget.addTab(tab, "Activity")
    
    def create_share_link(self):
        """Create a new share link"""
        try:
            permission = self.permission_combo.currentData()
            
            expires_in_days = None
            if self.expiry_checkbox.isChecked():
                days_diff = QDate.currentDate().daysTo(self.expiry_date.date())
                expires_in_days = max(1, days_diff)
            
            max_uses = None
            if self.max_uses_checkbox.isChecked():
                max_uses = self.max_uses_spin.value()
            
            description = self.description_edit.text().strip()
            
            share_link = self.sharing_service.create_share_link(
                self.prompt_id,
                self.current_user_id,
                permission,
                expires_in_days,
                max_uses,
                description
            )
            
            if share_link:
                # Show the share link to user
                link_url = f"https://promptorganizer.app/shared/{share_link.token}"
                
                QMessageBox.information(
                    self, "Share Link Created",
                    f"Share link created successfully!\n\n"
                    f"Link: {link_url}\n\n"
                    f"Permission: {permission.value}\n"
                    f"This link has been copied to your clipboard."
                )
                
                # Copy to clipboard
                from PyQt6.QtWidgets import QApplication
                clipboard = QApplication.clipboard()
                clipboard.setText(link_url)
                
                # Refresh the links table
                self.load_share_links()
                
                # Clear form
                self.description_edit.clear()
                self.expiry_checkbox.setChecked(False)
                self.max_uses_checkbox.setChecked(False)
            else:
                QMessageBox.warning(self, "Error", "Failed to create share link.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error creating share link: {str(e)}")
    
    def add_collaborator(self):
        """Add a new collaborator"""
        try:
            email = self.collab_email.text().strip()
            name = self.collab_name.text().strip()
            permission = self.collab_permission.currentData()
            
            if not email or not name:
                QMessageBox.warning(self, "Warning", "Please enter both email and name.")
                return
            
            # Generate user ID from email (in real app, this would be looked up)
            user_id = email.replace("@", "_").replace(".", "_")
            
            success = self.sharing_service.add_collaborator(
                self.prompt_id, user_id, name, email, permission, self.current_user_id
            )
            
            if success:
                QMessageBox.information(self, "Success", f"Added {name} as collaborator.")
                self.load_collaborators()
                
                # Clear form
                self.collab_email.clear()
                self.collab_name.clear()
            else:
                QMessageBox.warning(self, "Error", "Failed to add collaborator.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error adding collaborator: {str(e)}")
    
    def load_sharing_data(self):
        """Load all sharing data"""
        self.load_share_links()
        self.load_collaborators()
        self.load_activity()
    
    def load_share_links(self):
        """Load existing share links"""
        try:
            # Get share links for this user (simplified - would need proper user management)
            shared_prompts = self.sharing_service.get_shared_prompts_by_user(self.current_user_id)
            
            # Filter for current prompt
            links = [sp for sp in shared_prompts if sp.prompt_id == self.prompt_id]
            
            self.links_table.setRowCount(len(links))
            
            for row, link in enumerate(links):
                # Token (truncated)
                token_item = QTableWidgetItem(link.share_token[:8] + "...")
                token_item.setToolTip(link.share_token)
                self.links_table.setItem(row, 0, token_item)
                
                # Permission
                self.links_table.setItem(row, 1, QTableWidgetItem(link.permission.value))
                
                # Created
                created_date = datetime.fromisoformat(link.created_at).strftime("%Y-%m-%d %H:%M")
                self.links_table.setItem(row, 2, QTableWidgetItem(created_date))
                
                # Expires
                expires_text = "Never"
                if link.expires_at:
                    expires_date = datetime.fromisoformat(link.expires_at).strftime("%Y-%m-%d %H:%M")
                    expires_text = expires_date
                self.links_table.setItem(row, 3, QTableWidgetItem(expires_text))
                
                # Uses
                uses_text = str(link.access_count)
                self.links_table.setItem(row, 4, QTableWidgetItem(uses_text))
                
                # Actions (simplified)
                self.links_table.setItem(row, 5, QTableWidgetItem("Revoke"))
                
        except Exception as e:
            print(f"Error loading share links: {e}")
    
    def load_collaborators(self):
        """Load existing collaborators"""
        try:
            collaborators = self.sharing_service.get_collaborators(self.prompt_id)
            
            self.collabs_table.setRowCount(len(collaborators))
            
            for row, collab in enumerate(collaborators):
                self.collabs_table.setItem(row, 0, QTableWidgetItem(collab.user_name))
                self.collabs_table.setItem(row, 1, QTableWidgetItem(collab.email))
                self.collabs_table.setItem(row, 2, QTableWidgetItem(collab.permission.value))
                
                added_date = datetime.fromisoformat(collab.added_at).strftime("%Y-%m-%d")
                self.collabs_table.setItem(row, 3, QTableWidgetItem(added_date))
                
                self.collabs_table.setItem(row, 4, QTableWidgetItem("Remove"))
                
        except Exception as e:
            print(f"Error loading collaborators: {e}")
    
    def load_activity(self):
        """Load sharing activity"""
        try:
            activities = self.sharing_service.get_share_activity(self.prompt_id, 20)
            
            self.activity_list.clear()
            
            for activity in activities:
                timestamp = datetime.fromisoformat(activity.timestamp).strftime("%Y-%m-%d %H:%M")
                text = f"[{timestamp}] {activity.user_name}: {activity.details}"
                
                item = QListWidgetItem(text)
                item.setToolTip(f"Action: {activity.action}")
                self.activity_list.addItem(item)
                
        except Exception as e:
            print(f"Error loading activity: {e}")


class ShareLinkViewerDialog(QDialog):
    """Dialog for viewing a shared prompt via link"""
    
    def __init__(self, share_token: str, sharing_service: SharingService, parent=None):
        super().__init__(parent)
        self.share_token = share_token
        self.sharing_service = sharing_service
        self.shared_data = None
        
        self.setWindowTitle("Shared Prompt")
        self.setModal(True)
        self.resize(600, 400)
        
        self.setup_ui()
        self.load_shared_prompt()
    
    def setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Prompt info
        info_group = QGroupBox("Prompt Information")
        info_layout = QFormLayout()
        
        self.title_label = QLabel()
        self.title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        info_layout.addRow("Title:", self.title_label)
        
        self.shared_by_label = QLabel()
        info_layout.addRow("Shared by:", self.shared_by_label)
        
        self.permission_label = QLabel()
        info_layout.addRow("Your permission:", self.permission_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Prompt content
        content_group = QGroupBox("Content")
        content_layout = QVBoxLayout()
        
        self.content_text = QTextEdit()
        self.content_text.setReadOnly(True)
        content_layout.addWidget(self.content_text)
        
        content_group.setLayout(content_layout)
        layout.addWidget(content_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.copy_btn = QPushButton("Copy Content")
        self.copy_btn.clicked.connect(self.copy_content)
        button_layout.addWidget(self.copy_btn)
        
        button_layout.addStretch()
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
    
    def load_shared_prompt(self):
        """Load the shared prompt data"""
        try:
            self.shared_data = self.sharing_service.access_shared_prompt(self.share_token)
            
            if not self.shared_data:
                QMessageBox.critical(self, "Error", "Invalid or expired share link.")
                self.reject()
                return
            
            prompt = self.shared_data['prompt']
            share_info = self.shared_data['share_info']
            permission = self.shared_data['permission']
            
            # Update UI
            self.title_label.setText(prompt['title'])
            self.shared_by_label.setText(share_info['created_by'])
            self.permission_label.setText(permission.value)
            self.content_text.setPlainText(prompt['content'])
            
            # Enable editing if user has write permission
            if permission in [SharePermission.WRITE, SharePermission.ADMIN]:
                self.content_text.setReadOnly(False)
                
                save_btn = QPushButton("Save Changes")
                save_btn.clicked.connect(self.save_changes)
                self.layout().itemAt(-1).layout().insertWidget(-2, save_btn)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading shared prompt: {str(e)}")
            self.reject()
    
    def copy_content(self):
        """Copy prompt content to clipboard"""
        if self.shared_data:
            from PyQt6.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            clipboard.setText(self.shared_data['prompt']['content'])
            
            QMessageBox.information(self, "Copied", "Prompt content copied to clipboard.")
    
    def save_changes(self):
        """Save changes to the shared prompt (if user has permission)"""
        # This would require additional implementation in the sharing service
        QMessageBox.information(self, "Info", "Save functionality would be implemented here.")