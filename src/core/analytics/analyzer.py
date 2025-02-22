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
    """Analytics time period"""
    start_time: datetime
    end_time: datetime
    interval: str  # '1h', '1d', '1w', '1m'

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
                    SELECT *
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
                'average_recognition_rate': float(df['recognition_rate'].mean()),
                'average_accuracy': float(df['accuracy'].mean()),
                'average_processing_time': float(df['processing_time'].mean()),
                'average_error_rate': float(df['error_rate'].mean()),
                'total_recognitions': int(df['recognition_rate'].sum() * self._metrics_interval),
                'peak_processing_time': float(df['processing_time'].max()),
                'min_accuracy': float(df['accuracy'].min())
            }
            
            # Generate plots
            plots = {
                'recognition_rate': self._create_time_series(
                    df, 'recognition_rate', 'Recognition Rate'
                ),
                'accuracy': self._create_time_series(
                    df, 'accuracy', 'Accuracy'
                ),
                'processing_time': self._create_time_series(
                    df, 'processing_time', 'Processing Time'
                ),
                'error_rate': self._create_time_series(
                    df, 'error_rate', 'Error Rate'
                )
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
                          title: str) -> Dict:
        """Create time series plot"""
        try:
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=df['timestamp'],
                y=df[metric],
                mode='lines',
                name=metric
            ))
            
            fig.update_layout(
                title=title,
                xaxis_title='Time',
                yaxis_title=metric.replace('_', ' ').title()
            )
            
            return fig.to_dict()
            
        except Exception as e:
            self.logger.error(f"Plot creation failed: {str(e)}")
            return {}

    async def get_stats(self) -> Dict:
        """Get analytics statistics"""
        return self._stats.copy() 