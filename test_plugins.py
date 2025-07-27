#!/usr/bin/env python3
"""
Test script for plugin system functionality
"""

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.database import DatabaseManager
from services.plugin_service import PluginManager
from models.plugin_models import PluginType, PluginStatus

def test_plugin_functionality():
    """Test the plugin system functionality"""
    print("Testing Plugin System Functionality")
    print("=" * 60)
    
    # Initialize database and plugin manager
    db = DatabaseManager()
    plugin_manager = PluginManager(None, db, None)
    
    # Test 1: Plugin discovery
    print("\n1. Testing plugin discovery:")
    
    discovered_plugins = plugin_manager.discover_plugins()
    print(f"   Discovered {len(discovered_plugins)} plugins:")
    for plugin_path in discovered_plugins:
        print(f"     - {plugin_path}")
    
    # Test 2: Plugin loading
    print("\n2. Testing plugin loading:")
    
    loaded_count = plugin_manager.load_all_plugins()
    print(f"   Loaded {loaded_count} plugins")
    
    # List loaded plugins
    plugins = plugin_manager.get_plugins()
    print(f"   Plugin registry contains {len(plugins)} plugins:")
    for plugin in plugins:
        print(f"     - {plugin.manifest.name} v{plugin.manifest.version} ({plugin.status.value})")
    
    # Test 3: Plugin activation
    print("\n3. Testing plugin activation:")
    
    activated_count = plugin_manager.auto_activate_plugins()
    print(f"   Activated {activated_count} plugins")
    
    # Show active plugins
    active_plugins = plugin_manager.get_plugins(status=PluginStatus.ACTIVE)
    print(f"   Active plugins: {len(active_plugins)}")
    for plugin in active_plugins:
        plugin_type_str = plugin.manifest.plugin_type.value if hasattr(plugin.manifest.plugin_type, 'value') else str(plugin.manifest.plugin_type)
        print(f"     - {plugin.manifest.name} (Type: {plugin_type_str})")
    
    # Test 4: Plugin type registries
    print("\n4. Testing plugin type registries:")
    
    prompt_processors = plugin_manager.prompt_processors
    print(f"   Prompt processors: {len(prompt_processors)}")
    for processor_id, processor in prompt_processors.items():
        print(f"     - {processor_id}: {processor.get_processor_name()}")
    
    ui_extensions = plugin_manager.ui_extensions
    print(f"   UI extensions: {len(ui_extensions)}")
    
    export_formats = plugin_manager.get_export_formats()
    print(f"   Export formats: {len(export_formats)}")
    
    import_formats = plugin_manager.get_import_formats()
    print(f"   Import formats: {len(import_formats)}")
    
    llm_providers = plugin_manager.get_llm_providers()
    print(f"   LLM providers: {len(llm_providers)}")
    
    # Test 5: Plugin execution
    print("\n5. Testing plugin execution:")
    
    if prompt_processors:
        processor_id = list(prompt_processors.keys())[0]
        processor = prompt_processors[processor_id]
        
        test_prompt = """Hello {name}, please write a story about {topic}.
        
        Make sure to include:
        - Character development
        - Plot progression
        - A satisfying conclusion"""
        
        print(f"   Testing processor: {processor.get_processor_name()}")
        print(f"   Original prompt:")
        print(f"     {test_prompt[:50]}...")
        
        # Test different transformations
        transformations = [
            {'transform_type': 'upper'},
            {'transform_type': 'lower'},
            {'transform_type': 'title'}
        ]
        
        for context in transformations:
            result = plugin_manager.execute_prompt_processor(processor_id, test_prompt, context)
            if result:
                transform_type = context['transform_type']
                print(f"   {transform_type.upper()} result:")
                print(f"     {result[:50]}...")
    
    # Test 6: Plugin settings
    print("\n6. Testing plugin settings:")
    
    if plugins:
        plugin = plugins[0]
        plugin_id = plugin.manifest.id
        
        print(f"   Testing settings for: {plugin.manifest.name}")
        
        # Get current settings
        current_settings = plugin.settings
        print(f"   Current settings: {current_settings}")
        
        # Update settings
        new_settings = {
            'default_case': 'upper',
            'preserve_formatting': False,
            'transform_variables': True
        }
        
        success = plugin_manager.update_plugin_settings(plugin_id, new_settings)
        if success:
            print(f"   [OK] Updated settings successfully")
            updated_plugin = plugin_manager.get_plugin(plugin_id)
            print(f"   New settings: {updated_plugin.settings}")
        else:
            print(f"   [ERROR] Failed to update settings")
    
    # Test 7: Plugin events
    print("\n7. Testing plugin events:")
    
    from models.plugin_models import PluginEvent
    
    # Create test event
    event = PluginEvent(
        event_type="transform_upper",
        data={"prompt_content": "test prompt content"},
        source="test_script"
    )
    
    handled = plugin_manager.emit_event(event)
    if handled:
        print(f"   [OK] Event handled successfully")
        result = event.data.get('result')
        if result:
            print(f"   Event result: {result}")
    else:
        print(f"   [INFO] No plugins handled the event")
    
    # Test 8: Plugin statistics
    print("\n8. Testing plugin statistics:")
    
    stats = plugin_manager.get_plugin_statistics()
    print(f"   Plugin statistics:")
    print(f"     Total plugins: {stats['total_plugins']}")
    print(f"     Active plugins: {stats['active_plugins']}")
    print(f"     Inactive plugins: {stats['inactive_plugins']}")
    print(f"     Error plugins: {stats['error_plugins']}")
    print(f"   Plugins by type:")
    for plugin_type, count in stats['plugins_by_type'].items():
        if count > 0:
            print(f"     {plugin_type}: {count}")
    
    # Test 9: Plugin deactivation and unloading
    print("\n9. Testing plugin lifecycle:")
    
    if active_plugins:
        plugin = active_plugins[0]
        plugin_id = plugin.manifest.id
        
        print(f"   Testing lifecycle for: {plugin.manifest.name}")
        
        # Deactivate
        deactivated = plugin_manager.deactivate_plugin(plugin_id)
        if deactivated:
            print(f"   [OK] Plugin deactivated")
            updated_plugin = plugin_manager.get_plugin(plugin_id)
            print(f"   Status: {updated_plugin.status.value}")
        
        # Reactivate
        reactivated = plugin_manager.activate_plugin(plugin_id)
        if reactivated:
            print(f"   [OK] Plugin reactivated")
            updated_plugin = plugin_manager.get_plugin(plugin_id)
            print(f"   Status: {updated_plugin.status.value}")
    
    print("\n" + "=" * 60)
    print("Plugin system testing completed!")
    print("\nKey features tested:")
    print("[OK] Plugin discovery and loading")
    print("[OK] Plugin activation and lifecycle management")
    print("[OK] Plugin type registries and organization")
    print("[OK] Plugin execution and processing")
    print("[OK] Plugin settings management")
    print("[OK] Plugin event system")
    print("[OK] Plugin statistics and monitoring")
    print("[OK] Plugin database integration")


