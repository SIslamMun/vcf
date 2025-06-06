"""Command-line interface for the MCP HDF5 server."""

import argparse
import sys
import os
from pathlib import Path


def create_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="MCP Server for HDF5 files",
        prog="mcp-h5-server"
    )
    parser.add_argument(
        "--directory",
        type=str,
        required=True,
        help="Root directory to scan for HDF5 files"
    )
    return parser


def validate_directory(directory_path: str) -> Path:
    """Validate that the provided directory exists and is accessible."""
    path = Path(directory_path).resolve()
    
    if not path.exists():
        print(f"Error: Directory '{directory_path}' does not exist.", file=sys.stderr)
        sys.exit(1)
    
    if not path.is_dir():
        print(f"Error: '{directory_path}' is not a directory.", file=sys.stderr)
        sys.exit(1)
    
    if not os.access(path, os.R_OK):
        print(f"Error: Directory '{directory_path}' is not readable.", file=sys.stderr)
        sys.exit(1)
    
    return path


def main() -> None:
    """Main entry point for the application."""
    import asyncio
    from .server import H5MCPServer
    
    parser = create_parser()
    args = parser.parse_args()
    
    # Validate the directory argument
    directory_path = validate_directory(args.directory)
    
    try:
        # Initialize and run the MCP server
        server = H5MCPServer(str(directory_path))
        asyncio.run(server.run())
    except KeyboardInterrupt:
        print("\nServer stopped by user.", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
