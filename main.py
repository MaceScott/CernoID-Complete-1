import os
import logging
import yaml
from app.gui.base_frame import CernoIDApp  # Adjust according to your project structure


def load_config(config_path="config/config.yaml"):
    """
    Loads the configuration file from the provided path.
    """
    with open(config_path, "r") as file:
        config = yaml.safe_load(file)
    return config


def configure_logging(log_path):
    """
    Sets up logging for the application.
    """
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    logging.basicConfig(
        filename=log_path,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    logging.info("Application started.")


def main():
    """
    Main entry point for the application.
    """
    # Load configuration
    config = load_config()

    # Extract variables from the configuration
    base_dir = config.get("BASE_DIR")
    shape_predictor_path = config.get("SHAPE_PREDICTOR_PATH")
    face_recognizer_path = config.get("FACE_RECOGNIZER_PATH")
    image_folder = config.get("IMAGE_FOLDER")
    logs_path = config.get("LOGS_PATH")
    db_config = config.get("DATABASE_CONFIG", {})

    # Replace database password with environment variable value
    db_password = os.getenv("DATABASE_PASSWORD", "")
    db_config["password"] = db_password

    # Configure logging
    configure_logging(logs_path)

    # Log the configuration (excluding sensitive data)
    logging.info("Configuration loaded successfully.")
    logging.info(f"Base Directory: {base_dir}")
    logging.info(f"Image Folder: {image_folder}")

    # Initialize the app (assuming it's a GUI application)
    app = CernoIDApp(
        base_dir=base_dir,
        shape_predictor=shape_predictor_path,
        face_recognizer=face_recognizer_path,
        image_folder=image_folder,
        database=db_config,
    )

    # Run the app's main loop
    app.run()


if __name__ == "__main__":
    main()
