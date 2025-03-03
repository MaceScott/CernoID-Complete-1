"""
Advanced face matching system with GPU acceleration and caching.

This module provides:
- Real-time face matching
- GPU-accelerated similarity search
- Match quality assessment
- Caching and performance optimization
- Cluster-based matching
"""

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
import torch
import logging
import json

from ..base import BaseComponent
from ..utils.errors import MatcherError

@dataclass
class MatchResult:
    """Face matching result with confidence and metadata"""
    person_id: str
    confidence: float
    encoding_id: str
    quality_score: float
    metadata: Dict[str, Any]
    match_time: float
    cluster_id: Optional[int] = None
    match_distance: Optional[float] = None

class FaceMatcher(BaseComponent):
    """Advanced face matching system with GPU support"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        
        # Matching settings
        self._min_confidence = config.get('matching.min_confidence', 0.6)
        self._max_distance = config.get('matching.max_distance', 0.6)
        self._use_quality_weighting = config.get('matching.use_quality_weighting', True)
        
        # Index settings
        self._index_type = config.get('matching.index_type', 'flat')  # flat, ivf, hnsw
        self._nprobe = config.get('matching.nprobe', 10)  # For IVF index
        self._ef_search = config.get('matching.ef_search', 40)  # For HNSW index
        
        # Storage settings
        self._storage_dir = Path(config.get('matching.storage_path', 'data/matching'))
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        self._index_file = self._storage_dir / 'face_index.bin'
        self._metadata_file = self._storage_dir / 'face_metadata.json'
        
        # Cache settings
        self._cache_size = config.get('matching.cache_size', 1000)
        self._cache_ttl = config.get('matching.cache_ttl', 3600)  # 1 hour
        
        # State
        self._index = None
        self._face_ids: List[str] = []
        self._encodings: List[np.ndarray] = []
        self._metadata: Dict[str, Dict] = {}
        self._match_cache: Dict[str, Tuple[List[MatchResult], float]] = {}
        self._index_lock = asyncio.Lock()
        
        # GPU support
        self.device = torch.device('cuda' if torch.cuda.is_available() and 
                                 config.get('gpu_enabled', True) else 'cpu')
        
        # Initialize
        self._initialize_matcher()
        
        # Start cache cleanup
        self._cleanup_interval = config.get('matching.cleanup_interval', 300)  # 5 minutes
        asyncio.create_task(self._periodic_cleanup())
        
        # Statistics
        self._stats = {
            'total_faces': 0,
            'total_matches': 0,
            'average_confidence': 0.0,
            'cache_hits': 0,
            'cache_misses': 0,
            'average_match_time': 0.0,
            'last_update': None
        }

    def _initialize_matcher(self) -> None:
        """Initialize matching system"""
        try:
            # Load metadata
            self._load_metadata()
            
            # Create index
            self._create_index()
            
            # Load existing index if available
            if self._index_file.exists():
                self._load_index()
            
            self.logger.info("Matching system initialized")
            
        except Exception as e:
            self.logger.error(f"Matcher initialization failed: {str(e)}")
            raise MatcherError(f"Failed to initialize matcher: {str(e)}")

    def _create_index(self) -> None:
        """Create FAISS index with GPU support if available"""
        try:
            # Get feature dimension from config or first encoding
            if self._encodings:
                dim = self._encodings[0].shape[0]
            else:
                dim = 512  # Default dimension
            
            if self._index_type == 'flat':
                if self.device.type == 'cuda':
                    # GPU index
                    res = faiss.StandardGpuResources()
                    config = faiss.GpuIndexFlatConfig()
                    config.device = 0
                    self._index = faiss.GpuIndexFlatIP(res, dim, config)
                else:
                    # CPU index
                    self._index = faiss.IndexFlatIP(dim)
                    
            elif self._index_type == 'ivf':
                # IVF index (better for large datasets)
                nlist = min(4096, max(16, len(self._face_ids) // 8))
                quantizer = faiss.IndexFlatIP(dim)
                self._index = faiss.IndexIVFFlat(quantizer, dim, nlist, faiss.METRIC_INNER_PRODUCT)
                if not self._index.is_trained and self._encodings:
                    self._index.train(np.vstack(self._encodings))
                self._index.nprobe = self._nprobe
                
            elif self._index_type == 'hnsw':
                # HNSW index (best for approximate search)
                self._index = faiss.IndexHNSWFlat(dim, 32, faiss.METRIC_INNER_PRODUCT)
                self._index.hnsw.efSearch = self._ef_search
                
            else:
                raise ValueError(f"Unknown index type: {self._index_type}")
            
            # Add existing encodings
            if self._encodings:
                self._index.add(np.vstack(self._encodings))
            
        except Exception as e:
            self.logger.error(f"Index creation failed: {str(e)}")
            raise MatcherError(f"Failed to create index: {str(e)}")

    def _load_metadata(self) -> None:
        """Load face metadata from disk"""
        try:
            if self._metadata_file.exists():
                with open(self._metadata_file, 'r') as f:
                    data = json.load(f)
                    
                self._metadata = data.get('metadata', {})
                self._face_ids = data.get('face_ids', [])
                
                # Load encodings
                if (self._storage_dir / 'encodings.npz').exists():
                    data = np.load(self._storage_dir / 'encodings.npz')
                    self._encodings = [enc for enc in data['encodings']]
                    
                self.logger.info(f"Loaded metadata for {len(self._face_ids)} faces")
                
        except Exception as e:
            self.logger.error(f"Failed to load metadata: {str(e)}")
            self._metadata = {}
            self._face_ids = []
            self._encodings = []

    def _load_index(self) -> None:
        """Load FAISS index from disk"""
        try:
            self._index = faiss.read_index(str(self._index_file))
            if self.device.type == 'cuda':
                # Convert to GPU index
                res = faiss.StandardGpuResources()
                self._index = faiss.index_cpu_to_gpu(res, 0, self._index)
                
            self.logger.info("Loaded face index from disk")
            
        except Exception as e:
            self.logger.error(f"Failed to load index: {str(e)}")
            self._create_index()

    async def add_face(self,
                      face_id: str,
                      encoding: np.ndarray,
                      metadata: Dict[str, Any]) -> bool:
        """
        Add face encoding to matching system
        
        Args:
            face_id: Unique face identifier
            encoding: Face encoding vector
            metadata: Additional face metadata
            
        Returns:
            True if face was added successfully
        """
        try:
            async with self._index_lock:
                # Normalize encoding
                encoding = self._normalize_encoding(encoding)
                
                # Validate encoding
                if not self._validate_encoding(encoding):
                    raise MatcherError("Invalid face encoding")
                
                # Add to index
                self._index.add(encoding.reshape(1, -1))
                self._face_ids.append(face_id)
                self._encodings.append(encoding)
                self._metadata[face_id] = {
                    **metadata,
                    'added_at': datetime.utcnow().isoformat()
                }
                
                # Update stats
                self._stats['total_faces'] += 1
                
                # Save periodically
                if len(self._face_ids) % 100 == 0:
                    await self._save_state()
                
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to add face: {str(e)}")
            return False

    async def find_matches(self,
                          encoding: np.ndarray,
                          max_matches: int = 5) -> List[MatchResult]:
        """
        Find matching faces for encoding
        
        Args:
            encoding: Query face encoding
            max_matches: Maximum number of matches to return
            
        Returns:
            List of MatchResult objects sorted by confidence
        """
        try:
            # Check cache
            cache_key = self._get_cache_key(encoding)
            if cache_key in self._match_cache:
                matches, timestamp = self._match_cache[cache_key]
                if time.time() - timestamp < self._cache_ttl:
                    self._stats['cache_hits'] += 1
                    return matches
                
            self._stats['cache_misses'] += 1
            start_time = time.time()
            
            # Normalize encoding
            encoding = self._normalize_encoding(encoding)
            
            # Search index
            k = min(max_matches * 2, len(self._face_ids))  # Get extra matches for filtering
            if k == 0:
                return []
                
            D, I = self._index.search(encoding.reshape(1, -1), k)
            
            # Process results
            matches = []
            seen_persons = set()
            
            for idx, (distance, face_idx) in enumerate(zip(D[0], I[0])):
                if face_idx >= len(self._face_ids):
                    continue
                    
                face_id = self._face_ids[face_idx]
                metadata = self._metadata[face_id]
                person_id = metadata.get('person_id')
                
                # Skip if we already have a better match for this person
                if person_id in seen_persons:
                    continue
                    
                # Convert distance to confidence
                confidence = self._distance_to_confidence(distance)
                if confidence < self._min_confidence:
                    continue
                
                # Apply quality weighting if enabled
                if self._use_quality_weighting:
                    quality_score = metadata.get('quality_score', 0.5)
                    confidence *= quality_score
                
                match = MatchResult(
                    person_id=person_id,
                    confidence=confidence,
                    encoding_id=face_id,
                    quality_score=metadata.get('quality_score', 0.0),
                    metadata=metadata,
                    match_time=time.time() - start_time,
                    match_distance=float(distance)
                )
                
                matches.append(match)
                seen_persons.add(person_id)
                
                if len(matches) >= max_matches:
                    break
            
            # Sort by confidence
            matches.sort(key=lambda m: m.confidence, reverse=True)
            
            # Update cache
            self._match_cache[cache_key] = (matches, time.time())
            
            # Update stats
            self._update_stats(matches)
            
            return matches
            
        except Exception as e:
            self.logger.error(f"Face matching failed: {str(e)}")
            raise MatcherError(f"Face matching failed: {str(e)}")

    def _normalize_encoding(self, encoding: np.ndarray) -> np.ndarray:
        """Normalize face encoding vector"""
        try:
            # Ensure correct shape
            if len(encoding.shape) == 1:
                encoding = encoding.reshape(1, -1)
            
            # L2 normalization
            norm = np.linalg.norm(encoding, axis=1, keepdims=True)
            return encoding / norm
            
        except Exception as e:
            self.logger.error(f"Encoding normalization failed: {str(e)}")
            raise MatcherError(f"Failed to normalize encoding: {str(e)}")

    def _validate_encoding(self, encoding: np.ndarray) -> bool:
        """Validate face encoding"""
        try:
            if encoding is None or not isinstance(encoding, np.ndarray):
                return False
                
            if len(encoding.shape) != 2:
                return False
                
            if np.isnan(encoding).any() or np.isinf(encoding).any():
                return False
                
            return True
            
        except Exception:
            return False

    def _distance_to_confidence(self, distance: float) -> float:
        """Convert distance metric to confidence score"""
        try:
            # For cosine similarity (inner product of normalized vectors)
            confidence = (distance + 1) / 2  # Convert from [-1,1] to [0,1]
            return float(np.clip(confidence, 0.0, 1.0))
            
        except Exception as e:
            self.logger.error(f"Confidence calculation failed: {str(e)}")
            return 0.0

    async def remove_face(self, face_id: str) -> bool:
        """Remove face from matching system"""
        try:
            async with self._index_lock:
                if face_id not in self._face_ids:
                    return False
                    
                # Get index of face
                idx = self._face_ids.index(face_id)
                
                # Remove from lists
                self._face_ids.pop(idx)
                self._encodings.pop(idx)
                self._metadata.pop(face_id, None)
                
                # Rebuild index
                await self._rebuild_index()
                
                # Clear cache
                self._match_cache.clear()
                
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to remove face: {str(e)}")
            return False

    async def _rebuild_index(self) -> None:
        """Rebuild FAISS index"""
        try:
            if not self._encodings:
                self._create_index()
                return
                
            # Create new index
            old_index = self._index
            self._create_index()
            
            # Add all encodings
            self._index.add(np.vstack(self._encodings))
            
            # Save state
            await self._save_state()
            
            # Clean up old index
            del old_index
            
        except Exception as e:
            self.logger.error(f"Index rebuild failed: {str(e)}")
            raise MatcherError(f"Failed to rebuild index: {str(e)}")

    async def _save_state(self) -> None:
        """Save matcher state to disk"""
        try:
            # Save metadata
            data = {
                'metadata': self._metadata,
                'face_ids': self._face_ids
            }
            
            with open(self._metadata_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Save encodings
            np.savez(
                self._storage_dir / 'encodings.npz',
                encodings=np.vstack(self._encodings)
            )
            
            # Save index
            if self.device.type == 'cuda':
                # Convert to CPU for saving
                cpu_index = faiss.index_gpu_to_cpu(self._index)
                faiss.write_index(cpu_index, str(self._index_file))
            else:
                faiss.write_index(self._index, str(self._index_file))
                
        except Exception as e:
            self.logger.error(f"Failed to save state: {str(e)}")
            raise MatcherError(f"Failed to save state: {str(e)}")

    def _get_cache_key(self, encoding: np.ndarray) -> str:
        """Generate cache key for encoding"""
        return str(hash(encoding.tobytes()))

    async def _periodic_cleanup(self) -> None:
        """Periodically clean up cache"""
        while True:
            try:
                await asyncio.sleep(self._cleanup_interval)
                
                # Remove expired cache entries
                current_time = time.time()
                expired = [k for k, (_, t) in self._match_cache.items()
                          if current_time - t > self._cache_ttl]
                
                for key in expired:
                    self._match_cache.pop(key, None)
                    
                # Limit cache size
                if len(self._match_cache) > self._cache_size:
                    # Remove oldest entries
                    sorted_cache = sorted(self._match_cache.items(),
                                       key=lambda x: x[1][1])
                    for key, _ in sorted_cache[:len(self._match_cache) - self._cache_size]:
                        self._match_cache.pop(key, None)
                        
            except Exception as e:
                self.logger.error(f"Cache cleanup failed: {str(e)}")

    def _update_stats(self, matches: List[MatchResult]) -> None:
        """Update matching statistics"""
        try:
            if not matches:
                return
                
            self._stats['total_matches'] += len(matches)
            self._stats['average_confidence'] = (
                (self._stats['average_confidence'] * (self._stats['total_matches'] - len(matches)) +
                 sum(m.confidence for m in matches)) / self._stats['total_matches']
            )
            self._stats['average_match_time'] = (
                (self._stats['average_match_time'] * (self._stats['total_matches'] - len(matches)) +
                 sum(m.match_time for m in matches)) / self._stats['total_matches']
            )
            self._stats['last_update'] = datetime.utcnow().isoformat()
            
        except Exception as e:
            self.logger.error(f"Failed to update stats: {str(e)}")

    async def get_stats(self) -> Dict:
        """Get matching statistics"""
        return self._stats.copy()

# Global matcher instance
face_matcher = FaceMatcher({}) 