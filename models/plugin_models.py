"""
Plugin system models for the Prompt Organizer
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import json


class PluginType(Enum):
    """Types of plugins"""
    PROMPT_PROCESSOR = "prompt_processor"
    UI_EXTENSION = "ui_extension"
    EXPORT_FORMAT = "export_format"
    IMPORT_FORMAT = "import_format"
    LLM_PROVIDER = "llm_provider"
    ANALYTICS_EXTENSION = "analytics_extension"
    SEARCH_PROVIDER = "search_provider"
    THEME_PROVIDER = "theme_provider"
    WORKFLOW_AUTOMATION = "workflow_automation"


class PluginStatus(Enum):
    """Plugin status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    LOADING = "loading"
    DISABLED = "disabled"


class PluginPermission(Enum):
    """Plugin permissions"""
    READ_PROMPTS = "read_prompts"
    WRITE_PROMPTS = "write_prompts"
    READ_FOLDERS = "read_folders"
    WRITE_FOLDERS = "write_folders"
    READ_TAGS = "read_tags"
    WRITE_TAGS = "write_tags"
    NETWORK_ACCESS = "network_access"
    FILE_SYSTEM_ACCESS = "file_system_access"
    UI_MODIFICATION = "ui_modification"
    DATABASE_ACCESS = "database_access"
    SETTINGS_ACCESS = "settings_access"
    ANALYTICS_ACCESS = "analytics_access"


@dataclass
class PluginManifest:
    """Plugin manifest containing metadata"""
    id: str = ""
    name: str = ""
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    author_email: str = ""
    website: str = ""
    license: str = "MIT"
    plugin_type: PluginType = PluginType.PROMPT_PROCESSOR
    entry_point: str = "main.py"
    dependencies: List[str] = field(default_factory=list)
    permissions: List[PluginPermission] = field(default_factory=list)
    min_app_version: str = "1.0.0"
    max_app_version: str = ""
    settings_schema: Dict[str, Any] = field(default_factory=dict)
    menu_items: List[Dict[str, str]] = field(default_factory=list)
    toolbar_items: List[Dict[str, str]] = field(default_factory=list)
    context_menu_items: List[Dict[str, str]] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class PluginInfo:
    """Runtime plugin information"""
    manifest: PluginManifest = field(default_factory=PluginManifest)
    path: str = ""
    status: PluginStatus = PluginStatus.INACTIVE
    error_message: Optional[str] = None
    last_loaded: Optional[str] = None
    last_error: Optional[str] = None
    settings: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    load_count: int = 0
    instance: Optional[Any] = None


@dataclass
class PluginHook:
    """Plugin hook definition"""
    name: str = ""
    description: str = ""
    parameters: Dict[str, type] = field(default_factory=dict)
    return_type: Optional[type] = None
    required: bool = False
    priority: int = 100


@dataclass
class PluginEvent:
    """Plugin event data"""
    event_type: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    source: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    handled: bool = False


