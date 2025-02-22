from typing import Dict, List, Optional, Any, Union, Callable, Type
import asyncio
import logging
from dataclasses import dataclass
import importlib
import inspect
import pkgutil
import yaml
from pathlib import Path
import sys
from abc import ABC, abstractmethod
from ..base import BaseComponent
from ..utils.errors import handle_errors
import pkg_resources

@dataclass
class PluginMetadata:
    """Plugin metadata"""
    name: str
    version: str
    description: str
    author: str
    dependencies: List[str] = None
    config_schema: Dict = None
    enabled: bool = True
    priority: int = 100

class PluginBase(ABC):
    """Base class for plugins"""
    
    @abstractmethod
    async def initialize(self, config: Dict) -> None:
        """Initialize plugin"""
        pass
        
    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup plugin resources"""
        pass

class PluginManager(BaseComponent):
    """Advanced plugin management system"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._plugins: Dict[str, 'Plugin'] = {}
        self._hooks: Dict[str, List[Any]] = {}
        self._disabled: List[str] = self.config.get('plugins.disabled', [])
        self._plugin_dir = Path(
            self.config.get('plugins.directory', 'plugins')
        )
        self._auto_discover = self.config.get('plugins.auto_discover', True)
        self._hot_reload = self.config.get('plugins.hot_reload', False)
        self._watch_interval = self.config.get('plugins.watch_interval', 1)
        self._stats = {
            'loaded': 0,
            'enabled': 0,
            'errors': 0
        }

    async def initialize(self) -> None:
        """Initialize plugin manager"""
        # Create plugin directory
        self._plugin_dir.mkdir(parents=True, exist_ok=True)
        
        # Load plugins
        if self._auto_discover:
            await self.discover()
            
        # Start hot reload watcher
        if self._hot_reload:
            asyncio.create_task(self._watch_task())

    async def cleanup(self) -> None:
        """Cleanup plugin resources"""
        # Unload all plugins
        for name in list(self._plugins.keys()):
            await self.unload(name)
            
        self._plugins.clear()
        self._hooks.clear()

    @handle_errors(logger=None)
    async def discover(self) -> None:
        """Discover and load plugins"""
        try:
            # Load from plugin directory
            for path in self._plugin_dir.glob('*.py'):
                if path.stem == '__init__':
                    continue
                    
                await self.load_from_path(path)
                
            # Load from entry points
            for entry_point in pkg_resources.iter_entry_points('app.plugins'):
                await self.load(
                    entry_point.name,
                    entry_point.load()
                )
                
        except Exception as e:
            self.logger.error(f"Plugin discovery error: {str(e)}")
            self._stats['errors'] += 1

    @handle_errors(logger=None)
    async def load(self,
                  name: str,
                  plugin_class: Type['Plugin']) -> bool:
        """Load plugin"""
        try:
            # Check if already loaded
            if name in self._plugins:
                return False
                
            # Check if disabled
            if name in self._disabled:
                return False
                
            # Create plugin instance
            plugin = plugin_class(self.app)
            
            # Initialize plugin
            await plugin.initialize()
            
            # Register hooks
            self._register_hooks(plugin)
            
            # Store plugin
            self._plugins[name] = plugin
            
            self._stats['loaded'] += 1
            self._stats['enabled'] += 1
            
            # Emit event
            await self.app.events.emit(
                'plugin.loaded',
                {'name': name}
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Plugin load error: {str(e)}")
            self._stats['errors'] += 1
            return False

    @handle_errors(logger=None)
    async def unload(self, name: str) -> bool:
        """Unload plugin"""
        try:
            if name not in self._plugins:
                return False
                
            plugin = self._plugins[name]
            
            # Cleanup plugin
            await plugin.cleanup()
            
            # Remove hooks
            self._unregister_hooks(plugin)
            
            # Remove plugin
            del self._plugins[name]
            
            self._stats['loaded'] -= 1
            self._stats['enabled'] -= 1
            
            # Emit event
            await self.app.events.emit(
                'plugin.unloaded',
                {'name': name}
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Plugin unload error: {str(e)}")
            self._stats['errors'] += 1
            return False

    @handle_errors(logger=None)
    async def reload(self, name: str) -> bool:
        """Reload plugin"""
        try:
            if name not in self._plugins:
                return False
                
            plugin = self._plugins[name]
            plugin_class = plugin.__class__
            
            # Unload plugin
            await self.unload(name)
            
            # Reload module
            module = importlib.reload(
                inspect.getmodule(plugin_class)
            )
            
            # Get updated plugin class
            plugin_class = getattr(
                module,
                plugin_class.__name__
            )
            
            # Load plugin
            return await self.load(name, plugin_class)
            
        except Exception as e:
            self.logger.error(f"Plugin reload error: {str(e)}")
            self._stats['errors'] += 1
            return False

    def get_plugin(self, name: str) -> Optional['Plugin']:
        """Get plugin instance"""
        return self._plugins.get(name)

    def list_plugins(self) -> List[str]:
        """List loaded plugins"""
        return list(self._plugins.keys())

    async def call_hook(self,
                       name: str,
                       *args,
                       **kwargs) -> List[Any]:
        """Call plugin hook"""
        if name not in self._hooks:
            return []
            
        results = []
        for hook in self._hooks[name]:
            try:
                if inspect.iscoroutinefunction(hook):
                    result = await hook(*args, **kwargs)
                else:
                    result = hook(*args, **kwargs)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Hook error: {str(e)}")
                self._stats['errors'] += 1
                
        return results

    async def get_stats(self) -> Dict[str, Any]:
        """Get plugin statistics"""
        return self._stats.copy()

    async def load_from_path(self, path: Path) -> bool:
        """Load plugin from file path"""
        try:
            # Import module
            spec = importlib.util.spec_from_file_location(
                path.stem,
                path
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find plugin class
            for item in dir(module):
                obj = getattr(module, item)
                if (inspect.isclass(obj) and
                    issubclass(obj, Plugin) and
                    obj != Plugin):
                    return await self.load(path.stem, obj)
                    
            return False
            
        except Exception as e:
            self.logger.error(f"Plugin load error: {str(e)}")
            self._stats['errors'] += 1
            return False

    def _register_hooks(self, plugin: 'Plugin') -> None:
        """Register plugin hooks"""
        for name, method in inspect.getmembers(plugin):
            if hasattr(method, '_hook'):
                hook_name = getattr(method, '_hook')
                if hook_name not in self._hooks:
                    self._hooks[hook_name] = []
                self._hooks[hook_name].append(method)

    def _unregister_hooks(self, plugin: 'Plugin') -> None:
        """Unregister plugin hooks"""
        for name, hooks in list(self._hooks.items()):
            self._hooks[name] = [
                h for h in hooks
                if not hasattr(h, '__self__') or
                h.__self__ != plugin
            ]
            if not self._hooks[name]:
                del self._hooks[name]

    async def _watch_task(self) -> None:
        """Watch for plugin changes"""
        last_modified = {}
        
        while True:
            try:
                # Check plugin files
                for path in self._plugin_dir.glob('*.py'):
                    if path.stem == '__init__':
                        continue
                        
                    mtime = path.stat().st_mtime
                    if path in last_modified:
                        if mtime > last_modified[path]:
                            # Reload plugin
                            await self.reload(path.stem)
                            
                    last_modified[path] = mtime
                    
                await asyncio.sleep(self._watch_interval)
                
            except Exception as e:
                self.logger.error(f"Plugin watch error: {str(e)}")
                await asyncio.sleep(self._watch_interval) 