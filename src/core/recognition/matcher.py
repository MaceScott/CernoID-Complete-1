from typing import Dict, List, Optional, Tuple, Union
import numpy as np
from datetime import datetime
import asyncio
from dataclasses import dataclass
from pathlib import Path
import faiss

from ..base import BaseComponent
from ..utils.errors import MatcherError
from ..utils.metrics import PerformanceMetrics

@dataclass
class MatchResult:
    """Represents a face matching result"""
    face_id: str
    confidence: float
    metadata: Dict
    timestamp: datetime = datetime.utcnow()

class FaceMatcher(BaseComponent):
    """Enhanced face matching engine"""
    
    def __init__(self, config: dict):
        self._validate_config(config)
        super().__init__(config)
        
        # Matching settings
        self._matching_threshold = config.get('matcher.threshold', 0.6)
        self._index_size = config.get('matcher.index_size', 128)  # Face encoding size
        self._batch_size = config.get('matcher.batch_size', 32)
        
        # Initialize FAISS index for fast similarity search
        self._index = self._initialize_index()
        
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

    def _initialize_index(self) -> faiss.Index:
        """Initialize FAISS index for face matching"""
        try:
            # Choose index type based on config
            index_type = self.config.get('matcher.index_type', 'L2')
            
            if index_type == 'L2':
                index = faiss.IndexFlatL2(self._index_size)
            elif index_type == 'IP':  # Inner Product
                index = faiss.IndexFlatIP(self._index_size)
            elif index_type == 'IVF':  # IVF with faster search
                quantizer = faiss.IndexFlatL2(self._index_size)
                index = faiss.IndexIVFFlat(
                    quantizer, 
                    self._index_size,
                    self.config.get('matcher.ivf_lists', 100)
                )
                index.train(np.zeros((1, self._index_size), dtype=np.float32))
            else:
                raise MatcherError(f"Unsupported index type: {index_type}")
            
            return index
            
        except Exception as e:
            raise MatcherError(f"Index initialization failed: {str(e)}")

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
                                    face_id=face_id,
                                    confidence=confidence,
                                    metadata=self._face_data[face_id]['metadata']
                                )
                                matches.append(match)
                
                self._stats['total_matches'] += len(matches)
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
        if self.config.get('matcher.metric') == 'L2':
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
            new_index = self._initialize_index()
            
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