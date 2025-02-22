from typing import Dict, List, Optional, Callable
import time
import asyncio
import statistics
from datetime import datetime
import psutil
import logging
from dataclasses import dataclass
import numpy as np

@dataclass
class BenchmarkResult:
    """Performance benchmark results"""
    operation: str
    execution_time: float
    memory_usage: float
    cpu_usage: float
    throughput: float
    concurrent_users: int
    timestamp: datetime
    details: Dict

class PerformanceBenchmarker:
    """System performance benchmarking"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger('PerformanceBenchmarker')
        self._results: List[BenchmarkResult] = []
        self._baseline_metrics: Dict = {}

    async def run_benchmark(self, 
                          operation: str,
                          test_func: Callable,
                          concurrent_users: int = 1,
                          duration: int = 60) -> BenchmarkResult:
        """Run performance benchmark"""
        try:
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss / 1024 / 1024
            
            # Create test tasks
            tasks = []
            request_count = 0
            
            async def worker():
                nonlocal request_count
                while time.time() - start_time < duration:
                    await test_func()
                    request_count += 1
            
            # Run concurrent workers
            workers = [worker() for _ in range(concurrent_users)]
            await asyncio.gather(*workers)
            
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024
            
            # Calculate metrics
            execution_time = end_time - start_time
            memory_usage = end_memory - start_memory
            cpu_usage = psutil.Process().cpu_percent()
            throughput = request_count / execution_time
            
            result = BenchmarkResult(
                operation=operation,
                execution_time=execution_time,
                memory_usage=memory_usage,
                cpu_usage=cpu_usage,
                throughput=throughput,
                concurrent_users=concurrent_users,
                timestamp=datetime.utcnow(),
                details={
                    "total_requests": request_count,
                    "avg_response_time": execution_time / request_count,
                    "memory_per_request": memory_usage / request_count
                }
            )
            
            self._results.append(result)
            await self._compare_with_baseline(result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Benchmark failed: {str(e)}")
            raise

    async def establish_baseline(self, 
                               operation: str,
                               test_func: Callable) -> None:
        """Establish performance baseline"""
        try:
            # Run multiple iterations to establish baseline
            iterations = 5
            results = []
            
            for _ in range(iterations):
                result = await self.run_benchmark(
                    operation,
                    test_func,
                    concurrent_users=1,
                    duration=30
                )
                results.append(result)
            
            # Calculate baseline metrics
            self._baseline_metrics[operation] = {
                "avg_throughput": statistics.mean([r.throughput for r in results]),
                "avg_response_time": statistics.mean([r.details["avg_response_time"] for r in results]),
                "avg_memory_usage": statistics.mean([r.memory_usage for r in results]),
                "avg_cpu_usage": statistics.mean([r.cpu_usage for r in results])
            }
            
            self.logger.info(f"Baseline established for {operation}")
            
        except Exception as e:
            self.logger.error(f"Baseline establishment failed: {str(e)}")
            raise

    async def generate_report(self) -> Dict:
        """Generate performance report"""
        try:
            report = {
                "summary": self._generate_summary(),
                "trends": self._analyze_trends(),
                "recommendations": self._generate_recommendations(),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Report generation failed: {str(e)}")
            raise

    def _generate_summary(self) -> Dict:
        """Generate performance summary"""
        summary = {}
        
        for operation in set(r.operation for r in self._results):
            op_results = [r for r in self._results if r.operation == operation]
            
            summary[operation] = {
                "avg_throughput": statistics.mean([r.throughput for r in op_results]),
                "max_throughput": max([r.throughput for r in op_results]),
                "avg_response_time": statistics.mean([r.details["avg_response_time"] for r in op_results]),
                "p95_response_time": np.percentile([r.details["avg_response_time"] for r in op_results], 95),
                "avg_memory_usage": statistics.mean([r.memory_usage for r in op_results]),
                "avg_cpu_usage": statistics.mean([r.cpu_usage for r in op_results])
            }
            
        return summary

    def _analyze_trends(self) -> Dict:
        """Analyze performance trends"""
        trends = {}
        
        for operation in set(r.operation for r in self._results):
            op_results = sorted([r for r in self._results if r.operation == operation],
                              key=lambda x: x.timestamp)
            
            if len(op_results) < 2:
                continue
                
            # Calculate trends
            throughput_trend = self._calculate_trend([r.throughput for r in op_results])
            response_trend = self._calculate_trend([r.details["avg_response_time"] for r in op_results])
            
            trends[operation] = {
                "throughput_trend": throughput_trend,
                "response_time_trend": response_trend,
                "degradation_detected": throughput_trend < 0 or response_trend > 0
            }
            
        return trends

    async def _compare_with_baseline(self, result: BenchmarkResult) -> None:
        """Compare results with baseline"""
        if result.operation not in self._baseline_metrics:
            return
            
        baseline = self._baseline_metrics[result.operation]
        
        # Check for significant deviations
        if result.throughput < baseline["avg_throughput"] * 0.8:
            self.logger.warning(
                f"Performance degradation detected in {result.operation}: "
                f"Throughput {result.throughput:.2f} vs baseline {baseline['avg_throughput']:.2f}"
            )

    @staticmethod
    def _calculate_trend(values: List[float]) -> float:
        """Calculate trend slope"""
        if len(values) < 2:
            return 0
        return (values[-1] - values[0]) / len(values) 