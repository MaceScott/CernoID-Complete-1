from typing import Any, Dict, List, Optional, Union
from datetime import datetime, date
from decimal import Decimal
import json
import re
import html
import urllib.parse
import base64
import hashlib

def format_date(value: Union[datetime, date],
               format_: str = '%Y-%m-%d') -> str:
    """Format date value"""
    if not value:
        return ''
    return value.strftime(format_)

def format_datetime(value: datetime,
                   format_: str = '%Y-%m-%d %H:%M:%S') -> str:
    """Format datetime value"""
    if not value:
        return ''
    return value.strftime(format_)

def format_number(value: Union[int, float, Decimal],
                 decimals: int = 2) -> str:
    """Format number value"""
    if not value:
        return '0'
    return f"{float(value):,.{decimals}f}"

def format_currency(value: Union[int, float, Decimal],
                   symbol: str = '$',
                   decimals: int = 2) -> str:
    """Format currency value"""
    if not value:
        return f"{symbol}0"
    return f"{symbol}{float(value):,.{decimals}f}"

def to_json(value: Any,
           indent: Optional[int] = None) -> str:
    """Convert value to JSON"""
    return json.dumps(value, indent=indent)

def from_json(value: str) -> Any:
    """Parse JSON string"""
    if not value:
        return None
    return json.loads(value)

def truncate(value: str,
            length: int,
            suffix: str = '...') -> str:
    """Truncate string"""
    if len(value) <= length:
        return value
    return value[:length].rstrip() + suffix

def slugify(value: str) -> str:
    """Convert string to slug"""
    # Convert to lowercase
    value = value.lower()
    
    # Remove special characters
    value = re.sub(r'[^\w\s-]', '', value)
    
    # Replace whitespace with dash
    value = re.sub(r'[-\s]+', '-', value)
    
    # Remove leading/trailing dashes
    return value.strip('-')

def strip_tags(value: str) -> str:
    """Remove HTML tags"""
    return re.sub(r'<[^>]+>', '', value)

def escape_html(value: str) -> str:
    """Escape HTML characters"""
    return html.escape(value)

def unescape_html(value: str) -> str:
    """Unescape HTML characters"""
    return html.unescape(value)

def url_encode(value: str) -> str:
    """URL encode string"""
    if not value:
        return ''
    return urllib.parse.quote(value)

def url_decode(value: str) -> str:
    """URL decode string"""
    if not value:
        return ''
    return urllib.parse.unquote(value)

def base64_encode(value: Union[str, bytes]) -> str:
    """Encode value as base64"""
    if isinstance(value, str):
        value = value.encode()
    return base64.b64encode(value).decode()

def base64_decode(value: str) -> bytes:
    """Decode base64 string"""
    return base64.b64decode(value)

def md5(value: Union[str, bytes]) -> str:
    """Calculate MD5 hash"""
    if isinstance(value, str):
        value = value.encode()
    return hashlib.md5(value).hexdigest()

def sha1(value: Union[str, bytes]) -> str:
    """Calculate SHA1 hash"""
    if isinstance(value, str):
        value = value.encode()
    return hashlib.sha1(value).hexdigest()

def sha256(value: Union[str, bytes]) -> str:
    """Calculate SHA256 hash"""
    if isinstance(value, str):
        value = value.encode()
    return hashlib.sha256(value).hexdigest()

def word_wrap(value: str,
             width: int = 79,
             break_long_words: bool = True) -> str:
    """Wrap text to specified width"""
    import textwrap
    return textwrap.fill(
        value,
        width,
        break_long_words=break_long_words
    )

def pluralize(value: Union[int, List],
             singular: str,
             plural: Optional[str] = None) -> str:
    """Pluralize word based on value"""
    if isinstance(value, list):
        count = len(value)
    else:
        count = value
        
    if count == 1:
        return singular
    return plural or f"{singular}s"

def filesize_format(bytes_: int) -> str:
    """Format file size"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_ < 1024:
            return f"{bytes_:.1f} {unit}"
        bytes_ /= 1024
    return f"{bytes_:.1f} PB"

# Register default filters
DEFAULT_FILTERS = {
    'date': format_date,
    'datetime': format_datetime,
    'number': format_number,
    'currency': format_currency,
    'json': to_json,
    'from_json': from_json,
    'truncate': truncate,
    'slugify': slugify,
    'strip_tags': strip_tags,
    'escape': escape_html,
    'unescape': unescape_html,
    'urlencode': url_encode,
    'urldecode': url_decode,
    'b64encode': base64_encode,
    'b64decode': base64_decode,
    'md5': md5,
    'sha1': sha1,
    'sha256': sha256,
    'word_wrap': word_wrap,
    'pluralize': pluralize,
    'filesize_format': filesize_format
} 