#!/usr/bin/env python3
"""
Test script for advanced search functionality
"""

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.database import DatabaseManager
from models.search_models import AdvancedSearchEngine

def test_advanced_search():
    """Test the advanced search functionality"""
    print("Testing Advanced Search Functionality")
    print("=" * 50)
    
    # Initialize database and search engine
    db = DatabaseManager()
    search_engine = AdvancedSearchEngine(db)
    
    # Create some test data (force creation for testing)
    print("Creating test data...")
    
    # Create test folders
    folder1_id = db.create_folder("AI Prompts", None)
    folder2_id = db.create_folder("Code Prompts", None)
    
    # Create test tags
    tag1_id = db.create_tag("python", "#007bff")
    tag2_id = db.create_tag("ai", "#28a745")
    tag3_id = db.create_tag("coding", "#dc3545")
    
    # Create test prompts
    prompt1_id = db.create_prompt(
        title="Python Code Generator",
        content="Write a Python function that generates clean, efficient code for the given task.",
        folder_id=folder2_id,
        is_favorite=True
    )
    
    prompt2_id = db.create_prompt(
        title="AI Assistant Prompt",
        content="You are a helpful AI assistant. Please provide accurate and detailed responses.",
        folder_id=folder1_id,
        is_template=True
    )
    
    prompt3_id = db.create_prompt(
        title="Regex Pattern Helper",
        content="Create a regex pattern that matches email addresses with proper validation.",
        folder_id=folder2_id
    )
    
    # Add tags to prompts
    db.add_tag_to_prompt(prompt1_id, tag1_id)
    db.add_tag_to_prompt(prompt1_id, tag3_id)
    db.add_tag_to_prompt(prompt2_id, tag2_id)
    db.add_tag_to_prompt(prompt3_id, tag1_id)
    
    print("Test data created successfully!")
    
    # Test basic search
    print("\n1. Testing basic search:")
    results = search_engine.search("python")
    print(f"   Search 'python': {len(results)} results")
    for result in results:
        print(f"   - {result.title}")
    
    # Test field-specific search
    print("\n2. Testing field-specific search:")
    results = search_engine.search("title:Python")
    print(f"   Search 'title:Python': {len(results)} results")
    for result in results:
        print(f"   - {result.title}")
    
    # Test boolean operators
    print("\n3. Testing boolean operators:")
    results = search_engine.search("python AND code")
    print(f"   Search 'python AND code': {len(results)} results")
    for result in results:
        print(f"   - {result.title}")
    
    # Test regex search
    print("\n4. Testing regex search:")
    results = search_engine.search("regex:/[Pp]ython/")
    print(f"   Search 'regex:/[Pp]ython/': {len(results)} results")
    for result in results:
        print(f"   - {result.title}")
    
    # Test quoted strings
    print("\n5. Testing quoted strings:")
    results = search_engine.search('"AI assistant"')
    print(f"   Search '\"AI assistant\"': {len(results)} results")
    for result in results:
        print(f"   - {result.title}")
    
    # Test negation
    print("\n6. Testing negation:")
    results = search_engine.search("code NOT regex")
    print(f"   Search 'code NOT regex': {len(results)} results")
    for result in results:
        print(f"   - {result.title}")
    
    # Test tag search
    print("\n7. Testing tag search:")
    results = search_engine.search("tags:python")
    print(f"   Search 'tags:python': {len(results)} results")
    for result in results:
        print(f"   - {result.title} (tags: {result.tags})")
    
    print("\n" + "=" * 50)
    print("Advanced search testing completed!")

if __name__ == "__main__":
    test_advanced_search()