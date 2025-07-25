from pathlib import Path
from typing import Dict, Any, List
from stc.ontology.models import Ontology
from stc.config import ensure_dir

def emit_peg_grammar(onto: Ontology, outdir: str) -> None:
    """
    Produce a PEG grammar that enforces JSON output matching definitions.
    """
    out_path = Path(outdir)
    ensure_dir(out_path)
    
    # Build the grammar content
    lines = [
        f"# PEG grammar for {onto.name} JSON validation",
        f"# Generated from ontology",
        "",
        "# Basic JSON structure",
        "start <- object",
        "object <- '{' (pair (',' pair)*)? '}'",
        "pair <- string ':' value",
        "value <- string / number / object / array / boolean / null",
        "array <- '[' (value (',' value)*)? ']'",
        "string <- '\"' (!'\"' .)* '\"'",
        "number <- '-'? [0-9]+ ('.' [0-9]+)?",
        "boolean <- 'true' / 'false'",
        "null <- 'null'",
        "",
        "# Entity-specific rules",
    ]
    
    # Add entity-specific rules
    for ent_name, ent in onto.entities.items():
        lines.append(f"# {ent_name} entity")
        lines.append(f"{ent_name.lower()}_object <- '{{'")
        
        # Build required field pairs
        required_fields = [fname for fname, fspec in ent.fields.items() if fspec.required]
        optional_fields = [fname for fname, fspec in ent.fields.items() if not fspec.required]
        
        if required_fields:
            lines.append(f"  {ent_name.lower()}_required_fields")
        
        if optional_fields:
            lines.append(f"  (',' {ent_name.lower()}_optional_fields)*")
        
        lines.append(f"  '}}'")
        lines.append("")
        
        # Required fields rule
        if required_fields:
            lines.append(f"{ent_name.lower()}_required_fields <- {ent_name.lower()}_{required_fields[0]}_pair")
            for field in required_fields[1:]:
                lines.append(f"  (',' {ent_name.lower()}_{field}_pair)*")
            lines.append("")
        
        # Optional fields rule
        if optional_fields:
            lines.append(f"{ent_name.lower()}_optional_fields <- {ent_name.lower()}_{optional_fields[0]}_pair")
            for field in optional_fields[1:]:
                lines.append(f"  / {ent_name.lower()}_{field}_pair")
            lines.append("")
        
        # Field-specific rules
        for fname, fspec in ent.fields.items():
            lines.append(f"# {fname} field")
            lines.append(f"{ent_name.lower()}_{fname}_pair <- '\"{fname}\"' ':' {ent_name.lower()}_{fname}_value")
            
            # Value validation based on field type
            if fspec.enum:
                enum_values = " / ".join(f"'{val}'" for val in fspec.enum)
                lines.append(f"{ent_name.lower()}_{fname}_value <- {enum_values}")
            elif fspec.type == "string":
                if fspec.range:
                    min_len, max_len = fspec.range
                    lines.append(f"{ent_name.lower()}_{fname}_value <- string_{min_len}_{max_len}")
                else:
                    lines.append(f"{ent_name.lower()}_{fname}_value <- string")
            elif fspec.type == "int":
                if fspec.range:
                    min_val, max_val = fspec.range
                    lines.append(f"{ent_name.lower()}_{fname}_value <- number_{min_val}_{max_val}")
                else:
                    lines.append(f"{ent_name.lower()}_{fname}_value <- number")
            elif fspec.type == "float":
                if fspec.range:
                    min_val, max_val = fspec.range
                    lines.append(f"{ent_name.lower()}_{fname}_value <- number_{min_val}_{max_val}")
                else:
                    lines.append(f"{ent_name.lower()}_{fname}_value <- number")
            elif fspec.type == "bool":
                lines.append(f"{ent_name.lower()}_{fname}_value <- boolean")
            elif fspec.type.startswith("list["):
                lines.append(f"{ent_name.lower()}_{fname}_value <- array")
            else:
                lines.append(f"{ent_name.lower()}_{fname}_value <- value")
            
            lines.append("")
    
    # Add constraint-based rules
    if onto.constraints:
        lines.append("# Constraint-based validation rules")
        for i, constraint in enumerate(onto.constraints):
            lines.append(f"# Constraint {i+1}: {constraint.expr}")
            # This would need more sophisticated parsing of constraint expressions
            lines.append(f"# TODO: Implement constraint validation for: {constraint.expr}")
        lines.append("")
    
    # Add length-constrained string rules
    lines.append("# Length-constrained strings")
    for ent_name, ent in onto.entities.items():
        for fname, fspec in ent.fields.items():
            if fspec.type == "string" and fspec.range:
                min_len, max_len = fspec.range
                lines.append(f"string_{min_len}_{max_len} <- '\"' string_content_{min_len}_{max_len} '\"'")
                lines.append(f"string_content_{min_len}_{max_len} <- (!'\"' .){{{min_len},{max_len}}}")
    
    # Add range-constrained number rules
    lines.append("# Range-constrained numbers")
    for ent_name, ent in onto.entities.items():
        for fname, fspec in ent.fields.items():
            if fspec.type in ["int", "float"] and fspec.range:
                min_val, max_val = fspec.range
                lines.append(f"number_{min_val}_{max_val} <- number")
                lines.append(f"# TODO: Add range validation for {min_val} <= number <= {max_val}")
    
    # Write the grammar file
    grammar_file = out_path / f"{onto.name}.peg"
    with open(grammar_file, "w") as f:
        f.write("\n".join(lines))
    
    # Also create a JSON Schema-based grammar (simpler alternative)
    lines_json = [
        f"# JSON Schema-based grammar for {onto.name}",
        f"# This is a simpler approach using JSON Schema validation",
        "",
        "import json",
        "import jsonschema",
        "from pathlib import Path",
        "",
        f"# Load the schema",
        f"SCHEMA_PATH = Path('{onto.name}.schema.json')",
        "with open(SCHEMA_PATH) as f:",
        "    SCHEMA = json.load(f)",
        "",
        "def validate_json(data_str: str) -> bool:",
        '    """Validate JSON string against the schema."""',
        "    try:",
        "        data = json.loads(data_str)",
        "        jsonschema.validate(data, SCHEMA)",
        "        return True",
        "    except (json.JSONDecodeError, jsonschema.ValidationError):",
        "        return False",
        "",
        "def validate_object(data: dict) -> bool:",
        '    """Validate Python dict against the schema."""',
        "    try:",
        "        jsonschema.validate(data, SCHEMA)",
        "        return True",
        "    except jsonschema.ValidationError:",
        "        return False",
    ]
    
    json_grammar_file = out_path / f"{onto.name}_validator.py"
    with open(json_grammar_file, "w") as f:
        f.write("\n".join(lines_json)) 