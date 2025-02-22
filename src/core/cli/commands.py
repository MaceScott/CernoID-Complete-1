from typing import Dict, Optional, Any, List, Callable
import click
import asyncio
from pathlib import Path
import yaml
import json
import shutil
from ..base import BaseComponent

class CommandGroup:
    """Base class for command groups"""
    
    def __init__(self, app: Any):
        self.app = app
        self.config = app.config
        self.logger = app.logger

    def get_commands(self) -> Dict[str, Callable]:
        """Get group commands"""
        commands = {}
        
        for name in dir(self):
            if name.startswith('cmd_'):
                cmd_name = name[4:].replace('_', '-')
                commands[cmd_name] = getattr(self, name)
                
        return commands

class AppCommands(CommandGroup):
    """Application management commands"""
    
    def cmd_start(self,
                 host: str = '127.0.0.1',
                 port: int = 8000,
                 reload: bool = False):
        """Start application server"""
        self.app.run(host, port, reload)

    def cmd_shell(self):
        """Start interactive shell"""
        import code
        code.interact(local=locals())

    def cmd_routes(self):
        """List application routes"""
        router = self.app.get_component('router')
        if not router:
            return
            
        for route in router.routes:
            click.echo(
                f"{route.methods} {route.path} -> "
                f"{route.endpoint.__name__}"
            )

    def cmd_components(self):
        """List application components"""
        for name, component in self.app.components.items():
            click.echo(f"{name}: {component.__class__.__name__}")

class DBCommands(CommandGroup):
    """Database management commands"""
    
    async def cmd_create(self):
        """Create database tables"""
        db = self.app.get_component('database')
        if not db:
            raise RuntimeError("Database not available")
            
        await db.create_all()

    async def cmd_drop(self):
        """Drop database tables"""
        db = self.app.get_component('database')
        if not db:
            raise RuntimeError("Database not available")
            
        await db.drop_all()

    async def cmd_seed(self,
                      file: Optional[Path] = None):
        """Seed database with data"""
        db = self.app.get_component('database')
        if not db:
            raise RuntimeError("Database not available")
            
        if file and file.exists():
            with open(file) as f:
                data = yaml.safe_load(f)
        else:
            data = self.config.get('db.seed_data', {})
            
        for model, records in data.items():
            model_cls = db.get_model(model)
            if not model_cls:
                continue
                
            for record in records:
                obj = model_cls(**record)
                await db.add(obj)
                
        await db.commit()

    async def cmd_backup(self,
                        file: Optional[Path] = None):
        """Backup database"""
        db = self.app.get_component('database')
        if not db:
            raise RuntimeError("Database not available")
            
        file = file or Path('backup.sql')
        await db.backup(file)

class CacheCommands(CommandGroup):
    """Cache management commands"""
    
    async def cmd_clear(self):
        """Clear cache"""
        cache = self.app.get_component('cache_manager')
        if not cache:
            raise RuntimeError("Cache not available")
            
        await cache.clear()

    async def cmd_stats(self):
        """Show cache statistics"""
        cache = self.app.get_component('cache_manager')
        if not cache:
            raise RuntimeError("Cache not available")
            
        stats = await cache.get_stats()
        click.echo(yaml.dump(stats))

class PluginCommands(CommandGroup):
    """Plugin management commands"""
    
    async def cmd_list(self):
        """List installed plugins"""
        plugins = self.app.get_component('plugin_manager')
        if not plugins:
            raise RuntimeError("Plugin manager not available")
            
        for name, plugin in plugins.get_plugins().items():
            status = 'enabled' if plugin.enabled else 'disabled'
            click.echo(f"{name} ({status})")

    async def cmd_install(self, name: str):
        """Install plugin"""
        plugins = self.app.get_component('plugin_manager')
        if not plugins:
            raise RuntimeError("Plugin manager not available")
            
        await plugins.install_plugin(name)

    async def cmd_uninstall(self, name: str):
        """Uninstall plugin"""
        plugins = self.app.get_component('plugin_manager')
        if not plugins:
            raise RuntimeError("Plugin manager not available")
            
        await plugins.uninstall_plugin(name)

class ConfigCommands(CommandGroup):
    """Configuration management commands"""
    
    def cmd_show(self,
                format: str = 'yaml',
                path: Optional[str] = None):
        """Show configuration"""
        config = self.app.config
        
        if path:
            for key in path.split('.'):
                config = config.get(key, {})
                
        if format == 'json':
            click.echo(json.dumps(config, indent=2))
        else:
            click.echo(yaml.dump(config))

    def cmd_set(self,
               key: str,
               value: str,
               format: str = 'yaml'):
        """Set configuration value"""
        if format == 'json':
            value = json.loads(value)
        else:
            value = yaml.safe_load(value)
            
        config = self.app.get_component('config_manager')
        if config:
            config.set(key, value)

    def cmd_export(self, file: Path):
        """Export configuration"""
        with open(file, 'w') as f:
            yaml.dump(self.app.config, f)

    def cmd_import(self, file: Path):
        """Import configuration"""
        if not file.exists():
            raise click.BadParameter("File not found")
            
        with open(file) as f:
            config = yaml.safe_load(f)
            
        config_mgr = self.app.get_component('config_manager')
        if config_mgr:
            config_mgr.update(config) 