@dataclass
class PluginAPI:
    """Plugin API interface"""
    app_instance: Optional[Any] = None
    database_manager: Optional[Any] = None
    settings_manager: Optional[Any] = None
    analytics_service: Optional[Any] = None
    performance_service: Optional[Any] = None
    sharing_service: Optional[Any] = None
    
    def get_prompts(self) -> List[Dict[str, Any]]:
        """Get all prompts"""
        if self.database_manager:
            return self.database_manager.get_prompts()
        return []
    
    def get_prompt(self, prompt_id: int) -> Optional[Dict[str, Any]]:
        """Get specific prompt"""
        if self.database_manager:
            return self.database_manager.get_prompt(prompt_id)
        return None
    
    def create_prompt(self, title: str, content: str, **kwargs) -> Optional[int]:
        """Create new prompt"""
        if self.database_manager:
            return self.database_manager.create_prompt(title, content, **kwargs)
        return None
    
    def update_prompt(self, prompt_id: int, **kwargs) -> bool:
        """Update existing prompt"""
        if self.database_manager:
            return self.database_manager.update_prompt(prompt_id, **kwargs)
        return False
    
    def delete_prompt(self, prompt_id: int) -> bool:
        """Delete prompt"""
        if self.database_manager:
            return self.database_manager.delete_prompt(prompt_id)
        return False
    
    def get_folders(self) -> List[Dict[str, Any]]:
        """Get all folders"""
        if self.database_manager:
            return self.database_manager.get_all_folders()
        return []
    
    def get_tags(self) -> List[Dict[str, Any]]:
        """Get all tags"""
        if self.database_manager:
            return self.database_manager.get_tags()
        return []
    
    def show_message(self, title: str, message: str, message_type: str = "info"):
        """Show message to user"""
        if self.app_instance:
            from PyQt6.QtWidgets import QMessageBox
            if message_type == "info":
                QMessageBox.information(self.app_instance, title, message)
            elif message_type == "warning":
                QMessageBox.warning(self.app_instance, title, message)
            elif message_type == "error":
                QMessageBox.critical(self.app_instance, title, message)
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get application setting"""
        if self.settings_manager:
            return self.settings_manager.get_setting(key, default)
        return default
    
    def set_setting(self, key: str, value: Any) -> bool:
        """Set application setting"""
        if self.settings_manager:
            return self.settings_manager.set_setting(key, value)
        return False


class PluginInterface:
    """Base interface for all plugins"""
    
    def __init__(self, api: PluginAPI):
        self.api = api
        self.manifest = None
        self.settings = {}
    
    def initialize(self) -> bool:
        """Initialize the plugin"""
        return True
    
    def activate(self) -> bool:
        """Activate the plugin"""
        return True
    
    def deactivate(self) -> bool:
        """Deactivate the plugin"""
        return True
    
    def cleanup(self) -> bool:
        """Cleanup plugin resources"""
        return True
    
    def get_name(self) -> str:
        """Get plugin name"""
        return self.manifest.name if self.manifest else "Unknown Plugin"
    
    def get_version(self) -> str:
        """Get plugin version"""
        return self.manifest.version if self.manifest else "1.0.0"
    
    def get_description(self) -> str:
        """Get plugin description"""
        return self.manifest.description if self.manifest else ""
    
    def get_settings_schema(self) -> Dict[str, Any]:
        """Get plugin settings schema"""
        return self.manifest.settings_schema if self.manifest else {}
    
    def update_settings(self, settings: Dict[str, Any]) -> bool:
        """Update plugin settings"""
        self.settings.update(settings)
        return True
    
    def handle_event(self, event: PluginEvent) -> bool:
        """Handle plugin event"""
        return False


class PromptProcessorPlugin(PluginInterface):
    """Base class for prompt processor plugins"""
    
    def process_prompt(self, prompt_content: str, context: Dict[str, Any] = None) -> str:
        """Process prompt content"""
        return prompt_content
    
    def get_processor_name(self) -> str:
        """Get processor name for UI"""
        return self.get_name()
    
    def get_processor_description(self) -> str:
        """Get processor description for UI"""
        return self.get_description()


class UIExtensionPlugin(PluginInterface):
    """Base class for UI extension plugins"""
    
    def create_menu_items(self) -> List[Dict[str, Any]]:
        """Create menu items for the plugin"""
        return []
    
    def create_toolbar_items(self) -> List[Dict[str, Any]]:
        """Create toolbar items for the plugin"""
        return []
    
    def create_context_menu_items(self) -> List[Dict[str, Any]]:
        """Create context menu items for the plugin"""
        return []
    
    def create_widget(self, parent=None) -> Optional[Any]:
        """Create plugin widget"""
        return None


class ExportFormatPlugin(PluginInterface):
    """Base class for export format plugins"""
    
    def get_format_name(self) -> str:
        """Get format name"""
        return "Unknown Format"
    
    def get_file_extension(self) -> str:
        """Get file extension"""
        return ".txt"
    
    def export_prompts(self, prompts: List[Dict[str, Any]], file_path: str) -> bool:
        """Export prompts to file"""
        return False
    
    def export_prompt(self, prompt: Dict[str, Any], file_path: str) -> bool:
        """Export single prompt to file"""
        return False


class ImportFormatPlugin(PluginInterface):
    """Base class for import format plugins"""
    
    def get_format_name(self) -> str:
        """Get format name"""
        return "Unknown Format"
    
    def get_file_extensions(self) -> List[str]:
        """Get supported file extensions"""
        return [".txt"]
    
    def import_prompts(self, file_path: str) -> List[Dict[str, Any]]:
        """Import prompts from file"""
        return []
    
    def validate_file(self, file_path: str) -> bool:
        """Validate if file can be imported"""
        return False


class LLMProviderPlugin(PluginInterface):
    """Base class for LLM provider plugins"""
    
    def get_provider_name(self) -> str:
        """Get provider name"""
        return "Unknown Provider"
    
    def get_models(self) -> List[str]:
        """Get available models"""
        return []
    
    def generate_text(self, prompt: str, model: str = None, **kwargs) -> str:
        """Generate text using the LLM"""
        return ""
    
    def estimate_cost(self, prompt: str, model: str = None) -> float:
        """Estimate cost for the request"""
        return 0.0
    
    def validate_connection(self) -> bool:
        """Validate connection to the LLM service"""
        return False


@dataclass
class PluginConfig:
    """Plugin system configuration"""
    plugins_directory: str = "plugins"
    auto_load_plugins: bool = True
    allow_unsafe_plugins: bool = False
    plugin_timeout: int = 30
    max_plugins: int = 100
    enable_plugin_updates: bool = True
    plugin_repository_url: str = ""
    sandbox_plugins: bool = True
    log_plugin_activity: bool = True