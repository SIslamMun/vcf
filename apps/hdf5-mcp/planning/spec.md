# MCP Server for HDF5 Technical Specification

## 1. System Overview

### Core Purpose and Value Proposition

This system is a Python-based server that implements the Model Context Protocol (MCP). Its purpose is to act as a bridge between Large Language Model (LLM) agents and HDF5 files. It allows a user, typically a scientist or developer, to perform exploratory data analysis by "chatting" with their HDF5 files via an LLM. The server makes HDF5 file structures discoverable as MCP Resources and provides an MCP Tool for targeted data retrieval, empowering the LLM to perform complex queries and analyses.

### Key Workflows

1.  **Initialization and Discovery:** The server is launched with a specified root directory. It scans this directory for all valid HDF5 files and makes them available as the initial set of MCP Resources.
2.  **Structural Introspection:** The client LLM agent requests to read resources (files, groups, datasets). The server responds with structured metadata, such as the children of a group or the shape and data type of a dataset. This allows the LLM to build a mental model of the HDF5 file's hierarchy.
3.  **Targeted Data Retrieval:** The LLM agent, having understood the structure, can request a specific slice of data from a dataset using a dedicated MCP Tool. This allows the agent to fetch only the data it needs for analysis, which it performs on the client side.

### System Architecture

The system is a single, standalone Python application designed to run as a command-line process. It communicates with a client over standard input/output (`stdio`) using the JSON-RPC 2.0 protocol, as specified by MCP.

*   **Transport Layer:** `stdio` for communication with the MCP client.
*   **Protocol Layer:** `mcp.py` library handles MCP message framing, request/response lifecycle, and object serialization.
*   **Application Layer:** This is the core of the project, containing the logic for handling MCP requests.
*   **Data Access Layer:** The `h5py` library is used for all interactions with the HDF5 files on the local filesystem.

The server is stateless; all information is read directly from the HDF5 files upon request. No database is required.

## 2. Project Structure

The project will be organized into a standard Python package structure to ensure modularity and testability.

```
mcp-h5-server/
├── mcp_h5_server/
│   ├── __init__.py
│   ├── __main__.py          # CLI entry point, argument parsing
│   ├── server.py            # Main MCP Server application class
│   ├── handlers.py          # Implementation of MCP request handlers
│   ├── h5_utils.py          # Low-level HDF5 interaction logic
│   ├── models.py            # Pydantic models for data structures and validation
│   └── uri.py               # URI parsing and building utilities
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Pytest fixtures (e.g., temporary HDF5 files)
│   ├── test_handlers.py     # Integration tests for MCP handlers
│   ├── test_h5_utils.py     # Unit tests for HDF5 utilities
│   └── test_uri.py          # Unit tests for URI parsing
├── pyproject.toml           # Project dependencies and metadata
└── README.md                # Documentation
```

## 3. Feature Specification

### 3.1. File System Scanning and Initialization

*   **User Story:** As a developer, I want to start the server and point it to a directory, so that all valid HDF5 files within that directory become available for querying.
*   **Requirements:**
    *   The server must accept a command-line argument, `--directory`, which specifies the root directory to scan.
    *   The server must recursively scan the specified directory.
    *   Files with extensions `.h5` and `.hdf5` should be considered for inclusion.
    *   The server must verify that each candidate file is a valid, readable HDF5 file. Invalid or unreadable files should be ignored with a warning log message.
*   **Implementation Steps:**
    1.  In `__main__.py`, use the `argparse` module to define and parse the `--directory` argument.
    2.  In `h5_utils.py`, create a function `scan_for_h5_files(root_dir: str) -> list[str]`.
    3.  This function will use `os.walk` to traverse the `root_dir`.
    4.  For each file found, check if its extension is in `['.h5', '.hdf5']`.
    5.  For each matching file, wrap a `h5py.File(file_path, 'r')` call in a `try...except Exception` block. If it succeeds, the file is valid; add its absolute path to a list. If it fails, log a warning and continue.
    6.  The main `Server` class in `server.py` will call this function on initialization to populate its list of available files.
*   **Error Handling:**
    *   If the provided directory does not exist, the application should exit gracefully with an error message.
    *   If a file cannot be opened (e.g., corrupt, permissions error), it should be skipped, and a warning should be logged to `stderr`.

### 3.2. MCP Resource Representation

*   **User Story:** As an LLM agent, I want to inspect the structure of an HDF5 file by reading different resources, so that I can understand its contents and metadata.
*   **Requirements:**
    *   The server must implement the `resources/list` and `resources/read` MCP requests.
    *   A URI scheme `h5://<absolute_file_path>?path=<internal_h5_path>` will be used.
    *   Reading a group resource must return its attributes and a list of its member names (datasets and sub-groups).
    *   Reading a dataset resource must return its attributes and metadata (shape, dtype, size, chunks).
    *   Reading a link resource must return its type (`SoftLink` or `ExternalLink`) and its target.
