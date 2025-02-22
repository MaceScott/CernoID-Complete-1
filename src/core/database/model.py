from typing import Dict, Optional, Any, List, Union, Type, ClassVar
from datetime import datetime
import json

class Model:
    """Base database model"""
    
    # Model configuration
    __table__: ClassVar[str]
    __connection__: ClassVar[str] = 'default'
    __primary_key__: ClassVar[str] = 'id'
    __timestamps__: ClassVar[bool] = True
    __soft_delete__: ClassVar[bool] = False
    
    def __init__(self, **data):
        self._data = {}
        self._original = {}
        self._changed = set()
        
        # Set data
        for key, value in data.items():
            setattr(self, key, value)
            
        # Store original data
        self._original = self._data.copy()

    def __getattr__(self, name: str) -> Any:
        """Get model attribute"""
        if name in self._data:
            return self._data[name]
        raise AttributeError(f"Unknown attribute: {name}")

    def __setattr__(self, name: str, value: Any) -> None:
        """Set model attribute"""
        if name.startswith('_'):
            super().__setattr__(name, value)
            return
            
        self._data[name] = value
        self._changed.add(name)

    @classmethod
    async def find(cls,
                  id: Any,
                  connection: Optional[str] = None) -> Optional['Model']:
        """Find model by primary key"""
        conn = cls._get_connection(connection)
        
        query = f"SELECT * FROM {cls.__table__} WHERE {cls.__primary_key__} = ?"
        result = await conn.fetch_one(query, (id,))
        
        if result:
            return cls(**result)
        return None

    @classmethod
    async def all(cls,
                 connection: Optional[str] = None) -> List['Model']:
        """Get all models"""
        conn = cls._get_connection(connection)
        
        query = f"SELECT * FROM {cls.__table__}"
        results = await conn.fetch_all(query)
        
        return [cls(**row) for row in results]

    @classmethod
    async def create(cls,
                    data: Dict,
                    connection: Optional[str] = None) -> 'Model':
        """Create new model"""
        conn = cls._get_connection(connection)
        
        # Add timestamps
        if cls.__timestamps__:
            now = datetime.utcnow()
            data['created_at'] = now
            data['updated_at'] = now
            
        # Build query
        fields = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        query = f"INSERT INTO {cls.__table__} ({fields}) VALUES ({placeholders})"
        
        # Execute query
        await conn.execute(query, tuple(data.values()))
        
        return cls(**data)

    async def update(self,
                    data: Optional[Dict] = None,
                    connection: Optional[str] = None) -> bool:
        """Update model"""
        if data:
            for key, value in data.items():
                setattr(self, key, value)
                
        if not self._changed:
            return True
            
        conn = self._get_connection(connection)
        
        # Add timestamp
        if self.__timestamps__:
            self.updated_at = datetime.utcnow()
            
        # Build query
        updates = ', '.join([
            f"{field} = ?" for field in self._changed
        ])
        query = f"UPDATE {self.__table__} SET {updates} WHERE {self.__primary_key__} = ?"
        
        # Get values
        values = [self._data[field] for field in self._changed]
        values.append(self._data[self.__primary_key__])
        
        # Execute query
        await conn.execute(query, tuple(values))
        
        # Update original data
        self._original = self._data.copy()
        self._changed.clear()
        
        return True

    async def delete(self,
                    connection: Optional[str] = None) -> bool:
        """Delete model"""
        conn = self._get_connection(connection)
        
        if self.__soft_delete__:
            # Soft delete
            query = f"UPDATE {self.__table__} SET deleted_at = ? WHERE {self.__primary_key__} = ?"
            await conn.execute(
                query,
                (datetime.utcnow(), self._data[self.__primary_key__])
            )
        else:
            # Hard delete
            query = f"DELETE FROM {self.__table__} WHERE {self.__primary_key__} = ?"
            await conn.execute(query, (self._data[self.__primary_key__],))
            
        return True

    def to_dict(self) -> Dict:
        """Convert model to dictionary"""
        return self._data.copy()

    def to_json(self) -> str:
        """Convert model to JSON"""
        return json.dumps(self.to_dict())

    @property
    def is_new(self) -> bool:
        """Check if model is new"""
        return self.__primary_key__ not in self._original

    @property
    def is_changed(self) -> bool:
        """Check if model is changed"""
        return bool(self._changed)

    @classmethod
    def _get_connection(cls,
                       name: Optional[str] = None) -> Any:
        """Get database connection"""
        from .manager import DatabaseManager
        manager = DatabaseManager.instance()
        return manager.connection(name or cls.__connection__) 