from typing import Optional, Any, Callable, Union
from functools import wraps
import inspect
import asyncio
from ..base import BaseComponent

def cached(ttl: Optional[int] = None,
          key_prefix: Optional[str] = None,
          handler: Optional[str] = None):
    """Cache decorator for methods and functions"""
    
    def decorator(func: Callable) -> Callable:
        # Get function signature
        sig = inspect.signature(func)
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get cache manager
            if not args:
                raise RuntimeError("No self argument")
                
            self = args[0]
            if not isinstance(self, BaseComponent):
                raise RuntimeError("Not a component method")
                
            cache = self.app.get_component('cache_manager')
            if not cache:
                # No cache available, execute normally
                return await func(*args, **kwargs)
                
            # Generate cache key
            key_parts = [key_prefix or func.__name__]
            
            # Add self reference if method
            if inspect.ismethod(func):
                key_parts.append(str(id(self)))
                
            # Add arguments
            bound_args = sig.bind(*args, **kwargs)
            for name, value in bound_args.arguments.items():
                if name == 'self':
                    continue
                key_parts.append(f"{name}:{value}")
                
            cache_key = ':'.join(key_parts)
            
            # Try to get cached value
            value = await cache.get(cache_key)
            if value is not None:
                return value
                
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            await cache.set(
                cache_key,
                result,
                ttl=ttl,
                handler=handler
            )
            
            return result
            
        return wrapper
        
    return decorator

def cache_invalidate(key_prefix: Optional[str] = None):
    """Cache invalidation decorator"""
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get cache manager
            if not args:
                raise RuntimeError("No self argument")
                
            self = args[0]
            if not isinstance(self, BaseComponent):
                raise RuntimeError("Not a component method")
                
            cache = self.app.get_component('cache_manager')
            if not cache:
                # No cache available, execute normally
                return await func(*args, **kwargs)
                
            # Execute function
            result = await func(*args, **kwargs)
            
            # Invalidate cache entries
            prefix = key_prefix or func.__name__
            keys_to_delete = [
                key for key in cache._cache.keys()
                if key.startswith(prefix)
            ]
            
            for key in keys_to_delete:
                await cache.delete(key)
                
            return result
            
        return wrapper
        
    return decorator

def cached_property(ttl: Optional[int] = None,
                   handler: Optional[str] = None):
    """Cached property decorator"""
    
    def decorator(func: Callable) -> property:
        name = f"_cached_{func.__name__}"
        
        @property
        @wraps(func)
        def wrapper(self):
            # Check if cached
            if hasattr(self, name):
                value, expires = getattr(self, name)
                if expires > time.time():
                    return value
                    
            # Get new value
            value = func(self)
            
            # Cache value
            if ttl is not None:
                expires = time.time() + ttl
            else:
                expires = float('inf')
                
            if handler:
                cache = self.app.get_component('cache_manager')
                if cache and handler in cache._handlers:
                    value = cache._handlers[handler](value)
                    
            setattr(self, name, (value, expires))
            return value
            
        return wrapper
        
    return decorator

def cache_region(region: str,
                key_generator: Optional[Callable] = None):
    """Cache region decorator"""
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get cache manager
            if not args:
                raise RuntimeError("No self argument")
                
            self = args[0]
            if not isinstance(self, BaseComponent):
                raise RuntimeError("Not a component method")
                
            cache = self.app.get_component('cache_manager')
            if not cache:
                # No cache available, execute normally
                return await func(*args, **kwargs)
                
            # Generate cache key
            if key_generator:
                cache_key = key_generator(*args, **kwargs)
            else:
                cache_key = cache.generate_key(*args, **kwargs)
                
            cache_key = f"{region}:{cache_key}"
            
            # Try to get cached value
            value = await cache.get(cache_key)
            if value is not None:
                return value
                
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            await cache.set(cache_key, result)
            
            return result
            
        return wrapper
        
    return decorator 