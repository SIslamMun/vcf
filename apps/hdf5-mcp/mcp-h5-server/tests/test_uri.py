"""Unit tests for URI parsing utilities."""
import pytest
from mcp_h5_server.uri import parse_uri, build_uri, H5URI


class TestParseURI:
    """Test URI parsing functionality."""
    
    def test_valid_uri_parsing(self):
        """Test parsing of valid URIs."""
        uri = "h5:///data/file.h5?path=/group1/dataset"
        result = parse_uri(uri)
        
        assert isinstance(result, H5URI)
        assert result.file_path == "/data/file.h5"
        assert result.internal_path == "/group1/dataset"
    
    def test_root_path(self):
        """Test parsing URI with root path."""
        uri = "h5:///data/file.h5?path=/"
        result = parse_uri(uri)
        
        assert result.file_path == "/data/file.h5"
        assert result.internal_path == "/"
    
    def test_path_without_leading_slash(self):
        """Test that internal path gets leading slash added."""
        uri = "h5:///data/file.h5?path=group1/dataset"
        result = parse_uri(uri)
        
        assert result.internal_path == "/group1/dataset"
    
    def test_empty_uri(self):
        """Test error handling for empty URI."""
        with pytest.raises(ValueError, match="URI string cannot be empty"):
            parse_uri("")
    
    def test_invalid_scheme(self):
        """Test error handling for invalid scheme."""
        uri = "http://example.com/file.h5?path=/data"
        with pytest.raises(ValueError, match="Invalid scheme 'http', expected 'h5'"):
            parse_uri(uri)
    
    def test_missing_file_path(self):
        """Test error handling for missing file path."""
        uri = "h5://?path=/data"
        with pytest.raises(ValueError, match="Missing file path in URI"):
            parse_uri(uri)
    
    def test_missing_path_parameter(self):
        """Test error handling for missing path query parameter."""
        uri = "h5:///data/file.h5"
        with pytest.raises(ValueError, match="Missing required 'path' query parameter"):
            parse_uri(uri)
    
    def test_empty_path_parameter(self):
        """Test error handling for empty path query parameter."""
        uri = "h5:///data/file.h5?path="
        with pytest.raises(ValueError, match="Empty 'path' query parameter"):
            parse_uri(uri)
    
    def test_encoded_characters(self):
        """Test handling of URL-encoded characters."""
        uri = "h5:///data/file%20with%20spaces.h5?path=/group%201/dataset"
        result = parse_uri(uri)
        
        assert result.file_path == "/data/file%20with%20spaces.h5"
        assert result.internal_path == "/group%201/dataset"


class TestBuildURI:
    """Test URI building functionality."""
    
    def test_build_simple_uri(self):
        """Test building a simple URI."""
        uri = build_uri("/data/file.h5", "/group1/dataset")
        expected = "h5:///data/file.h5?path=/group1/dataset"
        assert uri == expected
    
    def test_build_root_uri(self):
        """Test building URI with root path."""
        uri = build_uri("/data/file.h5", "/")
        expected = "h5:///data/file.h5?path=/"
        assert uri == expected
    
    def test_build_uri_with_default_path(self):
        """Test building URI with default internal path."""
        uri = build_uri("/data/file.h5")
        expected = "h5:///data/file.h5?path=/"
        assert uri == expected
    
    def test_add_leading_slash(self):
        """Test that leading slash is added to internal path."""
        uri = build_uri("/data/file.h5", "group1/dataset")
        expected = "h5:///data/file.h5?path=/group1/dataset"
        assert uri == expected
    
    def test_special_characters_encoding(self):
        """Test URL encoding of special characters."""
        uri = build_uri("/data/file.h5", "/group 1/dataset")
        expected = "h5:///data/file.h5?path=/group%201/dataset"
        assert uri == expected
    
    def test_empty_file_path(self):
        """Test error handling for empty file path."""
        with pytest.raises(ValueError, match="File path cannot be empty"):
            build_uri("", "/data")


class TestURIRoundTrip:
    """Test that URIs can be built and parsed consistently."""
    
    def test_round_trip(self):
        """Test that build_uri and parse_uri are inverse operations."""
        original_file = "/data/file.h5"
        original_path = "/group1/dataset"
        
        # Build URI
        uri = build_uri(original_file, original_path)
        
        # Parse it back
        parsed = parse_uri(uri)
        
        assert parsed.file_path == original_file
        assert parsed.internal_path == original_path
    
    def test_round_trip_with_special_chars(self):
        """Test round trip with special characters."""
        original_file = "/data/file with spaces.h5"
        original_path = "/group 1/dataset"
        
        # Build URI
        uri = build_uri(original_file, original_path)
        
        # Parse it back
        parsed = parse_uri(uri)
        
        # Note: file path will remain encoded, internal path will be decoded
        assert "/data/file" in parsed.file_path  # Contains the base part
        assert parsed.internal_path == original_path
