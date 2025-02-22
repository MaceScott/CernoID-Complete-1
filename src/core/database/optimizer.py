from typing import Dict, List, Optional
import time
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from dataclasses import dataclass

@dataclass
class QueryStats:
    """Query performance statistics"""
    query_hash: str
    execution_time: float
    rows_affected: int
    timestamp: float
    query_plan: Dict

class QueryOptimizer:
    """Database query optimization and monitoring"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.logger = logging.getLogger('QueryOptimizer')
        self._query_stats: Dict[str, List[QueryStats]] = {}
        self._slow_query_threshold = 1.0  # seconds
        
    async def analyze_query(self, query: str) -> Dict:
        """Analyze query execution plan"""
        try:
            explain_query = f"EXPLAIN (FORMAT JSON, ANALYZE, BUFFERS) {query}"
            result = await self.session.execute(text(explain_query))
            plan = result.scalar()
            
            return {
                'plan': plan,
                'recommendations': self._generate_recommendations(plan)
            }
        except Exception as e:
            self.logger.error(f"Query analysis failed: {str(e)}")
            raise

    async def optimize_query(self, query: str) -> str:
        """Optimize query based on analysis"""
        try:
            analysis = await self.analyze_query(query)
            optimized_query = self._apply_optimizations(query, analysis)
            
            # Verify optimization improved performance
            original_stats = await self._measure_query(query)
            optimized_stats = await self._measure_query(optimized_query)
            
            if optimized_stats.execution_time < original_stats.execution_time:
                return optimized_query
            return query
            
        except Exception as e:
            self.logger.error(f"Query optimization failed: {str(e)}")
            raise

    async def create_indexes(self, table_name: str) -> List[str]:
        """Create recommended indexes"""
        try:
            # Analyze table usage patterns
            query = f"""
                SELECT schemaname, tablename, attname, n_distinct, correlation
                FROM pg_stats
                WHERE tablename = :table_name
            """
            result = await self.session.execute(
                text(query),
                {'table_name': table_name}
            )
            stats = result.fetchall()
            
            # Generate index recommendations
            recommendations = self._recommend_indexes(stats)
            created_indexes = []
            
            # Create recommended indexes
            for index_sql in recommendations:
                await self.session.execute(text(index_sql))
                created_indexes.append(index_sql)
                
            await self.session.commit()
            return created_indexes
            
        except Exception as e:
            self.logger.error(f"Index creation failed: {str(e)}")
            raise

    def _generate_recommendations(self, plan: Dict) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []
        
        # Analyze sequential scans
        if self._has_sequential_scan(plan):
            recommendations.append("Consider adding an index to avoid sequential scan")
            
        # Check for unused indexes
        if self._has_unused_indexes(plan):
            recommendations.append("Remove unused indexes to improve write performance")
            
        # Analyze join operations
        if self._has_nested_loops(plan):
            recommendations.append("Consider using JOIN hints to improve join performance")
            
        return recommendations

    async def _measure_query(self, query: str) -> QueryStats:
        """Measure query performance"""
        start_time = time.time()
        result = await self.session.execute(text(query))
        execution_time = time.time() - start_time
        
        return QueryStats(
            query_hash=hash(query),
            execution_time=execution_time,
            rows_affected=result.rowcount,
            timestamp=start_time,
            query_plan=await self.analyze_query(query)
        )

    def _recommend_indexes(self, stats: List) -> List[str]:
        """Generate index recommendations"""
        recommendations = []
        
        for stat in stats:
            if stat.n_distinct > 100 and abs(stat.correlation) < 0.5:
                recommendations.append(
                    f"CREATE INDEX ON {stat.tablename} ({stat.attname})"
                )
                
        return recommendations

    @staticmethod
    def _has_sequential_scan(plan: Dict) -> bool:
        """Check for sequential scans in query plan"""
        if 'Node Type' in plan and plan['Node Type'] == 'Seq Scan':
            return True
        for child in plan.get('Plans', []):
            if QueryOptimizer._has_sequential_scan(child):
                return True
        return False

    @staticmethod
    def _has_nested_loops(plan: Dict) -> bool:
        """Check for nested loop joins in query plan"""
        if 'Node Type' in plan and plan['Node Type'] == 'Nested Loop':
            return True
        for child in plan.get('Plans', []):
            if QueryOptimizer._has_nested_loops(child):
                return True
        return False 