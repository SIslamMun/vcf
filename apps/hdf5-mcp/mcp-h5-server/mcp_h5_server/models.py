"""Pydantic models for data structures and validation.

This module defines the data models used throughout the MCP H5 server for
consistent data representation and validation.
"""
from typing import List, Dict, Any, Optional, Union, Tuple
from pydantic import BaseModel, Field


class GroupInfo(BaseModel):
    """Information about an HDF5 group."""
    type: str = Field(default="Group", description="Object type")
    attributes: Dict[str, Any] = Field(description="Group attributes")
    members: List[str] = Field(description="Names of member objects")


class DatasetInfo(BaseModel):
    """Information about an HDF5 dataset."""
    type: str = Field(default="Dataset", description="Object type")
    attributes: Dict[str, Any] = Field(description="Dataset attributes")
    shape: Tuple[int, ...] = Field(description="Dataset shape")
    dtype: str = Field(description="Dataset data type")
    size: int = Field(description="Total number of elements")
    chunks: Optional[Tuple[int, ...]] = Field(description="Chunk size (if chunked)")


class LinkInfo(BaseModel):
    """Information about an HDF5 link."""
    type: str = Field(description="Link type (SoftLink or ExternalLink)")
    target: str = Field(description="Link target path")


class ToolInput(BaseModel):
    """Input parameters for the read_dataset_slice tool."""
    uri: str = Field(description="HDF5 URI pointing to a dataset")
    slice_str: str = Field(description="NumPy-style slice string")


class H5ObjectInfo(BaseModel):
    """Generic HDF5 object information."""
    type: str = Field(description="Object type")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Object attributes")
    
    # Optional fields for different object types
    members: Optional[List[str]] = Field(None, description="Members (for groups)")
    shape: Optional[Tuple[int, ...]] = Field(None, description="Shape (for datasets)")
    dtype: Optional[str] = Field(None, description="Data type (for datasets)")
    size: Optional[int] = Field(None, description="Size (for datasets)")
    chunks: Optional[Tuple[int, ...]] = Field(None, description="Chunks (for datasets)")
    target: Optional[str] = Field(None, description="Target (for links)")


# Type aliases for convenience
ObjectInfo = Union[GroupInfo, DatasetInfo, LinkInfo, H5ObjectInfo]
