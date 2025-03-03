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
from datetime import datetime
import logging
from dataclasses import dataclass
from sklearn.metrics import precision_recall_curve, roc_curve, auc
import asyncio
from pathlib import Path
import json

from ..base import BaseComponent
from ..utils.errors import MetricsError

@dataclass
class RecognitionMetrics:
    """Recognition quality metrics"""
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int
    average_confidence: float
    processing_time: float
    timestamp: datetime

class QualityMetricsTracker(BaseComponent):
    """Advanced recognition quality metrics tracking and analysis"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        
        # Metrics settings
        self._confidence_threshold = config.get('metrics.confidence_threshold', 0.85)
        self._min_accuracy = config.get('metrics.min_accuracy', 0.95)
        self._max_fpr = config.get('metrics.max_fpr', 0.01)
        self._max_processing_time = config.get('metrics.max_processing_time', 1.0)
        
        # Storage settings
        self._metrics_dir = Path(config.get('metrics.storage_path', 'data/metrics'))
        self._metrics_dir.mkdir(parents=True, exist_ok=True)
        
        # Metrics state
        self._metrics_history: List[RecognitionMetrics] = []
        self._metrics_lock = asyncio.Lock()
        
        # Load historical metrics
        self._load_metrics()
        
        # Start periodic saving
        self._save_interval = config.get('metrics.save_interval', 300)  # 5 minutes
        asyncio.create_task(self._periodic_save())

    def _load_metrics(self) -> None:
        """Load historical metrics from disk"""
        try:
            metrics_file = self._metrics_dir / 'recognition_metrics.json'
            if metrics_file.exists():
                with open(metrics_file, 'r') as f:
                    data = json.load(f)
                    
                self._metrics_history = [
                    RecognitionMetrics(
                        true_positives=m['true_positives'],
                        false_positives=m['false_positives'],
                        true_negatives=m['true_negatives'],
                        false_negatives=m['false_negatives'],
                        average_confidence=m['average_confidence'],
                        processing_time=m['processing_time'],
                        timestamp=datetime.fromisoformat(m['timestamp'])
                    )
                    for m in data['metrics']
                ]
                
                self.logger.info(f"Loaded {len(self._metrics_history)} historical metrics")
                
        except Exception as e:
            self.logger.error(f"Failed to load metrics: {str(e)}")

    async def _periodic_save(self) -> None:
        """Periodically save metrics to disk"""
        while True:
            try:
                await asyncio.sleep(self._save_interval)
                await self._save_metrics()
            except Exception as e:
                self.logger.error(f"Periodic metrics save failed: {str(e)}")

    async def _save_metrics(self) -> None:
        """Save metrics to disk"""
        try:
            async with self._metrics_lock:
                metrics_file = self._metrics_dir / 'recognition_metrics.json'
                
                data = {
                    'metrics': [
                        {
                            'true_positives': m.true_positives,
                            'false_positives': m.false_positives,
                            'true_negatives': m.true_negatives,
                            'false_negatives': m.false_negatives,
                            'average_confidence': m.average_confidence,
                            'processing_time': m.processing_time,
                            'timestamp': m.timestamp.isoformat()
                        }
                        for m in self._metrics_history
                    ]
                }
                
                with open(metrics_file, 'w') as f:
                    json.dump(data, f, indent=2)
                    
                self.logger.debug(f"Saved {len(self._metrics_history)} metrics to disk")
                
        except Exception as e:
            self.logger.error(f"Failed to save metrics: {str(e)}")

    async def track_recognition(self, 
                              prediction: bool,
                              ground_truth: bool,
                              confidence: float,
                              processing_time: float) -> None:
        """
        Track recognition result
        
        Args:
            prediction: Predicted match result
            ground_truth: Actual match result
            confidence: Recognition confidence
            processing_time: Processing time in seconds
        """
        try:
            metrics = RecognitionMetrics(
                true_positives=int(prediction and ground_truth),
                false_positives=int(prediction and not ground_truth),
                true_negatives=int(not prediction and not ground_truth),
                false_negatives=int(not prediction and ground_truth),
                average_confidence=confidence,
                processing_time=processing_time,
                timestamp=datetime.utcnow()
            )
            
            async with self._metrics_lock:
                self._metrics_history.append(metrics)
                
                # Limit history size
                if len(self._metrics_history) > 10000:
                    self._metrics_history = self._metrics_history[-10000:]
            
            # Check quality thresholds
            if await self._check_quality_issues(metrics):
                await self._handle_quality_alert()
                
        except Exception as e:
            self.logger.error(f"Metrics tracking failed: {str(e)}")
            raise MetricsError(f"Failed to track recognition: {str(e)}")

    async def get_quality_metrics(self,
                                window: Optional[int] = 1000) -> Dict:
        """
        Calculate current quality metrics
        
        Args:
            window: Number of recent recognitions to analyze
            
        Returns:
            Dictionary of quality metrics
        """
        try:
            async with self._metrics_lock:
                if not self._metrics_history:
                    return {}
                    
                recent_metrics = self._metrics_history[-window:] if window else self._metrics_history
                
                total = sum([
                    m.true_positives + m.false_positives +
                    m.true_negatives + m.false_negatives
                    for m in recent_metrics
                ])
                
                metrics = {
                    "accuracy": self._calculate_accuracy(recent_metrics),
                    "precision": self._calculate_precision(recent_metrics),
                    "recall": self._calculate_recall(recent_metrics),
                    "f1_score": self._calculate_f1_score(recent_metrics),
                    "false_positive_rate": self._calculate_fpr(recent_metrics),
                    "average_confidence": np.mean([m.average_confidence for m in recent_metrics]),
                    "average_processing_time": np.mean([m.processing_time for m in recent_metrics]),
                    "total_processed": total,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                return metrics
                
        except Exception as e:
            self.logger.error(f"Metrics calculation failed: {str(e)}")
            raise MetricsError(f"Failed to calculate metrics: {str(e)}")

    async def get_roc_curve(self) -> Tuple[List[float], List[float], List[float]]:
        """
        Generate ROC curve data
        
        Returns:
            Tuple of (false positive rates, true positive rates, thresholds)
        """
        try:
            async with self._metrics_lock:
                y_true = []
                y_scores = []
                
                for metric in self._metrics_history:
                    # Combine true positives and true negatives
                    actual = metric.true_positives or metric.false_negatives
                    y_true.append(actual)
                    y_scores.append(metric.average_confidence)
                    
                fpr, tpr, thresholds = roc_curve(y_true, y_scores)
                return fpr.tolist(), tpr.tolist(), thresholds.tolist()
                
        except Exception as e:
            self.logger.error(f"ROC curve generation failed: {str(e)}")
            raise MetricsError(f"Failed to generate ROC curve: {str(e)}")

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
                    actual = metric.true_positives or metric.false_negatives
                    y_true.append(actual)
                    y_scores.append(metric.average_confidence)
                    
                precision, recall, thresholds = precision_recall_curve(y_true, y_scores)
                f1_scores = 2 * (precision * recall) / (precision + recall)
                optimal_threshold = thresholds[np.argmax(f1_scores)]
                
                return float(optimal_threshold)
                
        except Exception as e:
            self.logger.error(f"Threshold optimization failed: {str(e)}")
            raise MetricsError(f"Failed to optimize threshold: {str(e)}")

    async def _check_quality_issues(self, metrics: RecognitionMetrics) -> bool:
        """Check for quality issues in recent metrics"""
        try:
            async with self._metrics_lock:
                recent_metrics = self._metrics_history[-100:]  # Last 100 recognitions
                
                # Check accuracy
                accuracy = self._calculate_accuracy(recent_metrics)
                if accuracy < self._min_accuracy:
                    self.logger.warning(f"Accuracy below threshold: {accuracy:.2f}")
                    return True
                    
                # Check false positive rate
                fpr = self._calculate_fpr(recent_metrics)
                if fpr > self._max_fpr:
                    self.logger.warning(f"False positive rate above threshold: {fpr:.2f}")
                    return True
                    
                # Check processing time
                if metrics.processing_time > self._max_processing_time:
                    self.logger.warning(f"Processing time above threshold: {metrics.processing_time:.2f}s")
                    return True
                    
                return False
                
        except Exception as e:
            self.logger.error(f"Quality check failed: {str(e)}")
            return False

    async def _handle_quality_alert(self) -> None:
        """Handle quality issue alert"""
        try:
            # Get current metrics
            metrics = await self.get_quality_metrics(window=100)
            
            # Create alert
            alert = {
                "type": "quality_issue",
                "metrics": metrics,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Save alert
            alert_file = self._metrics_dir / 'quality_alerts.json'
            try:
                if alert_file.exists():
                    with open(alert_file, 'r') as f:
                        alerts = json.load(f)
                else:
                    alerts = []
            except:
                alerts = []
                
            alerts.append(alert)
            
            with open(alert_file, 'w') as f:
                json.dump(alerts, f, indent=2)
                
            self.logger.warning("Quality issue detected and logged")
            
        except Exception as e:
            self.logger.error(f"Failed to handle quality alert: {str(e)}")

    @staticmethod
    def _calculate_accuracy(metrics: List[RecognitionMetrics]) -> float:
        """Calculate accuracy from metrics"""
        total = sum([
            m.true_positives + m.false_positives +
            m.true_negatives + m.false_negatives
            for m in metrics
        ])
        correct = sum([m.true_positives + m.true_negatives for m in metrics])
        return correct / total if total > 0 else 0

    @staticmethod
    def _calculate_precision(metrics: List[RecognitionMetrics]) -> float:
        """Calculate precision from metrics"""
        positives = sum([m.true_positives + m.false_positives for m in metrics])
        return sum([m.true_positives for m in metrics]) / positives if positives > 0 else 0

    @staticmethod
    def _calculate_recall(metrics: List[RecognitionMetrics]) -> float:
        """Calculate recall from metrics"""
        actual_positives = sum([m.true_positives + m.false_negatives for m in metrics])
        return sum([m.true_positives for m in metrics]) / actual_positives if actual_positives > 0 else 0

    @staticmethod
    def _calculate_f1_score(metrics: List[RecognitionMetrics]) -> float:
        """Calculate F1 score from metrics"""
        precision = QualityMetricsTracker._calculate_precision(metrics)
        recall = QualityMetricsTracker._calculate_recall(metrics)
        return 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    @staticmethod
    def _calculate_fpr(metrics: List[RecognitionMetrics]) -> float:
        """Calculate false positive rate from metrics"""
        negatives = sum([m.false_positives + m.true_negatives for m in metrics])
        return sum([m.false_positives for m in metrics]) / negatives if negatives > 0 else 0

# Global metrics tracker instance
metrics_tracker = QualityMetricsTracker({}) 