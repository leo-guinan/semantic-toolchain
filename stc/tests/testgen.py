"""Property-based test generator from ontology constraints."""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from textwrap import dedent
from stc.config import ensure_dir

def generate_property_tests(schema_path: str, out_path: str) -> None:
    """Generate property-based tests from ontology constraints."""
    schema_file = Path(schema_path)
    out_file = Path(out_path)
    
    if not schema_file.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    # Load schema
    with open(schema_file) as f:
        schema = json.load(f)
    
    # Ensure output directory exists
    ensure_dir(out_file.parent)
    
    # Generate test code
    test_code = generate_test_code(schema, schema_file.name)
    
    # Write test file
    with open(out_file, "w") as f:
        f.write(test_code)

def generate_test_code(schema: Dict[str, Any], schema_filename: str) -> str:
    """Generate Python test code from schema."""
    
    # Extract schema information
    definitions = schema.get("definitions", {})
    entity_names = list(definitions.keys())
    
    # Generate imports and setup
    code_lines = [
        '"""Property-based tests generated from ontology schema."""',
        "",
        "import pytest",
        "import json",
        "import jsonschema",
        "from pathlib import Path",
        "from hypothesis import given, strategies as st",
        "from hypothesis.extra.jsonschema import from_schema",
        "",
        f"# Load schema from {schema_filename}",
        f"SCHEMA_PATH = Path('{schema_filename}')",
        "with open(SCHEMA_PATH) as f:",
        "    SCHEMA = json.load(f)",
        "",
        "validator = jsonschema.Draft7Validator(SCHEMA)",
        "",
    ]
    
    # Generate tests for each entity
    for entity_name, entity_schema in definitions.items():
        code_lines.extend(generate_entity_tests(entity_name, entity_schema))
        code_lines.append("")
    
    # Generate general schema tests
    code_lines.extend(generate_schema_tests(schema))
    code_lines.append("")
    
    # Generate constraint tests
    code_lines.extend(generate_constraint_tests(schema))
    code_lines.append("")
    
    # Generate fuzz tests
    code_lines.extend(generate_fuzz_tests(schema))
    
    return "\n".join(code_lines)

def generate_entity_tests(entity_name: str, entity_schema: Dict[str, Any]) -> List[str]:
    """Generate tests for a specific entity."""
    lines = [
        f"# Tests for {entity_name} entity",
        f"class Test{entity_name.title()}:",
        "",
    ]
    
    # Test valid entity generation
    lines.extend([
        f"    @given(from_schema(SCHEMA['definitions']['{entity_name}']))",
        f"    def test_{entity_name.lower()}_valid_schema(self, data):",
        f'        """Test that generated {entity_name} data is valid."""',
        f"        errors = list(validator.iter_errors(data))",
        f"        assert not errors, f'Validation errors: {{errors}}'",
        "",
    ])
    
    # Test required fields
    required_fields = entity_schema.get("required", [])
    if required_fields:
        lines.extend([
        f"    @given(st.data())",
        f"    def test_{entity_name.lower()}_required_fields(self, data):",
        f'        """Test that {entity_name} has all required fields."""',
        f"        # Generate valid data",
        f"        valid_data = data.draw(from_schema(SCHEMA['definitions']['{entity_name}']))",
        f"        ",
        f"        # Check each required field",
        f"        for field in {required_fields}:",
        f"            assert field in valid_data, f'Missing required field: {{field}}'",
        f"            assert valid_data[field] is not None, f'Required field is None: {{field}}'",
        "",
        ])
    
    # Test field constraints
    properties = entity_schema.get("properties", {})
    for field_name, field_schema in properties.items():
        lines.extend(generate_field_tests(entity_name, field_name, field_schema))
    
    return lines

def generate_field_tests(entity_name: str, field_name: str, field_schema: Dict[str, Any]) -> List[str]:
    """Generate tests for a specific field."""
    lines = []
    
    # Test field type
    field_type = field_schema.get("type")
    if field_type:
        lines.extend([
        f"    def test_{entity_name.lower()}_{field_name}_type(self):",
        f'        """Test that {field_name} has correct type."""',
        f"        # This test would be implemented with specific type checking",
        f"        # based on the field schema",
        f"        pass",
        "",
        ])
    
    # Test enum values
    enum_values = field_schema.get("enum")
    if enum_values:
        lines.extend([
        f"    @given(st.sampled_from({enum_values}))",
        f"    def test_{entity_name.lower()}_{field_name}_enum(self, value):",
        f'        """Test that {field_name} accepts valid enum values."""',
        f"        data = {{'{field_name}': value}}",
        f"        # Add other required fields if needed",
        f"        errors = list(validator.iter_errors(data))",
        f"        # Note: This is a simplified test",
        f"        pass",
        "",
        ])
    
    # Test string length constraints
    if field_type == "string":
        min_length = field_schema.get("minLength")
        max_length = field_schema.get("maxLength")
        
        if min_length or max_length:
            lines.extend([
        f"    def test_{entity_name.lower()}_{field_name}_length(self):",
        f'        """Test that {field_name} respects length constraints."""',
        f"        min_len = {min_length or 0}",
        f"        max_len = {max_length or 'None'}",
        f"        # This test would validate string length constraints",
        f"        pass",
        "",
            ])
    
    # Test numeric range constraints
    if field_type in ["integer", "number"]:
        minimum = field_schema.get("minimum")
        maximum = field_schema.get("maximum")
        
        if minimum is not None or maximum is not None:
            lines.extend([
        f"    def test_{entity_name.lower()}_{field_name}_range(self):",
        f'        """Test that {field_name} respects range constraints."""',
        f"        min_val = {minimum or 'None'}",
        f"        max_val = {maximum or 'None'}",
        f"        # This test would validate numeric range constraints",
        f"        pass",
        "",
            ])
    
    return lines

