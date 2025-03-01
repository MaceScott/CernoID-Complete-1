import os
import numpy as np
import logging
from functools import lru_cache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NoFacesDetectedError(Exception):
    """Raised when no faces are detected in one or both images."""
    pass


def match_faces(image1_path, image2_path, threshold=0.6):
    """
    Compare faces from two images to verify if they match.

    Args:
        image1_path (str): Path to the first image.
        image2_path (str): Path to the second image.
        threshold (float): Matching threshold (default: 0.6).

    Returns:
        bool: True if faces match, False otherwise.

    Raises:
        ValueError: If inputs are invalid.
        FileNotFoundError: If image paths do not exist.
        NoFacesDetectedError: If no faces are detected in one or both images.
    """
    # Validate inputs
    if not isinstance(threshold, float) or not (0 <= threshold <= 1):
        raise ValueError("Threshold must be a float value between 0 and 1.")
    if not os.path.isfile(image1_path) or not os.path.isfile(image2_path):
        raise FileNotFoundError("One or both image paths do not exist.")

    try:
        from app.face_recognition.face_encoding import encode_faces

        # Generate encodings for both images
        encodings1 = encode_faces(image1_path)
        encodings2 = encode_faces(image2_path)

        if not encodings1 or not encodings2:
            raise NoFacesDetectedError("No faces detected in one or both images.")

        # Use the first detected face in each image
        encoding1 = encodings1[0]
        encoding2 = encodings2[0]

        # Compute the distance between the two encodings
        distance = np.linalg.norm(encoding1 - encoding2)
        return distance <= threshold

    except NoFacesDetectedError as e:
        # Directly propagate this specific exception
        raise e
    except ValueError as e:
        # Handle invalid input values explicitly
        raise ValueError(f"Invalid value encountered: {e}")
    except FileNotFoundError as e:
        # Handle missing file paths explicitly
        raise FileNotFoundError(f"File not found error: {e}")
    except ImportError as e:
        # Handle errors related to importing modules
        raise ImportError(f"An import error occurred: {e}")
    except Exception as e:
        # Catch any other unexpected exceptions
        raise RuntimeError(f"An unexpected error occurred: {e}")


@lru_cache(maxsize=100)
def cached_encode_faces(image_path):
    from app.face_recognition.face_encoding import encode_faces
    return encode_faces(image_path)


# Enhanced logging for face matching
logger.info(f"Matching faces from {image1_path} and {image2_path} with threshold {threshold}")

# Replace encode_faces with cached_encode_faces
encodings1 = cached_encode_faces(image1_path)
encodings2 = cached_encode_faces(image2_path)

# Enhanced logging for distance calculation
logger.info(f"Calculated distance between faces: {distance}")

