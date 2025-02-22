from typing import Dict, Optional, Any, Callable, Type, Union
import asyncio
import json
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID
from fastapi.testclient import TestClient
from httpx import AsyncClient
from ..application import Application
from ..base import BaseComponent

class TestHelper:
    """Test helper utilities"""
    
    def __init__(self, app: Application):
        self.app = app
        self.client = TestClient(app.fastapi_app)
        self._async_client = None

    async def initialize(self) -> None:
        """Initialize test helper"""
        self._async_client = AsyncClient(
            app=self.app.fastapi_app,
            base_url='http://test'
        )

    async def cleanup(self) -> None:
        """Cleanup test helper"""
        if self._async_client:
            await self._async_client.aclose()

    async def async_client(self) -> AsyncClient:
        """Get async test client"""
        if not self._async_client:
            await self.initialize()
        return self._async_client

    def get_component(self,
                     name: str) -> Optional[BaseComponent]:
        """Get application component"""
        return self.app.get_component(name)

    async def create_test_data(self,
                             model: Type,
                             data: Union[Dict, List[Dict]]) -> None:
        """Create test database records"""
        db = self.get_component('database')
        if not db:
            raise RuntimeError("Database not available")
            
        if isinstance(data, dict):
            data = [data]
            
        for item in data:
            record = model(**item)
            db.add(record)
            
        await db.commit()

    async def cleanup_test_data(self,
                              model: Type) -> None:
        """Cleanup test database records"""
        db = self.get_component('database')
        if not db:
            raise RuntimeError("Database not available")
            
        await db.execute(
            f"DELETE FROM {model.__tablename__}"
        )
        await db.commit()

    def serialize_json(self, obj: Any) -> str:
        """Serialize object to JSON"""
        return json.dumps(
            obj,
            default=self._json_serializer
        )

    def deserialize_json(self, data: str) -> Any:
        """Deserialize JSON to object"""
        return json.loads(
            data,
            object_hook=self._json_deserializer
        )

    async def mock_coro(self,
                       return_value: Any = None) -> Any:
        """Create mock coroutine"""
        return return_value

    def assert_json_equal(self,
                         obj1: Any,
                         obj2: Any) -> None:
        """Assert JSON equality"""
        json1 = self.serialize_json(obj1)
        json2 = self.serialize_json(obj2)
        assert json1 == json2

    def assert_model_equal(self,
                          model1: Any,
                          model2: Any,
                          exclude: Optional[List[str]] = None) -> None:
        """Assert model equality"""
        exclude = exclude or []
        
        for field in model1.__table__.columns:
            if field.name in exclude:
                continue
                
            value1 = getattr(model1, field.name)
            value2 = getattr(model2, field.name)
            assert value1 == value2

    def _json_serializer(self, obj: Any) -> Any:
        """JSON serializer for special types"""
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, UUID):
            return str(obj)
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        return str(obj)

    def _json_deserializer(self, obj: Dict) -> Any:
        """JSON deserializer for special types"""
        for key, value in obj.items():
            if isinstance(value, str):
                try:
                    # Try parsing datetime
                    obj[key] = datetime.fromisoformat(value)
                except ValueError:
                    try:
                        # Try parsing UUID
                        obj[key] = UUID(value)
                    except ValueError:
                        pass
        return obj 