from pathlib import Path
import ast
import logging

class ProjectCodeAnalyzer:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.setup_logging()

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def analyze(self):
        self.logger.info("\n=== Project Code Analysis ===\n")
        
        # Only analyze these project-specific directories
        project_dirs = [
            'app',
            'backend',
            'src',
            'tests'
        ]
        
        for dir_name in project_dirs:
            dir_path = self.project_root / dir_name
            if dir_path.exists():
                self.logger.info(f"\nAnalyzing {dir_name}/:")
                self._analyze_directory(dir_path)
            else:
                self.logger.info(f"\n{dir_name}/ not found")

    def _analyze_directory(self, directory: Path):
        """Analyze a specific project directory"""
        # Find all Python files in this directory
        python_files = list(directory.rglob('*.py'))
        
        if not python_files:
            self.logger.info("  No Python files found")
            return
            
        self.logger.info(f"  Found {len(python_files)} Python files")
        
        # Analyze each Python file
        for py_file in python_files:
            relative_path = py_file.relative_to(self.project_root)
            self.logger.info(f"\n  {relative_path}:")
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    tree = ast.parse(content)
                    
                # Count functions and classes
                functions = len([node for node in ast.walk(tree) 
                               if isinstance(node, ast.FunctionDef)])
                classes = len([node for node in ast.walk(tree) 
                             if isinstance(node, ast.ClassDef)])
                
                # Get project-specific imports
                imports = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom) and node.module:
                        if any(node.module.startswith(dir_) 
                              for dir_ in ['app', 'backend', 'src']):
                            imports.append(node.module)
                
                self.logger.info(f"    Functions: {functions}")
                self.logger.info(f"    Classes: {classes}")
                if imports:
                    self.logger.info("    Project imports:")
                    for imp in imports:
                        self.logger.info(f"      - {imp}")
                
            except Exception as e:
                self.logger.warning(f"    Error analyzing file: {str(e)}")

def main():
    project_path = "C:/Users/maces/CernoID-Complete"
    analyzer = ProjectCodeAnalyzer(project_path)
    analyzer.analyze()

if __name__ == "__main__":
    main() 