"""Unit tests for HDF5 utilities."""
import pytest
import os
import tempfile
from pathlib import Path
import numpy as np

from mcp_h5_server.h5_utils import (
    scan_for_h5_files,
    get_object_info,
    parse_slice_string,
    read_dataset_slice,
    _is_integer
)


class TestScanForH5Files:
    """Test HDF5 file scanning functionality."""
    
    def test_scan_existing_directory(self, tmp_directory):
        """Test scanning a directory with HDF5 files."""
        files = scan_for_h5_files(tmp_directory)
        
        # Should find .h5 and .hdf5 files but not invalid ones
        assert len(files) >= 4  # test_0.h5, test_1.h5, test_2.h5, test.hdf5
        
        # All returned paths should be absolute
        for file_path in files:
            assert os.path.isabs(file_path)
            assert file_path.endswith(('.h5', '.hdf5'))
            assert os.path.exists(file_path)
    
    def test_scan_nonexistent_directory(self):
        """Test error handling for nonexistent directory."""
        with pytest.raises(ValueError, match="Directory does not exist"):
            scan_for_h5_files("/nonexistent/directory")
    
    def test_scan_file_instead_of_directory(self, tmp_h5_file):
        """Test error handling when path is a file, not directory."""
        with pytest.raises(ValueError, match="Path is not a directory"):
            scan_for_h5_files(tmp_h5_file)
    
    def test_scan_empty_directory(self):
        """Test scanning an empty directory."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            files = scan_for_h5_files(tmp_dir)
            assert files == []


class TestGetObjectInfo:
    """Test HDF5 object inspection functionality."""
    
    def test_get_root_group_info(self, tmp_h5_file):
        """Test getting info for root group."""
        info = get_object_info(tmp_h5_file, "/")
        
        assert info["type"] == "Group"
        assert "attributes" in info
        assert "members" in info
        
        # Check some expected members
        members = info["members"]
        assert "group1" in members
        assert "strings" in members
        assert "scalar" in members
    
    def test_get_group_info(self, tmp_h5_file):
        """Test getting info for a group."""
        info = get_object_info(tmp_h5_file, "/group1")
        
        assert info["type"] == "Group"
        assert info["attributes"]["description"] == "Test group 1"
        
        members = info["members"]
        assert "data_1d" in members
        assert "data_2d" in members
        assert "nested" in members
    
    def test_get_dataset_info(self, tmp_h5_file):
        """Test getting info for a dataset."""
        info = get_object_info(tmp_h5_file, "/group1/data_1d")
        
        assert info["type"] == "Dataset"
        assert info["shape"] == (100,)
        assert "int" in info["dtype"]  # Should be some kind of integer
        assert info["size"] == 100
        assert info["attributes"]["units"] == "counts"
    
    def test_get_2d_dataset_info(self, tmp_h5_file):
        """Test getting info for a 2D dataset."""
        info = get_object_info(tmp_h5_file, "/group1/data_2d")
        
        assert info["type"] == "Dataset"
        assert info["shape"] == (50, 20)
        assert "float" in info["dtype"]
        assert info["size"] == 1000
        assert info["chunks"] is not None  # Should be chunked
    
    def test_get_soft_link_info(self, tmp_h5_file):
        """Test getting info for a soft link."""
        info = get_object_info(tmp_h5_file, "/soft_link")
        
        assert info["type"] == "SoftLink"
        assert info["target"] == "/group1/data_1d"
    
    def test_get_external_link_info(self, tmp_h5_file):
        """Test getting info for an external link."""
        info = get_object_info(tmp_h5_file, "/external_link")
        
        assert info["type"] == "ExternalLink"
        assert "external_data" in info["target"]
    
    def test_nonexistent_file(self):
        """Test error handling for nonexistent file."""
        with pytest.raises(ValueError, match="File does not exist"):
            get_object_info("/nonexistent/file.h5", "/")
    
    def test_nonexistent_path(self, tmp_h5_file):
        """Test error handling for nonexistent internal path."""
        with pytest.raises(ValueError, match="not found in file"):
            get_object_info(tmp_h5_file, "/nonexistent/path")


class TestParseSliceString:
    """Test slice string parsing functionality."""
    
    def test_empty_slice(self):
        """Test parsing empty slice string."""
        result = parse_slice_string("")
        assert result == ()
    
    def test_single_integer(self):
        """Test parsing single integer."""
        result = parse_slice_string("5")
        assert result == (5,)
    
    def test_negative_integer(self):
        """Test parsing negative integer."""
        result = parse_slice_string("-1")
        assert result == (-1,)
    
    def test_simple_slice(self):
        """Test parsing simple slice."""
        result = parse_slice_string("0:10")
        assert result == (slice(0, 10, None),)
    
    def test_slice_with_step(self):
        """Test parsing slice with step."""
        result = parse_slice_string("0:10:2")
        assert result == (slice(0, 10, 2),)
    
    def test_open_ended_slices(self):
        """Test parsing open-ended slices."""
        result = parse_slice_string(":10")
        assert result == (slice(None, 10, None),)
        
        result = parse_slice_string("5:")
        assert result == (slice(5, None, None),)
        
        result = parse_slice_string(":")
        assert result == (slice(None, None, None),)
    
    def test_ellipsis(self):
        """Test parsing ellipsis."""
        result = parse_slice_string("...")
        assert result == (Ellipsis,)
    
    def test_multidimensional_slice(self):
        """Test parsing multidimensional slice."""
        result = parse_slice_string("0:10, :, 5")
        expected = (slice(0, 10, None), slice(None, None, None), 5)
        assert result == expected
    
    def test_complex_slice(self):
        """Test parsing complex slice with ellipsis."""
        result = parse_slice_string("0:10, ..., -1")
        expected = (slice(0, 10, None), Ellipsis, -1)
        assert result == expected
    
    def test_invalid_slice_string(self):
        """Test error handling for invalid slice strings."""
        with pytest.raises(ValueError, match="Invalid slice component"):
            parse_slice_string("abc")
        
        with pytest.raises(ValueError, match="Invalid slice value"):
            parse_slice_string("0:abc")
        
        with pytest.raises(ValueError, match="Too many ':' in slice component"):
            parse_slice_string("0:1:2:3")
        
        with pytest.raises(ValueError, match="Empty slice component"):
            parse_slice_string("0:10, , 5")
    
    def test_whitespace_handling(self):
        """Test that whitespace is handled correctly."""
        result = parse_slice_string("  0 : 10  ,  :  ,  5  ")
        expected = (slice(0, 10, None), slice(None, None, None), 5)
        assert result == expected


class TestIsInteger:
    """Test the _is_integer utility function."""
    
    def test_valid_integers(self):
        """Test recognition of valid integers."""
        assert _is_integer("0")
        assert _is_integer("123")
        assert _is_integer("-456")
        assert _is_integer("  789  ")  # With whitespace
    
    def test_invalid_integers(self):
        """Test rejection of invalid integers."""
        assert not _is_integer("")
        assert not _is_integer("abc")
        assert not _is_integer("12.34")
        assert not _is_integer("12a")
        assert not _is_integer("a12")


class TestReadDatasetSlice:
    """Test dataset slice reading functionality."""
    
    def test_read_full_dataset(self, tmp_h5_file):
        """Test reading entire dataset."""
        slice_obj = ()  # Empty slice = read all
        data = read_dataset_slice(tmp_h5_file, "/group1/data_1d", slice_obj)
        
        assert isinstance(data, list)
        assert len(data) == 100
        assert data[0] == 0
        assert data[99] == 99
    
    def test_read_slice(self, tmp_h5_file):
        """Test reading a slice of data."""
        slice_obj = (slice(10, 20, None),)
        data = read_dataset_slice(tmp_h5_file, "/group1/data_1d", slice_obj)
        
        assert isinstance(data, list)
        assert len(data) == 10
        assert data[0] == 10
        assert data[9] == 19
    
    def test_read_2d_slice(self, tmp_h5_file):
        """Test reading a 2D slice."""
        slice_obj = (slice(0, 5, None), slice(0, 3, None))
        data = read_dataset_slice(tmp_h5_file, "/group1/data_2d", slice_obj)
        
        assert isinstance(data, list)
        assert len(data) == 5  # 5 rows
        assert len(data[0]) == 3  # 3 columns
    
    def test_read_single_element(self, tmp_h5_file):
        """Test reading a single element."""
        slice_obj = (10,)
        data = read_dataset_slice(tmp_h5_file, "/group1/data_1d", slice_obj)
        
        # Single element should be returned as scalar
        assert data == 10
    
    def test_read_scalar_dataset(self, tmp_h5_file):
        """Test reading a scalar dataset."""
        slice_obj = ()
        data = read_dataset_slice(tmp_h5_file, "/scalar", slice_obj)
        
        assert data == 42.5
    
    def test_out_of_bounds_slice(self, tmp_h5_file):
        """Test error handling for out-of-bounds slice."""
        slice_obj = (slice(0, 1000, None),)  # Dataset only has 100 elements
        
        # This should not raise an error - HDF5/NumPy handles this gracefully
        data = read_dataset_slice(tmp_h5_file, "/group1/data_1d", slice_obj)
        assert len(data) == 100  # Should return available data
    
    def test_read_nonexistent_dataset(self, tmp_h5_file):
        """Test error handling for nonexistent dataset."""
        slice_obj = ()
        with pytest.raises(ValueError, match="not found in file"):
            read_dataset_slice(tmp_h5_file, "/nonexistent", slice_obj)
    
    def test_read_group_instead_of_dataset(self, tmp_h5_file):
        """Test error handling when trying to read a group as dataset."""
        slice_obj = ()
        with pytest.raises(ValueError, match="is not a dataset"):
            read_dataset_slice(tmp_h5_file, "/group1", slice_obj)
    
    def test_read_nonexistent_file(self):
        """Test error handling for nonexistent file."""
        slice_obj = ()
        with pytest.raises(ValueError, match="File does not exist"):
            read_dataset_slice("/nonexistent/file.h5", "/data", slice_obj)
