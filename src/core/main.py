import os
import sys
import logging
import yaml
import argparse
from tkinter import Tk
from pathlib import Path

# Add the src directory to the Python path
src_dir = Path(__file__).resolve().parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from core.gui.base_frame import CernoIDApp


def load_config(config_path=None):
    """
    Loads the configuration file from the provided path, with error handling.
    """
    config_path = config_path or os.getenv("CONFIG_PATH", "config/config.yaml")

    try:
        with open(config_path, "r") as file:
            config = yaml.safe_load(file)
        logging.info(f"Configuration file loaded from: {config_path}")
        return config
    except FileNotFoundError:
        logging.error(f"Configuration file not found at: {config_path}")
        raise
    except yaml.YAMLError as e:
        logging.error(f"Error parsing the YAML configuration file: {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error while loading configuration: {e}")
        raise


def configure_logging(log_path):
    """
    Configures logging for the application and ensures the log directory exists.
    """
    try:
        log_dir = os.path.dirname(log_path)
        if log_dir:  # Only create if a directory path is provided
            os.makedirs(log_dir, exist_ok=True)

        # Setup logging configuration
        logging.basicConfig(
            filename=log_path,
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )
        logging.info("Logging configuration completed.")
    except Exception as e:
        logging.error(f"Error setting up logging: {e}")
        raise


def validate_config(config):
    """
    Validates the configuration file to ensure all required settings exist and are valid.
    """
    required_keys = [
        "BASE_DIR", "SHAPE_PREDICTOR_PATH", "FACE_RECOGNIZER_PATH",
        "IMAGE_FOLDER", "LOGS_PATH", "DATABASE_CONFIG"
    ]

    for key in required_keys:
        if key not in config:
            logging.error(f"Missing required key in configuration: {key}")
            raise KeyError(f"Configuration file is missing required key: {key}")

    # Validate paths
    if not os.path.exists(config.get("BASE_DIR", "")):
        logging.error(f"'BASE_DIR' does not exist: {config['BASE_DIR']}")
        raise FileNotFoundError(f"'BASE_DIR' does not exist: {config['BASE_DIR']}")

    if not os.path.exists(config.get("SHAPE_PREDICTOR_PATH", "")):
        logging.error(f"Shape predictor file not found: {config['SHAPE_PREDICTOR_PATH']}")
        raise FileNotFoundError(f"Shape predictor file not found: {config['SHAPE_PREDICTOR_PATH']}")

    if not os.path.exists(config.get("FACE_RECOGNIZER_PATH", "")):
        logging.error(f"Face recognizer file not found: {config['FACE_RECOGNIZER_PATH']}")
        raise FileNotFoundError(f"Face recognizer file not found: {config['FACE_RECOGNIZER_PATH']}")

    if not os.path.exists(config.get("IMAGE_FOLDER", "")):
        logging.error(f"Image folder not found: {config['IMAGE_FOLDER']}")
        raise FileNotFoundError(f"Image folder not found: {config['IMAGE_FOLDER']}")

    logging.info("Configuration validation passed successfully.")


def main():
    """
    Primary entry point for the CernoID application.
    """
    parser = argparse.ArgumentParser(description="Run the CernoID Application.")
    parser.add_argument(
        "--config-path",
        type=str,
        help="Path to the configuration file.",
        default="config/config.yaml"
    )
    args = parser.parse_args()

    try:
        # Load configuration
        config = load_config(config_path=args.config_path)

        # Validate the configuration
        validate_config(config)

        # Extract relevant configuration variables
        base_dir = config["BASE_DIR"]
        shape_predictor_path = config["SHAPE_PREDICTOR_PATH"]
        face_recognizer_path = config["FACE_RECOGNIZER_PATH"]
        image_folder = config["IMAGE_FOLDER"]
        logs_path = config["LOGS_PATH"]
        db_config = config.get("DATABASE_CONFIG", {})

        # Get database password from environment (fallback to default)
        db_password = os.getenv("DATABASE_PASSWORD", "default_password")
        if not db_password:
            logging.warning("Database password not set in environment! Using default (insecure).")
        db_config["password"] = db_password

        # Configure logging system
        configure_logging(logs_path)

        # Log the configuration information (excluding sensitive data)
        logging.info("Configuration successfully loaded.")
        logging.info(f"Base Directory: {base_dir}")
        logging.info(f"Image Folder: {image_folder}")

        # Initialize the application and start the GUI
        root = Tk()
        app = CernoIDApp(
            root=root,
            shape_predictor=shape_predictor_path,
            face_recognizer=face_recognizer_path,
            database=db_config,
            image_folder=image_folder,
        )

        logging.info("Starting the application...")
        root.mainloop()

    except Exception as e:
        logging.error(f"Application encountered a critical error: {e}")
        raise


if __name__ == "__main__":
    main()

