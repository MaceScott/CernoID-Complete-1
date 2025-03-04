from typing import List, Optional
import numpy as np
from concurrent.futures import ThreadPoolExecutor

class BatchDetector:
    def __init__(self, batch_size: int = 4, max_workers: Optional[int] = None):
        self.batch_size = batch_size
        self.max_workers = max_workers

    def process_images(self, images: List[np.ndarray]):
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            batches = [images[i:i + self.batch_size] 
                      for i in range(0, len(images), self.batch_size)]
            results = list(executor.map(self._process_batch, batches))
        return [item for batch in results for item in batch]  # Flatten results 