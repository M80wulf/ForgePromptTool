"""
Application settings and configuration management
"""

import json
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from PyQt6.QtCore import QSettings


@dataclass
class LLMConfig:
    """LLM configuration settings"""
    enabled: bool = False
    provider: str = "local"  # "local", "lmstudio", "openai"
    local_base_url: str = "http://localhost:11434"
    local_model: str = "llama2"
    lmstudio_base_url: str = "http://localhost:1234"
    lmstudio_model: str = "local-model"
    openai_api_key: str = ""
    openai_model: str = "gpt-3.5-turbo"


@dataclass
class UIConfig:
    """UI configuration settings"""
    window_geometry: str = ""
    splitter_state: str = ""
    font_family: str = "Consolas"
    font_size: int = 11
    theme: str = "light"
    show_line_numbers: bool = True
    word_wrap: bool = True


@dataclass
class AppConfig:
    """Main application configuration"""
    auto_save: bool = True
    auto_save_interval: int = 30  # seconds
    backup_enabled: bool = True
    backup_interval: int = 24  # hours
    max_recent_files: int = 10
    database_path: str = "prompts.db"
    export_format: str = "json"
    ui: UIConfig = None
    llm: LLMConfig = None
    
    def __post_init__(self):
        if self.ui is None:
            self.ui = UIConfig()
        if self.llm is None:
            self.llm = LLMConfig()