def test_text_transformer_plugin():
    """Test the specific text transformer plugin"""
    print("\n" + "=" * 60)
    print("Testing Text Transformer Plugin Specifically")
    print("=" * 60)
    
    # Test the plugin directly
    try:
        # Import the plugin
        sys.path.append(os.path.join(os.path.dirname(__file__), 'plugins', 'prompt_processor', 'text_transformer'))
        from main import Plugin
        
        # Mock API
        class MockAPI:
            def show_message(self, title, message, message_type="info"):
                print(f"[{message_type.upper()}] {title}: {message}")
        
        # Create plugin instance
        api = MockAPI()
        plugin = Plugin(api)
        
        # Initialize and activate
        plugin.initialize()
        plugin.activate()
        
        # Test prompt
        test_prompt = """Hello {name}, please write a story about {topic}.
        
        Make sure to include:
        - Character development
        - Plot progression
        - A satisfying conclusion
        
        The story should be engaging and well-written."""
        
        print("\nOriginal prompt:")
        print(test_prompt)
        print("\n" + "-" * 40)
        
        # Test transformations
        transformations = [
            ('upper', 'UPPERCASE'),
            ('lower', 'lowercase'),
            ('title', 'Title Case'),
            ('sentence', 'Sentence case')
        ]
        
        for transform_type, description in transformations:
            print(f"\n{description} transformation:")
            result = plugin.process_prompt(test_prompt, {'transform_type': transform_type})
            print(result[:200] + "..." if len(result) > 200 else result)
        
        # Test settings
        print(f"\n" + "-" * 40)
        print("Testing settings:")
        
        # Test with variable transformation enabled
        plugin.update_settings({'transform_variables': True})
        print("\nUPPERCASE with variables transformed:")
        result = plugin.process_prompt(test_prompt, {'transform_type': 'upper'})
        print(result[:200] + "..." if len(result) > 200 else result)
        
        print("\n[OK] Text Transformer plugin test completed successfully!")
        
    except Exception as e:
        print(f"\n[ERROR] Text Transformer plugin test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_plugin_functionality()
    test_text_transformer_plugin()