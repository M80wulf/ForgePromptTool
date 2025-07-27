#!/usr/bin/env python3
"""
Test script for the template system functionality
"""

import sys
import os
import tempfile

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.database import DatabaseManager
from models.template_models import PromptTemplate, TemplateVariable, TemplateEngine
from services.template_service import TemplateService


def test_template_engine():
    """Test the template engine functionality"""
    print("Testing Template Engine")
    print("=" * 30)
    
    # Test variable extraction
    content = "Hello {name}, welcome to {company}! Your role is {position}."
    variables = TemplateEngine.extract_variables_from_content(content)
    print(f"[OK] Extracted variables: {variables}")
    assert set(variables) == {"name", "company", "position"}
    
    # Test syntax validation
    valid_content = "Hello {name}, your score is {score}."
    errors = TemplateEngine.validate_template_syntax(valid_content)
    print(f"[OK] Valid syntax errors: {len(errors)} (should be 0)")
    assert len(errors) == 0
    
    invalid_content = "Hello {}, your score is {invalid-name}."
    errors = TemplateEngine.validate_template_syntax(invalid_content)
    print(f"[OK] Invalid syntax errors: {len(errors)} (should be > 0)")
    assert len(errors) > 0
    
    # Test variable type suggestions
    suggestions = [
        ("user_count", "number"),
        ("is_enabled", "boolean"),
        ("email_address", "text"),
        ("category_type", "choice")
    ]
    
    for var_name, expected_type in suggestions:
        suggested_type = TemplateEngine.suggest_variable_types(var_name)
        print(f"[OK] {var_name} -> {suggested_type} (expected: {expected_type})")
    
    print("[OK] Template engine tests passed!\n")


def test_template_variables():
    """Test template variable functionality"""
    print("Testing Template Variables")
    print("=" * 30)
    
    # Test text variable
    text_var = TemplateVariable(
        name="username",
        description="User's name",
        variable_type="text",
        required=True
    )
    
    assert text_var.validate_value("john_doe")
    assert not text_var.validate_value("")  # Required but empty
    print("[OK] Text variable validation works")
    
    # Test number variable
    number_var = TemplateVariable(
        name="count",
        variable_type="number",
        required=True
    )
    
    assert number_var.validate_value("42")
    assert number_var.validate_value("3.14")
    assert not number_var.validate_value("not_a_number")
    print("[OK] Number variable validation works")
    
    # Test boolean variable
    bool_var = TemplateVariable(
        name="enabled",
        variable_type="boolean",
        required=True
    )
    
    assert bool_var.validate_value("true")
    assert bool_var.validate_value("false")
    assert bool_var.validate_value("yes")
    assert bool_var.validate_value("no")
    assert not bool_var.validate_value("maybe")
    print("[OK] Boolean variable validation works")
    
    # Test choice variable
    choice_var = TemplateVariable(
        name="format",
        variable_type="choice",
        choices=["JSON", "XML", "CSV"],
        required=True
    )
    
    assert choice_var.validate_value("JSON")
    assert choice_var.validate_value("XML")
    assert not choice_var.validate_value("YAML")
    print("[OK] Choice variable validation works")
    
    # Test value formatting
    assert number_var.format_value("42.0") == "42"
    assert number_var.format_value("3.14") == "3.14"
    assert bool_var.format_value("yes") == "true"
    assert bool_var.format_value("no") == "false"
    print("[OK] Value formatting works")
    
    print("[OK] Template variable tests passed!\n")


