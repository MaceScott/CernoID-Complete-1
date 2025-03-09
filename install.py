"""CernoID Installer Script"""
import os
import sys
import shutil
import subprocess
from pathlib import Path
import ctypes
import json

def is_admin():
    """Check if the script is running with admin privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def get_app_dir() -> Path:
    """Get the application directory."""
    return Path.home() / '.cernoid'

def setup_directories(app_dir: Path) -> None:
    """Setup application directories."""
    # Create required directories
    dirs = [
        app_dir,
        app_dir / 'logs',
        app_dir / 'data',
        app_dir / 'data/images',
        app_dir / 'config',
        app_dir / 'models',
        app_dir / 'static'
    ]
    for dir_path in dirs:
        dir_path.mkdir(exist_ok=True)

def create_default_config(app_dir: Path) -> None:
    """Create default configuration file."""
    config = {
        "database": {
            "host": "localhost",
            "port": 5432,
            "name": "cernoid",
            "user": "postgres",
            "password": "postgres"
        },
        "face_recognition": {
            "min_face_size": 64,
            "matching_threshold": 0.6,
            "cache_size": 1000,
            "cache_ttl": 3600
        },
        "logging": {
            "level": "INFO",
            "file": "logs/app.log"
        },
        "server": {
            "host": "0.0.0.0",
            "port": 8000,
            "workers": "auto"
        }
    }
    
    config_path = app_dir / 'config' / 'config.json'
    if not config_path.exists():
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)

def create_desktop_shortcut():
    """Create desktop shortcut for CernoID."""
    # Get desktop path
    desktop = Path.home() / 'Desktop'
    app_dir = get_app_dir()
    
    # Create shortcut
    shortcut_path = desktop / 'CernoID.lnk'
    
    # Get Python executable path
    python_exe = sys.executable
    
    # Create VBS script to create shortcut
    vbs_script = f"""
    Set WS = WScript.CreateObject("WScript.Shell")
    Set link = WS.CreateShortcut("{shortcut_path}")
    link.TargetPath = "{python_exe}"
    link.Arguments = "-m cernoid"
    link.WorkingDirectory = "{app_dir}"
    link.IconLocation = "{app_dir / 'icon.ico'}"
    link.Description = "CernoID Face Recognition System"
    link.Save
    """
    
    # Write and execute VBS script
    vbs_path = app_dir / 'create_shortcut.vbs'
    with open(vbs_path, 'w') as f:
        f.write(vbs_script)
    
    subprocess.run(['cscript', str(vbs_path)], check=True)
    vbs_path.unlink()

def main():
    """Main installation function."""
    if not is_admin():
        # Re-run the script with admin privileges
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        return

    print("Installing CernoID...")
    
    # Get application directory
    app_dir = get_app_dir()
    
    # Setup application directories
    setup_directories(app_dir)
    
    # Copy icon file
    icon_path = Path(__file__).parent / 'assets' / 'icon.ico'
    if icon_path.exists():
        shutil.copy(icon_path, app_dir / 'icon.ico')
    
    # Install package
    print("Installing Python package...")
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-e', '.'], check=True)
    
    # Create default configuration
    create_default_config(app_dir)
    
    # Create desktop shortcut
    create_desktop_shortcut()
    
    print("""
CernoID has been successfully installed!
A desktop shortcut has been created.
You can now start CernoID by double-clicking the desktop icon.

Configuration files are located in: %USERPROFILE%\\.cernoid
Logs are stored in: %USERPROFILE%\\.cernoid\\logs
    """)

if __name__ == "__main__":
    main() 