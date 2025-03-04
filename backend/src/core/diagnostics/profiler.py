from typing import Optional, Dict, List, Callable, Any
import cProfile
import pstats
import tracemalloc
import asyncio
import time
from pathlib import Path
from ..base import BaseComponent
from ..utils.errors import handle_errors

class Profiler(BaseComponent):
    """Application profiling and diagnostics"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._profile_path = Path(
            self.config.get('profiler.path', 'profiles')
        )
        self._enabled = self.config.get('profiler.enabled', False)
        self._tracemalloc_enabled = self.config.get(
            'profiler.tracemalloc',
            False
        )
        self._profiler: Optional[cProfile.Profile] = None
        self._memory_snapshots: Dict[str, tracemalloc.Snapshot] = {}

    async def initialize(self) -> None:
        """Initialize profiler"""
        self._profile_path.mkdir(parents=True, exist_ok=True)
        
        if self._tracemalloc_enabled:
            tracemalloc.start()

    async def cleanup(self) -> None:
        """Cleanup profiler resources"""
        if self._profiler:
            self._profiler.disable()
            
        if self._tracemalloc_enabled:
            tracemalloc.stop()
            
        self._memory_snapshots.clear()

    def start_profiling(self) -> None:
        """Start CPU profiling"""
        if not self._enabled:
            return
            
        self._profiler = cProfile.Profile()
        self._profiler.enable()

    def stop_profiling(self, save: bool = True) -> Optional[pstats.Stats]:
        """Stop CPU profiling"""
        if not self._profiler:
            return None
            
        self._profiler.disable()
        stats = pstats.Stats(self._profiler)
        
        if save:
            # Save profile results
            timestamp = int(time.time())
            stats.dump_stats(
                self._profile_path / f"profile_{timestamp}.prof"
            )
            
        self._profiler = None
        return stats

    def take_memory_snapshot(self, name: str) -> None:
        """Take memory usage snapshot"""
        if not self._tracemalloc_enabled:
            return
            
        self._memory_snapshots[name] = tracemalloc.take_snapshot()

    def compare_memory_snapshots(self,
                               start: str,
                               end: str) -> List[Dict]:
        """Compare memory snapshots"""
        if not self._tracemalloc_enabled:
            return []
            
        if start not in self._memory_snapshots or \
           end not in self._memory_snapshots:
            raise ValueError("Snapshot not found")
            
        start_snapshot = self._memory_snapshots[start]
        end_snapshot = self._memory_snapshots[end]
        
        # Compare snapshots
        stats = end_snapshot.compare_to(start_snapshot, 'lineno')
        
        return [
            {
                'file': str(stat.traceback[0].filename),
                'line': stat.traceback[0].lineno,
                'size_diff': stat.size_diff,
                'count_diff': stat.count_diff
            }
            for stat in stats
        ]

    async def profile_function(self,
                             func: Callable,
                             *args,
                             **kwargs) -> Any:
        """Profile specific function"""
        if not self._enabled:
            return await func(*args, **kwargs)
            
        self.start_profiling()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            stats = self.stop_profiling()
            if stats:
                stats.sort_stats('cumulative')
                stats.print_stats(30)  # Show top 30 functions

    def get_memory_stats(self) -> Dict:
        """Get current memory statistics"""
        if not self._tracemalloc_enabled:
            return {}
            
        snapshot = tracemalloc.take_snapshot()
        stats = snapshot.statistics('lineno')
        
        return {
            'current': tracemalloc.get_traced_memory()[0],
            'peak': tracemalloc.get_traced_memory()[1],
            'top_allocations': [
                {
                    'file': str(stat.traceback[0].filename),
                    'line': stat.traceback[0].lineno,
                    'size': stat.size,
                    'count': stat.count
                }
                for stat in stats[:10]  # Top 10 allocations
            ]
        }

    def clear_snapshots(self) -> None:
        """Clear memory snapshots"""
        self._memory_snapshots.clear()

    def get_profile_files(self) -> List[str]:
        """Get list of profile files"""
        return [
            str(f.name) for f in self._profile_path.glob('*.prof')
        ]

    async def analyze_profile(self, filename: str) -> Dict:
        """Analyze profile file"""
        profile_file = self._profile_path / filename
        if not profile_file.exists():
            raise ValueError(f"Profile file not found: {filename}")
            
        stats = pstats.Stats(str(profile_file))
        
        # Get top functions by cumulative time
        stats.sort_stats('cumulative')
        top_stats = []
        for func in stats.stats.items():
            cc, nc, tt, ct, callers = func[1]
            top_stats.append({
                'function': f"{func[0][0]}:{func[0][1]}({func[0][2]})",
                'calls': cc,
                'cumtime': ct,
                'percall': ct/cc if cc > 0 else 0
            })
            if len(top_stats) >= 30:
                break
                
        return {
            'filename': filename,
            'total_calls': stats.total_calls,
            'total_time': stats.total_tt,
            'top_functions': top_stats
        } 