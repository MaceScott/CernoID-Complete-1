from pathlib import Path
import shutil
import logging

class SafePycacheCleaner:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.setup_logging()

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def clean(self):
        self.logger.info("\n=== Safe __pycache__ Cleanup ===\n")
        
        # Define safe project directories to clean
        safe_dirs = [
            'app',
            'backend',
            'src',
            'tests'
        ]
        
        cleaned_count = 0
        for safe_dir in safe_dirs:
            dir_path = self.project_root / safe_dir
            if dir_path.exists():
                # Find pycache in this directory
                pycache_dirs = list(dir_path.rglob('__pycache__'))
                for pycache_dir in pycache_dirs:
                    shutil.rmtree(pycache_dir)
                    cleaned_count += 1
                    self.logger.info(f"Removed: {pycache_dir.relative_to(self.project_root)}")

        self.logger.info(f"\nCleaned {cleaned_count} __pycache__ directories from project code")
        self.logger.info("(Skipped dependency directories for safety)")

def main():
    project_path = "C:/Users/maces/CernoID-Complete"
    cleaner = SafePycacheCleaner(project_path)
    cleaner.clean()

if __name__ == "__main__":
    main() 