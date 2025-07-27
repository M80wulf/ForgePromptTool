"""
Test script for batch operations functionality
"""

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ui.main_window import MainWindow
from models.database import DatabaseManager


def create_test_data():
    """Create test data for batch operations testing"""
    db = DatabaseManager("test_batch_operations.db")
    
    # Create test folders
    folder1_id = db.create_folder("Test Folder 1")
    folder2_id = db.create_folder("Test Folder 2")
    
    # Create test tags
    tag1_id = db.create_tag("AI", "#007bff")
    tag2_id = db.create_tag("Coding", "#28a745")
    tag3_id = db.create_tag("Writing", "#dc3545")
    
    # Create test prompts
    prompts_data = [
        {
            "title": "AI Assistant Prompt",
            "content": "You are a helpful AI assistant. Please provide clear and concise answers.",
            "folder_id": folder1_id,
            "is_favorite": True,
            "is_template": False,
            "tags": [tag1_id]
        },
        {
            "title": "Code Review Prompt",
            "content": "Please review this code and provide suggestions for improvement.",
            "folder_id": folder1_id,
            "is_favorite": False,
            "is_template": True,
            "tags": [tag1_id, tag2_id]
        },
        {
            "title": "Creative Writing Prompt",
            "content": "Write a short story about a time traveler who gets stuck in the past.",
            "folder_id": folder2_id,
            "is_favorite": True,
            "is_template": False,
            "tags": [tag3_id]
        },
        {
            "title": "Technical Documentation",
            "content": "Create comprehensive documentation for this API endpoint.",
            "folder_id": folder2_id,
            "is_favorite": False,
            "is_template": True,
            "tags": [tag2_id, tag3_id]
        },
        {
            "title": "Data Analysis Prompt",
            "content": "Analyze this dataset and provide insights on trends and patterns.",
            "folder_id": None,  # Root folder
            "is_favorite": True,
            "is_template": False,
            "tags": [tag1_id, tag2_id]
        },
        {
            "title": "Email Template",
            "content": "Draft a professional email for client communication.",
            "folder_id": None,  # Root folder
            "is_favorite": False,
            "is_template": True,
            "tags": [tag3_id]
        }
    ]
    
    # Create prompts and add tags
    for prompt_data in prompts_data:
        tags = prompt_data.pop('tags', [])
        prompt_id = db.create_prompt(**prompt_data)
        
        for tag_id in tags:
            db.add_tag_to_prompt(prompt_id, tag_id)
    
    print(f"Created test database with {len(prompts_data)} prompts")
    return db


def test_batch_operations():
    """Test the batch operations functionality"""
    print("Testing Batch Operations Functionality")
    print("=" * 50)
    
    # Create test data
    db = create_test_data()
    
    # Create and show the application
    app = QApplication(sys.argv)
    
    # Override the database path in the main window
    window = MainWindow()
    window.db = db  # Use our test database
    
    # Refresh the UI with test data
    window.refresh_all()
    
    print("\nTest Instructions:")
    print("1. Select multiple prompts using Ctrl+Click or Shift+Click")
    print("2. Notice the batch operations panel appears when multiple items are selected")
    print("3. Try the following batch operations:")
    print("   - Right-click for context menu with batch options")
    print("   - Use Edit > Batch Operations menu")
    print("   - Use keyboard shortcuts:")
    print("     * Ctrl+A: Select all prompts")
    print("     * Ctrl+I: Invert selection")
    print("     * Escape: Clear selection")
    print("     * Ctrl+B: Open batch operations dialog")
    print("     * Ctrl+Shift+C: Copy all selected")
    print("     * Ctrl+Shift+Delete: Delete all selected")
    print("4. Test batch operations:")
    print("   - Batch tag management (add/remove tags)")
    print("   - Batch move to folder")
    print("   - Batch export (JSON, text files)")
    print("   - Batch copy to clipboard")
    print("   - Batch duplicate")
    print("   - Batch favorite/unfavorite")
    print("   - Batch delete")
    
    window.show()
    
    # Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    test_batch_operations()