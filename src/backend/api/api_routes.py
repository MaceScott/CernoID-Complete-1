import sys
import os
import uuid
import logging
import imghdr
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
from app.face_recognition.face_matching import match_faces
from app.face_recognition.face_encoding import encode_faces
from config import IMAGE_FOLDER  # Ensure config.py exists and IMAGE_FOLDER is defined
from fastapi import FastAPI, UploadFile
import asyncio
from typing import List

# Load environment variables (from .env file if exists)
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Logging setup
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Ensure the folder for uploaded images exists
os.makedirs(IMAGE_FOLDER, exist_ok=True)

# Configure the app
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB file size limit

# Set up rate limiter
limiter = Limiter(get_remote_address, app=app)


# Utility function for saving uploaded files securely
def save_uploaded_file(file, folder):
    """
    Securely save the uploaded file and return its path.
    """
    filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4()}_{filename}"  # Add a UUID to prevent duplicates
    file_path = os.path.join(folder, unique_filename)

    try:
        file.save(file_path)
    except Exception as e:
        logging.error(f"Error saving file: {e}")
        raise ValueError(f"Could not save file: {e}")

    # Validate if the file is a valid image
    if not imghdr.what(file_path):
        os.remove(file_path)  # Clean up invalid files
        raise ValueError("Uploaded file is not a valid image.")

    return file_path


# Endpoint to encode faces
@limiter.limit("10 per minute")
@app.route("/encode", methods=["POST"])
def encode_image():
    """
    API endpoint for encoding faces from an uploaded image.
    """
    if "image" not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    image = request.files["image"]

    try:
        # Save the uploaded file
        image_path = save_uploaded_file(image, IMAGE_FOLDER)

        # Get face encodings from the image
        encodings = encode_faces(image_path)
        return jsonify({"encodings": [e.tolist() for e in encodings]}), 200

    except ValueError as ve:
        logging.warning(f"Validation error: {ve}")
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        logging.exception(f"Unexpected error during encoding: {e}")
        return jsonify({"error": "An internal error occurred"}), 500


# Endpoint to match two images
@limiter.limit("10 per minute")
@app.route("/match", methods=["POST"])
def match_images():
    """
    API endpoint to match faces in two uploaded images.
    """
    if "image1" not in request.files or "image2" not in request.files:
        return jsonify({"error": "Two image files (image1, image2) must be provided"}), 400

    image1 = request.files["image1"]
    image2 = request.files["image2"]

    try:
        # Save uploaded files securely
        image1_path = save_uploaded_file(image1, IMAGE_FOLDER)
        image2_path = save_uploaded_file(image2, IMAGE_FOLDER)

        # Match faces in the two images
        match_result = match_faces(image1_path, image2_path)
        return jsonify({"match": match_result}), 200

    except ValueError as ve:
        logging.warning(f"Validation error: {ve}")
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        logging.exception(f"Unexpected error during matching: {e}")
        return jsonify({"error": "An internal error occurred"}), 500


# Handle file size limit exceeded errors
@app.errorhandler(413)
def request_entity_too_large(error):
    """
    Handle requests for files larger than the allowed size (16 MB).
    """
    logging.warning("Request exceeded file size limit.")
    return jsonify({"error": "File size exceeds the maximum allowed size of 16 MB"}), 413


if __name__ == "__main__":
    """
    Run the Flask app using host and port configurations, 
    with the option to enable debugging mode.
    """
    # Read configurations from environment variables
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_PORT", 5000))
    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() in ["true", "1"]

    # Run the Flask app
    app.run(debug=debug_mode, host=host, port=port)

