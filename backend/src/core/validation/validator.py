from typing import Dict, List, Optional, Any, Union, Type, Set
import json
from datetime import datetime
import logging
from dataclasses import dataclass
import jsonschema
from jsonschema import validators
import re
from pathlib import Path
from decimal import Decimal
import uuid
from pydantic import BaseModel, ValidationError
from ..base import BaseComponent
from ..utils.errors import handle_errors

@dataclass
class ValidationRule:
    """Validation rule definition"""
    name: str
    schema: Dict
    description: str
    version: str
    required: bool = True
    custom_validators: Optional[Dict[str, callable]] = None

class DataValidator:
    """Data validation system"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger('DataValidator')
        self._rules: Dict[str, ValidationRule] = {}
        self._custom_formats: Dict[str, callable] = {}
        self._schema_store: Dict[str, Dict] = {}
        self._setup_validator()

    def _setup_validator(self) -> None:
        """Setup JSON Schema validator"""
        try:
            # Register custom formats
            self._register_custom_formats()
            
            # Load schema store
            self._load_schema_store()
            
            # Create validator
            self._validator = validators.create(
                meta_schema=self.config.get('meta_schema'),
                validators=self._custom_validators()
            )
            
            self.logger.info("Validator setup completed")
            
        except Exception as e:
            self.logger.error(f"Validator setup failed: {str(e)}")
            raise

    def add_rule(self, rule: ValidationRule) -> None:
        """Add validation rule"""
        try:
            # Validate rule schema
            jsonschema.validate(
                rule.schema,
                self.config['meta_schema']
            )
            
            self._rules[rule.name] = rule
            self.logger.info(f"Added validation rule: {rule.name}")
            
        except Exception as e:
            self.logger.error(f"Failed to add rule: {str(e)}")
            raise

    def validate(self,
                data: Union[Dict, List],
                rule_name: str) -> Dict[str, Any]:
        """Validate data against rule"""
        try:
            rule = self._rules.get(rule_name)
            if not rule:
                raise ValueError(f"Unknown validation rule: {rule_name}")
                
            # Create validation context
            context = {
                "timestamp": datetime.utcnow(),
                "rule": rule_name,
                "errors": [],
                "warnings": []
            }
            
            # Validate against schema
            try:
                self._validator(
                    rule.schema,
                    format_checker=jsonschema.FormatChecker()
                ).validate(data)
            except jsonschema.exceptions.ValidationError as e:
                if rule.required:
                    context["errors"].append(str(e))
                else:
                    context["warnings"].append(str(e))
                    
            # Run custom validators
            if rule.custom_validators:
                for validator_name, validator_func in \
                    rule.custom_validators.items():
                    try:
                        validator_func(data, context)
                    except Exception as e:
                        context["errors"].append(
                            f"Custom validation '{validator_name}' failed: {str(e)}"
                        )
                        
            # Set validation status
            context["valid"] = len(context["errors"]) == 0
            
            return context
            
        except Exception as e:
            self.logger.error(f"Validation failed: {str(e)}")
            raise

    def _register_custom_formats(self) -> None:
        """Register custom format validators"""
        # Email format
        def validate_email(value: str) -> bool:
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            return bool(re.match(pattern, value))
            
        self._custom_formats["email"] = validate_email
        
        # Phone format
        def validate_phone(value: str) -> bool:
            pattern = r'^\+?1?\d{9,15}$'
            return bool(re.match(pattern, value))
            
        self._custom_formats["phone"] = validate_phone
        
        # Date format
        def validate_date(value: str) -> bool:
            try:
                datetime.strptime(value, '%Y-%m-%d')
                return True
            except ValueError:
                return False
                
        self._custom_formats["date"] = validate_date
        
        # Register with JSON Schema
        for format_name, validator in self._custom_formats.items():
            jsonschema.FormatChecker.checks(format_name)(validator)

    def _load_schema_store(self) -> None:
        """Load JSON Schema store"""
        schema_dir = Path(self.config['schema_dir'])
        if not schema_dir.exists():
            return
            
        for schema_file in schema_dir.glob("*.json"):
            try:
                with open(schema_file, 'r') as f:
                    schema = json.load(f)
                    if '$id' in schema:
                        self._schema_store[schema['$id']] = schema
            except Exception as e:
                self.logger.error(
                    f"Failed to load schema {schema_file}: {str(e)}"
                )

    def _custom_validators(self) -> Dict[str, callable]:
        """Create custom validators"""
        validators = {}
        
        # Dependency validator
        def validate_dependencies(validator, dependencies, instance, schema):
            if not isinstance(instance, dict):
                return
                
            for property, dependency in dependencies.items():
                if property in instance:
                    if isinstance(dependency, list):
                        for dep in dependency:
                            if dep not in instance:
                                yield jsonschema.exceptions.ValidationError(
                                    f"'{property}' requires '{dep}'"
                                )
                    else:
                        yield from validator.descend(
                            instance,
                            dependency,
                            schema_path=property
                        )
                        
        validators["dependencies"] = validate_dependencies
        
        # Conditional validator
        def validate_if_then_else(validator, if_then_else, instance, schema):
            if_schema = if_then_else.get("if", {})
            then_schema = if_then_else.get("then", {})
            else_schema = if_then_else.get("else", {})
            
            try:
                validator.validate(instance, if_schema)
                yield from validator.descend(
                    instance,
                    then_schema,
                    schema_path="then"
                )
            except jsonschema.exceptions.ValidationError:
                yield from validator.descend(
                    instance,
                    else_schema,
                    schema_path="else"
                )
                
        validators["if_then_else"] = validate_if_then_else
        
        return validators

    def _resolve_schema_ref(self, ref: str) -> Dict:
        """Resolve JSON Schema reference"""
        if not ref.startswith('#'):
            schema = self._schema_store.get(ref)
            if not schema:
                raise ValueError(f"Unknown schema reference: {ref}")
            return schema
            
        return None  # Let JSON Schema handle local refs 

class Validator(BaseComponent):
    """Advanced validation system"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._rules: Dict[str, Dict[str, List[ValidationRule]]] = {}
        self._models: Dict[str, Type[BaseModel]] = {}
        self._custom_rules: Dict[str, Type[ValidationRule]] = {}
        
        # Register default rules
        self._register_default_rules()

    async def initialize(self) -> None:
        """Initialize validator"""
        # Load validation schemas
        await self._load_schemas()

    async def cleanup(self) -> None:
        """Cleanup validator resources"""
        self._rules.clear()
        self._models.clear()
        self._custom_rules.clear()

    @handle_errors(logger=None)
    async def validate(self,
                      schema: str,
                      data: Dict,
                      context: Optional[Dict] = None) -> Dict[str, List[str]]:
        """Validate data against schema"""
        if schema not in self._rules:
            raise ValueError(f"Schema not found: {schema}")
            
        errors = {}
        context = context or {}
        
        # Validate with rules
        for field, rules in self._rules[schema].items():
            value = data.get(field)
            field_errors = []
            
            for rule in rules:
                error = await rule.validate(value, context)
                if error:
                    field_errors.append(error)
                    
            if field_errors:
                errors[field] = field_errors
                
        # Validate with Pydantic model if exists
        if schema in self._models:
            try:
                self._models[schema](**data)
            except ValidationError as e:
                for error in e.errors():
                    field = '.'.join(str(x) for x in error['loc'])
                    message = error['msg']
                    if field in errors:
                        errors[field].append(message)
                    else:
                        errors[field] = [message]
                        
        return errors

    def add_rule(self,
                 schema: str,
                 field: str,
                 rule: ValidationRule) -> None:
        """Add validation rule"""
        if schema not in self._rules:
            self._rules[schema] = {}
            
        if field not in self._rules[schema]:
            self._rules[schema][field] = []
            
        self._rules[schema][field].append(rule)

    def add_model(self,
                 name: str,
                 model: Type[BaseModel]) -> None:
        """Add Pydantic model"""
        self._models[name] = model

    def register_rule(self,
                     name: str,
                     rule_class: Type[ValidationRule]) -> None:
        """Register custom validation rule"""
        self._custom_rules[name] = rule_class

    def create_rule(self,
                   name: str,
                   **options) -> ValidationRule:
        """Create validation rule instance"""
        if name not in self._custom_rules:
            raise ValueError(f"Rule not found: {name}")
            
        return self._custom_rules[name](**options)

    def _register_default_rules(self) -> None:
        """Register default validation rules"""
        self._custom_rules.update({
            'required': RequiredRule,
            'type': TypeRule,
            'range': RangeRule,
            'regex': RegexRule
        })

    async def _load_schemas(self) -> None:
        """Load validation schemas"""
        config = self.app.get_component('config_manager')
        if not config:
            return
            
        schemas = config.get('validation.schemas', {})
        
        for name, schema in schemas.items():
            # Add rules
            for field, rules in schema.get('rules', {}).items():
                for rule in rules:
                    rule_type = rule.pop('type')
                    self.add_rule(
                        name,
                        field,
                        self.create_rule(rule_type, **rule)
                    )
                    
            # Add model if exists
            model = schema.get('model')
            if model:
                if isinstance(model, str):
                    # Import model class
                    parts = model.split('.')
                    module = __import__(
                        '.'.join(parts[:-1]),
                        fromlist=[parts[-1]]
                    )
                    model = getattr(module, parts[-1])
                    
                self.add_model(name, model) 