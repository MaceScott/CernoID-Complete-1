from typing import Dict, List, Optional, Tuple
import re
from sqlalchemy import text
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class QueryOptimizer:
    """Database query optimization system."""
    
    def __init__(self, session_factory):
        self.session_factory = session_factory
        
    def generate_recommendations(self, plan: Dict) -> List[str]:
        """Generate optimization recommendations."""
        recommendations = []
        
        # Analyze sequential scans
        if self._has_sequential_scan(plan):
            tables = self._extract_tables_from_plan(plan)
            for table, columns in tables.items():
                recommendations.append(
                    f"Consider adding indexes on {table} ({', '.join(columns)}) "
                    "to avoid sequential scan"
                )
            
        # Check for unused indexes
        unused_indexes = self._get_unused_indexes()
        if unused_indexes:
            recommendations.extend([
                f"Remove unused index {idx} to improve write performance"
                for idx in unused_indexes
            ])
            
        # Analyze join operations
        if self._has_nested_loops(plan):
            tables = self._extract_join_tables(plan)
            recommendations.extend([
                f"Consider using HASH JOIN hint for {t1} and {t2}"
                for t1, t2 in tables
            ])
            
        # Check for table statistics
        stale_tables = self._get_stale_statistics()
        if stale_tables:
            recommendations.extend([
                f"Run ANALYZE on {table} to update statistics"
                for table in stale_tables
            ])
            
        return recommendations

    def _extract_tables_from_plan(self, plan: Dict) -> Dict[str, List[str]]:
        """Extract tables and their columns from query plan."""
        tables = {}
        
        def extract_from_node(node: Dict) -> None:
            if 'Relation Name' in node:
                table = node['Relation Name']
                if table not in tables:
                    tables[table] = []
                if 'Filter' in node:
                    columns = self._extract_columns_from_filter(node['Filter'])
                    tables[table].extend(columns)
            for child in node.get('Plans', []):
                extract_from_node(child)
                
        extract_from_node(plan)
        return tables

    def _extract_columns_from_filter(self, filter_expr: str) -> List[str]:
        """Extract column names from filter expression."""
        return re.findall(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*[=<>]', filter_expr)

    def _extract_join_tables(self, plan: Dict) -> List[Tuple[str, str]]:
        """Extract tables involved in nested loop joins."""
        joins = []
        
        def extract_from_node(node: Dict) -> None:
            if node.get('Node Type') == 'Nested Loop':
                outer = self._get_table_from_plan(node.get('Plans', [])[0])
                inner = self._get_table_from_plan(node.get('Plans', [])[1])
                if outer and inner:
                    joins.append((outer, inner))
            for child in node.get('Plans', []):
                extract_from_node(child)
                
        extract_from_node(plan)
        return joins

    def _get_table_from_plan(self, plan: Dict) -> Optional[str]:
        """Get table name from plan node."""
        if 'Relation Name' in plan:
            return plan['Relation Name']
        for child in plan.get('Plans', []):
            table = self._get_table_from_plan(child)
            if table:
                return table
        return None

    async def _get_unused_indexes(self) -> List[str]:
        """Get list of unused indexes."""
        try:
            query = """
                SELECT schemaname || '.' || tablename || '.' || indexname as idx,
                       idx_scan as scans
                FROM pg_stat_user_indexes
                WHERE idx_scan = 0
                  AND schemaname NOT IN ('pg_catalog', 'pg_toast')
                ORDER BY pg_relation_size(indexrelid) DESC;
            """
            async with self.session_factory() as session:
                result = await session.execute(text(query))
                return [row[0] for row in result]
        except Exception as e:
            logger.error(f"Failed to get unused indexes: {str(e)}")
            return []

    async def _get_stale_statistics(self) -> List[str]:
        """Get tables with stale statistics."""
        try:
            query = """
                SELECT schemaname || '.' || tablename
                FROM pg_stat_user_tables
                WHERE (n_mod_since_analyze > 1000 OR n_live_tup > 10000)
                  AND COALESCE(last_analyze, last_autoanalyze) < 
                      NOW() - INTERVAL '1 day';
            """
            async with self.session_factory() as session:
                result = await session.execute(text(query))
                return [row[0] for row in result]
        except Exception as e:
            logger.error(f"Failed to get stale statistics: {str(e)}")
            return []

    @staticmethod
    def _has_sequential_scan(plan: Dict) -> bool:
        """Check for sequential scans in query plan."""
        if 'Node Type' in plan and plan['Node Type'] == 'Seq Scan':
            return True
        for child in plan.get('Plans', []):
            if QueryOptimizer._has_sequential_scan(child):
                return True
        return False

    @staticmethod
    def _has_nested_loops(plan: Dict) -> bool:
        """Check for nested loop joins in query plan."""
        if 'Node Type' in plan and plan['Node Type'] == 'Nested Loop':
            return True
        for child in plan.get('Plans', []):
            if QueryOptimizer._has_nested_loops(child):
                return True
        return False 