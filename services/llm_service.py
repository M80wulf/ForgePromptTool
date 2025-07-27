"""
Service layer for future LLM integration
"""

from typing import Dict, List, Optional, Callable
from abc import ABC, abstractmethod
import json
import requests
from datetime import datetime


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    def rewrite_prompt(self, prompt: str, style: str = "clear") -> str:
        """Rewrite a prompt for better clarity"""
        pass
    
    @abstractmethod
    def explain_prompt(self, prompt: str) -> str:
        """Explain what a prompt does"""
        pass
    
    @abstractmethod
    def suggest_improvements(self, prompt: str) -> List[str]:
        """Suggest improvements for a prompt"""
        pass
    
    @abstractmethod
    def generate_tags(self, prompt: str) -> List[str]:
        """Generate relevant tags for a prompt"""
        pass


class LocalLLMProvider(LLMProvider):
    """Provider for local LLM APIs (like Ollama, LocalAI, etc.)"""
    
    def __init__(self, base_url: str = "http://localhost:11434", 
                 model: str = "llama2"):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.timeout = 30
    
    def _make_request(self, prompt: str, system_prompt: str = "") -> str:
        """Make a request to the local LLM API"""
        try:
            print(f"[DEBUG] Making LLM request to: {self.base_url}")
            print(f"[DEBUG] Model: {self.model}")
            print(f"[DEBUG] Prompt length: {len(prompt)}")
            print(f"[DEBUG] System prompt: {system_prompt[:100]}...")
            
            # Detect API format based on base URL
            if "1234" in self.base_url or "lmstudio" in self.base_url.lower():
                # LM Studio uses OpenAI-compatible API
                print("[DEBUG] Using LM Studio/OpenAI API format")
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})
                
                payload = {
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "max_tokens": 1000,
                    "temperature": 0.7
                }
                
                endpoint = f"{self.base_url}/v1/chat/completions"
            else:
                # Ollama API format
                print("[DEBUG] Using Ollama API format")
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "system": system_prompt,
                    "stream": False
                }
                
                endpoint = f"{self.base_url}/api/generate"
            
            print(f"[DEBUG] Request endpoint: {endpoint}")
            print(f"[DEBUG] Request payload: {payload}")
            
            response = requests.post(
                endpoint,
                json=payload,
                timeout=self.timeout
            )
            
            print(f"[DEBUG] Response status: {response.status_code}")
            print(f"[DEBUG] Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"[DEBUG] Response JSON: {result}")
                
                # Extract response based on API format
                if "1234" in self.base_url or "lmstudio" in self.base_url.lower():
                    # LM Studio/OpenAI format
                    response_text = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                else:
                    # Ollama format
                    response_text = result.get('response', '')
                
                print(f"[DEBUG] Extracted response: '{response_text}'")
                return response_text
            else:
                print(f"[DEBUG] Error response text: {response.text}")
                raise Exception(f"API request failed: {response.status_code} - {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"[DEBUG] Request exception: {str(e)}")
            raise Exception(f"Connection error: {str(e)}")
    
    def rewrite_prompt(self, prompt: str, style: str = "clear") -> str:
        """Rewrite a prompt for better clarity"""
        system_prompt = f"""You are an expert at rewriting prompts to be more {style} and effective. 
        Rewrite the following prompt to be clearer, more specific, and better structured while maintaining its original intent."""
        
        user_prompt = f"Please rewrite this prompt:\n\n{prompt}"
        
        try:
            return self._make_request(user_prompt, system_prompt)
        except Exception as e:
            return f"Error rewriting prompt: {str(e)}"
    
    def explain_prompt(self, prompt: str) -> str:
        """Explain what a prompt does"""
        system_prompt = """You are an expert at analyzing prompts. 
        Explain what the following prompt is designed to do, what kind of responses it might generate, 
        and any notable techniques or patterns it uses."""
        
        user_prompt = f"Please explain this prompt:\n\n{prompt}"
        
        try:
            return self._make_request(user_prompt, system_prompt)
        except Exception as e:
            return f"Error explaining prompt: {str(e)}"
    
    def suggest_improvements(self, prompt: str) -> List[str]:
        """Suggest improvements for a prompt"""
        system_prompt = """You are an expert at improving prompts. 
        Analyze the following prompt and suggest 3-5 specific improvements. 
        Format your response as a JSON array of strings."""
        
        user_prompt = f"Please suggest improvements for this prompt:\n\n{prompt}"
        
        try:
            response = self._make_request(user_prompt, system_prompt)
            # Try to parse as JSON, fallback to splitting by lines
            try:
                suggestions = json.loads(response)
                if isinstance(suggestions, list):
                    return suggestions
            except json.JSONDecodeError:
                pass
            
            # Fallback: split by lines and clean up
            lines = response.strip().split('\n')
            suggestions = [line.strip('- •').strip() for line in lines if line.strip()]
            return suggestions[:5]  # Limit to 5 suggestions
            
        except Exception as e:
            return [f"Error generating suggestions: {str(e)}"]
    
    def generate_tags(self, prompt: str) -> List[str]:
        """Generate relevant tags for a prompt"""
        system_prompt = """You are an expert at categorizing prompts. 
        Generate 3-7 relevant tags for the following prompt. 
        Tags should be single words or short phrases that describe the prompt's purpose, domain, or technique.
        Format your response as a JSON array of strings."""
        
        user_prompt = f"Please generate tags for this prompt:\n\n{prompt}"
        
        try:
            response = self._make_request(user_prompt, system_prompt)
            # Try to parse as JSON
            try:
                tags = json.loads(response)
                if isinstance(tags, list):
                    return [tag.strip().lower() for tag in tags if tag.strip()]
            except json.JSONDecodeError:
                pass
            
            # Fallback: extract words that look like tags
            words = response.replace(',', ' ').replace(';', ' ').split()
            tags = [word.strip('[]"\'.,;:!?').lower() for word in words 
                   if len(word.strip('[]"\'.,;:!?')) > 2]
            return list(set(tags))[:7]  # Remove duplicates and limit
            
        except Exception as e:
            return ["error", "llm-failed"]


class OpenAIProvider(LLMProvider):
    """Provider for OpenAI API"""
    
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.openai.com/v1"
    
    def _make_request(self, messages: List[Dict]) -> str:
        """Make a request to OpenAI API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 1000,
            "temperature": 0.7
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                raise Exception(f"API request failed: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"Connection error: {str(e)}")
    
    def rewrite_prompt(self, prompt: str, style: str = "clear") -> str:
        """Rewrite a prompt for better clarity"""
        messages = [
            {
                "role": "system",
                "content": f"You are an expert at rewriting prompts to be more {style} and effective. Rewrite prompts to be clearer, more specific, and better structured while maintaining their original intent."
            },
            {
                "role": "user",
                "content": f"Please rewrite this prompt:\n\n{prompt}"
            }
        ]
        
        try:
            return self._make_request(messages)
        except Exception as e:
            return f"Error rewriting prompt: {str(e)}"
    
    def explain_prompt(self, prompt: str) -> str:
        """Explain what a prompt does"""
        messages = [
            {
                "role": "system",
                "content": "You are an expert at analyzing prompts. Explain what prompts are designed to do, what kind of responses they might generate, and any notable techniques or patterns they use."
            },
            {
                "role": "user",
                "content": f"Please explain this prompt:\n\n{prompt}"
            }
        ]
        
        try:
            return self._make_request(messages)
        except Exception as e:
            return f"Error explaining prompt: {str(e)}"
    
    def suggest_improvements(self, prompt: str) -> List[str]:
        """Suggest improvements for a prompt"""
        messages = [
            {
                "role": "system",
                "content": "You are an expert at improving prompts. Analyze prompts and suggest 3-5 specific improvements. Format your response as a JSON array of strings."
            },
            {
                "role": "user",
                "content": f"Please suggest improvements for this prompt:\n\n{prompt}"
            }
        ]
        
        try:
            response = self._make_request(messages)
            try:
                suggestions = json.loads(response)
                if isinstance(suggestions, list):
                    return suggestions
            except json.JSONDecodeError:
                pass
            
            # Fallback parsing
            lines = response.strip().split('\n')
            suggestions = [line.strip('- •').strip() for line in lines if line.strip()]
            return suggestions[:5]
            
        except Exception as e:
            return [f"Error generating suggestions: {str(e)}"]
    
    def generate_tags(self, prompt: str) -> List[str]:
        """Generate relevant tags for a prompt"""
        messages = [
            {
                "role": "system",
                "content": "You are an expert at categorizing prompts. Generate 3-7 relevant tags for prompts. Tags should be single words or short phrases that describe the prompt's purpose, domain, or technique. Format your response as a JSON array of strings."
            },
            {
                "role": "user",
                "content": f"Please generate tags for this prompt:\n\n{prompt}"
            }
        ]
        
        try:
            response = self._make_request(messages)
            try:
                tags = json.loads(response)
                if isinstance(tags, list):
                    return [tag.strip().lower() for tag in tags if tag.strip()]
            except json.JSONDecodeError:
                pass
            
            # Fallback parsing
            words = response.replace(',', ' ').replace(';', ' ').split()
            tags = [word.strip('[]"\'.,;:!?').lower() for word in words 
                   if len(word.strip('[]"\'.,;:!?')) > 2]
            return list(set(tags))[:7]
            
        except Exception as e:
            return ["error", "llm-failed"]


class LLMService:
    """Service for managing LLM operations"""
    
    def __init__(self):
        self.providers: Dict[str, LLMProvider] = {}
        self.active_provider: Optional[str] = None
        self.history: List[Dict] = []
    
    def add_provider(self, name: str, provider: LLMProvider):
        """Add an LLM provider"""
        self.providers[name] = provider
        if self.active_provider is None:
            self.active_provider = name
    
    def set_active_provider(self, name: str):
        """Set the active LLM provider"""
        if name in self.providers:
            self.active_provider = name
        else:
            raise ValueError(f"Provider '{name}' not found")
    
    def get_active_provider(self) -> Optional[LLMProvider]:
        """Get the active LLM provider"""
        if self.active_provider and self.active_provider in self.providers:
            return self.providers[self.active_provider]
        return None
    
    def _log_operation(self, operation: str, prompt: str, result: str):
        """Log LLM operations for history"""
        self.history.append({
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'provider': self.active_provider,
            'prompt_preview': prompt[:100] + '...' if len(prompt) > 100 else prompt,
            'result_preview': result[:200] + '...' if len(result) > 200 else result
        })
        
        # Keep only last 100 operations
        if len(self.history) > 100:
            self.history = self.history[-100:]
    
    def rewrite_prompt(self, prompt: str, style: str = "clear") -> str:
        """Rewrite a prompt using the active provider"""
        provider = self.get_active_provider()
        if not provider:
            return "No LLM provider configured"
        
        result = provider.rewrite_prompt(prompt, style)
        self._log_operation("rewrite", prompt, result)
        return result
    
    def explain_prompt(self, prompt: str) -> str:
        """Explain a prompt using the active provider"""
        provider = self.get_active_provider()
        if not provider:
            return "No LLM provider configured"
        
        result = provider.explain_prompt(prompt)
        self._log_operation("explain", prompt, result)
        return result
    
    def suggest_improvements(self, prompt: str) -> List[str]:
        """Suggest improvements using the active provider"""
        provider = self.get_active_provider()
        if not provider:
            return ["No LLM provider configured"]
        
        result = provider.suggest_improvements(prompt)
        self._log_operation("improve", prompt, str(result))
        return result
    
    def generate_tags(self, prompt: str) -> List[str]:
        """Generate tags using the active provider"""
        provider = self.get_active_provider()
        if not provider:
            return ["no-llm"]
        
        result = provider.generate_tags(prompt)
        self._log_operation("tags", prompt, str(result))
        return result
    
    def get_history(self) -> List[Dict]:
        """Get operation history"""
        return self.history.copy()
    
    def clear_history(self):
        """Clear operation history"""
        self.history.clear()
    
    def is_available(self) -> bool:
        """Check if any LLM provider is available"""
        return self.get_active_provider() is not None
    
    def get_provider_names(self) -> List[str]:
        """Get list of available provider names"""
        return list(self.providers.keys())


# Factory function for easy setup
def create_llm_service(config: Dict) -> LLMService:
    """Create and configure LLM service based on config"""
    service = LLMService()
    
    # Add local LLM if configured
    if config.get('local_llm', {}).get('enabled', False):
        local_config = config['local_llm']
        provider = LocalLLMProvider(
            base_url=local_config.get('base_url', 'http://localhost:11434'),
            model=local_config.get('model', 'llama2')
        )
        service.add_provider('local', provider)
    
    # Add LM Studio if configured (uses same LocalLLMProvider as local)
    if config.get('lmstudio', {}).get('enabled', False):
        lmstudio_config = config['lmstudio']
        provider = LocalLLMProvider(
            base_url=lmstudio_config.get('base_url', 'http://localhost:1234'),
            model=lmstudio_config.get('model', 'local-model')
        )
        service.add_provider('lmstudio', provider)
    
    # Handle case where 'lmstudio' provider is specified but config uses 'local_llm'
    if config.get('active_provider') == 'lmstudio' and config.get('local_llm', {}).get('enabled', False):
        local_config = config['local_llm']
        provider = LocalLLMProvider(
            base_url=local_config.get('base_url', 'http://localhost:1234'),
            model=local_config.get('model', 'local-model')
        )
        service.add_provider('lmstudio', provider)
    
    # Add OpenAI if configured
    if config.get('openai', {}).get('enabled', False):
        openai_config = config['openai']
        api_key = openai_config.get('api_key')
        if api_key:
            provider = OpenAIProvider(
                api_key=api_key,
                model=openai_config.get('model', 'gpt-3.5-turbo')
            )
            service.add_provider('openai', provider)
    
    # Set active provider
    active = config.get('active_provider')
    if active and active in service.get_provider_names():
        service.set_active_provider(active)
    
    return service