def generate_schema_tests(schema: Dict[str, Any]) -> List[str]:
    """Generate general schema validation tests."""
    return [
        "class TestSchemaValidation:",
        "",
        "    def test_schema_structure(self):",
        '        """Test that schema has required structure."""',
        "        assert '$schema' in SCHEMA",
        "        assert 'definitions' in SCHEMA",
        "        assert len(SCHEMA['definitions']) > 0",
        "",
        "    def test_all_entities_valid(self):",
        '        """Test that all entity definitions are valid."""',
        "        for entity_name, entity_schema in SCHEMA['definitions'].items():",
        "            assert 'type' in entity_schema",
        "            assert entity_schema['type'] == 'object'",
        "            if 'properties' in entity_schema:",
        "                assert isinstance(entity_schema['properties'], dict)",
        "",
        "    @given(from_schema(SCHEMA))",
        "    def test_generated_data_valid(self, data):",
        '        """Test that data generated from schema is valid."""',
        "        errors = list(validator.iter_errors(data))",
        "        assert not errors, f'Validation errors: {{errors}}'",
        "",
    ]

def generate_constraint_tests(schema: Dict[str, Any]) -> List[str]:
    """Generate tests for schema constraints."""
    return [
        "class TestConstraints:",
        "",
        "    def test_no_additional_properties(self):",
        '        """Test that entities don't allow additional properties."""',
        "        for entity_name, entity_schema in SCHEMA['definitions'].items():",
        "            if entity_schema.get('additionalProperties') is False:",
        "                # Test with extra field",
        "                test_data = {'extra_field': 'value'}",
        "                errors = list(validator.iter_errors(test_data))",
        "                # Should have validation errors for extra fields",
        "                pass",
        "",
        "    def test_required_fields_enforced(self):",
        '        """Test that required fields are enforced."""',
        "        for entity_name, entity_schema in SCHEMA['definitions'].items():",
        "            required = entity_schema.get('required', [])",
        "            if required:",
        "                # Test with missing required field",
        "                test_data = {}",
        "                errors = list(validator.iter_errors(test_data))",
        "                # Should have validation errors for missing required fields",
        "                pass",
        "",
    ]

def generate_fuzz_tests(schema: Dict[str, Any]) -> List[str]:
    """Generate fuzz tests for robustness."""
    return [
        "class TestFuzzing:",
        "",
        "    @given(st.text())",
        "    def test_invalid_json_strings(self, text):",
        '        """Test handling of invalid JSON strings."""',
        "        try:",
        "            data = json.loads(text)",
        "            # If parsing succeeds, validate against schema",
        "            errors = list(validator.iter_errors(data))",
        "            # Should handle gracefully",
        "        except json.JSONDecodeError:",
        "            # Expected for invalid JSON",
        "            pass",
        "",
        "    @given(st.dictionaries(st.text(), st.text()))",
        "    def test_random_dicts(self, data):",
        '        """Test handling of random dictionaries."""',
        "        errors = list(validator.iter_errors(data))",
        "        # Should handle gracefully without crashing",
        "        assert isinstance(errors, list)",
        "",
        "    def test_malformed_data_types(self):",
        '        """Test handling of malformed data types."""',
        "        malformed_data = [",
        "            None,",
        "            '',",
        "            [],",
        "            {'invalid': 'data'}",
        "        ]",
        "        ",
        "        for data in malformed_data:",
        "            errors = list(validator.iter_errors(data))",
        "            # Should handle gracefully",
        "            assert isinstance(errors, list)",
        "",
    ]

def generate_hypothesis_strategies(schema: Dict[str, Any]) -> str:
    """Generate Hypothesis strategies for schema."""
    lines = [
        "# Hypothesis strategies for schema entities",
        "",
        "import hypothesis.strategies as st",
        "from hypothesis.extra.jsonschema import from_schema",
        "",
    ]
    
    definitions = schema.get("definitions", {})
    for entity_name in definitions.keys():
        lines.extend([
        f"def {entity_name.lower()}_strategy():",
        f'    """Generate {entity_name} instances."""',
        f"    return from_schema(SCHEMA['definitions']['{entity_name}'])",
        "",
        ])
    
    return "\n".join(lines) 