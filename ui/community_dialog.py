#!/usr/bin/env python3
"""
Community dialog for the Prompt Organizer application.
Provides UI for browsing, sharing, and managing community prompts.
"""

import sys
import os
from typing import List, Dict, Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QLabel, QPushButton, QComboBox, QCheckBox, QLineEdit, QTextEdit,
    QGroupBox, QListWidget, QListWidgetItem, QSplitter, QTabWidget,
    QWidget, QScrollArea, QFrame, QProgressBar, QMessageBox,
    QSpinBox, QSlider, QButtonGroup, QRadioButton, QTreeWidget,
    QTreeWidgetItem, QHeaderView, QTableWidget, QTableWidgetItem
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QFont, QIcon, QPixmap, QColor, QPalette

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.community_service import (
    CommunityService, CommunityPrompt, PromptCategory, PromptVisibility,
    PromptRating, SearchFilters, UserProfile, PromptReview
)


class CommunityPromptWidget(QWidget):
    """Widget for displaying a single community prompt"""
    
    download_requested = pyqtSignal(str)  # prompt_id
    favorite_toggled = pyqtSignal(str, bool)  # prompt_id, is_favorite
    rating_requested = pyqtSignal(str)  # prompt_id
    
    def __init__(self, prompt: CommunityPrompt, parent=None):
        super().__init__(parent)
        self.prompt = prompt
        self.is_favorite = False
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the prompt widget UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Create frame for styling
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.Box)
        frame.setLineWidth(1)
        frame_layout = QVBoxLayout(frame)
        
        # Header with title and metadata
        header_layout = QHBoxLayout()
        
        # Title and author
        title_layout = QVBoxLayout()
        
        title_label = QLabel(self.prompt.title)
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title_label.setFont(title_font)
        title_layout.addWidget(title_label)
        
        author_label = QLabel(f"by {self.prompt.author_name}")
        author_label.setStyleSheet("color: #666; font-style: italic;")
        title_layout.addWidget(author_label)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        # Rating and stats
        stats_layout = QVBoxLayout()
        
        if self.prompt.rating_count > 0:
            rating_text = f"★ {self.prompt.rating_average:.1f} ({self.prompt.rating_count} reviews)"
        else:
            rating_text = "No ratings yet"
        rating_label = QLabel(rating_text)
        rating_label.setStyleSheet("color: #f39c12; font-weight: bold;")
        stats_layout.addWidget(rating_label)
        
        downloads_label = QLabel(f"↓ {self.prompt.download_count} downloads")
        downloads_label.setStyleSheet("color: #27ae60;")
        stats_layout.addWidget(downloads_label)
        
        header_layout.addLayout(stats_layout)
        
        # Badges
        badges_layout = QVBoxLayout()
        
        if self.prompt.is_featured:
            featured_badge = QLabel("FEATURED")
            featured_badge.setStyleSheet("""
                background-color: #e74c3c; color: white; padding: 2px 6px; 
                border-radius: 8px; font-size: 8pt; font-weight: bold;
            """)
            badges_layout.addWidget(featured_badge)
        
        if self.prompt.is_verified:
            verified_badge = QLabel("VERIFIED")
            verified_badge.setStyleSheet("""
                background-color: #3498db; color: white; padding: 2px 6px; 
                border-radius: 8px; font-size: 8pt; font-weight: bold;
            """)
            badges_layout.addWidget(verified_badge)
        
        category_badge = QLabel(self.prompt.category.value.upper())
        category_badge.setStyleSheet("""
            background-color: #95a5a6; color: white; padding: 2px 6px; 
            border-radius: 8px; font-size: 8pt; font-weight: bold;
        """)
        badges_layout.addWidget(category_badge)
        
        header_layout.addLayout(badges_layout)
        
        frame_layout.addLayout(header_layout)
        
        # Description
        if self.prompt.description:
            desc_label = QLabel("Description:")
            desc_label.setFont(QFont("", 9, QFont.Weight.Bold))
            frame_layout.addWidget(desc_label)
            
            desc_text = QLabel(self.prompt.description)
            desc_text.setWordWrap(True)
            desc_text.setStyleSheet("color: #444; margin-left: 10px; margin-bottom: 10px;")
            frame_layout.addWidget(desc_text)
        
        # Content preview
        content_label = QLabel("Content Preview:")
        content_label.setFont(QFont("", 9, QFont.Weight.Bold))
        frame_layout.addWidget(content_label)
        
        content_preview = QTextEdit()
        content_preview.setPlainText(self.prompt.content[:200] + "..." if len(self.prompt.content) > 200 else self.prompt.content)
        content_preview.setMaximumHeight(80)
        content_preview.setReadOnly(True)
        content_preview.setStyleSheet("background-color: #f8f9fa; border: 1px solid #ddd; margin-left: 10px;")
        frame_layout.addWidget(content_preview)
        
        # Tags
        if self.prompt.tags:
            tags_layout = QHBoxLayout()
            tags_label = QLabel("Tags:")
            tags_label.setFont(QFont("", 8))
            tags_layout.addWidget(tags_label)
            
            for tag in self.prompt.tags[:5]:  # Show max 5 tags
                tag_label = QLabel(tag)
                tag_label.setStyleSheet("""
                    background-color: #e1e8ed; color: #1da1f2; padding: 2px 6px; 
                    border-radius: 10px; font-size: 8pt; margin-right: 3px;
                """)
                tags_layout.addWidget(tag_label)
            
            if len(self.prompt.tags) > 5:
                more_label = QLabel(f"+{len(self.prompt.tags) - 5} more")
                more_label.setStyleSheet("color: #666; font-size: 8pt;")
                tags_layout.addWidget(more_label)
            
            tags_layout.addStretch()
            frame_layout.addLayout(tags_layout)
        
        # Actions
        actions_layout = QHBoxLayout()
        
        self.download_btn = QPushButton("Download")
        self.download_btn.clicked.connect(lambda: self.download_requested.emit(self.prompt.id))
        self.download_btn.setStyleSheet("background-color: #28a745; color: white; padding: 5px 15px;")
        actions_layout.addWidget(self.download_btn)
        
        self.favorite_btn = QPushButton("♡ Favorite")
        self.favorite_btn.clicked.connect(self.toggle_favorite)
        self.favorite_btn.setStyleSheet("background-color: #ffc107; color: black; padding: 5px 15px;")
        actions_layout.addWidget(self.favorite_btn)
        
        self.rate_btn = QPushButton("Rate & Review")
        self.rate_btn.clicked.connect(lambda: self.rating_requested.emit(self.prompt.id))
        actions_layout.addWidget(self.rate_btn)
        
        actions_layout.addStretch()
        
        # Metadata
        meta_text = f"Created: {self.prompt.created_at.strftime('%Y-%m-%d')} | "
        meta_text += f"Version: {self.prompt.version} | License: {self.prompt.license}"
        meta_label = QLabel(meta_text)
        meta_label.setStyleSheet("color: #888; font-size: 8pt;")
        actions_layout.addWidget(meta_label)
        
        frame_layout.addLayout(actions_layout)
        
        layout.addWidget(frame)
    
    def toggle_favorite(self):
        """Toggle favorite status"""
        self.is_favorite = not self.is_favorite
        if self.is_favorite:
            self.favorite_btn.setText("♥ Favorited")
            self.favorite_btn.setStyleSheet("background-color: #dc3545; color: white; padding: 5px 15px;")
        else:
            self.favorite_btn.setText("♡ Favorite")
            self.favorite_btn.setStyleSheet("background-color: #ffc107; color: black; padding: 5px 15px;")
        
        self.favorite_toggled.emit(self.prompt.id, self.is_favorite)


