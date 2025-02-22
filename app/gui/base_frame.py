import os
import logging
import yaml
import argparse
from tkinter import Tk
from app.gui.base_frame import CernoIDApp


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
        image_folder = config["IMAGE_FOLDER"]
        logs_path = config["LOGS_PATH"]

        # Configure logging system
        configure_logging(logs_path)

        # Initialize the application and start the GUI
        root = Tk()
        app = CernoIDApp(root, image_folder=image_folder)

        logging.info("Starting the application...")
        root.mainloop()

    except Exception as e:
        logging.error(f"Application encountered a critical error: {e}")
        raise


if __name__ == "__main__":
    main()
