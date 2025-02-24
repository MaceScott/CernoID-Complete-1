from functools import lru_cache

@lru_cache(maxsize=1000)
def compute_face_encoding(face_image: np.ndarray) -> np.ndarray:
    # Your existing encoding logic
    pass 