"""Validators for ontology data structures."""

from typing import Dict, List, Any
from .models import Ontology, EntitySpec, FieldSpec, Constraint

def validate_ontology(ontology: Ontology) -> List[str]:
    """Validate ontology and return list of errors."""
    errors = []
    
    # Check for duplicate entity names
    entity_names = list(ontology.entities.keys())
    if len(entity_names) != len(set(entity_names)):
        errors.append("Duplicate entity names found")
    
    # Validate each entity
    for entity_name, entity in ontology.entities.items():
        entity_errors = validate_entity(entity_name, entity)
        errors.extend(entity_errors)
    
    # Validate constraints
    for i, constraint in enumerate(ontology.constraints):
        if not constraint.expr.strip():
            errors.append(f"Constraint {i}: Empty expression")
    
    return errors

def validate_entity(name: str, entity: EntitySpec) -> List[str]:
    """Validate a single entity."""
    errors = []
    
    # Check for duplicate field names
    field_names = list(entity.fields.keys())
    if len(field_names) != len(set(field_names)):
        errors.append(f"Entity '{name}': Duplicate field names")
    
    # Validate each field
    for field_name, field in entity.fields.items():
        field_errors = validate_field(field_name, field)
        errors.extend([f"Entity '{name}'.{error}" for error in field_errors])
    
    return errors

def validate_field(name: str, field: FieldSpec) -> List[str]:
    """Validate a single field."""
    errors = []
    
    # Validate type
    if not field.type:
        errors.append(f"Field '{name}': Missing type")
    
    # Validate enum values
    if field.enum is not None:
        if not isinstance(field.enum, list):
            errors.append(f"Field '{name}': Enum must be a list")
        elif len(field.enum) == 0:
            errors.append(f"Field '{name}': Enum cannot be empty")
    
    # Validate range
    if field.range is not None:
        if not isinstance(field.range, tuple) or len(field.range) != 2:
            errors.append(f"Field '{name}': Range must be a tuple of (min, max)")
        elif field.range[0] >= field.range[1]:
            errors.append(f"Field '{name}': Range min must be less than max")
    
    return errors

def validate_data_against_ontology(data: Dict[str, Any], ontology: Ontology) -> List[str]:
    """Validate data against ontology constraints."""
    errors = []
    
    # Check if data matches any entity
    for entity_name, entity in ontology.entities.items():
        entity_errors = validate_data_against_entity(data, entity_name, entity)
        if not entity_errors:
            # Data matches this entity, no need to check others
            break
        errors.extend(entity_errors)
    else:
        # Data doesn't match any entity
        errors.append("Data doesn't match any defined entity")
    
    # Check constraints
    for constraint in ontology.constraints:
        try:
            # Simple constraint evaluation (in practice, you'd use a proper expression evaluator)
            if not evaluate_constraint(data, constraint.expr):
                errors.append(f"Constraint failed: {constraint.expr}")
        except Exception as e:
            errors.append(f"Constraint evaluation error: {e}")
    
    return errors

def validate_data_against_entity(data: Dict[str, Any], entity_name: str, entity: EntitySpec) -> List[str]:
    """Validate data against a specific entity."""
    errors = []
    
    # Check required fields
    for field_name, field in entity.fields.items():
        if field.required and field_name not in data:
            errors.append(f"Missing required field: {field_name}")
    
    # Check field types and constraints
    for field_name, field_value in data.items():
        if field_name not in entity.fields:
            errors.append(f"Unknown field: {field_name}")
            continue
        
        field_spec = entity.fields[field_name]
        field_errors = validate_field_value(field_name, field_value, field_spec)
        errors.extend(field_errors)
    
    return errors

def validate_field_value(name: str, value: Any, field: FieldSpec) -> List[str]:
    """Validate a field value against its specification."""
    errors = []
    
    # Type validation
    if field.type == "string" and not isinstance(value, str):
        errors.append(f"Field '{name}': Expected string, got {type(value).__name__}")
    elif field.type == "int" and not isinstance(value, int):
        errors.append(f"Field '{name}': Expected int, got {type(value).__name__}")
    elif field.type == "float" and not isinstance(value, (int, float)):
        errors.append(f"Field '{name}': Expected number, got {type(value).__name__}")
    elif field.type == "bool" and not isinstance(value, bool):
        errors.append(f"Field '{name}': Expected bool, got {type(value).__name__}")
    
    # Enum validation
    if field.enum is not None and value not in field.enum:
        errors.append(f"Field '{name}': Value '{value}' not in enum {field.enum}")
    
    # Range validation
    if field.range is not None:
        min_val, max_val = field.range
        if value < min_val or value > max_val:
            errors.append(f"Field '{name}': Value {value} not in range [{min_val}, {max_val}]")
    
    return errors

def evaluate_constraint(data: Dict[str, Any], expr: str) -> bool:
    """Evaluate a constraint expression against data."""
    # This is a simplified implementation
    # In practice, you'd use a proper expression evaluator like `asteval` or `eval` with restricted globals
    
    # Simple length constraint evaluation
    if "len(" in expr and ")" in expr:
        field_name = expr.split("len(")[1].split(")")[0]
        if field_name in data:
            field_value = data[field_name]
            if isinstance(field_value, str):
                length = len(field_value)
                # Extract comparison from expression
                if "<=" in expr:
                    max_len = int(expr.split("<=")[1].strip())
                    return length <= max_len
                elif ">=" in expr:
                    min_len = int(expr.split(">=")[1].strip())
                    return length >= min_len
    
    # Default to True for unknown expressions
    return True 