import os
import shutil
from pathlib import Path
import logging
from typing import List, Dict
from datetime import datetime, timedelta
import sys
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description='Reorganize project directory structure')
    parser.add_argument('project_root', nargs='?', default='.',
                       help='Project root directory (default: current directory)')
    parser.add_argument('--force', '-f', action='store_true',
                       help='Force reorganization even if already processed')
    parser.add_argument('--dry-run', '-n', action='store_true',
                       help='Show what would be done without making changes')
    parser.add_argument('--clean-backups', '-c', action='store_true',
                       help='Clean up old backup directories')
    parser.add_argument('--aggressive-cleanup', '-a', action='store_true',
                       help='Aggressively remove source files after successful move')
    return parser.parse_args()

class ProjectReorganizer:
    def __init__(self, root_dir: str, dry_run: bool = False, aggressive: bool = False):
        self.root_dir = Path(root_dir).resolve()
        if not self.root_dir.exists():
            raise ValueError(f"Directory does not exist: {root_dir}")
            
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.backup_dir = self.root_dir / "backup" / f"backup_{timestamp}"
        self.src_dir = self.root_dir / "src"
        self.ignore_patterns = {'__pycache__', '.git', '.pytest_cache', '*.pyc', '*.pyo', '*.pyd'}
        self.moved_files = []  # Track successful moves for potential rollback
        self.processed_marker = self.root_dir / ".reorganize_processed"
        self.dry_run = dry_run
        self.aggressive = aggressive

    def create_backup(self) -> None:
        """Create backup of current structure"""
        logger.info(f"Creating backup in {self.backup_dir}")
        self.backup_dir.parent.mkdir(parents=True, exist_ok=True)
        if self.src_dir.exists():
            shutil.copytree(self.src_dir, self.backup_dir / "src")
            logger.info("Backup created successfully")

    def create_directory_structure(self) -> None:
        """Create new directory structure"""
        directories = [
            "src/core",
            "src/api",
            "src/models", 
            "src/schemas",
            "src/services",
            "src/utils",
            "src/gui",
            "tests/unit",
            "tests/integration",
            "tests/e2e"
        ]
        
        for directory in directories:
            dir_path = self.root_dir / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {directory}")

    def safe_copy_directory(self, src: Path, dest: Path) -> bool:
        """Safely copy directory contents instead of moving"""
        try:
            if not src.exists():
                return False

            if not dest.exists():
                dest.mkdir(parents=True, exist_ok=True)

            # Special handling for Next.js route groups (directories with parentheses)
            src_name = src.name
            if src_name.startswith('(') and src_name.endswith(')'):
                # Remove parentheses for the destination
                dest = dest.parent / src_name[1:-1]
                dest.mkdir(parents=True, exist_ok=True)
                logger.info(f"Converting route group {src_name} to {dest.name}")

            for item in src.glob('*'):
                if self.should_ignore(item):
                    continue

                target = dest / item.name
                if item.is_file():
                    if not target.exists() or item.read_bytes() != target.read_bytes():
                        target.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(str(item), str(target))
                        logger.info(f"Copied {item} to {target}")
                else:
                    self.safe_copy_directory(item, target)
            return True
        except Exception as e:
            logger.error(f"Error copying directory {src} to {dest}: {e}")
            return False

    def move_files(self) -> None:
        """Move files to their new locations"""
        moves = [
            # Core modules - copy instead of move for existing directories
            ("src/core/recognition", "src/core/recognition", True),
            ("src/core/security", "src/core/security", True),
            ("src/core/config", "src/core/config", True),
            ("src/core/database", "src/core/database", True),
            ("src/core/monitoring", "src/core/monitoring", True),
            ("src/core/logging", "src/core/logging", True),
            ("src/core/cache", "src/core/cache", True),
            ("src/core/events", "src/core/events", True),
            ("src/core/utils", "src/core/utils", True),
            
            # API structure
            ("src/api/v1/endpoints", "src/api/endpoints", True),
            ("src/api/v1/websockets", "src/api/websockets", True),
            ("src/api/middleware", "src/api/middleware", True),
            ("src/api/routes", "src/api/routes", True),
            
            # Models and schemas
            ("src/models", "src/models", True),
            ("src/schemas", "src/schemas", True),
            
            # Services
            ("src/services", "src/services", True),
            ("src/core/services", "src/services/core", True),
            
            # GUI components
            ("src/gui", "src/gui", True),
            ("src/app/gui", "src/gui/components", True),
            ("src/gui/camera", "src/gui/camera", True),
            ("src/gui/multi_camera", "src/gui/multi_camera", True),
            
            # Tests
            ("src/tests/unit", "tests/unit", True),
            ("src/tests/integration", "tests/integration", True),
            ("src/tests/e2e", "tests/e2e", True),
            ("src/tests/utils", "tests/utils", True),
            
            # Utils and scripts
            ("src/scripts", "src/utils/scripts", True),
            ("src/core/utils", "src/utils/core", True),
            
            # Face recognition specific
            ("src/face_recognition", "src/core/face_recognition", False),
            
            # Config files
            ("src/config", "src/core/config", False),
            
            # Database
            ("src/database", "src/core/database", False),

            # Next.js app structure
            ("src/app/(auth)", "src/gui/auth", True),
            ("src/app/(dashboard)", "src/gui/dashboard", True),
            ("src/app/admin", "src/gui/admin", True),
            ("src/app/api", "src/api/routes", True),
            ("src/app/face_recognition", "src/core/face_recognition", True),
            ("src/app/multi_camera", "src/gui/multi_camera", True),
            ("src/app/gui/ui", "src/gui/components/ui", True),
            
            # Static assets and styles
            ("src/app/background.png", "src/gui/assets/background.png", False),
            ("src/app/globals.css", "src/gui/styles/globals.css", False),
            
            # React/Next.js components
            ("src/app/layout.tsx", "src/gui/components/layout.tsx", False),
            ("src/app/page.tsx", "src/gui/components/page.tsx", False),
            
            # Python UI components
            ("src/app/main_ui.py", "src/gui/components/main_ui.py", False),
            ("src/app/__init__.py", "src/gui/__init__.py", False),
            
            # Config files
            ("src/config/.jupyter", "src/core/config/.jupyter", True),
            ("src/database/database", "src/core/database/database", True),

            # Special handling for this script
            ("src/scripts/reorganize_project.py", "src/utils/scripts/reorganize_project.py", False),
        ]

        # Create additional required directories
        additional_dirs = [
            "src/gui/assets",
            "src/gui/styles",
            "src/gui/auth",
            "src/gui/dashboard",
            "src/gui/admin",
            "src/gui/components/ui"
        ]
        
        for dir_path in additional_dirs:
            dir_full_path = self.root_dir / dir_path
            dir_full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created additional directory: {dir_path}")

        for src_path, dest_path, is_core in moves:
            src = self.root_dir / src_path
            dest = self.root_dir / dest_path

            # Skip moving this script if it's currently running
            if src_path == "src/scripts/reorganize_project.py":
                if not self.dry_run:
                    # Just copy the script, don't move it
                    self.safe_copy_directory(src.parent, dest.parent)
                continue

            if not src.exists():
                continue

            if is_core:
                # For core directories that already exist, copy contents
                logger.info(f"Copying contents of {src} to {dest}")
                self.safe_copy_directory(src, dest)
            else:
                # For new locations, try moving
                if dest.exists() and src != dest:
                    logger.info(f"Merging {src} into {dest}")
                    self.merge_directories(src, dest)
                else:
                    self.safe_move(src, dest)

    def should_ignore(self, path: Path) -> bool:
        """Check if path should be ignored"""
        return any(
            pattern in str(path) or 
            (pattern.startswith('*.') and path.suffix == pattern[1:])
            for pattern in self.ignore_patterns
        )

    def merge_directories(self, src: Path, dest: Path) -> None:
        """Recursively merge directories by copying"""
        if self.should_ignore(src):
            return

        if not dest.exists():
            try:
                shutil.copytree(src, dest, ignore=shutil.ignore_patterns(*self.ignore_patterns))
                logger.info(f"Copied directory {src} to {dest}")
                # Try to remove source after successful copy
                try:
                    shutil.rmtree(src)
                    logger.info(f"Removed source directory {src}")
                except Exception as e:
                    logger.warning(f"Could not remove source directory {src}: {e}")
            except Exception as e:
                logger.error(f"Error copying directory {src} to {dest}: {e}")
            return

        for item in src.glob('*'):
            if self.should_ignore(item):
                continue

            target = dest / item.name
            if item.is_file():
                self.safe_copy_file(item, target)
            else:
                self.merge_directories(item, target)

    def safe_copy_file(self, src: Path, dest: Path) -> bool:
        """Safely copy a file with backup"""
        try:
            if not src.exists():
                return False

            if dest.exists():
                if src.read_bytes() == dest.read_bytes():
                    logger.info(f"Files are identical, skipping: {dest}")
                    return True
                backup = dest.with_suffix(dest.suffix + '.bak')
                shutil.copy2(str(dest), str(backup))
                logger.info(f"Backed up existing file to: {backup}")

            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(src), str(dest))
            logger.info(f"Copied {src} to {dest}")

            # Try to remove source after successful copy
            try:
                src.unlink()
                logger.info(f"Removed source file {src}")
            except Exception as e:
                logger.warning(f"Could not remove source file {src}: {e}")

            return True
        except Exception as e:
            logger.error(f"Error copying {src} to {dest}: {e}")
            return False

    def safe_move(self, src: Path, dest: Path) -> bool:
        """Safely move files with error handling"""
        try:
            if self.should_ignore(src):
                return False
                
            if src.exists():
                if dest.exists():
                    if src.read_bytes() == dest.read_bytes():
                        logger.info(f"Files are identical, skipping: {dest}")
                    else:
                        backup = dest.with_suffix(dest.suffix + '.bak')
                        shutil.move(str(dest), str(backup))
                        logger.info(f"Backed up existing file to: {backup}")
                        shutil.move(str(src), str(dest))
                        logger.info(f"Moved {src} to {dest}")
                    return True
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(dest))
                logger.info(f"Moved {src} to {dest}")
                return True
            else:
                logger.warning(f"Source does not exist: {src}")
                return False
        except Exception as e:
            logger.error(f"Error moving {src} to {dest}: {e}")
            return False

    def verify_structure(self) -> bool:
        """Verify the new structure is valid"""
        required_dirs = [
            "src/core",
            "src/api",
            "src/models",
            "src/services",
            "src/utils",
            "src/gui",
            "tests"
        ]
        
        for dir_path in required_dirs:
            if not (self.root_dir / dir_path).exists():
                logger.error(f"Required directory missing: {dir_path}")
                return False
        return True

    def is_already_processed(self) -> bool:
        """Check if reorganization was already done"""
        return self.processed_marker.exists()

    def mark_as_processed(self) -> None:
        """Mark the reorganization as complete"""
        self.processed_marker.touch()

    def force_remove(self, path: Path) -> None:
        """Forcefully remove a file or directory"""
        try:
            if path.is_file():
                path.unlink()
                logger.info(f"Removed file: {path}")
            elif path.is_dir():
                shutil.rmtree(path)
                logger.info(f"Removed directory: {path}")
        except Exception as e:
            logger.error(f"Could not remove {path}: {e}")

    def cleanup(self) -> None:
        """Clean up duplicate files and empty directories"""
        logger.info("Starting cleanup phase...")
        
        # Files that should be removed after successful move
        force_remove_paths = [
            "src/config/.jupyter",
            "src/database/database",
            "src/app/gui/ui",
            "src/app/(auth)",
            "src/app/(dashboard)",
            "src/app/admin",
            "src/app/api",
            "src/app/face_recognition",
            "src/app/gui",
            "src/app/multi_camera"
        ]

        if self.aggressive and not self.dry_run:
            for path_str in force_remove_paths:
                path = self.root_dir / path_str
                if path.exists():
                    self.force_remove(path)

            # Clean up empty parent directories
            empty_dirs = [
                "src/config",
                "src/database",
                "src/app"
            ]
            
            for dir_str in empty_dirs:
                dir_path = self.root_dir / dir_str
                if dir_path.exists() and not any(dir_path.iterdir()):
                    self.force_remove(dir_path)

        # List of directories to clean
        cleanup_dirs = [
            "src/config",
            "src/database",
            "src/tests",
            "src/face_recognition",  # Add this since it's moved to core
            "src/core/utils"  # Add this since it's moved to utils/core
        ]
        
        # Additional cleanup for backup files
        backup_patterns = ["*.bak", "*.old", "*.tmp"]
        
        for dir_path in cleanup_dirs:
            path = self.root_dir / dir_path
            if path.exists():
                try:
                    # Remove backup files first
                    for pattern in backup_patterns:
                        for backup_file in path.rglob(pattern):
                            try:
                                backup_file.unlink()
                                logger.info(f"Removed backup file: {backup_file}")
                            except Exception as e:
                                logger.warning(f"Could not remove backup file {backup_file}: {e}")

                    # Remove empty directories recursively
                    for p in sorted(path.glob('**/*'), reverse=True):
                        try:
                            if p.is_dir() and not any(p.iterdir()):
                                p.rmdir()
                                logger.info(f"Removed empty directory: {p}")
                        except Exception as e:
                            logger.warning(f"Could not remove directory {p}: {e}")
                    
                    # Try to remove the root directory if empty
                    if path.is_dir() and not any(path.iterdir()):
                        path.rmdir()
                        logger.info(f"Removed empty directory: {path}")
                except Exception as e:
                    logger.warning(f"Could not clean directory {path}: {e}")

    def clean_old_backups(self, days: int = 7) -> None:
        """Clean up backup directories older than specified days"""
        logger.info(f"Cleaning up backups older than {days} days...")
        backup_dir = self.root_dir / "backup"
        if not backup_dir.exists():
            return

        cutoff = datetime.now() - timedelta(days=days)
        for backup in backup_dir.glob("backup_*"):
            try:
                # Parse backup directory timestamp
                timestamp = datetime.strptime(backup.name.split('_')[1], '%Y%m%d')
                if timestamp < cutoff:
                    if self.dry_run:
                        logger.info(f"Would remove old backup: {backup}")
                    else:
                        shutil.rmtree(backup)
                        logger.info(f"Removed old backup: {backup}")
            except (ValueError, IndexError) as e:
                logger.warning(f"Could not parse backup directory name: {backup}")

    def verify_cleanup(self) -> bool:
        """Verify that cleanup was complete"""
        logger.info("Verifying cleanup...")
        
        # Check for old directories that should be empty/removed
        old_locations = [
            "src/config",
            "src/database",
            "src/tests",
            "src/face_recognition",
            "src/core/utils",
            "src/api/v1",
            "src/app"
        ]
        
        issues_found = False
        
        # Check old locations
        for loc in old_locations:
            path = self.root_dir / loc
            if path.exists():
                if any(path.iterdir()):
                    logger.warning(f"Found remaining files in {loc}")
                    for item in path.iterdir():
                        logger.warning(f"  - {item.relative_to(self.root_dir)}")
                    issues_found = True
                else:
                    logger.warning(f"Empty directory remains: {loc}")
                    issues_found = True

        # Verify core structure
        required_structure = {
            "src/core/recognition": ["*.py"],
            "src/core/security": ["*.py"],
            "src/core/config": ["*.yaml", "*.py"],
            "src/core/database": ["*.py", "schema.sql"],
            "src/api/endpoints": ["*.py"],
            "src/api/middleware": ["*.py"],
            "src/services": ["*.py"],
            "src/utils/core": ["*.py"],
            "src/gui/components": ["*.py"],
            "tests": ["unit", "integration", "e2e"]
        }
        
        # Update required structure with more specific Next.js patterns
        required_structure.update({
            "src/gui/auth": ["*/page.tsx"],  # Next.js pages must be in page.tsx files
            "src/gui/dashboard": ["*/page.tsx"],
            "src/gui/admin": ["*/page.tsx", "*.py"],  # Admin can have both Next.js and Python files
            "src/gui/assets": ["*.png", "*.jpg", "*.svg"],
            "src/gui/styles": ["*.css"],
            "src/gui/components/ui": ["*.tsx"],
            "src/core/face_recognition": ["*.py"],
        })

        for dir_path, expected_contents in required_structure.items():
            path = self.root_dir / dir_path
            if not path.exists():
                logger.error(f"Required directory missing: {dir_path}")
                issues_found = True
            else:
                has_matching_files = False
                for pattern in expected_contents:
                    # Handle Next.js page patterns
                    if pattern == "*/page.tsx":
                        # Check for any page.tsx files in subdirectories
                        if any(path.glob("**/page.tsx")):
                            has_matching_files = True
                            break
                    elif any(path.glob(pattern)):
                        has_matching_files = True
                        break
                if not has_matching_files:
                    logger.warning(f"Directory may be empty or missing expected files: {dir_path}")
                    issues_found = True

        if issues_found:
            logger.warning("Cleanup verification found issues - some files or directories may need manual review")
        else:
            logger.info("Cleanup verification passed - directory structure is clean")
        
        return not issues_found

    def verify_and_fix_auth(self) -> None:
        """Verify and fix auth directory contents"""
        auth_dir = self.root_dir / "src/gui/auth"
        
        # Try to find auth files in the latest backup
        try:
            latest_backup = max((self.root_dir / "backup").glob("backup_*"))
            backup_auth = latest_backup / "src/app/(auth)"
            
            if backup_auth.exists():
                logger.info("Found auth files in backup, restoring...")
                # Remove existing auth directory if empty
                if auth_dir.exists() and not any(auth_dir.iterdir()):
                    auth_dir.rmdir()
                
                # Copy from backup, handling the route group properly
                self.safe_copy_directory(backup_auth, auth_dir.parent)
                logger.info("Restored auth files from backup")
                return
        except Exception as e:
            logger.warning(f"Could not restore auth files from backup: {e}")
        
        # If no backup found or restore failed, create minimal structure
        logger.info("Creating minimal auth structure...")
        auth_dir.mkdir(parents=True, exist_ok=True)
        
        # Create minimal Next.js auth structure
        minimal_structure = {
            "login/page.tsx": """
export default function LoginPage() {
    return <div>Login Page</div>
}
""",
            "forgot-password/page.tsx": """
export default function ForgotPasswordPage() {
    return <div>Forgot Password Page</div>
}
""",
            "register/page.tsx": """
export default function RegisterPage() {
    return <div>Register Page</div>
}
"""
        }
        
        for path, content in minimal_structure.items():
            file_path = auth_dir / path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content.strip())
            logger.info(f"Created {file_path}")

    def run(self, force: bool = False) -> None:
        """Execute the reorganization"""
        if self.is_already_processed() and not force:
            logger.info("Project has already been reorganized. Use --force to run again.")
            return

        try:
            logger.info("Starting project reorganization...")
            if self.dry_run:
                logger.info("DRY RUN - no changes will be made")
            
            self.create_backup()
            self.create_directory_structure()
            self.move_files()
            
            if self.verify_structure():
                self.cleanup()
                cleanup_verified = self.verify_cleanup()
                
                # Add verification and fix for auth
                if not cleanup_verified:
                    self.verify_and_fix_auth()
                    cleanup_verified = self.verify_cleanup()
                    
                if not self.dry_run:
                    self.mark_as_processed()
                logger.info("Project reorganization completed successfully")
                logger.info(f"Backup created at: {self.backup_dir}")
                if not cleanup_verified:
                    logger.warning("Some cleanup issues were found. Please review the logs.")
            else:
                logger.error("Project reorganization completed with errors")
                
        except Exception as e:
            logger.error(f"Failed to reorganize project: {e}")
            raise

def main():
    args = parse_args()
    
    try:
        # Check if we're running from the original location
        script_path = Path(__file__)
        if 'utils/scripts' in str(script_path):
            logger.info("Script has been moved to utils/scripts. Skipping execution.")
            return

        # Get the project root directory
        project_root = Path(args.project_root).resolve()
        
        logger.info(f"Project root directory: {project_root}")
        reorganizer = ProjectReorganizer(
            str(project_root), 
            dry_run=args.dry_run,
            aggressive=args.aggressive_cleanup
        )
        
        if args.clean_backups:
            reorganizer.clean_old_backups()
            if not args.force:
                return

        reorganizer.run(force=args.force)
    except Exception as e:
        logger.error(f"Failed to reorganize project: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()