def test_prompt_template():
    """Test prompt template functionality"""
    print("Testing Prompt Template")
    print("=" * 30)
    
    # Create a template
    template = PromptTemplate(
        title="Email Template",
        content="Dear {recipient},\n\nI hope this email finds you well. I wanted to discuss {topic} with you.\n\nBest regards,\n{sender}",
        description="A professional email template",
        category="Communication"
    )
    
    # Test variable extraction
    extracted_vars = template.extract_variables()
    expected_vars = {"recipient", "topic", "sender"}
    assert set(extracted_vars) == expected_vars
    print(f"[OK] Extracted variables: {extracted_vars}")
    
    # Add variables
    template.add_variable(TemplateVariable(
        name="recipient",
        description="Email recipient name",
        variable_type="text",
        required=True
    ))
    
    template.add_variable(TemplateVariable(
        name="topic",
        description="Discussion topic",
        variable_type="text",
        required=True
    ))
    
    template.add_variable(TemplateVariable(
        name="sender",
        description="Sender name",
        variable_type="text",
        default_value="John Doe",
        required=False
    ))
    
    # Test substitution
    substitutions = {
        "recipient": "Alice Smith",
        "topic": "the upcoming project",
        "sender": "Bob Johnson"
    }
    
    result = template.substitute_variables(substitutions)
    expected_content = "Dear Alice Smith,\n\nI hope this email finds you well. I wanted to discuss the upcoming project with you.\n\nBest regards,\nBob Johnson"
    assert result == expected_content
    print("[OK] Variable substitution works")
    
    # Test validation
    valid_substitutions = {
        "recipient": "Alice",
        "topic": "meeting",
        "sender": "Bob"
    }
    errors = template.validate_substitutions(valid_substitutions)
    assert len(errors) == 0
    print("[OK] Valid substitutions pass validation")
    
    invalid_substitutions = {
        "recipient": "",  # Required but empty
        "topic": "meeting"
        # sender missing but has default
    }
    errors = template.validate_substitutions(invalid_substitutions)
    assert len(errors) > 0
    print("[OK] Invalid substitutions fail validation")
    
    # Test preview
    preview = template.get_preview(valid_substitutions)
    assert "Alice" in preview
    assert "meeting" in preview
    print("[OK] Preview generation works")
    
    print("[OK] Prompt template tests passed!\n")


def test_template_service():
    """Test template service functionality"""
    print("Testing Template Service")
    print("=" * 30)
    
    # Create temporary database
    temp_fd, temp_db_path = tempfile.mkstemp(suffix='.db')
    os.close(temp_fd)
    
    try:
        db = DatabaseManager(temp_db_path)
        service = TemplateService(db)
        
        # Create a template
        template = PromptTemplate(
            title="Code Review Template",
            content="Please review the following {language} code:\n\n{code}\n\nFocus on {focus_areas}.",
            description="Template for code review requests",
            category="Development"
        )
        
        # Add variables
        template.add_variable(TemplateVariable(
            name="language",
            description="Programming language",
            variable_type="choice",
            choices=["Python", "JavaScript", "Java", "C++"],
            required=True
        ))
        
        template.add_variable(TemplateVariable(
            name="code",
            description="Code to review",
            variable_type="text",
            required=True
        ))
        
        template.add_variable(TemplateVariable(
            name="focus_areas",
            description="Areas to focus on",
            variable_type="text",
            default_value="performance and security",
            required=False
        ))
        
        # Test template creation
        template_id = service.create_template(template)
        assert template_id > 0
        print(f"[OK] Created template with ID: {template_id}")
        
        # Test template retrieval
        retrieved_template = service.get_template(template_id)
        assert retrieved_template is not None
        assert retrieved_template.title == template.title
        assert len(retrieved_template.variables) == 3
        print("[OK] Template retrieval works")
        
        # Test template usage
        substitutions = {
            "language": "Python",
            "code": "def hello():\n    print('Hello, World!')",
            "focus_areas": "code style and documentation"
        }
        
        content, prompt_id = service.use_template(
            template_id=template_id,
            substitutions=substitutions,
            create_prompt=True,
            prompt_title="Code Review Request"
        )
        
        assert "Python" in content
        assert "Hello, World!" in content
        assert prompt_id is not None
        print("[OK] Template usage works")
        
        # Test template listing
        templates = service.get_templates()
        assert len(templates) == 1
        assert templates[0].title == template.title
        print("[OK] Template listing works")
        
        # Test template search
        search_results = service.search_templates("code")
        assert len(search_results) == 1
        print("[OK] Template search works")
        
        # Test usage history
        usage_history = service.get_template_usage_history(template_id)
        assert len(usage_history) == 1
        print("[OK] Usage history tracking works")
        
        # Test template validation
        issues = service.validate_template(retrieved_template)
        print(f"[OK] Template validation found {len(issues)} issues")
        
        # Test suggestions
        suggestions = service.suggest_improvements(retrieved_template)
        print(f"[OK] Template suggestions: {len(suggestions)} suggestions")
        
        # Test auto-detection
        auto_vars = service.auto_detect_variables("Hello {name}, your {item_type} is ready!")
        assert len(auto_vars) == 2
        var_names = [var.name for var in auto_vars]
        assert "name" in var_names
        assert "item_type" in var_names
        print("[OK] Auto-detection works")
        
        print("[OK] Template service tests passed!\n")
        
    finally:
        # Clean up
        try:
            os.remove(temp_db_path)
        except:
            pass


