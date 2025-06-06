"""HDF5 utilities for file scanning, object inspection, and data retrieval.

This module provides low-level functions for interacting with HDF5 files,
including file discovery, metadata extraction, and safe data access.
"""
import os
import sys
import re
from typing import List, Dict, Any, Tuple, Union
import warnings

try:
    import h5py
    import numpy as np
except ImportError as e:
    print(f"Error: Required dependencies not installed: {e}", file=sys.stderr)
    print("Please install with: uv sync", file=sys.stderr)
    sys.exit(1)


def scan_for_h5_files(root_dir: str) -> List[str]:
    """Recursively scan a directory for valid HDF5 files.
    
    Args:
        root_dir: Root directory to scan recursively
        
    Returns:
        List of absolute paths to valid HDF5 files
        
    Note:
        Invalid or unreadable files are skipped with a warning message.
    """
    if not os.path.exists(root_dir):
        raise ValueError(f"Directory does not exist: {root_dir}")
    
    if not os.path.isdir(root_dir):
        raise ValueError(f"Path is not a directory: {root_dir}")
    
    valid_files = []
    h5_extensions = {'.h5', '.hdf5'}
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            # Check if file has HDF5 extension
            _, ext = os.path.splitext(filename.lower())
            if ext not in h5_extensions:
                continue
            
            file_path = os.path.join(dirpath, filename)
            absolute_path = os.path.abspath(file_path)
            
            # Try to open the file to verify it's a valid HDF5 file
            try:
                with h5py.File(absolute_path, 'r') as f:
                    # Successfully opened, so it's valid
                    valid_files.append(absolute_path)
            except Exception as e:
                # Log warning and continue
                print(f"Warning: Skipping invalid HDF5 file '{absolute_path}': {e}", 
                      file=sys.stderr)
                continue
    
    return valid_files


def get_object_info(file_path: str, internal_path: str) -> Dict[str, Any]:
    """Get metadata information about an HDF5 object.
    
    Args:
        file_path: Absolute path to the HDF5 file
        internal_path: Path within the HDF5 file
        
    Returns:
        Dictionary containing object metadata. Structure depends on object type:
        - Link: {'type': 'SoftLink'|'ExternalLink', 'target': str}
        - Group: {'type': 'Group', 'attributes': dict, 'members': list}
        - Dataset: {'type': 'Dataset', 'attributes': dict, 'shape': tuple, 
                   'dtype': str, 'size': int, 'chunks': tuple|None}
        
    Raises:
        ValueError: If file doesn't exist or internal path is invalid
        OSError: If file cannot be opened
    """
    if not os.path.exists(file_path):
        raise ValueError(f"File does not exist: {file_path}")
    
    try:
        with h5py.File(file_path, 'r') as f:
            # First check if it's a link
            link = f.get(internal_path, getlink=True)
            
            if isinstance(link, h5py.SoftLink):
                return {
                    'type': 'SoftLink',
                    'target': link.path
                }
            elif isinstance(link, h5py.ExternalLink):
                return {
                    'type': 'ExternalLink',
                    'target': f"{link.filename}:{link.path}"
                }
            
            # Not a link, get the actual object
            if internal_path not in f:
                raise ValueError(f"Path '{internal_path}' not found in file")
            
            obj = f[internal_path]
            
            if isinstance(obj, h5py.Group):
                return {
                    'type': 'Group',
                    'attributes': dict(obj.attrs),
                    'members': list(obj.keys())
                }
            elif isinstance(obj, h5py.Dataset):
                return {
                    'type': 'Dataset',
                    'attributes': dict(obj.attrs),
                    'shape': obj.shape,
                    'dtype': str(obj.dtype),
                    'size': obj.size,
                    'chunks': obj.chunks
                }
            else:
                # Fallback for unknown object types
                return {
                    'type': str(type(obj).__name__),
                    'attributes': dict(obj.attrs) if hasattr(obj, 'attrs') else {}
                }
                
    except Exception as e:
        if "does not exist" in str(e) or "not found" in str(e):
            raise ValueError(f"Path '{internal_path}' not found in file '{file_path}'")
        else:
            raise OSError(f"Failed to read file '{file_path}': {e}")


