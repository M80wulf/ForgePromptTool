"""
Template service for the Prompt Organizer application
"""

from typing import List, Dict, Optional, Tuple
import json
from datetime import datetime

from models.database import DatabaseManager
from models.template_models import (
    PromptTemplate, TemplateVariable, TemplateUsage, TemplateCategory,
    TemplateEngine, DEFAULT_CATEGORIES
)


class TemplateService:
    """Service for managing prompt templates"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.engine = TemplateEngine()
    
    # Template CRUD operations
    def create_template(self, template: PromptTemplate) -> int:
        """Create a new template"""
        # Validate template syntax
        errors = self.engine.validate_template_syntax(template.content)
        if errors:
            raise ValueError(f"Template syntax errors: {'; '.join(errors)}")
        
        # Create template record
        tags_str = ','.join(template.tags) if template.tags else ''
        template_id = self.db.create_template(
            title=template.title,
            content=template.content,
            description=template.description,
            category=template.category,
            tags=tags_str
        )
        
        # Create variables
        for variable in template.variables:
            choices_str = ','.join(variable.choices) if variable.choices else ''
            self.db.create_template_variable(
                template_id=template_id,
                name=variable.name,
                description=variable.description,
                default_value=variable.default_value,
                variable_type=variable.variable_type,
                choices=choices_str,
                required=variable.required,
                validation_pattern=variable.validation_pattern or ''
            )
        
        return template_id
    
    def get_template(self, template_id: int) -> Optional[PromptTemplate]:
        """Get a template by ID"""
        template_data = self.db.get_template(template_id)
        if not template_data:
            return None
        
        # Get variables
        variables_data = self.db.get_template_variables(template_id)
        variables = []
        
        for var_data in variables_data:
            choices = var_data['choices'].split(',') if var_data['choices'] else []
            variable = TemplateVariable(
                name=var_data['name'],
                description=var_data['description'],
                default_value=var_data['default_value'],
                variable_type=var_data['variable_type'],
                choices=choices,
                required=bool(var_data['required']),
                validation_pattern=var_data['validation_pattern']
            )
            variables.append(variable)
        
        # Parse tags
        tags = template_data['tags'].split(',') if template_data['tags'] else []
        
        return PromptTemplate(
            id=template_data['id'],
            title=template_data['title'],
            content=template_data['content'],
            description=template_data['description'],
            variables=variables,
            category=template_data['category'],
            tags=tags,
            created_at=datetime.fromisoformat(template_data['created_at']) if template_data['created_at'] else None,
            updated_at=datetime.fromisoformat(template_data['updated_at']) if template_data['updated_at'] else None,
            usage_count=template_data['usage_count']
        )
    
    def get_templates(self, category: str = None, search_term: str = "") -> List[PromptTemplate]:
        """Get templates with optional filtering"""
        templates_data = self.db.get_templates(category=category, search_term=search_term)
        templates = []
        
        for template_data in templates_data:
            template = self.get_template(template_data['id'])
            if template:
                templates.append(template)
        
        return templates
    
    def update_template(self, template: PromptTemplate) -> bool:
        """Update an existing template"""
        if not template.id:
            return False
        
        # Validate template syntax
        errors = self.engine.validate_template_syntax(template.content)
        if errors:
            raise ValueError(f"Template syntax errors: {'; '.join(errors)}")
        
        # Update template record
        tags_str = ','.join(template.tags) if template.tags else ''
        success = self.db.update_template(
            template_id=template.id,
            title=template.title,
            content=template.content,
            description=template.description,
            category=template.category,
            tags=tags_str
        )
        
        if success:
            # Update variables - delete all and recreate
            self.db.delete_template_variables(template.id)
            
            for variable in template.variables:
                choices_str = ','.join(variable.choices) if variable.choices else ''
                self.db.create_template_variable(
                    template_id=template.id,
                    name=variable.name,
                    description=variable.description,
                    default_value=variable.default_value,
                    variable_type=variable.variable_type,
                    choices=choices_str,
                    required=variable.required,
                    validation_pattern=variable.validation_pattern or ''
                )
        
        return success
    
    def delete_template(self, template_id: int) -> bool:
        """Delete a template"""
        return self.db.delete_template(template_id)
    
    # Template usage operations
    def use_template(self, template_id: int, substitutions: Dict[str, str],
                    create_prompt: bool = True, prompt_title: str = None,
                    folder_id: int = None) -> Tuple[str, Optional[int]]:
        """Use a template with substitutions"""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        # Validate substitutions
        errors = template.validate_substitutions(substitutions)
        if errors:
            error_messages = [f"{field}: {message}" for field, message in errors.items()]
            raise ValueError(f"Validation errors: {'; '.join(error_messages)}")
        
        # Generate content
        generated_content = template.substitute_variables(substitutions)
        
        # Create prompt if requested
        prompt_id = None
        if create_prompt:
            if not prompt_title:
                prompt_title = f"{template.title} - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            prompt_id = self.db.create_prompt(
                title=prompt_title,
                content=generated_content,
                folder_id=folder_id,
                is_template=False
            )
        
        # Record usage
        substitutions_json = json.dumps(substitutions)
        self.db.create_template_usage(
            template_id=template_id,
            substitutions=substitutions_json,
            generated_prompt_id=prompt_id
        )
        
        # Increment usage count
        self.db.increment_template_usage(template_id)
        
        return generated_content, prompt_id
    
    def get_template_usage_history(self, template_id: int) -> List[TemplateUsage]:
        """Get usage history for a template"""
        usage_data = self.db.get_template_usage_history(template_id)
        usage_list = []
        
        for usage in usage_data:
            usage_obj = TemplateUsage.from_json(
                template_id=usage['template_id'],
                json_str=usage['substitutions'],
                id=usage['id'],
                generated_prompt_id=usage['generated_prompt_id'],
                created_at=datetime.fromisoformat(usage['created_at']) if usage['created_at'] else None
            )
            usage_list.append(usage_obj)
        
        return usage_list
    
    # Template creation helpers
    def create_template_from_prompt(self, prompt_id: int, template_title: str = None,
                                   template_description: str = "", category: str = "General") -> int:
        """Create a template from an existing prompt"""
        prompt = self.db.get_prompt(prompt_id)
        if not prompt:
            raise ValueError(f"Prompt {prompt_id} not found")
        
        title = template_title or f"{prompt['title']} Template"
        
        # Create template using engine
        template = self.engine.create_template_from_prompt(
            title=title,
            content=prompt['content'],
            description=template_description
        )
        template.category = category
        
        return self.create_template(template)
    
    def auto_detect_variables(self, content: str) -> List[TemplateVariable]:
        """Auto-detect variables from content and suggest configurations"""
        variable_names = self.engine.extract_variables_from_content(content)
        variables = []
        
        for name in variable_names:
            variable = TemplateVariable(
                name=name,
                description=self.engine.generate_variable_description(name),
                variable_type=self.engine.suggest_variable_types(name),
                required=True
            )
            
            # Add some common choices for certain variable types
            if variable.variable_type == "choice":
                if "format" in name.lower():
                    variable.choices = ["JSON", "XML", "CSV", "Plain Text"]
                elif "style" in name.lower():
                    variable.choices = ["Formal", "Casual", "Technical", "Creative"]
                elif "language" in name.lower():
                    variable.choices = ["English", "Spanish", "French", "German", "Chinese"]
            
            variables.append(variable)
        
        return variables
    
    # Category operations
    def get_categories(self) -> List[TemplateCategory]:
        """Get all template categories"""
        db_categories = self.db.get_template_categories()
        
        # Combine default categories with custom ones from database
        all_categories = {cat.name: cat for cat in DEFAULT_CATEGORIES}
        
        for cat_name in db_categories:
            if cat_name not in all_categories:
                all_categories[cat_name] = TemplateCategory(cat_name)
        
        return list(all_categories.values())
    
    def get_popular_templates(self, limit: int = 10) -> List[PromptTemplate]:
        """Get most popular templates by usage count"""
        templates = self.get_templates()
        return sorted(templates, key=lambda t: t.usage_count, reverse=True)[:limit]
    
    def get_recent_templates(self, limit: int = 10) -> List[PromptTemplate]:
        """Get most recently created templates"""
        templates = self.get_templates()
        return sorted(templates, key=lambda t: t.created_at or datetime.min, reverse=True)[:limit]
    
    def search_templates(self, query: str, category: str = None) -> List[PromptTemplate]:
        """Search templates by query"""
        return self.get_templates(category=category, search_term=query)
    
    # Template validation and suggestions
    def validate_template(self, template: PromptTemplate) -> List[str]:
        """Validate a template and return list of issues"""
        issues = []
        
        # Check syntax
        syntax_errors = self.engine.validate_template_syntax(template.content)
        issues.extend(syntax_errors)
        
        # Check if all variables in content have definitions
        content_variables = set(template.extract_variables())
        defined_variables = set(var.name for var in template.variables)
        
        undefined_vars = content_variables - defined_variables
        if undefined_vars:
            issues.append(f"Undefined variables: {', '.join(undefined_vars)}")
        
        unused_vars = defined_variables - content_variables
        if unused_vars:
            issues.append(f"Unused variable definitions: {', '.join(unused_vars)}")
        
        # Check for required variables without default values
        for var in template.variables:
            if var.required and not var.default_value:
                if var.name not in content_variables:
                    issues.append(f"Required variable '{var.name}' not used in template")
        
        return issues
    
    def suggest_improvements(self, template: PromptTemplate) -> List[str]:
        """Suggest improvements for a template"""
        suggestions = []
        
        # Check for missing descriptions
        if not template.description:
            suggestions.append("Add a description to help users understand the template's purpose")
        
        # Check variable descriptions
        for var in template.variables:
            if not var.description:
                suggestions.append(f"Add description for variable '{var.name}'")
        
        # Check for default values
        text_vars_without_defaults = [
            var.name for var in template.variables 
            if var.variable_type == "text" and not var.default_value and not var.required
        ]
        if text_vars_without_defaults:
            suggestions.append(f"Consider adding default values for optional variables: {', '.join(text_vars_without_defaults)}")
        
        # Check for validation patterns
        text_vars_without_validation = [
            var.name for var in template.variables 
            if var.variable_type == "text" and not var.validation_pattern and "email" in var.name.lower()
        ]
        if text_vars_without_validation:
            suggestions.append(f"Consider adding validation patterns for: {', '.join(text_vars_without_validation)}")
        
        return suggestions
    
    # Export/Import operations
    def export_template(self, template_id: int) -> Dict:
        """Export a template to a dictionary"""
        template = self.get_template(template_id)
        if not template:
            return {}
        
        return {
            'title': template.title,
            'content': template.content,
            'description': template.description,
            'category': template.category,
            'tags': template.tags,
            'variables': [
                {
                    'name': var.name,
                    'description': var.description,
                    'default_value': var.default_value,
                    'variable_type': var.variable_type,
                    'choices': var.choices,
                    'required': var.required,
                    'validation_pattern': var.validation_pattern
                }
                for var in template.variables
            ]
        }
    
    def import_template(self, template_data: Dict) -> int:
        """Import a template from a dictionary"""
        # Create template object
        template = PromptTemplate(
            title=template_data['title'],
            content=template_data['content'],
            description=template_data.get('description', ''),
            category=template_data.get('category', 'General'),
            tags=template_data.get('tags', [])
        )
        
        # Add variables
        for var_data in template_data.get('variables', []):
            variable = TemplateVariable(
                name=var_data['name'],
                description=var_data.get('description', ''),
                default_value=var_data.get('default_value', ''),
                variable_type=var_data.get('variable_type', 'text'),
                choices=var_data.get('choices', []),
                required=var_data.get('required', True),
                validation_pattern=var_data.get('validation_pattern', '')
            )
            template.add_variable(variable)
        
        return self.create_template(template)