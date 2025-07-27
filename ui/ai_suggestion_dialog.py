#!/usr/bin/env python3
"""
AI Suggestion Dialog for the Prompt Organizer application.
Provides UI for viewing and managing AI-powered prompt suggestions.
"""

import sys
import json
from datetime import datetime
from typing import List, Optional, Dict, Any

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget,
    QLabel, QTextEdit, QPushButton, QListWidget, QListWidgetItem,
    QProgressBar, QFrame, QScrollArea, QWidget, QSplitter,
    QGroupBox, QComboBox, QSpinBox, QCheckBox, QMessageBox,
    QApplication, QHeaderView, QTableWidget, QTableWidgetItem,
    QTextBrowser, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QFont, QColor, QPalette, QIcon, QPixmap

from services.ai_suggestion_service import AISuggestionService, PromptSuggestion, PromptAnalysis


class PromptAnalysisWidget(QWidget):
    """Widget for displaying prompt analysis results"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.analysis = None
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the analysis widget UI"""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Prompt Analysis")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Scores section
        scores_group = QGroupBox("Quality Scores")
        scores_layout = QGridLayout(scores_group)
        
        # Score labels and progress bars
        self.clarity_label = QLabel("Clarity:")
        self.clarity_bar = QProgressBar()
        self.clarity_bar.setRange(0, 100)
        self.clarity_score_label = QLabel("0%")
        
        self.specificity_label = QLabel("Specificity:")
        self.specificity_bar = QProgressBar()
        self.specificity_bar.setRange(0, 100)
        self.specificity_score_label = QLabel("0%")
        
        self.completeness_label = QLabel("Completeness:")
        self.completeness_bar = QProgressBar()
        self.completeness_bar.setRange(0, 100)
        self.completeness_score_label = QLabel("0%")
        
        self.overall_label = QLabel("Overall:")
        self.overall_bar = QProgressBar()
        self.overall_bar.setRange(0, 100)
        self.overall_score_label = QLabel("0%")
        
        # Add to grid
        scores_layout.addWidget(self.clarity_label, 0, 0)
        scores_layout.addWidget(self.clarity_bar, 0, 1)
        scores_layout.addWidget(self.clarity_score_label, 0, 2)
        
        scores_layout.addWidget(self.specificity_label, 1, 0)
        scores_layout.addWidget(self.specificity_bar, 1, 1)
        scores_layout.addWidget(self.specificity_score_label, 1, 2)
        
        scores_layout.addWidget(self.completeness_label, 2, 0)
        scores_layout.addWidget(self.completeness_bar, 2, 1)
        scores_layout.addWidget(self.completeness_score_label, 2, 2)
        
        scores_layout.addWidget(self.overall_label, 3, 0)
        scores_layout.addWidget(self.overall_bar, 3, 1)
        scores_layout.addWidget(self.overall_score_label, 3, 2)
        
        layout.addWidget(scores_group)
        
        # Strengths and weaknesses
        feedback_layout = QHBoxLayout()
        
        # Strengths
        strengths_group = QGroupBox("Strengths")
        strengths_layout = QVBoxLayout(strengths_group)
        self.strengths_list = QListWidget()
        strengths_layout.addWidget(self.strengths_list)
        feedback_layout.addWidget(strengths_group)
        
        # Weaknesses
        weaknesses_group = QGroupBox("Areas for Improvement")
        weaknesses_layout = QVBoxLayout(weaknesses_group)
        self.weaknesses_list = QListWidget()
        weaknesses_layout.addWidget(self.weaknesses_list)
        feedback_layout.addWidget(weaknesses_group)
        
        layout.addLayout(feedback_layout)
        
        # Analysis timestamp
        self.timestamp_label = QLabel("Analysis performed: Not analyzed")
        self.timestamp_label.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(self.timestamp_label)
    
    def set_analysis(self, analysis: PromptAnalysis):
        """Set the analysis data to display"""
        self.analysis = analysis
        
        # Update scores
        self.clarity_bar.setValue(int(analysis.clarity_score * 100))
        self.clarity_score_label.setText(f"{analysis.clarity_score:.1%}")
        
        self.specificity_bar.setValue(int(analysis.specificity_score * 100))
        self.specificity_score_label.setText(f"{analysis.specificity_score:.1%}")
        
        self.completeness_bar.setValue(int(analysis.completeness_score * 100))
        self.completeness_score_label.setText(f"{analysis.completeness_score:.1%}")
        
        self.overall_bar.setValue(int(analysis.overall_score * 100))
        self.overall_score_label.setText(f"{analysis.overall_score:.1%}")
        
        # Set progress bar colors based on scores
        self._set_progress_bar_color(self.clarity_bar, analysis.clarity_score)
        self._set_progress_bar_color(self.specificity_bar, analysis.specificity_score)
        self._set_progress_bar_color(self.completeness_bar, analysis.completeness_score)
        self._set_progress_bar_color(self.overall_bar, analysis.overall_score)
        
        # Update strengths
        self.strengths_list.clear()
        for strength in analysis.strengths:
            item = QListWidgetItem(f"✓ {strength}")
            item.setForeground(QColor(0, 150, 0))
            self.strengths_list.addItem(item)
        
        # Update weaknesses
        self.weaknesses_list.clear()
        for weakness in analysis.weaknesses:
            item = QListWidgetItem(f"⚠ {weakness}")
            item.setForeground(QColor(200, 100, 0))
            self.weaknesses_list.addItem(item)
        
        # Update timestamp
        self.timestamp_label.setText(f"Analysis performed: {analysis.analyzed_at.strftime('%Y-%m-%d %H:%M:%S')}")
    
    def _set_progress_bar_color(self, progress_bar: QProgressBar, score: float):
        """Set progress bar color based on score"""
        if score >= 0.8:
            color = "green"
        elif score >= 0.6:
            color = "orange"
        else:
            color = "red"
        
        progress_bar.setStyleSheet(f"""
            QProgressBar::chunk {{
                background-color: {color};
            }}
        """)


