"""Pytest fixtures for testing the MCP H5 server."""
import pytest
import tempfile
import os
from pathlib import Path

try:
    import h5py
    import numpy as np
except ImportError:
    pytest.skip("h5py or numpy not available", allow_module_level=True)


@pytest.fixture
def tmp_h5_file():
    """Create a temporary HDF5 file with a well-structured test dataset.
    
    Yields:
        str: Path to the temporary HDF5 file
    """
    # Create a temporary file
    with tempfile.NamedTemporaryFile(suffix='.h5', delete=False) as tmp_file:
        file_path = tmp_file.name
    
    try:
        # Create HDF5 file structure
        with h5py.File(file_path, 'w') as f:
            # Root attributes
            f.attrs['title'] = 'Test HDF5 File'
            f.attrs['version'] = '1.0'
            
            # Create a group with attributes and members
            group1 = f.create_group('group1')
            group1.attrs['description'] = 'Test group 1'
            group1.attrs['created'] = '2025-06-06'
            
            # Create a nested group
            nested_group = group1.create_group('nested')
            nested_group.attrs['type'] = 'nested'
            
            # Create datasets with different shapes and types
            # 1D integer dataset
            data_1d = np.arange(100)
            dset_1d = group1.create_dataset('data_1d', data=data_1d)
            dset_1d.attrs['units'] = 'counts'
            dset_1d.attrs['description'] = '1D integer array'
            
            # 2D float dataset with chunks
            data_2d = np.random.rand(50, 20).astype(np.float32)
            dset_2d = group1.create_dataset('data_2d', data=data_2d, chunks=True)
            dset_2d.attrs['units'] = 'normalized'
            dset_2d.attrs['description'] = '2D float array'
            
            # 3D dataset
            data_3d = np.random.randint(0, 255, (10, 10, 3), dtype=np.uint8)
            dset_3d = nested_group.create_dataset('data_3d', data=data_3d)
            dset_3d.attrs['description'] = '3D image-like data'
            
            # String dataset
            string_data = np.array([b'hello', b'world', b'test'], dtype='S10')
            dset_str = f.create_dataset('strings', data=string_data)
            dset_str.attrs['encoding'] = 'utf-8'
            
            # Scalar dataset
            scalar_data = 42.5
            dset_scalar = f.create_dataset('scalar', data=scalar_data)
            dset_scalar.attrs['description'] = 'Scalar value'
        
        # Create another temporary file for external link
        with tempfile.NamedTemporaryFile(suffix='.h5', delete=False) as ext_tmp_file:
            ext_file_path = ext_tmp_file.name
        
        try:
            with h5py.File(ext_file_path, 'w') as ext_f:
                ext_f.create_dataset('external_data', data=np.arange(10))
            
            # Add links to the main file
            with h5py.File(file_path, 'a') as f:
                # Soft link
                f['soft_link'] = h5py.SoftLink('/group1/data_1d')
                
                # External link
                f['external_link'] = h5py.ExternalLink(ext_file_path, '/external_data')
            
            yield file_path
            
        finally:
            # Clean up external file
            if os.path.exists(ext_file_path):
                os.unlink(ext_file_path)
        
    finally:
        # Clean up main file
        if os.path.exists(file_path):
            os.unlink(file_path)


@pytest.fixture
def tmp_directory():
    """Create a temporary directory with multiple HDF5 files.
    
    Yields:
        str: Path to the temporary directory
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create subdirectories
        subdir1 = Path(tmp_dir) / 'subdir1'
        subdir2 = Path(tmp_dir) / 'subdir2'
        subdir1.mkdir()
        subdir2.mkdir()
        
        # Create valid HDF5 files
        for i, directory in enumerate([tmp_dir, subdir1, subdir2]):
            file_path = Path(directory) / f'test_{i}.h5'
            with h5py.File(file_path, 'w') as f:
                f.attrs['file_number'] = i
                f.create_dataset('data', data=np.arange(10 * (i + 1)))
        
        # Create a file with .hdf5 extension
        hdf5_file = Path(tmp_dir) / 'test.hdf5'
        with h5py.File(hdf5_file, 'w') as f:
            f.create_dataset('hdf5_data', data=np.ones(5))
        
        # Create some non-HDF5 files that should be ignored
        (Path(tmp_dir) / 'readme.txt').write_text('This is not an HDF5 file')
        (Path(tmp_dir) / 'data.csv').write_text('col1,col2\n1,2\n3,4')
        
        # Create a file with .h5 extension but invalid content
        invalid_h5 = Path(tmp_dir) / 'invalid.h5'
        invalid_h5.write_text('This is not a valid HDF5 file')
        
        yield tmp_dir


@pytest.fixture
def sample_uris():
    """Sample URIs for testing URI parsing."""
    return [
        'h5:///data/file.h5?path=/',
        'h5:///data/file.h5?path=/group1',
        'h5:///data/file.h5?path=/group1/dataset',
        'h5:///path/with%20spaces/file.h5?path=/data',
    ]


@pytest.fixture
def sample_slice_strings():
    """Sample slice strings for testing slice parsing."""
    return [
        '',  # Empty slice
        '5',  # Single integer
        ':',  # All elements
        '0:10',  # Start:stop
        '::2',  # Step only
        '1:10:2',  # Start:stop:step
        '0:10, :',  # Multi-dimensional
        '...',  # Ellipsis
        '0:10, ..., -1',  # Complex slice
    ]
