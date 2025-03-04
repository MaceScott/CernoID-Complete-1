"""
Advanced face search system with GPU-accelerated similarity search and clustering.
"""

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
from ..utils.decorators import measure_performance

@dataclass
class SearchResult:
    """Face search result"""
    face_id: str
    similarity: float
    metadata: Optional[Dict] = None
    cluster_id: Optional[int] = None
    timestamp: datetime = None

class FaceSearch(BaseComponent):
    """Advanced face search system with GPU acceleration"""
    
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
            'index_updates': 0,
            'gpu_utilization': 0.0 if self._use_gpu else None
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
            
            self.logger.info(
                f"Search initialized with {self._stats['total_faces']} faces"
            )
            
        except Exception as e:
            raise SearchError(f"Search initialization failed: {str(e)}")

    def _create_index(self) -> None:
        """Create FAISS index with GPU support"""
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
                # HNSW index for approximate search
                self._index = faiss.IndexHNSWFlat(
                    self._dimension,
                    32  # M parameter
                )
            else:
                # Simple flat index
                self._index = faiss.IndexFlatL2(self._dimension)
            
            # Move to GPU if enabled
            if self._use_gpu and faiss.get_num_gpus() > 0:
                self.logger.info("Moving index to GPU")
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
                
                self._stats['total_faces'] = len(self._features)
                self.logger.info(f"Loaded {len(self._features)} face features")
            
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
                self.logger.info(f"Built index with {len(features)} features")
            
        except Exception as e:
            raise SearchError(f"Index building failed: {str(e)}")

    @measure_performance()
    async def add_face(self,
                      face_id: str,
                      features: np.ndarray,
                      metadata: Optional[Dict] = None,
                      cluster_id: Optional[int] = None) -> None:
        """
        Add face to search index
        
        Args:
            face_id: Unique identifier for the face
            features: Face embedding features
            metadata: Additional face information
            cluster_id: Optional cluster assignment
        """
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
            
            self.logger.debug(f"Added face {face_id} to index")
            
        except Exception as e:
            raise SearchError(f"Failed to add face: {str(e)}")

    @measure_performance()
    async def search(self,
                    features: np.ndarray,
                    k: int = 10,
                    min_similarity: Optional[float] = None) -> List[SearchResult]:
        """
        Search for similar faces
        
        Args:
            features: Query face features
            k: Number of results to return
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of search results sorted by similarity
        """
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
            
            # Update GPU stats if enabled
            if self._use_gpu:
                try:
                    import pynvml
                    pynvml.nvmlInit()
                    handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                    info = pynvml.nvmlDeviceGetUtilizationRates(handle)
                    self._stats['gpu_utilization'] = info.gpu
                except:
                    pass
            
            return sorted(results, key=lambda x: x.similarity, reverse=True)
            
        except Exception as e:
            raise SearchError(f"Search failed: {str(e)}")

    @measure_performance()
    async def batch_search(self,
                         features_list: List[np.ndarray],
                         k: int = 10) -> List[List[SearchResult]]:
        """
        Search for multiple faces in batch
        
        Args:
            features_list: List of query face features
            k: Number of results per query
            
        Returns:
            List of search results for each query
        """
        try:
            # Normalize features
            features_list = [
                features / np.linalg.norm(features)
                for features in features_list
            ]
            
            # Stack features
            features = np.stack(features_list)
            
            with self._index_lock:
                # Batch search
                distances, indices = self._index.search(features, k)
                
                # Process results
                all_results = []
                face_ids = list(self._features.keys())
                
                for query_distances, query_indices in zip(distances, indices):
                    query_results = []
                    
                    for dist, idx in zip(query_distances, query_indices):
                        if idx == -1:
                            continue
                        
                        # Calculate similarity
                        similarity = 1.0 - dist
                        if similarity < self._min_similarity:
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
                        query_results.append(result)
                    
                    all_results.append(
                        sorted(query_results, key=lambda x: x.similarity, reverse=True)
                    )
            
            return all_results
            
        except Exception as e:
            raise SearchError(f"Batch search failed: {str(e)}")

    @measure_performance()
    async def search_by_cluster(self,
                              cluster_id: int,
                              k: int = 10) -> List[SearchResult]:
        """
        Search for faces within a cluster
        
        Args:
            cluster_id: Cluster identifier
            k: Number of results to return
            
        Returns:
            List of faces in the cluster
        """
        try:
            with self._index_lock:
                # Get faces in cluster
                face_ids = self._reverse_index.get(cluster_id, [])
                if not face_ids:
                    return []
                
                # Create results
                results = []
                for face_id in face_ids[:k]:
                    metadata = self._metadata.get(face_id)
                    
                    result = SearchResult(
                        face_id=face_id,
                        similarity=1.0,  # Same cluster
                        metadata=metadata,
                        cluster_id=cluster_id,
                        timestamp=datetime.utcnow()
                    )
                    results.append(result)
                
                return results
                
        except Exception as e:
            raise SearchError(f"Cluster search failed: {str(e)}")

    async def _save_features(self) -> None:
        """Save features and metadata to disk"""
        try:
            # Create directory
            save_dir = Path('data/features')
            save_dir.mkdir(parents=True, exist_ok=True)
            
            # Save features
            feature_file = save_dir / 'features.npz'
            np.savez(
                feature_file,
                **self._features
            )
            
            # Save metadata
            metadata_file = save_dir / 'metadata.json'
            with open(metadata_file, 'w') as f:
                json.dump({
                    'metadata': self._metadata,
                    'clusters': self._clusters
                }, f, indent=2)
                
            self.logger.info(f"Saved {len(self._features)} features to disk")
            
        except Exception as e:
            self.logger.error(f"Feature saving failed: {str(e)}")

    async def get_stats(self) -> Dict:
        """Get search statistics"""
        stats = self._stats.copy()
        
        # Add index info
        if hasattr(self._index, 'ntotal'):
            stats['index_size'] = self._index.ntotal
        
        return stats 