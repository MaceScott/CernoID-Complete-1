from typing import Dict, Optional, Any, Callable
import inspect
from ..base import BaseComponent
from abc import ABC, abstractmethod

def hook(hook_name: str) -> Callable:
    """Decorator to mark plugin hooks"""
    def decorator(func: Callable) -> Callable:
        setattr(func, '_hook', hook_name)
        return func
    return decorator

class PluginBase(ABC):
    """Base class for plugins"""
    
    def __init__(self, app: Any):
        self.app = app
        self.config = {}
        self.logger = None

    async def initialize(self) -> None:
        """Initialize plugin"""
        # Get plugin config
        config = self.app.get_component('config_manager')
        if config:
            plugin_name = self.__class__.__name__.lower()
            self.config = config.get(f'plugins.{plugin_name}', {})
            
        # Get logger
        logger = self.app.get_component('logger')
        if logger:
            self.logger = logger.get_logger(
                f"plugin.{self.__class__.__name__}"
            )

    async def cleanup(self) -> None:
        """Cleanup plugin resources"""
        pass

    @abstractmethod
    async def setup(self) -> None:
        """Setup plugin (must be implemented)"""
        pass

class PluginMount(type):
    """Metaclass for plugin registration"""
    
    def __init__(cls, name, bases, attrs):
        if not hasattr(cls, '_plugins'):
            cls._plugins = {}
        else:
            cls._plugins[name.lower()] = cls

    def get_plugins(cls) -> Dict[str, type]:
        """Get registered plugins"""
        return cls._plugins

class Plugin(PluginBase, metaclass=PluginMount):
    """Plugin implementation class"""
    
    @classmethod
    def create(cls,
              name: str,
              app: Any) -> Optional['Plugin']:
        """Create plugin instance"""
        plugin_cls = cls._plugins.get(name.lower())
        if plugin_cls:
            return plugin_cls(app)
        return None

class EventPlugin(Plugin):
    """Base class for event handling plugins"""
    
    async def setup(self) -> None:
        """Setup event handlers"""
        events = self.app.get_component('event_dispatcher')
        if not events:
            raise RuntimeError("Event dispatcher not available")
            
        # Register event handlers
        for name in dir(self):
            if name.startswith('on_'):
                event = name[3:].replace('_', '.')
                handler = getattr(self, name)
                events.add_handler(event, handler)

class WebPlugin(Plugin):
    """Base class for web handling plugins"""
    
    async def setup(self) -> None:
        """Setup web routes"""
        router = self.app.get_component('router')
        if not router:
            raise RuntimeError("Router not available")
            
        # Register routes
        self.register_routes(router)

    @abstractmethod
    def register_routes(self, router: Any) -> None:
        """Register plugin routes (must be implemented)"""
        pass

class StoragePlugin(Plugin):
    """Base class for storage plugins"""
    
    async def setup(self) -> None:
        """Setup storage"""
        # Initialize storage
        await self.initialize_storage()
        
        # Register cleanup
        self.app.add_cleanup_callback(self.cleanup_storage)

    @abstractmethod
    async def initialize_storage(self) -> None:
        """Initialize storage (must be implemented)"""
        pass

    @abstractmethod
    async def cleanup_storage(self) -> None:
        """Cleanup storage (must be implemented)"""
        pass

    def get_plugin(self, name: str) -> Optional['Plugin']:
        """Get another plugin instance"""
        if not self._manager:
            return None
        return self._manager.get_plugin(name)

    async def execute_hook(self,
                         hook_name: str,
                         *args,
                         **kwargs) -> list:
        """Execute plugin hook"""
        if not self._manager:
            return []
        return await self._manager.execute_hook(
            hook_name,
            *args,
            **kwargs
        )

    async def _init_config(self) -> None:
        """Initialize plugin configuration"""
        # Load plugin-specific config
        plugin_config = self.config.get(f'plugins.{self.name}', {})
        
        # Update configuration defaults
        if hasattr(self.__class__, 'CONFIG_DEFAULTS'):
            defaults = getattr(self.__class__, 'CONFIG_DEFAULTS')
            for key, value in defaults.items():
                if key not in plugin_config:
                    plugin_config[key] = value
                    
        self.config[f'plugins.{self.name}'] = plugin_config

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get plugin configuration value"""
        return self.config.get(
            f'plugins.{self.name}.{key}',
            default
        )

    def set_config(self, key: str, value: Any) -> None:
        """Set plugin configuration value"""
        self.config[f'plugins.{self.name}.{key}'] = value

    @classmethod
    def requires(cls, *plugin_names: str) -> None:
        """Decorator to specify plugin dependencies"""
        if not hasattr(cls, 'DEPENDENCIES'):
            cls.DEPENDENCIES = []
        cls.DEPENDENCIES.extend(plugin_names)

    @classmethod
    def config_defaults(cls, **defaults: Any) -> None:
        """Decorator to specify configuration defaults"""
        if not hasattr(cls, 'CONFIG_DEFAULTS'):
            cls.CONFIG_DEFAULTS = {}
        cls.CONFIG_DEFAULTS.update(defaults)

class Plugin(BaseComponent):
    """Base plugin class"""
    
    def __init__(self, app: Any):
        super().__init__(app.config)
        self.app = app
        self.name = self.__class__.__name__
        self.description = self.__class__.__doc__ or ''
        self.version = getattr(self.__class__, '__version__', '0.1.0')
        self.author = getattr(self.__class__, '__author__', '')
        self._enabled = False

    async def initialize(self) -> None:
        """Initialize plugin"""
        self._enabled = True

    async def cleanup(self) -> None:
        """Cleanup plugin resources"""
        self._enabled = False

    @property
    def enabled(self) -> bool:
        """Check if plugin is enabled"""
        return self._enabled

    def get_info(self) -> Dict[str, Any]:
        """Get plugin information"""
        return {
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'author': self.author,
            'enabled': self.enabled
        }

def config_required(*keys):
    """Config requirement decorator"""
    
    def decorator(func):
        async def wrapper(self, *args, **kwargs):
            for key in keys:
                if key not in self.config:
                    raise ValueError(
                        f"Missing required config: {key}"
                    )
            return await func(self, *args, **kwargs)
            
        return wrapper
        
    return decorator

def plugin_enabled(func):
    """Plugin enabled check decorator"""
    
    async def wrapper(self, *args, **kwargs):
        if not self.enabled:
            raise RuntimeError("Plugin is not enabled")
        return await func(self, *args, **kwargs)
        
    return wrapper 