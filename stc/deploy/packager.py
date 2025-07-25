"""Container and bundle builder for deployment."""

import json
import shutil
import tarfile
from pathlib import Path
from typing import Dict, Any, List, Optional
from stc.config import ensure_dir

def build_bundle(model_path: str, schema_path: str, output_path: Optional[str] = None) -> str:
    """Build a deployable bundle with model and validators."""
    
    model_path = Path(model_path)
    schema_path = Path(schema_path)
    
    if not model_path.exists():
        raise FileNotFoundError(f"Model path not found: {model_path}")
    
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema path not found: {schema_path}")
    
    # Create bundle directory
    if output_path is None:
        output_path = f"bundle_{model_path.stem}_{schema_path.stem}"
    
    bundle_path = Path(output_path)
    ensure_dir(bundle_path)
    
    # Copy model files
    model_dest = bundle_path / "model"
    ensure_dir(model_dest)
    
    if model_path.is_file():
        shutil.copy2(model_path, model_dest)
    else:
        shutil.copytree(model_path, model_dest, dirs_exist_ok=True)
    
    # Copy schema files
    schema_dest = bundle_path / "schema"
    ensure_dir(schema_dest)
    
    if schema_path.is_file():
        shutil.copy2(schema_path, schema_dest)
    else:
        shutil.copytree(schema_path, schema_dest, dirs_exist_ok=True)
    
    # Create runtime configuration
    runtime_config = {
        "model_path": "model",
        "schema_path": "schema",
        "runtime_type": "python",
        "version": "1.0.0",
        "dependencies": [
            "transformers",
            "torch",
            "jsonschema",
            "pydantic"
        ]
    }
    
    with open(bundle_path / "runtime_config.json", "w") as f:
        json.dump(runtime_config, f, indent=2)
    
    # Create Dockerfile
    dockerfile_content = generate_dockerfile(runtime_config)
    with open(bundle_path / "Dockerfile", "w") as f:
        f.write(dockerfile_content)
    
    # Create requirements.txt
    requirements_content = generate_requirements(runtime_config)
    with open(bundle_path / "requirements.txt", "w") as f:
        f.write(requirements_content)
    
    # Create entrypoint script
    entrypoint_content = generate_entrypoint()
    with open(bundle_path / "entrypoint.py", "w") as f:
        f.write(entrypoint_content)
    
    # Create bundle manifest
    manifest = {
        "name": bundle_path.name,
        "version": "1.0.0",
        "model_type": "transformer",
        "schema_type": "json_schema",
        "created_at": str(Path().cwd()),
        "files": list_files_recursive(bundle_path)
    }
    
    with open(bundle_path / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
    
    # Create compressed archive
    archive_path = create_archive(bundle_path)
    
    return str(archive_path)

def generate_dockerfile(config: Dict[str, Any]) -> str:
    """Generate Dockerfile for the bundle."""
    return f"""# Dockerfile for {config.get('name', 'semantic-toolchain')} bundle
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bundle files
COPY . .

# Set environment variables
ENV MODEL_PATH=/app/model
ENV SCHEMA_PATH=/app/schema
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "entrypoint.py"]
"""

def generate_requirements(config: Dict[str, Any]) -> str:
    """Generate requirements.txt for the bundle."""
    base_requirements = [
        "transformers>=4.42.0",
        "torch>=2.0.0",
        "jsonschema>=4.21.1",
        "pydantic>=2.5.0",
        "fastapi>=0.100.0",
        "uvicorn>=0.20.0",
        "rich>=13.7.0"
    ]
    
    # Add custom dependencies
    custom_deps = config.get("dependencies", [])
    for dep in custom_deps:
        if dep not in [req.split(">=")[0] for req in base_requirements]:
            base_requirements.append(dep)
    
    return "\n".join(base_requirements)

def generate_entrypoint() -> str:
    """Generate entrypoint script for the bundle."""
    return '''"""Entrypoint script for semantic toolchain bundle."""

import os
import json
import asyncio
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

# Load runtime configuration
with open("runtime_config.json") as f:
    RUNTIME_CONFIG = json.load(f)

# Load schema
SCHEMA_PATH = Path(RUNTIME_CONFIG["schema_path"])
with open(SCHEMA_PATH) as f:
    SCHEMA = json.load(f)

# Initialize FastAPI app
app = FastAPI(title="Semantic Toolchain Runtime")

class PredictionRequest(BaseModel):
    input: Dict[str, Any]

class PredictionResponse(BaseModel):
    output: Dict[str, Any]
    confidence: float

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "model_loaded": True}

@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """Make a prediction using the loaded model."""
    try:
        # TODO: Implement actual model inference
        # This is a placeholder implementation
        
        # Validate input against schema
        # validate_input(request.input, SCHEMA)
        
        # Generate prediction
        output = {
            "type": "example_entity",
            "field1": "example_value",
            "field2": 42
        }
        
        return PredictionResponse(
            output=output,
            confidence=0.95
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/schema")
async def get_schema():
    """Get the schema definition."""
    return SCHEMA

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''

def list_files_recursive(directory: Path) -> List[str]:
    """List all files in directory recursively."""
    files = []
    for item in directory.rglob("*"):
        if item.is_file():
            files.append(str(item.relative_to(directory)))
    return files

def create_archive(bundle_path: Path) -> Path:
    """Create a compressed archive of the bundle."""
    archive_path = bundle_path.with_suffix(".tar.gz")
    
    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(bundle_path, arcname=bundle_path.name)
    
    return archive_path

def extract_bundle(archive_path: str, extract_to: Optional[str] = None) -> str:
    """Extract a bundle archive."""
    archive_path = Path(archive_path)
    
    if not archive_path.exists():
        raise FileNotFoundError(f"Archive not found: {archive_path}")
    
    if extract_to is None:
        extract_to = archive_path.stem
    
    extract_path = Path(extract_to)
    ensure_dir(extract_path)
    
    with tarfile.open(archive_path, "r:gz") as tar:
        tar.extractall(extract_path)
    
    return str(extract_path)

def validate_bundle(bundle_path: str) -> List[str]:
    """Validate a bundle for deployment."""
    bundle_path = Path(bundle_path)
    errors = []
    
    # Check required files
    required_files = [
        "runtime_config.json",
        "manifest.json",
        "Dockerfile",
        "requirements.txt",
        "entrypoint.py"
    ]
    
    for file_name in required_files:
        if not (bundle_path / file_name).exists():
            errors.append(f"Missing required file: {file_name}")
    
    # Check model directory
    if not (bundle_path / "model").exists():
        errors.append("Missing model directory")
    
    # Check schema directory
    if not (bundle_path / "schema").exists():
        errors.append("Missing schema directory")
    
    # Validate runtime config
    try:
        with open(bundle_path / "runtime_config.json") as f:
            config = json.load(f)
        
        required_config_keys = ["model_path", "schema_path", "runtime_type"]
        for key in required_config_keys:
            if key not in config:
                errors.append(f"Missing config key: {key}")
    except Exception as e:
        errors.append(f"Invalid runtime config: {e}")
    
    return errors 