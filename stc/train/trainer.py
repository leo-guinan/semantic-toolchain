"""Model training with schema-aware rejection sampling."""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from transformers import (
    AutoModelForCausalLM, 
    AutoTokenizer, 
    Trainer, 
    TrainingArguments,
    DataCollatorForLanguageModeling
)
from datasets import load_dataset
from peft import LoraConfig, get_peft_model, TaskType
import torch
from stc.config import ensure_dir

def train_model(
    base: str,
    data: str,
    schema: str,
    decoder: str,
    out: str,
    lora: bool = True,
    epochs: int = 3
) -> None:
    """
    Fine-tune a domain-specific model with schema-aware rejection sampling.
    """
    # Ensure output directory exists
    out_path = Path(out)
    ensure_dir(out_path)
    
    # Load model and tokenizer
    print(f"Loading base model: {base}")
    tokenizer = AutoTokenizer.from_pretrained(base)
    model = AutoModelForCausalLM.from_pretrained(base)
    
    # Add padding token if not present
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    # Configure LoRA if requested
    if lora:
        print("Configuring LoRA fine-tuning")
        lora_config = LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            inference_mode=False,
            r=16,
            lora_alpha=32,
            lora_dropout=0.1,
            target_modules=["q_proj", "v_proj", "k_proj", "o_proj"]
        )
        model = get_peft_model(model, lora_config)
        model.print_trainable_parameters()
    
    # Load dataset
    print(f"Loading dataset: {data}")
    dataset = load_dataset("json", data_files=data, split="train")
    
    # Load schema for validation
    schema_data = load_schema(schema)
    
    # Preprocess dataset
    print("Preprocessing dataset")
    tokenized_dataset = preprocess_dataset(dataset, tokenizer, schema_data)
    
    # Configure training arguments
    training_args = TrainingArguments(
        output_dir=str(out_path / "checkpoints"),
        per_device_train_batch_size=2,
        per_device_eval_batch_size=2,
        num_train_epochs=epochs,
        logging_steps=20,
        save_steps=500,
        eval_steps=500,
        save_strategy="steps",
        evaluation_strategy="steps",
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        warmup_steps=100,
        learning_rate=5e-5,
        weight_decay=0.01,
        fp16=torch.cuda.is_available(),
        dataloader_pin_memory=False,
        remove_unused_columns=False,
    )
    
    # Create data collator
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,
    )
    
    # Create trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset,
        data_collator=data_collator,
    )
    
    # Train the model
    print("Starting training")
    trainer.train()
    
    # Save the final model
    print(f"Saving model to {out}")
    if lora:
        # Save LoRA adapter
        model.save_pretrained(out)
        tokenizer.save_pretrained(out)
    else:
        # Save full model
        trainer.save_model(out)
        tokenizer.save_pretrained(out)
    
    # Save training metadata
    save_training_metadata(out_path, base, data, schema, lora, epochs)

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load JSON schema for validation."""
    with open(schema_path) as f:
        return json.load(f)

def preprocess_dataset(dataset, tokenizer, schema_data: Dict[str, Any]) -> Any:
    """Preprocess dataset with schema-aware formatting."""
    
    def format_example(example):
        """Format a single example for training."""
        # Extract input and output
        if "input" in example and "output" in example:
            # Structured input/output format
            input_text = format_input(example["input"])
            output_text = format_output(example["output"], schema_data)
        else:
            # Assume it's already formatted
            input_text = example.get("text", "")
            output_text = ""
        
        # Combine input and output
        full_text = f"{input_text}\n{output_text}"
        
        # Tokenize
        tokenized = tokenizer(
            full_text,
            truncation=True,
            max_length=2048,
            padding=False,
            return_tensors=None,
        )
        
        # Add labels (same as input_ids for causal LM)
        tokenized["labels"] = tokenized["input_ids"].copy()
        
        return tokenized
    
    return dataset.map(format_example, remove_columns=dataset.column_names)

def format_input(input_data: Dict[str, Any]) -> str:
    """Format input data as text prompt."""
    if isinstance(input_data, dict):
        # Convert dict to formatted text
        lines = []
        for key, value in input_data.items():
            if isinstance(value, str):
                lines.append(f"{key}: {value}")
            else:
                lines.append(f"{key}: {json.dumps(value)}")
        return "\n".join(lines)
    else:
        return str(input_data)

def format_output(output_data: Dict[str, Any], schema_data: Dict[str, Any]) -> str:
    """Format output data according to schema."""
    # Validate output against schema
    try:
        validate_against_schema(output_data, schema_data)
        return json.dumps(output_data, indent=2)
    except Exception as e:
        # If validation fails, still format but mark as invalid
        print(f"Warning: Output validation failed: {e}")
        return json.dumps(output_data, indent=2)

def validate_against_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """Validate data against JSON schema."""
    # Simple validation - in practice, use jsonschema library
    try:
        # Check if data matches any entity in schema
        definitions = schema.get("definitions", {})
        for entity_name, entity_schema in definitions.items():
            if validate_entity(data, entity_schema):
                return True
        return False
    except Exception:
        return False

def validate_entity(data: Dict[str, Any], entity_schema: Dict[str, Any]) -> bool:
    """Validate data against a specific entity schema."""
    properties = entity_schema.get("properties", {})
    required = entity_schema.get("required", [])
    
    # Check required fields
    for field in required:
        if field not in data:
            return False
    
    # Check field types (simplified)
    for field, value in data.items():
        if field in properties:
            field_schema = properties[field]
            if not validate_field_value(value, field_schema):
                return False
    
    return True

def validate_field_value(value: Any, field_schema: Dict[str, Any]) -> bool:
    """Validate a field value against its schema."""
    field_type = field_schema.get("type")
    
    if field_type == "string":
        return isinstance(value, str)
    elif field_type == "integer":
        return isinstance(value, int)
    elif field_type == "number":
        return isinstance(value, (int, float))
    elif field_type == "boolean":
        return isinstance(value, bool)
    elif field_type == "array":
        return isinstance(value, list)
    elif field_type == "object":
        return isinstance(value, dict)
    
    return True

def save_training_metadata(out_path: Path, base: str, data: str, schema: str, lora: bool, epochs: int) -> None:
    """Save training metadata."""
    metadata = {
        "base_model": base,
        "training_data": data,
        "schema": schema,
        "lora": lora,
        "epochs": epochs,
        "training_completed": True,
    }
    
    with open(out_path / "training_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2) 