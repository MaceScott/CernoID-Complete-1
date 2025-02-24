class FaceMatcher:
    def __init__(self):
        self._encodings_cache = {}
        
    def clear_cache(self):
        """Clear encodings cache when memory usage is high"""
        self._encodings_cache.clear()
        
    def match_face(self, encoding):
        # Use weakref for large objects
        from weakref import WeakValueDictionary
        self._large_objects = WeakValueDictionary() 