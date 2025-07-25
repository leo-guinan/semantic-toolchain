from ruamel.yaml import YAML
from pathlib import Path
import json
from typing import Union
from .models import Ontology, FieldSpec, EntitySpec, Constraint, ExamplePair

yaml = YAML(typ="safe")

def load_ontology(path: Union[str, Path]) -> Ontology:
    """Load ontology from YAML or JSON file."""
    path = Path(path)
    
    if not path.exists():
        raise FileNotFoundError(f"Ontology file not found: {path}")
    
    if path.suffix.lower() in ['.yaml', '.yml']:
        data = yaml.load(path.read_text())
    elif path.suffix.lower() == '.json':
        data = json.loads(path.read_text())
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")
    
    # Convert raw dict to Ontology object
    entities = {}
    for name, spec in data.get("entities", {}).items():
        fields = {}
        for fname, fdef in spec.get("fields", {}).items():
            if isinstance(fdef, dict):
                fields[fname] = FieldSpec(**fdef)
            else:
                # Handle simple string type definitions
                fields[fname] = FieldSpec(type=str(fdef))
        
        entities[name] = EntitySpec(
            fields=fields,
            description=spec.get("description")
        )
    
    constraints = [Constraint(**c) for c in data.get("constraints", [])]
    examples = [ExamplePair(**e) for e in data.get("examples", [])]
    
    return Ontology(
        name=data.get("name", path.stem),
        entities=entities,
        constraints=constraints,
        examples=examples,
        description=data.get("description"),
        version=data.get("version")
    ) 