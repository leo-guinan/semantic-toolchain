# JSON Schema-based grammar for example
# This is a simpler approach using JSON Schema validation

import json
import jsonschema
from pathlib import Path

# Load the schema
SCHEMA_PATH = Path('example.schema.json')
with open(SCHEMA_PATH) as f:
    SCHEMA = json.load(f)

def validate_json(data_str: str) -> bool:
    """Validate JSON string against the schema."""
    try:
        data = json.loads(data_str)
        jsonschema.validate(data, SCHEMA)
        return True
    except (json.JSONDecodeError, jsonschema.ValidationError):
        return False

def validate_object(data: dict) -> bool:
    """Validate Python dict against the schema."""
    try:
        jsonschema.validate(data, SCHEMA)
        return True
    except jsonschema.ValidationError:
        return False