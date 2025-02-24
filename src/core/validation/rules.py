"""
Validation rules for data validation.
Organized into categories with consistent error handling and type checking.
"""

from typing import Dict, Optional, Any, List, Pattern, Union, Callable, TypeVar
from datetime import datetime, date
from decimal import Decimal
import re
import uuid
import ipaddress
from dataclasses import dataclass
from enum import Enum
from email_validator import validate_email, EmailNotValidError
from ..utils.errors import handle_errors, ValidationError

T = TypeVar('T')

class RuleCategory(Enum):
    """Categories for validation rules"""
    TYPE = "type"
    STRING = "string"
    NUMBER = "number"
    DATE = "date"
    NETWORK = "network"
    COMPARISON = "comparison"
    CUSTOM = "custom"

@dataclass
class ValidationContext:
    """Context for validation rules"""
    data: Dict[str, Any]
    db: Optional[Any] = None
    user: Optional[Dict[str, Any]] = None
    request: Optional[Any] = None

class BaseRule:
    """Base class for all validation rules"""
    
    def __init__(self, message: Optional[str] = None, category: RuleCategory = None):
        self.message = message
        self.category = category

    @handle_errors
    async def validate(self, value: Any, context: Optional[ValidationContext] = None) -> Optional[str]:
        """Validate the value"""
        raise NotImplementedError

    def _format_message(self, default: str) -> str:
        """Format error message"""
        return self.message or default

class TypeRules:
    """Type validation rules"""

    @staticmethod
    def required(value: Any) -> Optional[str]:
        """Validate required field"""
        if value is None or (isinstance(value, str) and not value.strip()):
            return "Field is required"
        return None

    @staticmethod
    def type_check(value: Any, expected_type: Union[type, tuple]) -> Optional[str]:
        """Validate value type"""
        if value is not None and not isinstance(value, expected_type):
            type_name = getattr(expected_type, '__name__', str(expected_type))
            return f"Must be of type {type_name}"
        return None

class StringRules:
    """String validation rules"""

    @staticmethod
    def length(value: str, min_length: Optional[int] = None, 
               max_length: Optional[int] = None) -> Optional[str]:
        """Validate string length"""
        if value is None:
            return None
            
        length = len(str(value))
        if min_length is not None and length < min_length:
            return f"Must be at least {min_length} characters"
        if max_length is not None and length > max_length:
            return f"Must be at most {max_length} characters"
        return None

    @staticmethod
    def pattern(value: str, regex: Union[str, Pattern]) -> Optional[str]:
        """Validate string pattern"""
        if value is None:
            return None
            
        pattern = re.compile(regex) if isinstance(regex, str) else regex
        if not pattern.match(str(value)):
            return "Invalid format"
        return None

    @staticmethod
    def email(value: str) -> Optional[str]:
        """Validate email address"""
        if value is None:
            return None
            
        try:
            validate_email(str(value))
            return None
        except EmailNotValidError:
            return "Invalid email address"

    @staticmethod
    def url(value: str) -> Optional[str]:
        """Validate URL format"""
        if value is None:
            return None
            
        url_pattern = (
            r'^https?:\/\/(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.'
            r'[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&\/=]*)$'
        )
        if not re.match(url_pattern, str(value)):
            return "Invalid URL"
        return None

class NumberRules:
    """Numeric validation rules"""

    @staticmethod
    def range(value: Union[int, float], 
             min_value: Optional[Union[int, float]] = None,
             max_value: Optional[Union[int, float]] = None) -> Optional[str]:
        """Validate numeric range"""
        if value is None:
            return None
            
        if min_value is not None and value < min_value:
            return f"Must be greater than or equal to {min_value}"
        if max_value is not None and value > max_value:
            return f"Must be less than or equal to {max_value}"
        return None

class DateRules:
    """Date validation rules"""

    @staticmethod
    def date_format(value: str, format_: str = '%Y-%m-%d') -> Optional[str]:
        """Validate date format"""
        if value is None:
            return None
            
        try:
            if isinstance(value, (datetime, date)):
                return None
            datetime.strptime(str(value), format_)
            return None
        except ValueError:
            return f"Must be a valid date in format {format_}"

class NetworkRules:
    """Network-related validation rules"""

    @staticmethod
    def ip_address(value: str) -> Optional[str]:
        """Validate IP address"""
        if value is None:
            return None
            
        try:
            ipaddress.ip_address(str(value))
            return None
        except ValueError:
            return "Invalid IP address"

    @staticmethod
    def uuid_check(value: str) -> Optional[str]:
        """Validate UUID format"""
        if value is None:
            return None
            
        try:
            uuid.UUID(str(value))
            return None
        except ValueError:
            return "Invalid UUID"

class ComparisonRules:
    """Comparison validation rules"""

    @staticmethod
    def choices(value: Any, options: List[Any]) -> Optional[str]:
        """Validate value against choices"""
        if value is not None and value not in options:
            return f"Must be one of: {', '.join(map(str, options))}"
        return None

    @staticmethod
    def compare(value: Any, other: Any, operator: str = '==') -> Optional[str]:
        """Compare values"""
        if value is None:
            return None
            
        operators = {
            '==': lambda x, y: x == y,
            '!=': lambda x, y: x != y,
            '>': lambda x, y: x > y,
            '>=': lambda x, y: x >= y,
            '<': lambda x, y: x < y,
            '<=': lambda x, y: x <= y
        }
        
        if operator not in operators:
            return f"Invalid operator: {operator}"
            
        if not operators[operator](value, other):
            return f"Must be {operator} {other}"
        return None

class CustomRule(BaseRule):
    """Custom validation rule"""
    
    def __init__(self, func: Callable[[Any, Optional[Dict]], Optional[str]], 
                 message: Optional[str] = None):
        super().__init__(message, RuleCategory.CUSTOM)
        self.func = func

    async def validate(self, value: Any, 
                      context: Optional[ValidationContext] = None) -> Optional[str]:
        """Execute custom validation function"""
        try:
            result = self.func(value, context)
            if isinstance(result, bool):
                return None if result else self._format_message("Validation failed")
            return result
        except Exception as e:
            return str(e)

# Register all validation rules
VALIDATION_RULES = {
    # Type rules
    'required': TypeRules.required,
    'type': TypeRules.type_check,
    
    # String rules
    'length': StringRules.length,
    'pattern': StringRules.pattern,
    'email': StringRules.email,
    'url': StringRules.url,
    
    # Number rules
    'range': NumberRules.range,
    
    # Date rules
    'date': DateRules.date_format,
    
    # Network rules
    'ip_address': NetworkRules.ip_address,
    'uuid': NetworkRules.uuid_check,
    
    # Comparison rules
    'choices': ComparisonRules.choices,
    'compare': ComparisonRules.compare
}

# For backward compatibility
BUILT_IN_RULES = VALIDATION_RULES 