"""IO utilities for the semantic toolchain."""

import json
import yaml
from pathlib import Path
from typing import Any, Dict, List, Union, Optional
from contextlib import contextmanager

def load_yaml(file_path: Union[str, Path]) -> Any:
    """Load YAML file."""
    with open(file_path, 'r') as f:
        return yaml.safe_load(f)

def save_yaml(data: Any, file_path: Union[str, Path]) -> None:
    """Save data to YAML file."""
    with open(file_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, indent=2)

def load_json(file_path: Union[str, Path]) -> Any:
    """Load JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)

def save_json(data: Any, file_path: Union[str, Path], indent: int = 2) -> None:
    """Save data to JSON file."""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=indent)

def load_jsonl(file_path: Union[str, Path]) -> List[Dict[str, Any]]:
    """Load JSONL file."""
    data = []
    with open(file_path, 'r') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data

def save_jsonl(data: List[Dict[str, Any]], file_path: Union[str, Path]) -> None:
    """Save data to JSONL file."""
    with open(file_path, 'w') as f:
        for item in data:
            f.write(json.dumps(item) + '\n')

def load_file(file_path: Union[str, Path]) -> str:
    """Load text file."""
    with open(file_path, 'r') as f:
        return f.read()

def save_file(content: str, file_path: Union[str, Path]) -> None:
    """Save content to text file."""
    with open(file_path, 'w') as f:
        f.write(content)

@contextmanager
def atomic_write(file_path: Union[str, Path], mode: str = 'w'):
    """Atomically write to a file."""
    file_path = Path(file_path)
    temp_path = file_path.with_suffix(file_path.suffix + '.tmp')
    
    try:
        with open(temp_path, mode) as f:
            yield f
        temp_path.replace(file_path)
    except Exception:
        if temp_path.exists():
            temp_path.unlink()
        raise

def ensure_file_exists(file_path: Union[str, Path], default_content: str = "") -> None:
    """Ensure a file exists, creating it with default content if it doesn't."""
    file_path = Path(file_path)
    if not file_path.exists():
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w') as f:
            f.write(default_content)

def copy_file_safe(src: Union[str, Path], dst: Union[str, Path]) -> None:
    """Safely copy a file, creating directories if needed."""
    src = Path(src)
    dst = Path(dst)
    
    if not src.exists():
        raise FileNotFoundError(f"Source file not found: {src}")
    
    dst.parent.mkdir(parents=True, exist_ok=True)
    
    with open(src, 'rb') as f_src:
        with open(dst, 'wb') as f_dst:
            f_dst.write(f_src.read())

def find_files(directory: Union[str, Path], pattern: str = "*") -> List[Path]:
    """Find files matching a pattern in a directory."""
    directory = Path(directory)
    if not directory.exists():
        return []
    
    return list(directory.glob(pattern))

def find_files_recursive(directory: Union[str, Path], pattern: str = "*") -> List[Path]:
    """Find files matching a pattern recursively in a directory."""
    directory = Path(directory)
    if not directory.exists():
        return []
    
    return list(directory.rglob(pattern))

def get_file_size(file_path: Union[str, Path]) -> int:
    """Get file size in bytes."""
    return Path(file_path).stat().st_size

def get_file_hash(file_path: Union[str, Path], algorithm: str = "md5") -> str:
    """Get file hash."""
    import hashlib
    
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hash_obj = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_obj.update(chunk)
    
    return hash_obj.hexdigest()

def backup_file(file_path: Union[str, Path], suffix: str = ".backup") -> Path:
    """Create a backup of a file."""
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    backup_path = file_path.with_suffix(file_path.suffix + suffix)
    copy_file_safe(file_path, backup_path)
    return backup_path

def restore_file(backup_path: Union[str, Path], original_path: Union[str, Path]) -> None:
    """Restore a file from backup."""
    backup_path = Path(backup_path)
    original_path = Path(original_path)
    
    if not backup_path.exists():
        raise FileNotFoundError(f"Backup file not found: {backup_path}")
    
    copy_file_safe(backup_path, original_path)

def read_lines(file_path: Union[str, Path]) -> List[str]:
    """Read file lines, stripping whitespace."""
    with open(file_path, 'r') as f:
        return [line.strip() for line in f if line.strip()]

def write_lines(lines: List[str], file_path: Union[str, Path]) -> None:
    """Write lines to file."""
    with open(file_path, 'w') as f:
        for line in lines:
            f.write(line + '\n')

def append_line(line: str, file_path: Union[str, Path]) -> None:
    """Append a line to a file."""
    with open(file_path, 'a') as f:
        f.write(line + '\n')

def count_lines(file_path: Union[str, Path]) -> int:
    """Count lines in a file."""
    with open(file_path, 'r') as f:
        return sum(1 for _ in f)

def is_binary_file(file_path: Union[str, Path]) -> bool:
    """Check if a file is binary."""
    file_path = Path(file_path)
    if not file_path.exists():
        return False
    
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(1024)
            return b'\x00' in chunk
    except Exception:
        return True

def get_file_extension(file_path: Union[str, Path]) -> str:
    """Get file extension."""
    return Path(file_path).suffix.lower()

def is_text_file(file_path: Union[str, Path]) -> bool:
    """Check if a file is a text file."""
    text_extensions = {'.txt', '.md', '.py', '.js', '.ts', '.json', '.yaml', '.yml', '.xml', '.html', '.css'}
    return get_file_extension(file_path) in text_extensions and not is_binary_file(file_path) 