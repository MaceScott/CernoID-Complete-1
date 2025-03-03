import logging
import sys
import argparse
from typing import Optional
from pathlib import Path
import shutil
from merge_plan import ProjectMerger
from cleanup import ProjectCleaner
import os


class CustomScript:
    """
    A base structure for a professional and extensible Python script.
    This class provides common functionality for building scalable scripts.
    """

    def __init__(self, config: Optional[dict] = None):
        """
        Initialize the script with optional configuration.

        :param config: Optional dictionary to hold dynamic configurations.
        """
        self.config = config or {}
        self.logger = self.setup_logger()

    def setup_logger(self, level: int = logging.INFO) -> logging.Logger:
        """
        Setup a logger for the script.

        :param level: Logging level (e.g., DEBUG, INFO).
        :return: A configured logger object.
        """
        logger = logging.getLogger(__name__)
        logger.setLevel(level)
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def run(self, operation: str, **kwargs) -> None:
        """
        Main execution method to decide the operation.

        :param operation: The operation or task to perform.
        :param kwargs: Additional parameters required for the operation.
        """
        self.logger.info(f"Running operation: {operation}")

        if operation == "example_task":
            self.example_task(kwargs.get("param1", "Default Param"))
        else:
            self.logger.error(f"Unknown operation: {operation}")

    def example_task(self, param: str) -> None:
        """
        Example task to demonstrate functionality.

        :param param: A sample parameter for demonstration.
        """
        self.logger.info(f"Executing example task with param: {param}")
        # Add task-specific logic here
        self.logger.debug("Debugging details for the example task.")
        print(f"Example task completed with param: {param}")

    def cleanup(self) -> None:
        """
        Perform any script cleanup tasks.
        """
        self.logger.info("Performing cleanup...")
        # Add any necessary resource cleanup logic here


def parse_arguments():
    """
    Parse command-line arguments provided to the script.

    :return: Parsed arguments as a Namespace object.
    """
    parser = argparse.ArgumentParser(description="Custom Script for Various Operations")
    parser.add_argument("-o", "--operation", type=str, required=True,
                        help="The operation to perform (e.g., 'example_task').")
    parser.add_argument("-p", "--param1", type=str, default=None,
                        help="Parameter for the specified operation.")
    parser.add_argument("-l", "--loglevel", type=str, default="INFO",
                        help="Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL.")
    return parser.parse_args()


def main():
    project_root = Path("C:/Users/maces/CernoID-Complete")
    
    # Run mergers
    merger = ProjectMerger(project_root)
    merger.merge_face_recognition()
    merger.merge_admin_utils()
    merger.merge_auth_services()
    
    # Run cleanup
    cleaner = ProjectCleaner(project_root)
    cleaner.remove_pycache()
    cleaner.remove_redundant_configs()
    cleaner.create_gitignore()
    cleaner.organize_configs()
    
    print("Project cleanup and merging completed. Check merge_operations.log and cleanup_operations.log for details.")

    # Read the log files to see what happened
    with open('merge_operations.log', 'r') as f:
        print("Merge operations:")
        print(f.read())
    
    with open('cleanup_operations.log', 'r') as f:
        print("\nCleanup operations:")
        print(f.read())

    def print_directory_structure(startpath):
        for root, dirs, files in os.walk(startpath):
            level = root.replace(startpath, '').count(os.sep)
            indent = ' ' * 4 * level
            print(f'{indent}{os.path.basename(root)}/')
            subindent = ' ' * 4 * (level + 1)
            for f in files:
                print(f'{subindent}{f}')

    print_directory_structure('.')


if __name__ == "__main__":
    main()

cv2.destroyAllWindows()