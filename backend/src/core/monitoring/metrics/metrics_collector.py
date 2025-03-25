from typing import Dict, List, Optional, Union, Any, Tuple
import asyncio
import time
from datetime import datetime, timedelta
import psutil
import logging
from dataclasses import dataclass
import prometheus_client as prom
from prometheus_client import CollectorRegistry, Gauge, Counter, Histogram, Summary
import numpy as np
import json
import GPUtil
from pathlib import Path
import pandas as pd
from scipy import stats
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ..base import BaseComponent
from ..utils.errors import MonitorError

@dataclass
class MetricDefinition:
    """Metric definition"""
    name: str
    type: str
    description: str
    labels: List[str]
    buckets: Optional[List[float]] = None

@dataclass
class MetricsConfig:
    """Metrics collection configuration"""
    interval: float = 1.0  # seconds
    history_size: int = 3600  # 1 hour
    enable_gpu: bool = True
    enable_process: bool = True
    enable_network: bool = True
    log_directory: str = 'logs/metrics'
    anomaly_threshold: float = 3.0
    aggregation_window: str = '5min'

@dataclass
class AggregatedMetrics:
    """Aggregated metrics with statistics"""
    metric_name: str
    count: int
    mean: float
    median: float
    std_dev: float
    min_value: float
    max_value: float
    percentiles: Dict[str, float]
    trend: str
    anomalies: List[Dict[str, Any]]

@dataclass
class MetricVisualization:
    """Metric visualization data"""
    figure: Any  # Plotly figure
    title: str
    description: str
    insights: List[str]

