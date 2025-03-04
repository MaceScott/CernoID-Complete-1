from typing import Optional, Any, Callable, Type, TypeVar
from functools import wraps
import inspect

T = TypeVar('T')

def inject(service_type: Optional[Type[T]] = None) -> Callable:
    """Dependency injection decorator"""
    
    def decorator(func: Callable) -> Callable:
        # Get parameter that needs injection
        params = inspect.signature(func).parameters
        param_name = None
        param_type = service_type
        
        for name, param in params.items():
            if param.annotation != inspect.Parameter.empty:
                if service_type is None:
                    param_type = param.annotation
                param_name = name
                break
                
        if param_name is None:
            raise ValueError("No injectable parameter found")
            
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Get container from first argument (self)
            if not args:
                raise ValueError("Missing self argument")
                
            instance = args[0]
            if not hasattr(instance, 'app'):
                raise ValueError("Instance missing app reference")
                
            container = instance.app.get_component('container')
            if not container:
                raise RuntimeError("DI container not available")
                
            # Inject dependency if not provided
            if param_name not in kwargs:
                service = await container.get(
                    param_type.__name__.lower()
                )
                kwargs[param_name] = service
                
            return await func(*args, **kwargs)
            
        return wrapper
        
    return decorator

def injectable(cls: Type[T]) -> Type[T]:
    """Injectable class decorator"""
    
    # Store original init
    original_init = cls.__init__
    
    @wraps(original_init)
    def new_init(self: Any, *args, **kwargs) -> None:
        # Initialize without injection
        if args or kwargs:
            original_init(self, *args, **kwargs)
            return
            
        # Get container from app
        if not hasattr(self, 'app'):
            raise ValueError("Instance missing app reference")
            
        container = self.app.get_component('container')
        if not container:
            raise RuntimeError("DI container not available")
            
        # Get constructor parameters
        params = inspect.signature(original_init).parameters
        inject_kwargs = {}
        
        # Resolve dependencies
        for name, param in params.items():
            if name == 'self':
                continue
                
            if param.annotation != inspect.Parameter.empty:
                service = await container.get(
                    param.annotation.__name__.lower()
                )
                inject_kwargs[name] = service
                
        # Initialize with injected dependencies
        original_init(self, **inject_kwargs)
        
    cls.__init__ = new_init
    return cls

def scoped(cls: Type[T]) -> Type[T]:
    """Scoped service decorator"""
    
    # Register class as scoped service
    def register(app: Any) -> None:
        container = app.get_component('container')
        if container:
            container.register(
                cls.__name__.lower(),
                cls,
                scope='scoped'
            )
            
    cls._register = register
    return cls

def singleton(cls: Type[T]) -> Type[T]:
    """Singleton service decorator"""
    
    # Register class as singleton service
    def register(app: Any) -> None:
        container = app.get_component('container')
        if container:
            container.register(
                cls.__name__.lower(),
                cls,
                scope='singleton'
            )
            
    cls._register = register
    return cls

def transient(cls: Type[T]) -> Type[T]:
    """Transient service decorator"""
    
    # Register class as transient service
    def register(app: Any) -> None:
        container = app.get_component('container')
        if container:
            container.register(
                cls.__name__.lower(),
                cls,
                scope='transient'
            )
            
    cls._register = register
    return cls 