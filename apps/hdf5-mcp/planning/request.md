# Project Name
MCP Server for HDF5

## Project Description
An MCP server that allows scientists and developers to perform exploratory data analysis on HDF5 files using an LLM agent. The server will scan a directory of HDF5 files on startup, exposing their structure and metadata as MCP Resources. It will also provide a specific MCP Tool to enable the retrieval of raw data from datasets. The client-side LLM agent is responsible for all data analysis.

## Target Audience
Scientists and developers using LLM-powered assistants (e.g., in VS Code) for data exploration and analysis.

## Desired Features
### File Access & Discovery
- [ ] On initialization, the server scans a root directory (provided as a configuration argument).
- [ ] All valid HDF5 files found in the root directory are exposed as top-level resources.

### Resource Representation
- [ ] HDF5 files, groups, datasets, and links are exposed as MCP resources with a consistent URI structure.
- [ ] Reading a 'group' resource returns a list of its members (sub-groups and datasets) and its attributes.
- [ ] Reading a 'dataset' resource returns its core metadata (shape, dtype, size, chunks, attributes).
- [ ] Reading a 'link' resource returns its type (soft/external) and the target path it points to.

### Data Retrieval Tools
- [ ] Provide a tool (`read_dataset_slice`) that retrieves data from a dataset given a URI and a NumPy-style slice string.
    - [ ] The tool's input must include the dataset URI and a slice string.
    - [ ] The tool's output will be the retrieved data in a JSON-compatible format (e.g., nested lists).

## Design Requests
- [ ] Define a clear and hierarchical URI scheme for addressing HDF5 file contents.
    - [ ] Proposed: `h5://<file_path>?path=<internal_path>`
- [ ] Define the JSON Schema for the `read_dataset_slice` tool's input parameters (`uri`, `slice_str`).

## Other Notes
- [!] The "scan on init" approach may have performance implications for directories with a very large number of files or very large files.
- [!] The server will need a robust parser for the NumPy-style slice string provided to the tool. This is a potential source of complexity and errors.
- [ ] For V1, we assume all files can be comfortably handled in memory. A chunking/streaming strategy for reading large datasets is a future consideration.
