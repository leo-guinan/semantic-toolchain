from pathlib import Path
from typing import Dict, Any
from stc.ontology.models import Ontology
from stc.config import ensure_dir

TYPE_MAP = {
    "string": "str",
    "int": "int",
    "float": "float",
    "bool": "bool",
    "list[string]": "List[str]",
    "list[int]": "List[int]",
    "list[float]": "List[float]",
    "list[bool]": "List[bool]",
}

def field_to_pydantic(field) -> str:
    """Convert a field specification to Pydantic field definition."""
    field_type = TYPE_MAP.get(field.type, "str")
    
    # Build field definition
    parts = [field_type]
    
    # Add default if specified
    if field.default is not None:
        parts.append(f"default={repr(field.default)}")
    
    # Add Field() with constraints
    field_args = []
    
    if field.description:
        field_args.append(f'description="{field.description}"')
    
    if field.enum:
        field_args.append(f'enum={field.enum}')
    
    if field.range and field.type in ["int", "float"]:
        min_val, max_val = field.range
        field_args.append(f"ge={min_val}")
        field_args.append(f"le={max_val}")
    
    if not field.required:
        field_args.append("default=None")
    
    if field_args:
        parts.append(f"Field({', '.join(field_args)})")
    
    return ": ".join(parts)

def emit_pydantic_models(onto: Ontology, outdir: str) -> None:
    """Emit Pydantic models from ontology."""
    out_path = Path(outdir)
    ensure_dir(out_path)
    
    # Generate the Python file content
    lines = [
        '"""Auto-generated Pydantic models from ontology."""',
        "",
        "from pydantic import BaseModel, Field",
        "from typing import List, Optional, Union",
        "from datetime import datetime",
        "",
        "",
    ]
    
    # Add imports for any custom types
    custom_types = set()
    for entity in onto.entities.values():
        for field in entity.fields.values():
            if field.type not in TYPE_MAP:
                custom_types.add(field.type)
    
    if custom_types:
        lines.append("# Custom type imports")
        for custom_type in sorted(custom_types):
            lines.append(f"# from .{custom_type.lower()} import {custom_type}")
        lines.append("")
    
    # Generate each entity as a Pydantic model
    for ent_name, ent in onto.entities.items():
        # Add class docstring
        if ent.description:
            lines.append(f'class {ent_name}(BaseModel):')
            lines.append(f'    """{ent.description}"""')
        else:
            lines.append(f'class {ent_name}(BaseModel):')
        
        # Add fields
        for fname, fspec in ent.fields.items():
            field_def = field_to_pydantic(fspec)
            lines.append(f"    {fname}: {field_def}")
        
        lines.append("")
    
    # Add a root model that can represent any entity
    if len(onto.entities) > 1:
        lines.append("class RootModel(BaseModel):")
        lines.append('    """Root model that can represent any entity type."""')
        lines.append("    type: str = Field(description='The type of entity')")
        lines.append("    data: Union[" + ", ".join(onto.entities.keys()) + "] = Field(description='The entity data')")
        lines.append("")
    
    # Add example usage
    lines.extend([
        "# Example usage:",
        "# from .models import " + ", ".join(onto.entities.keys()),
        "#",
        "# # Create an instance",
        "# instance = " + list(onto.entities.keys())[0] + "(...)",
        "#",
        "# # Validate data",
        "# validated = " + list(onto.entities.keys())[0] + ".model_validate(data_dict)",
    ])
    
    # Write the file
    models_file = out_path / f"{onto.name}_models.py"
    with open(models_file, "w") as f:
        f.write("\n".join(lines))
    
    # Also create an __init__.py for easy importing
    init_lines = [
        '"""Pydantic models for ' + onto.name + '."""',
        "",
    ]
    
    for ent_name in onto.entities.keys():
        init_lines.append(f"from .{onto.name}_models import {ent_name}")
    
    if len(onto.entities) > 1:
        init_lines.append(f"from .{onto.name}_models import RootModel")
    
    init_lines.extend([
        "",
        "__all__ = [" + ", ".join(f'"{name}"' for name in onto.entities.keys()) + "]",
    ])
    
    init_file = out_path / "__init__.py"
    with open(init_file, "w") as f:
        f.write("\n".join(init_lines)) 