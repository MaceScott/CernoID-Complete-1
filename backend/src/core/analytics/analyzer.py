from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import asyncio
from pathlib import Path
import json
import logging
from collections import defaultdict
import plotly.graph_objects as go
import plotly.express as px
from dataclasses import dataclass
import aiofiles
import aiosqlite

from ..base import BaseComponent
from ..utils.errors import AnalyticsError

@dataclass
class AnalyticsPeriod:
    """Time period for analytics"""
    start_time: datetime
    end_time: datetime
    interval: str = '1h'  # Supported: 1m, 5m, 15m, 1h, 1d

@dataclass
class SystemMetrics:
    """System performance metrics"""
    recognition_rate: float
    accuracy: float
    processing_time: float
    error_rate: float
    resource_usage: Dict[str, float]
    timestamp: datetime

class AnalyticsEngine(BaseComponent):
    """Advanced analytics system"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        
        # Analytics settings
        self._db_path = config.get('analytics.db_path', 'data/analytics.db')
        self._metrics_interval = config.get('analytics.interval', 300)  # 5 minutes
        self._retention_days = config.get('analytics.retention', 90)
        
        # Performance thresholds
        self._min_accuracy = config.get('analytics.min_accuracy', 0.95)
        self._max_latency = config.get('analytics.max_latency', 1.0)
        self._max_error_rate = config.get('analytics.max_error_rate', 0.01)
        
        # Metrics storage
        self._metrics_cache: Dict[str, List] = defaultdict(list)
        self._last_cleanup = datetime.utcnow()
        
        # Initialize analytics
        self._initialize_analytics()
        
        # Statistics
        self._stats = {
            'total_recognitions': 0,
            'average_accuracy': 0.0,
            'average_latency': 0.0,
            'total_errors': 0,
            'uptime': 0.0
        }

    async def _initialize_analytics(self) -> None:
        """Initialize analytics system"""
        try:
            # Create database
            await self._create_database()
            
            # Start metrics collection
            self._collection_task = asyncio.create_task(
                self._collect_metrics()
            )
            
            # Start cleanup task
            self._cleanup_task = asyncio.create_task(
                self._cleanup_old_data()
            )
            
        except Exception as e:
            raise AnalyticsError(f"Analytics initialization failed: {str(e)}")

    async def _create_database(self) -> None:
        """Create analytics database"""
        try:
            async with aiosqlite.connect(self._db_path) as db:
                # Create metrics table
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        metric_type TEXT NOT NULL,
                        value REAL NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create events table
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        event_type TEXT NOT NULL,
                        description TEXT,
                        metadata TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create performance table
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS performance (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        recognition_rate REAL,
                        accuracy REAL,
                        processing_time REAL,
                        error_rate REAL,
                        resource_usage TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                await db.commit()
                
        except Exception as e:
            raise AnalyticsError(f"Database creation failed: {str(e)}")

    async def _collect_metrics(self) -> None:
        """Collect system metrics periodically"""
        while True:
            try:
                # Collect current metrics
                metrics = await self._get_system_metrics()
                
                # Store in database
                await self._store_metrics(metrics)
                
                # Update cache
                self._update_metrics_cache(metrics)
                
                # Wait for next interval
                await asyncio.sleep(self._metrics_interval)
                
            except Exception as e:
                self.logger.error(f"Metrics collection failed: {str(e)}")
                await asyncio.sleep(60)

    async def _get_system_metrics(self) -> SystemMetrics:
        """Get current system metrics"""
        try:
            # Get recognition stats
            recognition_stats = await self._get_recognition_stats()
            
            # Get resource usage
            resource_usage = await self._get_resource_usage()
            
            return SystemMetrics(
                recognition_rate=recognition_stats['rate'],
                accuracy=recognition_stats['accuracy'],
                processing_time=recognition_stats['latency'],
                error_rate=recognition_stats['error_rate'],
                resource_usage=resource_usage,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            raise AnalyticsError(f"Failed to get metrics: {str(e)}")

    async def _store_metrics(self, metrics: SystemMetrics) -> None:
        """Store metrics in database"""
        try:
            async with aiosqlite.connect(self._db_path) as db:
                # Store performance metrics
                await db.execute('''
                    INSERT INTO performance (
                        recognition_rate,
                        accuracy,
                        processing_time,
                        error_rate,
                        resource_usage,
                        timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    metrics.recognition_rate,
                    metrics.accuracy,
                    metrics.processing_time,
                    metrics.error_rate,
                    json.dumps(metrics.resource_usage),
                    metrics.timestamp.isoformat()
                ))
                
                await db.commit()
                
        except Exception as e:
            raise AnalyticsError(f"Failed to store metrics: {str(e)}")

    def _update_metrics_cache(self, metrics: SystemMetrics) -> None:
        """Update metrics cache"""
        try:
            # Add to cache
            self._metrics_cache['recognition_rate'].append(
                (metrics.timestamp, metrics.recognition_rate)
            )
            self._metrics_cache['accuracy'].append(
                (metrics.timestamp, metrics.accuracy)
            )
            self._metrics_cache['processing_time'].append(
                (metrics.timestamp, metrics.processing_time)
            )
            self._metrics_cache['error_rate'].append(
                (metrics.timestamp, metrics.error_rate)
            )
            
            # Trim old data
            cutoff = datetime.utcnow() - timedelta(hours=24)
            for metric_type in self._metrics_cache:
                self._metrics_cache[metric_type] = [
                    (ts, val) for ts, val in self._metrics_cache[metric_type]
                    if ts > cutoff
                ]
                
        except Exception as e:
            self.logger.error(f"Cache update failed: {str(e)}")

    async def _cleanup_old_data(self) -> None:
        """Clean up old analytics data"""
        while True:
            try:
                # Calculate cutoff date
                cutoff = datetime.utcnow() - timedelta(days=self._retention_days)
                
                async with aiosqlite.connect(self._db_path) as db:
                    # Delete old metrics
                    await db.execute('''
                        DELETE FROM metrics
                        WHERE timestamp < ?
                    ''', (cutoff.isoformat(),))
                    
                    # Delete old events
                    await db.execute('''
                        DELETE FROM events
                        WHERE timestamp < ?
                    ''', (cutoff.isoformat(),))
                    
                    # Delete old performance data
                    await db.execute('''
                        DELETE FROM performance
                        WHERE timestamp < ?
                    ''', (cutoff.isoformat(),))
                    
                    await db.commit()
                
                # Update last cleanup time
                self._last_cleanup = datetime.utcnow()
                
                # Wait for next day
                await asyncio.sleep(86400)  # 24 hours
                
            except Exception as e:
                self.logger.error(f"Data cleanup failed: {str(e)}")
                await asyncio.sleep(3600)  # 1 hour

    async def get_performance_metrics(self,
                                   period: AnalyticsPeriod) -> pd.DataFrame:
        """Get performance metrics for period"""
        try:
            async with aiosqlite.connect(self._db_path) as db:
                # Query performance data
                query = '''
                    SELECT 
                        timestamp,
                        recognition_rate,
                        accuracy,
                        processing_time,
                        error_rate,
                        resource_usage,
                        batch_size,
                        cache_hits,
                        cache_misses,
                        gpu_utilization,
                        memory_usage
                    FROM performance
                    WHERE timestamp BETWEEN ? AND ?
                    ORDER BY timestamp ASC
                '''
                
                cursor = await db.execute(query, (
                    period.start_time.isoformat(),
                    period.end_time.isoformat()
                ))
                
                # Convert to DataFrame
                rows = await cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                df = pd.DataFrame(rows, columns=columns)
                
                # Parse timestamps
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                
                # Parse resource usage
                df['resource_usage'] = df['resource_usage'].apply(json.loads)
                
                # Resample data based on interval
                interval_map = {
                    '1m': '1T',
                    '5m': '5T',
                    '15m': '15T',
                    '1h': '1H',
                    '1d': '1D'
                }
                df = df.set_index('timestamp').resample(
                    interval_map[period.interval]
                ).agg({
                    'recognition_rate': 'mean',
                    'accuracy': 'mean',
                    'processing_time': 'mean',
                    'error_rate': 'mean',
                    'batch_size': 'mean',
                    'cache_hits': 'sum',
                    'cache_misses': 'sum',
                    'gpu_utilization': 'mean',
                    'memory_usage': 'mean'
                }).reset_index()
                
                return df
                
        except Exception as e:
            raise AnalyticsError(f"Failed to get metrics: {str(e)}")

    async def generate_performance_report(self,
                                       period: AnalyticsPeriod) -> Dict:
        """Generate performance report"""
        try:
            # Get metrics
            df = await self.get_performance_metrics(period)
            
            # Calculate statistics
            stats = {
                'recognition': {
                    'average_rate': float(df['recognition_rate'].mean()),
                    'peak_rate': float(df['recognition_rate'].max()),
                    'total_recognitions': int(df['recognition_rate'].sum() * self._metrics_interval)
                },
                'accuracy': {
                    'average': float(df['accuracy'].mean()),
                    'min': float(df['accuracy'].min()),
                    'std_dev': float(df['accuracy'].std())
                },
                'performance': {
                    'average_processing_time': float(df['processing_time'].mean()),
                    'peak_processing_time': float(df['processing_time'].max()),
                    'average_batch_size': float(df['batch_size'].mean())
                },
                'errors': {
                    'average_error_rate': float(df['error_rate'].mean()),
                    'peak_error_rate': float(df['error_rate'].max())
                },
                'caching': {
                    'total_cache_hits': int(df['cache_hits'].sum()),
                    'total_cache_misses': int(df['cache_misses'].sum()),
                    'cache_hit_ratio': float(
                        df['cache_hits'].sum() / 
                        (df['cache_hits'].sum() + df['cache_misses'].sum())
                    )
                },
                'resources': {
                    'average_gpu_utilization': float(df['gpu_utilization'].mean()),
                    'peak_gpu_utilization': float(df['gpu_utilization'].max()),
                    'average_memory_usage': float(df['memory_usage'].mean()),
                    'peak_memory_usage': float(df['memory_usage'].max())
                }
            }
            
            # Generate plots
            plots = {
                'recognition_rate': self._create_time_series(
                    df, 'recognition_rate', 'Recognition Rate',
                    color='blue', fill=True
                ),
                'accuracy': self._create_time_series(
                    df, 'accuracy', 'Accuracy',
                    color='green', fill=True
                ),
                'processing_time': self._create_time_series(
                    df, 'processing_time', 'Processing Time (ms)',
                    color='orange'
                ),
                'error_rate': self._create_time_series(
                    df, 'error_rate', 'Error Rate',
                    color='red'
                ),
                'resource_usage': self._create_resource_usage_plot(df),
                'cache_performance': self._create_cache_performance_plot(df)
            }
            
            return {
                'period': {
                    'start': period.start_time.isoformat(),
                    'end': period.end_time.isoformat(),
                    'interval': period.interval
                },
                'statistics': stats,
                'plots': plots
            }
            
        except Exception as e:
            raise AnalyticsError(f"Report generation failed: {str(e)}")

    def _create_time_series(self,
                          df: pd.DataFrame,
                          metric: str,
                          title: str,
                          color: str = 'blue',
                          fill: bool = False) -> Dict:
        """Create time series plot"""
        try:
            fig = go.Figure()
            
            # Add main trace
            fig.add_trace(go.Scatter(
                x=df['timestamp'],
                y=df[metric],
                mode='lines',
                name=title,
                line=dict(color=color),
                fill='tozeroy' if fill else None
            ))
            
            # Add trend line
            z = np.polyfit(range(len(df)), df[metric], 1)
            p = np.poly1d(z)
            fig.add_trace(go.Scatter(
                x=df['timestamp'],
                y=p(range(len(df))),
                mode='lines',
                name='Trend',
                line=dict(
                    color='rgba(0,0,0,0.3)',
                    dash='dash'
                )
            ))
            
            # Update layout
            fig.update_layout(
                title=title,
                xaxis_title='Time',
                yaxis_title=metric.replace('_', ' ').title(),
                showlegend=True,
                hovermode='x unified'
            )
            
            return fig.to_dict()
            
        except Exception as e:
            self.logger.error(f"Failed to create time series plot: {str(e)}")
            return {}

    def _create_resource_usage_plot(self, df: pd.DataFrame) -> Dict:
        """Create resource usage plot"""
        try:
            fig = go.Figure()
            
            # Add GPU utilization
            fig.add_trace(go.Scatter(
                x=df['timestamp'],
                y=df['gpu_utilization'],
                mode='lines',
                name='GPU Utilization',
                line=dict(color='purple')
            ))
            
            # Add memory usage
            fig.add_trace(go.Scatter(
                x=df['timestamp'],
                y=df['memory_usage'],
                mode='lines',
                name='Memory Usage',
                line=dict(color='blue')
            ))
            
            # Update layout
            fig.update_layout(
                title='Resource Usage',
                xaxis_title='Time',
                yaxis_title='Percentage',
                showlegend=True,
                hovermode='x unified'
            )
            
            return fig.to_dict()
            
        except Exception as e:
            self.logger.error(f"Failed to create resource usage plot: {str(e)}")
            return {}

    def _create_cache_performance_plot(self, df: pd.DataFrame) -> Dict:
        """Create cache performance plot"""
        try:
            fig = go.Figure()
            
            # Add cache hits
            fig.add_trace(go.Bar(
                x=df['timestamp'],
                y=df['cache_hits'],
                name='Cache Hits',
                marker_color='green'
            ))
            
            # Add cache misses
            fig.add_trace(go.Bar(
                x=df['timestamp'],
                y=df['cache_misses'],
                name='Cache Misses',
                marker_color='red'
            ))
            
            # Add hit ratio line
            hit_ratio = df['cache_hits'] / (df['cache_hits'] + df['cache_misses'])
            fig.add_trace(go.Scatter(
                x=df['timestamp'],
                y=hit_ratio,
                mode='lines',
                name='Hit Ratio',
                yaxis='y2',
                line=dict(color='blue')
            ))
            
            # Update layout
            fig.update_layout(
                title='Cache Performance',
                xaxis_title='Time',
                yaxis_title='Count',
                yaxis2=dict(
                    title='Hit Ratio',
                    overlaying='y',
                    side='right',
                    range=[0, 1]
                ),
                showlegend=True,
                hovermode='x unified'
            )
            
            return fig.to_dict()
            
        except Exception as e:
            self.logger.error(f"Failed to create cache performance plot: {str(e)}")
            return {}

    async def get_stats(self) -> Dict:
        """Get analytics statistics"""
        return self._stats.copy() 