class SettingsManager:
    """Manages application settings using QSettings and JSON files"""
    
    def __init__(self, app_name: str = "PromptOrganizer"):
        self.app_name = app_name
        self.qsettings = QSettings("PromptOrg", app_name)
        self.config_file = os.path.join(os.path.expanduser("~"), f".{app_name.lower()}", "config.json")
        self.config_dir = os.path.dirname(self.config_file)
        
        # Ensure config directory exists
        os.makedirs(self.config_dir, exist_ok=True)
        
        self._config = self.load_config()
    
    def load_config(self) -> AppConfig:
        """Load configuration from file"""
        try:
            print(f"[DEBUG] Loading config from: {self.config_file}")
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                print(f"[DEBUG] Loaded config data: {data}")
                
                # Convert nested dicts back to dataclasses
                ui_data = data.get('ui', {})
                llm_data = data.get('llm', {})
                
                print(f"[DEBUG] UI data: {ui_data}")
                print(f"[DEBUG] LLM data: {llm_data}")
                
                config = AppConfig(
                    auto_save=data.get('auto_save', True),
                    auto_save_interval=data.get('auto_save_interval', 30),
                    backup_enabled=data.get('backup_enabled', True),
                    backup_interval=data.get('backup_interval', 24),
                    max_recent_files=data.get('max_recent_files', 10),
                    database_path=data.get('database_path', 'prompts.db'),
                    export_format=data.get('export_format', 'json'),
                    ui=UIConfig(**ui_data),
                    llm=LLMConfig(**llm_data)
                )
                
                print(f"[DEBUG] Created config - Theme: {config.ui.theme}, LLM enabled: {config.llm.enabled}")
                return config
            else:
                print(f"[DEBUG] Config file does not exist: {self.config_file}")
            
        except Exception as e:
            print(f"[DEBUG] Error loading config: {e}")
            import traceback
            traceback.print_exc()
        
        # Return default config if loading fails
        print("[DEBUG] Returning default config")
        return AppConfig()
    
    def save_config(self):
        """Save configuration to file"""
        try:
            print(f"[DEBUG] Saving config to: {self.config_file}")
            # Convert dataclass to dict
            config_dict = asdict(self._config)
            print(f"[DEBUG] Config dict to save: {config_dict}")
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            
            print(f"[DEBUG] Config saved successfully")
                
        except Exception as e:
            print(f"[DEBUG] Error saving config: {e}")
            import traceback
            traceback.print_exc()
    
    def get_config(self) -> AppConfig:
        """Get current configuration"""
        return self._config
    
    def update_config(self, **kwargs):
        """Update configuration values"""
        for key, value in kwargs.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)
        self.save_config()
    
    def update_ui_config(self, **kwargs):
        """Update UI configuration values"""
        for key, value in kwargs.items():
            if hasattr(self._config.ui, key):
                setattr(self._config.ui, key, value)
        self.save_config()
    
    def update_llm_config(self, **kwargs):
        """Update LLM configuration values"""
        for key, value in kwargs.items():
            if hasattr(self._config.llm, key):
                setattr(self._config.llm, key, value)
        self.save_config()
    
    # QSettings methods for window state
    def save_window_geometry(self, geometry: bytes):
        """Save window geometry"""
        self.qsettings.setValue("geometry", geometry)
        self.qsettings.sync()
    
    def load_window_geometry(self) -> Optional[bytes]:
        """Load window geometry"""
        return self.qsettings.value("geometry")
    
    def save_splitter_state(self, state: bytes):
        """Save splitter state"""
        self.qsettings.setValue("splitter_state", state)
        self.qsettings.sync()
    
    def load_splitter_state(self) -> Optional[bytes]:
        """Load splitter state"""
        return self.qsettings.value("splitter_state")
    
    def save_recent_files(self, files: list):
        """Save recent files list"""
        self.qsettings.setValue("recent_files", files)
        self.qsettings.sync()
    
    def load_recent_files(self) -> list:
        """Load recent files list"""
        return self.qsettings.value("recent_files", [])
    
    def add_recent_file(self, file_path: str):
        """Add a file to recent files list"""
        recent = self.load_recent_files()
        
        # Remove if already exists
        if file_path in recent:
            recent.remove(file_path)
        
        # Add to beginning
        recent.insert(0, file_path)
        
        # Limit to max recent files
        recent = recent[:self._config.max_recent_files]
        
        self.save_recent_files(recent)
    
    def get_database_path(self) -> str:
        """Get full database path"""
        db_path = self._config.database_path
        
        # If relative path, make it relative to config directory
        if not os.path.isabs(db_path):
            db_path = os.path.join(self.config_dir, db_path)
        
        return db_path
    
    def get_backup_directory(self) -> str:
        """Get backup directory path"""
        backup_dir = os.path.join(self.config_dir, "backups")
        os.makedirs(backup_dir, exist_ok=True)
        return backup_dir
    
    def reset_to_defaults(self):
        """Reset configuration to defaults"""
        self._config = AppConfig()
        self.save_config()
        
        # Clear QSettings
        self.qsettings.clear()
        self.qsettings.sync()
    
    def export_settings(self, file_path: str):
        """Export settings to a file"""
        try:
            # Include both JSON config and QSettings
            export_data = {
                'config': asdict(self._config),
                'qsettings': {
                    'geometry': self.qsettings.value("geometry"),
                    'splitter_state': self.qsettings.value("splitter_state"),
                    'recent_files': self.qsettings.value("recent_files", [])
                },
                'export_timestamp': json.dumps(None, default=str)  # Current timestamp
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
                
        except Exception as e:
            raise Exception(f"Failed to export settings: {e}")
    
    def import_settings(self, file_path: str):
        """Import settings from a file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Import config
            if 'config' in data:
                config_data = data['config']
                ui_data = config_data.get('ui', {})
                llm_data = config_data.get('llm', {})
                
                self._config = AppConfig(
                    auto_save=config_data.get('auto_save', True),
                    auto_save_interval=config_data.get('auto_save_interval', 30),
                    backup_enabled=config_data.get('backup_enabled', True),
                    backup_interval=config_data.get('backup_interval', 24),
                    max_recent_files=config_data.get('max_recent_files', 10),
                    database_path=config_data.get('database_path', 'prompts.db'),
                    export_format=config_data.get('export_format', 'json'),
                    ui=UIConfig(**ui_data),
                    llm=LLMConfig(**llm_data)
                )
                
                self.save_config()
            
            # Import QSettings
            if 'qsettings' in data:
                qsettings_data = data['qsettings']
                for key, value in qsettings_data.items():
                    if value is not None:
                        self.qsettings.setValue(key, value)
                self.qsettings.sync()
                
        except Exception as e:
            raise Exception(f"Failed to import settings: {e}")


# Global settings instance
_settings_manager = None


def get_settings() -> SettingsManager:
    """Get global settings manager instance"""
    global _settings_manager
    if _settings_manager is None:
        _settings_manager = SettingsManager()
    return _settings_manager


def initialize_settings(app_name: str = "PromptOrganizer") -> SettingsManager:
    """Initialize global settings manager"""
    global _settings_manager
    _settings_manager = SettingsManager(app_name)
    return _settings_manager