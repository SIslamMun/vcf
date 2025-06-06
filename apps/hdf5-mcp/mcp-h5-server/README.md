# MCP Server for HDF5

A Model Context Protocol (MCP) server that enables Large Language Model (LLM) agents to interact with HDF5 files through structured queries and data retrieval.

## Overview

This server acts as a bridge between LLM agents and HDF5 files, allowing users to perform exploratory data analysis by "chatting" with their HDF5 files. The server exposes HDF5 file structures as MCP Resources and provides tools for targeted data retrieval.

## Features

- **File Discovery**: Automatically scans directories for valid HDF5 files
- **Structure Exploration**: Browse HDF5 file hierarchies (groups, datasets, links)
- **Data Retrieval**: Extract specific slices of data from datasets
- **MCP Compliance**: Full compatibility with the Model Context Protocol

## Installation

This project uses [UV](https://github.com/astral-sh/uv) for dependency management.

```bash
# Install UV if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
cd mcp-h5-server
uv sync
```

## Usage

```bash
# Run the server with UV
uv run mcp-h5-server --directory /path/to/your/hdf5/files
```

## Development

### Running Tests

```bash
# Install with dev dependencies
uv sync --all-extras

# Run tests
uv run pytest
```

### Code Formatting

```bash
black mcp_h5_server/
isort mcp_h5_server/
```

## Architecture

The server follows a modular architecture:

- **URI Parsing**: Custom `h5://` URI scheme for addressing HDF5 objects
- **File Scanning**: Recursive discovery of valid HDF5 files
- **Data Access**: Safe and efficient HDF5 data retrieval
- **MCP Integration**: Full protocol compliance for seamless LLM integration

## License

MIT License - see LICENSE file for details.
