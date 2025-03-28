from typing import Dict, Optional, Any, List, Union, Callable
import asyncio
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from ..base import BaseComponent
from ..utils.decorators import handle_errors

class TemplateManager(BaseComponent):
    """Advanced template management system"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._env: Optional[Environment] = None
        self._loaders: Dict[str, FileSystemLoader] = {}
        self._filters: Dict[str, Callable] = {}
        self._globals: Dict[str, Any] = {}
        self._cache: Dict[str, Any] = {}
        self._template_dirs: List[Path] = []
        self._default_encoding = self.config.get('template.encoding', 'utf-8')
        self._cache_size = self.config.get('template.cache_size', 100)
        self._auto_reload = self.config.get('template.auto_reload', True)
        self._stats = {
            'renders': 0,
            'cache_hits': 0,
            'errors': 0
        }

    async def initialize(self) -> None:
        """Initialize template manager"""
        # Setup template directories
        template_dirs = self.config.get('template.directories', ['templates'])
        for directory in template_dirs:
            path = Path(directory)
            path.mkdir(parents=True, exist_ok=True)
            self._template_dirs.append(path)
            
        # Create Jinja environment
        self._env = Environment(
            loader=FileSystemLoader(
                self._template_dirs,
                encoding=self._default_encoding
            ),
            autoescape=select_autoescape(['html', 'xml']),
            enable_async=True,
            cache_size=self._cache_size,
            auto_reload=self._auto_reload
        )
        
        # Load custom filters
        filters = self.config.get('template.filters', {})
        for name, func in filters.items():
            self.add_filter(name, func)
            
        # Load global variables
        globals_ = self.config.get('template.globals', {})
        for name, value in globals_.items():
            self.add_global(name, value)

    async def cleanup(self) -> None:
        """Cleanup template resources"""
        self._loaders.clear()
        self._filters.clear()
        self._globals.clear()
        self._cache.clear()

    @handle_errors(logger=None)
    async def render(self,
                    template: str,
                    context: Optional[Dict] = None,
                    **kwargs) -> str:
        """Render template"""
        try:
            # Get template
            template_obj = self._env.get_template(template)
            
            # Merge context
            ctx = {}
            if context:
                ctx.update(context)
            ctx.update(kwargs)
            
            # Render template
            result = await template_obj.render_async(**ctx)
            
            self._stats['renders'] += 1
            return result
            
        except Exception as e:
            self.logger.error(f"Template render error: {str(e)}")
            self._stats['errors'] += 1
            raise

    @handle_errors(logger=None)
    async def render_string(self,
                          source: str,
                          context: Optional[Dict] = None,
                          **kwargs) -> str:
        """Render template string"""
        try:
            # Create template
            template = self._env.from_string(source)
            
            # Merge context
            ctx = {}
            if context:
                ctx.update(context)
            ctx.update(kwargs)
            
            # Render template
            result = await template.render_async(**ctx)
            
            self._stats['renders'] += 1
            return result
            
        except Exception as e:
            self.logger.error(f"Template string render error: {str(e)}")
            self._stats['errors'] += 1
            raise

    def add_filter(self,
                  name: str,
                  func: Union[Callable, str]) -> None:
        """Add custom template filter"""
        if isinstance(func, str):
            # Import function from string
            module_path, func_name = func.rsplit('.', 1)
            module = importlib.import_module(module_path)
            func = getattr(module, func_name)
            
        self._env.filters[name] = func
        self._filters[name] = func

    def remove_filter(self, name: str) -> None:
        """Remove custom template filter"""
        self._env.filters.pop(name, None)
        self._filters.pop(name, None)

    def add_global(self,
                  name: str,
                  value: Any) -> None:
        """Add global template variable"""
        self._env.globals[name] = value
        self._globals[name] = value

    def remove_global(self, name: str) -> None:
        """Remove global template variable"""
        self._env.globals.pop(name, None)
        self._globals.pop(name, None)

    def add_directory(self,
                     path: Union[str, Path]) -> None:
        """Add template directory"""
        path = Path(path)
        if path not in self._template_dirs:
            path.mkdir(parents=True, exist_ok=True)
            self._template_dirs.append(path)
            
            # Update loader
            self._env.loader = FileSystemLoader(
                self._template_dirs,
                encoding=self._default_encoding
            )

    def list_templates(self,
                      pattern: Optional[str] = None) -> List[str]:
        """List available templates"""
        return self._env.list_templates(pattern)

    def get_template(self, name: str) -> Any:
        """Get template object"""
        return self._env.get_template(name)

    async def get_stats(self) -> Dict[str, Any]:
        """Get template statistics"""
        return self._stats.copy()

    def clear_cache(self) -> None:
        """Clear template cache"""
        self._env.cache.clear()
        self._cache.clear() 