"""CernoID Installer"""
import os
import sys
import subprocess
import shutil
from pathlib import Path
import venv
import json
import ctypes
import winreg

def is_admin():
    """Check if running with admin privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def get_install_dir() -> Path:
    """Get the installation directory."""
    return Path(os.environ['PROGRAMFILES']) / 'CernoID'

def get_app_data_dir() -> Path:
    """Get the application data directory."""
    return Path(os.environ['APPDATA']) / 'CernoID'

def create_virtual_environment(install_dir: Path):
    """Create a Python virtual environment."""
    venv_dir = install_dir / 'venv'
    print("Creating Python virtual environment...")
    venv.create(venv_dir, with_pip=True)
    return venv_dir

def install_python_dependencies(venv_dir: Path, source_dir: Path):
    """Install Python dependencies in the virtual environment."""
    pip = venv_dir / 'Scripts' / 'pip.exe'
    subprocess.run([
        str(pip), 'install', '-e', str(source_dir)
    ], check=True)

def build_frontend(source_dir: Path, install_dir: Path):
    """Build the frontend."""
    frontend_dir = source_dir / 'frontend'
    print("Building frontend...")
    
    # Install Node.js dependencies
    subprocess.run(['npm', 'install'], cwd=frontend_dir, check=True)
    
    # Build frontend
    subprocess.run(['npm', 'run', 'build'], cwd=frontend_dir, check=True)
    
    # Copy build output
    shutil.copytree(
        frontend_dir / 'out',
        install_dir / 'frontend',
        dirs_exist_ok=True
    )

def create_shortcut(install_dir: Path):
    """Create desktop and start menu shortcuts."""
    print("Creating shortcuts...")
    
    # Create VBScript to make shortcuts
    vbs_content = f"""
    Set WS = WScript.CreateObject("WScript.Shell")
    
    ' Desktop shortcut
    Set link = WS.CreateShortcut(WS.SpecialFolders("Desktop") & "\\CernoID.lnk")
    link.TargetPath = "{install_dir}\\venv\\Scripts\\pythonw.exe"
    link.Arguments = "-m cernoid"
    link.WorkingDirectory = "{install_dir}"
    link.IconLocation = "{install_dir}\\assets\\icon.ico"
    link.Description = "CernoID Face Recognition System"
    link.Save
    
    ' Start Menu shortcut
    Set link = WS.CreateShortcut(WS.SpecialFolders("StartMenu") & "\\Programs\\CernoID.lnk")
    link.TargetPath = "{install_dir}\\venv\\Scripts\\pythonw.exe"
    link.Arguments = "-m cernoid"
    link.WorkingDirectory = "{install_dir}"
    link.IconLocation = "{install_dir}\\assets\\icon.ico"
    link.Description = "CernoID Face Recognition System"
    link.Save
    """
    
    vbs_path = install_dir / 'create_shortcuts.vbs'
    with open(vbs_path, 'w') as f:
        f.write(vbs_content)
    
    # Execute VBScript
    subprocess.run(['cscript', str(vbs_path)], check=True)
    vbs_path.unlink()

def create_config(app_data_dir: Path):
    """Create default configuration."""
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
        "server": {
            "host": "127.0.0.1",
            "port": 8000,
            "workers": "auto"
        }
    }
    
    config_dir = app_data_dir / 'config'
    config_dir.mkdir(parents=True, exist_ok=True)
    
    with open(config_dir / 'config.json', 'w') as f:
        json.dump(config, f, indent=4)

def setup_registry():
    """Set up registry entries for autostart and uninstall."""
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\CernoID"
    
    try:
        with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
            winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, "CernoID")
            winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, 
                            str(get_install_dir() / "uninstall.exe"))
            winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, 
                            str(get_install_dir() / "assets" / "icon.ico"))
            winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, "CernoID")
            winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, "1.0.0")
    except Exception as e:
        print(f"Warning: Could not create registry entries: {e}")

def main():
    """Main installation function."""
    if not is_admin():
        # Re-run with admin privileges
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        return

    try:
        print("Installing CernoID...")
        
        # Get directories
        install_dir = get_install_dir()
        app_data_dir = get_app_data_dir()
        source_dir = Path(__file__).parent
        
        # Create installation directory
        install_dir.mkdir(parents=True, exist_ok=True)
        
        # Create virtual environment and install dependencies
        venv_dir = create_virtual_environment(install_dir)
        install_python_dependencies(venv_dir, source_dir)
        
        # Build and install frontend
        build_frontend(source_dir, install_dir)
        
        # Copy assets
        shutil.copytree(
            source_dir / 'assets',
            install_dir / 'assets',
            dirs_exist_ok=True
        )
        
        # Create configuration
        create_config(app_data_dir)
        
        # Create shortcuts
        create_shortcut(install_dir)
        
        # Setup registry
        setup_registry()
        
        print("""
CernoID has been successfully installed!

You can start the application by:
1. Double-clicking the desktop icon
2. Using the Start Menu shortcut
3. Running 'cernoid' from the command line

Configuration files are located in: %APPDATA%\\CernoID
        """)
        
    except Exception as e:
        print(f"Error during installation: {e}")
        input("Press Enter to exit...")
        sys.exit(1)

if __name__ == "__main__":
    main() 