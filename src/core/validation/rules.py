from typing import Dict, Optional, Any, List, Pattern, Union
import re
from datetime import datetime, date
from decimal import Decimal
import uuid
from email_validator import validate_email, EmailNotValidError
from ..utils.errors import handle_errors
from .validator import ValidationRule
import ipaddress

class EmailRule(ValidationRule):
    """Email validation"""
    
    async def validate(self,
                      value: Any,
                      context: Dict = None) -> Optional[str]:
        if value is None:
            return None
            
        try:
            validate_email(str(value))
        except EmailNotValidError:
            return self.message or "Invalid email address"
            
        return None

class LengthRule(ValidationRule):
    """String length validation"""
    
    def __init__(self,
                 min_: Optional[int] = None,
                 max_: Optional[int] = None,
                 message: Optional[str] = None):
        super().__init__(message)
        self.min = min_
        self.max = max_

    async def validate(self,
                      value: Any,
                      context: Dict = None) -> Optional[str]:
        if value is None:
            return None
            
        length = len(str(value))
        
        if self.min is not None and length < self.min:
            return (
                self.message or
                f"Must be at least {self.min} characters"
            )
            
        if self.max is not None and length > self.max:
            return (
                self.message or
                f"Must be at most {self.max} characters"
            )
            
        return None

class DateRule(ValidationRule):
    """Date validation"""
    
    def __init__(self,
                 format_: str = '%Y-%m-%d',
                 message: Optional[str] = None):
        super().__init__(message)
        self.format = format_

    async def validate(self,
                      value: Any,
                      context: Dict = None) -> Optional[str]:
        if value is None:
            return None
            
        try:
            if isinstance(value, (datetime, date)):
                return None
                
            datetime.strptime(str(value), self.format)
        except ValueError:
            return (
                self.message or
                f"Must be a valid date in format {self.format}"
            )
            
        return None

class ChoiceRule(ValidationRule):
    """Choice validation"""
    
    def __init__(self,
                 choices: List[Any],
                 message: Optional[str] = None):
        super().__init__(message)
        self.choices = choices

    async def validate(self,
                      value: Any,
                      context: Dict = None) -> Optional[str]:
        if value is not None and value not in self.choices:
            return (
                self.message or
                f"Must be one of: {', '.join(map(str, self.choices))}"
            )
            
        return None

class UniqueRule(ValidationRule):
    """Unique field validation"""
    
    def __init__(self,
                 model: str,
                 field: str,
                 message: Optional[str] = None):
        super().__init__(message)
        self.model = model
        self.field = field

    async def validate(self,
                      value: Any,
                      context: Dict = None) -> Optional[str]:
        if value is None:
            return None
            
        db = context.get('db')
        if not db:
            return None
            
        model = db.get_model(self.model)
        if not model:
            return None
            
        exists = await db.exists(
            model,
            **{self.field: value}
        )
        
        if exists:
            return (
                self.message or
                f"Value already exists"
            )
            
        return None

class CompareRule(ValidationRule):
    """Compare fields validation"""
    
    def __init__(self,
                 field: str,
                 operator: str = '==',
                 message: Optional[str] = None):
        super().__init__(message)
        self.field = field
        self.operator = operator

    async def validate(self,
                      value: Any,
                      context: Dict = None) -> Optional[str]:
        if value is None:
            return None
            
        data = context.get('data', {})
        other = data.get(self.field)
        
        if self.operator == '==':
            valid = value == other
        elif self.operator == '!=':
            valid = value != other
        elif self.operator == '>':
            valid = value > other
        elif self.operator == '>=':
            valid = value >= other
        elif self.operator == '<':
            valid = value < other
        elif self.operator == '<=':
            valid = value <= other
        else:
            valid = False
            
        if not valid:
            return (
                self.message or
                f"Must be {self.operator} {self.field}"
            )
            
        return None

class CustomRule(ValidationRule):
    """Custom validation function"""
    
    def __init__(self,
                 func: callable,
                 message: Optional[str] = None):
        super().__init__(message)
        self.func = func

    async def validate(self,
                      value: Any,
                      context: Dict = None) -> Optional[str]:
        try:
            result = self.func(value, context)
            
            if isinstance(result, bool):
                return (
                    None if result
                    else (self.message or "Validation failed")
                )
                
            return result
            
        except Exception as e:
            return str(e)

