from typing import Dict, Optional, Any, Type, List, Set
import inspect
from functools import partial
import asyncio
from ..base import BaseComponent
from ..utils.errors import handle_errors

class DIContainer(BaseComponent):
    """Advanced dependency injection container"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._services: Dict[str, Dict] = {}
        self._instances: Dict[str, Any] = {}
        self._factories: Dict[str, callable] = {}
        self._dependencies: Dict[str, Set[str]] = {}
        self._scopes: Dict[str, str] = {}
        self._scope_instances: Dict[str, Dict[str, Any]] = {}
        self._resolving: Set[str] = set()

    async def initialize(self) -> None:
        """Initialize DI container"""
        # Register core services
        self._register_core_services()
        
        # Initialize singleton services
        await self._initialize_singletons()

    async def cleanup(self) -> None:
        """Cleanup container resources"""
        # Cleanup scoped instances
        for instances in self._scope_instances.values():
            for service in instances.values():
                if hasattr(service, 'cleanup'):
                    await service.cleanup()
                    
        # Cleanup singleton instances
        for service in self._instances.values():
            if hasattr(service, 'cleanup'):
                await service.cleanup()
                
        self._services.clear()
        self._instances.clear()
        self._factories.clear()
        self._dependencies.clear()
        self._scopes.clear()
        self._scope_instances.clear()

    @handle_errors(logger=None)
    def register(self,
                name: str,
                service: Any,
                scope: str = 'singleton',
                factory: Optional[callable] = None) -> None:
        """Register service with container"""
        if name in self._services:
            raise ValueError(f"Service already registered: {name}")
            
        # Validate scope
        if scope not in ['singleton', 'scoped', 'transient']:
            raise ValueError(f"Invalid scope: {scope}")
            
        # Add service
        self._services[name] = {
            'service': service,
            'scope': scope
        }
        
        # Add factory if provided
        if factory:
            self._factories[name] = factory
            
        # Extract dependencies
        self._dependencies[name] = self._get_dependencies(service)
        
        # Add to scope registry
        self._scopes[name] = scope

    def register_factory(self,
                        name: str,
                        factory: callable,
                        scope: str = 'singleton') -> None:
        """Register factory function"""
        self.register(name, None, scope, factory)

    @handle_errors(logger=None)
    async def get(self,
                 name: str,
                 scope_id: Optional[str] = None) -> Any:
        """Get service instance"""
        if name not in self._services:
            raise ValueError(f"Service not registered: {name}")
            
        # Check circular dependencies
        if name in self._resolving:
            raise ValueError(
                f"Circular dependency detected: {name}"
            )
            
        self._resolving.add(name)
        try:
            return await self._resolve_service(name, scope_id)
        finally:
            self._resolving.remove(name)

    def has(self, name: str) -> bool:
        """Check if service is registered"""
        return name in self._services

    @handle_errors(logger=None)
    async def create_scope(self) -> str:
        """Create new dependency scope"""
        scope_id = str(len(self._scope_instances))
        self._scope_instances[scope_id] = {}
        return scope_id

    async def remove_scope(self, scope_id: str) -> None:
        """Remove dependency scope"""
        if scope_id in self._scope_instances:
            # Cleanup scoped services
            for service in self._scope_instances[scope_id].values():
                if hasattr(service, 'cleanup'):
                    await service.cleanup()
                    
            del self._scope_instances[scope_id]

    def _register_core_services(self) -> None:
        """Register core framework services"""
        # Register self
        self.register('container', self)
        
        # Register components
        for name, component in self.app.components.items():
            self.register(name, component)

    async def _initialize_singletons(self) -> None:
        """Initialize singleton services"""
        for name, service in self._services.items():
            if service['scope'] == 'singleton':
                await self.get(name)

    async def _resolve_service(self,
                             name: str,
                             scope_id: Optional[str] = None) -> Any:
        """Resolve service instance"""
        service = self._services[name]
        scope = service['scope']
        
        # Handle different scopes
        if scope == 'singleton':
            return await self._resolve_singleton(name)
        elif scope == 'scoped':
            if not scope_id:
                raise ValueError(
                    f"Scope required for scoped service: {name}"
                )
            return await self._resolve_scoped(name, scope_id)
        else:  # transient
            return await self._create_instance(name)

    async def _resolve_singleton(self, name: str) -> Any:
        """Resolve singleton service"""
        if name in self._instances:
            return self._instances[name]
            
        instance = await self._create_instance(name)
        self._instances[name] = instance
        return instance

    async def _resolve_scoped(self,
                            name: str,
                            scope_id: str) -> Any:
        """Resolve scoped service"""
        if scope_id not in self._scope_instances:
            raise ValueError(f"Invalid scope: {scope_id}")
            
        scope = self._scope_instances[scope_id]
        
        if name in scope:
            return scope[name]
            
        instance = await self._create_instance(name)
        scope[name] = instance
        return instance

    async def _create_instance(self, name: str) -> Any:
        """Create service instance"""
        service = self._services[name]
        
        # Use factory if available
        if name in self._factories:
            factory = self._factories[name]
            return await self._invoke_factory(factory)
            
        # Create from class/function
        if service['service'] is None:
            raise ValueError(f"No service implementation: {name}")
            
        return await self._construct_service(service['service'])

    async def _construct_service(self, service: Any) -> Any:
        """Construct service instance"""
        # Get constructor parameters
        params = inspect.signature(service.__init__).parameters
        args = {}
        
        # Resolve dependencies
        for name, param in params.items():
            if name == 'self':
                continue
                
            if param.annotation != inspect.Parameter.empty:
                dependency = await self.get(param.annotation.__name__.lower())
                args[name] = dependency
                
        # Create instance
        return service(**args)

    async def _invoke_factory(self, factory: callable) -> Any:
        """Invoke factory function"""
        # Get factory parameters
        params = inspect.signature(factory).parameters
        args = {}
        
        # Resolve dependencies
        for name, param in params.items():
            if param.annotation != inspect.Parameter.empty:
                dependency = await self.get(param.annotation.__name__.lower())
                args[name] = dependency
                
        # Call factory
        result = factory(**args)
        
        # Handle async factories
        if inspect.iscoroutine(result):
            result = await result
            
        return result

    def _get_dependencies(self, service: Any) -> Set[str]:
        """Get service dependencies"""
        if service is None:
            return set()
            
        deps = set()
        params = inspect.signature(service.__init__).parameters
        
        for param in params.values():
            if param.annotation != inspect.Parameter.empty:
                deps.add(param.annotation.__name__.lower())
                
        return deps 