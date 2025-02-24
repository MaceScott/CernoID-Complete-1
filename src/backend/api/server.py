import os
import logging
from api import app


def get_config():
    """
    Load configuration for the server from environment variables or use defaults.
    """
    return {
        "host": os.getenv("HOST", "127.0.0.1"),  # Default to localhost
        "port": int(os.getenv("PORT", 5000)),  # Default to port 5000
        "debug": os.getenv("DEBUG", "False").lower() in ["true", "1"],  # Boolean conversion
    }


def setup_logging():
    """
    Configure logging for the application.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler()  # Logs to console
        ]
    )
    logging.info("Logging is configured.")


def start_server():
    """
    Starts the CernoID API server.
    """
    config = get_config()

    try:
        # Log basic server information
        logging.info(
            f"Starting the CernoID API server on {config['host']}:{config['port']} "
            f"in {'debug' if config['debug'] else 'production'} mode..."
        )

        # Start the server
        app.run(
            host=config["host"],
            port=config["port"],
            debug=config["debug"]
        )
    except Exception as e:
        # Catch any errors during startup and log them
        logging.error(f"Failed to start the server: {e}", exc_info=True)


if __name__ == "__main__":
    setup_logging()
    start_server()
