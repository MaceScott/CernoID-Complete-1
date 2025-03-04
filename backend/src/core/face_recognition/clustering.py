"""
Advanced face clustering system with GPU acceleration and multiple algorithms.

This module provides:
- Real-time face clustering
- Multiple clustering algorithms (DBSCAN, K-Means)
- GPU-accelerated similarity search
- Cluster quality analysis
- Automatic cluster maintenance
"""

from typing import Dict, List, Optional, Tuple, Set, Union
import numpy as np
from sklearn.cluster import DBSCAN, KMeans, AgglomerativeClustering
from sklearn.preprocessing import normalize
import faiss
import torch
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import asyncio
import logging
from pathlib import Path
import json
from concurrent.futures import ThreadPoolExecutor

from ..base import BaseComponent
from ..utils.errors import ClusteringError
from .models import ModelManager
from .metrics import QualityMetricsTracker

@dataclass
class ClusterMetrics:
    """Cluster quality metrics"""
    silhouette_score: float = 0.0
    intra_cluster_distance: float = 0.0
    inter_cluster_distance: float = 0.0
    density: float = 0.0
    purity: float = 0.0
    updated: datetime = field(default_factory=datetime.now)

@dataclass
class ClusterInfo:
    """Enhanced cluster information"""
    cluster_id: int
    size: int
    center: np.ndarray
    members: List[str]  # face IDs
    confidence: float
    created: datetime
    updated: datetime
    metrics: ClusterMetrics = field(default_factory=ClusterMetrics)
    metadata: Optional[Dict] = None