*   **Implementation Steps:**
    1.  **URI Handling (`uri.py`):**
        *   Create a `H5URI` dataclass with `file_path: str` and `internal_path: str` attributes.
        *   Create a `parse_uri(uri_str: str) -> H5URI` function that uses `urllib.parse` to split the URI into its components and populates the dataclass. It must perform validation.
    2.  **`resources/list` Handler (`handlers.py`):**
        *   This handler will iterate through the list of file paths discovered at startup.
        *   For each file path, it will construct a `mcp.Resource` object with `uri=f"h5://{file_path}?path=/"` and `name=os.path.basename(file_path)`.
        *   It returns a list of these `mcp.Resource` objects.
    3.  **`resources/read` Handler (`handlers.py`):**
        *   The handler receives a `uri` parameter. It calls `uri.parse_uri` to deconstruct it.
        *   It calls a helper function `h5_utils.get_object_info(file_path, internal_path)`.
        *   **`get_object_info` (`h5_utils.py`):**
            *   Opens the HDF5 file: `with h5py.File(file_path, 'r') as f:`.
            *   Uses `f.get(internal_path, getlink=True)` to check if the path points to a link.
            *   If it's a `h5py.SoftLink` or `h5py.ExternalLink`, return a dictionary with its type and target.
            *   If not a link, get the object: `obj = f[internal_path]`.
            *   Check the object's type: `isinstance(obj, h5py.Group)` or `h5py.Dataset`.
            *   Based on the type, populate a dictionary with the required metadata (keys, attributes, shape, dtype, etc.). `obj.attrs` can be converted to a dict via `dict(obj.attrs)`.
        *   The handler returns the resulting dictionary as the `contents` of the MCP response.
*   **Error Handling:**
    *   If `resources/read` receives a malformed URI, return a `ParseError`.
    *   If the file path in the URI does not exist or is not a valid HDF5 file, return a `MethodNotFound` error.
    *   If the internal path does not exist within the HDF5 file, return a `MethodNotFound` error.

### 3.3. Data Retrieval Tool (`read_dataset_slice`)

*   **User Story:** As an LLM agent, I want to retrieve a specific slice of data from a dataset, so I can perform calculations or analysis on it.
*   **Requirements:**
    *   The server must expose a single MCP Tool named `read_dataset_slice`.
    *   The tool's input must be a JSON object with two required fields: `uri` (string) and `slice_str` (string).
    *   The `slice_str` must be safely parsed to prevent arbitrary code execution.
    *   The tool must return the sliced data in a JSON-compatible format (nested lists).
*   **Implementation Steps:**
    1.  **Tool Definition (`server.py`):**
        *   When initializing the MCP `Server`, define the `tools` capability. The `tools/list` handler will return a single `mcp.Tool` definition.
        *   The `inputSchema` for the tool will be defined as a JSON Schema object:
            ```json
            {
              "type": "object",
              "properties": {
                "uri": { "type": "string", "description": "The URI of the dataset to slice." },
                "slice_str": { "type": "string", "description": "A NumPy-style slice string (e.g., '0:10, :')." }
              },
              "required": ["uri", "slice_str"]
            }
            ```
    2.  **`tools/call` Handler (`handlers.py`):**
        *   The handler validates that the requested tool name is `read_dataset_slice`.
        *   It parses the `uri` and `slice_str` from the input arguments.
        *   It calls `h5_utils.parse_slice_string(slice_str)` to get a valid slice object.
        *   It calls `h5_utils.read_dataset_slice(file_path, internal_path, slice_obj)`.
        *   The result, a NumPy array, is converted to a list using `.tolist()`.
        *   The handler returns the list as the tool's result content.
    3.  **Slice Parser (`h5_utils.py`):**
        *   Create `parse_slice_string(slice_str: str) -> tuple`.
        *   **This is a critical security-sensitive function.** It must **NOT** use `eval`.
        *   It will split the `slice_str` by commas. For each part, it will parse it into a `slice` object or an integer. It should handle `...` (Ellipsis) correctly. A regex can be used to validate the format of each part (e.g., `\s*(-?\d+)?\s*:\s*(-?\d+)?\s*(:\s*(-?\d+)?)?\s*`).
        *   If parsing fails at any point, it must raise a `ValueError`.
*   **Error Handling:**
    *   If the tool name is unknown, return a `MethodNotFound` error.
    *   If input parameters are missing or invalid, return an `InvalidParams` error.
    *   If `slice_str` is malformed, the tool should return an `isError: true` result with a descriptive error message.
    *   If the URI points to a group instead of a dataset, return an `isError: true` result.
    *   If the slice is out of bounds for the dataset's shape, `h5py` will raise an `IndexError`. Catch this and return an `isError: true` result.

