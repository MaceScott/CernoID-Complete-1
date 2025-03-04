from typing import Dict, Optional, Any, Callable, AsyncGenerator
import asyncio
import pytest
from pathlib import Path
import tempfile
import shutil
import yaml
import json
from ..application import Application
from ..base import BaseComponent
from ..utils.errors import handle_errors

@pytest.fixture
async def test_app(request) -> AsyncGenerator[Application, None]:
    """Test application fixture"""
    # Create temp config directory
    config_dir = Path(tempfile.mkdtemp())
    
    try:
        # Create test config
        config = {
            'app': {
                'name': 'test_app',
                'testing': True
            },
            'logging': {
                'level': 'DEBUG',
                'format': '%(levelname)s: %(message)s'
            },
            'database': {
                'url': 'sqlite:///:memory:'
            },
            'cache': {
                'backend': 'memory'
            }
        }
        
        # Add custom config from marker
        marker = request.node.get_closest_marker('app_config')
        if marker:
            config.update(marker.kwargs)
            
        # Write config file
        config_file = config_dir / 'config.yaml'
        with open(config_file, 'w') as f:
            yaml.dump(config, f)
            
        # Create and initialize app
        app = Application(str(config_dir))
        await app.initialize()
        
        yield app
        
        # Cleanup
        await app.cleanup()
        
    finally:
        shutil.rmtree(config_dir)

@pytest.fixture
def component_config() -> Dict:
    """Base component configuration"""
    return {
        'logging': {
            'level': 'DEBUG'
        }
    }

@pytest.fixture
async def test_component(
    test_app: Application,
    component_config: Dict
) -> AsyncGenerator[BaseComponent, None]:
    """Test component fixture"""
    # Create component
    component = BaseComponent(component_config)
    component.app = test_app
    
    # Initialize
    await component.initialize()
    
    yield component
    
    # Cleanup
    await component.cleanup()

@pytest.fixture
async def test_database(test_app: Application):
    """Test database fixture"""
    db = test_app.get_component('database')
    
    # Create tables
    await db.create_all()
    
    yield db
    
    # Drop tables
    await db.drop_all()

@pytest.fixture
async def test_cache(test_app: Application):
    """Test cache fixture"""
    cache = test_app.get_component('cache_manager')
    
    yield cache
    
    # Clear cache
    await cache.clear()

@pytest.fixture
def mock_component(monkeypatch):
    """Mock component fixture"""
    
    def _mock_component(name: str,
                       methods: Optional[Dict] = None):
        """Create mock component"""
        methods = methods or {}
        
        class MockComponent(BaseComponent):
            def __init__(self):
                self.calls = []
                
            async def initialize(self):
                pass
                
            async def cleanup(self):
                pass
                
            def __getattr__(self, attr):
                if attr in methods:
                    return methods[attr]
                    
                async def mock_method(*args, **kwargs):
                    self.calls.append({
                        'method': attr,
                        'args': args,
                        'kwargs': kwargs
                    })
                return mock_method
                
        component = MockComponent()
        monkeypatch.setattr(
            test_app.components,
            name,
            component
        )
        return component
        
    return _mock_component 