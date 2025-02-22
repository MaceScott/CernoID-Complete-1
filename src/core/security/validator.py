from typing import Any, Dict, List, Optional, Union
import re
from datetime import datetime
from jsonschema import validate, ValidationError
from ..utils.errors import ValidationError as AppValidationError

class RequestValidator:
    """Request data validation"""
    
    def __init__(self):
        self._schemas: Dict[str, Dict] = {}
        self._custom_validators: Dict[str, callable] = {}

    def add_schema(self, name: str, schema: Dict) -> None:
        """Add JSON schema"""
        self._schemas[name] = schema

    def add_validator(self,
                     name: str,
                     validator: callable) -> None:
        """Add custom validator"""
        self._custom_validators[name] = validator

    def validate(self,
                data: Any,
                schema_name: str) -> None:
        """Validate data against schema"""
        if schema_name not in self._schemas:
            raise AppValidationError(f"Schema not found: {schema_name}")
            
        try:
            validate(instance=data, schema=self._schemas[schema_name])
        except ValidationError as e:
            raise AppValidationError(str(e))

    def validate_type(self,
                     value: Any,
                     expected_type: Union[type, tuple],
                     field_name: str) -> None:
        """Validate value type"""
        if not isinstance(value, expected_type):
            raise AppValidationError(
                f"Invalid type for {field_name}. "
                f"Expected {expected_type}, got {type(value)}"
            )

    def validate_range(self,
                      value: Union[int, float],
                      min_value: Optional[Union[int, float]] = None,
                      max_value: Optional[Union[int, float]] = None,
                      field_name: str) -> None:
        """Validate numeric range"""
        if min_value is not None and value < min_value:
            raise AppValidationError(
                f"{field_name} must be >= {min_value}"
            )
        if max_value is not None and value > max_value:
            raise AppValidationError(
                f"{field_name} must be <= {max_value}"
            )

    def validate_length(self,
                       value: Union[str, list, dict],
                       min_length: Optional[int] = None,
                       max_length: Optional[int] = None,
                       field_name: str) -> None:
        """Validate length of string or collection"""
        length = len(value)
        if min_length is not None and length < min_length:
            raise AppValidationError(
                f"{field_name} length must be >= {min_length}"
            )
        if max_length is not None and length > max_length:
            raise AppValidationError(
                f"{field_name} length must be <= {max_length}"
            )

    def validate_pattern(self,
                        value: str,
                        pattern: str,
                        field_name: str) -> None:
        """Validate string pattern"""
        if not re.match(pattern, value):
            raise AppValidationError(
                f"{field_name} does not match pattern: {pattern}"
            )

    def validate_email(self, email: str) -> None:
        """Validate email address"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        self.validate_pattern(email, pattern, 'email')

    def validate_date(self,
                     date_str: str,
                     format: str = '%Y-%m-%d') -> None:
        """Validate date string"""
        try:
            datetime.strptime(date_str, format)
        except ValueError:
            raise AppValidationError(
                f"Invalid date format. Expected {format}"
            )

    def validate_custom(self,
                       data: Any,
                       validator_name: str,
                       **kwargs) -> None:
        """Run custom validator"""
        if validator_name not in self._custom_validators:
            raise AppValidationError(
                f"Validator not found: {validator_name}"
            )
            
        validator = self._custom_validators[validator_name]
        validator(data, **kwargs) 