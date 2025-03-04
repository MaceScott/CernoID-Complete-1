from typing import Dict, List, Optional, Any, Union
import asyncio
import logging
import time
from datetime import datetime
from pathlib import Path
import json
from ..base import BaseComponent
from ..utils.errors import handle_errors

class TestRunner(BaseComponent):
    """Test execution and reporting system"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._results: Dict[str, List[Dict]] = {}
        self._reports_path = Path(
            self.config.get('test.reports_path', 'reports')
        )
        self._current_run: Optional[Dict] = None
        self._parallel_tests = self.config.get('test.parallel_tests', 4)
        self._retry_failed = self.config.get('test.retry_failed', True)
        self._max_retries = self.config.get('test.max_retries', 3)

    async def initialize(self) -> None:
        """Initialize test runner"""
        self._reports_path.mkdir(parents=True, exist_ok=True)

    async def cleanup(self) -> None:
        """Cleanup test runner resources"""
        self._results.clear()
        self._current_run = None

    @handle_errors(logger=None)
    async def run_suite(self,
                       suite_name: str,
                       tests: List[Dict]) -> Dict:
        """Run test suite"""
        self._current_run = {
            'suite': suite_name,
            'start_time': datetime.utcnow().isoformat(),
            'tests': len(tests),
            'passed': 0,
            'failed': 0,
            'skipped': 0
        }
        
        # Group tests by tags for parallel execution
        test_groups = self._group_tests(tests)
        
        # Run test groups
        results = []
        for group in test_groups:
            group_results = await self._run_test_group(group)
            results.extend(group_results)
            
        # Update run statistics
        self._current_run.update({
            'end_time': datetime.utcnow().isoformat(),
            'passed': len([r for r in results if r['status'] == 'passed']),
            'failed': len([r for r in results if r['status'] == 'failed']),
            'skipped': len([r for r in results if r['status'] == 'skipped'])
        })
        
        # Store results
        self._results[suite_name] = results
        
        # Generate report
        await self._generate_report(suite_name, results)
        
        return self._current_run

    def get_results(self,
                   suite_name: Optional[str] = None) -> Union[Dict, List[Dict]]:
        """Get test results"""
        if suite_name:
            return self._results.get(suite_name, [])
        return self._results

    def get_report_path(self, suite_name: str) -> Path:
        """Get test report path"""
        return self._reports_path / f"{suite_name}.json"

    def _group_tests(self, tests: List[Dict]) -> List[List[Dict]]:
        """Group tests for parallel execution"""
        groups: List[List[Dict]] = [[] for _ in range(self._parallel_tests)]
        
        # Group by tags and dependencies
        for test in tests:
            # Find group with least tests and no conflicts
            target_group = min(
                groups,
                key=lambda g: (
                    self._has_conflicts(test, g),
                    len(g)
                )
            )
            target_group.append(test)
            
        return [g for g in groups if g]

    def _has_conflicts(self,
                      test: Dict,
                      group: List[Dict]) -> bool:
        """Check for test conflicts in group"""
        test_tags = set(test.get('tags', []))
        test_deps = set(test.get('depends_on', []))
        
        for other in group:
            other_tags = set(other.get('tags', []))
            # Check for tag conflicts
            if test_tags & other_tags:
                return True
            # Check for dependencies
            if other['name'] in test_deps:
                return True
                
        return False

    async def _run_test_group(self,
                             tests: List[Dict]) -> List[Dict]:
        """Run group of tests"""
        results = []
        for test in tests:
            result = await self._run_test(test)
            results.append(result)
            
            # Handle test failure
            if result['status'] == 'failed' and self._retry_failed:
                retries = 0
                while (retries < self._max_retries and 
                       result['status'] == 'failed'):
                    self.logger.warning(
                        f"Retrying failed test: {test['name']}"
                    )
                    result = await self._run_test(test)
                    retries += 1
                    
        return results

    async def _run_test(self, test: Dict) -> Dict:
        """Run single test"""
        start_time = time.time()
        result = {
            'name': test['name'],
            'tags': test.get('tags', []),
            'start_time': datetime.utcnow().isoformat()
        }
        
        try:
            # Skip if dependencies failed
            if not await self._check_dependencies(test):
                result.update({
                    'status': 'skipped',
                    'reason': 'Failed dependencies'
                })
                return result
                
            # Run test
            framework = self.app.get_component('test_framework')
            if not framework:
                raise Exception("Test framework not available")
                
            await framework.run_tests(
                pattern=test['file'],
                markers=test.get('markers')
            )
            
            result['status'] = 'passed'
            
        except Exception as e:
            result.update({
                'status': 'failed',
                'error': str(e),
                'traceback': self._format_traceback(e)
            })
            
        finally:
            result.update({
                'end_time': datetime.utcnow().isoformat(),
                'duration': time.time() - start_time
            })
            
        return result

    async def _check_dependencies(self, test: Dict) -> bool:
        """Check test dependencies"""
        dependencies = test.get('depends_on', [])
        if not dependencies:
            return True
            
        # Check if all dependencies passed
        for dep in dependencies:
            for suite_results in self._results.values():
                dep_result = next(
                    (r for r in suite_results if r['name'] == dep),
                    None
                )
                if dep_result and dep_result['status'] != 'passed':
                    return False
                    
        return True

    async def _generate_report(self,
                             suite_name: str,
                             results: List[Dict]) -> None:
        """Generate test report"""
        report = {
            'suite': suite_name,
            'timestamp': datetime.utcnow().isoformat(),
            'config': self.config.get('test', {}),
            'summary': self._current_run,
            'results': results
        }
        
        report_path = self.get_report_path(suite_name)
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

    def _format_traceback(self, error: Exception) -> str:
        """Format exception traceback"""
        import traceback
        return ''.join(traceback.format_exception(
            type(error),
            error,
            error.__traceback__
        )) 