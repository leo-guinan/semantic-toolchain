# Semantic Toolchain (stc)

A CLI tool to compile ontologies into schemas, grammars, tests, and Model Validation Models (MVMs).

## Overview

Semantic Toolchain is a comprehensive toolkit for building domain-specific AI models with strong schema validation. It provides a complete pipeline from ontology definition to deployed, validated models.

## Features

- **Ontology Compilation**: Convert YAML/JSON ontologies into multiple formats
- **Schema Generation**: JSON Schema, Pydantic models, TypeScript interfaces
- **Grammar Generation**: PEG/CFG grammars for constrained decoding
- **Data Curation**: Filter, dedupe, and annotate training corpora
- **Model Training**: Fine-tune with schema-aware rejection sampling
- **Test Generation**: Property-based tests from ontology constraints
- **Deployment**: Containerized bundles with fail-closed validation

## Quick Start

### Installation

```bash
# Using uv (recommended)
uv pip install semantic-toolchain

# Or from source
git clone https://github.com/your-org/semantic-toolchain.git
cd semantic-toolchain
uv pip install -e .
```

### Basic Usage

1. **Create an ontology**:

```yaml
# example.yaml
name: fairwork
description: Fair work ontology
version: "1.0.0"

entities:
  Job:
    description: A job posting
    fields:
      title:
        type: string
        description: Job title
        required: true
      salary:
        type: float
        description: Annual salary
        range: [0, 1000000]
        required: true
      location:
        type: string
        enum: ["remote", "hybrid", "onsite"]
        required: true

constraints:
  - expr: "salary > 0"
    message: "Salary must be positive"
```

2. **Compile to schemas**:

```bash
stc compile example.yaml --emit jsonschema,pydantic,ts,grammar
```

3. **Curate training data**:

```bash
stc curate raw_data/ --include-tags job,remote --exclude-tags pii
```

4. **Train a model**:

```bash
stc train --base mistral-0.7b --data data/clean/train.jsonl --schema build/fairwork.schema.json
```

5. **Generate tests**:

```bash
stc testgen build/fairwork.schema.json --out tests/property_tests.py
```

6. **Deploy**:

```bash
stc deploy models/mvm.ckpt build/fairwork.schema.json --runtime k8s
```

## CLI Commands

### `stc init <name>`
Scaffold a new domain project with sample files.

### `stc compile <ontology>`
Compile ontology into various artifacts:
- `--emit`: Output formats (jsonschema, pydantic, ts, grammar)
- `--out`: Output directory

### `stc curate <raw_dir>`
Filter and process raw data:
- `--include-tags`: Tags to keep
- `--exclude-tags`: Tags to drop
- `--out`: Output directory

### `stc train`
Fine-tune a model:
- `--base`: Base model ID/path
- `--data`: Training data file
- `--schema`: JSON schema path
- `--decoder`: Grammar file path
- `--lora`: Use LoRA fine-tuning
- `--epochs`: Number of epochs

### `stc testgen <schema>`
Generate property-based tests:
- `--out`: Output test file

### `stc deploy <model> <schema>`
Deploy model with validation:
- `--runtime`: Deployment target (k8s, local, ecs)
- `--bundle`: Create deployable bundle

## Development

### Setup

```bash
# Clone and setup
git clone https://github.com/your-org/semantic-toolchain.git
cd semantic-toolchain

# Use the development script
./scripts/dev.sh setup
```

### Development Commands

```bash
# Format code
./scripts/dev.sh format

# Run linting
./scripts/dev.sh lint

# Run tests
./scripts/dev.sh test

# Build package
./scripts/dev.sh build

# Create example ontology
./scripts/dev.sh example
```

### Project Structure

