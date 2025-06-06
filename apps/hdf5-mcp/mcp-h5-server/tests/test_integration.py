"""Integration tests for MCP handlers.

This module contains integration tests that verify the complete MCP protocol
functionality including resource and tool handlers.
"""
import pytest
import json
import os
from unittest.mock import patch, AsyncMock

from mcp_h5_server.handlers import (
    handle_resources_list,
    handle_resources_read,
    handle_tools_list,
    handle_tools_call
)
from mcp_h5_server.server import H5MCPServer
from mcp_h5_server.uri import build_uri


class TestResourceHandlers:
    """Test the MCP resource handlers."""
    
    def test_handle_resources_list_empty(self):
        """Test resources list with no files."""
        result = handle_resources_list([])
        assert result == []
    
    def test_handle_resources_list_single_file(self, simple_h5_file):
        """Test resources list with a single HDF5 file."""
        result = handle_resources_list([simple_h5_file])
        
        assert len(result) == 1
        resource = result[0]
        
        assert "uri" in resource
        assert "name" in resource
        assert "description" in resource
        assert "mimeType" in resource
        
        assert resource["name"] == os.path.basename(simple_h5_file)
        assert resource["mimeType"] == "application/x-hdf5"
        assert resource["uri"] == build_uri(simple_h5_file, "/")
        assert simple_h5_file in resource["description"]
    
    def test_handle_resources_list_multiple_files(self, simple_h5_file, complex_h5_file):
        """Test resources list with multiple HDF5 files."""
        files = [simple_h5_file, complex_h5_file]
        result = handle_resources_list(files)
        
        assert len(result) == 2
        
        # Check that all files are represented
        uris = [res["uri"] for res in result]
        expected_uris = [build_uri(f, "/") for f in files]
        
        for expected_uri in expected_uris:
            assert expected_uri in uris
    
    def test_handle_resources_read_root_group(self, simple_h5_file):
        """Test reading the root group of an HDF5 file."""
        uri = build_uri(simple_h5_file, "/")
        result = handle_resources_read(uri)
        
        assert "contents" in result
        assert len(result["contents"]) == 1
        assert result["contents"][0]["type"] == "text"
        
        content = result["contents"][0]["text"]
        assert "HDF5 Group: /" in content
        assert simple_h5_file in content
        assert "Members" in content
    
    def test_handle_resources_read_dataset(self, simple_h5_file):
        """Test reading dataset information."""
        uri = build_uri(simple_h5_file, "/data")
        result = handle_resources_read(uri)
        
        assert "contents" in result
        content = result["contents"][0]["text"]
        
        assert "HDF5 Dataset: /data" in content
        assert "Shape:" in content
        assert "Data type:" in content
        assert "To read data, use the read_dataset_slice tool" in content
    
    def test_handle_resources_read_group(self, complex_h5_file):
        """Test reading group information."""
        uri = build_uri(complex_h5_file, "/group1")
        result = handle_resources_read(uri)
        
        assert "contents" in result
        content = result["contents"][0]["text"]
        
        assert "HDF5 Group: /group1" in content
        assert "Members" in content
    
    def test_handle_resources_read_link(self, complex_h5_file):
        """Test reading link information."""
        uri = build_uri(complex_h5_file, "/soft_link")
        result = handle_resources_read(uri)
        
        assert "contents" in result
        content = result["contents"][0]["text"]
        
        assert "HDF5 SoftLink: /soft_link" in content
        assert "Target:" in content
    
    def test_handle_resources_read_invalid_uri(self):
        """Test reading with invalid URI."""
        with pytest.raises(ValueError, match="Failed to read resource"):
            handle_resources_read("invalid://uri")
    
    def test_handle_resources_read_nonexistent_file(self):
        """Test reading from non-existent file."""
        uri = build_uri("/nonexistent/file.h5", "/data")
        with pytest.raises(ValueError, match="Failed to read resource"):
            handle_resources_read(uri)
    
    def test_handle_resources_read_nonexistent_path(self, simple_h5_file):
        """Test reading non-existent path in valid file."""
        uri = build_uri(simple_h5_file, "/nonexistent")
        with pytest.raises(ValueError, match="Failed to read resource"):
            handle_resources_read(uri)


