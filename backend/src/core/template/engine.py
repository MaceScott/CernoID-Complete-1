from typing import Dict, Optional, Any, List, Union
import os
from pathlib import Path
import asyncio
from jinja2 import Environment, FileSystemLoader, select_autoescape
from ..base import BaseComponent
from ..utils.errors import handle_errors

class TemplateEngine(BaseComponent):
    """Advanced template engine system"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._env: Optional[Environment] = None
        self._loaders: Dict[str, FileSystemLoader] = {}
        self._globals: Dict[str, Any] = {}
        self._filters: Dict[str, callable] = {}
        self._tests: Dict[str, callable] = {}
        self._extensions: List[str] = []
        self._cache: Dict[str, Any] = {}
        self._template_dirs: List[Path] = []
        
        # Load config
        self._cache_size = self.config.get('template.cache_size', 100)
        self._auto_reload = self.config.get('template.auto_reload', True)
        self._default_encoding = self.config.get(
            'template.encoding',
            'utf-8'
        )

    async def initialize(self) -> None:
        """Initialize template engine"""
        # Setup template directories
        template_dirs = self.config.get('template.directories', ['templates'])
        for directory in template_dirs:
            path = Path(directory)
            if path.exists():
                self._template_dirs.append(path)
                
        # Create Jinja environment
        self._env = Environment(
            loader=FileSystemLoader(
                [str(d) for d in self._template_dirs]
            ),
            autoescape=select_autoescape(['html', 'xml']),
            enable_async=True,
            cache_size=self._cache_size,
            auto_reload=self._auto_reload,
            encoding=self._default_encoding
        )
        
        # Register default extensions
        self._register_extensions()
        
        # Register default filters
        self._register_filters()
        
        # Register default tests
        self._register_tests()
        
        # Register default globals
        self._register_globals()

    async def cleanup(self) -> None:
        """Cleanup template engine resources"""
        self._loaders.clear()
        self._globals.clear()
        self._filters.clear()
        self._tests.clear()
        self._cache.clear()
        self._template_dirs.clear()

    @handle_errors(logger=None)
    async def render(self,
                    template: str,
                    context: Optional[Dict] = None,
                    **kwargs) -> str:
        """Render template"""
        if not self._env:
            raise RuntimeError("Template engine not initialized")
            
        # Merge context
        ctx = {}
        if context:
            ctx.update(context)
        ctx.update(kwargs)
        
        # Add request context
        request = ctx.get('request')
        if request:
            ctx.update({
                'url_for': request.url_for,
                'static_url': request.static_url
            })
            
        # Render template
        template = self._env.get_template(template)
        return await template.render_async(**ctx)

    @handle_errors(logger=None)
    async def render_string(self,
                          source: str,
                          context: Optional[Dict] = None,
                          **kwargs) -> str:
        """Render template string"""
        if not self._env:
            raise RuntimeError("Template engine not initialized")
            
        # Merge context
        ctx = {}
        if context:
            ctx.update(context)
        ctx.update(kwargs)
        
        # Render template
        template = self._env.from_string(source)
        return await template.render_async(**ctx)

    def add_directory(self, path: Union[str, Path]) -> None:
        """Add template directory"""
        path = Path(path)
        if not path.exists():
            raise ValueError(f"Directory not found: {path}")
            
        self._template_dirs.append(path)
        
        # Update loader
        if self._env:
            self._env.loader = FileSystemLoader(
                [str(d) for d in self._template_dirs]
            )

    def add_filter(self,
                  name: str,
                  filter_func: callable) -> None:
        """Add template filter"""
        self._filters[name] = filter_func
        if self._env:
            self._env.filters[name] = filter_func

    def add_test(self,
                 name: str,
                 test_func: callable) -> None:
        """Add template test"""
        self._tests[name] = test_func
        if self._env:
            self._env.tests[name] = test_func

    def add_global(self,
                  name: str,
                  value: Any) -> None:
        """Add template global"""
        self._globals[name] = value
        if self._env:
            self._env.globals[name] = value

    def add_extension(self, extension: str) -> None:
        """Add template extension"""
        if extension not in self._extensions:
            self._extensions.append(extension)
            if self._env:
                self._env.add_extension(extension)

    def _register_extensions(self) -> None:
        """Register default extensions"""
        extensions = [
            'jinja2.ext.do',
            'jinja2.ext.loopcontrols',
            'jinja2.ext.with_',
            'jinja2.ext.i18n'
        ]
        for ext in extensions:
            self.add_extension(ext)

    def _register_filters(self) -> None:
        """Register default filters"""
        from .filters import DEFAULT_FILTERS
        for name, func in DEFAULT_FILTERS.items():
            self.add_filter(name, func)

    def _register_tests(self) -> None:
        """Register default tests"""
        from .tests import DEFAULT_TESTS
        for name, func in DEFAULT_TESTS.items():
            self.add_test(name, func)

    def _register_globals(self) -> None:
        """Register default globals"""
        self.add_global('app', self.app)
        self.add_global('config', self.app.config)
        
        # Add URL helpers
        self.add_global('url_for', lambda *a, **kw: '#')
        self.add_global('static_url', lambda *a, **kw: '#') 