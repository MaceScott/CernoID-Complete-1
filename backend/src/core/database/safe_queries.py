from typing import Any, Dict, List, Optional, Union
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

class DatabaseError(Exception):
    """Raised when database operations fail"""
    pass

async def execute_safe_query(
    session: AsyncSession,
    query: str,
    params: Optional[Dict[str, Any]] = None,
    fetch: bool = True
) -> Union[List[Dict[str, Any]], None]:
    """
    Execute a database query safely with parameter binding.
    
    Args:
        session: Database session
        query: SQL query string
        params: Query parameters
        fetch: Whether to fetch results
        
    Returns:
        List of dictionaries containing query results, or None if fetch=False
        
    Raises:
        DatabaseError: If query execution fails
    """
    try:
        # Use SQLAlchemy's text() for safe parameter binding
        stmt = text(query)
        
        if fetch:
            result = await session.execute(stmt, params or {})
            return [dict(row) for row in result]
        else:
            await session.execute(stmt, params or {})
            await session.commit()
            return None
            
    except SQLAlchemyError as e:
        logger.error(f"Database query error: {str(e)}")
        raise DatabaseError(f"Database operation failed: {str(e)}")

async def execute_safe_many(
    session: AsyncSession,
    query: str,
    params_list: List[Dict[str, Any]]
) -> None:
    """
    Execute multiple database operations safely.
    
    Args:
        session: Database session
        query: SQL query string
        params_list: List of parameter dictionaries
        
    Raises:
        DatabaseError: If any operation fails
    """
    try:
        stmt = text(query)
        
        for params in params_list:
            await session.execute(stmt, params)
            
        await session.commit()
        
    except SQLAlchemyError as e:
        logger.error(f"Database batch operation error: {str(e)}")
        raise DatabaseError(f"Batch operation failed: {str(e)}")

def sanitize_column_name(column: str) -> str:
    """
    Sanitize a column name for SQL queries.
    
    Args:
        column: Column name to sanitize
        
    Returns:
        str: Sanitized column name
    """
    # Remove SQL injection attempts
    column = column.replace(';', '')
    column = column.replace('--', '')
    column = column.replace('/*', '')
    column = column.replace('*/', '')
    
    # Remove whitespace
    column = column.strip()
    
    # Remove special characters
    column = ''.join(c for c in column if c.isalnum() or c == '_')
    
    return column

def build_safe_order_by(
    column: str,
    direction: str = 'asc'
) -> str:
    """
    Build a safe ORDER BY clause.
    
    Args:
        column: Column to order by
        direction: Sort direction ('asc' or 'desc')
        
    Returns:
        str: Safe ORDER BY clause
    """
    # Sanitize column name
    safe_column = sanitize_column_name(column)
    
    # Validate direction
    direction = direction.lower()
    if direction not in ['asc', 'desc']:
        direction = 'asc'
    
    return f"{safe_column} {direction}"

def build_safe_where_clause(
    conditions: Dict[str, Any]
) -> tuple[str, Dict[str, Any]]:
    """
    Build a safe WHERE clause with parameter binding.
    
    Args:
        conditions: Dictionary of column-value pairs
        
    Returns:
        tuple: (WHERE clause string, parameters dictionary)
    """
    where_clauses = []
    params = {}
    
    for i, (column, value) in enumerate(conditions.items()):
        safe_column = sanitize_column_name(column)
        param_name = f"param_{i}"
        
        where_clauses.append(f"{safe_column} = :{param_name}")
        params[param_name] = value
    
    where_clause = " AND ".join(where_clauses)
    return where_clause, params 