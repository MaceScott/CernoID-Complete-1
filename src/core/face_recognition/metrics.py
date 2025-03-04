"""
Advanced recognition quality metrics tracking and analysis system.

This module provides:
- Recognition quality metrics tracking
- Performance analysis
- ROC curve generation
- Threshold optimization
- Quality issue detection
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from sklearn.metrics import precision_recall_curve, roc_curve, auc
import asyncio
from pathlib import Path
import json
import plotly.graph_objects as go

from ..base import BaseComponent
from ..utils.errors import MetricsError

@dataclass
class RecognitionMetrics:
    """Recognition quality metrics"""
    timestamp: datetime
    true_positives: int
    false_positives: int
    false_negatives: int
    average_confidence: float
    processing_time: float
    face_count: int
    match_count: int

class QualityMetricsTracker(BaseComponent):
    """Advanced recognition quality metrics tracking and analysis"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        
        # Metrics settings
        self._metrics_interval = config.get('metrics.interval', 60)  # seconds
        self._history_size = config.get('metrics.history', 1000)
        self._confidence_threshold = config.get('metrics.confidence', 0.7)
        
        # Metrics storage
        self._metrics_history: List[RecognitionMetrics] = []
        self._metrics_lock = asyncio.Lock()
        
        # Performance thresholds
        self._min_accuracy = config.get('metrics.min_accuracy', 0.95)
        self._max_false_positives = config.get('metrics.max_false_positives', 0.01)
        self._max_processing_time = config.get('metrics.max_processing_time', 100)  # ms
        
        # Statistics
        self._stats = {
            'total_faces': 0,
            'total_matches': 0,
            'average_confidence': 0.0,
            'average_processing_time': 0.0,
            'accuracy': 0.0,
            'false_positive_rate': 0.0
        }
        
        self.logger = logging.getLogger(__name__)

    async def add_metrics(self,
                         true_positives: int,
                         false_positives: int,
                         false_negatives: int,
                         confidence: float,
                         processing_time: float,
                         face_count: int,
                         match_count: int) -> None:
        """Add new recognition metrics"""
        try:
            metrics = RecognitionMetrics(
                timestamp=datetime.utcnow(),
                true_positives=true_positives,
                false_positives=false_positives,
                false_negatives=false_negatives,
                average_confidence=confidence,
                processing_time=processing_time,
                face_count=face_count,
                match_count=match_count
            )
            
            async with self._metrics_lock:
                # Add to history
                self._metrics_history.append(metrics)
                if len(self._metrics_history) > self._history_size:
                    self._metrics_history.pop(0)
                
                # Update statistics
                self._update_statistics()
                
                # Save metrics to file
                await self._save_metrics(metrics)
                
                # Check for quality issues
                await self._check_quality()
            
        except Exception as e:
            raise MetricsError(f"Failed to add metrics: {str(e)}")

    def _update_statistics(self) -> None:
        """Update recognition statistics"""
        try:
            total_faces = sum(m.face_count for m in self._metrics_history)
            total_matches = sum(m.match_count for m in self._metrics_history)
            total_true_positives = sum(m.true_positives for m in self._metrics_history)
            total_false_positives = sum(m.false_positives for m in self._metrics_history)
            total_false_negatives = sum(m.false_negatives for m in self._metrics_history)
            
            # Calculate metrics
            accuracy = total_true_positives / (total_true_positives + total_false_positives + total_false_negatives)
            false_positive_rate = total_false_positives / (total_false_positives + total_true_positives)
            average_confidence = np.mean([m.average_confidence for m in self._metrics_history])
            average_processing_time = np.mean([m.processing_time for m in self._metrics_history])
            
            # Update statistics
            self._stats.update({
                'total_faces': total_faces,
                'total_matches': total_matches,
                'average_confidence': float(average_confidence),
                'average_processing_time': float(average_processing_time),
                'accuracy': float(accuracy),
                'false_positive_rate': float(false_positive_rate)
            })
            
        except Exception as e:
            self.logger.error(f"Statistics update failed: {str(e)}")

    async def _check_quality(self) -> None:
        """Check for quality issues"""
        try:
            issues = []
            
            # Check accuracy
            if self._stats['accuracy'] < self._min_accuracy:
                issues.append(f"Low accuracy: {self._stats['accuracy']:.2%}")
            
            # Check false positive rate
            if self._stats['false_positive_rate'] > self._max_false_positives:
                issues.append(
                    f"High false positive rate: {self._stats['false_positive_rate']:.2%}"
                )
            
            # Check processing time
            if self._stats['average_processing_time'] > self._max_processing_time:
                issues.append(
                    f"High processing time: {self._stats['average_processing_time']:.2f}ms"
                )
            
            # Log issues
            if issues:
                self.logger.warning(
                    "Quality issues detected:\n" + "\n".join(f"- {issue}" for issue in issues)
                )
            
        except Exception as e:
            self.logger.error(f"Quality check failed: {str(e)}")

    async def _save_metrics(self, metrics: RecognitionMetrics) -> None:
        """Save metrics to file"""
        try:
            metrics_file = Path('logs/recognition_metrics.jsonl')
            metrics_file.parent.mkdir(parents=True, exist_ok=True)
            
            metrics_dict = {
                'timestamp': metrics.timestamp.isoformat(),
                'true_positives': metrics.true_positives,
                'false_positives': metrics.false_positives,
                'false_negatives': metrics.false_negatives,
                'average_confidence': metrics.average_confidence,
                'processing_time': metrics.processing_time,
                'face_count': metrics.face_count,
                'match_count': metrics.match_count
            }
            
            with open(metrics_file, 'a') as f:
                f.write(json.dumps(metrics_dict) + '\n')
                
        except Exception as e:
            self.logger.error(f"Metrics saving failed: {str(e)}")

    async def optimize_threshold(self) -> float:
        """
        Optimize confidence threshold using precision-recall curve
        
        Returns:
            Optimal confidence threshold
        """
        try:
            async with self._metrics_lock:
                y_true = []
                y_scores = []
                
                for metric in self._metrics_history:
                    actual = metric.true_positives + metric.false_negatives
                    y_true.extend([1] * metric.true_positives + [0] * metric.false_positives)
                    y_scores.extend([metric.average_confidence] * (metric.true_positives + metric.false_positives))
                    
                if not y_true or not y_scores:
                    return self._confidence_threshold
                    
                # Calculate precision-recall curve
                precision, recall, thresholds = precision_recall_curve(y_true, y_scores)
                
                # Calculate F1 scores
                f1_scores = 2 * (precision * recall) / (precision + recall)
                
                # Find optimal threshold
                optimal_idx = np.argmax(f1_scores)
                optimal_threshold = thresholds[optimal_idx]
                
                # Save optimization results
                await self._save_optimization_results(
                    precision, recall, thresholds, f1_scores, optimal_threshold
                )
                
                return float(optimal_threshold)
                
        except Exception as e:
            self.logger.error(f"Threshold optimization failed: {str(e)}")
            return self._confidence_threshold

    async def _save_optimization_results(self,
                                      precision: np.ndarray,
                                      recall: np.ndarray,
                                      thresholds: np.ndarray,
                                      f1_scores: np.ndarray,
                                      optimal_threshold: float) -> None:
        """Save optimization results"""
        try:
            results_file = Path('logs/threshold_optimization.json')
            results_file.parent.mkdir(parents=True, exist_ok=True)
            
            results = {
                'timestamp': datetime.utcnow().isoformat(),
                'precision': precision.tolist(),
                'recall': recall.tolist(),
                'thresholds': thresholds.tolist(),
                'f1_scores': f1_scores.tolist(),
                'optimal_threshold': float(optimal_threshold)
            }
            
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save optimization results: {str(e)}")

    def create_quality_report(self) -> Dict:
        """Create quality metrics report with visualizations"""
        try:
            # Create time series plots
            plots = {
                'accuracy': self._create_accuracy_plot(),
                'confidence': self._create_confidence_plot(),
                'processing_time': self._create_processing_time_plot(),
                'face_counts': self._create_face_counts_plot()
            }
            
            # Calculate statistics
            recent_metrics = self._metrics_history[-100:]  # Last 100 records
            stats = {
                'recent': {
                    'accuracy': float(np.mean([
                        m.true_positives / (m.true_positives + m.false_positives + m.false_negatives)
                        for m in recent_metrics
                    ])),
                    'false_positive_rate': float(np.mean([
                        m.false_positives / (m.false_positives + m.true_positives)
                        for m in recent_metrics
                    ])),
                    'average_confidence': float(np.mean([
                        m.average_confidence for m in recent_metrics
                    ])),
                    'average_processing_time': float(np.mean([
                        m.processing_time for m in recent_metrics
                    ]))
                },
                'total': self._stats.copy()
            }
            
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'statistics': stats,
                'plots': plots
            }
            
        except Exception as e:
            self.logger.error(f"Report generation failed: {str(e)}")
            return {}

    def _create_accuracy_plot(self) -> Dict:
        """Create accuracy plot"""
        try:
            fig = go.Figure()
            
            # Add accuracy trace
            accuracies = [
                m.true_positives / (m.true_positives + m.false_positives + m.false_negatives)
                for m in self._metrics_history
            ]
            fig.add_trace(go.Scatter(
                x=[m.timestamp for m in self._metrics_history],
                y=accuracies,
                mode='lines',
                name='Accuracy',
                line=dict(color='green')
            ))
            
            # Add threshold line
            fig.add_hline(
                y=self._min_accuracy,
                line_dash="dash",
                line_color="red",
                annotation_text="Minimum Accuracy"
            )
            
            # Update layout
            fig.update_layout(
                title='Recognition Accuracy',
                xaxis_title='Time',
                yaxis_title='Accuracy',
                showlegend=True,
                hovermode='x unified'
            )
            
            return fig.to_dict()
            
        except Exception as e:
            self.logger.error(f"Accuracy plot creation failed: {str(e)}")
            return {}

    def _create_confidence_plot(self) -> Dict:
        """Create confidence plot"""
        try:
            fig = go.Figure()
            
            # Add confidence trace
            fig.add_trace(go.Scatter(
                x=[m.timestamp for m in self._metrics_history],
                y=[m.average_confidence for m in self._metrics_history],
                mode='lines',
                name='Confidence',
                line=dict(color='blue')
            ))
            
            # Add threshold line
            fig.add_hline(
                y=self._confidence_threshold,
                line_dash="dash",
                line_color="red",
                annotation_text="Confidence Threshold"
            )
            
            # Update layout
            fig.update_layout(
                title='Recognition Confidence',
                xaxis_title='Time',
                yaxis_title='Confidence',
                showlegend=True,
                hovermode='x unified'
            )
            
            return fig.to_dict()
            
        except Exception as e:
            self.logger.error(f"Confidence plot creation failed: {str(e)}")
            return {}

    def _create_processing_time_plot(self) -> Dict:
        """Create processing time plot"""
        try:
            fig = go.Figure()
            
            # Add processing time trace
            fig.add_trace(go.Scatter(
                x=[m.timestamp for m in self._metrics_history],
                y=[m.processing_time for m in self._metrics_history],
                mode='lines',
                name='Processing Time',
                line=dict(color='orange')
            ))
            
            # Add threshold line
            fig.add_hline(
                y=self._max_processing_time,
                line_dash="dash",
                line_color="red",
                annotation_text="Maximum Processing Time"
            )
            
            # Update layout
            fig.update_layout(
                title='Processing Time',
                xaxis_title='Time',
                yaxis_title='Processing Time (ms)',
                showlegend=True,
                hovermode='x unified'
            )
            
            return fig.to_dict()
            
        except Exception as e:
            self.logger.error(f"Processing time plot creation failed: {str(e)}")
            return {}

    def _create_face_counts_plot(self) -> Dict:
        """Create face counts plot"""
        try:
            fig = go.Figure()
            
            # Add face count trace
            fig.add_trace(go.Bar(
                x=[m.timestamp for m in self._metrics_history],
                y=[m.face_count for m in self._metrics_history],
                name='Total Faces',
                marker_color='blue'
            ))
            
            # Add match count trace
            fig.add_trace(go.Bar(
                x=[m.timestamp for m in self._metrics_history],
                y=[m.match_count for m in self._metrics_history],
                name='Matches',
                marker_color='green'
            ))
            
            # Update layout
            fig.update_layout(
                title='Face Detection and Recognition Counts',
                xaxis_title='Time',
                yaxis_title='Count',
                barmode='group',
                showlegend=True,
                hovermode='x unified'
            )
            
            return fig.to_dict()
            
        except Exception as e:
            self.logger.error(f"Face counts plot creation failed: {str(e)}")
            return {}

# Global metrics tracker instance
metrics_tracker = QualityMetricsTracker({}) 