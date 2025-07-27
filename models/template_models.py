"""
Template models for the Prompt Organizer application
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
import re
import json


@dataclass
class TemplateVariable:
    """Represents a variable in a template"""
    name: str
    description: str = ""
    default_value: str = ""
    variable_type: str = "text"  # text, number, boolean, choice, date
    choices: List[str] = field(default_factory=list)  # For choice type
    required: bool = True
    validation_pattern: Optional[str] = None  # Regex pattern for validation
    
    def validate_value(self, value: str) -> bool:
        """Validate a value against this variable's constraints"""
        if self.required and not value.strip():
            return False
        
        if self.variable_type == "number":
            try:
                float(value)
            except ValueError:
                return False
        
        elif self.variable_type == "boolean":
            if value.lower() not in ["true", "false", "yes", "no", "1", "0"]:
                return False
        
        elif self.variable_type == "choice":
            if self.choices and value not in self.choices:
                return False
        
        if self.validation_pattern:
            if not re.match(self.validation_pattern, value):
                return False
        
        return True
    
    def format_value(self, value: str) -> str:
        """Format a value according to the variable type"""
        if self.variable_type == "boolean":
            return "true" if value.lower() in ["true", "yes", "1"] else "false"
        elif self.variable_type == "number":
            try:
                # Try to format as integer if possible, otherwise as float
                num = float(value)
                return str(int(num)) if num.is_integer() else str(num)
            except ValueError:
                return value
        return value


@dataclass
class PromptTemplate:
    """Represents a prompt template with variables"""
    id: Optional[int] = None
    title: str = ""
    content: str = ""
    description: str = ""
    variables: List[TemplateVariable] = field(default_factory=list)
    category: str = "General"
    tags: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    usage_count: int = 0
    
    def extract_variables(self) -> List[str]:
        """Extract variable names from template content"""
        # Find all {variable_name} patterns
        pattern = r'\{([^}]+)\}'
        matches = re.findall(pattern, self.content)
        return list(set(matches))  # Remove duplicates
    
    def get_variable(self, name: str) -> Optional[TemplateVariable]:
        """Get a variable by name"""
        return next((var for var in self.variables if var.name == name), None)
    
    def add_variable(self, variable: TemplateVariable):
        """Add a variable to the template"""
        # Remove existing variable with same name
        self.variables = [var for var in self.variables if var.name != variable.name]
        self.variables.append(variable)
    
    def remove_variable(self, name: str):
        """Remove a variable by name"""
        self.variables = [var for var in self.variables if var.name != name]
    
    def validate_substitutions(self, substitutions: Dict[str, str]) -> Dict[str, str]:
        """Validate substitution values and return errors"""
        errors = {}
        
        for variable in self.variables:
            value = substitutions.get(variable.name, "")
            if not variable.validate_value(value):
                if variable.required and not value.strip():
                    errors[variable.name] = f"'{variable.name}' is required"
                elif variable.variable_type == "number":
                    errors[variable.name] = f"'{variable.name}' must be a number"
                elif variable.variable_type == "boolean":
                    errors[variable.name] = f"'{variable.name}' must be true/false"
                elif variable.variable_type == "choice":
                    errors[variable.name] = f"'{variable.name}' must be one of: {', '.join(variable.choices)}"
                elif variable.validation_pattern:
                    errors[variable.name] = f"'{variable.name}' format is invalid"
                else:
                    errors[variable.name] = f"'{variable.name}' value is invalid"
        
        return errors
    
    def substitute_variables(self, substitutions: Dict[str, str]) -> str:
        """Substitute variables in the template content"""
        result = self.content
        
        for variable in self.variables:
            value = substitutions.get(variable.name, variable.default_value)
            formatted_value = variable.format_value(value)
            
            # Replace all occurrences of {variable_name}
            pattern = r'\{' + re.escape(variable.name) + r'\}'
            result = re.sub(pattern, formatted_value, result)
        
        return result
    
    def get_preview(self, substitutions: Dict[str, str] = None) -> str:
        """Get a preview of the template with current substitutions"""
        if not substitutions:
            substitutions = {}
        
        # Use default values for missing substitutions
        full_substitutions = {}
        for variable in self.variables:
            full_substitutions[variable.name] = substitutions.get(
                variable.name, variable.default_value or f"[{variable.name}]"
            )
        
        return self.substitute_variables(full_substitutions)