def required(value: Any,
            param: bool = True) -> Optional[str]:
    """Required field validation"""
    if param and value is None:
        return "Field is required"
    return None

def type_(value: Any,
         type_name: str) -> Optional[str]:
    """Type validation"""
    if value is None:
        return None
        
    if type_name == 'string' and not isinstance(value, str):
        return "Must be a string"
    elif type_name == 'integer' and not isinstance(value, int):
        return "Must be an integer"
    elif type_name == 'float' and not isinstance(value, (int, float)):
        return "Must be a number"
    elif type_name == 'boolean' and not isinstance(value, bool):
        return "Must be a boolean"
    elif type_name == 'array' and not isinstance(value, list):
        return "Must be an array"
    elif type_name == 'object' and not isinstance(value, dict):
        return "Must be an object"
        
    return None

def min_length(value: Union[str, List],
              length: int) -> Optional[str]:
    """Minimum length validation"""
    if value is None:
        return None
        
    if len(value) < length:
        return f"Must be at least {length} characters long"
    return None

def max_length(value: Union[str, List],
              length: int) -> Optional[str]:
    """Maximum length validation"""
    if value is None:
        return None
        
    if len(value) > length:
        return f"Must be at most {length} characters long"
    return None

def min_value(value: Union[int, float],
             min_val: Union[int, float]) -> Optional[str]:
    """Minimum value validation"""
    if value is None:
        return None
        
    if value < min_val:
        return f"Must be greater than or equal to {min_val}"
    return None

def max_value(value: Union[int, float],
             max_val: Union[int, float]) -> Optional[str]:
    """Maximum value validation"""
    if value is None:
        return None
        
    if value > max_val:
        return f"Must be less than or equal to {max_val}"
    return None

def pattern(value: str,
           regex: str) -> Optional[str]:
    """Pattern validation"""
    if value is None:
        return None
        
    if not re.match(regex, value):
        return "Invalid format"
    return None

def email(value: str) -> Optional[str]:
    """Email validation"""
    if value is None:
        return None
        
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_regex, value):
        return "Invalid email address"
    return None

def url(value: str) -> Optional[str]:
    """URL validation"""
    if value is None:
        return None
        
    url_regex = r'^https?:\/\/(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&\/=]*)$'
    if not re.match(url_regex, value):
        return "Invalid URL"
    return None

def ip_address(value: str) -> Optional[str]:
    """IP address validation"""
    if value is None:
        return None
        
    try:
        ipaddress.ip_address(value)
        return None
    except ValueError:
        return "Invalid IP address"

def uuid_(value: str) -> Optional[str]:
    """UUID validation"""
    if value is None:
        return None
        
    try:
        uuid.UUID(value)
        return None
    except ValueError:
        return "Invalid UUID"

def date(value: str,
        format: str = '%Y-%m-%d') -> Optional[str]:
    """Date validation"""
    if value is None:
        return None
        
    try:
        datetime.strptime(value, format)
        return None
    except ValueError:
        return "Invalid date format"

def choices(value: Any,
           options: List) -> Optional[str]:
    """Choices validation"""
    if value is None:
        return None
        
    if value not in options:
        return f"Must be one of: {', '.join(map(str, options))}"
    return None

def range_(value: Union[int, float],
         min_val: Union[int, float],
         max_val: Union[int, float]) -> Optional[str]:
    """Range validation"""
    if value is None:
        return None
        
    if value < min_val or value > max_val:
        return f"Must be between {min_val} and {max_val}"
    return None

# Register built-in rules
BUILT_IN_RULES = {
    'required': required,
    'type': type_,
    'min_length': min_length,
    'max_length': max_length,
    'min_value': min_value,
    'max_value': max_value,
    'pattern': pattern,
    'email': email,
    'url': url,
    'ip_address': ip_address,
    'uuid': uuid_,
    'date': date,
    'choices': choices,
    'range': range_
} 