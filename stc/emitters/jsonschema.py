import json
from pathlib import Path
from typing import Dict, Any
from stc.ontology.models import Ontology
from stc.config import ensure_dir

TYPE_MAP = {
    "string": "string",
    "int": "integer",
    "float": "number",
    "bool": "boolean",
    "list[string]": {"type": "array", "items": {"type": "string"}},
    "list[int]": {"type": "array", "items": {"type": "integer"}},
    "list[float]": {"type": "array", "items": {"type": "number"}},
    "list[bool]": {"type": "array", "items": {"type": "boolean"}},
    # Extend as needed...
}

def field_to_schema(field) -> Dict[str, Any]:
    """Convert a field specification to JSON Schema."""
    schema = {}
    
    # Handle enum fields
    if field.enum:
        schema["type"] = "string"
        schema["enum"] = field.enum
        return schema
    
    # Handle basic types
    base_type = TYPE_MAP.get(field.type, "string")
    if isinstance(base_type, dict):
        schema.update(base_type)
    else:
        schema["type"] = base_type
    
    # Add range constraints for numbers
    if field.range and field.type in ["int", "float"]:
        min_val, max_val = field.range
        schema["minimum"] = min_val
        schema["maximum"] = max_val
    
    # Add description if available
    if field.description:
        schema["description"] = field.description
    
    return schema

def emit_jsonschema(onto: Ontology, outdir: str) -> None:
    """Emit JSON Schema from ontology."""
    out_path = Path(outdir)
    ensure_dir(out_path)
    
    # Build definitions for each entity
    definitions = {}
    for ent_name, ent in onto.entities.items():
        properties = {}
        required = []
        
        for fname, fspec in ent.fields.items():
            properties[fname] = field_to_schema(fspec)
            if fspec.required:
                required.append(fname)
        
        definitions[ent_name] = {
            "type": "object",
            "properties": properties,
            "additionalProperties": False
        }
        
        if required:
            definitions[ent_name]["required"] = required
        
        if ent.description:
            definitions[ent_name]["description"] = ent.description
    
    # Build the full schema
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "$id": f"https://example.com/schemas/{onto.name}.json",
        "title": onto.name.title(),
        "description": onto.description or f"Schema for {onto.name}",
        "definitions": definitions,
        "oneOf": [
            {"$ref": f"#/definitions/{ent_name}"} 
            for ent_name in onto.entities.keys()
        ]
    }
    
    # Add version if specified
    if onto.version:
        schema["version"] = onto.version
    
    # Write the schema file
    schema_file = out_path / f"{onto.name}.schema.json"
    with open(schema_file, "w") as f:
        json.dump(schema, f, indent=2)
    
    # Also create a root schema that references all entities
    root_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "$id": f"https://example.com/schemas/{onto.name}-root.json",
        "title": f"{onto.name.title()} Root Schema",
        "description": f"Root schema for {onto.name} with all entity definitions",
        "definitions": definitions,
        "type": "object",
        "properties": {
            "type": {
                "type": "string",
                "enum": list(onto.entities.keys()),
                "description": "The type of entity"
            },
            "data": {
                "oneOf": [
                    {"$ref": f"#/definitions/{ent_name}"} 
                    for ent_name in onto.entities.keys()
                ]
            }
        },
        "required": ["type", "data"]
    }
    
    root_file = out_path / f"{onto.name}-root.schema.json"
    with open(root_file, "w") as f:
        json.dump(root_schema, f, indent=2) 