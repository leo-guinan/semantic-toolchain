"""Schema-aware rejection sampling for model training."""

import json
import jsonschema
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from transformers import PreTrainedTokenizer
import torch

@dataclass
class RejectionConfig:
    """Configuration for rejection sampling."""
    schema_path: str
    max_rejection_attempts: int = 10
    rejection_threshold: float = 0.5
    enable_grammar_constraints: bool = True
    enable_schema_validation: bool = True
    enable_custom_validators: bool = True

class SchemaAwareSampler:
    """Schema-aware rejection sampling for structured outputs."""
    
    def __init__(self, config: RejectionConfig, tokenizer: PreTrainedTokenizer):
        self.config = config
        self.tokenizer = tokenizer
        self.schema = self._load_schema()
        self.validator = jsonschema.Draft7Validator(self.schema)
        self.custom_validators = []
    
    def _load_schema(self) -> Dict[str, Any]:
        """Load JSON schema from file."""
        with open(self.config.schema_path) as f:
            return json.load(f)
    
    def add_custom_validator(self, validator: Callable[[Dict[str, Any]], bool]) -> None:
        """Add a custom validation function."""
        self.custom_validators.append(validator)
    
    def validate_output(self, output: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate output against schema and constraints."""
        errors = []
        
        # Schema validation
        if self.config.enable_schema_validation:
            try:
                self.validator.validate(output)
            except jsonschema.ValidationError as e:
                errors.append(f"Schema validation failed: {e.message}")
        
        # Grammar constraints
        if self.config.enable_grammar_constraints:
            grammar_errors = self._check_grammar_constraints(output)
            errors.extend(grammar_errors)
        
        # Custom validators
        if self.config.enable_custom_validators:
            for validator in self.custom_validators:
                try:
                    if not validator(output):
                        errors.append("Custom validation failed")
                except Exception as e:
                    errors.append(f"Custom validation error: {e}")
        
        return len(errors) == 0, errors
    
    def _check_grammar_constraints(self, output: Dict[str, Any]) -> List[str]:
        """Check grammar-based constraints."""
        errors = []
        
        # Check for required fields based on entity type
        if "type" in output:
            entity_type = output["type"]
            if entity_type in self.schema.get("definitions", {}):
                entity_schema = self.schema["definitions"][entity_type]
                required_fields = entity_schema.get("required", [])
                
                for field in required_fields:
                    if field not in output:
                        errors.append(f"Missing required field: {field}")
        
        # Check field value constraints
        for field_name, field_value in output.items():
            if field_name in self.schema.get("definitions", {}):
                field_schema = self.schema["definitions"][field_name]
                field_errors = self._validate_field_constraints(field_value, field_schema)
                errors.extend(field_errors)
        
        return errors
    
    def _validate_field_constraints(self, value: Any, field_schema: Dict[str, Any]) -> List[str]:
        """Validate field value against constraints."""
        errors = []
        
        # Check enum values
        if "enum" in field_schema and value not in field_schema["enum"]:
            errors.append(f"Value '{value}' not in allowed enum: {field_schema['enum']}")
        
        # Check string length constraints
        if field_schema.get("type") == "string" and isinstance(value, str):
            min_length = field_schema.get("minLength")
            max_length = field_schema.get("maxLength")
            
            if min_length and len(value) < min_length:
                errors.append(f"String too short: {len(value)} < {min_length}")
            
            if max_length and len(value) > max_length:
                errors.append(f"String too long: {len(value)} > {max_length}")
        
        # Check numeric range constraints
        if field_schema.get("type") in ["integer", "number"] and isinstance(value, (int, float)):
            minimum = field_schema.get("minimum")
            maximum = field_schema.get("maximum")
            
            if minimum is not None and value < minimum:
                errors.append(f"Value too small: {value} < {minimum}")
            
            if maximum is not None and value > maximum:
                errors.append(f"Value too large: {value} > {maximum}")
        
        return errors
    
    def sample_with_rejection(self, model, input_ids: torch.Tensor, max_length: int = 512) -> torch.Tensor:
        """Generate output with rejection sampling."""
        for attempt in range(self.config.max_rejection_attempts):
            # Generate candidate output
            with torch.no_grad():
                outputs = model.generate(
                    input_ids,
                    max_length=max_length,
                    do_sample=True,
                    temperature=0.7,
                    top_p=0.9,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                )
            
            # Decode the generated text
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Try to parse as JSON
            try:
                parsed_output = self._extract_json_from_text(generated_text)
                if parsed_output is not None:
                    # Validate the parsed output
                    is_valid, errors = self.validate_output(parsed_output)
                    if is_valid:
                        return outputs[0]
                    else:
                        print(f"Rejection attempt {attempt + 1}: {errors}")
            except Exception as e:
                print(f"Parsing error in attempt {attempt + 1}: {e}")
        
        # If all attempts failed, return the last generated output
        print("Warning: All rejection sampling attempts failed, returning last output")
        return outputs[0]
    
    def _extract_json_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from generated text."""
        # Look for JSON-like structures in the text
        import re
        
        # Try to find JSON object patterns
        json_patterns = [
            r'\{[^{}]*\}',  # Simple JSON object
            r'\{.*\}',      # More complex JSON object
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue
        
        # If no JSON found, try to parse the entire text
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None
    
    def create_training_hook(self) -> Callable:
        """Create a training hook for rejection sampling."""
        def rejection_hook(model, inputs, outputs):
            """Hook to apply rejection sampling during training."""
            # This would be called during training to validate outputs
            # and potentially adjust the loss based on schema compliance
            pass
        
        return rejection_hook

class ConstraintValidator:
    """Validator for complex constraints."""
    
    def __init__(self, constraints: List[str]):
        self.constraints = constraints
    
    def validate(self, data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate data against constraints."""
        errors = []
        
        for constraint in self.constraints:
            if not self._evaluate_constraint(data, constraint):
                errors.append(f"Constraint failed: {constraint}")
        
        return len(errors) == 0, errors
    
    def _evaluate_constraint(self, data: Dict[str, Any], constraint: str) -> bool:
        """Evaluate a single constraint."""
        try:
            # Simple constraint evaluation
            # In practice, you'd use a proper expression evaluator
            
            # Handle length constraints
            if "len(" in constraint and ")" in constraint:
                return self._evaluate_length_constraint(data, constraint)
            
            # Handle comparison constraints
            if any(op in constraint for op in ["<=", ">=", "<", ">", "==", "!="]):
                return self._evaluate_comparison_constraint(data, constraint)
            
            # Default to True for unknown constraints
            return True
        except Exception:
            return False
    
    def _evaluate_length_constraint(self, data: Dict[str, Any], constraint: str) -> bool:
        """Evaluate length-based constraints."""
        import re
        
        # Parse len(field) <= value
        match = re.search(r'len\((\w+)\)\s*([<>=]+)\s*(\d+)', constraint)
        if match:
            field, op, value = match.groups()
            value = int(value)
            
            if field in data:
                field_value = data[field]
                if isinstance(field_value, str):
                    length = len(field_value)
                    
                    if op == "<=":
                        return length <= value
                    elif op == ">=":
                        return length >= value
                    elif op == "<":
                        return length < value
                    elif op == ">":
                        return length > value
        
        return True
    
    def _evaluate_comparison_constraint(self, data: Dict[str, Any], constraint: str) -> bool:
        """Evaluate comparison constraints."""
        import re
        
        # Parse field op value
        match = re.search(r'(\w+)\s*([<>=!]+)\s*([^<>=!]+)', constraint)
        if match:
            field, op, value = match.groups()
            
            if field in data:
                field_value = data[field]
                
                # Try to convert value to appropriate type
                try:
                    if isinstance(field_value, (int, float)):
                        value = float(value)
                    elif isinstance(field_value, str):
                        value = value.strip('"\'')
                    
                    if op == "<=":
                        return field_value <= value
                    elif op == ">=":
                        return field_value >= value
                    elif op == "<":
                        return field_value < value
                    elif op == ">":
                        return field_value > value
                    elif op == "==":
                        return field_value == value
                    elif op == "!=":
                        return field_value != value
                except (ValueError, TypeError):
                    pass
        
        return True 