class FaceClusterer(BaseComponent):
    """Advanced face clustering system with GPU acceleration"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        
        # Core settings
        self._method = config.get('clustering.method', 'dbscan')
        self._batch_size = config.get('clustering.batch_size', 1000)
        self._min_cluster_size = config.get('clustering.min_size', 3)
        self._update_interval = config.get('clustering.update_interval', 100)
        self._cache_ttl = config.get('clustering.cache_ttl', 3600)  # 1 hour
        
        # Algorithm parameters
        self._eps = config.get('clustering.eps', 0.3)
        self._min_samples = config.get('clustering.min_samples', 5)
        self._n_clusters = config.get('clustering.n_clusters', 'auto')
        
        # GPU settings
        self._use_gpu = config.get('clustering.use_gpu', True) and torch.cuda.is_available()
        self._gpu_batch_size = config.get('clustering.gpu_batch_size', 10000)
        
        # FAISS parameters
        self._nlist = config.get('clustering.nlist', 100)
        self._nprobe = config.get('clustering.nprobe', 10)
        self._use_faiss = config.get('clustering.use_faiss', True)
        
        # Quality thresholds
        self._min_quality = config.get('clustering.min_quality', 0.5)
        self._confidence_threshold = config.get('clustering.confidence', 0.7)
        
        # Storage
        self._clusters: Dict[int, ClusterInfo] = {}
        self._face_to_cluster: Dict[str, int] = {}
        self._next_cluster_id = 0
        self._features: Dict[str, np.ndarray] = {}
        self._pending_features: List[Tuple[str, np.ndarray]] = []
        
        # Caching
        self._cache: Dict[str, Tuple[np.ndarray, datetime]] = {}
        self._cache_lock = asyncio.Lock()
        
        # Thread pool for CPU operations
        self._thread_pool = ThreadPoolExecutor(max_workers=4)
        
        # Metrics
        self._metrics = QualityMetricsTracker()
        
        # Initialize
        self._initialize_clustering()
        
    def _initialize_clustering(self) -> None:
        """Initialize clustering system with GPU support"""
        try:
            # Initialize FAISS
            if self._use_faiss:
                self._init_faiss_index()
            
            # Load existing clusters
            self._load_clusters()
            
            # Start maintenance tasks
            self._start_maintenance_tasks()
            
        except Exception as e:
            self.logger.error(f"Clustering initialization failed: {str(e)}")
            raise

    def _init_faiss_index(self) -> None:
        """Initialize FAISS index with GPU support"""
        try:
            dimension = 512  # Feature dimension
            
            # Create quantizer
            quantizer = faiss.IndexFlatL2(dimension)
            
            # Create index
            self._index = faiss.IndexIVFFlat(
                quantizer,
                dimension,
                self._nlist,
                faiss.METRIC_L2
            )
            
            # Move to GPU if enabled
            if self._use_gpu:
                res = faiss.StandardGpuResources()
                self._index = faiss.index_cpu_to_gpu(res, 0, self._index)
                
            self._index.nprobe = self._nprobe
            
        except Exception as e:
            self.logger.error(f"FAISS initialization failed: {str(e)}")
            raise

    def _start_maintenance_tasks(self) -> None:
        """Start background maintenance tasks"""
        asyncio.create_task(self._periodic_update())
        asyncio.create_task(self._cache_cleanup())
        asyncio.create_task(self._cluster_maintenance())

    async def add_face(self,
                      face_id: str,
                      features: np.ndarray,
                      quality_score: float,
                      metadata: Optional[Dict] = None) -> None:
        """Add face features for clustering with quality check"""
        try:
            # Quality check
            if quality_score < self._min_quality:
                self.logger.warning(f"Face {face_id} rejected due to low quality: {quality_score}")
                return
            
            # Normalize features
            features = await self._normalize_features(features)
            
            # Update storage
            async with self._cache_lock:
                self._features[face_id] = features
                self._pending_features.append((face_id, features))
                self._cache[face_id] = (features, datetime.now())
            
            # Update metrics
            self._metrics.track_addition(quality_score)
            
            # Trigger update if batch size reached
            if len(self._pending_features) >= self._batch_size:
                await self._update_clusters()
            
        except Exception as e:
            self.logger.error(f"Failed to add face: {str(e)}")
            raise

    async def _normalize_features(self, features: np.ndarray) -> np.ndarray:
        """Normalize features using GPU if available"""
        if self._use_gpu:
            features_tensor = torch.from_numpy(features).cuda()
            features_tensor = torch.nn.functional.normalize(features_tensor, dim=0)
            return features_tensor.cpu().numpy()
        return normalize(features.reshape(1, -1))[0]

    async def _update_clusters(self) -> None:
        """Update clusters with new faces using selected algorithm"""
        try:
            if not self._pending_features:
                return
            
            # Get pending features
            face_ids, features = zip(*self._pending_features)
            features = np.stack(features)
            
            # Select clustering method
            if self._method == 'dbscan':
                await self._dbscan_clustering(face_ids, features)
            elif self._method == 'kmeans':
                await self._kmeans_clustering(face_ids, features)
            elif self._method == 'hierarchical':
                await self._hierarchical_clustering(face_ids, features)
            
            # Update FAISS index
            if self._use_faiss:
                await self._update_faiss_index()
            
            # Clear pending
            self._pending_features.clear()
            
            # Save and update metrics
            await self._save_clusters()
            self._metrics.update_clustering_stats(len(self._clusters))
            
        except Exception as e:
            self.logger.error(f"Cluster update failed: {str(e)}")
            raise

    async def _cluster_maintenance(self) -> None:
        """Periodic cluster maintenance"""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                
                # Merge similar clusters
                await self._merge_similar_clusters()
                
                # Split low quality clusters
                await self._split_low_quality_clusters()
                
                # Remove stale clusters
                await self._remove_stale_clusters()
                
                # Update metrics
                await self._update_cluster_metrics()
                
            except Exception as e:
                self.logger.error(f"Cluster maintenance failed: {str(e)}")

    async def get_cluster(self, face_id: str) -> Optional[ClusterInfo]:
        """Get cluster information for a face"""
        cluster_id = self._face_to_cluster.get(face_id)
        return self._clusters.get(cluster_id) if cluster_id is not None else None

    async def search_similar_faces(self,
                                 features: np.ndarray,
                                 k: int = 10,
                                 threshold: float = 0.7) -> List[Tuple[str, float]]:
        """Search for similar faces using FAISS"""
        try:
            if not self._use_faiss or len(self._features) == 0:
                return []
            
            # Normalize query
            query = await self._normalize_features(features)
            
            # Search
            D, I = self._index.search(query.reshape(1, -1), k)
            
            # Get results
            results = []
            for dist, idx in zip(D[0], I[0]):
                if dist > threshold:
                    continue
                face_id = list(self._features.keys())[idx]
                similarity = 1.0 - dist
                results.append((face_id, similarity))
            
            return results
            
        except Exception as e:
            self.logger.error(f"Similar face search failed: {str(e)}")
            return []

    def get_statistics(self) -> Dict:
        """Get clustering statistics"""
        return {
            'total_faces': len(self._features),
            'total_clusters': len(self._clusters),
            'average_cluster_size': np.mean([c.size for c in self._clusters.values()]) if self._clusters else 0,
            'largest_cluster': max([c.size for c in self._clusters.values()]) if self._clusters else 0,
            'gpu_enabled': self._use_gpu,
            'cache_size': len(self._cache),
            'pending_faces': len(self._pending_features),
            **self._metrics.get_stats()
        }

# Global clusterer instance
face_clusterer = FaceClusterer({}) 