def parse_slice_string(slice_str: str) -> Tuple:
    """Parse a NumPy-style slice string into a tuple of slice objects.
    
    This function safely parses slice strings without using eval() to prevent
    code injection. It supports:
    - Empty string -> ()
    - Single integers: "5" -> (5,)
    - Slices: "1:10", ":5", "::2" -> (slice(1,10), slice(None,5), slice(None,None,2))
    - Multiple dimensions: "1:10, :, 5" -> (slice(1,10), slice(None), 5)
    - Ellipsis: "..." -> (Ellipsis,)
    
    Args:
        slice_str: String representation of a slice (e.g., "0:10, :, 5")
        
    Returns:
        Tuple of slice objects, integers, and/or Ellipsis
        
    Raises:
        ValueError: If the slice string is malformed
        
    Examples:
        >>> parse_slice_string("0:10")
        (slice(0, 10, None),)
        >>> parse_slice_string("5")
        (5,)
        >>> parse_slice_string("1:10, :, 5")
        (slice(1, 10, None), slice(None, None, None), 5)
    """
    if not slice_str.strip():
        return ()
    
    # Split by comma and process each component
    components = [comp.strip() for comp in slice_str.split(',')]
    result = []
    
    for comp in components:
        if not comp:
            raise ValueError("Empty slice component")
        
        # Handle ellipsis
        if comp == '...':
            result.append(Ellipsis)
            continue
        
        # Check if it's a simple integer
        if _is_integer(comp):
            result.append(int(comp))
            continue
        
        # Must be a slice - validate format
        if ':' not in comp:
            raise ValueError(f"Invalid slice component: '{comp}'")
        
        # Parse slice components
        slice_parts = comp.split(':')
        if len(slice_parts) > 3:
            raise ValueError(f"Too many ':' in slice component: '{comp}'")
        
        # Convert slice parts to integers or None
        parsed_parts = []
        for part in slice_parts:
            part = part.strip()
            if part == '':
                parsed_parts.append(None)
            elif _is_integer(part):
                parsed_parts.append(int(part))
            else:
                raise ValueError(f"Invalid slice value: '{part}'")
        
        # Create slice object
        if len(parsed_parts) == 1:
            # Should not happen since we checked for ':' above, but be safe
            raise ValueError(f"Invalid slice format: '{comp}'")
        elif len(parsed_parts) == 2:
            result.append(slice(parsed_parts[0], parsed_parts[1]))
        else:  # len == 3
            result.append(slice(parsed_parts[0], parsed_parts[1], parsed_parts[2]))
    
    return tuple(result)


def _is_integer(s: str) -> bool:
    """Check if a string represents a valid integer (including negative)."""
    s = s.strip()
    if not s:
        return False
    
    # Use regex to match integer pattern
    return bool(re.match(r'^-?\d+$', s))


def read_dataset_slice(file_path: str, internal_path: str, slice_obj: Tuple) -> List:
    """Read a slice of data from an HDF5 dataset.
    
    Args:
        file_path: Absolute path to the HDF5 file
        internal_path: Path to the dataset within the HDF5 file
        slice_obj: Tuple of slice objects from parse_slice_string()
        
    Returns:
        JSON-serializable list representation of the data
        
    Raises:
        ValueError: If the path doesn't point to a dataset or slice is invalid
        OSError: If file cannot be opened
    """
    if not os.path.exists(file_path):
        raise ValueError(f"File does not exist: {file_path}")
    
    try:
        with h5py.File(file_path, 'r') as f:
            if internal_path not in f:
                raise ValueError(f"Path '{internal_path}' not found in file")
            
            obj = f[internal_path]
            
            if not isinstance(obj, h5py.Dataset):
                raise ValueError(f"Path '{internal_path}' is not a dataset (it's a {type(obj).__name__})")
            
            # Apply the slice
            try:
                if slice_obj:
                    data = obj[slice_obj]
                else:
                    data = obj[()]  # Get all data for empty slice
                
                # Convert to JSON-serializable format
                if isinstance(data, np.ndarray):
                    return data.tolist()
                else:
                    # Scalar value
                    return data.item() if hasattr(data, 'item') else data
                    
            except IndexError as e:
                raise ValueError(f"Slice out of bounds for dataset shape {obj.shape}: {e}")
            except Exception as e:
                raise ValueError(f"Failed to apply slice to dataset: {e}")
                
    except Exception as e:
        if isinstance(e, ValueError):
            raise
        else:
            raise OSError(f"Failed to read from file '{file_path}': {e}")
