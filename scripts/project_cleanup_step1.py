from pathlib import Path
import ast
import logging
from typing import Dict, List, Set
import shutil

class ProjectCleanupManager:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.setup_logging()
        self.issues = {
            'syntax_errors': [],
            'duplicates': [],
            'empty_files': [],
            'complex_files': []
        }

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def analyze_step1(self):
        """Step 1: Identify immediate issues"""
        self.logger.info("\n=== Step 1: Initial Analysis ===\n")
        
        # Check only project directories
        project_dirs = ['app', 'backend', 'src']
        
        for dir_name in project_dirs:
            dir_path = self.project_root / dir_name
            if dir_path.exists():
                self._analyze_directory(dir_path)

        # Report findings
        self._report_findings()

    def _analyze_directory(self, directory: Path):
        """Analyze a specific directory for issues"""
        for py_file in directory.rglob('*.py'):
            relative_path = py_file.relative_to(self.project_root)
            
            # Skip __init__.py files
            if py_file.name == '__init__.py':
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Check for empty files
                if not content.strip():
                    self.issues['empty_files'].append(str(relative_path))
                    continue
                    
                # Try parsing to check for syntax errors
                try:
                    tree = ast.parse(content)
                    
                    # Check for complex files
                    functions = len([node for node in ast.walk(tree) 
                                   if isinstance(node, ast.FunctionDef)])
                    if functions > 15:  # Files with too many functions
                        self.issues['complex_files'].append(
                            f"{relative_path} ({functions} functions)")
                        
                except SyntaxError as se:
                    self.issues['syntax_errors'].append(
                        f"{relative_path} - Line {se.lineno}: {se.msg}")
                    
            except Exception as e:
                self.logger.warning(f"Error analyzing {relative_path}: {str(e)}")

    def _report_findings(self):
        """Report all issues found"""
        self.logger.info("\nIssues Found:\n")
        
        if self.issues['syntax_errors']:
            self.logger.info("Syntax Errors to Fix:")
            for error in self.issues['syntax_errors']:
                self.logger.info(f"  - {error}")
        
        if self.issues['empty_files']:
            self.logger.info("\nEmpty Files to Remove:")
            for file in self.issues['empty_files']:
                self.logger.info(f"  - {file}")
        
        if self.issues['complex_files']:
            self.logger.info("\nComplex Files to Refactor:")
            for file in self.issues['complex_files']:
                self.logger.info(f"  - {file}")

        self.logger.info("\nRecommended Actions:")
        self.logger.info("1. Fix syntax errors in identified files")
        self.logger.info("2. Review and remove empty files if unnecessary")
        self.logger.info("3. Plan refactoring of complex files")
        
        # Create backup of files to be modified
        self._create_backup()

    def _create_backup(self):
        """Create backup of files that need modification"""
        backup_dir = self.project_root / 'backup_before_cleanup'
        if not backup_dir.exists():
            backup_dir.mkdir()
            
        # Backup files with issues
        for issue_type, files in self.issues.items():
            for file in files:
                if isinstance(file, str) and not file.endswith(')'): # Skip complex files entries
                    src_file = self.project_root / file
                    if src_file.exists():
                        dest_file = backup_dir / file
                        dest_file.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src_file, dest_file)
        
        self.logger.info(f"\nBackup created in: {backup_dir}")

def main():
    project_path = "C:/Users/maces/CernoID-Complete"
    cleanup_manager = ProjectCleanupManager(project_path)
    cleanup_manager.analyze_step1()

if __name__ == "__main__":
    main() 