@dataclass
class TemplateUsage:
    """Represents usage of a template"""
    id: Optional[int] = None
    template_id: int = 0
    substitutions: Dict[str, str] = field(default_factory=dict)
    generated_prompt_id: Optional[int] = None
    created_at: Optional[datetime] = None
    
    def to_json(self) -> str:
        """Convert substitutions to JSON string"""
        return json.dumps(self.substitutions)
    
    @classmethod
    def from_json(cls, template_id: int, json_str: str, **kwargs):
        """Create TemplateUsage from JSON string"""
        substitutions = json.loads(json_str) if json_str else {}
        return cls(template_id=template_id, substitutions=substitutions, **kwargs)


@dataclass
class TemplateCategory:
    """Represents a template category"""
    name: str
    description: str = ""
    color: str = "#007bff"
    icon: str = "📋"
    
    def __hash__(self):
        return hash(self.name)


# Predefined template categories
DEFAULT_CATEGORIES = [
    TemplateCategory("General", "General purpose templates", "#6c757d", "📋"),
    TemplateCategory("AI Assistant", "AI assistant and chatbot prompts", "#007bff", "🤖"),
    TemplateCategory("Code Review", "Code review and analysis templates", "#28a745", "💻"),
    TemplateCategory("Writing", "Creative and technical writing prompts", "#dc3545", "✍️"),
    TemplateCategory("Analysis", "Data analysis and research templates", "#ffc107", "📊"),
    TemplateCategory("Documentation", "Documentation and explanation templates", "#17a2b8", "📚"),
    TemplateCategory("Email", "Email and communication templates", "#6f42c1", "📧"),
    TemplateCategory("Meeting", "Meeting and collaboration templates", "#e83e8c", "🤝"),
    TemplateCategory("Learning", "Educational and training templates", "#fd7e14", "🎓"),
    TemplateCategory("Business", "Business and professional templates", "#20c997", "💼"),
]


class TemplateEngine:
    """Engine for processing templates and variable substitution"""
    
    @staticmethod
    def extract_variables_from_content(content: str) -> List[str]:
        """Extract variable names from content"""
        pattern = r'\{([^}]+)\}'
        matches = re.findall(pattern, content)
        return list(set(matches))
    
    @staticmethod
    def validate_template_syntax(content: str) -> List[str]:
        """Validate template syntax and return list of errors"""
        errors = []
        
        # Check for unmatched braces
        open_braces = content.count('{')
        close_braces = content.count('}')
        
        if open_braces != close_braces:
            errors.append(f"Unmatched braces: {open_braces} opening, {close_braces} closing")
        
        # Check for empty variable names
        empty_vars = re.findall(r'\{\s*\}', content)
        if empty_vars:
            errors.append(f"Found {len(empty_vars)} empty variable placeholder(s)")
        
        # Check for nested braces
        nested = re.findall(r'\{[^}]*\{[^}]*\}[^}]*\}', content)
        if nested:
            errors.append("Nested braces are not allowed in variable names")
        
        # Check for invalid variable names
        variables = TemplateEngine.extract_variables_from_content(content)
        for var in variables:
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', var.strip()):
                errors.append(f"Invalid variable name: '{var}' (use letters, numbers, underscore only)")
        
        return errors
    
    @staticmethod
    def suggest_variable_types(variable_name: str) -> str:
        """Suggest variable type based on name"""
        name_lower = variable_name.lower()
        
        if any(word in name_lower for word in ['count', 'number', 'amount', 'quantity', 'size', 'length']):
            return "number"
        elif any(word in name_lower for word in ['enable', 'disable', 'is_', 'has_', 'should_', 'can_']):
            return "boolean"
        elif any(word in name_lower for word in ['date', 'time', 'when', 'deadline']):
            return "date"
        elif any(word in name_lower for word in ['type', 'kind', 'category', 'format', 'style']):
            return "choice"
        else:
            return "text"
    
    @staticmethod
    def generate_variable_description(variable_name: str) -> str:
        """Generate a description for a variable based on its name"""
        # Convert camelCase or snake_case to readable format
        readable_name = re.sub(r'([A-Z])', r' \1', variable_name)
        readable_name = readable_name.replace('_', ' ').strip().title()
        
        return f"Enter the {readable_name.lower()}"
    
    @staticmethod
    def create_template_from_prompt(title: str, content: str, description: str = "") -> PromptTemplate:
        """Create a template from a regular prompt"""
        template = PromptTemplate(
            title=title,
            content=content,
            description=description
        )
        
        # Extract variables and create TemplateVariable objects
        variable_names = template.extract_variables()
        for var_name in variable_names:
            variable = TemplateVariable(
                name=var_name,
                description=TemplateEngine.generate_variable_description(var_name),
                variable_type=TemplateEngine.suggest_variable_types(var_name),
                required=True
            )
            template.add_variable(variable)
        
        return template