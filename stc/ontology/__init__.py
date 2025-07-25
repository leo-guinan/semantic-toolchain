"""Ontology processing module."""

from .models import Ontology, EntitySpec, FieldSpec, Constraint, ExamplePair
from .validators import validate_ontology, validate_data_against_ontology

# Import loader only if dependencies are available
try:
    from .loader import load_ontology
    __all__ = [
        "load_ontology",
        "Ontology",
        "EntitySpec", 
        "FieldSpec",
        "Constraint",
        "ExamplePair",
        "validate_ontology",
        "validate_data_against_ontology"
    ]
except ImportError:
    __all__ = [
        "Ontology",
        "EntitySpec", 
        "FieldSpec",
        "Constraint",
        "ExamplePair",
        "validate_ontology",
        "validate_data_against_ontology"
    ] 