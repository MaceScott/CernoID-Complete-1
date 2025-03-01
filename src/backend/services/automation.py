import json
import logging
import numpy as np
from pathlib import Path
from typing import List, Dict, Any
from face_matching import match_faces
from extract_embeddings import extract_embeddings
from config import IMAGE_FOLDER

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("automation.log"),  # Logs are written to a file
        logging.StreamHandler()  # Logs are also output to the console
    ]
)


def validate_folder(folder_path: str) -> Path:
    """
    Validates that a folder path exists and is accessible.

    Args:
        folder_path (str): Path to the folder.

    Returns:
        Path: A valid Path object pointing to the folder.

    Raises:
        ValueError: If the folder does not exist or is not a directory.
    """
    path = Path(folder_path)
    if not path.exists() or not path.is_dir():
        raise ValueError(f"Provided folder path is invalid or does not exist: {folder_path}")
    return path


def extract_image_embeddings(image_folder: Path, output_file: Path) -> None:
    """
    Extract embeddings for images located in the given folder.

    Args:
        image_folder (Path): Path to the folder containing images.
        output_file (Path): File to save the extracted embeddings.

    Returns:
        None
    """
    logging.info("Starting the extraction of embeddings...")
    # Call custom embeddings extractor
    extract_embeddings(str(image_folder), str(output_file))
    logging.info(f"Embeddings successfully saved to: {output_file}")


def load_embeddings(embeddings_file: Path) -> Dict[str, Any]:
    """
    Load image embeddings from a .npy file.

    Args:
        embeddings_file (Path): Path to the NumPy file containing embeddings.

    Returns:
        Dict[str, Any]: A dictionary of embeddings data loaded from the file.

    Raises:
        FileNotFoundError: If the embeddings file does not exist.
        ValueError: If the file contents are invalid or corrupt.
    """
    try:
        logging.info(f"Loading embeddings from: {embeddings_file}")
        embeddings = np.load(embeddings_file, allow_pickle=True).item()
        if not isinstance(embeddings, dict):
            raise ValueError("Invalid format: Embeddings file does not contain a valid dictionary.")
        return embeddings
    except Exception as exc:
        raise ValueError(f"Failed to load embeddings: {exc}")


def match_images(embeddings: Dict[str, Any], image_folder: Path) -> List[Dict[str, Any]]:
    """
    Matches all image pairs using their embeddings with optimized parallel processing.

    Args:
        embeddings (Dict): Dictionary where keys are image names and values are embeddings.
        image_folder (Path): Path to the folder containing the images.

    Returns:
        List[Dict[str, Any]]: A list of match results containing compared image pairs and whether they matched.
    """
    from concurrent.futures import ThreadPoolExecutor

    logging.info("Starting optimized image matching process...")

    def match_pair(pair):
        img1, img2 = pair
        match = match_faces(image_folder / img1, image_folder / img2)
        return {"image1": img1, "image2": img2, "match": match}

    images = list(embeddings.keys())
    pairs = [(images[i], images[j]) for i in range(len(images)) for j in range(i + 1, len(images))]

    with ThreadPoolExecutor() as executor:
        results = list(executor.map(match_pair, pairs))

    logging.info(f"Completed optimized matching of {len(results)} image pairs.")
    return results


def save_results_to_json(results: List[Dict[str, Any]], output_file: Path) -> None:
    """
    Saves the final matching results to a JSON file.

    Args:
        results (List[Dict]): A list of dictionaries containing match results.
        output_file (Path): Path to the output JSON file.

    Returns:
        None
    """
    with open(output_file, "w") as f:
        json.dump(results, f, indent=4)
    logging.info(f"Results successfully saved to: {output_file}")


def batch_process_images(image_folder: str, output_file: str) -> None:
    """
    The main function to process images in bulk: extract embeddings, match pairs, and save results.

    Args:
        image_folder (str): Path to the folder containing images.
        output_file (str): Path to save the results of image processing.

    Returns:
        None
    """
    try:
        # Validate paths
        image_folder_path = validate_folder(image_folder)
        embeddings_file = Path(output_file).with_suffix('.npy')
        results_file = Path(output_file).with_suffix('.json')

        # Step 1: Extract Embeddings
        extract_image_embeddings(image_folder_path, embeddings_file)

        # Step 2: Load Embeddings
        embeddings = load_embeddings(embeddings_file)

        # Step 3: Match Images
        results = match_images(embeddings, image_folder_path)

        # Step 4: Save Results
        save_results_to_json(results, results_file)

        logging.info("Batch processing completed successfully.")
    except Exception as e:
        logging.error(f"An error occurred during batch processing: {e}")


if __name__ == "__main__":
    # Base name for output files
    output_file_name = "results"

    try:
        # Main entry point for image batch processing
        batch_process_images(IMAGE_FOLDER, output_file_name)
    except Exception as e:
        logging.critical(f"A critical error occurred in the main function: {e}")

