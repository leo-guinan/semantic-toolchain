#!/bin/bash

# Development script for semantic-toolchain

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if uv is installed
check_uv() {
    if ! command -v uv &> /dev/null; then
        print_error "uv is not installed. Please install it first:"
        echo "curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi
    print_success "uv is installed"
}

# Setup development environment
setup_dev() {
    print_status "Setting up development environment..."
    
    # Create virtual environment and install dependencies
    uv venv
    uv pip install -e .
    uv pip install -e ".[dev]"
    
    print_success "Development environment setup complete"
}

# Run tests
run_tests() {
    print_status "Running tests..."
    
    # Run pytest
    uv run pytest tests/ -v --tb=short
    
    print_success "Tests completed"
}

# Run linting
run_lint() {
    print_status "Running linting..."
    
    # Run black
    uv run black stc/ --check
    
    # Run isort
    uv run isort stc/ --check-only
    
    # Run mypy
    uv run mypy stc/
    
    print_success "Linting completed"
}

# Format code
format_code() {
    print_status "Formatting code..."
    
    # Run black
    uv run black stc/
    
    # Run isort
    uv run isort stc/
    
    print_success "Code formatting completed"
}

# Build package
build_package() {
    print_status "Building package..."
    
    # Clean previous builds
    rm -rf dist/ build/ *.egg-info/
    
    # Build package
    uv run python -m build
    
    print_success "Package build completed"
}

# Install package
install_package() {
    print_status "Installing package..."
    
    # Install in development mode
    uv pip install -e .
    
    print_success "Package installed"
}

# Run CLI
run_cli() {
    print_status "Running CLI..."
    
    # Run the CLI with help
    uv run stc --help
    
    print_success "CLI test completed"
}

# Create example ontology
create_example() {
    print_status "Creating example ontology..."
    
    mkdir -p examples
    
    cat > examples/example_ontology.yaml << 'EOF'
name: example
description: Example ontology for testing
version: "1.0.0"

entities:
  Person:
    description: A person entity
    fields:
      name:
        type: string
        description: Full name of the person
        required: true
      age:
        type: int
        description: Age of the person
        range: [0, 150]
        required: true
      email:
        type: string
        description: Email address
        required: false
      status:
        type: string
        enum: ["active", "inactive", "pending"]
        description: Current status
        required: true

  Product:
    description: A product entity
    fields:
      id:
        type: string
        description: Unique product identifier
        required: true
      name:
        type: string
        description: Product name
        required: true
      price:
        type: float
        description: Product price
        range: [0.0, 1000000.0]
        required: true
      category:
        type: string
        enum: ["electronics", "clothing", "books", "other"]
        description: Product category
        required: true

constraints:
  - expr: "len(name) >= 2"
    message: "Name must be at least 2 characters long"
  - expr: "price > 0"
    message: "Price must be positive"

examples:
  - input:
      type: "Person"
      name: "John Doe"
      age: 30
      email: "john@example.com"
      status: "active"
    output:
      type: "Person"
      name: "John Doe"
      age: 30
      email: "john@example.com"
      status: "active"
EOF

    print_success "Example ontology created at examples/example_ontology.yaml"
}

# Show help
show_help() {
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  setup     - Setup development environment"
    echo "  test      - Run tests"
    echo "  lint      - Run linting"
    echo "  format    - Format code"
    echo "  build     - Build package"
    echo "  install   - Install package"
    echo "  cli       - Test CLI"
    echo "  example   - Create example ontology"
    echo "  all       - Run setup, format, lint, and test"
    echo "  help      - Show this help message"
    echo ""
}

# Main script logic
main() {
    check_uv
    
    case "${1:-help}" in
        setup)
            setup_dev
            ;;
        test)
            run_tests
            ;;
        lint)
            run_lint
            ;;
        format)
            format_code
            ;;
        build)
            build_package
            ;;
        install)
            install_package
            ;;
        cli)
            run_cli
            ;;
        example)
            create_example
            ;;
        all)
            setup_dev
            format_code
            run_lint
            run_tests
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@" 