from typing import Dict, Optional, Any, List, Union, Callable
import argparse
import importlib
import inspect
from dataclasses import dataclass

@dataclass
class CommandGroup:
    """Command group class"""
    name: str
    help: str
    subparsers: argparse._SubParsersAction

class Command:
    """CLI command class"""
    
    def __init__(self,
                 name: str,
                 callback: Union[Callable, str],
                 help: str,
                 group: CommandGroup,
                 arguments: List[Dict]):
        self.name = name
        self.help = help
        self.group = group
        self.arguments = arguments
        self._callback = self._resolve_callback(callback)

    async def execute(self, args: argparse.Namespace) -> Any:
        """Execute command"""
        if inspect.iscoroutinefunction(self._callback):
            return await self._callback(args)
        return self._callback(args)

    def _resolve_callback(self,
                         callback: Union[Callable, str]) -> Callable:
        """Resolve callback function"""
        if isinstance(callback, str):
            # Import callback from string
            module_path, func_name = callback.rsplit('.', 1)
            module = importlib.import_module(module_path)
            return getattr(module, func_name)
        return callback

    def get_info(self) -> Dict[str, Any]:
        """Get command information"""
        return {
            'name': self.name,
            'help': self.help,
            'group': self.group.name,
            'arguments': self.arguments
        } 