class SuggestionWidget(QWidget):
    """Widget for displaying a single suggestion"""
    
    suggestion_applied = pyqtSignal(str)  # suggestion_id
    suggestion_rated = pyqtSignal(str, int)  # suggestion_id, rating
    
    def __init__(self, suggestion: PromptSuggestion, parent=None):
        super().__init__(parent)
        self.suggestion = suggestion
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the suggestion widget UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Create frame for styling
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.Box)
        frame.setLineWidth(1)
        frame_layout = QVBoxLayout(frame)
        
        # Header with title and confidence
        header_layout = QHBoxLayout()
        
        title_label = QLabel(self.suggestion.title)
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Confidence indicator
        confidence_label = QLabel(f"Confidence: {self.suggestion.confidence:.1%}")
        confidence_label.setStyleSheet(self._get_confidence_style())
        header_layout.addWidget(confidence_label)
        
        # Type badge
        type_label = QLabel(self.suggestion.suggestion_type.title())
        type_label.setStyleSheet(self._get_type_style())
        header_layout.addWidget(type_label)
        
        frame_layout.addLayout(header_layout)
        
        # Reasoning
        reasoning_label = QLabel("Reasoning:")
        reasoning_label.setFont(QFont("", 9, QFont.Weight.Bold))
        frame_layout.addWidget(reasoning_label)
        
        reasoning_text = QLabel(self.suggestion.reasoning)
        reasoning_text.setWordWrap(True)
        reasoning_text.setStyleSheet("color: #666; margin-left: 10px;")
        frame_layout.addWidget(reasoning_text)
        
        # Content
        content_label = QLabel("Suggested Content:")
        content_label.setFont(QFont("", 9, QFont.Weight.Bold))
        frame_layout.addWidget(content_label)
        
        content_text = QTextBrowser()
        content_text.setPlainText(self.suggestion.content)
        content_text.setMaximumHeight(150)
        content_text.setStyleSheet("background-color: #f8f8f8; border: 1px solid #ddd; margin-left: 10px;")
        frame_layout.addWidget(content_text)
        
        # Actions
        actions_layout = QHBoxLayout()
        
        # Apply button
        if not self.suggestion.applied:
            self.apply_button = QPushButton("Apply Suggestion")
            self.apply_button.clicked.connect(self._apply_suggestion)
            self.apply_button.setStyleSheet("background-color: #4CAF50; color: white; padding: 5px 15px;")
            actions_layout.addWidget(self.apply_button)
        else:
            applied_label = QLabel("✓ Applied")
            applied_label.setStyleSheet("color: green; font-weight: bold;")
            actions_layout.addWidget(applied_label)
        
        actions_layout.addStretch()
        
        # Rating
        rating_label = QLabel("Rate:")
        actions_layout.addWidget(rating_label)
        
        self.rating_combo = QComboBox()
        self.rating_combo.addItems(["", "⭐", "⭐⭐", "⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐⭐⭐"])
        if self.suggestion.user_rating:
            self.rating_combo.setCurrentIndex(self.suggestion.user_rating)
        self.rating_combo.currentIndexChanged.connect(self._rate_suggestion)
        actions_layout.addWidget(self.rating_combo)
        
        frame_layout.addLayout(actions_layout)
        
        # Tags
        if self.suggestion.tags:
            tags_layout = QHBoxLayout()
            tags_label = QLabel("Tags:")
            tags_label.setFont(QFont("", 8))
            tags_layout.addWidget(tags_label)
            
            for tag in self.suggestion.tags:
                tag_label = QLabel(tag)
                tag_label.setStyleSheet("""
                    background-color: #e1e8ed; 
                    color: #1da1f2; 
                    padding: 2px 6px; 
                    border-radius: 10px; 
                    font-size: 8pt;
                """)
                tags_layout.addWidget(tag_label)
            
            tags_layout.addStretch()
            frame_layout.addLayout(tags_layout)
        
        layout.addWidget(frame)
    
    def _get_confidence_style(self) -> str:
        """Get style for confidence indicator"""
        if self.suggestion.confidence >= 0.8:
            return "color: green; font-weight: bold;"
        elif self.suggestion.confidence >= 0.6:
            return "color: orange; font-weight: bold;"
        else:
            return "color: red; font-weight: bold;"
    
    def _get_type_style(self) -> str:
        """Get style for suggestion type"""
        colors = {
            "improvement": "#2196F3",
            "alternative": "#FF9800",
            "template": "#9C27B0",
            "completion": "#4CAF50"
        }
        
        color = colors.get(self.suggestion.suggestion_type, "#666")
        return f"""
            background-color: {color}; 
            color: white; 
            padding: 2px 8px; 
            border-radius: 12px; 
            font-size: 10pt;
            font-weight: bold;
        """
    
    def _apply_suggestion(self):
        """Apply the suggestion"""
        self.suggestion_applied.emit(self.suggestion.suggestion_id)
        self.apply_button.setText("Applied!")
        self.apply_button.setEnabled(False)
        self.apply_button.setStyleSheet("background-color: #888; color: white; padding: 5px 15px;")
    
    def _rate_suggestion(self, index: int):
        """Rate the suggestion"""
        if index > 0:
            self.suggestion_rated.emit(self.suggestion.suggestion_id, index)