class SharePromptDialog(QDialog):
    """Dialog for sharing a prompt to the community"""
    
    def __init__(self, community_service: CommunityService, local_prompt: Dict, parent=None):
        super().__init__(parent)
        self.community_service = community_service
        self.local_prompt = local_prompt
        
        self.setWindowTitle("Share Prompt to Community")
        self.setModal(True)
        self.resize(600, 500)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the share dialog UI"""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Share Prompt to Community")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Original prompt info
        prompt_group = QGroupBox("Original Prompt")
        prompt_layout = QVBoxLayout(prompt_group)
        
        orig_title = QLabel(f"Title: {self.local_prompt['title']}")
        orig_title.setFont(QFont("", 10, QFont.Weight.Bold))
        prompt_layout.addWidget(orig_title)
        
        orig_content = QTextEdit()
        orig_content.setPlainText(self.local_prompt['content'])
        orig_content.setMaximumHeight(100)
        orig_content.setReadOnly(True)
        prompt_layout.addWidget(orig_content)
        
        layout.addWidget(prompt_group)
        
        # Share configuration
        config_group = QGroupBox("Share Configuration")
        config_layout = QFormLayout(config_group)
        
        # Title (editable)
        self.title_edit = QLineEdit()
        self.title_edit.setText(self.local_prompt['title'])
        config_layout.addRow("Public Title:", self.title_edit)
        
        # Description
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        self.description_edit.setPlaceholderText("Describe what this prompt does and how to use it...")
        config_layout.addRow("Description:", self.description_edit)
        
        # Category
        self.category_combo = QComboBox()
        for category in PromptCategory:
            self.category_combo.addItem(category.value.title(), category)
        config_layout.addRow("Category:", self.category_combo)
        
        # Tags
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("Enter tags separated by commas (e.g., writing, creative, business)")
        config_layout.addRow("Tags:", self.tags_edit)
        
        # Visibility
        self.visibility_combo = QComboBox()
        self.visibility_combo.addItem("Public (visible to everyone)", PromptVisibility.PUBLIC)
        self.visibility_combo.addItem("Unlisted (accessible via link only)", PromptVisibility.UNLISTED)
        config_layout.addRow("Visibility:", self.visibility_combo)
        
        layout.addWidget(config_group)
        
        # License info
        license_group = QGroupBox("License Information")
        license_layout = QVBoxLayout(license_group)
        
        license_text = QLabel("""
        By sharing this prompt, you agree to license it under Creative Commons Attribution 4.0 (CC BY 4.0).
        This allows others to use, modify, and distribute your prompt with attribution.
        """)
        license_text.setWordWrap(True)
        license_text.setStyleSheet("color: #666; font-size: 9pt;")
        license_layout.addWidget(license_text)
        
        layout.addWidget(license_group)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.share_btn = QPushButton("Share to Community")
        self.share_btn.clicked.connect(self.share_prompt)
        self.share_btn.setStyleSheet("background-color: #28a745; color: white; padding: 8px 16px;")
        buttons_layout.addWidget(self.share_btn)
        
        buttons_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)
    
    def share_prompt(self):
        """Share the prompt to community"""
        title = self.title_edit.text().strip()
        description = self.description_edit.toPlainText().strip()
        category = self.category_combo.currentData()
        visibility = self.visibility_combo.currentData()
        
        if not title:
            QMessageBox.warning(self, "Warning", "Please enter a title for the shared prompt.")
            return
        
        if not description:
            QMessageBox.warning(self, "Warning", "Please enter a description for the shared prompt.")
            return
        
        # Parse tags
        tags_text = self.tags_edit.text().strip()
        tags = [tag.strip() for tag in tags_text.split(',') if tag.strip()] if tags_text else []
        
        try:
            prompt_id = self.community_service.share_prompt(
                local_prompt_id=self.local_prompt['id'],
                title=title,
                description=description,
                category=category,
                tags=tags,
                visibility=visibility
            )
            
            QMessageBox.information(
                self, "Success", 
                f"Prompt shared successfully!\nCommunity ID: {prompt_id}"
            )
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to share prompt: {str(e)}")


class RatingDialog(QDialog):
    """Dialog for rating and reviewing a community prompt"""
    
    def __init__(self, community_service: CommunityService, prompt: CommunityPrompt, parent=None):
        super().__init__(parent)
        self.community_service = community_service
        self.prompt = prompt
        
        self.setWindowTitle("Rate & Review Prompt")
        self.setModal(True)
        self.resize(500, 400)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the rating dialog UI"""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel(f"Rate & Review: {self.prompt.title}")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Author
        author_label = QLabel(f"by {self.prompt.author_name}")
        author_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(author_label)
        
        # Rating section
        rating_group = QGroupBox("Your Rating")
        rating_layout = QVBoxLayout(rating_group)
        
        # Star rating
        stars_layout = QHBoxLayout()
        stars_layout.addWidget(QLabel("Rating:"))
        
        self.rating_group = QButtonGroup()
        self.rating_buttons = []
        
        for i in range(1, 6):
            btn = QRadioButton(f"{'★' * i} ({i})")
            btn.setProperty("rating", i)
            self.rating_group.addButton(btn)
            self.rating_buttons.append(btn)
            stars_layout.addWidget(btn)
        
        stars_layout.addStretch()
        rating_layout.addLayout(stars_layout)
        
        layout.addWidget(rating_group)
        
        # Review section
        review_group = QGroupBox("Your Review (Optional)")
        review_layout = QVBoxLayout(review_group)
        
        self.review_edit = QTextEdit()
        self.review_edit.setPlaceholderText("Share your thoughts about this prompt...")
        self.review_edit.setMaximumHeight(120)
        review_layout.addWidget(self.review_edit)
        
        layout.addWidget(review_group)
        
        # Existing reviews
        if hasattr(self, 'show_existing_reviews'):
            self.show_existing_reviews()
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        submit_btn = QPushButton("Submit Rating")
        submit_btn.clicked.connect(self.submit_rating)
        submit_btn.setStyleSheet("background-color: #007bff; color: white; padding: 8px 16px;")
        buttons_layout.addWidget(submit_btn)
        
        buttons_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)
    
    def submit_rating(self):
        """Submit the rating and review"""
        # Get selected rating
        selected_button = self.rating_group.checkedButton()
        if not selected_button:
            QMessageBox.warning(self, "Warning", "Please select a rating.")
            return
        
        rating_value = selected_button.property("rating")
        rating = PromptRating(rating_value)
        comment = self.review_edit.toPlainText().strip()
        
        try:
            review_id = self.community_service.rate_prompt(
                prompt_id=self.prompt.id,
                rating=rating,
                comment=comment
            )
            
            QMessageBox.information(
                self, "Success", 
                "Thank you for your rating and review!"
            )
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to submit rating: {str(e)}")


