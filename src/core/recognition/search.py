from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import faiss
import torch
from datetime import datetime
from dataclasses import dataclass
import asyncio
import json
from pathlib import Path
import threading
from collections import defaultdict
import heapq

from ..base import BaseComponent
from ..utils.errors import SearchError

@dataclass
class SearchResult:
    """Face search result"""
    face_id: str
    similarity: float
    metadata: Optional[Dict] = None
    cluster_id: Optional[int] = None
    timestamp: datetime = None

class FaceSearch(BaseComponent):
    """Advanced face search system"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        
        # Search settings
        self._index_type = config.get('search.index_type', 'ivf')
        self._use_gpu = config.get('search.use_gpu', True)
        self._batch_size = config.get('search.batch_size', 100)
        self._min_similarity = config.get('search.min_similarity', 0.6)
        
        # Index parameters
        self._dimension = config.get('search.dimension', 512)
        self._nlist = config.get('search.nlist', 100)
        self._nprobe = config.get('search.nprobe', 10)
        
        # Feature storage
        self._features: Dict[str, np.ndarray] = {}
        self._metadata: Dict[str, Dict] = {}
        self._clusters: Dict[str, int] = {}
        self._reverse_index: Dict[int, List[str]] = defaultdict(list)
        
        # Index lock
        self._index_lock = threading.Lock()
        
        # Initialize search
        self._initialize_search()
        
        # Statistics
        self._stats = {
            'total_faces': 0,
            'total_searches': 0,
            'average_search_time': 0.0,
            'cache_hits': 0,
            'index_updates': 0
        }

    def _initialize_search(self) -> None:
        """Initialize search system"""
        try:
            # Create FAISS index
            self._create_index()
            
            # Load existing features
            self._load_features()
            
            # Build initial index
            self._build_index()
            
        except Exception as e:
            raise SearchError(f"Search initialization failed: {str(e)}")

    def _create_index(self) -> None:
        """Create FAISS index"""
        try:
            if self._index_type == 'ivf':
                # IVF index with L2 distance
                quantizer = faiss.IndexFlatL2(self._dimension)
                self._index = faiss.IndexIVFFlat(
                    quantizer,
                    self._dimension,
                    self._nlist,
                    faiss.METRIC_L2
                )
            elif self._index_type == 'hnsw':
                # HNSW index
                self._index = faiss.IndexHNSWFlat(
                    self._dimension,
                    32  # M parameter
                )
            else:
                # Simple flat index
                self._index = faiss.IndexFlatL2(self._dimension)
            
            # Move to GPU if enabled
            if self._use_gpu and faiss.get_num_gpus() > 0:
                self._index = faiss.index_cpu_to_gpu(
                    faiss.StandardGpuResources(),
                    0,
                    self._index
                )
            
            # Set search parameters
            if hasattr(self._index, 'nprobe'):
                self._index.nprobe = self._nprobe
            
        except Exception as e:
            raise SearchError(f"Index creation failed: {str(e)}")

    def _load_features(self) -> None:
        """Load existing features from disk"""
        try:
            feature_file = Path('data/features/features.npz')
            metadata_file = Path('data/features/metadata.json')
            
            if feature_file.exists() and metadata_file.exists():
                # Load features
                data = np.load(feature_file)
                for face_id, features in data.items():
                    self._features[face_id] = features
                
                # Load metadata
                with open(metadata_file, 'r') as f:
                    data = json.load(f)
                    self._metadata = data.get('metadata', {})
                    self._clusters = data.get('clusters', {})
                
                # Update reverse index
                for face_id, cluster_id in self._clusters.items():
                    self._reverse_index[cluster_id].append(face_id)
            
        except Exception as e:
            self.logger.error(f"Feature loading failed: {str(e)}")

    def _build_index(self) -> None:
        """Build search index"""
        try:
            with self._index_lock:
                if not self._features:
                    return
                
                # Stack features
                features = np.stack(list(self._features.values()))
                
                # Train index if needed
                if hasattr(self._index, 'train'):
                    self._index.train(features)
                
                # Add features
                self._index.add(features)
                
                self._stats['index_updates'] += 1
            
        except Exception as e:
            raise SearchError(f"Index building failed: {str(e)}")

    async def add_face(self,
                      face_id: str,
                      features: np.ndarray,
                      metadata: Optional[Dict] = None,
                      cluster_id: Optional[int] = None) -> None:
        """Add face to search index"""
        try:
            # Normalize features
            features = features / np.linalg.norm(features)
            
            with self._index_lock:
                # Store face data
                self._features[face_id] = features
                if metadata:
                    self._metadata[face_id] = metadata
                if cluster_id is not None:
                    self._clusters[face_id] = cluster_id
                    self._reverse_index[cluster_id].append(face_id)
                
                # Update index
                self._index.add(features.reshape(1, -1))
                
                self._stats['total_faces'] += 1
            
            # Save periodically
            if self._stats['total_faces'] % 100 == 0:
                await self._save_features()
            
        except Exception as e:
            raise SearchError(f"Failed to add face: {str(e)}")

    async def search(self,
                    features: np.ndarray,
                    k: int = 10,
                    min_similarity: Optional[float] = None) -> List[SearchResult]:
        """Search for similar faces"""
        try:
            start_time = datetime.utcnow()
            
            # Normalize features
            features = features / np.linalg.norm(features)
            
            # Set similarity threshold
            min_similarity = min_similarity or self._min_similarity
            
            with self._index_lock:
                # Search index
                distances, indices = self._index.search(
                    features.reshape(1, -1),
                    k
                )
                
                # Process results
                results = []
                face_ids = list(self._features.keys())
                
                for dist, idx in zip(distances[0], indices[0]):
                    if idx == -1:
                        continue
                    
                    # Calculate similarity
                    similarity = 1.0 - dist
                    if similarity < min_similarity:
                        continue
                    
                    # Get face data
                    face_id = face_ids[idx]
                    metadata = self._metadata.get(face_id)
                    cluster_id = self._clusters.get(face_id)
                    
                    # Create result
                    result = SearchResult(
                        face_id=face_id,
                        similarity=float(similarity),
                        metadata=metadata,
                        cluster_id=cluster_id,
                        timestamp=datetime.utcnow()
                    )
                    results.append(result)
            
            # Update stats
            self._stats['total_searches'] += 1
            search_time = (datetime.utcnow() - start_time).total_seconds()
            n = self._stats['total_searches']
            self._stats['average_search_time'] = (
                (self._stats['average_search_time'] * (n - 1) + search_time) / n
            )
            
            return results
            
        except Exception as e:
            raise SearchError(f"Search failed: {str(e)}")

    async def batch_search(self,
                         features_list: List[np.ndarray],
                         k: int = 10) -> List[List[SearchResult]]:
        """Search for multiple faces"""
        try:
            results = []
            
            # Process in batches
            for i in range(0, len(features_list), self._batch_size):
                batch = features_list[i:i + self._batch_size]
                
                # Stack and normalize features
                batch_features = np.stack([
                    f / np.linalg.norm(f) for f in batch
                ])
                
                with self._index_lock:
                    # Search index
                    distances, indices = self._index.search(batch_features, k)
                    
                    # Process results
                    batch_results = []
                    face_ids = list(self._features.keys())
                    
                    for dists, idxs in zip(distances, indices):
                        face_results = []
                        
                        for dist, idx in zip(dists, idxs):
                            if idx == -1:
                                continue
                            
                            similarity = 1.0 - dist
                            if similarity < self._min_similarity:
                                continue
                            
                            face_id = face_ids[idx]
                            result = SearchResult(
                                face_id=face_id,
                                similarity=float(similarity),
                                metadata=self._metadata.get(face_id),
                                cluster_id=self._clusters.get(face_id),
                                timestamp=datetime.utcnow()
                            )
                            face_results.append(result)
                        
                        batch_results.append(face_results)
                    
                    results.extend(batch_results)
            
            return results
            
        except Exception as e:
            raise SearchError(f"Batch search failed: {str(e)}")

    async def search_by_cluster(self,
                              cluster_id: int,
                              k: int = 10) -> List[SearchResult]:
        """Search faces in cluster"""
        try:
            results = []
            
            # Get cluster faces
            face_ids = self._reverse_index.get(cluster_id, [])
            if not face_ids:
                return results
            
            # Get face features
            features = []
            for face_id in face_ids:
                if face_id in self._features:
                    features.append(self._features[face_id])
            
            if not features:
                return results
            
            # Calculate average features
            center = np.mean(features, axis=0)
            center = center / np.linalg.norm(center)
            
            # Search similar faces
            results = await self.search(center, k)
            
            return results
            
        except Exception as e:
            raise SearchError(f"Cluster search failed: {str(e)}")

    async def _save_features(self) -> None:
        """Save features to disk"""
        try:
            # Create feature directory
            feature_dir = Path('data/features')
            feature_dir.mkdir(parents=True, exist_ok=True)
            
            # Save features
            feature_file = feature_dir / 'features.npz'
            np.savez(feature_file, **self._features)
            
            # Save metadata
            metadata_file = feature_dir / 'metadata.json'
            data = {
                'metadata': self._metadata,
                'clusters': self._clusters
            }
            with open(metadata_file, 'w') as f:
                json.dump(data, f, indent=2)
            
        except Exception as e:
            self.logger.error(f"Feature save failed: {str(e)}")

    async def get_stats(self) -> Dict:
        """Get search statistics"""
        return self._stats.copy() 