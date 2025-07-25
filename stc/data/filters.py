"""Data filtering utilities for ontology-aligned datasets."""

import re
from typing import List, Dict, Any, Callable, Optional
from dataclasses import dataclass

@dataclass
class FilterConfig:
    """Configuration for data filtering."""
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    required_fields: List[str] = None
    forbidden_patterns: List[str] = None
    allowed_patterns: List[str] = None
    min_quality_score: Optional[float] = None
    
    def __post_init__(self):
        if self.required_fields is None:
            self.required_fields = []
        if self.forbidden_patterns is None:
            self.forbidden_patterns = []
        if self.allowed_patterns is None:
            self.allowed_patterns = []

class DataFilter:
    """Filter for data quality and relevance."""
    
    def __init__(self, config: FilterConfig):
        self.config = config
        self.forbidden_regex = [re.compile(pattern) for pattern in config.forbidden_patterns]
        self.allowed_regex = [re.compile(pattern) for pattern in config.allowed_patterns]
    
    def filter_item(self, item: Dict[str, Any]) -> bool:
        """Check if an item passes all filters."""
        try:
            # Check required fields
            if not self._check_required_fields(item):
                return False
            
            # Check length constraints
            if not self._check_length_constraints(item):
                return False
            
            # Check forbidden patterns
            if not self._check_forbidden_patterns(item):
                return False
            
            # Check allowed patterns
            if not self._check_allowed_patterns(item):
                return False
            
            # Check quality score
            if not self._check_quality_score(item):
                return False
            
            return True
        except Exception:
            # If any check fails, reject the item
            return False
    
    def _check_required_fields(self, item: Dict[str, Any]) -> bool:
        """Check if all required fields are present."""
        for field in self.config.required_fields:
            if field not in item or item[field] is None:
                return False
        return True
    
    def _check_length_constraints(self, item: Dict[str, Any]) -> bool:
        """Check text length constraints."""
        text = self._extract_text(item)
        if not text:
            return True  # No text to check
        
        length = len(text)
        
        if self.config.min_length and length < self.config.min_length:
            return False
        
        if self.config.max_length and length > self.config.max_length:
            return False
        
        return True
    
    def _check_forbidden_patterns(self, item: Dict[str, Any]) -> bool:
        """Check if item contains forbidden patterns."""
        text = self._extract_text(item)
        if not text:
            return True
        
        for pattern in self.forbidden_regex:
            if pattern.search(text):
                return False
        
        return True
    
    def _check_allowed_patterns(self, item: Dict[str, Any]) -> bool:
        """Check if item matches allowed patterns."""
        if not self.allowed_regex:
            return True  # No restrictions
        
        text = self._extract_text(item)
        if not text:
            return False
        
        for pattern in self.allowed_regex:
            if pattern.search(text):
                return True
        
        return False
    
    def _check_quality_score(self, item: Dict[str, Any]) -> bool:
        """Check quality score threshold."""
        if self.config.min_quality_score is None:
            return True
        
        score = self._extract_quality_score(item)
        return score >= self.config.min_quality_score
    
    def _extract_text(self, item: Dict[str, Any]) -> str:
        """Extract text content from item."""
        # Common text field names
        text_fields = ['text', 'content', 'message', 'description', 'summary']
        
        for field in text_fields:
            if field in item and item[field]:
                return str(item[field])
        
        # If no text field found, try to extract from any string field
        for value in item.values():
            if isinstance(value, str) and len(value) > 10:
                return value
        
        return ""
    
    def _extract_quality_score(self, item: Dict[str, Any]) -> float:
        """Extract quality score from item."""
        # Common quality score field names
        score_fields = ['quality_score', 'score', 'confidence', 'quality']
        
        for field in score_fields:
            if field in item:
                try:
                    return float(item[field])
                except (ValueError, TypeError):
                    continue
        
        # Default quality score
        return 1.0

def create_ontology_filter(ontology) -> DataFilter:
    """Create a filter based on ontology constraints."""
    config = FilterConfig()
    
    # Extract constraints from ontology
    for constraint in ontology.constraints:
        if "len(" in constraint.expr:
            # Parse length constraints
            match = re.search(r'len\((\w+)\)\s*([<>=]+)\s*(\d+)', constraint.expr)
            if match:
                field, op, value = match.groups()
                value = int(value)
                
                if op == "<=":
                    config.max_length = value
                elif op == ">=":
                    config.min_length = value
                elif op == "<":
                    config.max_length = value - 1
                elif op == ">":
                    config.min_length = value + 1
    
    # Extract required fields from entities
    for entity in ontology.entities.values():
        for field_name, field_spec in entity.fields.items():
            if field_spec.required:
                config.required_fields.append(field_name)
    
    return DataFilter(config)

def filter_dataset(data: List[Dict[str, Any]], filter_func: Callable[[Dict[str, Any]], bool]) -> List[Dict[str, Any]]:
    """Apply a filter function to a dataset."""
    return [item for item in data if filter_func(item)]

def create_custom_filter(**kwargs) -> DataFilter:
    """Create a custom filter with specific parameters."""
    config = FilterConfig(**kwargs)
    return DataFilter(config) 