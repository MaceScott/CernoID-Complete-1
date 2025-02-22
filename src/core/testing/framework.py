from typing import Dict, List, Optional, Any, Callable
import asyncio
import pytest
import logging
from pathlib import Path
import json
import yaml
from ..base import BaseComponent
from .client import TestClient
from ..utils.errors import handle_errors

class TestFramework(BaseComponent):
    """Integration test framework"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._client = TestClient(config)
        self._fixtures: Dict[str, Callable] = {}
        self._mocks: Dict[str, Any] = {}
        self._test_data: Dict[str, Any] = {}
        
        # Test configuration
        self._test_path = Path(self.config.get('test.path', 'tests'))
        self._data_path = self._test_path / 'data'
        self._timeout = self.config.get('test.timeout', 30)
        self._parallel = self.config.get('test.parallel', True)

    async def initialize(self) -> None:
        """Initialize test framework"""
        await self._client.initialize()
        self._data_path.mkdir(parents=True, exist_ok=True)
        
        # Load test data
        await self._load_test_data()
        
        # Register core fixtures
        self._register_core_fixtures()

    async def cleanup(self) -> None:
        """Cleanup test framework resources"""
        await self._client.cleanup()
        self._fixtures.clear()
        self._mocks.clear()
        self._test_data.clear()

    def register_fixture(self,
                        name: str,
                        fixture: Callable) -> None:
        """Register test fixture"""
        self._fixtures[name] = fixture

    def register_mock(self,
                     component: str,
                     mock_obj: Any) -> None:
        """Register component mock"""
        self._mocks[component] = mock_obj

    def get_fixture(self, name: str) -> Optional[Callable]:
        """Get test fixture"""
        return self._fixtures.get(name)

    def get_mock(self, component: str) -> Optional[Any]:
        """Get component mock"""
        return self._mocks.get(component)

    def get_test_data(self,
                     name: str,
                     default: Any = None) -> Any:
        """Get test data"""
        return self._test_data.get(name, default)

    @handle_errors(logger=None)
    async def run_tests(self,
                       pattern: str = 'test_*.py',
                       markers: Optional[List[str]] = None) -> Dict:
        """Run integration tests"""
        # Collect test files
        test_files = list(self._test_path.glob(pattern))
        
        # Configure pytest
        pytest_args = [
            str(self._test_path),
            '-v',
            '--asyncio-mode=auto'
        ]
        
        if markers:
            pytest_args.extend(['-m', ' or '.join(markers)])
            
        if self._parallel:
            pytest_args.extend(['-n', 'auto'])
            
        # Run tests
        result = pytest.main(pytest_args)
        
        return {
            'result': result,
            'files': len(test_files),
            'markers': markers
        }

    async def _load_test_data(self) -> None:
        """Load test data files"""
        if not self._data_path.exists():
            return
            
        for data_file in self._data_path.glob('*.yml'):
            with open(data_file) as f:
                self._test_data[data_file.stem] = yaml.safe_load(f)

    def _register_core_fixtures(self) -> None:
        """Register core test fixtures"""
        @pytest.fixture
        async def test_client():
            """Test client fixture"""
            return self._client

        @pytest.fixture
        async def test_data():
            """Test data fixture"""
            return self._test_data

        @pytest.fixture
        async def mock_redis():
            """Redis mock fixture"""
            from unittest.mock import MagicMock
            redis_mock = MagicMock()
            self.register_mock('redis', redis_mock)
            return redis_mock

        self.register_fixture('client', test_client)
        self.register_fixture('data', test_data)
        self.register_fixture('redis_mock', mock_redis) 