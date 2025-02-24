from typing import Any, Dict, List, Optional, Union, Callable
import re
from datetime import datetime
from jsonschema import validate, ValidationError
from ..utils.errors import ValidationError as AppValidationError

class RequestValidator:
    """Request data validation"""
    
    def __init__(self):
        self._schemas: Dict[str, Dict[str, Any]] = {}
        self._custom_validators: Dict[str, Callable] = {}

    def add_schema(self, name: str, schema: Dict[str, Any]) -> None:
        """
        Add JSON schema for validation
        
        Args:
            name: Schema identifier
            schema: JSON schema definition
        """
        if not name or not isinstance(name, str):
            raise ValueError("Schema name must be a non-empty string")
        if not schema or not isinstance(schema, dict):
            raise ValueError("Schema must be a non-empty dictionary")
            
        self._schemas[name] = schema

    def add_validator(self, name: str, validator: Callable) -> None:
        """
        Add custom validator function
        
        Args:
            name: Validator identifier
            validator: Callable validation function
        """
        if not name or not isinstance(name, str):
            raise ValueError("Validator name must be a non-empty string")
        if not callable(validator):
            raise ValueError("Validator must be a callable")
            
        self._custom_validators[name] = validator

    def validate(self, data: Any, schema_name: str) -> None:
        """
        Validate data against registered schema
        
        Args:
            data: Data to validate
            schema_name: Name of schema to validate against
            
        Raises:
            AppValidationError: If validation fails
        """
        if schema_name not in self._schemas:
            raise AppValidationError(f"Schema not found: {schema_name}")
            
        try:
            validate(instance=data, schema=self._schemas[schema_name])
        except ValidationError as e:
            raise AppValidationError(str(e))

    def validate_type(self, value: Any, expected_type: Union[type, tuple], field_name: str) -> None:
        """
        Validate value type
        
        Args:
            value: Value to validate
            expected_type: Expected type or tuple of types
            field_name: Name of field being validated
        """
        if not isinstance(value, expected_type):
            raise AppValidationError(
                f"Invalid type for {field_name}. "
                f"Expected {expected_type}, got {type(value)}"
            )

    def validate_range(
        self,
        value: Union[int, float],
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None,
        field_name: str
    ) -> None:
        """
        Validate numeric range
        
        Args:
            value: Number to validate
            min_value: Optional minimum value
            max_value: Optional maximum value
            field_name: Name of field being validated
        """
        if min_value is not None and value < min_value:
            raise AppValidationError(f"{field_name} must be >= {min_value}")
        if max_value is not None and value > max_value:
            raise AppValidationError(f"{field_name} must be <= {max_value}")

    def validate_length(
        self,
        value: Union[str, List, Dict],
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        field_name: str
    ) -> None:
        """
        Validate length of string or collection
        
        Args:
            value: Value to validate length
            min_length: Optional minimum length
            max_length: Optional maximum length
            field_name: Name of field being validated
        """
        length = len(value)
        if min_length is not None and length < min_length:
            raise AppValidationError(f"{field_name} length must be >= {min_length}")
        if max_length is not None and length > max_length:
            raise AppValidationError(f"{field_name} length must be <= {max_length}")

    def validate_pattern(self, value: str, pattern: str, field_name: str) -> None:
        """
        Validate string pattern
        
        Args:
            value: String to validate
            pattern: Regex pattern to match
            field_name: Name of field being validated
        """
        if not isinstance(value, str):
            raise AppValidationError(f"{field_name} must be a string")
        if not re.match(pattern, value):
            raise AppValidationError(f"{field_name} does not match pattern: {pattern}")

    def validate_email(self, email: str) -> None:
        """
        Validate email address format
        
        Args:
            email: Email address to validate
        """
        if not isinstance(email, str):
            raise AppValidationError("Email must be a string")
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        self.validate_pattern(email, pattern, 'email')

    def validate_date(self, date_str: str, format: str = '%Y-%m-%d') -> None:
        """
        Validate date string format
        
        Args:
            date_str: Date string to validate
            format: Expected date format
        """
        if not isinstance(date_str, str):
            raise AppValidationError("Date must be a string")
        try:
            datetime.strptime(date_str, format)
        except ValueError:
            raise AppValidationError(f"Invalid date format. Expected {format}")

    def validate_custom(self, data: Any, validator_name: str, **kwargs) -> None:
        """
        Run custom validator
        
        Args:
            data: Data to validate
            validator_name: Name of custom validator to use
            **kwargs: Additional arguments for validator
        """
        if validator_name not in self._custom_validators:
            raise AppValidationError(f"Validator not found: {validator_name}")
            
        validator = self._custom_validators[validator_name]
        validator(data, **kwargs) 