class AISuggestionDialog(QDialog):
    """Dialog for viewing and managing AI suggestions for a prompt"""
    
    def __init__(self, ai_service: AISuggestionService, prompt_id: int, prompt_content: str, parent=None):
        super().__init__(parent)
        self.ai_service = ai_service
        self.prompt_id = prompt_id
        self.prompt_content = prompt_content
        self.analysis = None
        self.suggestions = []
        
        self.setWindowTitle("AI Prompt Analysis & Suggestions")
        self.setModal(True)
        self.resize(900, 700)
        
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("AI-Powered Prompt Analysis & Suggestions")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Original prompt display
        prompt_group = QGroupBox("Original Prompt")
        prompt_layout = QVBoxLayout(prompt_group)
        
        self.prompt_display = QTextBrowser()
        self.prompt_display.setPlainText(self.prompt_content)
        self.prompt_display.setMaximumHeight(100)
        prompt_layout.addWidget(self.prompt_display)
        
        layout.addWidget(prompt_group)
        
        # Tab widget for analysis and suggestions
        self.tab_widget = QTabWidget()
        
        # Analysis tab
        self.analysis_widget = PromptAnalysisWidget()
        self.tab_widget.addTab(self.analysis_widget, "Analysis")
        
        # Suggestions tab
        suggestions_widget = QWidget()
        suggestions_layout = QVBoxLayout(suggestions_widget)
        
        # Suggestions header
        suggestions_header = QHBoxLayout()
        suggestions_title = QLabel("AI Suggestions")
        suggestions_title.setFont(QFont("", 12, QFont.Weight.Bold))
        suggestions_header.addWidget(suggestions_title)
        
        suggestions_header.addStretch()
        
        # Filter controls
        filter_label = QLabel("Filter:")
        suggestions_header.addWidget(filter_label)
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All", "Improvement", "Alternative", "Template", "Completion"])
        self.filter_combo.currentTextChanged.connect(self.filter_suggestions)
        suggestions_header.addWidget(self.filter_combo)
        
        suggestions_layout.addLayout(suggestions_header)
        
        # Suggestions scroll area
        self.suggestions_scroll = QScrollArea()
        self.suggestions_scroll.setWidgetResizable(True)
        self.suggestions_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.suggestions_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        self.suggestions_container = QWidget()
        self.suggestions_layout = QVBoxLayout(self.suggestions_container)
        self.suggestions_layout.addStretch()
        
        self.suggestions_scroll.setWidget(self.suggestions_container)
        suggestions_layout.addWidget(self.suggestions_scroll)
        
        self.tab_widget.addTab(suggestions_widget, "Suggestions")
        
        layout.addWidget(self.tab_widget)
        
        # Action buttons
        buttons_layout = QHBoxLayout()
        
        self.reanalyze_button = QPushButton("Re-analyze Prompt")
        self.reanalyze_button.clicked.connect(self.reanalyze_prompt)
        buttons_layout.addWidget(self.reanalyze_button)
        
        buttons_layout.addStretch()
        
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        buttons_layout.addWidget(self.close_button)
        
        layout.addLayout(buttons_layout)
        
        # Status bar
        self.status_label = QLabel("Loading analysis...")
        self.status_label.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(self.status_label)
    
    def load_data(self):
        """Load analysis and suggestions data"""
        # Check if analysis already exists
        self.analysis = self.ai_service.get_prompt_analysis(self.prompt_id)
        
        if self.analysis:
            self.display_analysis()
            self.display_suggestions()
            self.status_label.setText("Analysis loaded from cache")
        else:
            self.analyze_prompt()
    
    def analyze_prompt(self):
        """Analyze the prompt using AI service"""
        self.status_label.setText("Analyzing prompt...")
        self.reanalyze_button.setEnabled(False)
        
        try:
            # Perform analysis
            self.analysis = self.ai_service.analyze_prompt(self.prompt_id, self.prompt_content)
            
            self.display_analysis()
            self.display_suggestions()
            
            self.status_label.setText(f"Analysis complete - {len(self.analysis.suggestions)} suggestions generated")
            
        except Exception as e:
            QMessageBox.critical(self, "Analysis Error", f"Failed to analyze prompt: {str(e)}")
            self.status_label.setText("Analysis failed")
        
        finally:
            self.reanalyze_button.setEnabled(True)
    
    def reanalyze_prompt(self):
        """Re-analyze the prompt"""
        reply = QMessageBox.question(
            self,
            "Re-analyze Prompt",
            "This will generate a new analysis and suggestions. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.analyze_prompt()
    
    def display_analysis(self):
        """Display the analysis results"""
        if self.analysis:
            self.analysis_widget.set_analysis(self.analysis)
    
    def display_suggestions(self):
        """Display the suggestions"""
        # Clear existing suggestions
        for i in reversed(range(self.suggestions_layout.count() - 1)):  # Keep the stretch
            child = self.suggestions_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        if not self.analysis or not self.analysis.suggestions:
            no_suggestions_label = QLabel("No suggestions available")
            no_suggestions_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_suggestions_label.setStyleSheet("color: gray; font-style: italic; padding: 20px;")
            self.suggestions_layout.insertWidget(0, no_suggestions_label)
            return
        
        # Add suggestion widgets
        self.suggestions = self.analysis.suggestions
        for suggestion in self.suggestions:
            suggestion_widget = SuggestionWidget(suggestion)
            suggestion_widget.suggestion_applied.connect(self.apply_suggestion)
            suggestion_widget.suggestion_rated.connect(self.rate_suggestion)
            self.suggestions_layout.insertWidget(self.suggestions_layout.count() - 1, suggestion_widget)
        
        # Update tab title with count
        self.tab_widget.setTabText(1, f"Suggestions ({len(self.suggestions)})")
    
    def filter_suggestions(self, filter_type: str):
        """Filter suggestions by type"""
        if not self.analysis:
            return
        
        # Clear existing suggestions
        for i in reversed(range(self.suggestions_layout.count() - 1)):
            child = self.suggestions_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        # Filter suggestions
        if filter_type == "All":
            filtered_suggestions = self.analysis.suggestions
        else:
            filtered_suggestions = [
                s for s in self.analysis.suggestions 
                if s.suggestion_type.lower() == filter_type.lower()
            ]
        
        # Add filtered suggestion widgets
        for suggestion in filtered_suggestions:
            suggestion_widget = SuggestionWidget(suggestion)
            suggestion_widget.suggestion_applied.connect(self.apply_suggestion)
            suggestion_widget.suggestion_rated.connect(self.rate_suggestion)
            self.suggestions_layout.insertWidget(self.suggestions_layout.count() - 1, suggestion_widget)
        
        # Update status
        if not filtered_suggestions:
            no_suggestions_label = QLabel(f"No {filter_type.lower()} suggestions available")
            no_suggestions_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_suggestions_label.setStyleSheet("color: gray; font-style: italic; padding: 20px;")
            self.suggestions_layout.insertWidget(0, no_suggestions_label)
    
    @pyqtSlot(str)
    def apply_suggestion(self, suggestion_id: str):
        """Apply a suggestion"""
        if self.ai_service.apply_suggestion(suggestion_id):
            self.status_label.setText("Suggestion applied successfully")
        else:
            QMessageBox.warning(self, "Error", "Failed to apply suggestion")
    
    @pyqtSlot(str, int)
    def rate_suggestion(self, suggestion_id: str, rating: int):
        """Rate a suggestion"""
        if self.ai_service.rate_suggestion(suggestion_id, rating):
            self.status_label.setText(f"Suggestion rated {rating} stars")
        else:
            QMessageBox.warning(self, "Error", "Failed to rate suggestion")


class AISuggestionStatsDialog(QDialog):
    """Dialog for viewing AI suggestion statistics"""
    
    def __init__(self, ai_service: AISuggestionService, parent=None):
        super().__init__(parent)
        self.ai_service = ai_service
        
        self.setWindowTitle("AI Suggestion Statistics")
        self.setModal(True)
        self.resize(600, 400)
        
        self.setup_ui()
        self.load_statistics()
    
    def setup_ui(self):
        """Setup the statistics dialog UI"""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("AI Suggestion Statistics")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Statistics table
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(2)
        self.stats_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.stats_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.stats_table)
        
        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)
    
    def load_statistics(self):
        """Load and display statistics"""
        try:
            stats = self.ai_service.get_suggestion_statistics()
            
            # Prepare data for table
            data = [
                ("Total Suggestions", str(stats.get('total_suggestions', 0))),
                ("Applied Suggestions", str(stats.get('applied_suggestions', 0))),
                ("Average Rating", f"{stats.get('average_rating', 0):.1f} stars" if stats.get('average_rating') else "No ratings"),
            ]
            
            # Add suggestion types
            by_type = stats.get('by_type', {})
            for suggestion_type, count in by_type.items():
                data.append((f"{suggestion_type.title()} Suggestions", str(count)))
            
            # Add categories
            by_category = stats.get('by_category', {})
            for category, count in by_category.items():
                data.append((f"{category} Category", str(count)))
            
            # Populate table
            self.stats_table.setRowCount(len(data))
            for row, (metric, value) in enumerate(data):
                self.stats_table.setItem(row, 0, QTableWidgetItem(metric))
                self.stats_table.setItem(row, 1, QTableWidgetItem(value))
            
            self.stats_table.resizeColumnsToContents()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load statistics: {str(e)}")