class CommunityBrowserDialog(QDialog):
    """Main dialog for browsing the community prompt library"""
    
    def __init__(self, community_service: CommunityService, database_manager, parent=None):
        super().__init__(parent)
        self.community_service = community_service
        self.db = database_manager
        self.current_prompts = []
        
        self.setWindowTitle("Community Prompt Library")
        self.setModal(True)
        self.resize(1000, 700)
        
        self.setup_ui()
        self.load_featured_prompts()
    
    def setup_ui(self):
        """Setup the main browser UI"""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Community Prompt Library")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        
        # Browse tab
        browse_tab = self.create_browse_tab()
        self.tab_widget.addTab(browse_tab, "Browse")
        
        # Search tab
        search_tab = self.create_search_tab()
        self.tab_widget.addTab(search_tab, "Search")
        
        # My Prompts tab
        my_prompts_tab = self.create_my_prompts_tab()
        self.tab_widget.addTab(my_prompts_tab, "My Prompts")
        
        # Favorites tab
        favorites_tab = self.create_favorites_tab()
        self.tab_widget.addTab(favorites_tab, "Favorites")
        
        layout.addWidget(self.tab_widget)
        
        # Status bar
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(self.status_label)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_current_tab)
        buttons_layout.addWidget(refresh_btn)
        
        buttons_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)
    
    def create_browse_tab(self) -> QWidget:
        """Create the browse tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Categories
        categories_layout = QHBoxLayout()
        categories_layout.addWidget(QLabel("Browse by category:"))
        
        self.category_combo = QComboBox()
        self.category_combo.addItem("All Categories", None)
        for category in PromptCategory:
            self.category_combo.addItem(category.value.title(), category)
        self.category_combo.currentTextChanged.connect(self.on_category_changed)
        categories_layout.addWidget(self.category_combo)
        
        # Quick filters
        self.featured_cb = QCheckBox("Featured only")
        self.featured_cb.stateChanged.connect(self.on_filter_changed)
        categories_layout.addWidget(self.featured_cb)
        
        self.verified_cb = QCheckBox("Verified only")
        self.verified_cb.stateChanged.connect(self.on_filter_changed)
        categories_layout.addWidget(self.verified_cb)
        
        categories_layout.addStretch()
        layout.addLayout(categories_layout)
        
        # Prompts scroll area
        self.browse_scroll = QScrollArea()
        self.browse_scroll.setWidgetResizable(True)
        self.browse_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        self.browse_container = QWidget()
        self.browse_layout = QVBoxLayout(self.browse_container)
        self.browse_layout.addStretch()
        
        self.browse_scroll.setWidget(self.browse_container)
        layout.addWidget(self.browse_scroll)
        
        return widget
    
    def create_search_tab(self) -> QWidget:
        """Create the search tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Search controls
        search_layout = QHBoxLayout()
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search prompts...")
        self.search_edit.returnPressed.connect(self.perform_search)
        search_layout.addWidget(self.search_edit)
        
        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self.perform_search)
        search_layout.addWidget(search_btn)
        
        layout.addLayout(search_layout)
        
        # Search results
        self.search_scroll = QScrollArea()
        self.search_scroll.setWidgetResizable(True)
        
        self.search_container = QWidget()
        self.search_layout = QVBoxLayout(self.search_container)
        self.search_layout.addStretch()
        
        self.search_scroll.setWidget(self.search_container)
        layout.addWidget(self.search_scroll)
        
        return widget
    
    def create_my_prompts_tab(self) -> QWidget:
        """Create the my prompts tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Info
        info_label = QLabel("Your shared prompts will appear here when you're logged in.")
        info_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(info_label)
        
        # My prompts list
        self.my_prompts_scroll = QScrollArea()
        self.my_prompts_scroll.setWidgetResizable(True)
        
        self.my_prompts_container = QWidget()
        self.my_prompts_layout = QVBoxLayout(self.my_prompts_container)
        self.my_prompts_layout.addStretch()
        
        self.my_prompts_scroll.setWidget(self.my_prompts_container)
        layout.addWidget(self.my_prompts_scroll)
        
        return widget
    
    def create_favorites_tab(self) -> QWidget:
        """Create the favorites tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Info
        info_label = QLabel("Your favorite community prompts will appear here.")
        info_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(info_label)
        
        # Favorites list
        self.favorites_scroll = QScrollArea()
        self.favorites_scroll.setWidgetResizable(True)
        
        self.favorites_container = QWidget()
        self.favorites_layout = QVBoxLayout(self.favorites_container)
        self.favorites_layout.addStretch()
        
        self.favorites_scroll.setWidget(self.favorites_container)
        layout.addWidget(self.favorites_scroll)
        
        return widget
    
    def load_featured_prompts(self):
        """Load featured prompts"""
        try:
            prompts = self.community_service.get_featured_prompts(limit=20)
            self.display_prompts(prompts, self.browse_layout)
            self.status_label.setText(f"Loaded {len(prompts)} featured prompts")
        except Exception as e:
            self.status_label.setText(f"Error loading prompts: {str(e)}")
    
    def on_category_changed(self):
        """Handle category change"""
        self.on_filter_changed()
    
    def on_filter_changed(self):
        """Handle filter change"""
        category = self.category_combo.currentData()
        featured_only = self.featured_cb.isChecked()
        verified_only = self.verified_cb.isChecked()
        
        filters = SearchFilters(
            category=category,
            featured_only=featured_only,
            verified_only=verified_only,
            sort_by="rating",
            sort_order="desc",
            limit=50
        )
        
        try:
            prompts = self.community_service.search_prompts(filters)
            self.display_prompts(prompts, self.browse_layout)
            self.status_label.setText(f"Found {len(prompts)} prompts")
        except Exception as e:
            self.status_label.setText(f"Error searching prompts: {str(e)}")
    
    def perform_search(self):
        """Perform search"""
        query = self.search_edit.text().strip()
        if not query:
            return
        
        filters = SearchFilters(
            query=query,
            sort_by="rating",
            sort_order="desc",
            limit=50
        )
        
        try:
            prompts = self.community_service.search_prompts(filters)
            self.display_prompts(prompts, self.search_layout)
            self.status_label.setText(f"Found {len(prompts)} prompts for '{query}'")
        except Exception as e:
            self.status_label.setText(f"Search error: {str(e)}")
    
    def display_prompts(self, prompts: List[CommunityPrompt], target_layout: QVBoxLayout):
        """Display prompts in the specified layout"""
        # Clear existing prompts
        for i in reversed(range(target_layout.count() - 1)):  # Keep the stretch
            child = target_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        if not prompts:
            no_prompts_label = QLabel("No prompts found")
            no_prompts_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_prompts_label.setStyleSheet("color: gray; font-style: italic; padding: 20px;")
            target_layout.insertWidget(0, no_prompts_label)
            return
        
        # Add prompt widgets
        for prompt in prompts:
            prompt_widget = CommunityPromptWidget(prompt)
            prompt_widget.download_requested.connect(self.download_prompt)
            prompt_widget.favorite_toggled.connect(self.toggle_favorite)
            prompt_widget.rating_requested.connect(self.rate_prompt)
            target_layout.insertWidget(target_layout.count() - 1, prompt_widget)
    
    def download_prompt(self, prompt_id: str):
        """Download a community prompt"""
        try:
            local_prompt_id = self.community_service.download_prompt(prompt_id)
            if local_prompt_id:
                QMessageBox.information(
                    self, "Success", 
                    f"Prompt downloaded successfully!\nLocal ID: {local_prompt_id}"
                )
            else:
                QMessageBox.warning(self, "Warning", "Failed to download prompt.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Download failed: {str(e)}")
    
    def toggle_favorite(self, prompt_id: str, is_favorite: bool):
        """Toggle favorite status"""
        try:
            if is_favorite:
                success = self.community_service.add_to_favorites(prompt_id)
                message = "Added to favorites" if success else "Already in favorites"
            else:
                success = self.community_service.remove_from_favorites(prompt_id)
                message = "Removed from favorites" if success else "Not in favorites"
            
            self.status_label.setText(message)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update favorites: {str(e)}")
    
    def rate_prompt(self, prompt_id: str):
        """Show rating dialog for a prompt"""
        try:
            prompt = self.community_service.get_community_prompt(prompt_id)
            if prompt:
                dialog = RatingDialog(self.community_service, prompt, self)
                dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open rating dialog: {str(e)}")
    
    def refresh_current_tab(self):
        """Refresh the current tab"""
        current_index = self.tab_widget.currentIndex()
        
        if current_index == 0:  # Browse tab
            self.on_filter_changed()
        elif current_index == 1:  # Search tab
            if self.search_edit.text().strip():
                self.perform_search()
        elif current_index == 2:  # My Prompts tab
            self.load_my_prompts()
        elif current_index == 3:  # Favorites tab
            self.load_favorites()
    
    def load_my_prompts(self):
        """Load user's shared prompts"""
        # This would load the user's prompts when logged in
        self.status_label.setText("Login required to view your prompts")
    
    def load_favorites(self):
        """Load user's favorite prompts"""
        # This would load the user's favorites when logged in
        self.status_label.setText("Login required to view favorites")


