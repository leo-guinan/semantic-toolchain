from pathlib import Path
from typing import Dict, Any
from stc.ontology.models import Ontology
from stc.config import ensure_dir

TYPE_MAP = {
    "string": "string",
    "int": "number",
    "float": "number",
    "bool": "boolean",
    "list[string]": "string[]",
    "list[int]": "number[]",
    "list[float]": "number[]",
    "list[bool]": "boolean[]",
}

def field_to_typescript(field) -> str:
    """Convert a field specification to TypeScript field definition."""
    field_type = TYPE_MAP.get(field.type, "string")
    
    # Handle optional fields
    if not field.required:
        field_type += "?"
    
    return field_type

def emit_ts_interfaces(onto: Ontology, outdir: str) -> None:
    """Emit TypeScript interfaces from ontology."""
    out_path = Path(outdir)
    ensure_dir(out_path)
    
    # Generate the TypeScript file content
    lines = [
        '// Auto-generated TypeScript interfaces from ontology',
        "",
        f"// {onto.name} - {onto.description or 'Generated interfaces'}",
        "",
    ]
    
    # Add version comment if specified
    if onto.version:
        lines.append(f"// Version: {onto.version}")
        lines.append("")
    
    # Generate each entity as a TypeScript interface
    for ent_name, ent in onto.entities.items():
        # Add interface comment
        if ent.description:
            lines.append(f"/** {ent.description} */")
        
        lines.append(f"export interface {ent_name} {{")
        
        # Add fields
        for fname, fspec in ent.fields.items():
            field_type = field_to_typescript(fspec)
            
            # Add field comment if description exists
            if fspec.description:
                lines.append(f"  /** {fspec.description} */")
            
            lines.append(f"  {fname}: {field_type};")
        
        lines.append("}")
        lines.append("")
    
    # Add a union type for all entities
    if len(onto.entities) > 1:
        entity_names = list(onto.entities.keys())
        lines.append(f"export type {onto.name.title()}Entity = " + " | ".join(entity_names) + ";")
        lines.append("")
    
    # Add a root interface that can represent any entity
    if len(onto.entities) > 1:
        lines.append("/** Root interface that can represent any entity type */")
        lines.append(f"export interface {onto.name.title()}Root {{")
        lines.append(f"  type: {onto.name.title()}Entity;")
        lines.append(f"  data: {onto.name.title()}Entity;")
        lines.append("}")
        lines.append("")
    
    # Add utility types
    lines.extend([
        "// Utility types",
        f"export type {onto.name.title()}EntityTypes = keyof typeof {onto.name.title()}Entities;",
        "",
        f"export const {onto.name.title()}Entities = {{",
    ])
    
    for ent_name in onto.entities.keys():
        lines.append(f"  {ent_name}: '{ent_name}',")
    
    lines.extend([
        "} as const;",
        "",
        "// Type guards",
    ])
    
    for ent_name in onto.entities.keys():
        lines.append(f"export function is{ent_name}(obj: any): obj is {ent_name} {{")
        lines.append(f"  return obj && typeof obj === 'object' && 'type' in obj && obj.type === '{ent_name}';")
        lines.append("}")
        lines.append("")
    
    # Add example usage
    lines.extend([
        "// Example usage:",
        f"// import {{ {', '.join(onto.entities.keys())} }} from './{onto.name}_interfaces';",
        "//",
        "// const data: " + list(onto.entities.keys())[0] + " = {",
        "//   // ... field values",
        "// };",
    ])
    
    # Write the file
    interfaces_file = out_path / f"{onto.name}_interfaces.ts"
    with open(interfaces_file, "w") as f:
        f.write("\n".join(lines))
    
    # Also create an index.ts for easy importing
    index_lines = [
        f'// Export all interfaces for {onto.name}',
        "",
    ]
    
    for ent_name in onto.entities.keys():
        index_lines.append(f"export {{ {ent_name} }} from './{onto.name}_interfaces';")
    
    if len(onto.entities) > 1:
        index_lines.extend([
            f"export {{ {onto.name.title()}Entity, {onto.name.title()}Root }} from './{onto.name}_interfaces';",
            f"export {{ {onto.name.title()}EntityTypes, {onto.name.title()}Entities }} from './{onto.name}_interfaces';",
        ])
    
    # Add type guards
    for ent_name in onto.entities.keys():
        index_lines.append(f"export {{ is{ent_name} }} from './{onto.name}_interfaces';")
    
    index_file = out_path / "index.ts"
    with open(index_file, "w") as f:
        f.write("\n".join(index_lines)) 