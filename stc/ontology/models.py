from pydantic import BaseModel, Field
from typing import Dict, List, Literal, Any, Optional, Union

class FieldSpec(BaseModel):
    type: str
    enum: Optional[List[str]] = None
    range: Optional[tuple[float, float]] = None
    description: Optional[str] = None
    required: bool = True
    default: Optional[Any] = None

class EntitySpec(BaseModel):
    fields: Dict[str, FieldSpec]
    description: Optional[str] = None

class Constraint(BaseModel):
    expr: str   # e.g. "len(summary) <= 300"
    message: Optional[str] = None
    severity: Literal["error", "warning", "info"] = "error"

class ExamplePair(BaseModel):
    input: Dict[str, Any]
    output: Dict[str, Any]
    description: Optional[str] = None

class Ontology(BaseModel):
    name: str
    entities: Dict[str, EntitySpec]
    constraints: List[Constraint] = []
    examples: List[ExamplePair] = []
    description: Optional[str] = None
    version: Optional[str] = None 