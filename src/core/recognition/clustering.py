from typing import Dict, List, Optional, Tuple, Set
import numpy as np
from sklearn.cluster import DBSCAN, KMeans
from sklearn.preprocessing import normalize
import faiss
import torch
from datetime import datetime
from dataclasses import dataclass
import asyncio
import logging
from pathlib import Path
import json

from ..base import BaseComponent
from ..utils.errors import ClusteringError

@dataclass
class ClusterInfo:
    """Cluster information"""
    cluster_id: int
    size: int
    center: np.ndarray
    members: List[str]  # face IDs
    confidence: float
    created: datetime
    updated: datetime
    metadata: Optional[Dict] = None

class FaceClusterer(BaseComponent):
    """Advanced face clustering system"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        
        # Clustering settings
        self._method = config.get('clustering.method', 'dbscan')
        self._batch_size = config.get('clustering.batch_size', 1000)
        self._min_cluster_size = config.get('clustering.min_size', 3)
        self._update_interval = config.get('clustering.update_interval', 100)
        
        # DBSCAN parameters
        self._eps = config.get('clustering.eps', 0.3)
        self._min_samples = config.get('clustering.min_samples', 5)
        
        # FAISS parameters
        self._use_gpu = config.get('clustering.use_gpu', True)
        self._nlist = config.get('clustering.nlist', 100)
        self._nprobe = config.get('clustering.nprobe', 10)
        
        # Cluster storage
        self._clusters: Dict[int, ClusterInfo] = {}
        self._face_to_cluster: Dict[str, int] = {}
        self._next_cluster_id = 0
        
        # Feature storage
        self._features: Dict[str, np.ndarray] = {}
        self._pending_features: List[Tuple[str, np.ndarray]] = []
        
        # Initialize clustering
        self._initialize_clustering()
        
        # Statistics
        self._stats = {
            'total_faces': 0,
            'total_clusters': 0,
            'average_cluster_size': 0.0,
            'largest_cluster': 0,
            'unclustered_faces': 0
        }

    def _initialize_clustering(self) -> None:
        """Initialize clustering system"""
        try:
            # Initialize FAISS index
            self._init_faiss_index()
            
            # Load existing clusters if any
            self._load_clusters()
            
            # Start update task
            self._update_task = asyncio.create_task(self._periodic_update())
            
        except Exception as e:
            raise ClusteringError(f"Clustering initialization failed: {str(e)}")

    def _init_faiss_index(self) -> None:
        """Initialize FAISS index"""
        try:
            dimension = 512  # Feature dimension
            
            # Create index
            self._index = faiss.IndexIVFFlat(
                faiss.IndexFlatL2(dimension),
                dimension,
                self._nlist
            )
            
            # Move to GPU if enabled
            if self._use_gpu and faiss.get_num_gpus() > 0:
                self._index = faiss.index_cpu_to_gpu(
                    faiss.StandardGpuResources(),
                    0,
                    self._index
                )
            
            # Set search parameters
            self._index.nprobe = self._nprobe
            
        except Exception as e:
            raise ClusteringError(f"FAISS initialization failed: {str(e)}")

    def _load_clusters(self) -> None:
        """Load existing clusters from disk"""
        try:
            cluster_file = Path('data/clusters/clusters.json')
            if not cluster_file.exists():
                return
            
            # Load cluster data
            with open(cluster_file, 'r') as f:
                data = json.load(f)
            
            # Reconstruct clusters
            for cluster_data in data['clusters']:
                cluster = ClusterInfo(
                    cluster_id=cluster_data['id'],
                    size=cluster_data['size'],
                    center=np.array(cluster_data['center']),
                    members=cluster_data['members'],
                    confidence=cluster_data['confidence'],
                    created=datetime.fromisoformat(cluster_data['created']),
                    updated=datetime.fromisoformat(cluster_data['updated']),
                    metadata=cluster_data.get('metadata')
                )
                self._clusters[cluster.cluster_id] = cluster
                
                # Update face mappings
                for face_id in cluster.members:
                    self._face_to_cluster[face_id] = cluster.cluster_id
            
            # Update next cluster ID
            self._next_cluster_id = max(self._clusters.keys()) + 1 if self._clusters else 0
            
        except Exception as e:
            self.logger.error(f"Cluster loading failed: {str(e)}")

    async def add_face(self,
                      face_id: str,
                      features: np.ndarray,
                      metadata: Optional[Dict] = None) -> None:
        """Add face features for clustering"""
        try:
            # Normalize features
            features = normalize(features.reshape(1, -1))[0]
            
            # Store features
            self._features[face_id] = features
            self._pending_features.append((face_id, features))
            
            # Update stats
            self._stats['total_faces'] += 1
            self._stats['unclustered_faces'] += 1
            
            # Trigger update if batch size reached
            if len(self._pending_features) >= self._batch_size:
                await self._update_clusters()
            
        except Exception as e:
            raise ClusteringError(f"Failed to add face: {str(e)}")

    async def _update_clusters(self) -> None:
        """Update clusters with new faces"""
        try:
            if not self._pending_features:
                return
            
            # Get pending features
            face_ids, features = zip(*self._pending_features)
            features = np.stack(features)
            
            # Perform clustering
            if self._method == 'dbscan':
                await self._dbscan_clustering(face_ids, features)
            else:
                await self._kmeans_clustering(face_ids, features)
            
            # Clear pending features
            self._pending_features.clear()
            
            # Update index
            if len(self._features) > 0:
                all_features = np.stack(list(self._features.values()))
                self._index.train(all_features)
                self._index.add(all_features)
            
            # Save clusters
            await self._save_clusters()
            
            # Update statistics
            self._update_stats()
            
        except Exception as e:
            self.logger.error(f"Cluster update failed: {str(e)}")

    async def _dbscan_clustering(self,
                               face_ids: List[str],
                               features: np.ndarray) -> None:
        """Perform DBSCAN clustering"""
        try:
            # Run DBSCAN
            clustering = DBSCAN(
                eps=self._eps,
                min_samples=self._min_samples,
                metric='cosine',
                n_jobs=-1
            )
            labels = clustering.fit_predict(features)
            
            # Process clusters
            unique_labels = set(labels)
            for label in unique_labels:
                if label == -1:  # Noise points
                    continue
                    
                # Get cluster members
                mask = labels == label
                cluster_features = features[mask]
                cluster_faces = [face_ids[i] for i, m in enumerate(mask) if m]
                
                if len(cluster_faces) < self._min_cluster_size:
                    continue
                
                # Calculate cluster center
                center = np.mean(cluster_features, axis=0)
                
                # Calculate confidence
                distances = np.linalg.norm(cluster_features - center, axis=1)
                confidence = 1.0 - np.mean(distances)
                
                # Create or update cluster
                await self._update_cluster(
                    cluster_faces,
                    center,
                    confidence
                )
            
        except Exception as e:
            raise ClusteringError(f"DBSCAN clustering failed: {str(e)}")

    async def _kmeans_clustering(self,
                               face_ids: List[str],
                               features: np.ndarray) -> None:
        """Perform K-means clustering"""
        try:
            # Estimate number of clusters
            n_clusters = max(1, len(face_ids) // self._min_cluster_size)
            
            # Run K-means
            clustering = KMeans(
                n_clusters=n_clusters,
                random_state=42,
                n_init=10
            )
            labels = clustering.fit_predict(features)
            
            # Process clusters
            for label in range(n_clusters):
                # Get cluster members
                mask = labels == label
                cluster_features = features[mask]
                cluster_faces = [face_ids[i] for i, m in enumerate(mask) if m]
                
                if len(cluster_faces) < self._min_cluster_size:
                    continue
                
                # Calculate confidence
                center = clustering.cluster_centers_[label]
                distances = np.linalg.norm(cluster_features - center, axis=1)
                confidence = 1.0 - np.mean(distances)
                
                # Create or update cluster
                await self._update_cluster(
                    cluster_faces,
                    center,
                    confidence
                )
            
        except Exception as e:
            raise ClusteringError(f"K-means clustering failed: {str(e)}")

    async def _update_cluster(self,
                            members: List[str],
                            center: np.ndarray,
                            confidence: float) -> None:
        """Create or update cluster"""
        try:
            # Check for existing cluster
            existing_clusters = set()
            for face_id in members:
                if face_id in self._face_to_cluster:
                    existing_clusters.add(self._face_to_cluster[face_id])
            
            if not existing_clusters:
                # Create new cluster
                cluster_id = self._next_cluster_id
                self._next_cluster_id += 1
                
                cluster = ClusterInfo(
                    cluster_id=cluster_id,
                    size=len(members),
                    center=center,
                    members=members,
                    confidence=confidence,
                    created=datetime.utcnow(),
                    updated=datetime.utcnow()
                )
                
                self._clusters[cluster_id] = cluster
                
                # Update mappings
                for face_id in members:
                    self._face_to_cluster[face_id] = cluster_id
                    
            else:
                # Merge with existing cluster
                main_cluster_id = min(existing_clusters)
                main_cluster = self._clusters[main_cluster_id]
                
                # Update members
                new_members = set(main_cluster.members)
                new_members.update(members)
                
                # Update cluster
                main_cluster.size = len(new_members)
                main_cluster.members = list(new_members)
                main_cluster.center = center
                main_cluster.confidence = confidence
                main_cluster.updated = datetime.utcnow()
                
                # Update mappings
                for face_id in new_members:
                    self._face_to_cluster[face_id] = main_cluster_id
                
                # Remove other clusters
                for cluster_id in existing_clusters:
                    if cluster_id != main_cluster_id:
                        self._clusters.pop(cluster_id, None)
            
        except Exception as e:
            self.logger.error(f"Cluster update failed: {str(e)}")

    async def _save_clusters(self) -> None:
        """Save clusters to disk"""
        try:
            # Create clusters directory
            cluster_dir = Path('data/clusters')
            cluster_dir.mkdir(parents=True, exist_ok=True)
            
            # Prepare cluster data
            data = {
                'clusters': [
                    {
                        'id': c.cluster_id,
                        'size': c.size,
                        'center': c.center.tolist(),
                        'members': c.members,
                        'confidence': c.confidence,
                        'created': c.created.isoformat(),
                        'updated': c.updated.isoformat(),
                        'metadata': c.metadata
                    }
                    for c in self._clusters.values()
                ]
            }
            
            # Save to file
            cluster_file = cluster_dir / 'clusters.json'
            with open(cluster_file, 'w') as f:
                json.dump(data, f, indent=2)
            
        except Exception as e:
            self.logger.error(f"Cluster save failed: {str(e)}")

    async def _periodic_update(self) -> None:
        """Periodic cluster update task"""
        while True:
            try:
                await asyncio.sleep(self._update_interval)
                await self._update_clusters()
                
            except Exception as e:
                self.logger.error(f"Periodic update failed: {str(e)}")

    def _update_stats(self) -> None:
        """Update clustering statistics"""
        try:
            self._stats['total_clusters'] = len(self._clusters)
            
            if self._clusters:
                sizes = [c.size for c in self._clusters.values()]
                self._stats['average_cluster_size'] = np.mean(sizes)
                self._stats['largest_cluster'] = max(sizes)
            
            self._stats['unclustered_faces'] = len(self._features) - sum(
                len(c.members) for c in self._clusters.values()
            )
            
        except Exception as e:
            self.logger.error(f"Stats update failed: {str(e)}")

    async def get_cluster(self, cluster_id: int) -> Optional[ClusterInfo]:
        """Get cluster information"""
        return self._clusters.get(cluster_id)

    async def get_face_cluster(self, face_id: str) -> Optional[ClusterInfo]:
        """Get cluster for face"""
        cluster_id = self._face_to_cluster.get(face_id)
        if cluster_id is not None:
            return self._clusters.get(cluster_id)
        return None

    async def search_similar(self,
                           features: np.ndarray,
                           k: int = 10) -> List[Tuple[str, float]]:
        """Search for similar faces"""
        try:
            # Normalize features
            features = normalize(features.reshape(1, -1))
            
            # Search index
            distances, indices = self._index.search(features, k)
            
            # Get results
            face_ids = list(self._features.keys())
            results = [
                (face_ids[idx], 1.0 - dist)
                for dist, idx in zip(distances[0], indices[0])
                if idx != -1
            ]
            
            return results
            
        except Exception as e:
            raise ClusteringError(f"Similarity search failed: {str(e)}")

    async def get_stats(self) -> Dict:
        """Get clustering statistics"""
        return self._stats.copy() 