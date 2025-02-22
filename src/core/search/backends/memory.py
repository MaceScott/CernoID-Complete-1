from typing import Dict, Optional, Any, List
import asyncio
from datetime import datetime
import re
from ...base import BaseComponent

class MemoryBackend(BaseComponent):
    """In-memory search backend"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._indexes: Dict[str, Dict] = {}
        self._documents: Dict[str, Dict] = {}
        self._stats = {
            'indexes': 0,
            'documents': 0
        }

    async def initialize(self) -> None:
        """Initialize memory backend"""
        pass

    async def cleanup(self) -> None:
        """Cleanup backend resources"""
        self._indexes.clear()
        self._documents.clear()

    async def create_index(self,
                         name: str,
                         mapping: Optional[Dict] = None,
                         settings: Optional[Dict] = None) -> bool:
        """Create search index"""
        try:
            self._indexes[name] = {
                'name': name,
                'mapping': mapping or {},
                'settings': settings or {},
                'created': datetime.utcnow()
            }
            
            self._documents[name] = {}
            self._stats['indexes'] += 1
            return True
            
        except Exception as e:
            self.logger.error(f"Memory index creation error: {str(e)}")
            return False

    async def delete_index(self, name: str) -> bool:
        """Delete search index"""
        try:
            if name in self._indexes:
                del self._indexes[name]
                del self._documents[name]
                self._stats['indexes'] -= 1
            return True
            
        except Exception as e:
            self.logger.error(f"Memory index deletion error: {str(e)}")
            return False

    async def index(self,
                   index: str,
                   documents: List[Dict],
                   refresh: bool = True) -> bool:
        """Index documents"""
        try:
            if index not in self._indexes:
                return False
                
            for doc in documents:
                doc_id = str(doc.get('id', doc.get('_id')))
                if not doc_id:
                    continue
                    
                self._documents[index][doc_id] = {
                    **doc,
                    '_indexed': datetime.utcnow()
                }
                
            self._stats['documents'] = sum(
                len(docs) for docs in self._documents.values()
            )
            return True
            
        except Exception as e:
            self.logger.error(f"Memory indexing error: {str(e)}")
            return False

    async def search(self,
                    index: str,
                    query: Dict,
                    offset: int = 0,
                    limit: int = 10,
                    sort: Optional[List] = None,
                    fields: Optional[List] = None,
                    filters: Optional[Dict] = None,
                    aggregations: Optional[Dict] = None,
                    **kwargs) -> Dict:
        """Search documents"""
        try:
            if index not in self._indexes:
                return {
                    'total': 0,
                    'hits': [],
                    'aggregations': {}
                }
                
            # Get all documents
            docs = list(self._documents[index].values())
            
            # Apply filters
            if filters:
                docs = self._apply_filters(docs, filters)
                
            # Apply query
            if query:
                docs = self._apply_query(docs, query)
                
            # Sort results
            if sort:
                docs = self._sort_documents(docs, sort)
                
            # Get total
            total = len(docs)
            
            # Apply pagination
            docs = docs[offset:offset + limit]
            
            # Select fields
            if fields:
                docs = [
                    {k: d[k] for k in fields if k in d}
                    for d in docs
                ]
                
            # Calculate aggregations
            aggs = {}
            if aggregations:
                aggs = self._calculate_aggregations(
                    docs,
                    aggregations
                )
                
            return {
                'total': total,
                'hits': docs,
                'aggregations': aggs
            }
            
        except Exception as e:
            self.logger.error(f"Memory search error: {str(e)}")
            return {
                'total': 0,
                'hits': [],
                'aggregations': {}
            }

    async def delete(self,
                    index: str,
                    ids: List[str],
                    refresh: bool = True) -> bool:
        """Delete documents"""
        try:
            if index not in self._indexes:
                return False
                
            for doc_id in ids:
                self._documents[index].pop(str(doc_id), None)
                
            self._stats['documents'] = sum(
                len(docs) for docs in self._documents.values()
            )
            return True
            
        except Exception as e:
            self.logger.error(f"Memory deletion error: {str(e)}")
            return False

    async def get_stats(self) -> Dict[str, Any]:
        """Get backend statistics"""
        return self._stats.copy()

    def _apply_filters(self,
                      docs: List[Dict],
                      filters: Dict) -> List[Dict]:
        """Apply filters to documents"""
        filtered = docs[:]
        
        for field, value in filters.items():
            filtered = [
                d for d in filtered
                if field in d and d[field] == value
            ]
            
        return filtered

    def _apply_query(self,
                    docs: List[Dict],
                    query: Dict) -> List[Dict]:
        """Apply query to documents"""
        if 'query_string' in query:
            return self._apply_query_string(
                docs,
                query['query_string']['query']
            )
            
        return docs

    def _apply_query_string(self,
                          docs: List[Dict],
                          query: str) -> List[Dict]:
        """Apply query string search"""
        pattern = re.compile(query, re.IGNORECASE)
        
        matches = []
        for doc in docs:
            text = ' '.join(str(v) for v in doc.values())
            if pattern.search(text):
                matches.append(doc)
                
        return matches

    def _sort_documents(self,
                       docs: List[Dict],
                       sort: List) -> List[Dict]:
        """Sort documents"""
        for field in reversed(sort):
            reverse = False
            if field.startswith('-'):
                field = field[1:]
                reverse = True
                
            docs.sort(
                key=lambda x: x.get(field, ''),
                reverse=reverse
            )
            
        return docs

    def _calculate_aggregations(self,
                              docs: List[Dict],
                              aggregations: Dict) -> Dict:
        """Calculate aggregations"""
        results = {}
        
        for name, agg in aggregations.items():
            if agg['type'] == 'terms':
                field = agg['field']
                results[name] = {}
                
                for doc in docs:
                    value = doc.get(field)
                    if value:
                        if value not in results[name]:
                            results[name][value] = 0
                        results[name][value] += 1
                        
        return results 