"""URI parsing utilities for HDF5 MCP server.

This module provides utilities for parsing and validating the custom h5:// URI scheme
used to address HDF5 objects within files.
"""
import urllib.parse
from dataclasses import dataclass
from typing import Optional


@dataclass
class H5URI:
    """Represents a parsed HDF5 URI.
    
    A URI has the format: h5:///absolute/path/to/file.h5?path=/internal/path
    """
    file_path: str
    internal_path: str


def parse_uri(uri_str: str) -> H5URI:
    """Parse an HDF5 URI string into its components.
    
    Args:
        uri_str: URI string in format h5:///absolute/path/to/file.h5?path=/internal/path
        
    Returns:
        H5URI object with file_path and internal_path
        
    Raises:
        ValueError: If the URI is malformed or missing required components
        
    Examples:
        >>> uri = parse_uri("h5:///data/file.h5?path=/group1/dataset")
        >>> uri.file_path
        '/data/file.h5'
        >>> uri.internal_path
        '/group1/dataset'
    """
    if not uri_str:
        raise ValueError("URI string cannot be empty")
    
    try:
        parsed = urllib.parse.urlparse(uri_str)
    except Exception as e:
        raise ValueError(f"Failed to parse URI: {e}")
    
    # Validate scheme
    if parsed.scheme != 'h5':
        raise ValueError(f"Invalid scheme '{parsed.scheme}', expected 'h5'")
    
    # The file path is in the path component (starts with /)
    if not parsed.path:
        raise ValueError("Missing file path in URI")
    
    file_path = parsed.path
    
    # Parse query parameters to get the internal HDF5 path
    query_params = urllib.parse.parse_qs(parsed.query)
    
    if 'path' not in query_params:
        raise ValueError("Missing required 'path' query parameter")
    
    path_values = query_params['path']
    if not path_values or not path_values[0]:
        raise ValueError("Empty 'path' query parameter")
    
    internal_path = path_values[0]
    
    # Ensure internal path starts with /
    if not internal_path.startswith('/'):
        internal_path = '/' + internal_path
    
    return H5URI(file_path=file_path, internal_path=internal_path)


def build_uri(file_path: str, internal_path: str = "/") -> str:
    """Build an HDF5 URI from file path and internal path.
    
    Args:
        file_path: Absolute path to the HDF5 file
        internal_path: Path within the HDF5 file (defaults to root "/")
        
    Returns:
        Formatted URI string
        
    Examples:
        >>> build_uri("/data/file.h5", "/group1/dataset")
        'h5:///data/file.h5?path=/group1/dataset'
    """
    if not file_path:
        raise ValueError("File path cannot be empty")
    
    # Ensure internal path starts with /
    if not internal_path.startswith('/'):
        internal_path = '/' + internal_path
    
    # URL encode the internal path
    encoded_internal_path = urllib.parse.quote(internal_path, safe='/')
    
    return f"h5://{file_path}?path={encoded_internal_path}"
