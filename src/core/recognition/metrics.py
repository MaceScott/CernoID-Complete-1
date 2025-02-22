from typing import Dict, List, Optional, Tuple
import numpy as np
from datetime import datetime
import logging
from dataclasses import dataclass
from sklearn.metrics import precision_recall_curve, roc_curve, auc

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

class QualityMetricsTracker:
    """Recognition quality metrics tracking and analysis"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger('QualityMetricsTracker')
        self._metrics_history: List[RecognitionMetrics] = []
        self._confidence_threshold = config.get('confidence_threshold', 0.85)

    async def track_recognition(self, 
                              prediction: bool,
                              ground_truth: bool,
                              confidence: float,
                              processing_time: float) -> None:
        """Track recognition result"""
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
            
            self._metrics_history.append(metrics)
            
            # Check quality thresholds
            if await self._check_quality_issues(metrics):
                await self._handle_quality_alert()
                
        except Exception as e:
            self.logger.error(f"Metrics tracking failed: {str(e)}")

    async def get_quality_metrics(self) -> Dict:
        """Calculate current quality metrics"""
        try:
            if not self._metrics_history:
                return {}
                
            recent_metrics = self._metrics_history[-1000:]  # Last 1000 recognitions
            
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
            raise

    async def get_roc_curve(self) -> Tuple[List[float], List[float], List[float]]:
        """Generate ROC curve data"""
        try:
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
            raise

    async def optimize_threshold(self) -> float:
        """Optimize confidence threshold"""
        try:
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
            raise

    async def _check_quality_issues(self, metrics: RecognitionMetrics) -> bool:
        """Check for quality issues"""
        recent_metrics = self._metrics_history[-100:]  # Last 100 recognitions
        
        # Check accuracy
        accuracy = self._calculate_accuracy(recent_metrics)
        if accuracy < self.config.get('min_accuracy', 0.95):
            return True
            
        # Check false positive rate
        fpr = self._calculate_fpr(recent_metrics)
        if fpr > self.config.get('max_fpr', 0.01):
            return True
            
        # Check processing time
        if metrics.processing_time > self.config.get('max_processing_time', 1.0):
            return True
            
        return False

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