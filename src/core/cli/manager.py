from typing import Dict, List, Optional, Any, Callable, Union
import click
import asyncio
from pathlib import Path
import json
import yaml
import argparse
import sys
from ..base import BaseComponent
from ..utils.errors import handle_errors

class CLIManager(BaseComponent):
    """Advanced CLI management system"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._commands: Dict[str, 'Command'] = {}
        self._groups: Dict[str, 'CommandGroup'] = {}
        self._default_group = 'general'
        self._parser = argparse.ArgumentParser(
            description=self.config.get('cli.description', '')
        )
        self._subparsers = self._parser.add_subparsers(
            dest='command',
            help='Available commands'
        )
        self._history: List[str] = []
        self._max_history = self.config.get('cli.max_history', 1000)
        self._stats = {
            'commands': 0,
            'executions': 0,
            'errors': 0
        }

    async def initialize(self) -> None:
        """Initialize CLI manager"""
        # Create default group
        self.add_group(self._default_group, 'General commands')
        
        # Load built-in commands
        await self._load_builtins()
        
        # Load commands from config
        commands = self.config.get('cli.commands', {})
        for name, config in commands.items():
            self.add_command(
                name,
                config['callback'],
                config.get('help', ''),
                config.get('group', self._default_group),
                config.get('arguments', [])
            )

    async def cleanup(self) -> None:
        """Cleanup CLI resources"""
        self._commands.clear()
        self._groups.clear()
        self._history.clear()

    @handle_errors(logger=None)
    def add_command(self,
                   name: str,
                   callback: Union[Callable, str],
                   help: str = '',
                   group: str = None,
                   arguments: List[Dict] = None) -> None:
        """Add CLI command"""
        # Get or create group
        group = group or self._default_group
        if group not in self._groups:
            self.add_group(group)
            
        # Create command
        command = Command(
            name=name,
            callback=callback,
            help=help,
            group=self._groups[group],
            arguments=arguments or []
        )
        
        # Add to parser
        parser = command.group.subparsers.add_parser(
            name,
            help=help
        )
        
        # Add arguments
        for arg in command.arguments:
            kwargs = arg.copy()
            name = kwargs.pop('name')
            parser.add_argument(name, **kwargs)
            
        # Store command
        self._commands[name] = command
        self._stats['commands'] += 1

    def add_group(self,
                 name: str,
                 help: str = '') -> None:
        """Add command group"""
        group = CommandGroup(
            name=name,
            help=help,
            subparsers=self._subparsers
        )
        self._groups[name] = group

    @handle_errors(logger=None)
    async def execute(self,
                     args: Optional[List[str]] = None) -> Any:
        """Execute CLI command"""
        try:
            # Parse arguments
            args = self._parser.parse_args(args)
            
            # Get command
            command = self._commands.get(args.command)
            if not command:
                self._parser.print_help()
                return
                
            # Add to history
            self._add_history(args.command)
            
            # Execute command
            result = await command.execute(args)
            self._stats['executions'] += 1
            
            return result
            
        except Exception as e:
            self.logger.error(f"Command execution error: {str(e)}")
            self._stats['errors'] += 1
            raise

    def get_command(self, name: str) -> Optional['Command']:
        """Get command by name"""
        return self._commands.get(name)

    def list_commands(self,
                     group: Optional[str] = None) -> List[str]:
        """List available commands"""
        if group:
            return [
                name for name, cmd in self._commands.items()
                if cmd.group.name == group
            ]
        return list(self._commands.keys())

    def get_history(self,
                   limit: Optional[int] = None) -> List[str]:
        """Get command execution history"""
        limit = limit or len(self._history)
        return self._history[-limit:]

    async def get_stats(self) -> Dict[str, Any]:
        """Get CLI statistics"""
        return self._stats.copy()

    def _add_history(self, command: str) -> None:
        """Add command to history"""
        self._history.append(command)
        
        # Trim history
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

    async def _load_builtins(self) -> None:
        """Load built-in commands"""
        # Help command
        self.add_command(
            'help',
            self._help_command,
            'Show help information',
            'system',
            [
                {
                    'name': 'command',
                    'nargs': '?',
                    'help': 'Command name'
                }
            ]
        )
        
        # Version command
        self.add_command(
            'version',
            self._version_command,
            'Show version information',
            'system'
        )
        
        # History command
        self.add_command(
            'history',
            self._history_command,
            'Show command history',
            'system',
            [
                {
                    'name': '--limit',
                    'type': int,
                    'help': 'Number of entries to show'
                }
            ]
        )

    async def _help_command(self, args: argparse.Namespace) -> None:
        """Built-in help command"""
        if args.command:
            command = self._commands.get(args.command)
            if command:
                command.group.subparsers.choices[args.command].print_help()
            else:
                print(f"Unknown command: {args.command}")
        else:
            self._parser.print_help()

    async def _version_command(self, args: argparse.Namespace) -> None:
        """Built-in version command"""
        version = self.config.get('version', '0.1.0')
        print(f"Version: {version}")

    async def _history_command(self, args: argparse.Namespace) -> None:
        """Built-in history command"""
        history = self.get_history(args.limit)
        for cmd in history:
            print(cmd)

    def run(self) -> None:
        """Run CLI application"""
        self._parser() 