class TestToolHandlers:
    """Test the MCP tool handlers."""
    
    def test_handle_tools_list(self):
        """Test listing available tools."""
        result = handle_tools_list()
        
        assert len(result) == 1
        tool = result[0]
        
        assert tool["name"] == "read_dataset_slice"
        assert "description" in tool
        assert "inputSchema" in tool
        
        # Check schema structure
        schema = tool["inputSchema"]
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "required" in schema
        assert "uri" in schema["properties"]
        assert "slice_str" in schema["properties"]
        assert set(schema["required"]) == {"uri", "slice_str"}
    
    def test_handle_tools_call_read_dataset_slice_full(self, simple_h5_file):
        """Test calling read_dataset_slice tool with full dataset."""
        uri = build_uri(simple_h5_file, "/data")
        arguments = {
            "uri": uri,
            "slice_str": ":"
        }
        
        result = handle_tools_call("read_dataset_slice", arguments)
        
        assert "content" in result
        assert "isError" not in result or not result["isError"]
        
        content_text = result["content"][0]["text"]
        data = json.loads(content_text)
        
        # Should be a list of integers [0, 1, 2, 3, 4]
        assert isinstance(data, list)
        assert data == [0, 1, 2, 3, 4]
    
    def test_handle_tools_call_read_dataset_slice_partial(self, simple_h5_file):
        """Test calling read_dataset_slice tool with partial slice."""
        uri = build_uri(simple_h5_file, "/data")
        arguments = {
            "uri": uri,
            "slice_str": "1:4"
        }
        
        result = handle_tools_call("read_dataset_slice", arguments)
        
        assert "content" in result
        assert "isError" not in result or not result["isError"]
        
        content_text = result["content"][0]["text"]
        data = json.loads(content_text)
        
        # Should be [1, 2, 3]
        assert data == [1, 2, 3]
    
    def test_handle_tools_call_read_dataset_slice_2d(self, complex_h5_file):
        """Test calling read_dataset_slice tool with 2D dataset."""
        uri = build_uri(complex_h5_file, "/group1/dataset_2d")
        arguments = {
            "uri": uri,
            "slice_str": "0:2, 0:2"
        }
        
        result = handle_tools_call("read_dataset_slice", arguments)
        
        assert "content" in result
        assert "isError" not in result or not result["isError"]
        
        content_text = result["content"][0]["text"]
        data = json.loads(content_text)
        
        # Should be a 2x2 array
        assert isinstance(data, list)
        assert len(data) == 2
        assert len(data[0]) == 2
    
    def test_handle_tools_call_unknown_tool(self):
        """Test calling unknown tool."""
        result = handle_tools_call("unknown_tool", {})
        
        assert result["isError"] is True
        assert "Unknown tool: unknown_tool" in result["content"][0]["text"]
    
    def test_handle_tools_call_invalid_arguments(self):
        """Test calling tool with invalid arguments."""
        # Missing required arguments
        result = handle_tools_call("read_dataset_slice", {})
        
        assert result["isError"] is True
        assert "Error:" in result["content"][0]["text"]
    
    def test_handle_tools_call_invalid_uri(self):
        """Test calling tool with invalid URI."""
        arguments = {
            "uri": "invalid://uri",
            "slice_str": ":"
        }
        
        result = handle_tools_call("read_dataset_slice", arguments)
        
        assert result["isError"] is True
        assert "Error:" in result["content"][0]["text"]
    
    def test_handle_tools_call_invalid_slice(self, simple_h5_file):
        """Test calling tool with invalid slice string."""
        uri = build_uri(simple_h5_file, "/data")
        arguments = {
            "uri": uri,
            "slice_str": "invalid_slice"
        }
        
        result = handle_tools_call("read_dataset_slice", arguments)
        
        assert result["isError"] is True
        assert "Error:" in result["content"][0]["text"]
    
    def test_handle_tools_call_nonexistent_dataset(self, simple_h5_file):
        """Test calling tool with non-existent dataset."""
        uri = build_uri(simple_h5_file, "/nonexistent")
        arguments = {
            "uri": uri,
            "slice_str": ":"
        }
        
        result = handle_tools_call("read_dataset_slice", arguments)
        
        assert result["isError"] is True
        assert "Error:" in result["content"][0]["text"]


class TestServerIntegration:
    """Test the complete MCP server integration."""
    
    @pytest.fixture
    def server(self, temp_h5_dir):
        """Create a server instance for testing."""
        return H5MCPServer(temp_h5_dir)
    
    def test_server_initialization(self, server, temp_h5_dir):
        """Test server initialization and file discovery."""
        assert server.root_dir == temp_h5_dir
        assert len(server.h5_files) > 0
        assert server.app is not None
    
    def test_server_file_scanning(self, server):
        """Test that server finds HDF5 files correctly."""
        # Should find at least the test files we created
        assert len(server.h5_files) >= 2
        
        # All found files should be HDF5 files
        for file_path in server.h5_files:
            assert file_path.endswith(('.h5', '.hdf5'))
            assert os.path.exists(file_path)
    
    @pytest.mark.asyncio
    async def test_server_mcp_handlers_registration(self, server):
        """Test that MCP handlers are properly registered."""
        # This is more of a smoke test since we can't easily test
        # the actual MCP protocol without a full MCP client
        
        # The server should have registered handlers
        assert hasattr(server.app, '_resources_list_handler')
        assert hasattr(server.app, '_resources_read_handler')
        assert hasattr(server.app, '_tools_list_handler')
        assert hasattr(server.app, '_tools_call_handler')


