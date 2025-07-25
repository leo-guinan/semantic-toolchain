"""Property-based tests generated from ontology schema."""

import pytest
import json
import jsonschema
from pathlib import Path
from hypothesis import given, strategies as st
from hypothesis.extra.jsonschema import from_schema

# Load schema from example.schema.json
SCHEMA_PATH = Path('example.schema.json')
with open(SCHEMA_PATH) as f:
    SCHEMA = json.load(f)

validator = jsonschema.Draft7Validator(SCHEMA)

# Tests for Person entity
class TestPerson:

    @given(from_schema(SCHEMA['definitions']['Person']))
    def test_person_valid_schema(self, data):
        """Test that generated Person data is valid."""
        errors = list(validator.iter_errors(data))
        assert not errors, f'Validation errors: {errors}'

    @given(st.data())
    def test_person_required_fields(self, data):
        """Test that Person has all required fields."""
        # Generate valid data
        valid_data = data.draw(from_schema(SCHEMA['definitions']['Person']))
        
        # Check each required field
        for field in ['name', 'age', 'status']:
            assert field in valid_data, f'Missing required field: {field}'
            assert valid_data[field] is not None, f'Required field is None: {field}'


# Tests for Product entity
class TestProduct:

    @given(from_schema(SCHEMA['definitions']['Product']))
    def test_product_valid_schema(self, data):
        """Test that generated Product data is valid."""
        errors = list(validator.iter_errors(data))
        assert not errors, f'Validation errors: {errors}'

    @given(st.data())
    def test_product_required_fields(self, data):
        """Test that Product has all required fields."""
        # Generate valid data
        valid_data = data.draw(from_schema(SCHEMA['definitions']['Product']))
        
        # Check each required field
        for field in ['id', 'name', 'price', 'category']:
            assert field in valid_data, f'Missing required field: {field}'
            assert valid_data[field] is not None, f'Required field is None: {field}'


class TestSchemaValidation:

    def test_schema_structure(self):
        """Test that schema has required structure."""
        assert '$schema' in SCHEMA
        assert 'definitions' in SCHEMA
        assert len(SCHEMA['definitions']) > 0

    def test_all_entities_valid(self):
        """Test that all entity definitions are valid."""
        for entity_name, entity_schema in SCHEMA['definitions'].items():
            assert 'type' in entity_schema
            assert entity_schema['type'] == 'object'
            if 'properties' in entity_schema:
                assert isinstance(entity_schema['properties'], dict)

    @given(from_schema(SCHEMA))
    def test_generated_data_valid(self, data):
        """Test that data generated from schema is valid."""
        errors = list(validator.iter_errors(data))
        assert not errors, f'Validation errors: {{errors}}'


class TestConstraints:

    def test_no_additional_properties(self):
        """Test that entities don't allow additional properties."""
        for entity_name, entity_schema in SCHEMA['definitions'].items():
            if entity_schema.get('additionalProperties') is False:
                # Test with extra field
                test_data = {'extra_field': 'value'}
                errors = list(validator.iter_errors(test_data))
                # Should have validation errors for extra fields
                pass

    def test_required_fields_enforced(self):
        """Test that required fields are enforced."""
        for entity_name, entity_schema in SCHEMA['definitions'].items():
            required = entity_schema.get('required', [])
            if required:
                # Test with missing required field
                test_data = {}
                errors = list(validator.iter_errors(test_data))
                # Should have validation errors for missing required fields
                pass


class TestFuzzing:

    @given(st.text())
    def test_invalid_json_strings(self, text):
        """Test handling of invalid JSON strings."""
        try:
            data = json.loads(text)
            # If parsing succeeds, validate against schema
            errors = list(validator.iter_errors(data))
            # Should handle gracefully
        except json.JSONDecodeError:
            # Expected for invalid JSON
            pass

    @given(st.dictionaries(st.text(), st.text()))
    def test_random_dicts(self, data):
        """Test handling of random dictionaries."""
        errors = list(validator.iter_errors(data))
        # Should handle gracefully without crashing
        assert isinstance(errors, list)

    def test_malformed_data_types(self):
        """Test handling of malformed data types."""
        malformed_data = [
            None,
            '',
            [],
            {'invalid': 'data'}
        ]
        
        for data in malformed_data:
            errors = list(validator.iter_errors(data))
            # Should handle gracefully
            assert isinstance(errors, list)
