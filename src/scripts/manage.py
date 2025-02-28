import argparse
from pathlib import Path
import importlib.util
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def import_script(script_name: str):
    """Dynamically import a script module"""
    script_path = Path(__file__).parent / f"{script_name}.py"
    if not script_path.exists():
        raise ImportError(f"Script not found: {script_name}")
        
    spec = importlib.util.spec_from_file_location(script_name, script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def main():
    parser = argparse.ArgumentParser(description='CernoID Project Management Scripts')
    parser.add_argument('script', choices=['reorganize_project', 'create_ui_structure'],
                       help='Script to run')
    parser.add_argument('--args', nargs=argparse.REMAINDER,
                       help='Arguments to pass to the script')

    args = parser.parse_args()

    try:
        script = import_script(args.script)
        script.main()
    except Exception as e:
        logger.error(f"Failed to run script {args.script}: {e}")

if __name__ == "__main__":
    main()
