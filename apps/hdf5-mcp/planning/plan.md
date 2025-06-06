# Implementation Plan

## Section 1: Project Foundation & Core Utilities

- [ ] Step 1: Initialize Project Structure and Dependencies
  - **Task**: Create the project directory structure and the `pyproject.toml` file to define project metadata and dependencies.
  - **Files**:
    - `mcp-h5-server/pyproject.toml`: Define project name, version, and dependencies (`h5py`, `numpy`, `mcp.py` - assuming it's a local library or on PyPI, `pytest`).
    - `mcp-h5-server/mcp_h5_server/__init__.py`: Create an empty init file.
    - `mcp-h5-server/tests/__init__.py`: Create an empty init file.
    - `mcp-h5-server/README.md`: Create a basic README file.
  - **Step Dependencies**: None
  - **User Instructions**: Run `pip install -e .[test]` (assuming a test extra is defined in `pyproject.toml`) to install the project in editable mode with its testing dependencies.

- [ ] Step 2: Implement Command-Line Interface
  - **Task**: Create the main entry point for the application, responsible for parsing the `--directory` command-line argument.
  - **Files**:
    - `mcp_h5_server/__main__.py`: Use the `argparse` module to create a parser that requires a `--directory` argument. For now, it can just print the provided directory path. Add basic error handling for when the directory doesn't exist.
  - **Step Dependencies**: Step 1

- [ ] Step 3: Implement URI Parsing Utilities
  - **Task**: Create the self-contained module for parsing and validating the custom `h5://` URI scheme.
  - **Files**:
    - `mcp_h5_server/uri.py`:
      - Create a `H5URI` dataclass with `file_path: str` and `internal_path: str` attributes.
      - Implement the `parse_uri(uri_str: str) -> H5URI` function using `urllib.parse`. It should validate that the scheme is `h5`, the netloc (file path) is present, and the `path` query parameter exists. Raise `ValueError` on failure.
  - **Step Dependencies**: Step 1

- [ ] Step 4: Implement HDF5 File System Scanner
  - **Task**: Create the utility function to scan a directory and identify all valid HDF5 files.
  - **Files**:
    - `mcp_h5_server/h5_utils.py`:
      - Implement `scan_for_h5_files(root_dir: str) -> list[str]`.
      - This function will use `os.walk` to find files ending in `.h5` or `.hdf5`.
      - For each found file, it will attempt to open it with `h5py.File(file_path, 'r')` inside a `try...except` block to validate it. Log a warning to `stderr` if a file is invalid and skip it.
      - Return a list of absolute paths to the valid files.
  - **Step Dependencies**: Step 1

- [ ] Step 5: Implement Secure Slice String Parser
  - **Task**: Implement the security-critical function to parse a NumPy-style slice string into a tuple of slice objects without using `eval`.
  - **Files**:
    - `mcp_h5_server/h5_utils.py`:
      - Implement `parse_slice_string(slice_str: str) -> tuple`.
      - The function should first check for an empty string, which corresponds to `()`.
      - It should handle the `...` (Ellipsis) object.
      - For each comma-separated component, use regex (`re` module) to parse integers and slice components (`start:stop:step`).
      - Construct a tuple of `slice` objects, `int`s, and `Ellipsis`.
      - Raise `ValueError` for any malformed component.
  - **Step Dependencies**: Step 1

## Section 2: HDF5 Data Access and Models

- [ ] Step 6: Implement HDF5 Object Inspector
  - **Task**: Create the utility function that inspects an object within an HDF5 file and returns its metadata.
  - **Files**:
    - `mcp_h5_server/h5_utils.py`:
      - Implement `get_object_info(file_path: str, internal_path: str) -> dict`.
      - The function will open the specified file.
      - It must use `f.get(internal_path, getlink=True)` to correctly identify links.
      - If the object is a `h5py.SoftLink` or `h5py.ExternalLink`, return a dict like `{'type': 'SoftLink', 'target': link.path}`.
      - If it's a `h5py.Group`, return a dict with its attributes (`dict(obj.attrs)`) and members (`list(obj.keys())`).
      - If it's a `h5py.Dataset`, return a dict with its attributes, `shape`, `dtype` (as a string), `size`, and `chunks`.
  - **Step Dependencies**: Step 4

- [ ] Step 7: Implement HDF5 Dataset Reader
  - **Task**: Create the utility function that reads a slice from a dataset using a parsed slice object.
  - **Files**:
    - `mcp_h5_server/h5_utils.py`:
      - Implement `read_dataset_slice(file_path: str, internal_path: str, slice_obj: tuple) -> list`.
      - The function will open the file, access the dataset at `internal_path`, and apply the `slice_obj` to it (e.g., `dset[slice_obj]`).
      - It will convert the resulting NumPy array to a JSON-serializable list using `.tolist()`.
      - It should handle `IndexError` if the slice is out of bounds and raise a `ValueError`.
  - **Step Dependencies**: Step 5

- [ ] Step 8: Define Data Models
  - **Task**: Create Pydantic models to represent the structured data returned by the handlers. This ensures data consistency and provides clear contracts.
  - **Files**:
    - `mcp_h5_server/models.py`:
      - `GroupInfo(BaseModel)`: with fields for `attributes` and `members`.
      - `DatasetInfo(BaseModel)`: with fields for `attributes`, `shape`, `dtype`, `size`, `chunks`.
      - `LinkInfo(BaseModel)`: with fields for `type` and `target`.
      - `ToolInput(BaseModel)`: with fields `uri: str` and `slice_str: str`.
  - **Step Dependencies**: Step 1

## Section 3: MCP Server and Handlers

- [ ] Step 9: Implement MCP Resource Handlers
  - **Task**: Implement the functions that will handle the `resources/list` and `resources/read` requests.
  - **Files**:
    - `mcp_h5_server/handlers.py`:
      - `handle_resources_list(file_paths: list[str]) -> list[dict]`: Takes the list of discovered files and returns a list of MCP Resource dictionaries.
      - `handle_resources_read(uri: str) -> dict`: Uses `uri.parse_uri` and `h5_utils.get_object_info` to fetch metadata and returns it in the MCP `contents` format. This function should return a Pydantic model from `models.py`.
  - **Step Dependencies**: Step 3, Step 6, Step 8

- [ ] Step 10: Implement MCP Tool Handlers
  - **Task**: Implement the functions that will handle the `tools/list` and `tools/call` requests.
  - **Files**:
    - `mcp_h5_server/handlers.py`:
      - `handle_tools_list() -> list[dict]`: Returns a static list containing the single JSON Schema definition for the `read_dataset_slice` tool.
      - `handle_tools_call(name: str, arguments: dict) -> dict`:
        - Validates the tool `name`.
        - Parses `arguments` using the `ToolInput` Pydantic model.
        - Orchestrates calls to `uri.parse_uri`, `h5_utils.parse_slice_string`, and `h5_utils.read_dataset_slice`.
        - Catches potential `ValueError` exceptions from the utilities and formats them into an `isError: true` MCP response.
        - Returns the sliced data in the MCP result format.
  - **Step Dependencies**: Step 7, Step 8, Step 9

- [ ] Step 11: Implement the Main Server Class
  - **Task**: Create the main server class that ties all the components together, registers handlers, and manages the MCP session.
  - **Files**:
    - `mcp_h5_server/server.py`:
      - Create a class `H5MCPTCPServer`.
      - The `__init__` method will take the `root_dir` as an argument, call `scan_for_h5_files`, and store the result.
      - It will instantiate an MCP `Server` object (from the `mcp.py` library).
      - It will register the handler functions from `handlers.py` with the MCP `Server` instance (e.g., `mcp_server.add_request_handler("resources/list", ...)`)
      - It will have a `run()` method to start the server's main communication loop.
  - **Step Dependencies**: Step 10

- [ ] Step 12: Final Integration in CLI
  - **Task**: Update the main entry point to instantiate and run the `H5MCPTCPServer`.
  - **Files**:
    - `mcp_h5_server/__main__.py`:
      - After parsing the `--directory` argument, instantiate `H5MCPTCPServer(root_dir=args.directory)`.
      - Call the `server.run()` method to start the application.
  - **Step Dependencies**: Step 11

## Section 4: Testing

- [ ] Step 13: Create Test Fixtures
  - **Task**: Set up the Pytest `conftest.py` with a fixture that creates a temporary, well-structured HDF5 file for testing.
  - **Files**:
    - `tests/conftest.py`:
      - Create a fixture `tmp_h5_file`.
      - Inside the fixture, use `h5py.File` to create a file with a known structure: at least one nested group, a dataset, attributes on both the group and dataset, a soft link, and an external link (pointing to another temp file).
      - Yield the path to this file.
  - **Step Dependencies**: Step 1

- [ ] Step 14: Write Unit Tests for Utilities
  - **Task**: Write comprehensive unit tests for the URI and H5 utility functions.
  - **Files**:
    - `tests/test_uri.py`: Test `parse_uri` with valid and invalid inputs.
    - `tests/test_h5_utils.py`:
      - Test `scan_for_h5_files` on a temporary directory structure.
      - Test `get_object_info` for each object type (group, dataset, link) using the `tmp_h5_file` fixture.
      - Write extensive tests for `parse_slice_string` covering valid, invalid, and edge cases.
      - Test `read_dataset_slice` with valid and out-of-bounds slices.
  - **Step Dependencies**: Step 7, Step 13

- [ ] Step 15: Write Integration Tests for Handlers
  - **Task**: Write integration tests for the MCP handlers to ensure they correctly process requests and interact with the utility modules.
  - **Files**:
    - `tests/test_handlers.py`:
      - Test `handle_resources_list` and assert the output structure.
      - Test `handle_resources_read` for each object type in the `tmp_h5_file` fixture.
      - Test `handle_tools_call` with valid inputs and assert the correctness of the returned data.
      - Test `handle_tools_call` with invalid inputs (bad URI, bad slice string, wrong object type) and assert that the `isError: true` response is correctly formatted.
  - **Step Dependencies**: Step 10, Step 14

# Summary of Approach

The implementation plan follows a logical, bottom-up progression. It starts by building a solid foundation of self-contained utility modules (`uri.py`, `h5_utils.py`) and immediately writing tests to validate their behavior. This de-risks the most complex parts of the application—specifically the secure slice string parser—early in the process.

Once the core logic for file system interaction and data manipulation is in place and tested, the plan moves up the stack to the MCP-specific layer. The handlers are implemented using the proven utility functions, and finally, the main server class integrates everything into a runnable application.

This sequential approach, with testing integrated at each stage, ensures that every component is reliable before being used by the next, leading to a more robust and maintainable final product. Each step is designed to be an atomic unit of work, suitable for a single code generation cycle.