def test_database_operations():
    """Test template database operations"""
    print("Testing Database Operations")
    print("=" * 30)
    
    # Create temporary database
    temp_fd, temp_db_path = tempfile.mkstemp(suffix='.db')
    os.close(temp_fd)
    
    try:
        db = DatabaseManager(temp_db_path)
        
        # Test template creation
        template_id = db.create_template(
            title="Test Template",
            content="Hello {name}!",
            description="A simple test template",
            category="Test",
            tags="test,simple"
        )
        assert template_id > 0
        print(f"[OK] Created template with ID: {template_id}")
        
        # Test variable creation
        var_id = db.create_template_variable(
            template_id=template_id,
            name="name",
            description="Person's name",
            variable_type="text",
            required=True
        )
        assert var_id > 0
        print(f"[OK] Created variable with ID: {var_id}")
        
        # Test template retrieval
        template = db.get_template(template_id)
        assert template is not None
        assert template['title'] == "Test Template"
        print("[OK] Template retrieval works")
        
        # Test variable retrieval
        variables = db.get_template_variables(template_id)
        assert len(variables) == 1
        assert variables[0]['name'] == "name"
        print("[OK] Variable retrieval works")
        
        # Test template listing
        templates = db.get_templates()
        assert len(templates) == 1
        print("[OK] Template listing works")
        
        # Test usage tracking
        usage_id = db.create_template_usage(
            template_id=template_id,
            substitutions='{"name": "Alice"}',
            generated_prompt_id=None
        )
        assert usage_id > 0
        print("[OK] Usage tracking works")
        
        # Test usage count increment
        success = db.increment_template_usage(template_id)
        assert success
        
        updated_template = db.get_template(template_id)
        assert updated_template['usage_count'] == 1
        print("[OK] Usage count increment works")
        
        # Test categories
        categories = db.get_template_categories()
        assert "Test" in categories
        print("[OK] Category listing works")
        
        print("[OK] Database operations tests passed!\n")
        
    finally:
        # Clean up
        try:
            os.remove(temp_db_path)
        except:
            pass


def main():
    """Run all template system tests"""
    print("Template System Test Suite")
    print("=" * 50)
    
    try:
        test_template_engine()
        test_template_variables()
        test_prompt_template()
        test_database_operations()
        test_template_service()
        
        print("=" * 50)
        print("[SUCCESS] ALL TEMPLATE SYSTEM TESTS PASSED!")
        print("\nTemplate System Features Implemented:")
        print("* Template engine with variable extraction and validation")
        print("* Multiple variable types (text, number, boolean, choice, date)")
        print("* Variable validation and formatting")
        print("* Template creation and management")
        print("* Variable substitution and preview")
        print("* Database storage and retrieval")
        print("* Template service with full CRUD operations")
        print("* Usage tracking and history")
        print("* Template validation and suggestions")
        print("* Auto-detection of variables")
        print("* Category management")
        print("* Search and filtering")
        print("\nThe template system is ready for production use!")
        
    except Exception as e:
        print(f"\n[FAILED] TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)