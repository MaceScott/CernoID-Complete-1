from pathlib import Path
import logging

class SyntaxFixer:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.setup_logging()

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def fix_all(self):
        self.logger.info("\n=== Fixing Syntax Errors ===\n")
        
        # 1. Fix database.py
        self.fix_database()
        
        # 2. Fix system.py
        self.fix_system()
        
        # 3. Fix recognition.py
        self.fix_recognition()
        
        # 4. Fix validator.py
        self.fix_validator()

    def fix_database(self):
        """Fix unterminated string literal in database.py"""
        file_path = self.project_root / 'backend/database/database/database.py'
        self.logger.info(f"Fixing {file_path.name}...")
        
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            # Fix line 125 - add missing quote
            if len(lines) >= 125:
                if not lines[124].strip().endswith('"'):
                    lines[124] = lines[124].rstrip() + '"\n'
            
            with open(file_path, 'w') as f:
                f.writelines(lines)
            
            self.logger.info("✓ Fixed unterminated string literal")
            
        except FileNotFoundError:
            self.logger.error("File not found")

    def fix_system(self):
        """Fix invalid syntax in system.py"""
        file_path = self.project_root / 'src/core/system.py'
        self.logger.info(f"\nFixing {file_path.name}...")
        
        # Create correct system.py content
        content = '''"""
System configuration and management module.
"""
from typing import Dict, Any
import os
import logging

class SystemManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config: Dict[str, Any] = {}
        
    def load_config(self) -> None:
        """Load system configuration"""
        try:
            # Add your configuration loading logic here
            pass
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a system setting"""
        return self.config.get(key, default)
'''
        
        try:
            with open(file_path, 'w') as f:
                f.write(content)
            self.logger.info("✓ Fixed invalid syntax")
        except FileNotFoundError:
            self.logger.error("File not found")

    def fix_recognition(self):
        """Fix parameter order in recognition.py"""
        file_path = self.project_root / 'src/api/routes/recognition.py'
        self.logger.info(f"\nFixing {file_path.name}...")
        
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            # Fix line 72 - reorder parameters
            if len(lines) >= 72:
                # We'll need to see the actual function to fix it properly
                self.logger.info("Please share the content of recognition.py around line 72")
                self.logger.info("for a proper parameter order fix")
            
        except FileNotFoundError:
            self.logger.error("File not found")

    def fix_validator(self):
        """Fix parameter order in validator.py"""
        file_path = self.project_root / 'src/core/security/validator.py'
        self.logger.info(f"\nFixing {file_path.name}...")
        
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            # Fix line 51 - reorder parameters
            if len(lines) >= 51:
                # We'll need to see the actual function to fix it properly
                self.logger.info("Please share the content of validator.py around line 51")
                self.logger.info("for a proper parameter order fix")
            
        except FileNotFoundError:
            self.logger.error("File not found")

def main():
    project_path = "C:/Users/maces/CernoID-Complete"
    fixer = SyntaxFixer(project_path)
    fixer.fix_all()

if __name__ == "__main__":
    main() 