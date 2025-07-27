"""
Plugin management service for the Prompt Organizer
"""

import os
import sys
import json
import importlib
import importlib.util
import traceback
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Any, Type
from datetime import datetime

from models.plugin_models import (
    PluginInfo, PluginManifest, PluginStatus, PluginType, PluginPermission,
    PluginInterface, PluginAPI, PluginEvent, PluginHook, PluginConfig,
    PromptProcessorPlugin, UIExtensionPlugin, ExportFormatPlugin,
    ImportFormatPlugin, LLMProviderPlugin
)


class PluginManager:
    """Manages plugin loading, execution, and lifecycle"""
    
    def __init__(self, app_instance=None, database_manager=None, settings_manager=None):
        self.app_instance = app_instance
        self.database_manager = database_manager
        self.settings_manager = settings_manager
        self.analytics_service = None
        self.performance_service = None
        self.sharing_service = None
        
        self.config = PluginConfig()
        self.plugins: Dict[str, PluginInfo] = {}
        self.hooks: Dict[str, List[PluginHook]] = {}
        self.event_handlers: Dict[str, List[PluginInterface]] = {}
        
        # Plugin type registries
        self.prompt_processors: Dict[str, PromptProcessorPlugin] = {}
        self.ui_extensions: Dict[str, UIExtensionPlugin] = {}
        self.export_formats: Dict[str, ExportFormatPlugin] = {}
        self.import_formats: Dict[str, ImportFormatPlugin] = {}
        self.llm_providers: Dict[str, LLMProviderPlugin] = {}
        
        self._init_plugin_database()
        self._setup_plugin_directory()
    
    def _init_plugin_database(self):
        """Initialize plugin database tables"""
        if not self.database_manager:
            return
        
        try:
            db_path = self.database_manager.db_path
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Plugin registry table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS plugins (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    version TEXT NOT NULL,
                    plugin_type TEXT NOT NULL,
                    path TEXT NOT NULL,
                    status TEXT NOT NULL,
                    enabled BOOLEAN DEFAULT 1,
                    settings TEXT DEFAULT '{}',
                    installed_at TEXT NOT NULL,
                    last_loaded TEXT,
                    last_error TEXT,
                    load_count INTEGER DEFAULT 0
                )
            """)
            
            # Plugin permissions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS plugin_permissions (
                    plugin_id TEXT NOT NULL,
                    permission TEXT NOT NULL,
                    granted BOOLEAN DEFAULT 0,
                    granted_at TEXT,
                    FOREIGN KEY (plugin_id) REFERENCES plugins (id) ON DELETE CASCADE,
                    PRIMARY KEY (plugin_id, permission)
                )
            """)
            
            # Plugin events table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS plugin_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plugin_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    event_data TEXT DEFAULT '{}',
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (plugin_id) REFERENCES plugins (id) ON DELETE CASCADE
                )
            """)
            
            conn.commit()
            
        except sqlite3.Error as e:
            print(f"Error initializing plugin database: {e}")
        finally:
            conn.close()
    
    def _setup_plugin_directory(self):
        """Setup plugin directory structure"""
        plugins_dir = Path(self.config.plugins_directory)
        plugins_dir.mkdir(exist_ok=True)
        
        # Create subdirectories for different plugin types
        for plugin_type in PluginType:
            type_dir = plugins_dir / plugin_type.value
            type_dir.mkdir(exist_ok=True)
    
    def set_services(self, analytics_service=None, performance_service=None, sharing_service=None):
        """Set additional services for plugin API"""
        self.analytics_service = analytics_service
        self.performance_service = performance_service
        self.sharing_service = sharing_service
    
    def create_plugin_api(self) -> PluginAPI:
        """Create plugin API instance"""
        return PluginAPI(
            app_instance=self.app_instance,
            database_manager=self.database_manager,
            settings_manager=self.settings_manager,
            analytics_service=self.analytics_service,
            performance_service=self.performance_service,
            sharing_service=self.sharing_service
        )
    
    def discover_plugins(self) -> List[str]:
        """Discover available plugins in the plugins directory"""
        plugins_dir = Path(self.config.plugins_directory)
        discovered = []
        
        if not plugins_dir.exists():
            return discovered
        
        # Look for plugin manifests
        for item in plugins_dir.rglob("plugin.json"):
            try:
                with open(item, 'r', encoding='utf-8') as f:
                    manifest_data = json.load(f)
                
                plugin_dir = item.parent
                # Convert plugin_type string to enum if needed
                if 'plugin_type' in manifest_data and isinstance(manifest_data['plugin_type'], str):
                    manifest_data['plugin_type'] = PluginType(manifest_data['plugin_type'])
                
                # Convert permissions strings to enums if needed
                if 'permissions' in manifest_data:
                    permissions = []
                    for perm in manifest_data['permissions']:
                        if isinstance(perm, str):
                            permissions.append(PluginPermission(perm))
                        else:
                            permissions.append(perm)
                    manifest_data['permissions'] = permissions
                
                manifest = PluginManifest(**manifest_data)
                
                # Validate manifest
                if self._validate_manifest(manifest, plugin_dir):
                    discovered.append(str(plugin_dir))
                    
            except Exception as e:
                print(f"Error reading plugin manifest {item}: {e}")
        
        return discovered
    
    def _validate_manifest(self, manifest: PluginManifest, plugin_dir: Path) -> bool:
        """Validate plugin manifest"""
        if not manifest.id or not manifest.name:
            return False
        
        # Check if entry point exists
        entry_point = plugin_dir / manifest.entry_point
        if not entry_point.exists():
            return False
        
        # Check version compatibility
        if manifest.min_app_version:
            # Would check against app version
            pass
        
        return True
    
    def load_plugin(self, plugin_path: str) -> bool:
        """Load a plugin from the given path"""
        try:
            plugin_dir = Path(plugin_path)
            manifest_file = plugin_dir / "plugin.json"
            
            if not manifest_file.exists():
                print(f"No plugin manifest found at {plugin_path}")
                return False
            
            # Load manifest
            with open(manifest_file, 'r', encoding='utf-8') as f:
                manifest_data = json.load(f)
            
            manifest = PluginManifest(**manifest_data)
            
            # Check if plugin already loaded
            if manifest.id in self.plugins:
                print(f"Plugin {manifest.id} already loaded")
                return False
            
            # Create plugin info
            plugin_info = PluginInfo(
                manifest=manifest,
                path=str(plugin_dir),
                status=PluginStatus.LOADING
            )
            
            # Load plugin module
            entry_point = plugin_dir / manifest.entry_point
            spec = importlib.util.spec_from_file_location(manifest.id, entry_point)
            
            if not spec or not spec.loader:
                plugin_info.status = PluginStatus.ERROR
                plugin_info.error_message = "Failed to create module spec"
                self.plugins[manifest.id] = plugin_info
                return False
            
            module = importlib.util.module_from_spec(spec)
            
            # Add plugin directory to Python path
            if str(plugin_dir) not in sys.path:
                sys.path.insert(0, str(plugin_dir))
            
            try:
                spec.loader.exec_module(module)
            except Exception as e:
                plugin_info.status = PluginStatus.ERROR
                plugin_info.error_message = f"Failed to execute module: {str(e)}"
                self.plugins[manifest.id] = plugin_info
                return False
            
            # Get plugin class
            plugin_class = getattr(module, 'Plugin', None)
            if not plugin_class:
                plugin_info.status = PluginStatus.ERROR
                plugin_info.error_message = "No Plugin class found"
                self.plugins[manifest.id] = plugin_info
                return False
            
            # Create plugin instance
            api = self.create_plugin_api()
            plugin_instance = plugin_class(api)
            plugin_instance.manifest = manifest
            
            # Initialize plugin
            if not plugin_instance.initialize():
                plugin_info.status = PluginStatus.ERROR
                plugin_info.error_message = "Plugin initialization failed"
                self.plugins[manifest.id] = plugin_info
                return False
            
            # Store plugin info
            plugin_info.instance = plugin_instance
            plugin_info.status = PluginStatus.INACTIVE
            plugin_info.last_loaded = datetime.now().isoformat()
            plugin_info.load_count += 1
            
            self.plugins[manifest.id] = plugin_info
            
            # Register plugin by type
            self._register_plugin_by_type(plugin_instance, manifest)
            
            # Save to database
            self._save_plugin_to_db(plugin_info)
            
            print(f"Successfully loaded plugin: {manifest.name} v{manifest.version}")
            return True
            
        except Exception as e:
            print(f"Error loading plugin from {plugin_path}: {e}")
            traceback.print_exc()
            return False
    
    def _register_plugin_by_type(self, plugin_instance: PluginInterface, manifest: PluginManifest):
        """Register plugin in appropriate type registry"""
        plugin_id = manifest.id
        
        if isinstance(plugin_instance, PromptProcessorPlugin):
            self.prompt_processors[plugin_id] = plugin_instance
        elif isinstance(plugin_instance, UIExtensionPlugin):
            self.ui_extensions[plugin_id] = plugin_instance
        elif isinstance(plugin_instance, ExportFormatPlugin):
            self.export_formats[plugin_id] = plugin_instance
        elif isinstance(plugin_instance, ImportFormatPlugin):
            self.import_formats[plugin_id] = plugin_instance
        elif isinstance(plugin_instance, LLMProviderPlugin):
            self.llm_providers[plugin_id] = plugin_instance
    
    def _save_plugin_to_db(self, plugin_info: PluginInfo):
        """Save plugin information to database"""
        if not self.database_manager:
            return
        
        try:
            db_path = self.database_manager.db_path
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            manifest = plugin_info.manifest
            
            # Handle plugin_type - convert to string if it's an enum
            plugin_type_str = manifest.plugin_type.value if hasattr(manifest.plugin_type, 'value') else str(manifest.plugin_type)
            
            cursor.execute("""
                INSERT OR REPLACE INTO plugins
                (id, name, version, plugin_type, path, status, enabled, settings,
                 installed_at, last_loaded, last_error, load_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                manifest.id, manifest.name, manifest.version, plugin_type_str,
                plugin_info.path, plugin_info.status.value, plugin_info.enabled,
                json.dumps(plugin_info.settings), manifest.created_at,
                plugin_info.last_loaded, plugin_info.last_error, plugin_info.load_count
            ))
            
            # Save permissions
            for permission in manifest.permissions:
                # Handle permission - convert to string if it's an enum
                permission_str = permission.value if hasattr(permission, 'value') else str(permission)
                cursor.execute("""
                    INSERT OR REPLACE INTO plugin_permissions
                    (plugin_id, permission, granted, granted_at)
                    VALUES (?, ?, ?, ?)
                """, (manifest.id, permission_str, True, datetime.now().isoformat()))
            
            conn.commit()
            
        except sqlite3.Error as e:
            print(f"Error saving plugin to database: {e}")
        finally:
            conn.close()
    
    def activate_plugin(self, plugin_id: str) -> bool:
        """Activate a loaded plugin"""
        if plugin_id not in self.plugins:
            return False
        
        plugin_info = self.plugins[plugin_id]
        
        if plugin_info.status != PluginStatus.INACTIVE:
            return False
        
        try:
            if plugin_info.instance and plugin_info.instance.activate():
                plugin_info.status = PluginStatus.ACTIVE
                self._log_plugin_event(plugin_id, "activated")
                return True
        except Exception as e:
            plugin_info.status = PluginStatus.ERROR
            plugin_info.error_message = str(e)
            self._log_plugin_event(plugin_id, "activation_failed", {"error": str(e)})
        
        return False
    
    def deactivate_plugin(self, plugin_id: str) -> bool:
        """Deactivate an active plugin"""
        if plugin_id not in self.plugins:
            return False
        
        plugin_info = self.plugins[plugin_id]
        
        if plugin_info.status != PluginStatus.ACTIVE:
            return False
        
        try:
            if plugin_info.instance and plugin_info.instance.deactivate():
                plugin_info.status = PluginStatus.INACTIVE
                self._log_plugin_event(plugin_id, "deactivated")
                return True
        except Exception as e:
            plugin_info.error_message = str(e)
            self._log_plugin_event(plugin_id, "deactivation_failed", {"error": str(e)})
        
        return False
    
    def unload_plugin(self, plugin_id: str) -> bool:
        """Unload a plugin"""
        if plugin_id not in self.plugins:
            return False
        
        plugin_info = self.plugins[plugin_id]
        
        try:
            # Deactivate if active
            if plugin_info.status == PluginStatus.ACTIVE:
                self.deactivate_plugin(plugin_id)
            
            # Cleanup
            if plugin_info.instance:
                plugin_info.instance.cleanup()
            
            # Remove from registries
            self._unregister_plugin_by_type(plugin_id, plugin_info.manifest.plugin_type)
            
            # Remove from plugins dict
            del self.plugins[plugin_id]
            
            self._log_plugin_event(plugin_id, "unloaded")
            return True
            
        except Exception as e:
            print(f"Error unloading plugin {plugin_id}: {e}")
            return False
    
    def _unregister_plugin_by_type(self, plugin_id: str, plugin_type: PluginType):
        """Unregister plugin from type registry"""
        if plugin_type == PluginType.PROMPT_PROCESSOR and plugin_id in self.prompt_processors:
            del self.prompt_processors[plugin_id]
        elif plugin_type == PluginType.UI_EXTENSION and plugin_id in self.ui_extensions:
            del self.ui_extensions[plugin_id]
        elif plugin_type == PluginType.EXPORT_FORMAT and plugin_id in self.export_formats:
            del self.export_formats[plugin_id]
        elif plugin_type == PluginType.IMPORT_FORMAT and plugin_id in self.import_formats:
            del self.import_formats[plugin_id]
        elif plugin_type == PluginType.LLM_PROVIDER and plugin_id in self.llm_providers:
            del self.llm_providers[plugin_id]
    
    def get_plugins(self, plugin_type: Optional[PluginType] = None, 
                   status: Optional[PluginStatus] = None) -> List[PluginInfo]:
        """Get plugins filtered by type and/or status"""
        plugins = list(self.plugins.values())
        
        if plugin_type:
            plugins = [p for p in plugins if p.manifest.plugin_type == plugin_type]
        
        if status:
            plugins = [p for p in plugins if p.status == status]
        
        return plugins
    
    def get_plugin(self, plugin_id: str) -> Optional[PluginInfo]:
        """Get specific plugin info"""
        return self.plugins.get(plugin_id)
    
    def execute_prompt_processor(self, processor_id: str, prompt_content: str, 
                                context: Dict[str, Any] = None) -> Optional[str]:
        """Execute a prompt processor plugin"""
        if processor_id not in self.prompt_processors:
            return None
        
        processor = self.prompt_processors[processor_id]
        
        try:
            return processor.process_prompt(prompt_content, context or {})
        except Exception as e:
            print(f"Error executing prompt processor {processor_id}: {e}")
            return None
    
    def get_export_formats(self) -> Dict[str, ExportFormatPlugin]:
        """Get available export format plugins"""
        return {k: v for k, v in self.export_formats.items() 
                if self.plugins[k].status == PluginStatus.ACTIVE}
    
    def get_import_formats(self) -> Dict[str, ImportFormatPlugin]:
        """Get available import format plugins"""
        return {k: v for k, v in self.import_formats.items() 
                if self.plugins[k].status == PluginStatus.ACTIVE}
    
    def get_llm_providers(self) -> Dict[str, LLMProviderPlugin]:
        """Get available LLM provider plugins"""
        return {k: v for k, v in self.llm_providers.items() 
                if self.plugins[k].status == PluginStatus.ACTIVE}
    
    def emit_event(self, event: PluginEvent) -> bool:
        """Emit event to all interested plugins"""
        handled = False
        
        for plugin_info in self.plugins.values():
            if (plugin_info.status == PluginStatus.ACTIVE and 
                plugin_info.instance and 
                hasattr(plugin_info.instance, 'handle_event')):
                
                try:
                    if plugin_info.instance.handle_event(event):
                        handled = True
                        event.handled = True
                except Exception as e:
                    print(f"Error handling event in plugin {plugin_info.manifest.id}: {e}")
        
        return handled
    
    def _log_plugin_event(self, plugin_id: str, event_type: str, data: Dict[str, Any] = None):
        """Log plugin event to database"""
        if not self.database_manager:
            return
        
        try:
            db_path = self.database_manager.db_path
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO plugin_events (plugin_id, event_type, event_data, timestamp)
                VALUES (?, ?, ?, ?)
            """, (plugin_id, event_type, json.dumps(data or {}), datetime.now().isoformat()))
            
            conn.commit()
            
        except sqlite3.Error as e:
            print(f"Error logging plugin event: {e}")
        finally:
            conn.close()
    
    def load_all_plugins(self) -> int:
        """Load all discovered plugins"""
        discovered = self.discover_plugins()
        loaded_count = 0
        
        for plugin_path in discovered:
            if self.load_plugin(plugin_path):
                loaded_count += 1
        
        return loaded_count
    
    def auto_activate_plugins(self) -> int:
        """Auto-activate enabled plugins"""
        activated_count = 0
        
        for plugin_info in self.plugins.values():
            if (plugin_info.enabled and 
                plugin_info.status == PluginStatus.INACTIVE):
                if self.activate_plugin(plugin_info.manifest.id):
                    activated_count += 1
        
        return activated_count
    
    def update_plugin_settings(self, plugin_id: str, settings: Dict[str, Any]) -> bool:
        """Update plugin settings"""
        if plugin_id not in self.plugins:
            return False
        
        plugin_info = self.plugins[plugin_id]
        plugin_info.settings.update(settings)
        
        # Update plugin instance
        if plugin_info.instance:
            plugin_info.instance.update_settings(settings)
        
        # Save to database
        self._save_plugin_to_db(plugin_info)
        
        return True
    
    def get_plugin_statistics(self) -> Dict[str, Any]:
        """Get plugin system statistics"""
        total_plugins = len(self.plugins)
        active_plugins = len([p for p in self.plugins.values() if p.status == PluginStatus.ACTIVE])
        inactive_plugins = len([p for p in self.plugins.values() if p.status == PluginStatus.INACTIVE])
        error_plugins = len([p for p in self.plugins.values() if p.status == PluginStatus.ERROR])
        
        type_counts = {}
        for plugin_type in PluginType:
            type_counts[plugin_type.value] = len([
                p for p in self.plugins.values() 
                if p.manifest.plugin_type == plugin_type
            ])
        
        return {
            "total_plugins": total_plugins,
            "active_plugins": active_plugins,
            "inactive_plugins": inactive_plugins,
            "error_plugins": error_plugins,
            "plugins_by_type": type_counts
        }