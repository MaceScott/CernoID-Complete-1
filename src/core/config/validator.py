from typing import Dict, List, Optional, Any, Union, Type
import json
from pathlib import Path
import logging
from dataclasses import dataclass
import jsonschema
import yaml
import re
from cerberus import Validator
from pydantic import BaseModel, ValidationError
from ..base import BaseComponent
from ..utils.errors import handle_errors

@dataclass
class ValidationSchema:
    """Configuration validation schema"""
    name: str
    schema: Dict
    required: bool = True
    custom_rules: Optional[Dict[str, callable]] = None
    dependencies: Optional[Dict[str, List[str]]] = None

class ConfigValidator(BaseComponent):
    """Configuration validation system"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._schemas: Dict[str, Type[BaseModel]] = {}
        self._rules: Dict[str, Dict] = {}
        self._required: List[str] = []
        
        # Load validation rules
        self._load_validation_rules()

    def register_schema(self,
                       key: str,
                       schema: Type[BaseModel]) -> None:
        """Register validation schema"""
        self._schemas[key] = schema

    def add_rule(self,
                 key: str,
                 rule: Dict) -> None:
        """Add validation rule"""
        self._rules[key] = rule

    def add_required(self, key: str) -> None:
        """Add required configuration key"""
        if key not in self._required:
            self._required.append(key)

    @handle_errors(logger=None)
    async def validate(self, config: Dict) -> None:
        """Validate complete configuration"""
        # Check required keys
        missing = [
            key for key in self._required
            if not self._get_nested(config, key)
        ]
        if missing:
            raise ValueError(
                f"Missing required configuration: {', '.join(missing)}"
            )
            
        # Validate against schemas
        for key, schema in self._schemas.items():
            value = self._get_nested(config, key)
            if value is not None:
                try:
                    schema(**value if isinstance(value, dict) else {'value': value})
                except ValidationError as e:
                    raise ValueError(
                        f"Invalid configuration for {key}: {str(e)}"
                    )
                    
        # Apply validation rules
        for key, rule in self._rules.items():
            value = self._get_nested(config, key)
            if value is not None:
                self._validate_rule(key, value, rule)

    def validate_key(self,
                    key: str,
                    value: Any) -> None:
        """Validate single configuration value"""
        # Check schema
        for schema_key, schema in self._schemas.items():
            if key.startswith(schema_key):
                try:
                    schema(**value if isinstance(value, dict) else {'value': value})
                except ValidationError as e:
                    raise ValueError(
                        f"Invalid configuration for {key}: {str(e)}"
                    )
                    
        # Check rules
        for rule_key, rule in self._rules.items():
            if key.startswith(rule_key):
                self._validate_rule(key, value, rule)

    def _load_validation_rules(self) -> None:
        """Load default validation rules"""
        # Add common validation rules
        self.add_rule('server.port', {
            'type': 'integer',
            'min': 1,
            'max': 65535
        })
        
        self.add_rule('logging.level', {
            'type': 'string',
            'enum': ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        })
        
        self.add_rule('database.pool_size', {
            'type': 'integer',
            'min': 1
        })
        
        # Add required configuration
        self.add_required('server.host')
        self.add_required('server.port')
        self.add_required('database.url')

    def _validate_rule(self,
                      key: str,
                      value: Any,
                      rule: Dict) -> None:
        """Validate value against rule"""
        # Type validation
        if 'type' in rule:
            if rule['type'] == 'integer':
                if not isinstance(value, int):
                    raise ValueError(
                        f"Invalid type for {key}: expected integer"
                    )
            elif rule['type'] == 'string':
                if not isinstance(value, str):
                    raise ValueError(
                        f"Invalid type for {key}: expected string"
                    )
                    
        # Range validation
        if isinstance(value, (int, float)):
            if 'min' in rule and value < rule['min']:
                raise ValueError(
                    f"Value for {key} must be >= {rule['min']}"
                )
            if 'max' in rule and value > rule['max']:
                raise ValueError(
                    f"Value for {key} must be <= {rule['max']}"
                )
                
        # Enum validation
        if 'enum' in rule and value not in rule['enum']:
            raise ValueError(
                f"Invalid value for {key}: must be one of {rule['enum']}"
            )
            
        # Pattern validation
        if 'pattern' in rule:
            if not isinstance(value, str):
                raise ValueError(
                    f"Invalid type for {key}: expected string"
                )
            if not re.match(rule['pattern'], value):
                raise ValueError(
                    f"Invalid format for {key}"
                )

    def _get_nested(self,
                    config: Dict,
                    key: str) -> Optional[Any]:
        """Get nested configuration value"""
        keys = key.split('.')
        value = config
        
        for k in keys:
            if not isinstance(value, dict):
                return None
            value = value.get(k)
            if value is None:
                return None
                
        return value

    def add_schema(self, schema: ValidationSchema) -> None:
        """Add validation schema"""
        try:
            # Validate schema structure
            jsonschema.validate(
                schema.schema,
                self.config.get('meta_schema', {})
            )
            
            self._schemas[schema.name] = schema
            
            # Register custom rules
            if schema.custom_rules:
                for rule_name, rule_func in schema.custom_rules.items():
                    self._validator.register_rule(rule_name, rule_func)
                    
            self.logger.info(f"Added validation schema: {schema.name}")
            
        except Exception as e:
            self.logger.error(f"Schema addition failed: {str(e)}")
            raise

    def validate_config(self,
                       config_data: Dict,
                       schema_name: str) -> Dict[str, List[str]]:
        """Validate configuration data"""
        try:
            schema = self._schemas.get(schema_name)
            if not schema:
                raise ValueError(f"Unknown schema: {schema_name}")
                
            errors = {}
            
            # Basic schema validation
            if not self._validator.validate(config_data, schema.schema):
                errors['schema'] = self._validator.errors
                
            # Check dependencies
            if schema.dependencies:
                dep_errors = self._check_dependencies(
                    config_data,
                    schema.dependencies
                )
                if dep_errors:
                    errors['dependencies'] = dep_errors
                    
            # Custom validation
            custom_errors = self._custom_validation(config_data, schema)
            if custom_errors:
                errors['custom'] = custom_errors
                
            return errors
            
        except Exception as e:
            self.logger.error(f"Configuration validation failed: {str(e)}")
            return {'error': str(e)}

    def validate_file(self, file_path: Union[str, Path]) -> Dict[str, List[str]]:
        """Validate configuration file"""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"Config file not found: {file_path}")
                
            # Load configuration file
            with open(file_path, 'r') as f:
                if file_path.suffix == '.json':
                    config_data = json.load(f)
                elif file_path.suffix in ['.yml', '.yaml']:
                    config_data = yaml.safe_load(f)
                else:
                    raise ValueError(
                        f"Unsupported file format: {file_path.suffix}"
                    )
                    
            # Determine schema from file name
            schema_name = file_path.stem
            return self.validate_config(config_data, schema_name)
            
        except Exception as e:
            self.logger.error(f"File validation failed: {str(e)}")
            return {'error': str(e)}

    def _setup_custom_rules(self) -> None:
        """Setup default custom validation rules"""
        # URL validation
        def validate_url(field, value, error):
            url_pattern = re.compile(
                r'^https?://'  # http:// or https://
                r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+'
                r'(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
                r'localhost|'  # localhost...
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
                r'(?::\d+)?'  # optional port
                r'(?:/?|[/?]\S+)$', re.IGNORECASE
            )
            if not url_pattern.match(value):
                error(field, "Invalid URL format")
                
        self._validator.register_rule('url', validate_url)
        
        # Version validation
        def validate_version(field, value, error):
            version_pattern = re.compile(
                r'^\d+\.\d+\.\d+(?:-[a-zA-Z0-9]+)?$'
            )
            if not version_pattern.match(value):
                error(field, "Invalid version format (e.g., 1.0.0 or 1.0.0-beta)")
                
        self._validator.register_rule('version', validate_version)
        
        # Cron expression validation
        def validate_cron(field, value, error):
            cron_pattern = re.compile(
                r'^(\*|[0-9,\-*/]+)\s+'  # minute
                r'(\*|[0-9,\-*/]+)\s+'  # hour
                r'(\*|[0-9,\-*/]+)\s+'  # day of month
                r'(\*|[0-9,\-*/]+)\s+'  # month
                r'(\*|[0-9,\-*/]+)$'    # day of week
            )
            if not cron_pattern.match(value):
                error(field, "Invalid cron expression")
                
        self._validator.register_rule('cron', validate_cron)

    def _check_dependencies(self,
                          config_data: Dict,
                          dependencies: Dict[str, List[str]]) -> List[str]:
        """Check configuration dependencies"""
        errors = []
        
        for field, required_fields in dependencies.items():
            if field in config_data:
                for required in required_fields:
                    if required not in config_data:
                        errors.append(
                            f"Field '{field}' requires '{required}'"
                        )
                        
        return errors

    def _custom_validation(self,
                          config_data: Dict,
                          schema: ValidationSchema) -> List[str]:
        """Perform custom validation"""
        errors = []
        
        # Port range validation
        if 'port' in config_data:
            port = config_data['port']
            if not (1024 <= port <= 65535):
                errors.append(
                    "Port must be between 1024 and 65535"
                )
                
        # Memory limit validation
        if 'memory_limit' in config_data:
            try:
                limit = self._parse_memory_limit(config_data['memory_limit'])
                if limit < 0:
                    errors.append("Invalid memory limit")
            except ValueError as e:
                errors.append(str(e))
                
        # Timeout validation
        if 'timeout' in config_data:
            timeout = config_data['timeout']
            if not (0 < timeout <= 300):
                errors.append(
                    "Timeout must be between 1 and 300 seconds"
                )
                
        return errors

    def _parse_memory_limit(self, limit: str) -> int:
        """Parse memory limit string to bytes"""
        units = {
            'B': 1,
            'K': 1024,
            'M': 1024 * 1024,
            'G': 1024 * 1024 * 1024
        }
        
        match = re.match(r'^(\d+)([BKMG])$', limit.upper())
        if not match:
            raise ValueError(
                "Invalid memory limit format (e.g., 512M, 2G)"
            )
            
        value, unit = match.groups()
        return int(value) * units[unit]

    def cleanup(self) -> None:
        """Cleanup validator resources"""
        # Cleanup can be extended based on requirements
        pass 