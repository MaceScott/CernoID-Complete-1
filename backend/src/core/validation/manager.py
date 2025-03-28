from typing import Dict, Optional, Any, List, Union, Callable, Type
import asyncio
from datetime import datetime
import re
from ..base import BaseComponent
from ..utils.decorators import handle_errors

class ValidationManager(BaseComponent):
    """Advanced validation management system"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._validators: Dict[str, 'Validator'] = {}
        self._rules: Dict[str, Callable] = {}
        self._custom_types: Dict[str, Type] = {}
        self._cache: Dict[str, Dict] = {}
        self._cache_size = self.config.get('validation.cache_size', 100)
        self._cache_ttl = self.config.get('validation.cache_ttl', 300)
        self._strict_mode = self.config.get('validation.strict', True)
        self._stats = {
            'validations': 0,
            'failures': 0,
            'cache_hits': 0
        }

    async def initialize(self) -> None:
        """Initialize validation manager"""
        # Register built-in rules
        from .rules import BUILT_IN_RULES
        for name, func in BUILT_IN_RULES.items():
            self.add_rule(name, func)
            
        # Register built-in types
        from .types import BUILT_IN_TYPES
        for name, type_class in BUILT_IN_TYPES.items():
            self.add_type(name, type_class)
            
        # Load custom rules
        rules = self.config.get('validation.rules', {})
        for name, func in rules.items():
            self.add_rule(name, func)

    async def cleanup(self) -> None:
        """Cleanup validation resources"""
        self._validators.clear()
        self._rules.clear()
        self._custom_types.clear()
        self._cache.clear()

    @handle_errors(logger=None)
    async def validate(self,
                      data: Any,
                      schema: Dict,
                      context: Optional[Dict] = None) -> Dict[str, List[str]]:
        """Validate data against schema"""
        try:
            # Check cache
            cache_key = self._get_cache_key(data, schema)
            if cache_key in self._cache:
                cache_entry = self._cache[cache_key]
                if datetime.utcnow().timestamp() - cache_entry['timestamp'] < self._cache_ttl:
                    self._stats['cache_hits'] += 1
                    return cache_entry['errors']
                    
            # Create validator
            validator = Validator(
                schema,
                self._rules,
                self._custom_types,
                self._strict_mode
            )
            
            # Validate data
            errors = await validator.validate(data, context or {})
            
            # Update stats
            self._stats['validations'] += 1
            if errors:
                self._stats['failures'] += 1
                
            # Update cache
            self._update_cache(cache_key, errors)
            
            return errors
            
        except Exception as e:
            self.logger.error(f"Validation error: {str(e)}")
            raise

    def add_rule(self,
                name: str,
                func: Union[Callable, str]) -> None:
        """Add validation rule"""
        if isinstance(func, str):
            # Import function from string
            module_path, func_name = func.rsplit('.', 1)
            module = importlib.import_module(module_path)
            func = getattr(module, func_name)
            
        self._rules[name] = func

    def remove_rule(self, name: str) -> None:
        """Remove validation rule"""
        self._rules.pop(name, None)

    def add_type(self,
                name: str,
                type_class: Type) -> None:
        """Add custom type"""
        self._custom_types[name] = type_class

    def remove_type(self, name: str) -> None:
        """Remove custom type"""
        self._custom_types.pop(name, None)

    def create_validator(self,
                       name: str,
                       schema: Dict) -> 'Validator':
        """Create named validator"""
        validator = Validator(
            schema,
            self._rules,
            self._custom_types,
            self._strict_mode
        )
        self._validators[name] = validator
        return validator

    def get_validator(self,
                     name: str) -> Optional['Validator']:
        """Get named validator"""
        return self._validators.get(name)

    async def get_stats(self) -> Dict[str, Any]:
        """Get validation statistics"""
        return self._stats.copy()

    def _get_cache_key(self,
                      data: Any,
                      schema: Dict) -> str:
        """Generate cache key"""
        import hashlib
        import json
        
        # Convert data and schema to JSON
        key_data = {
            'data': data,
            'schema': schema
        }
        key_str = json.dumps(key_data, sort_keys=True)
        
        # Generate MD5 hash
        return hashlib.md5(key_str.encode()).hexdigest()

    def _update_cache(self,
                     key: str,
                     errors: Dict[str, List[str]]) -> None:
        """Update validation cache"""
        self._cache[key] = {
            'errors': errors,
            'timestamp': datetime.utcnow().timestamp()
        }
        
        # Trim cache if needed
        if len(self._cache) > self._cache_size:
            # Remove oldest entries
            sorted_keys = sorted(
                self._cache.keys(),
                key=lambda k: self._cache[k]['timestamp']
            )
            for old_key in sorted_keys[:len(sorted_keys) - self._cache_size]:
                del self._cache[old_key] 