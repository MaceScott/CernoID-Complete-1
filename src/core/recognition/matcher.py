from typing import Dict, List, Optional, Tuple, Union, Any
import numpy as np
from datetime import datetime
import asyncio
from dataclasses import dataclass
from pathlib import Path
import faiss
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from ..utils.config import get_settings
from ..utils.logging import get_logger
from .encoder import EncodingResult

from ..base import BaseComponent
from ..utils.errors import MatcherError
from ..utils.metrics import PerformanceMetrics

@dataclass
class MatchResult:
    """Face matching result with confidence and metadata"""
    person_id: str
    confidence: float
    encoding_id: str
    quality_score: float
    metadata: Dict[str, Any]
    match_time: float

class FaceMatcher(BaseComponent):
    """
    Advanced face matcher with FAISS indexing and clustering
    """
    
    def __init__(self, config: dict):
        self._validate_config(config)
        super().__init__(config)
        
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        
        # Matching settings
        self._matching_threshold = config.get('matcher.threshold', 0.6)
        self._index_size = config.get('matcher.index_size', 128)  # Face encoding size
        self._batch_size = config.get('matcher.batch_size', 32)
        
        # Initialize FAISS index for fast similarity search
        self._index = self._create_index()
        
        # Face storage
        self._face_data: Dict[str, Dict] = {}
        self._next_id = 0
        
        # Processing state
        self._processing = False
        self._index_lock = asyncio.Lock()
        
        # Performance monitoring
        self._metrics = PerformanceMetrics()
        
        # Statistics
        self._stats = {
            'total_faces': 0,
            'total_matches': 0,
            'average_match_time': 0.0,
            'false_positives': 0,
            'false_negatives': 0
        }
        
        # Initialize thread pool
        self.thread_pool = ThreadPoolExecutor(
            max_workers=self.settings.matcher_threads
        )
        
        # Cache for frequent matches
        self.match_cache = {}
        
        # Initialize clustering
        self.clusters = defaultdict(list)
        self.cluster_centers = {}

    def _validate_config(self, config: dict) -> None:
        """Validate matcher configuration"""
        required_keys = [
            'matcher.threshold',
            'matcher.index_type',
            'matcher.metric'
        ]
        
        for key in required_keys:
            if not self._get_nested_config(config, key):
                raise MatcherError(f"Missing required config: {key}")

    def _create_index(self) -> faiss.Index:
        """Create FAISS index for fast matching"""
        dimension = self._index_size
        
        if self.settings.use_gpu and faiss.get_num_gpus() > 0:
            # GPU index
            index = faiss.IndexFlatL2(dimension)
            index = faiss.index_cpu_to_gpu(
                faiss.StandardGpuResources(),
                0,
                index
            )
        else:
            # CPU index
            index = faiss.IndexFlatL2(dimension)
            
        return index

    async def add_face(self, face_id: str, encoding: np.ndarray, metadata: Dict) -> bool:
        """Add face encoding to matcher"""
        try:
            async with self._index_lock:
                # Validate encoding
                if not self._validate_encoding(encoding):
                    raise ValueError("Invalid face encoding")
                
                # Normalize encoding
                encoding = self._normalize_encoding(encoding)
                
                # Add to index
                self._index.add(encoding.reshape(1, -1))
                
                # Store face data
                self._face_data[face_id] = {
                    'id': face_id,
                    'index': self._next_id,
                    'metadata': metadata,
                    'added_at': datetime.utcnow().isoformat()
                }
                
                self._next_id += 1
                self._stats['total_faces'] += 1
                
                # Update clusters
                await self._update_clusters(face_id, encoding)
                
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to add face: {str(e)}")
            return False

    async def find_matches(self, encoding: np.ndarray, max_matches: int = 5) -> List[MatchResult]:
        """Find matching faces for encoding"""
        try:
            async with self._metrics.measure('matching_time'):
                # Validate encoding
                if not self._validate_encoding(encoding):
                    raise ValueError("Invalid face encoding")
                
                # Normalize encoding
                encoding = self._normalize_encoding(encoding)
                
                # Check cache first
                cache_key = self._get_cache_key(encoding)
                if cache_key in self.match_cache:
                    return self.match_cache[cache_key]
                
                # Search index
                distances, indices = self._index.search(
                    encoding.reshape(1, -1),
                    max_matches
                )
                
                # Process results
                matches = []
                for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
                    if idx != -1:  # Valid match
                        # Convert distance to confidence
                        confidence = self._distance_to_confidence(distance)
                        
                        if confidence >= self._matching_threshold:
                            # Find face_id for index
                            face_id = self._get_face_id(idx)
                            if face_id:
                                match = MatchResult(
                                    person_id=face_id,
                                    confidence=confidence,
                                    encoding_id=str(idx),
                                    quality_score=self._face_data[face_id]['metadata'].get('quality_score', 0.0),
                                    metadata=self._face_data[face_id]['metadata'],
                                    match_time=time.time() - self._metrics.get_start('matching_time')
                                )
                                matches.append(match)
                
                self._stats['total_matches'] += len(matches)
                
                # Cache results
                if matches:
                    self.match_cache[cache_key] = matches
                
                return matches
                
        except Exception as e:
            self.logger.error(f"Face matching failed: {str(e)}")
            raise MatcherError(f"Matching failed: {str(e)}")

    def _normalize_encoding(self, encoding: np.ndarray) -> np.ndarray:
        """Normalize face encoding"""
        # Ensure correct shape
        if len(encoding.shape) == 1:
            encoding = encoding.reshape(1, -1)
        
        # Normalize to unit length
        norm = np.linalg.norm(encoding, axis=1, keepdims=True)
        return encoding / norm

    def _validate_encoding(self, encoding: np.ndarray) -> bool:
        """Validate face encoding"""
        if not isinstance(encoding, np.ndarray):
            return False
        
        if encoding.size != self._index_size:
            return False
        
        if not np.isfinite(encoding).all():
            return False
        
        return True

    def _distance_to_confidence(self, distance: float) -> float:
        """Convert distance metric to confidence score"""
        # For L2 distance, smaller is better
        if self.settings.use_l2_distance:
            return max(0, 1 - (distance / 2))
        # For Inner Product, larger is better
        else:
            return max(0, (1 + distance) / 2)

    def _get_face_id(self, index: int) -> Optional[str]:
        """Get face ID from index"""
        for face_id, data in self._face_data.items():
            if data['index'] == index:
                return face_id
        return None

    async def remove_face(self, face_id: str) -> bool:
        """Remove face from matcher"""
        try:
            async with self._index_lock:
                if face_id not in self._face_data:
                    return False
                
                # Remove from face data
                face_data = self._face_data.pop(face_id)
                
                # Rebuild index without this face
                await self._rebuild_index()
                
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to remove face: {str(e)}")
            return False

    async def _rebuild_index(self) -> None:
        """Rebuild FAISS index"""
        try:
            # Create new index
            new_index = self._create_index()
            
            # Add all faces except removed one
            encodings = []
            new_face_data = {}
            next_id = 0
            
            for face_id, data in self._face_data.items():
                encoding = self._load_encoding(face_id)
                if encoding is not None:
                    encodings.append(encoding)
                    data['index'] = next_id
                    new_face_data[face_id] = data
                    next_id += 1
            
            if encodings:
                encodings = np.vstack(encodings)
                new_index.add(encodings)
            
            # Update instance variables
            self._index = new_index
            self._face_data = new_face_data
            self._next_id = next_id
            
        except Exception as e:
            raise MatcherError(f"Index rebuild failed: {str(e)}")

    async def get_stats(self) -> Dict:
        """Get matcher statistics"""
        stats = self._stats.copy()
        
        # Add metrics
        stats.update({
            'matching_time': self._metrics.get_average('matching_time'),
            'index_size': len(self._face_data)
        })
        
        return stats

    async def _update_clusters(self, person_id: str, encoding: np.ndarray) -> None:
        """Update person clusters with new encoding"""
        try:
            # Add to person's cluster
            self.clusters[person_id].append(encoding)
            
            # Update cluster center
            if len(self.clusters[person_id]) > 1:
                center = np.mean(self.clusters[person_id], axis=0)
                self.cluster_centers[person_id] = center
                
                # Remove outliers
                if self.settings.remove_outliers:
                    await self._remove_cluster_outliers(person_id)
                    
        except Exception as e:
            self.logger.warning(f"Cluster update failed: {str(e)}")
            
    async def _remove_cluster_outliers(self, person_id: str) -> None:
        """Remove outlier encodings from person's cluster"""
        center = self.cluster_centers[person_id]
        encodings = self.clusters[person_id]
        
        # Calculate distances to center
        distances = [
            np.linalg.norm(enc - center)
            for enc in encodings
        ]
        
        # Remove outliers (beyond 2 standard deviations)
        mean_dist = np.mean(distances)
        std_dist = np.std(distances)
        threshold = mean_dist + 2 * std_dist
        
        self.clusters[person_id] = [
            enc for enc, dist in zip(encodings, distances)
            if dist <= threshold
        ]
        
    def _get_cache_key(self, encoding: np.ndarray) -> str:
        """Generate cache key for encoding"""
        return hash(encoding.tobytes())
        
    async def cleanup(self) -> None:
        """Cleanup resources"""
        self.thread_pool.shutdown()
        self.match_cache.clear()
        
    def get_statistics(self) -> Dict[str, Any]:
        """Get matcher statistics"""
        return {
            "total_encodings": self._index.ntotal,
            "total_persons": len(self.clusters),
            "cache_size": len(self.match_cache),
            "avg_cluster_size": np.mean([
                len(cluster) for cluster in self.clusters.values()
            ]),
            "memory_usage": self._index.get_memory_usage()
        } 