class UnifiedMetricsCollector(BaseComponent):
    """Unified system metrics collection"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Configuration
        self.config = MetricsConfig(
            interval=config.get('metrics.interval', 1.0),
            history_size=config.get('metrics.history_size', 3600),
            enable_gpu=config.get('metrics.enable_gpu', True),
            enable_process=config.get('metrics.enable_process', True),
            enable_network=config.get('metrics.enable_network', True),
            log_directory=config.get('metrics.log_directory', 'logs/metrics'),
            anomaly_threshold=config.get('metrics.anomaly_threshold', 3.0),
            aggregation_window=config.get('metrics.aggregation_window', '5min')
        )
        
        # Initialize registry
        self._registry = CollectorRegistry()
        
        # Initialize metrics
        self._metrics: Dict[str, Union[Counter, Gauge, Histogram, Summary]] = {}
        self._setup_metrics()
        
        # Metrics history
        self._history: Dict[str, List[Dict[str, Any]]] = {}
        
        # Anomaly detection
        self._anomaly_history: Dict[str, List[Dict[str, Any]]] = {}
        self._baseline_stats: Dict[str, Dict[str, float]] = {}
        
        # Setup logging
        self._setup_logging()
        
        # Start collection
        self._collection_task = None
        self._collecting = False

    def _setup_metrics(self) -> None:
        """Setup all metrics collectors"""
        # System metrics
        self._setup_system_metrics()
        
        # Application metrics
        self._setup_application_metrics()
        
        # Performance metrics
        self._setup_performance_metrics()
        
        # Recognition metrics
        self._setup_recognition_metrics()
        
        # Database metrics
        self._setup_database_metrics()
        
        # Cache metrics
        self._setup_cache_metrics()

    def _setup_system_metrics(self) -> None:
        """Setup system-level metrics"""
        # CPU metrics
        self._metrics['cpu_usage'] = Gauge(
            'system_cpu_usage',
            'CPU usage percentage',
            ['cpu'],
            registry=self._registry
        )
        
        # Memory metrics
        self._metrics['memory_usage'] = Gauge(
            'system_memory_usage',
            'Memory usage in bytes',
            ['type'],
            registry=self._registry
        )
        
        # Disk metrics
        self._metrics['disk_usage'] = Gauge(
            'system_disk_usage',
            'Disk usage percentage',
            ['device'],
            registry=self._registry
        )
        
        # GPU metrics if enabled
        if self.config.enable_gpu:
            self._metrics['gpu_usage'] = Gauge(
                'system_gpu_usage',
                'GPU usage percentage',
                ['gpu'],
                registry=self._registry
            )
            self._metrics['gpu_memory'] = Gauge(
                'system_gpu_memory',
                'GPU memory usage in bytes',
                ['gpu'],
                registry=self._registry
            )
        
        # Network metrics if enabled
        if self.config.enable_network:
            self._metrics['network_io'] = Counter(
                'system_network_io_bytes',
                'Network I/O in bytes',
                ['direction'],
                registry=self._registry
            )

    def _setup_application_metrics(self) -> None:
        """Setup application-specific metrics"""
        # Request metrics
        self._metrics['request_total'] = Counter(
            'app_request_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status'],
            registry=self._registry
        )
        
        self._metrics['request_duration'] = Histogram(
            'app_request_duration_seconds',
            'HTTP request duration',
            ['method', 'endpoint'],
            registry=self._registry
        )
        
        # Error metrics
        self._metrics['error_total'] = Counter(
            'app_error_total',
            'Total application errors',
            ['type', 'component'],
            registry=self._registry
        )

    def _setup_performance_metrics(self) -> None:
        """Setup performance metrics"""
        # Processing metrics
        self._metrics['processing_time'] = Histogram(
            'app_processing_time_seconds',
            'Processing time in seconds',
            ['operation'],
            registry=self._registry
        )
        
        self._metrics['queue_size'] = Gauge(
            'app_queue_size',
            'Queue size',
            ['queue'],
            registry=self._registry
        )
        
        # Component health
        self._metrics['component_health'] = Gauge(
            'app_component_health',
            'Component health status',
            ['component'],
            registry=self._registry
        )

    def _setup_recognition_metrics(self) -> None:
        """Setup recognition-specific metrics"""
        # Recognition performance
        self._metrics['recognition_rate'] = Counter(
            'recognition_total',
            'Total face recognitions',
            ['result'],
            registry=self._registry
        )
        
        self._metrics['recognition_accuracy'] = Gauge(
            'recognition_accuracy',
            'Recognition accuracy',
            ['model'],
            registry=self._registry
        )
        
        self._metrics['recognition_latency'] = Histogram(
            'recognition_latency_seconds',
            'Recognition latency in seconds',
            ['model'],
            registry=self._registry
        )

    def _setup_database_metrics(self) -> None:
        """Setup database metrics"""
        self._metrics['db_connections'] = Gauge(
            'db_connections_active',
            'Active database connections',
            registry=self._registry
        )
        
        self._metrics['db_operations'] = Counter(
            'db_operations_total',
            'Total database operations',
            ['operation'],
            registry=self._registry
        )
        
        self._metrics['db_latency'] = Histogram(
            'db_operation_latency_seconds',
            'Database operation latency',
            ['operation'],
            registry=self._registry
        )

    def _setup_cache_metrics(self) -> None:
        """Setup cache metrics"""
        self._metrics['cache_operations'] = Counter(
            'cache_operations_total',
            'Total cache operations',
            ['operation', 'cache'],
            registry=self._registry
        )
        
        self._metrics['cache_size'] = Gauge(
            'cache_size',
            'Current cache size',
            ['cache'],
            registry=self._registry
        )
        
        self._metrics['cache_hit_ratio'] = Gauge(
            'cache_hit_ratio',
            'Cache hit ratio',
            ['cache'],
            registry=self._registry
        )

    def _setup_logging(self) -> None:
        """Setup metrics logging"""
        log_path = Path(self.config.log_directory)
        log_path.mkdir(parents=True, exist_ok=True)
        
        handler = logging.FileHandler(log_path / 'metrics.log')
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    async def start_collection(self) -> None:
        """Start metrics collection"""
        if self._collecting:
            return
            
        self._collecting = True
        self._collection_task = asyncio.create_task(self._collect_metrics())
        self.logger.info("Metrics collection started")

    async def stop_collection(self) -> None:
        """Stop metrics collection"""
        if not self._collecting:
            return
            
        self._collecting = False
        if self._collection_task:
            self._collection_task.cancel()
            try:
                await self._collection_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Metrics collection stopped")

    async def _collect_metrics(self) -> None:
        """Collect all metrics periodically"""
        while self._collecting:
            try:
                # Collect system metrics
                await self._collect_system_metrics()
                
                # Collect application metrics
                await self._collect_application_metrics()
                
                # Store history
                self._store_history()
                
                # Wait for next interval
                await asyncio.sleep(self.config.interval)
                
            except Exception as e:
                self.logger.error(f"Metrics collection failed: {str(e)}")
                await asyncio.sleep(1)

    async def _collect_system_metrics(self) -> None:
        """Collect system metrics"""
        try:
            # CPU metrics
            for cpu_num, cpu_percent in enumerate(psutil.cpu_percent(percpu=True)):
                self._metrics['cpu_usage'].labels(cpu=str(cpu_num)).set(cpu_percent)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            self._metrics['memory_usage'].labels(type='total').set(memory.total)
            self._metrics['memory_usage'].labels(type='used').set(memory.used)
            self._metrics['memory_usage'].labels(type='available').set(memory.available)
            
            # Disk metrics
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    self._metrics['disk_usage'].labels(
                        device=partition.device
                    ).set(usage.percent)
                except Exception:
                    continue
            
            # GPU metrics if enabled
            if self.config.enable_gpu:
                gpus = GPUtil.getGPUs()
                for idx, gpu in enumerate(gpus):
                    self._metrics['gpu_usage'].labels(
                        gpu=str(idx)
                    ).set(gpu.load * 100)
                    self._metrics['gpu_memory'].labels(
                        gpu=str(idx)
                    ).set(gpu.memoryUsed)
            
            # Network metrics if enabled
            if self.config.enable_network:
                net_io = psutil.net_io_counters()
                self._metrics['network_io'].labels(
                    direction='sent'
                ).inc(net_io.bytes_sent)
                self._metrics['network_io'].labels(
                    direction='received'
                ).inc(net_io.bytes_recv)
                
        except Exception as e:
            self.logger.error(f"System metrics collection failed: {str(e)}")

    async def _collect_application_metrics(self) -> None:
        """Collect application metrics"""
        try:
            # Collect component health
            for component, health in self.app.monitor.get_component_status().items():
                self._metrics['component_health'].labels(
                    component=component
                ).set(1 if health.status == 'healthy' else 0)
            
            # Collect queue sizes
            for queue_name, size in self.app.get_queue_sizes().items():
                self._metrics['queue_size'].labels(
                    queue=queue_name
                ).set(size)
                
        except Exception as e:
            self.logger.error(f"Application metrics collection failed: {str(e)}")

    def _store_history(self) -> None:
        """Store metrics history with enhanced error handling"""
        try:
            timestamp = datetime.utcnow()
            
            for metric_name, metric in self._metrics.items():
                if metric_name not in self._history:
                    self._history[metric_name] = []
                
                try:
                    # Get current value
                    if isinstance(metric, (Counter, Gauge)):
                        value = metric._value.get()
                    else:  # Histogram, Summary
                        value = metric._sum.get()
                    
                    # Add to history
                    entry = {
                        'timestamp': timestamp,
                        'value': value
                    }
                    
                    self._history[metric_name].append(entry)
                    
                    # Update baseline stats
                    if metric_name not in self._baseline_stats:
                        self._baseline_stats[metric_name] = {
                            'mean': value,
                            'std_dev': 0,
                            'count': 1
                        }
                    else:
                        stats = self._baseline_stats[metric_name]
                        n = stats['count']
                        old_mean = stats['mean']
                        
                        # Update mean and standard deviation
                        new_mean = old_mean + (value - old_mean) / (n + 1)
                        new_std = np.sqrt(
                            (stats['std_dev']**2 * n + (value - old_mean) * (value - new_mean)) / (n + 1)
                        )
                        
                        self._baseline_stats[metric_name].update({
                            'mean': new_mean,
                            'std_dev': new_std,
                            'count': n + 1
                        })
                    
                    # Check for anomalies
                    if self._baseline_stats[metric_name]['count'] > 10:
                        z_score = abs(
                            (value - self._baseline_stats[metric_name]['mean']) /
                            self._baseline_stats[metric_name]['std_dev']
                        )
                        
                        if z_score > self.config.anomaly_threshold:
                            if metric_name not in self._anomaly_history:
                                self._anomaly_history[metric_name] = []
                            
                            self._anomaly_history[metric_name].append({
                                'timestamp': timestamp,
                                'value': value,
                                'z_score': z_score
                            })
                    
                    # Trim history
                    if len(self._history[metric_name]) > self.config.history_size:
                        self._history[metric_name] = self._history[metric_name][-self.config.history_size:]
                        
                except Exception as e:
                    self.logger.error(f"Failed to store metric {metric_name}: {str(e)}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"History storage failed: {str(e)}")

    def track_request(self,
                     endpoint: str,
                     method: str,
                     status: int,
                     duration: float) -> None:
        """Track API request"""
        try:
            self._metrics['request_total'].labels(
                endpoint=endpoint,
                method=method,
                status=str(status)
            ).inc()
            
            self._metrics['request_duration'].labels(
                endpoint=endpoint,
                method=method
            ).observe(duration)
            
        except Exception as e:
            self.logger.error(f"Request tracking failed: {str(e)}")

    def track_error(self,
                   error_type: str,
                   component: str) -> None:
        """Track application error"""
        try:
            self._metrics['error_total'].labels(
                type=error_type,
                component=component
            ).inc()
            
        except Exception as e:
            self.logger.error(f"Error tracking failed: {str(e)}")

    def track_recognition(self,
                        model: str,
                        result: str,
                        latency: float,
                        accuracy: float) -> None:
        """Track recognition metrics"""
        try:
            self._metrics['recognition_rate'].labels(
                result=result
            ).inc()
            
            self._metrics['recognition_accuracy'].labels(
                model=model
            ).set(accuracy)
            
            self._metrics['recognition_latency'].labels(
                model=model
            ).observe(latency)
            
        except Exception as e:
            self.logger.error(f"Recognition tracking failed: {str(e)}")

    def track_database(self,
                      operation: str,
                      latency: float) -> None:
        """Track database operation"""
        try:
            self._metrics['db_operations'].labels(
                operation=operation
            ).inc()
            
            self._metrics['db_latency'].labels(
                operation=operation
            ).observe(latency)
            
        except Exception as e:
            self.logger.error(f"Database tracking failed: {str(e)}")

    def track_cache(self,
                   cache: str,
                   operation: str,
                   hit: bool = None) -> None:
        """Track cache operation"""
        try:
            self._metrics['cache_operations'].labels(
                operation=operation,
                cache=cache
            ).inc()
            
            if hit is not None:
                hits = self._metrics['cache_operations'].labels(
                    operation='hit',
                    cache=cache
                )._value.get()
                total = self._metrics['cache_operations'].labels(
                    operation='total',
                    cache=cache
                )._value.get()
                
                if total > 0:
                    self._metrics['cache_hit_ratio'].labels(
                        cache=cache
                    ).set(hits / total)
            
        except Exception as e:
            self.logger.error(f"Cache tracking failed: {str(e)}")

    async def get_metrics(self,
                         metric_name: Optional[str] = None,
                         start_time: Optional[datetime] = None,
                         end_time: Optional[datetime] = None) -> Dict[str, List]:
        """Get historical metrics"""
        try:
            if metric_name:
                if metric_name not in self._history:
                    return {}
                history = self._history[metric_name]
            else:
                history = self._history
            
            # Filter by time range
            if start_time or end_time:
                if not start_time:
                    start_time = datetime.min
                if not end_time:
                    end_time = datetime.max
                    
                if metric_name:
                    history = [
                        m for m in history
                        if start_time <= m['timestamp'] <= end_time
                    ]
                else:
                    history = {
                        name: [
                            m for m in metrics
                            if start_time <= m['timestamp'] <= end_time
                        ]
                        for name, metrics in history.items()
                    }
            
            return history
            
        except Exception as e:
            self.logger.error(f"Failed to get metrics: {str(e)}")
            return {}

    def _detect_anomalies(self, metric_name: str, values: List[float]) -> List[Dict[str, Any]]:
        """Detect anomalies using statistical methods"""
        try:
            if len(values) < 10:
                return []
                
            # Calculate z-scores
            z_scores = stats.zscore(values)
            
            # Identify anomalies
            anomalies = []
            for i, (value, z_score) in enumerate(zip(values, z_scores)):
                if abs(z_score) > self.config.anomaly_threshold:
                    anomalies.append({
                        'index': i,
                        'value': value,
                        'z_score': z_score,
                        'timestamp': self._history[metric_name][i]['timestamp']
                    })
            
            return anomalies
            
        except Exception as e:
            self.logger.error(f"Anomaly detection failed: {str(e)}")
            return []

    async def get_aggregated_metrics(self,
                                   metric_name: Optional[str] = None,
                                   start_time: Optional[datetime] = None,
                                   end_time: Optional[datetime] = None,
                                   window: str = '5min') -> Dict[str, AggregatedMetrics]:
        """Get aggregated metrics with statistics"""
        try:
            # Get raw metrics
            raw_metrics = await self.get_metrics(metric_name, start_time, end_time)
            if not raw_metrics:
                return {}
                
            result = {}
            for name, data in raw_metrics.items():
                if not data:
                    continue
                    
                # Convert to DataFrame for easier analysis
                df = pd.DataFrame(data)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
                
                # Resample and aggregate
                resampled = df['value'].resample(window).agg([
                    'count', 'mean', 'median', 'std', 'min', 'max'
                ])
                
                # Calculate percentiles
                percentiles = {
                    '95th': np.percentile(df['value'], 95),
                    '99th': np.percentile(df['value'], 99),
                    '99.9th': np.percentile(df['value'], 99.9)
                }
                
                # Detect trend
                trend = 'stable'
                if len(df) > 1:
                    slope = stats.linregress(range(len(df)), df['value']).slope
                    if slope > 0.1:
                        trend = 'increasing'
                    elif slope < -0.1:
                        trend = 'decreasing'
                
                # Detect anomalies
                anomalies = self._detect_anomalies(name, df['value'].values)
                
                result[name] = AggregatedMetrics(
                    metric_name=name,
                    count=int(resampled['count'].sum()),
                    mean=float(resampled['mean'].mean()),
                    median=float(resampled['median'].mean()),
                    std_dev=float(resampled['std'].mean()),
                    min_value=float(resampled['min'].min()),
                    max_value=float(resampled['max'].max()),
                    percentiles=percentiles,
                    trend=trend,
                    anomalies=anomalies
                )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Metrics aggregation failed: {str(e)}")
            return {}

    async def visualize_metrics(self,
                              metric_names: List[str],
                              start_time: Optional[datetime] = None,
                              end_time: Optional[datetime] = None) -> List[MetricVisualization]:
        """Generate visualizations for metrics"""
        try:
            visualizations = []
            
            # Get metrics data
            raw_metrics = await self.get_metrics(None, start_time, end_time)
            if not raw_metrics:
                return []
                
            for metric_name in metric_names:
                if metric_name not in raw_metrics:
                    continue
                    
                data = raw_metrics[metric_name]
                df = pd.DataFrame(data)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                
                # Create subplots
                fig = make_subplots(
                    rows=2, cols=1,
                    subplot_titles=(
                        f'{metric_name} Time Series',
                        f'{metric_name} Distribution'
                    )
                )
                
                # Add time series plot
                fig.add_trace(
                    go.Scatter(
                        x=df['timestamp'],
                        y=df['value'],
                        mode='lines',
                        name='Value'
                    ),
                    row=1, col=1
                )
                
                # Add anomalies if any
                anomalies = self._detect_anomalies(metric_name, df['value'].values)
                if anomalies:
                    anomaly_times = [a['timestamp'] for a in anomalies]
                    anomaly_values = [a['value'] for a in anomalies]
                    fig.add_trace(
                        go.Scatter(
                            x=anomaly_times,
                            y=anomaly_values,
                            mode='markers',
                            name='Anomalies',
                            marker=dict(color='red', size=10)
                        ),
                        row=1, col=1
                    )
                
                # Add distribution plot
                fig.add_trace(
                    go.Histogram(
                        x=df['value'],
                        name='Distribution'
                    ),
                    row=2, col=1
                )
                
                # Update layout
                fig.update_layout(
                    height=800,
                    showlegend=True,
                    title_text=f'Metric Analysis: {metric_name}'
                )
                
                # Generate insights
                insights = []
                agg_metrics = await self.get_aggregated_metrics(
                    metric_name, start_time, end_time
                )
                if metric_name in agg_metrics:
                    metrics = agg_metrics[metric_name]
                    insights.extend([
                        f"Average value: {metrics.mean:.2f}",
                        f"Trend: {metrics.trend}",
                        f"Standard deviation: {metrics.std_dev:.2f}",
                        f"Number of anomalies: {len(metrics.anomalies)}"
                    ])
                
                visualizations.append(MetricVisualization(
                    figure=fig,
                    title=f'Metric Analysis: {metric_name}',
                    description=f'Analysis of {metric_name} including time series and distribution',
                    insights=insights
                ))
            
            return visualizations
            
        except Exception as e:
            self.logger.error(f"Metric visualization failed: {str(e)}")
            return []

    async def export_metrics(self,
                           format: str = 'json',
                           output_dir: Optional[str] = None) -> Optional[str]:
        """Export metrics to various formats"""
        try:
            if not output_dir:
                output_dir = self.config.log_directory
                
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Get all metrics
            metrics_data = await self.get_metrics()
            if not metrics_data:
                return None
                
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            
            if format == 'json':
                output_file = output_path / f'metrics_export_{timestamp}.json'
                with open(output_file, 'w') as f:
                    json.dump(metrics_data, f, default=str, indent=2)
                    
            elif format == 'csv':
                output_file = output_path / f'metrics_export_{timestamp}.csv'
                all_metrics = []
                for metric_name, data in metrics_data.items():
                    for entry in data:
                        entry['metric_name'] = metric_name
                        all_metrics.append(entry)
                        
                df = pd.DataFrame(all_metrics)
                df.to_csv(output_file, index=False)
                
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"Metrics export failed: {str(e)}")
            return None

    async def analyze_correlations(self,
                                 metric_names: List[str],
                                 window: str = '5min') -> Dict[str, float]:
        """Analyze correlations between metrics"""
        try:
            metrics_data = await self.get_metrics()
            if not metrics_data:
                return {}
                
            # Prepare data for correlation analysis
            metric_series = {}
            for name in metric_names:
                if name not in metrics_data:
                    continue
                    
                df = pd.DataFrame(metrics_data[name])
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
                metric_series[name] = df['value'].resample(window).mean()
            
            if len(metric_series) < 2:
                return {}
                
            # Calculate correlations
            correlations = {}
            for i, (name1, series1) in enumerate(metric_series.items()):
                for name2, series2 in list(metric_series.items())[i+1:]:
                    # Align series and calculate correlation
                    aligned1, aligned2 = series1.align(series2, join='inner')
                    if len(aligned1) > 1:
                        corr = aligned1.corr(aligned2)
                        correlations[f"{name1}_vs_{name2}"] = corr
            
            return correlations
            
        except Exception as e:
            self.logger.error(f"Correlation analysis failed: {str(e)}")
            return {} 