```
semantic-toolchain/
├── pyproject.toml          # Package configuration
├── README.md              # This file
├── stc/                   # Main package
│   ├── __init__.py
│   ├── cli.py             # CLI entrypoint
│   ├── config.py          # Global configuration
│   ├── ontology/          # Ontology processing
│   │   ├── loader.py      # YAML/JSON → AST
│   │   ├── models.py      # Pydantic models
│   │   └── validators.py  # Validation logic
│   ├── emitters/          # Code generation
│   │   ├── jsonschema.py  # JSON Schema
│   │   ├── pydantic_models.py
│   │   ├── ts_interfaces.py
│   │   └── grammar.py     # PEG/CFG
│   ├── data/              # Data processing
│   │   ├── curate.py      # Data curation
│   │   └── filters.py     # Data filtering
│   ├── train/             # Model training
│   │   ├── trainer.py     # HF/LoRA wrapper
│   │   └── rejection.py   # Schema sampling
│   ├── tests/             # Test generation
│   │   └── testgen.py     # Property tests
│   ├── deploy/            # Deployment
│   │   ├── packager.py    # Bundle builder
│   │   └── runtime.py     # Validators
│   └── utils/             # Utilities
│       ├── io.py          # File I/O
│       └── logging.py     # Logging
└── scripts/
    └── dev.sh             # Development script
```

## Ontology Format

Ontologies are defined in YAML or JSON with the following structure:

```yaml
name: string                    # Ontology name
description: string            # Description
version: string               # Version

entities:                      # Entity definitions
  EntityName:
    description: string        # Entity description
    fields:                    # Field definitions
      fieldName:
        type: string          # Field type
        description: string   # Field description
        required: boolean     # Required field
        enum: [string]        # Enum values
        range: [min, max]     # Numeric range
        default: any          # Default value

constraints:                   # Global constraints
  - expr: string              # Constraint expression
    message: string           # Error message
    severity: string          # Error severity

examples:                      # Example data
  - input: object             # Input data
    output: object            # Expected output
    description: string       # Example description
```

### Supported Field Types

- `string`: Text data
- `int`: Integer numbers
- `float`: Floating point numbers
- `bool`: Boolean values
- `list[string]`: String arrays
- `list[int]`: Integer arrays
- `list[float]`: Float arrays
- `list[bool]`: Boolean arrays

### Constraint Expressions

Constraints use a simple expression language:

```yaml
constraints:
  - expr: "len(name) >= 2"           # String length
  - expr: "age >= 18"                # Numeric comparison
  - expr: "price > 0"                # Positive values
  - expr: "status in ['active', 'pending']"  # Enum validation
```

## Generated Artifacts

### JSON Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "definitions": {
    "Job": {
      "type": "object",
      "properties": {
        "title": {"type": "string"},
        "salary": {"type": "number", "minimum": 0},
        "location": {"type": "string", "enum": ["remote", "hybrid", "onsite"]}
      },
      "required": ["title", "salary", "location"]
    }
  }
}
```

### Pydantic Models
```python
from pydantic import BaseModel, Field

class Job(BaseModel):
    title: str = Field(description="Job title")
    salary: float = Field(ge=0, description="Annual salary")
    location: str = Field(enum=["remote", "hybrid", "onsite"])
```

### TypeScript Interfaces
```typescript
export interface Job {
  title: string;
  salary: number;
  location: "remote" | "hybrid" | "onsite";
}
```

### PEG Grammar
```
# PEG grammar for constrained JSON generation
job_object <- '{' job_fields '}'
job_fields <- title_pair ',' salary_pair ',' location_pair
title_pair <- '"title"' ':' string
salary_pair <- '"salary"' ':' number_positive
location_pair <- '"location"' ':' location_enum
```

## Model Training

The training pipeline includes:

1. **Schema-aware preprocessing**: Data is validated against the ontology
2. **Rejection sampling**: Invalid outputs are rejected during training
3. **LoRA fine-tuning**: Efficient parameter-efficient fine-tuning
4. **Constraint enforcement**: Grammar-based decoding

## Deployment

Deployed models include:

- **Fail-closed validation**: Invalid outputs are rejected
- **Schema enforcement**: Runtime validation of inputs/outputs
- **Health monitoring**: Built-in health checks
- **Containerized**: Docker-based deployment

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run the development script: `./scripts/dev.sh all`
6. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Roadmap

- [ ] Support for more ontology formats (OWL, RDF)
- [ ] Advanced constraint language
- [ ] Multi-modal model support
- [ ] Cloud-native deployment
- [ ] Model versioning and A/B testing
- [ ] Integration with vector databases
- [ ] Real-time validation APIs