# Test the dialog
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # Mock community service for testing
    class MockCommunityService:
        def get_featured_prompts(self, limit=10):
            from datetime import datetime
            return [
                CommunityPrompt(
                    id="test1",
                    title="Test Prompt 1",
                    content="This is a test prompt content for testing the UI.",
                    description="A sample prompt for testing purposes",
                    category=PromptCategory.WRITING,
                    tags=["test", "sample", "writing"],
                    author_id="user1",
                    author_name="Test User",
                    visibility=PromptVisibility.PUBLIC,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    download_count=42,
                    rating_average=4.5,
                    rating_count=10,
                    is_featured=True,
                    is_verified=True
                )
            ]
        
        def search_prompts(self, filters):
            return self.get_featured_prompts()
        
        def download_prompt(self, prompt_id):
            return 123  # Mock local prompt ID
        
        def add_to_favorites(self, prompt_id):
            return True
        
        def remove_from_favorites(self, prompt_id):
            return True
        
        def get_community_prompt(self, prompt_id):
            return self.get_featured_prompts()[0]
    
    # Mock database manager
    class MockDatabaseManager:
        pass
    
    dialog = CommunityBrowserDialog(MockCommunityService(), MockDatabaseManager())
    dialog.show()
    
    sys.exit(app.exec_())