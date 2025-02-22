from typing import Dict, Optional, Any, List, Type, Union
import json
from enum import Enum
from pydantic import BaseModel, Field, ValidationError
from ..base import BaseComponent
from ..utils.errors import handle_errors
import re
from datetime import datetime

class ConfigType(str, Enum):
    """Configuration value types"""
    STRING = 'string'
    INTEGER = 'integer'
    FLOAT = 'float'
    BOOLEAN = 'boolean'
    ARRAY = 'array'
    OBJECT = 'object'
    DATETIME = 'datetime'
    ENUM = 'enum'

class ConfigSchema(BaseModel):
    """Configuration schema definition"""
    type: ConfigType
    description: Optional[str] = None
    default: Optional[Any] = None
    required: bool = False
    items: Optional['ConfigSchema'] = None
    properties: Optional[Dict[str, 'ConfigSchema']] = None
    enum: Optional[List[Any]] = None
    minimum: Optional[float] = None
    maximum: Optional[float] = None
    pattern: Optional[str] = None

class SchemaValidator(BaseComponent):
    """Configuration schema validation"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._schemas: Dict[str, ConfigSchema] = {}
        self._validators: Dict[str, Type[BaseModel]] = {}
        self._types = {
            'string': str,
            'integer': int,
            'float': float,
            'boolean': bool,
            'array': list,
            'object': dict,
            'datetime': datetime,
            'enum': Enum
        }

    async def initialize(self) -> None:
        """Initialize schema validator"""
        # Load schema definitions
        await self._load_schemas()

    async def cleanup(self) -> None:
        """Cleanup validator resources"""
        self._schemas.clear()
        self._validators.clear()

    @handle_errors(logger=None)
    def add_schema(self,
                  name: str,
                  schema: Union[Dict, ConfigSchema]) -> None:
        """Add configuration schema"""
        if isinstance(schema, dict):
            schema = ConfigSchema(**schema)
            
        self._schemas[name] = schema
        
        # Create validator
        self._validators[name] = self._create_validator(schema)

    def remove_schema(self, name: str) -> None:
        """Remove configuration schema"""
        self._schemas.pop(name, None)
        self._validators.pop(name, None)

    @handle_errors(logger=None)
    def validate(self,
                name: str,
                config: Dict) -> Dict:
        """Validate configuration against schema"""
        if name not in self._validators:
            raise ValueError(f"Schema not found: {name}")
            
        try:
            # Validate with Pydantic model
            validator = self._validators[name]
            validated = validator(**config)
            return validated.dict()
            
        except ValidationError as e:
            raise ValueError(str(e))

    def get_schema(self,
                  name: Optional[str] = None) -> Union[Dict, ConfigSchema]:
        """Get configuration schema"""
        if name:
            return self._schemas.get(name)
        return self._schemas

    def _create_validator(self,
                        schema: ConfigSchema) -> Type[BaseModel]:
        """Create Pydantic validator model"""
        fields = {}
        
        if schema.type == ConfigType.OBJECT:
            # Create nested validators
            for name, prop in (schema.properties or {}).items():
                validator = self._create_validator(prop)
                fields[name] = (
                    Optional[validator]
                    if not prop.required
                    else validator
                )
                
        elif schema.type == ConfigType.ARRAY:
            # Create list validator
            if schema.items:
                validator = self._create_validator(schema.items)
                fields['__root__'] = (List[validator], ...)
                
        else:
            # Create field validator
            python_type = self._get_python_type(schema.type)
            fields['__root__'] = (
                python_type,
                Field(
                    default=schema.default,
                    description=schema.description
                )
            )
            
        # Create model class
        return type(
            'ConfigValidator',
            (BaseModel,),
            fields
        )

    def _get_python_type(self,
                        config_type: ConfigType) -> Type:
        """Get Python type for config type"""
        return self._types.get(config_type, str)

    async def _load_schemas(self) -> None:
        """Load schema definitions"""
        try:
            config = self.app.get_component('config_manager')
            if not config:
                return
                
            schemas = config.get('config.schemas', {})
            for name, schema in schemas.items():
                self.add_schema(name, schema)
                
        except Exception as e:
            self.logger.error(f"Failed to load schemas: {str(e)}")

    def validate_config(self, data: Dict) -> List[str]:
        """Validate config data against schema"""
        errors = []
        self._validate_dict(data, self.get_schema(), '', errors)
        return errors

    def _validate_dict(self,
                      data: Dict,
                      schema: Dict,
                      path: str,
                      errors: List[str]) -> None:
        """Validate dictionary against schema"""
        # Check required fields
        for key, field in schema.items():
            if field.get('required', False):
                if key not in data:
                    errors.append(
                        f"Missing required field: {self._get_path(path, key)}"
                    )
                    
        # Validate fields
        for key, value in data.items():
            if key not in schema:
                if not schema.get('additional_properties', False):
                    errors.append(
                        f"Unknown field: {self._get_path(path, key)}"
                    )
                continue
                
            field = schema[key]
            field_path = self._get_path(path, key)
            
            # Validate type
            if not self._validate_type(value, field, field_path, errors):
                continue
                
            # Validate nested object
            if field['type'] == ConfigType.OBJECT and 'properties' in field:
                if not isinstance(value, dict):
                    continue
                self._validate_dict(
                    value,
                    field['properties'],
                    field_path,
                    errors
                )
                
            # Validate array items
            elif field['type'] == ConfigType.ARRAY and 'items' in field:
                if not isinstance(value, list):
                    continue
                for i, item in enumerate(value):
                    item_path = f"{field_path}[{i}]"
                    if not self._validate_type(
                        item,
                        field['items'],
                        item_path,
                        errors
                    ):
                        continue

    def _validate_type(self,
                      value: Any,
                      field: Dict,
                      path: str,
                      errors: List[str]) -> bool:
        """Validate field type"""
        field_type = field['type']
        
        # Check type
        if field_type in self._types:
            expected_type = self._types[field_type]
            if not isinstance(value, expected_type):
                errors.append(
                    f"Invalid type for {path}: "
                    f"expected {field_type}, got {type(value).__name__}"
                )
                return False
                
        # Validate string
        if field_type == ConfigType.STRING:
            # Check pattern
            if 'pattern' in field:
                if not re.match(field['pattern'], value):
                    errors.append(
                        f"Invalid format for {path}: "
                        f"does not match pattern {field['pattern']}"
                    )
                    
            # Check length
            if 'min_length' in field and len(value) < field['min_length']:
                errors.append(
                    f"Invalid length for {path}: "
                    f"minimum length is {field['min_length']}"
                )
            if 'max_length' in field and len(value) > field['max_length']:
                errors.append(
                    f"Invalid length for {path}: "
                    f"maximum length is {field['max_length']}"
                )
                
        # Validate number
        elif field_type in (ConfigType.INTEGER, ConfigType.FLOAT):
            if 'minimum' in field and value < field['minimum']:
                errors.append(
                    f"Invalid value for {path}: "
                    f"minimum value is {field['minimum']}"
                )
            if 'maximum' in field and value > field['maximum']:
                errors.append(
                    f"Invalid value for {path}: "
                    f"maximum value is {field['maximum']}"
                )
                
        # Validate enum
        elif field_type == ConfigType.ENUM:
            if 'values' in field and value not in field['values']:
                errors.append(
                    f"Invalid value for {path}: "
                    f"must be one of {field['values']}"
                )
                
        # Validate array
        elif field_type == ConfigType.ARRAY:
            if 'min_items' in field and len(value) < field['min_items']:
                errors.append(
                    f"Invalid length for {path}: "
                    f"minimum items is {field['min_items']}"
                )
            if 'max_items' in field and len(value) > field['max_items']:
                errors.append(
                    f"Invalid length for {path}: "
                    f"maximum items is {field['max_items']}"
                )
                
        return True

    def _get_path(self, base: str, key: str) -> str:
        """Get field path"""
        return f"{base}.{key}" if base else key 