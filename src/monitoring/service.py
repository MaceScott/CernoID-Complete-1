"""
Unified monitoring system with metrics, visualization, and optimization.
"""
from typing import Dict, List, Any, Optional
import asyncio
from datetime import datetime
import torch
import torch.cuda
import psutil
import gc
import aiohttp
import json
from pathlib import Path
import numpy as np
import prometheus_client as prom

from ..utils.config import get_settings
from ..utils.logging import get_logger
from ..database.service import DatabaseService

class MonitoringService:
    """
    Unified monitoring system combining metrics, visualization, and optimization
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        self.db = DatabaseService()
        
        # Initialize Grafana client
        self.grafana_url = self.settings.grafana_url
        self.grafana_key = self.settings.grafana_api_key
        self.session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self.grafana_key}",
                "Content-Type": "application/json"
            }
        )
        
        # Initialize Prometheus metrics
        self.metrics = {
            "recognition_requests": prom.Counter(
                "recognition_requests_total",
                "Total number of recognition requests"
            ),
            "recognition_latency": prom.Histogram(
                "recognition_latency_seconds",
                "Recognition request latency"
            ),
            "gpu_memory_used": prom.Gauge(
                "gpu_memory_bytes",
                "GPU memory usage in bytes"
            ),
            "cpu_usage": prom.Gauge(
                "cpu_usage_percent",
                "CPU usage percentage"
            ),
            "memory_usage": prom.Gauge(
                "memory_usage_percent",
                "Memory usage percentage"
            )
        }
        
        # Initialize performance metrics history
        self.performance_history = {
            "gpu_memory": [],
            "cpu_usage": [],
            "memory_usage": [],
            "processing_times": []
        }
        
        # Load dashboard templates
        self.dashboard_templates = self._load_dashboard_templates()
        
        # Start monitoring task
        self.monitoring_task = asyncio.create_task(
            self._monitor_resources()
        )
        
    def _load_dashboard_templates(self) -> Dict[str, Dict]:
        """Load dashboard templates."""
        template_dir = Path("src/monitoring/dashboards")
        templates = {}
        
        for template_file in template_dir.glob("*.json"):
            with open(template_file) as f:
                templates[template_file.stem] = json.load(f)
                
        return templates
        
    async def collect_metrics(self) -> Dict[str, Any]:
        """Collect current system metrics."""
        try:
            metrics = {
                "cpu_usage": psutil.cpu_percent(),
                "memory_usage": psutil.virtual_memory().percent,
                "gpu_memory": (
                    torch.cuda.memory_allocated()
                    if torch.cuda.is_available()
                    else 0
                ),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Update Prometheus metrics
            self.metrics["cpu_usage"].set(metrics["cpu_usage"])
            self.metrics["memory_usage"].set(metrics["memory_usage"])
            self.metrics["gpu_memory_used"].set(metrics["gpu_memory"])
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Metrics collection failed: {str(e)}")
            raise
            
    async def create_dashboard(self,
                             name: str,
                             template: str) -> Dict[str, Any]:
        """Create new Grafana dashboard."""
        try:
            if template not in self.dashboard_templates:
                raise ValueError(f"Template {template} not found")
                
            dashboard_data = self.dashboard_templates[template].copy()
            dashboard_data["dashboard"]["title"] = name
            
            async with self.session.post(
                f"{self.grafana_url}/api/dashboards/db",
                json=dashboard_data
            ) as response:
                if response.status != 200:
                    raise Exception(
                        f"Dashboard creation failed: {await response.text()}"
                    )
                    
                return await response.json()
                
        except Exception as e:
            self.logger.error(f"Dashboard creation failed: {str(e)}")
            raise
            
    async def optimize_performance(self) -> Dict[str, Any]:
        """Optimize system performance."""
        try:
            optimizations = {}
            
            # Optimize GPU memory
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                gc.collect()
                
                optimizations["gpu"] = {
                    "memory_freed": torch.cuda.memory_allocated(),
                    "cache_cleared": True
                }
                
            # Optimize batch size
            optimizations["batch_size"] = await self._optimize_batch_size()
            
            # Optimize database
            optimizations["database"] = await self._optimize_database()
            
            return {
                "status": "success",
                "optimizations": optimizations,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Performance optimization failed: {str(e)}")
            raise
            
    async def _optimize_batch_size(self,
                                 initial_size: int = 32,
                                 target_memory: float = 0.8
                                 ) -> Dict[str, Any]:
        """Optimize batch size based on available memory."""
        if not torch.cuda.is_available():
            return {"batch_size": initial_size}
            
        gpu_memory = torch.cuda.get_device_properties(0).total_memory
        target_memory = int(gpu_memory * target_memory)
        
        # Binary search for optimal batch size
        left, right = 1, initial_size * 2
        optimal_size = initial_size
        
        while left <= right:
            mid = (left + right) // 2
            try:
                dummy_input = torch.randn(mid, 3, 224, 224, device="cuda")
                memory_used = torch.cuda.memory_allocated()
                
                if memory_used < target_memory:
                    optimal_size = mid
                    left = mid + 1
                else:
                    right = mid - 1
                    
                del dummy_input
                torch.cuda.empty_cache()
                
            except RuntimeError:
                right = mid - 1
                
        return {
            "batch_size": optimal_size,
            "memory_target": target_memory
        }
        
    async def _optimize_database(self) -> Dict[str, Any]:
        """Optimize database performance."""
        slow_queries = await self.db.get_slow_queries()
        index_updates = await self.db.optimize_indexes()
        plan_updates = await self.db.update_query_plans()
        
        return {
            "slow_queries": len(slow_queries),
            "index_updates": index_updates,
            "plan_updates": plan_updates
        }
        
    async def _monitor_resources(self):
        """Continuous resource monitoring."""
        while True:
            try:
                metrics = await self.collect_metrics()
                
                # Update history
                for key in self.performance_history:
                    if key in metrics:
                        self.performance_history[key].append(metrics[key])
                        
                        # Keep last hour of metrics
                        if len(self.performance_history[key]) > 3600:
                            self.performance_history[key].pop(0)
                            
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Resource monitoring failed: {str(e)}")
                await asyncio.sleep(5)
                
    async def get_performance_history(self) -> Dict[str, Any]:
        """Get performance metrics history."""
        return {
            "cpu_usage": np.mean(self.performance_history["cpu_usage"]),
            "memory_usage": np.mean(self.performance_history["memory_usage"]),
            "gpu_memory": np.mean(self.performance_history["gpu_memory"]),
            "processing_times": np.mean(self.performance_history["processing_times"]),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    async def cleanup(self):
        """Cleanup resources."""
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
                
        await self.session.close()

# Global monitoring service instance
monitoring_service = MonitoringService() 