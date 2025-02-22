from typing import Dict, Optional, Any, List, Union
import asyncio
from datetime import datetime
import re
from ...base import BaseComponent
from ...utils.errors import SearchError

class MemoryEngine(BaseComponent):
    """In-memory search engine implementation"""
    
    def __init__(self, config: dict, pool: Any):
        super().__init__(config)
        self.name = 'memory'
        self._pool = pool
        self._indices: Dict[str, Dict] = {}
        self._schemas: Dict[str, Dict] = {}
        self._analyzers: Dict[str, Any] = {}
        self._stats = {
            'documents': 0,
            'indices': 0,
            'searches': 0
        }

    async def initialize(self) -> None:
        """Initialize memory engine"""
        # Register default analyzers
        self._analyzers['standard'] = self._standard_analyzer
        self._analyzers['keyword'] = self._keyword_analyzer
        self._analyzers['ngram'] = self._ngram_analyzer

    async def cleanup(self) -> None:
        """Cleanup engine resources"""
        self._indices.clear()
        self._schemas.clear()

    async def create_index(self,
                         name: str,
                         schema: Dict) -> bool:
        """Create search index"""
        try:
            if name in self._indices:
                raise SearchError(f"Index already exists: {name}")
            
            # Validate schema
            self._validate_schema(schema)
            
            # Create index
            self._indices[name] = {}
            self._schemas[name] = schema
            self._stats['indices'] += 1
            
            return True
            
        except Exception as e:
            raise SearchError(f"Index creation failed: {str(e)}")

    async def index(self,
                   index: str,
                   documents: List[Dict]) -> bool:
        """Index documents"""
        try:
            if index not in self._indices:
                raise SearchError(f"Unknown index: {index}")
            
            schema = self._schemas[index]
            
            # Process documents
            for doc in documents:
                # Validate document
                self._validate_document(doc, schema)
                
                # Generate ID if not provided
                doc_id = str(doc.get('id', self._generate_id()))
                
                # Process fields
                processed = self._process_document(doc, schema)
                
                # Store document
                self._indices[index][doc_id] = {
                    'document': doc,
                    'processed': processed,
                    'timestamp': datetime.utcnow()
                }
            
            self._stats['documents'] += len(documents)
            return True
            
        except Exception as e:
            raise SearchError(f"Indexing failed: {str(e)}")

    async def search(self,
                    index: str,
                    query: Union[str, Dict],
                    options: Dict,
                    connection: Optional[Any] = None) -> Dict:
        """Search documents"""
        try:
            if index not in self._indices:
                raise SearchError(f"Unknown index: {index}")
            
            # Parse query
            if isinstance(query, str):
                query = {'query': query}
            
            # Get search options
            limit = options.get('limit', 10)
            offset = options.get('offset', 0)
            sort = options.get('sort', [])
            
            # Execute search
            results = []
            for doc_id, entry in self._indices[index].items():
                if self._matches_query(entry['processed'], query):
                    results.append({
                        'id': doc_id,
                        'score': self._calculate_score(entry, query),
                        'document': entry['document']
                    })
            
            # Sort results
            for field, order in reversed(sort):
                reverse = order.lower() == 'desc'
                results.sort(
                    key=lambda x: x['document'].get(field),
                    reverse=reverse
                )
            
            # Sort by score
            results.sort(key=lambda x: x['score'], reverse=True)
            
            # Apply pagination
            total = len(results)
            results = results[offset:offset + limit]
            
            self._stats['searches'] += 1
            
            return {
                'total': total,
                'hits': results
            }
            
        except Exception as e:
            raise SearchError(f"Search failed: {str(e)}")

    async def update(self,
                    index: str,
                    document_id: str,
                    document: Dict) -> bool:
        """Update document"""
        try:
            if index not in self._indices:
                raise SearchError(f"Unknown index: {index}")
            
            if document_id not in self._indices[index]:
                raise SearchError(f"Document not found: {document_id}")
            
            # Process document
            schema = self._schemas[index]
            self._validate_document(document, schema)
            processed = self._process_document(document, schema)
            
            # Update document
            self._indices[index][document_id] = {
                'document': document,
                'processed': processed,
                'timestamp': datetime.utcnow()
            }
            
            return True
            
        except Exception as e:
            raise SearchError(f"Update failed: {str(e)}")

    async def delete(self,
                    index: str,
                    document_id: str) -> bool:
        """Delete document"""
        try:
            if index not in self._indices:
                raise SearchError(f"Unknown index: {index}")
            
            if document_id in self._indices[index]:
                del self._indices[index][document_id]
                self._stats['documents'] -= 1
                return True
            
            return False
            
        except Exception as e:
            raise SearchError(f"Deletion failed: {str(e)}")

    async def refresh(self) -> None:
        """Refresh indices"""
        pass  # No-op for memory engine

    async def cleanup(self) -> None:
        """Cleanup expired documents"""
        try:
            now = datetime.utcnow()
            ttl = self.config.get('search.ttl')
            
            if not ttl:
                return
                
            for index in self._indices.values():
                expired = [
                    doc_id for doc_id, entry in index.items()
                    if (now - entry['timestamp']).total_seconds() > ttl
                ]
                
                for doc_id in expired:
                    del index[doc_id]
                    self._stats['documents'] -= 1
                    
        except Exception as e:
            self.logger.error(f"Cleanup error: {str(e)}")

    async def get_stats(self) -> Dict[str, Any]:
        """Get engine statistics"""
        return self._stats.copy()

    def _validate_schema(self, schema: Dict) -> None:
        """Validate index schema"""
        if not isinstance(schema, dict):
            raise ValueError("Schema must be a dictionary")
            
        if 'fields' not in schema:
            raise ValueError("Schema must define fields")
            
        for name, field in schema['fields'].items():
            if 'type' not in field:
                raise ValueError(f"Field {name} must define type")

    def _validate_document(self,
                         document: Dict,
                         schema: Dict) -> None:
        """Validate document against schema"""
        for name, field in schema['fields'].items():
            if field.get('required', False):
                if name not in document:
                    raise ValueError(f"Required field missing: {name}")

    def _process_document(self,
                        document: Dict,
                        schema: Dict) -> Dict:
        """Process document fields"""
        processed = {}
        
        for name, field in schema['fields'].items():
            if name in document:
                value = document[name]
                
                # Apply analyzer
                analyzer = self._analyzers.get(
                    field.get('analyzer', 'standard')
                )
                if analyzer:
                    processed[name] = analyzer(value)
                else:
                    processed[name] = value
                    
        return processed

    def _matches_query(self,
                      processed: Dict,
                      query: Dict) -> bool:
        """Check if document matches query"""
        if 'query' in query:
            # Full-text search
            search_text = query['query'].lower()
            return any(
                search_text in str(value).lower()
                for value in processed.values()
            )
        
        # TODO: Implement more complex queries
        return True

    def _calculate_score(self,
                        entry: Dict,
                        query: Dict) -> float:
        """Calculate document score"""
        # Simple TF scoring for now
        if 'query' in query:
            search_text = query['query'].lower()
            score = sum(
                str(value).lower().count(search_text)
                for value in entry['processed'].values()
            )
            return score
        return 1.0

    def _generate_id(self) -> str:
        """Generate unique document ID"""
        import uuid
        return str(uuid.uuid4())

    def _standard_analyzer(self, text: str) -> List[str]:
        """Standard text analyzer"""
        if not isinstance(text, str):
            return []
        return text.lower().split()

    def _keyword_analyzer(self, text: str) -> List[str]:
        """Keyword analyzer"""
        if not isinstance(text, str):
            return []
        return [text.lower()]

    def _ngram_analyzer(self,
                       text: str,
                       min_size: int = 3,
                       max_size: int = 3) -> List[str]:
        """N-gram analyzer"""
        if not isinstance(text, str):
            return []
            
        text = text.lower()
        ngrams = []
        
        for i in range(len(text)):
            for size in range(min_size, max_size + 1):
                if i + size <= len(text):
                    ngrams.append(text[i:i + size])
                    
        return ngrams 