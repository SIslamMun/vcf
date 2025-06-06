"""MCP request handlers for resources and tools.

This module implements the handlers for MCP requests including resource listing,
resource reading, tool listing, and tool execution.
"""
from typing import List, Dict, Any, Union
import json
import os

from .uri import parse_uri, build_uri
from .h5_utils import get_object_info, parse_slice_string, read_dataset_slice
from .models import ToolInput, H5ObjectInfo


def handle_resources_list(file_paths: List[str]) -> List[Dict[str, Any]]:
    """Handle the resources/list MCP request.
    
    Args:
        file_paths: List of absolute paths to HDF5 files
        
    Returns:
        List of MCP Resource dictionaries
    """
    resources = []
    
    for file_path in file_paths:
        # Create a resource for the root of each file
        uri = build_uri(file_path, "/")
        name = os.path.basename(file_path)
        
        resource = {
            "uri": uri,
            "name": name,
            "description": f"HDF5 file: {name}",
            "mimeType": "application/x-hdf5"
        }
        resources.append(resource)
    
    return resources


def handle_resources_read(uri: str) -> Dict[str, Any]:
    """Handle the resources/read MCP request.
    
    Args:
        uri: HDF5 URI to read
        
    Returns:
        MCP resource content dictionary
        
    Raises:
        ValueError: If URI is invalid or object not found
    """
    try:
        # Parse the URI
        h5_uri = parse_uri(uri)
        
        # Get object information
        obj_info = get_object_info(h5_uri.file_path, h5_uri.internal_path)
        
        # Create H5ObjectInfo model for validation
        h5_obj = H5ObjectInfo(**obj_info)
        
        # Format the content based on object type
        if h5_obj.type == "Group":
            content_text = _format_group_content(h5_obj, h5_uri)
        elif h5_obj.type == "Dataset":
            content_text = _format_dataset_content(h5_obj, h5_uri)
        elif h5_obj.type in ["SoftLink", "ExternalLink"]:
            content_text = _format_link_content(h5_obj, h5_uri)
        else:
            content_text = f"Unknown object type: {h5_obj.type}"
        
        return {
            "contents": [
                {
                    "type": "text",
                    "text": content_text
                }
            ]
        }
        
    except Exception as e:
        raise ValueError(f"Failed to read resource '{uri}': {e}")


def _format_group_content(obj: H5ObjectInfo, h5_uri) -> str:
    """Format group information as text content."""
    lines = [
        f"HDF5 Group: {h5_uri.internal_path}",
        f"File: {h5_uri.file_path}",
        "",
        f"Members ({len(obj.members or [])}):"
    ]
    
    if obj.members:
        for member in obj.members:
            member_path = h5_uri.internal_path.rstrip('/') + '/' + member
            member_uri = build_uri(h5_uri.file_path, member_path)
            lines.append(f"  - {member} ({member_uri})")
    else:
        lines.append("  (no members)")
    
    if obj.attributes:
        lines.extend([
            "",
            "Attributes:"
        ])
        for key, value in obj.attributes.items():
            lines.append(f"  {key}: {value}")
    
    return "\n".join(lines)


def _format_dataset_content(obj: H5ObjectInfo, h5_uri) -> str:
    """Format dataset information as text content."""
    lines = [
        f"HDF5 Dataset: {h5_uri.internal_path}",
        f"File: {h5_uri.file_path}",
        "",
        f"Shape: {obj.shape}",
        f"Data type: {obj.dtype}",
        f"Size: {obj.size} elements"
    ]
    
    if obj.chunks:
        lines.append(f"Chunks: {obj.chunks}")
    
    if obj.attributes:
        lines.extend([
            "",
            "Attributes:"
        ])
        for key, value in obj.attributes.items():
            lines.append(f"  {key}: {value}")
    
    lines.extend([
        "",
        f"To read data, use the read_dataset_slice tool with URI: {build_uri(h5_uri.file_path, h5_uri.internal_path)}"
    ])
    
    return "\n".join(lines)


def _format_link_content(obj: H5ObjectInfo, h5_uri) -> str:
    """Format link information as text content."""
    lines = [
        f"HDF5 {obj.type}: {h5_uri.internal_path}",
        f"File: {h5_uri.file_path}",
        "",
        f"Target: {obj.target}"
    ]
    
    return "\n".join(lines)


def handle_tools_list() -> List[Dict[str, Any]]:
    """Handle the tools/list MCP request.
    
    Returns:
        List containing the read_dataset_slice tool definition
    """
    tool_definition = {
        "name": "read_dataset_slice",
        "description": "Read a slice of data from an HDF5 dataset",
        "inputSchema": {
            "type": "object",
            "properties": {
                "uri": {
                    "type": "string",
                    "description": "The HDF5 URI pointing to the dataset (e.g., h5:///path/to/file.h5?path=/dataset)"
                },
                "slice_str": {
                    "type": "string",
                    "description": "NumPy-style slice string (e.g., '0:10', ':', '0:10, 5:15', '...')"
                }
            },
            "required": ["uri", "slice_str"]
        }
    }
    
    return [tool_definition]


def handle_tools_call(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handle the tools/call MCP request.
    
    Args:
        name: Tool name to call
        arguments: Tool arguments
        
    Returns:
        MCP tool result dictionary
    """
    if name != "read_dataset_slice":
        return {
            "isError": True,
            "content": [
                {
                    "type": "text",
                    "text": f"Unknown tool: {name}"
                }
            ]
        }
    
    try:
        # Validate input using Pydantic model
        tool_input = ToolInput(**arguments)
        
        # Parse the URI
        h5_uri = parse_uri(tool_input.uri)
        
        # Parse the slice string
        slice_obj = parse_slice_string(tool_input.slice_str)
        
        # Read the data slice
        data = read_dataset_slice(h5_uri.file_path, h5_uri.internal_path, slice_obj)
        
        # Return the data as JSON
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(data, indent=2)
                }
            ]
        }
        
    except Exception as e:
        return {
            "isError": True,
            "content": [
                {
                    "type": "text",
                    "text": f"Error: {str(e)}"
                }
            ]
        }
