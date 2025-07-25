"""Runtime validators and middleware for deployment."""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
import jsonschema
from jsonschema import Draft7Validator

@dataclass
class RuntimeConfig:
    """Configuration for runtime validation."""
    schema_path: str
    enable_validation: bool = True
    enable_logging: bool = True
    fail_closed: bool = True
    max_validation_errors: int = 10

class RuntimeValidator:
    """Runtime validator for schema enforcement."""
    
    def __init__(self, config: RuntimeConfig):
        self.config = config
        self.schema = self._load_schema()
        self.validator = Draft7Validator(self.schema)
        self.logger = self._setup_logger()
    
    def _load_schema(self) -> Dict[str, Any]:
        """Load JSON schema from file."""
        with open(self.config.schema_path) as f:
            return json.load(f)
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logging for the runtime."""
        logger = logging.getLogger("stc_runtime")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def validate_input(self, data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate input data against schema."""
        if not self.config.enable_validation:
            return True, []
        
        try:
            errors = list(self.validator.iter_errors(data))
            error_messages = [str(error) for error in errors[:self.config.max_validation_errors]]
            
            if errors:
                self.logger.warning(f"Input validation failed: {error_messages}")
                if self.config.fail_closed:
                    return False, error_messages
            
            return True, error_messages
        except Exception as e:
            error_msg = f"Validation error: {e}"
            self.logger.error(error_msg)
            if self.config.fail_closed:
                return False, [error_msg]
            return True, [error_msg]
    
    def validate_output(self, data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate output data against schema."""
        if not self.config.enable_validation:
            return True, []
        
        try:
            errors = list(self.validator.iter_errors(data))
            error_messages = [str(error) for error in errors[:self.config.max_validation_errors]]
            
            if errors:
                self.logger.warning(f"Output validation failed: {error_messages}")
                if self.config.fail_closed:
                    return False, error_messages
            
            return True, error_messages
        except Exception as e:
            error_msg = f"Validation error: {e}"
            self.logger.error(error_msg)
            if self.config.fail_closed:
                return False, [error_msg]
            return True, [error_msg]

class RuntimeMiddleware:
    """Middleware for request/response validation."""
    
    def __init__(self, validator: RuntimeValidator):
        self.validator = validator
    
    def validate_request(self, request_data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate incoming request data."""
        return self.validator.validate_input(request_data)
    
    def validate_response(self, response_data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate outgoing response data."""
        return self.validator.validate_output(response_data)
    
    def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process and validate request data."""
        is_valid, errors = self.validate_request(request_data)
        
        if not is_valid:
            raise ValueError(f"Request validation failed: {errors}")
        
        return request_data
    
    def process_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process and validate response data."""
        is_valid, errors = self.validate_response(response_data)
        
        if not is_valid:
            self.validator.logger.warning(f"Response validation failed: {errors}")
            # In fail-closed mode, we might want to return an error response
            # instead of the invalid data
        
        return response_data

class ModelRuntime:
    """Runtime for model inference with validation."""
    
    def __init__(self, model_path: str, validator: RuntimeValidator):
        self.model_path = Path(model_path)
        self.validator = validator
        self.model = None
        self.tokenizer = None
        self._load_model()
    
    def _load_model(self):
        """Load the trained model."""
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            self.model = AutoModelForCausalLM.from_pretrained(self.model_path)
            
            self.validator.logger.info(f"Model loaded from {self.model_path}")
        except Exception as e:
            self.validator.logger.error(f"Failed to load model: {e}")
            raise
    
    def predict(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Make a prediction with validation."""
        # Validate input
        is_valid, errors = self.validator.validate_input(input_data)
        if not is_valid:
            raise ValueError(f"Input validation failed: {errors}")
        
        # Format input for model
        formatted_input = self._format_input(input_data)
        
        # Generate prediction
        try:
            output = self._generate_output(formatted_input)
            
            # Validate output
            is_valid, errors = self.validator.validate_output(output)
            if not is_valid:
                self.validator.logger.warning(f"Output validation failed: {errors}")
            
            return output
        except Exception as e:
            self.validator.logger.error(f"Prediction failed: {e}")
            raise
    
    def _format_input(self, input_data: Dict[str, Any]) -> str:
        """Format input data for the model."""
        # Convert input to text format
        if isinstance(input_data, dict):
            lines = []
            for key, value in input_data.items():
                if isinstance(value, str):
                    lines.append(f"{key}: {value}")
                else:
                    lines.append(f"{key}: {json.dumps(value)}")
            return "\n".join(lines)
        else:
            return str(input_data)
    
    def _generate_output(self, formatted_input: str) -> Dict[str, Any]:
        """Generate output from formatted input."""
        import torch
        
        # Tokenize input
        inputs = self.tokenizer(
            formatted_input,
            return_tensors="pt",
            truncation=True,
            max_length=2048
        )
        
        # Generate output
        with torch.no_grad():
            outputs = self.model.generate(
                inputs.input_ids,
                max_length=512,
                do_sample=True,
                temperature=0.7,
                pad_token_id=self.tokenizer.eos_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
            )
        
        # Decode output
        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Try to parse as JSON
        try:
            return json.loads(generated_text)
        except json.JSONDecodeError:
            # If not valid JSON, return as text
            return {"text": generated_text}

class HealthChecker:
    """Health checker for runtime monitoring."""
    
    def __init__(self, validator: RuntimeValidator, model_runtime: Optional[ModelRuntime] = None):
        self.validator = validator
        self.model_runtime = model_runtime
    
    def check_health(self) -> Dict[str, Any]:
        """Check the health of the runtime."""
        health_status = {
            "status": "healthy",
            "validator": True,
            "model": False,
            "schema": True,
            "errors": []
        }
        
        # Check validator
        try:
            # Test validation with sample data
            test_data = {"type": "test", "field": "value"}
            is_valid, errors = self.validator.validate_input(test_data)
            if not is_valid:
                health_status["validator"] = False
                health_status["errors"].append(f"Validator test failed: {errors}")
        except Exception as e:
            health_status["validator"] = False
            health_status["errors"].append(f"Validator error: {e}")
        
        # Check model
        if self.model_runtime:
            try:
                # Test model with sample input
                test_input = {"input": "test"}
                output = self.model_runtime.predict(test_input)
                health_status["model"] = True
            except Exception as e:
                health_status["model"] = False
                health_status["errors"].append(f"Model error: {e}")
        
        # Check schema
        try:
            with open(self.validator.config.schema_path) as f:
                json.load(f)
        except Exception as e:
            health_status["schema"] = False
            health_status["errors"].append(f"Schema error: {e}")
        
        # Overall status
        if not all([health_status["validator"], health_status["schema"]]):
            health_status["status"] = "unhealthy"
        
        return health_status

def create_runtime(schema_path: str, model_path: Optional[str] = None, **config_kwargs) -> tuple[RuntimeValidator, Optional[ModelRuntime]]:
    """Create a runtime with validator and optional model."""
    config = RuntimeConfig(schema_path=schema_path, **config_kwargs)
    validator = RuntimeValidator(config)
    
    model_runtime = None
    if model_path:
        model_runtime = ModelRuntime(model_path, validator)
    
    return validator, model_runtime 