class TestEndToEndWorkflow:
    """Test complete end-to-end workflows."""
    
    def test_discover_and_explore_workflow(self, temp_h5_dir, simple_h5_file, complex_h5_file):
        """Test the complete workflow of discovering and exploring HDF5 files."""
        # Step 1: Create server and list resources
        server = H5MCPServer(temp_h5_dir)
        resources = handle_resources_list(server.h5_files)
        
        assert len(resources) >= 2
        
        # Step 2: Read root group of first file
        first_file_uri = resources[0]["uri"]
        root_info = handle_resources_read(first_file_uri)
        
        assert "contents" in root_info
        assert "Members" in root_info["contents"][0]["text"]
        
        # Step 3: List available tools
        tools = handle_tools_list()
        assert len(tools) == 1
        assert tools[0]["name"] == "read_dataset_slice"
        
        # Step 4: Use tool to read data
        # Find a dataset URI from one of our test files
        data_uri = build_uri(simple_h5_file, "/data")
        tool_result = handle_tools_call("read_dataset_slice", {
            "uri": data_uri,
            "slice_str": ":"
        })
        
        assert "isError" not in tool_result or not tool_result["isError"]
        data = json.loads(tool_result["content"][0]["text"])
        assert isinstance(data, list)
    
    def test_complex_file_exploration(self, complex_h5_file):
        """Test exploring a complex HDF5 file structure."""
        # Start with root group
        root_uri = build_uri(complex_h5_file, "/")
        root_info = handle_resources_read(root_uri)
        
        # Should contain references to groups and datasets
        root_content = root_info["contents"][0]["text"]
        assert "group1" in root_content
        assert "group2" in root_content
        
        # Explore a subgroup
        group1_uri = build_uri(complex_h5_file, "/group1")
        group1_info = handle_resources_read(group1_uri)
        
        group1_content = group1_info["contents"][0]["text"]
        assert "dataset_1d" in group1_content
        assert "dataset_2d" in group1_content
        
        # Read data from a dataset in the subgroup
        dataset_uri = build_uri(complex_h5_file, "/group1/dataset_1d")
        dataset_info = handle_resources_read(dataset_uri)
        
        dataset_content = dataset_info["contents"][0]["text"]
        assert "Shape:" in dataset_content
        assert "Data type:" in dataset_content
        
        # Actually read the data
        data_result = handle_tools_call("read_dataset_slice", {
            "uri": dataset_uri,
            "slice_str": ":"
        })
        
        assert "isError" not in data_result or not data_result["isError"]
        data = json.loads(data_result["content"][0]["text"])
        assert isinstance(data, list)
    
    def test_error_handling_workflow(self, temp_h5_dir):
        """Test error handling throughout the workflow."""
        server = H5MCPServer(temp_h5_dir)
        
        # Try to read non-existent resource
        bad_uri = build_uri("/nonexistent/file.h5", "/data")
        with pytest.raises(ValueError):
            handle_resources_read(bad_uri)
        
        # Try to use tool with bad arguments
        bad_tool_result = handle_tools_call("read_dataset_slice", {
            "uri": bad_uri,
            "slice_str": ":"
        })
        assert bad_tool_result["isError"] is True
        
        # Try unknown tool
        unknown_tool_result = handle_tools_call("unknown_tool", {})
        assert unknown_tool_result["isError"] is True


@pytest.mark.asyncio
class TestAsyncIntegration:
    """Test async integration patterns."""
    
    async def test_server_mock_run(self, temp_h5_dir):
        """Test server run method (mocked)."""
        server = H5MCPServer(temp_h5_dir)
        
        # Mock the stdio_server and app.run to avoid actual MCP protocol
        with patch('mcp_h5_server.server.stdio_server') as mock_stdio:
            with patch.object(server.app, 'run') as mock_run:
                mock_stdio.return_value.__aenter__.return_value = (AsyncMock(), AsyncMock())
                mock_run.return_value = None
                
                # This should not raise an exception
                await server.run()
                
                # Verify that the run method was called
                mock_run.assert_called_once()