## 4. Database Schema

Not applicable, as this project is stateless and does not use a database.

## 5. Server Actions

This section describes the core interactions with the HDF5 file system.

### 5.1. HDF5 Actions (`h5_utils.py`)

*   **`scan_for_h5_files(root_dir: str) -> list[str]`**
    *   **Description:** Recursively finds all valid HDF5 files in a directory.
    *   **Input:** `root_dir` (string path).
    *   **Return:** A list of absolute string paths to valid HDF5 files.
*   **`get_object_info(file_path: str, internal_path: str) -> dict`**
    *   **Description:** Retrieves metadata for a specific object within an HDF5 file.
    *   **Input:** `file_path`, `internal_path` (strings).
    *   **Return:** A dictionary containing the object's metadata. The structure of the dictionary depends on the object type (Group, Dataset, or Link).
*   **`parse_slice_string(slice_str: str) -> tuple`**
    *   **Description:** Safely parses a string representation of a NumPy slice into a tuple of `slice` objects and integers that `h5py` can use.
    *   **Input:** `slice_str` (e.g., `"0:10, ..."`).
    *   **Return:** A tuple suitable for `h5py` indexing (e.g., `(slice(0, 10, None), Ellipsis)`).
*   **`read_dataset_slice(file_path: str, internal_path: str, slice_obj: tuple) -> numpy.ndarray`**
    *   **Description:** Reads a slice of data from a specified dataset.
    *   **Input:** `file_path`, `internal_path`, and the `slice_obj` tuple from `parse_slice_string`.
    *   **Return:** A NumPy array containing the requested data.

## 6. Component Architecture

### 6.1. Server Components

*   **`Server` (`server.py`):**
    *   **Responsibility:** The main application class. Initializes the MCP session, holds the list of discovered files, and registers the MCP request handlers from `handlers.py`.
*   **`MCP Handlers` (`handlers.py`):**
    *   **Responsibility:** A collection of functions, each handling a specific MCP request (`resources/list`, `resources/read`, `tools/call`). They orchestrate calls to the utility components (`URIParser`, `H5Accessor`).
*   **`URIParser` (`uri.py`):**
    *   **Responsibility:** Provides functions to parse and validate the `h5://` URI scheme. Decouples URI logic from the handlers.
*   **`H5Accessor` (`h5_utils.py`):**
    *   **Responsibility:** A module of functions that encapsulates all direct `h5py` library calls. It handles file opening/closing, object inspection, and data reading. This isolates the core application logic from the specifics of the `h5py` API.
*   **`SliceParser` (`h5_utils.py`'s `parse_slice_string` function):**
    *   **Responsibility:** Safely parses the user-provided slice string. This is a critical component for security and stability.

## 7. Data Flow

The data flow for a `tools/call` request to `read_dataset_slice` is as follows:

1.  **Client -> Server:** The MCP client sends a JSON-RPC request over `stdio`:
    ```json
    {
      "jsonrpc": "2.0",
      "method": "tools/call",
      "params": {
        "name": "read_dataset_slice",
        "arguments": {
          "uri": "h5:///path/to/my_file.h5?path=/data/temp",
          "slice_str": "5:15"
        }
      },
      "id": 123
    }
    ```
2.  **Server (MCP Layer):** The `mcp.py` library receives the string, parses it into a request object, and invokes the registered `tools/call` handler.
3.  **Server (Handler):** The `handle_tools_call` function in `handlers.py` is executed.
4.  **URI Parsing:** The handler passes the `uri` string to `uri.parse_uri`, which returns `H5URI(file_path='/path/to/my_file.h5', internal_path='/data/temp')`.
5.  **Slice Parsing:** The handler passes the `slice_str` to `h5_utils.parse_slice_string`, which returns `(slice(5, 15, None),)`.
6.  **Data Access:** The handler calls `h5_utils.read_dataset_slice` with the file path, internal path, and slice object. This function opens the HDF5 file, accesses the dataset, reads the slice, and returns a NumPy array.
7.  **Serialization:** The handler receives the NumPy array and calls `.tolist()` to convert it into a JSON-serializable list of lists/numbers.
8.  **Server -> Client:** The handler returns the list. The `mcp.py` library constructs the final JSON-RPC response and writes it to `stdout`:
    ```json
    {
      "jsonrpc": "2.0",
      "result": {
        "content": [ { "type": "text", "text": "[...data...]" } ] // Or however the tool result is structured
      },
      "id": 123
    }
    ```

## 8. Testing

A simple testing is essential, with a focus on the utility functions that contain the most complex logic. End to end tests will be implemented to ensure the server behaves correctly with a real HDF5 file.


