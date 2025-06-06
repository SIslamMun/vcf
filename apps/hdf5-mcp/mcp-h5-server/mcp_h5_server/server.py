"""Main MCP server implementation for HDF5 files.

This module contains the main server class that integrates all components
and manages the MCP session.
"""
import asyncio
import sys
from typing import List, Any, Dict
import logging

try:
    import mcp.types as types
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
except ImportError as e:
    print(f"Error: MCP library not installed: {e}", file=sys.stderr)
    print("Please install with: uv sync", file=sys.stderr)
    sys.exit(1)

from .h5_utils import scan_for_h5_files
from .handlers import (
    handle_resources_list,
    handle_resources_read,
    handle_tools_list,
    handle_tools_call
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class H5MCPServer:
    """MCP Server for HDF5 file exploration and data retrieval."""
    
    def __init__(self, root_dir: str):
        """Initialize the server with a root directory.
        
        Args:
            root_dir: Root directory to scan for HDF5 files
        """
        self.root_dir = root_dir
        self.h5_files: List[str] = []
        self.app = Server("mcp-h5-server")
        
        # Scan for HDF5 files
        logger.info(f"Scanning for HDF5 files in: {root_dir}")
        self.h5_files = scan_for_h5_files(root_dir)
        logger.info(f"Found {len(self.h5_files)} HDF5 files")
        
        # Register handlers
        self._register_handlers()
    
    def _register_handlers(self):
        """Register MCP request handlers."""
        
        # Register resource handlers
        @self.app.list_resources()
        async def list_resources() -> List[types.Resource]:
            """List available HDF5 files as resources."""
            resource_dicts = handle_resources_list(self.h5_files)
            
            resources = []
            for res_dict in resource_dicts:
                resource = types.Resource(
                    uri=res_dict["uri"],
                    name=res_dict["name"],
                    description=res_dict.get("description"),
                    mimeType=res_dict.get("mimeType")
                )
                resources.append(resource)
            
            return resources
        
        @self.app.read_resource()
        async def read_resource(uri: str) -> str:
            """Read a specific HDF5 resource."""
            try:
                result = handle_resources_read(uri)
                # Extract text content from the result
                if "contents" in result and result["contents"]:
                    return result["contents"][0]["text"]
                return "No content available"
            except Exception as e:
                logger.error(f"Error reading resource {uri}: {e}")
                raise
        
        # Register tool handlers
        @self.app.list_tools()
        async def list_tools() -> List[types.Tool]:
            """List available tools."""
            tool_dicts = handle_tools_list()
            
            tools = []
            for tool_dict in tool_dicts:
                tool = types.Tool(
                    name=tool_dict["name"],
                    description=tool_dict["description"],
                    inputSchema=tool_dict["inputSchema"]
                )
                tools.append(tool)
            
            return tools
        
        @self.app.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
            """Call a tool with the given arguments."""
            try:
                result = handle_tools_call(name, arguments)
                
                if result.get("isError", False):
                    # Return error content
                    error_text = result["content"][0]["text"]
                    return [types.TextContent(type="text", text=error_text)]
                else:
                    # Return success content
                    success_text = result["content"][0]["text"]
                    return [types.TextContent(type="text", text=success_text)]
                    
            except Exception as e:
                logger.error(f"Error calling tool {name}: {e}")
                error_message = f"Tool execution failed: {str(e)}"
                return [types.TextContent(type="text", text=error_message)]
    
    async def run(self):
        """Run the MCP server."""
        logger.info("Starting MCP H5 Server...")
        logger.info(f"Serving {len(self.h5_files)} HDF5 files from {self.root_dir}")
        
        # Use stdio transport
        async with stdio_server() as (read_stream, write_stream):
            await self.app.run(
                read_stream,
                write_stream,
                self.app.create_initialization_options()
            )
