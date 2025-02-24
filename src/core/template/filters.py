"""
Template filters for data formatting and transformation.
Organized into categories for better maintainability.
"""

from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime, date
from decimal import Decimal
import json
import re
import html
import urllib.parse
import base64
import hashlib
import textwrap
from dataclasses import dataclass
from enum import Enum

class FilterCategory(Enum):
    """Categories for template filters"""
    DATE = "date"
    NUMBER = "number"
    STRING = "string"
    ENCODING = "encoding"
    HASH = "hash"
    HTML = "html"
    URL = "url"
    UTILITY = "utility"

@dataclass
class FilterInfo:
    """Metadata for template filters"""
    func: Callable
    category: FilterCategory
    description: str

class DateFilters:
    """Date and time formatting filters"""
    
    @staticmethod
    def format_date(value: Union[datetime, date], format_: str = '%Y-%m-%d') -> str:
        """Format date value"""
        if not value:
            return ''
        return value.strftime(format_)

    @staticmethod
    def format_datetime(value: datetime, format_: str = '%Y-%m-%d %H:%M:%S') -> str:
        """Format datetime value"""
        if not value:
            return ''
        return value.strftime(format_)

class NumberFilters:
    """Numeric value formatting filters"""
    
    @staticmethod
    def format_number(value: Union[int, float, Decimal], decimals: int = 2) -> str:
        """Format number with thousand separators and decimal places"""
        if not value:
            return '0'
        return f"{float(value):,.{decimals}f}"

    @staticmethod
    def format_currency(value: Union[int, float, Decimal], 
                       symbol: str = '$', decimals: int = 2) -> str:
        """Format currency value with symbol"""
        if not value:
            return f"{symbol}0"
        return f"{symbol}{float(value):,.{decimals}f}"

    @staticmethod
    def filesize_format(bytes_: int) -> str:
        """Format file size with appropriate unit"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_ < 1024:
                return f"{bytes_:.1f} {unit}"
            bytes_ /= 1024
        return f"{bytes_:.1f} PB"

class StringFilters:
    """String manipulation filters"""
    
    @staticmethod
    def truncate(value: str, length: int, suffix: str = '...') -> str:
        """Truncate string to specified length"""
        if len(value) <= length:
            return value
        return value[:length].rstrip() + suffix

    @staticmethod
    def slugify(value: str) -> str:
        """Convert string to URL-friendly slug"""
        value = value.lower()
        value = re.sub(r'[^\w\s-]', '', value)
        value = re.sub(r'[-\s]+', '-', value)
        return value.strip('-')

    @staticmethod
    def word_wrap(value: str, width: int = 79, break_long_words: bool = True) -> str:
        """Wrap text to specified width"""
        return textwrap.fill(value, width, break_long_words=break_long_words)

    @staticmethod
    def pluralize(value: Union[int, List], singular: str, 
                  plural: Optional[str] = None) -> str:
        """Pluralize word based on value"""
        count = len(value) if isinstance(value, list) else value
        return singular if count == 1 else (plural or f"{singular}s")

class EncodingFilters:
    """Data encoding filters"""
    
    @staticmethod
    def to_json(value: Any, indent: Optional[int] = None) -> str:
        """Convert value to JSON string"""
        return json.dumps(value, indent=indent)

    @staticmethod
    def from_json(value: str) -> Any:
        """Parse JSON string to Python object"""
        return json.loads(value) if value else None

    @staticmethod
    def base64_encode(value: Union[str, bytes]) -> str:
        """Encode value as base64"""
        if isinstance(value, str):
            value = value.encode()
        return base64.b64encode(value).decode()

    @staticmethod
    def base64_decode(value: str) -> bytes:
        """Decode base64 string"""
        return base64.b64decode(value)

class HashFilters:
    """Cryptographic hash filters"""
    
    @staticmethod
    def md5(value: Union[str, bytes]) -> str:
        """Calculate MD5 hash (for non-security purposes)"""
        if isinstance(value, str):
            value = value.encode()
        return hashlib.md5(value).hexdigest()

    @staticmethod
    def sha1(value: Union[str, bytes]) -> str:
        """Calculate SHA1 hash"""
        if isinstance(value, str):
            value = value.encode()
        return hashlib.sha1(value).hexdigest()

    @staticmethod
    def sha256(value: Union[str, bytes]) -> str:
        """Calculate SHA256 hash"""
        if isinstance(value, str):
            value = value.encode()
        return hashlib.sha256(value).hexdigest()

class HTMLFilters:
    """HTML-related filters"""
    
    @staticmethod
    def strip_tags(value: str) -> str:
        """Remove HTML tags from string"""
        return re.sub(r'<[^>]+>', '', value)

    @staticmethod
    def escape_html(value: str) -> str:
        """Escape HTML special characters"""
        return html.escape(value)

    @staticmethod
    def unescape_html(value: str) -> str:
        """Unescape HTML special characters"""
        return html.unescape(value)

class URLFilters:
    """URL-related filters"""
    
    @staticmethod
    def url_encode(value: str) -> str:
        """URL encode string"""
        return urllib.parse.quote(value) if value else ''

    @staticmethod
    def url_decode(value: str) -> str:
        """URL decode string"""
        return urllib.parse.unquote(value) if value else ''

# Register all filters with metadata
FILTERS: Dict[str, FilterInfo] = {
    # Date filters
    'date': FilterInfo(DateFilters.format_date, FilterCategory.DATE, 
                      "Format date value"),
    'datetime': FilterInfo(DateFilters.format_datetime, FilterCategory.DATE,
                         "Format datetime value"),
    
    # Number filters
    'number': FilterInfo(NumberFilters.format_number, FilterCategory.NUMBER,
                        "Format number with separators"),
    'currency': FilterInfo(NumberFilters.format_currency, FilterCategory.NUMBER,
                          "Format currency value"),
    'filesize': FilterInfo(NumberFilters.filesize_format, FilterCategory.NUMBER,
                          "Format file size"),
    
    # String filters
    'truncate': FilterInfo(StringFilters.truncate, FilterCategory.STRING,
                          "Truncate string"),
    'slugify': FilterInfo(StringFilters.slugify, FilterCategory.STRING,
                         "Convert to URL slug"),
    'word_wrap': FilterInfo(StringFilters.word_wrap, FilterCategory.STRING,
                           "Wrap text to width"),
    'pluralize': FilterInfo(StringFilters.pluralize, FilterCategory.STRING,
                           "Pluralize word"),
    
    # Encoding filters
    'json': FilterInfo(EncodingFilters.to_json, FilterCategory.ENCODING,
                      "Convert to JSON"),
    'from_json': FilterInfo(EncodingFilters.from_json, FilterCategory.ENCODING,
                           "Parse JSON string"),
    'b64encode': FilterInfo(EncodingFilters.base64_encode, FilterCategory.ENCODING,
                           "Base64 encode"),
    'b64decode': FilterInfo(EncodingFilters.base64_decode, FilterCategory.ENCODING,
                           "Base64 decode"),
    
    # Hash filters
    'md5': FilterInfo(HashFilters.md5, FilterCategory.HASH, "MD5 hash"),
    'sha1': FilterInfo(HashFilters.sha1, FilterCategory.HASH, "SHA1 hash"),
    'sha256': FilterInfo(HashFilters.sha256, FilterCategory.HASH, "SHA256 hash"),
    
    # HTML filters
    'strip_tags': FilterInfo(HTMLFilters.strip_tags, FilterCategory.HTML,
                            "Remove HTML tags"),
    'escape': FilterInfo(HTMLFilters.escape_html, FilterCategory.HTML,
                        "Escape HTML"),
    'unescape': FilterInfo(HTMLFilters.unescape_html, FilterCategory.HTML,
                          "Unescape HTML"),
    
    # URL filters
    'urlencode': FilterInfo(URLFilters.url_encode, FilterCategory.URL,
                           "URL encode"),
    'urldecode': FilterInfo(URLFilters.url_decode, FilterCategory.URL,
                           "URL decode")
}

# For backward compatibility
DEFAULT_FILTERS = {name: info.func for name, info in FILTERS.items()} 