class AIPromptGeneratorDialog(QDialog):
    """Dialog for generating complete prompts from short descriptions"""
    
    def __init__(self, ai_service: AISuggestionService, parent=None):
        super().__init__(parent)
        self.ai_service = ai_service
        self.generated_prompt = ""
        
        self.setWindowTitle("AI Prompt Generator")
        self.setModal(True)
        self.resize(800, 600)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the generator dialog UI"""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("AI Prompt Generator")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel("Describe what you want your prompt to accomplish:")
        desc_label.setStyleSheet("color: #666; margin: 10px 0;")
        layout.addWidget(desc_label)
        
        # Input section
        input_group = QGroupBox("Your Description")
        input_layout = QVBoxLayout(input_group)
        
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText(
            "Example: Create a prompt that helps me write professional emails to clients, "
            "including proper greetings, clear purpose, and professional closing..."
        )
        self.description_edit.setMaximumHeight(120)
        input_layout.addWidget(self.description_edit)
        
        # Options
        options_layout = QHBoxLayout()
        
        # Prompt type
        type_label = QLabel("Prompt Type:")
        options_layout.addWidget(type_label)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "General Purpose",
            "Creative Writing",
            "Business Communication",
            "Technical Documentation",
            "Educational Content",
            "Data Analysis",
            "Code Generation",
            "Problem Solving"
        ])
        options_layout.addWidget(self.type_combo)
        
        options_layout.addStretch()
        
        # Length preference
        length_label = QLabel("Length:")
        options_layout.addWidget(length_label)
        
        self.length_combo = QComboBox()
        self.length_combo.addItems(["Short", "Medium", "Detailed"])
        self.length_combo.setCurrentText("Medium")
        options_layout.addWidget(self.length_combo)
        
        input_layout.addLayout(options_layout)
        
        # Generate button
        self.generate_btn = QPushButton("Generate Prompt")
        self.generate_btn.clicked.connect(self.generate_prompt)
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                font-size: 12pt;
                font-weight: bold;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        input_layout.addWidget(self.generate_btn)
        
        layout.addWidget(input_group)
        
        # Output section
        output_group = QGroupBox("Generated Prompt")
        output_layout = QVBoxLayout(output_group)
        
        self.output_edit = QTextEdit()
        self.output_edit.setPlaceholderText("Your generated prompt will appear here...")
        self.output_edit.setReadOnly(True)
        output_layout.addWidget(self.output_edit)
        
        # Preview actions
        preview_layout = QHBoxLayout()
        
        self.copy_btn = QPushButton("Copy to Clipboard")
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        self.copy_btn.setEnabled(False)
        preview_layout.addWidget(self.copy_btn)
        
        self.regenerate_btn = QPushButton("Regenerate")
        self.regenerate_btn.clicked.connect(self.regenerate_prompt)
        self.regenerate_btn.setEnabled(False)
        preview_layout.addWidget(self.regenerate_btn)
        
        preview_layout.addStretch()
        
        # Quality indicator
        self.quality_label = QLabel("")
        self.quality_label.setStyleSheet("font-weight: bold;")
        preview_layout.addWidget(self.quality_label)
        
        output_layout.addLayout(preview_layout)
        
        layout.addWidget(output_group)
        
        # Dialog buttons
        buttons_layout = QHBoxLayout()
        
        self.use_prompt_btn = QPushButton("Use This Prompt")
        self.use_prompt_btn.clicked.connect(self.accept)
        self.use_prompt_btn.setEnabled(False)
        self.use_prompt_btn.setStyleSheet("""
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
        buttons_layout.addWidget(self.use_prompt_btn)
        
        buttons_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)
        
        # Status label
        self.status_label = QLabel("Enter a description and click 'Generate Prompt' to begin")
        self.status_label.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(self.status_label)
    
    def generate_prompt(self):
        """Generate a prompt from the user's description"""
        description = self.description_edit.toPlainText().strip()
        
        if not description:
            QMessageBox.warning(self, "Input Required", "Please enter a description of what you want your prompt to accomplish.")
            return
        
        # Disable UI during generation
        self.generate_btn.setEnabled(False)
        self.generate_btn.setText("Generating...")
        self.status_label.setText("Generating prompt... This may take a moment.")
        
        try:
            # Get generation parameters
            prompt_type = self.type_combo.currentText()
            length = self.length_combo.currentText()
            
            # Generate the prompt using AI service
            self.generated_prompt = self.ai_service.generate_prompt_from_description(
                description=description,
                prompt_type=prompt_type,
                length_preference=length
            )
            
            if self.generated_prompt:
                self.output_edit.setPlainText(self.generated_prompt)
                self.copy_btn.setEnabled(True)
                self.regenerate_btn.setEnabled(True)
                self.use_prompt_btn.setEnabled(True)
                
                # Analyze quality
                quality_score = self._estimate_quality(self.generated_prompt)
                self._update_quality_indicator(quality_score)
                
                self.status_label.setText("Prompt generated successfully!")
            else:
                QMessageBox.warning(self, "Generation Failed", "Failed to generate prompt. Please try again.")
                self.status_label.setText("Generation failed. Please try again.")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error generating prompt: {str(e)}")
            self.status_label.setText("Error occurred during generation.")
        
        finally:
            self.generate_btn.setEnabled(True)
            self.generate_btn.setText("Generate Prompt")
    
    def regenerate_prompt(self):
        """Regenerate the prompt with the same parameters"""
        reply = QMessageBox.question(
            self,
            "Regenerate Prompt",
            "This will create a new version of the prompt. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.generate_prompt()
    
    def copy_to_clipboard(self):
        """Copy the generated prompt to clipboard"""
        if self.generated_prompt:
            clipboard = QApplication.clipboard()
            clipboard.setText(self.generated_prompt)
            self.status_label.setText("Prompt copied to clipboard!")
            
            # Temporarily change button text
            original_text = self.copy_btn.text()
            self.copy_btn.setText("Copied!")
            QTimer.singleShot(2000, lambda: self.copy_btn.setText(original_text))
    
    def get_generated_prompt(self) -> str:
        """Get the generated prompt content"""
        return self.generated_prompt
    
    def _estimate_quality(self, prompt: str) -> float:
        """Estimate the quality of the generated prompt"""
        # Simple quality estimation based on length and structure
        score = 0.5  # Base score
        
        # Length factor
        word_count = len(prompt.split())
        if 20 <= word_count <= 200:
            score += 0.2
        elif word_count > 200:
            score += 0.1
        
        # Structure indicators
        if any(indicator in prompt.lower() for indicator in ['please', 'create', 'generate', 'write']):
            score += 0.1
        
        if any(indicator in prompt.lower() for indicator in ['format', 'style', 'tone', 'length']):
            score += 0.1
        
        if any(indicator in prompt.lower() for indicator in ['example', 'include', 'ensure', 'make sure']):
            score += 0.1
        
        return min(score, 1.0)
    
    def _update_quality_indicator(self, score: float):
        """Update the quality indicator based on score"""
        if score >= 0.8:
            self.quality_label.setText("Quality: Excellent ⭐⭐⭐⭐⭐")
            self.quality_label.setStyleSheet("color: green; font-weight: bold;")
        elif score >= 0.6:
            self.quality_label.setText("Quality: Good ⭐⭐⭐⭐")
            self.quality_label.setStyleSheet("color: orange; font-weight: bold;")
        elif score >= 0.4:
            self.quality_label.setText("Quality: Fair ⭐⭐⭐")
            self.quality_label.setStyleSheet("color: #ff9800; font-weight: bold;")
        else:
            self.quality_label.setText("Quality: Needs Improvement ⭐⭐")
            self.quality_label.setStyleSheet("color: red; font-weight: bold;")


# Test the dialog
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Mock data for testing
    from services.ai_suggestion_service import PromptSuggestion, PromptAnalysis
    
    # Create mock suggestions
    suggestions = [
        PromptSuggestion(
            suggestion_id="test1",
            prompt_id=1,
            suggestion_type="improvement",
            title="Add Clear Objective",
            content="Consider starting your prompt with a clear statement...",
            reasoning="Adding a clear objective helps the AI understand exactly what you want.",
            confidence=0.85,
            category="Improvement",
            tags=["clarity", "objective"],
            created_at=datetime.now()
        ),
        PromptSuggestion(
            suggestion_id="test2",
            prompt_id=1,
            suggestion_type="alternative",
            title="Alternative Structure",
            content="Here's an alternative way to structure your prompt...",
            reasoning="This structure may improve response quality.",
            confidence=0.72,
            category="Alternative",
            tags=["structure", "alternative"],
            created_at=datetime.now()
        )
    ]
    
    # Create mock analysis
    analysis = PromptAnalysis(
        prompt_id=1,
        clarity_score=0.75,
        specificity_score=0.60,
        completeness_score=0.80,
        overall_score=0.72,
        strengths=["Well-structured", "Clear language"],
        weaknesses=["Lacks specific details", "No output format"],
        suggestions=suggestions,
        analyzed_at=datetime.now()
    )
    
    # Test analysis widget
    analysis_widget = PromptAnalysisWidget()
    analysis_widget.set_analysis(analysis)
    analysis_widget.show()
    
    sys.exit(app.exec_())