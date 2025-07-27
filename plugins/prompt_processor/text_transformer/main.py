"""
Text Transformer Plugin for Prompt Organizer
Transforms text case and format in prompts
"""

import re
import sys
import os

# Add the main app directory to the path so we can import the plugin models
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from models.plugin_models import PromptProcessorPlugin, PluginEvent
from typing import Dict, Any


class Plugin(PromptProcessorPlugin):
    """Text Transformer Plugin"""
    
    def __init__(self, api):
        super().__init__(api)
        self.name = "Text Transformer"
        self.version = "1.0.0"
    
    def initialize(self) -> bool:
        """Initialize the plugin"""
        print(f"Initializing {self.name} v{self.version}")
        return True
    
    def activate(self) -> bool:
        """Activate the plugin"""
        print(f"Activating {self.name}")
        return True
    
    def deactivate(self) -> bool:
        """Deactivate the plugin"""
        print(f"Deactivating {self.name}")
        return True
    
    def process_prompt(self, prompt_content: str, context: Dict[str, Any] = None) -> str:
        """Process prompt content with text transformations"""
        if not context:
            context = {}
        
        transform_type = context.get('transform_type', self.settings.get('default_case', 'none'))
        preserve_formatting = self.settings.get('preserve_formatting', True)
        transform_variables = self.settings.get('transform_variables', False)
        
        if transform_type == 'none':
            return prompt_content
        
        # Split content into lines to preserve formatting if needed
        if preserve_formatting:
            lines = prompt_content.split('\n')
            transformed_lines = []
            
            for line in lines:
                transformed_line = self._transform_line(line, transform_type, transform_variables)
                transformed_lines.append(transformed_line)
            
            return '\n'.join(transformed_lines)
        else:
            return self._transform_text(prompt_content, transform_type, transform_variables)
    
    def _transform_line(self, line: str, transform_type: str, transform_variables: bool) -> str:
        """Transform a single line of text"""
        # Preserve leading/trailing whitespace
        leading_space = len(line) - len(line.lstrip())
        trailing_space = len(line) - len(line.rstrip())
        
        content = line.strip()
        if not content:
            return line
        
        transformed = self._transform_text(content, transform_type, transform_variables)
        
        # Restore whitespace
        return ' ' * leading_space + transformed + ' ' * trailing_space
    
    def _transform_text(self, text: str, transform_type: str, transform_variables: bool) -> str:
        """Transform text according to the specified type"""
        if not transform_variables:
            # Preserve variables in {brackets} and other special patterns
            variable_pattern = r'(\{[^}]+\})'
            parts = re.split(variable_pattern, text)
            
            transformed_parts = []
            for part in parts:
                if re.match(variable_pattern, part):
                    # This is a variable, don't transform
                    transformed_parts.append(part)
                else:
                    # Transform this part
                    transformed_parts.append(self._apply_transform(part, transform_type))
            
            return ''.join(transformed_parts)
        else:
            return self._apply_transform(text, transform_type)
    
    def _apply_transform(self, text: str, transform_type: str) -> str:
        """Apply the actual text transformation"""
        if transform_type == 'upper':
            return text.upper()
        elif transform_type == 'lower':
            return text.lower()
        elif transform_type == 'title':
            return text.title()
        elif transform_type == 'sentence':
            # Capitalize first letter of each sentence
            sentences = re.split(r'([.!?]+\s*)', text)
            result = []
            for sentence in sentences:
                if sentence.strip() and not re.match(r'[.!?]+\s*', sentence):
                    # This is actual text, not punctuation
                    sentence = sentence.strip()
                    if sentence:
                        sentence = sentence[0].upper() + sentence[1:].lower()
                result.append(sentence)
            return ''.join(result)
        else:
            return text
    
    def get_processor_name(self) -> str:
        """Get processor name for UI"""
        return "Text Transformer"
    
    def get_processor_description(self) -> str:
        """Get processor description for UI"""
        return "Transform text case and format in prompts"
    
    def handle_event(self, event: PluginEvent) -> bool:
        """Handle plugin events"""
        if event.event_type == "transform_upper":
            # Handle uppercase transformation request
            prompt_content = event.data.get('prompt_content', '')
            if prompt_content:
                transformed = self.process_prompt(prompt_content, {'transform_type': 'upper'})
                event.data['result'] = transformed
                return True
        
        elif event.event_type == "transform_lower":
            # Handle lowercase transformation request
            prompt_content = event.data.get('prompt_content', '')
            if prompt_content:
                transformed = self.process_prompt(prompt_content, {'transform_type': 'lower'})
                event.data['result'] = transformed
                return True
        
        return False
    
    def get_available_transforms(self) -> Dict[str, str]:
        """Get available transformation types"""
        return {
            'none': 'No transformation',
            'upper': 'UPPERCASE',
            'lower': 'lowercase',
            'title': 'Title Case',
            'sentence': 'Sentence case'
        }
    
    def validate_settings(self, settings: Dict[str, Any]) -> bool:
        """Validate plugin settings"""
        valid_cases = ['none', 'upper', 'lower', 'title', 'sentence']
        
        default_case = settings.get('default_case', 'none')
        if default_case not in valid_cases:
            return False
        
        return True
    
    def update_settings(self, settings: Dict[str, Any]) -> bool:
        """Update plugin settings"""
        if not self.validate_settings(settings):
            return False
        
        self.settings.update(settings)
        print(f"Updated {self.name} settings: {settings}")
        return True


# Example usage and testing
if __name__ == "__main__":
    # Mock API for testing
    class MockAPI:
        def show_message(self, title, message, message_type="info"):
            print(f"[{message_type.upper()}] {title}: {message}")
    
    # Test the plugin
    api = MockAPI()
    plugin = Plugin(api)
    
    # Initialize
    plugin.initialize()
    plugin.activate()
    
    # Test transformations
    test_prompt = """Hello {name}, please write a story about {topic}.
    
    Make sure to include:
    - Character development
    - Plot progression
    - A satisfying conclusion
    
    The story should be engaging and well-written."""
    
    print("Original prompt:")
    print(test_prompt)
    print("\n" + "="*50 + "\n")
    
    # Test different transformations
    transforms = ['upper', 'lower', 'title', 'sentence']
    
    for transform in transforms:
        print(f"{transform.upper()} transformation:")
        result = plugin.process_prompt(test_prompt, {'transform_type': transform})
        print(result)
        print("\n" + "-"*30 + "\n")
    
    # Test with variable transformation enabled
    plugin.update_settings({'transform_variables': True})
    print("UPPER transformation with variables transformed:")
    result = plugin.process_prompt(test_prompt, {'transform_type': 'upper'})
    print(result)