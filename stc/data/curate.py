"""Data curation and filtering utilities."""

import json
from pathlib import Path
from typing import List, Dict, Any, Set
import hashlib
from stc.config import ensure_dir

def curate_corpus(raw_dir: str, out_dir: str, include_tags: List[str], exclude_tags: List[str]) -> None:
    """
    Filter/dedupe/annotate raw corpora into ontology-aligned datasets.
    """
    raw_path = Path(raw_dir)
    out_path = Path(out_dir)
    ensure_dir(out_path)
    
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw data directory not found: {raw_dir}")
    
    # Collect all data files
    data_files = []
    for ext in ['.json', '.jsonl', '.yaml', '.yml']:
        data_files.extend(raw_path.glob(f"*{ext}"))
    
    if not data_files:
        raise ValueError(f"No data files found in {raw_dir}")
    
    # Process each file
    all_data = []
    seen_hashes = set()
    
    for file_path in data_files:
        data = load_data_file(file_path)
        filtered_data = filter_data(data, include_tags, exclude_tags)
        deduplicated_data = deduplicate_data(filtered_data, seen_hashes)
        all_data.extend(deduplicated_data)
    
    # Split into train/validation/test
    train_data, val_data, test_data = split_data(all_data)
    
    # Write output files
    write_jsonl(train_data, out_path / "train.jsonl")
    write_jsonl(val_data, out_path / "val.jsonl")
    write_jsonl(test_data, out_path / "test.jsonl")
    
    # Write metadata
    metadata = {
        "total_samples": len(all_data),
        "train_samples": len(train_data),
        "val_samples": len(val_data),
        "test_samples": len(test_data),
        "include_tags": include_tags,
        "exclude_tags": exclude_tags,
        "source_files": [str(f) for f in data_files]
    }
    
    with open(out_path / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

def load_data_file(file_path: Path) -> List[Dict[str, Any]]:
    """Load data from various file formats."""
    if file_path.suffix.lower() in ['.yaml', '.yml']:
        import yaml
        with open(file_path) as f:
            return yaml.safe_load(f)
    elif file_path.suffix.lower() == '.json':
        with open(file_path) as f:
            return json.load(f)
    elif file_path.suffix.lower() == '.jsonl':
        data = []
        with open(file_path) as f:
            for line in f:
                if line.strip():
                    data.append(json.loads(line))
        return data
    else:
        raise ValueError(f"Unsupported file format: {file_path.suffix}")

def filter_data(data: List[Dict[str, Any]], include_tags: List[str], exclude_tags: List[str]) -> List[Dict[str, Any]]:
    """Filter data based on tags."""
    if not include_tags and not exclude_tags:
        return data
    
    filtered = []
    for item in data:
        # Extract tags from item (assuming tags field or metadata)
        item_tags = extract_tags(item)
        
        # Check include tags
        if include_tags and not any(tag in item_tags for tag in include_tags):
            continue
        
        # Check exclude tags
        if exclude_tags and any(tag in item_tags for tag in exclude_tags):
            continue
        
        filtered.append(item)
    
    return filtered

def extract_tags(item: Dict[str, Any]) -> Set[str]:
    """Extract tags from a data item."""
    tags = set()
    
    # Common tag locations
    if 'tags' in item:
        if isinstance(item['tags'], list):
            tags.update(item['tags'])
        elif isinstance(item['tags'], str):
            tags.update(item['tags'].split(','))
    
    if 'metadata' in item and 'tags' in item['metadata']:
        if isinstance(item['metadata']['tags'], list):
            tags.update(item['metadata']['tags'])
        elif isinstance(item['metadata']['tags'], str):
            tags.update(item['metadata']['tags'].split(','))
    
    # Extract tags from text content (simple keyword matching)
    if 'text' in item:
        text = item['text'].lower()
        common_tags = ['pii', 'sensitive', 'private', 'public', 'internal']
        for tag in common_tags:
            if tag in text:
                tags.add(tag)
    
    return tags

def deduplicate_data(data: List[Dict[str, Any]], seen_hashes: Set[str]) -> List[Dict[str, Any]]:
    """Remove duplicate data items."""
    deduplicated = []
    
    for item in data:
        # Create a hash of the item content
        item_hash = create_item_hash(item)
        
        if item_hash not in seen_hashes:
            seen_hashes.add(item_hash)
            deduplicated.append(item)
    
    return deduplicated

def create_item_hash(item: Dict[str, Any]) -> str:
    """Create a hash of an item for deduplication."""
    # Normalize the item for hashing
    normalized = normalize_item(item)
    item_str = json.dumps(normalized, sort_keys=True)
    return hashlib.md5(item_str.encode()).hexdigest()

def normalize_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize an item for consistent hashing."""
    # Remove metadata that shouldn't affect deduplication
    normalized = item.copy()
    
    # Remove common metadata fields
    for key in ['id', 'created_at', 'updated_at', 'source', 'filename']:
        normalized.pop(key, None)
    
    # Normalize text content
    if 'text' in normalized:
        normalized['text'] = normalized['text'].strip().lower()
    
    return normalized

def split_data(data: List[Dict[str, Any]], train_ratio: float = 0.8, val_ratio: float = 0.1) -> tuple:
    """Split data into train/validation/test sets."""
    import random
    
    # Shuffle data
    random.shuffle(data)
    
    total = len(data)
    train_end = int(total * train_ratio)
    val_end = train_end + int(total * val_ratio)
    
    train_data = data[:train_end]
    val_data = data[train_end:val_end]
    test_data = data[val_end:]
    
    return train_data, val_data, test_data

def write_jsonl(data: List[Dict[str, Any]], file_path: Path) -> None:
    """Write data to JSONL format."""
    with open(file_path, "w") as f:
        for item in data:
            f.write(json.dumps(item) + "\n") 