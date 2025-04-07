#!/usr/bin/env python
"""
UltimateCoder
A FastMCP server that exposes comprehensive file-system operations along with
advanced coding functionalities using MCP core concepts: Resources, Prompts, and Context.
Designed for advanced coding workflows, precise code modifications, process management,
code searching/editing, intelligent block replacement, linting, and static analysis.
"""

import os
import subprocess
import shutil
import base64
import mimetypes
import difflib
import tempfile
import json
import re
import fnmatch
from datetime import datetime
from typing import Any, Dict, List, Union
from fastmcp import FastMCP, Context

# ---------------------------------------------------------------------
# Error Message Templates for Patch/Block Replacement Failures
# ---------------------------------------------------------------------

no_match_error = (
    "UnifiedDiffNoMatch: hunk failed to apply!\n\n"
    "{path} does not contain the exact context required by the patch.\n"
    "The hunk needed {num_lines} contiguous lines:\n"
    "```\n{original}\n```\n"
    "Ensure that the file has not been modified and that the context is exact (100% match)."
)

not_unique_error = (
    "UnifiedDiffNotUnique: hunk failed to apply!\n\n"
    "{path} contains multiple occurrences of the context.\n"
    "The patch must apply uniquely. The hunk needed {num_lines} contiguous lines:\n"
    "```\n{original}\n```\n"
    "Please add additional context so the match is unique."
)

other_hunks_applied = (
    "Note: Some hunks may have applied successfully. Review the output above."
)

# ---------------------------------------------------------------------
# Helper Functions: File, Patch, and Validation
# ---------------------------------------------------------------------

def resolve_path(file_path: str) -> str:
    """Expand user shortcuts and return an absolute path."""
    expanded = os.path.expanduser(file_path)
    return os.path.abspath(expanded)

def validate_parent_directories(directory_path: str) -> bool:
    """Recursively check if at least one parent directory exists."""
    parent_dir = os.path.dirname(directory_path)
    if parent_dir == directory_path or parent_dir == os.path.dirname(parent_dir):
        return False
    return os.path.exists(parent_dir) or validate_parent_directories(parent_dir)

def validate_path(requested_path: str) -> str:
    """
    Resolve and validate a path.
    If the path exists, return its real (absolute) path.
    Otherwise, ensure that at least one parent directory exists.
    """
    full_path = resolve_path(requested_path)
    if os.path.exists(full_path):
        return os.path.realpath(full_path)
    if validate_parent_directories(full_path):
        return full_path
    print(f"Warning: No existing parent directory found for: {os.path.dirname(full_path)}")
    return full_path

def is_image_file(mime_type: str) -> bool:
    """Return True if the MIME type indicates an image."""
    return mime_type.startswith("image/") if mime_type else False

# ---------------------------------------------------------------------
# Read, Write, and Info
# ---------------------------------------------------------------------

def read_file(file_path: str, return_metadata: bool = False) -> Union[str, Dict[str, Any]]:
    """
    Read a file from disk, returning content or metadata.

    **When to use 'read_file':**
    1. You want to load a file's contents into memory (string or base64 for images).
    2. You may optionally need metadata (MIME type, is_image).

    **Parameters**:
    - file_path: str  
      Absolute or relative path to the file to read.
    - return_metadata: bool (default=False)  
      If True, returns a dictionary with 'content', 'mime_type', 'is_image'.  
      Otherwise returns only the file's content as a string.

    **Error Handling**:
    - If the file cannot be read, tries reading as binary -> base64.  
    - If no parent directory is valid, prints a warning.

    Returns:
    - If return_metadata=False, a string of file contents.
    - If return_metadata=True, a dictionary with keys: content, mime_type, is_image.
    """
    valid_path = validate_path(file_path)
    mime_type, _ = mimetypes.guess_type(valid_path)
    is_img = is_image_file(mime_type if mime_type else "")
    if is_img:
        with open(valid_path, "rb") as f:
            content_bytes = f.read()
        content = base64.b64encode(content_bytes).decode("utf-8")
        result = {"content": content, "mime_type": mime_type, "is_image": True}
    else:
        try:
            with open(valid_path, "r", encoding="utf-8") as f:
                content = f.read()
            result = {"content": content, "mime_type": mime_type or "text/plain", "is_image": False}
        except Exception:
            # fallback to binary -> base64 if text read fails
            with open(valid_path, "rb") as f:
                content_bytes = f.read()
            content = "Binary file content (base64 encoded):\n" + base64.b64encode(content_bytes).decode("utf-8")
            result = {"content": content, "mime_type": "text/plain", "is_image": False}
    return result if return_metadata else result["content"]

def write_file(file_path: str, content: str) -> None:
    """
    Overwrite a file with new content.

    **When to use 'write_file':**
    1. You're replacing an entire file's contents with new text.

    **Parameters**:
    - file_path: str  
      Path to the file to write.
    - content: str  
      The new text content to store in the file.

    **Error Handling**:
    - Creates parent directories if they don't exist.
    - Overwrites existing file content.
    """
    valid_path = validate_path(file_path)
    os.makedirs(os.path.dirname(valid_path), exist_ok=True)
    with open(valid_path, "w", encoding="utf-8") as f:
        f.write(content)

def create_directory(dir_path: str) -> None:
    """
    Recursively create a directory.

    **When to use 'create_directory':**
    1. You need to ensure a folder structure is in place before writing files.

    **Parameters**:
    - dir_path: str  
      The directory path to create.

    **Error Handling**:
    - Validates the path first; no exception if the directory already exists.
    """
    valid_path = validate_path(dir_path)
    os.makedirs(valid_path, exist_ok=True)

def list_directory(dir_path: str) -> List[str]:
    """
    List contents of a directory, prefixing each entry with [DIR] or [FILE].

    **When to use 'list_directory':**
    1. You want a human-readable listing (like `ls`) with type info.

    **Parameters**:
    - dir_path: str  
      Path of the directory.

    **Error Handling**:
    - Raises ValueError if the path is not a directory.
    """
    valid_path = validate_path(dir_path)
    if not os.path.isdir(valid_path):
        raise ValueError(f"'{dir_path}' is not a directory.")
    entries = os.listdir(valid_path)
    return [f"[DIR] {e}" if os.path.isdir(os.path.join(valid_path, e)) else f"[FILE] {e}" for e in entries]

def delete_path(path_to_delete: str) -> None:
    """
    Delete a file or directory (recursively).

    **When to use 'delete_path':**
    1. You need to remove unwanted files/folders.

    **Parameters**:
    - path_to_delete: str  
      The file or directory path to remove.

    **Error Handling**:
    - Raises ValueError if path does not exist.
    - Recursively deletes directories.
    """
    valid_path = validate_path(path_to_delete)
    if os.path.isfile(valid_path):
        os.remove(valid_path)
    elif os.path.isdir(valid_path):
        shutil.rmtree(valid_path)
    else:
        raise ValueError(f"Path '{path_to_delete}' does not exist.")

def move_file(source_path: str, destination_path: str) -> None:
    """
    Move or rename a file/directory.

    **When to use 'move_file':**
    1. You want to relocate a file or directory within the filesystem.
    2. You want to rename a file or folder.

    **Parameters**:
    - source_path: str  
      The original path.
    - destination_path: str  
      Where to move/rename the item.

    **Error Handling**:
    - Creates parent directories if necessary.
    - Raises exceptions if the source doesn't exist.
    """
    valid_source = validate_path(source_path)
    valid_destination = validate_path(destination_path)
    os.makedirs(os.path.dirname(valid_destination), exist_ok=True)
    shutil.move(valid_source, valid_destination)

def get_file_info(file_path: str) -> Dict[str, Any]:
    """
    Retrieve metadata about a file.

    **When to use 'get_file_info':**
    1. You need size, timestamps, type, or permissions info.

    **Parameters**:
    - file_path: str  
      Path to the file.

    **Returns**:
    - A dictionary with fields 'size', 'created', 'modified', 'accessed',
      'is_directory', 'is_file', 'permissions'.

    **Error Handling**:
    - Raises if path is invalid or doesn't exist.
    """
    valid_path = validate_path(file_path)
    stats = os.stat(valid_path)
    return {
        "size": stats.st_size,
        "created": datetime.fromtimestamp(
            stats.st_birthtime if hasattr(stats, 'st_birthtime') else stats.st_ctime
        ).isoformat(),
        "modified": datetime.fromtimestamp(stats.st_mtime).isoformat(),
        "accessed": datetime.fromtimestamp(stats.st_atime).isoformat(),
        "is_directory": os.path.isdir(valid_path),
        "is_file": os.path.isfile(valid_path),
        "permissions": oct(stats.st_mode)[-3:]
    }

# ---------------------------------------------------------------------
# Diff and Patch
# ---------------------------------------------------------------------

def diff_files(file1: str, file2: str) -> str:
    """
    Generate a unified diff of two text files.

    **When to use 'diff_files':**
    1. You want to compare two files line-by-line (text) and produce a diff.
    2. Quick change detection or pre-patch analysis.

    **Parameters**:
    - file1: str
      Path to the original file.
    - file2: str
      Path to the modified file.

    **Error Handling**:
    - If either file is binary, returns a note that diffing binary is not supported.
    - If an exception occurs reading the files, returns an error message.

    Returns:
    - A unified diff as a string, or a note if no differences.
    """
    try:
        content1 = read_file(file1)
        content2 = read_file(file2)
        if content1.startswith("Binary file content") or content2.startswith("Binary file content"):
            return "Diffing binary files is not supported."
        diff = list(difflib.unified_diff(
            content1.splitlines(keepends=True),
            content2.splitlines(keepends=True),
            fromfile=file1,
            tofile=file2,
            lineterm=""
        ))
        return "Files are identical." if not diff else "".join(diff)
    except Exception as e:
        return f"Error diffing files: {e}"

def apply_patch(patch_text: str) -> str:
    """
    Apply a unified diff patch with strict context matching (zero fuzz).

    **When to use 'apply_patch':**
    1. You have a valid unified diff and want to automatically apply those changes.

    **Parameters**:
    - patch_text: str  
      The full text of the unified diff (e.g., from a diff tool).

    **Error Handling**:
    - Requires the `patch` command to be installed.
    - If patch fails to apply, returns stdout/stderr explaining why.
    - If patch partially applies, user must verify the resulting file manually.

    Returns:
    - A success message or detailed error output from the patch command.
    """
    if shutil.which("patch") is None:
        return "Error: 'patch' command not found on this system."
    with tempfile.NamedTemporaryFile('w+', delete=False) as patch_file:
        patch_file.write(patch_text)
        patch_file.flush()
        patch_filename = patch_file.name
    try:
        result = subprocess.run(
            ["patch", "-F", "0", "-p0", "-i", patch_filename],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            error_message = (
                f"Patch failed (return code {result.returncode}).\n"
                f"STDOUT:\n{result.stdout}\n"
                f"STDERR:\n{result.stderr}\n"
                "The patch did not find a 100% context match. Please verify that the file "
                "contains the exact lines required by the diff."
            )
            return error_message
        return f"Patch applied successfully.\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    except Exception as e:
        return f"Error applying patch: {e}"
    finally:
        os.remove(patch_filename)

# ---------------------------------------------------------------------
# Editing Tools: Line and Block Replacement
# ---------------------------------------------------------------------

def replace_line(file_path: str, line_number: int, new_line: str) -> str:
    """
    Replace a single line in a file by line number (1-based).

    **When to use 'replace_line':**
    1. You want to fix or update a specific line in a text file.
    2. Great for small single-line edits.

    **Parameters**:
    - file_path: str  
      The file where the change is applied.
    - line_number: int  
      The (1-based) line index to replace.
    - new_line: str  
      The new text that will replace the existing line.

    **Error Handling**:
    - If line_number is out of range, returns an error stating how many lines exist.
    - If the file cannot be read/written, returns an error message.

    Returns:
    - Success or error string.
    """
    valid_path = validate_path(file_path)
    try:
        with open(valid_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        return f"Error reading file: {e}"
    if line_number < 1 or line_number > len(lines):
        return f"Invalid line number: file has {len(lines)} lines."
    lines[line_number - 1] = new_line + "\n"
    try:
        with open(valid_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
        return f"Line {line_number} in '{file_path}' replaced successfully."
    except Exception as e:
        return f"Error writing updated file: {e}"

def replace_block(file_path: str, search_block: str, replacement_block: str, use_regex: bool = False) -> str:
    """
    Replace a multi-line block of text within a file, optionally using regex for advanced matching.

    **When to use 'replace_block':**
    1. You need to replace a chunk of text that is less than ~30% of the file's content.
       (For bigger edits, consider a complete file replacement or patch approach.)
    2. A smaller, line-level edit or single-string search/replace won't suffice.
    3. You want to ensure the entire matching context is replaced in one go, especially with multi-line changes.

    **Parameters**:
    - file_path: str  
      Path to the file you want to edit.
    - search_block: str  
      The exact block or regex pattern to match.
    - replacement_block: str  
      The text that will overwrite the matched block.
    - use_regex: bool (default=False)  
      If True, interpret search_block as a regex in DOTALL mode.

    **Error Handling**:
    - Returns an error if the block is not found or if multiple matches exist (can't disambiguate).
    - Overwrites the first or unique match only.

    **Cautions**:
    - If the file changes drastically (>30%), consider a complete replacement or patch approach.
    - If you only need to fix a single line, see `replace_line`.
    - For small single-string edits, try `search_replace`.

    **Examples**:
    1) Non-Regex:
      {
        "file_path": "path/to/code.py",
        "search_block": "oldFunction()\\n    pass",
        "replacement_block": "newFunction()\\n    print('Hello')",
        "use_regex": false
      }

    2) Regex:
      {
        "file_path": "path/to/config.json",
        "search_block": "\"version\": \\d+",
        "replacement_block": "\"version\": 42",
        "use_regex": true
      }

    Returns:
    - Success or error message.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        if use_regex:
            matches = list(re.finditer(search_block, content, re.DOTALL))
        else:
            matches = []
            start = 0
            while True:
                index = content.find(search_block, start)
                if index == -1:
                    break
                matches.append((index, index + len(search_block)))
                start = index + 1

        if not matches:
            return f"Error: The specified search block was not found in {file_path}."
        if len(matches) > 1:
            details = []
            if use_regex:
                for m in matches:
                    snippet = m.group(0).replace("\n", "\\n")[:60]
                    details.append(f"Index {m.start()}: {snippet}...")
            else:
                for index_i, end_i in matches:
                    snippet = content[index_i:end_i].replace("\n", "\\n")[:60]
                    details.append(f"Index {index_i}: {snippet}...")
            return (
                f"Error: The specified search block is not unique in {file_path}.\n"
                f"Found {len(matches)} matches at: " + ", ".join(details) +
                "\nPlease provide additional context to uniquely identify the block."
            )

        # Exactly one match: do the replacement
        if use_regex:
            new_content, count = re.subn(search_block, replacement_block, content, count=1, flags=re.DOTALL)
            if count == 0:
                return f"Error: No match was replaced in {file_path}."
        else:
            index, end_index = matches[0]
            new_content = content[:index] + replacement_block + content[end_index:]

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        return f"Block replaced successfully in {file_path}."

    except Exception as e:
        return f"Error replacing block in {file_path}: {e}"

# ---------------------------------------------------------------------
# Process Management & Code Search
# ---------------------------------------------------------------------

def list_processes() -> str:
    """
    List current system processes.

    **When to use 'list_processes':**
    1. You need a snapshot of running processes to see what's active.

    **Implementation**:
    - On Windows, uses 'tasklist'.
    - On Unix, uses 'ps aux'.

    Returns:
    - A string containing the process list.
    """
    import platform
    try:
        cmd = "tasklist" if platform.system().lower() == "windows" else "ps aux"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout
    except Exception as e:
        return f"Error listing processes: {e}"

def kill_process(pid: int) -> str:
    """
    Terminate a process by PID (forcefully).

    **When to use 'kill_process':**
    1. You want to stop a rogue or hung process by specifying its PID.

    **Parameters**:
    - pid: int  
      Process ID to kill.

    **Error Handling**:
    - Uses signal 9 on Unix. 
    - Returns an error if the process cannot be killed.

    Returns:
    - Success or error message.
    """
    try:
        os.kill(pid, 9)
        return f"Process {pid} terminated successfully."
    except Exception as e:
        return f"Error terminating process {pid}: {e}"

def search_code(options: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Search file contents using ripgrep if available, or fallback to Python-based search.

    **When to use 'search_code':**
    1. You want to find lines containing a specific pattern (text or regex) within a directory.

    **Parameters** (through 'options' dict):
    - rootPath (str): Base directory to start searching.
    - pattern (str): Text or regex pattern to search for.
    - filePattern (str): Optional filename pattern filter (e.g. *.py).
    - ignoreCase (bool): Case-insensitive search if True.
    - maxResults (int): Limit on the number of matches to return.
    - includeHidden (bool): Whether to search hidden files.
    - contextLines (int): Number of lines of context around each match.

    **Error Handling**:
    - If 'rg' is not installed or an error occurs, does a fallback line-by-line search in Python.
    - Ignores binary files in fallback mode.

    Returns:
    - A list of dicts: [{"file": <path>, "line": <lineNumber>, "match": <matchText>}].
    """
    rg_command = "rg"
    args = ["--json", "--line-number"]
    if options.get("ignoreCase", True):
        args.append("-i")
    if "maxResults" in options:
        args.extend(["-m", str(options["maxResults"])])
    if options.get("includeHidden", False):
        args.append("--hidden")
    if options.get("contextLines", 0) > 0:
        args.extend(["-C", str(options["contextLines"])])
    if options.get("filePattern"):
        args.extend(["-g", options["filePattern"]])
    args.append(options["pattern"])
    args.append(options["rootPath"])
    try:
        result = subprocess.run([rg_command] + args, capture_output=True, text=True, check=True)
        output_lines = result.stdout.strip().split("\n")
        results = []
        for line in output_lines:
            try:
                parsed = json.loads(line)
                if parsed.get("type") == "match":
                    data = parsed["data"]
                    path_text = data["path"]["text"]
                    line_num = data["line_number"]
                    for submatch in data.get("submatches", []):
                        match_text = submatch["match"]["text"]
                        results.append({"file": path_text, "line": line_num, "match": match_text})
            except Exception:
                continue
        return results
    except Exception:
        # Fallback to Python-based search
        fallback_results = []
        root_dir = validate_path(options["rootPath"])
        max_results = options.get("maxResults", 1000)
        pattern = options["pattern"].lower() if options.get("ignoreCase", True) else options["pattern"]
        for current_dir, dirs, files in os.walk(root_dir):
            for file in files:
                if options.get("filePattern") and not fnmatch.fnmatch(file, options["filePattern"]):
                    continue
                filepath = os.path.join(current_dir, file)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                    for i, line_text in enumerate(lines):
                        candidate = line_text.lower() if options.get("ignoreCase", True) else line_text
                        if pattern in candidate:
                            fallback_results.append({
                                "file": filepath,
                                "line": i+1,
                                "match": line_text.strip()
                            })
                            if len(fallback_results) >= max_results:
                                return fallback_results
                except Exception:
                    continue
        return fallback_results

def search_replace(file_path: str, search: str, replace: str) -> str:
    """
    Perform a single occurrence search-and-replace within a file.

    **When to use 'search_replace':**
    1. You want to do a quick fix, substituting the first instance of 'search' with 'replace' in a file.
    2. For multi-line changes, see `replace_block`.

    **Parameters**:
    - file_path: str
      The file where the search-and-replace will happen.
    - search: str
      The text to locate.
    - replace: str
      The text to replace the first occurrence with.

    **Error Handling**:
    - If 'search' is not found, returns a message stating that.
    - If there's an error reading/writing, returns an error message.

    Returns:
    - Success or error string.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        index = content.find(search)
        if index == -1:
            return f"Search string not found in {file_path}."
        new_content = content.replace(search, replace, 1)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        return f"Replaced first occurrence in {file_path}."
    except Exception as e:
        return f"Error in search and replace: {e}"

# ---------------------------------------------------------------------
# Linting & Static Analysis for JSON / Python
# ---------------------------------------------------------------------

def lint_json_file(file_path: str) -> str:
    """
    Validate that a file is valid JSON.

    **When to use 'lint_json_file':**
    1. You suspect a JSON file might have syntax errors.

    **Parameters**:
    - file_path: str
      The JSON file to validate.

    **Error Handling**:
    - Returns an error message if JSON fails to parse.

    Returns:
    - A success string if valid, or an error message.
    """
    try:
        content = read_file(file_path)
        json.loads(content)
        return f"Linting Passed: {file_path} is valid JSON."
    except Exception as e:
        return f"Linting Error in {file_path}: {e}"

def lint_python_file(file_path: str) -> str:
    """
    Run flake8 linting on a Python file.

    **When to use 'lint_python_file':**
    1. You want to quickly catch style/syntax warnings in a .py file.

    **Parameters**:
    - file_path: str
      The Python file to lint.

    **Error Handling**:
    - Returns a string with flake8's warnings/errors, or "No linting issues found."

    Returns:
    - The lint report or error message if the linting tool fails.
    """
    try:
        result = subprocess.run(["flake8", file_path], capture_output=True, text=True)
        output = result.stdout.strip()
        return output if output else "No linting issues found."
    except Exception as e:
        return f"Error running flake8 on {file_path}: {e}"

def static_analysis_python(file_path: str) -> str:
    """
    Run pylint for deeper static analysis on a Python file.

    **When to use 'static_analysis_python':**
    1. You want more thorough checks than flake8 can provide.

    **Parameters**:
    - file_path: str
      The Python file to analyze.

    **Error Handling**:
    - Returns an error message if pylint fails to run.

    Returns:
    - The pylint report or 'No static analysis issues found.' if empty.
    """
    try:
        result = subprocess.run(["pylint", file_path, "--score", "y"], capture_output=True, text=True)
        output = result.stdout.strip()
        return output if output else "No static analysis issues found."
    except Exception as e:
        return f"Error running pylint on {file_path}: {e}"

def line_number_python_file(file_path: str) -> str:
    """
    Return a Python file's content with line numbers for referencing or partial edits.

    **When to use 'line_number_python_file':**
    1. You want to display a file with line numbers for context before editing lines.

    **Parameters**:
    - file_path: str
      The Python file to read.

    **Error Handling**:
    - Returns an error message if file reading fails.

    Returns:
    - A string with each line prefixed by its line number (1-based).
    """
    try:
        valid_path = validate_path(file_path)
        with open(valid_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        numbered = [f"{i+1:4d}: {line}" for i, line in enumerate(lines)]
        return "".join(numbered)
    except Exception as e:
        return f"Error reading Python file: {e}"

# ---------------------------------------------------------------------
# Additional Helper for Searching Filenames
# ---------------------------------------------------------------------

def search_files(root_path: str, pattern: str) -> List[str]:
    """
    Recursively search for filenames matching a pattern.

    **When to use 'search_files':**
    1. You need to locate all files that match a specific filename pattern, e.g. '*.cpp'.

    **Parameters**:
    - root_path: str
      Directory to start searching.
    - pattern: str
      Filename pattern to match (glob style, e.g., '*.py').

    **Returns**:
    - A list of file paths that match the pattern.

    **Error Handling**:
    - Raises ValueError if root_path is invalid or not a directory.
    """
    matches = []
    root_path = validate_path(root_path)
    if not os.path.isdir(root_path):
        raise ValueError(f"'{root_path}' is not a valid directory.")
    
    for root, dirs, files in os.walk(root_path):
        for filename in files:
            if fnmatch.fnmatch(filename, pattern):
                full_path = os.path.join(root, filename)
                matches.append(full_path)
    return matches

# ---------------------------------------------------------------------
# MCP Server & Tools
# ---------------------------------------------------------------------

mcp = FastMCP("UltimateCoder", dependencies=[
    "fastmcp",
    "pandas",
    "numpy",
    "flake8",
    "pylint"
])


# ------------------- Resources ------------------- #
@mcp.resource("config://project")
def get_project_config() -> str:
    """
    Resource that returns dynamic project config info.

    **When to use 'get_project_config':**
    1. You want to query the environment (CWD, user, Python version).

    Returns:
    - A multi-line string with config data like directory, user, python_version, dependencies.
    """
    config = {
        "current_working_directory": os.getcwd(),
        "user": os.environ.get("USER", "unknown"),
        "python_version": os.sys.version,
        "dependencies": ["fastmcp", "pandas", "numpy"]
    }
    return "\n".join(f"{k}: {v}" for k, v in config.items())

# ------------------- Prompts ------------------- #

@mcp.prompt("prompt://review_code")
def review_code_prompt(code: str) -> str:
    """
    **LLM Prompt**: Provide a code review for clarity, efficiency, and maintainability.

    **Parameters**:
    - code: str
      The code to be reviewed.

    Returns:
    - A prompt string for the LLM to generate a code review.
    """
    return (
        "Please review the following code for clarity, efficiency, and maintainability. "
        "Provide concise, actionable feedback:\n\n"
        f"{code}"
    )

@mcp.prompt("prompt://debug_error")
def debug_error_prompt(error: str) -> str:
    """
    **LLM Prompt**: Diagnose an error and propose fixes/debugging steps.

    **Parameters**:
    - error: str
      Error message or traceback to analyze.

    Returns:
    - A prompt string for the LLM to suggest debugging approaches.
    """
    return (
        "I'm encountering this error in my code. Please analyze it and propose potential fixes:\n\n"
        f"{error}\n\n"
        "Include any relevant debugging steps or recommended modifications."
    )

@mcp.prompt("prompt://architect")
def architect_prompt(change_request: str, code: str) -> str:
    """
    **LLM Prompt**: Provide architectural guidance for a given change request.

    **Parameters**:
    - change_request: str  
      Description of the feature/change needed.
    - code: str  
      Current code to modify or extend.

    Returns:
    - A prompt string that instructs the LLM to propose best-practice modifications.
    """
    return (
        "Act as an expert software architect. Study the change request below, then examine the current code.\n"
        "Provide clear, concise instructions on how to modify the code to meet these requirements. Use bullet points, "
        "diff-like notation, or short, unambiguous steps.\n\n"
        "If a complete file replacement is needed, clearly state:\n"
        "'Completely replace file contents. Best for large changes (>20% of file) or when incremental edits fail. Use caution.'\n\n"
        f"Change Request:\n{change_request}\n\n"
        f"Current Code:\n{code}"
    )

@mcp.prompt("prompt://complete_file_replace")
def complete_file_replace_prompt(file_path: str, new_content: str) -> str:
    """
    **LLM Prompt**: Instruct the user/AI to replace an entire file with new content.

    **Parameters**:
    - file_path: str
      The file path to overwrite.
    - new_content: str
      The new content for the file.

    Returns:
    - A prompt clarifying that this is a full replacement (data loss caution).
    """
    return (
        f"Completely replace the contents of the file '{file_path}' with the new content below.\n"
        "This is intended for large-scale changes or if smaller edits have failed.\n"
        "Be aware that all existing data is lost.\n\n"
        f"New Content:\n{new_content}"
    )

# ------------------- Tools ------------------- #
@mcp.tool()
async def tool_process_files(files: List[str], ctx: Context) -> str:
    """
    Process multiple files asynchronously with progress updates.

    **When to use 'tool_process_files':**
    1. You want to read and process a batch of files in sequence while reporting progress.

    **Parameters**:
    - files: List[str]
      A list of file paths.
    - ctx: Context
      The FastMCP context for logging and progress updates.

    **Behavior**:
    - Reads each file, logs how many characters were read, or logs an error.
    - Reports incremental progress for each file.

    Returns:
    - A summary of the results for each file.
    """
    total = len(files)
    results = []
    for i, file in enumerate(files, start=1):
        ctx.info(f"Processing file: {file}")
        try:
            content = read_file(file)
            results.append(f"{file}: Read {len(content)} characters")
        except Exception as e:
            results.append(f"{file}: Error - {e}")
        await ctx.report_progress(i, total)
    return "Processing complete:\n" + "\n".join(results)

@mcp.tool()
def tool_list_files(directory_path: str = None, recursive: bool = False) -> str:
    """
    List the contents of a directory, optionally recursively.

    **When to use 'tool_list_files':**
    1. You want a simple directory listing with type info ([DIR], [FILE]).
    2. You can optionally traverse subdirectories with `recursive=True`.

    **Parameters**:
    - directory_path: str (default=None)
      The path of the directory to list. If None, uses current working directory.
    - recursive: bool (default=False)
      Whether to recurse into subdirectories.

    **Error Handling**:
    - Returns an error if the path is not a directory.
    - If an exception arises, returns the error message.

    Returns:
    - A newline-separated list of entries, each prefixed with [FILE] or [DIR].
    """
    try:
        dir_path = directory_path if directory_path else os.getcwd()
        valid_path = validate_path(dir_path)
        
        if not os.path.isdir(valid_path):
            return f"Error: '{dir_path}' is not a directory."
            
        if not recursive:
            # Use the existing list_directory function for non-recursive listing
            return "\n".join(list_directory(valid_path))
        
        # For recursive listing, we need to walk the directory tree
        matches = []
        for root, dirs, files in os.walk(valid_path):
            rel_root = os.path.relpath(root, valid_path)
            if rel_root == '.':
                # For the top directory, don't add the relative path
                for file in files:
                    matches.append(f"[FILE] {file}")
                for d in dirs:
                    matches.append(f"[DIR] {d}")
            else:
                # For subdirectories, include the relative path
                for file in files:
                    matches.append(f"[FILE] {os.path.join(rel_root, file)}")
                for d in dirs:
                    matches.append(f"[DIR] {os.path.join(rel_root, d)}")
        return "\n".join(matches)
    except Exception as e:
        return f"Error listing files: {e}"

@mcp.tool()
def tool_read_file(file_path: str, return_metadata: bool = False) -> str:
    """
    Read a file (text or image) from disk, optionally returning metadata.

    **When to use 'tool_read_file':**
    1. You need to retrieve file contents as plain text or base64 (for images).
    2. You might also want metadata like MIME type.

    **Parameters**:
    - file_path: str  
      Path to the file to read.
    - return_metadata: bool (default=False)  
      If True, returns a dict with content, mime_type, is_image.

    **Error Handling**:
    - Returns a string with the error if something fails.
    """
    try:
        result = read_file(file_path, return_metadata)
        return str(result)
    except Exception as e:
        return f"Error reading file: {e}"

@mcp.tool()
@mcp.tool()
def tool_write_file(file_path: str, content: str) -> str:
    """
    Overwrite a file's content with new text.

    **When to use 'tool_write_file':**
    1. You want to replace a file entirely with new content.

    **Parameters**:
    - file_path: str
      Target file path.
    - content: str
      New text content to write.

    **Error Handling**:
    - Returns error messages on I/O failure.
    """
    try:
        # Ensure content is treated as a string
        content_str = str(content)
        write_file(file_path, content_str)
        return f"File '{file_path}' written successfully."
    except Exception as e:
        return f"Error writing file: {e}"

@mcp.tool()
def tool_delete_path(path_to_delete: str) -> str:
    """
    Delete a file or directory (recursively).

    **When to use 'tool_delete_path':**
    1. You want to remove a file or folder from the filesystem.

    **Parameters**:
    - path_to_delete: str  
      The path to remove.

    **Error Handling**:
    - Returns a message if path does not exist or if deletion fails.
    """
    try:
        delete_path(path_to_delete)
        return f"Path '{path_to_delete}' deleted successfully."
    except Exception as e:
        return f"Error deleting path: {e}"

@mcp.tool()
def tool_move_file(source_path: str, destination_path: str) -> str:
    """
    Move or rename a file or directory.

    **When to use 'tool_move_file':**
    1. You want to rename a file or relocate it in the filesystem.

    **Parameters**:
    - source_path: str
      The current file or folder path.
    - destination_path: str
      The new location/path.

    **Error Handling**:
    - Returns an error string if operation fails.
    """
    try:
        move_file(source_path, destination_path)
        return f"Moved '{source_path}' to '{destination_path}'."
    except Exception as e:
        return f"Error moving file: {e}"

@mcp.tool()
def tool_search_files(root_path: str, pattern: str) -> str:
    """
    Search for filenames matching a pattern under a given root directory.

    **When to use 'tool_search_files':**
    1. You need to locate all files with a given extension or wildcard (e.g., '*.cpp').

    **Parameters**:
    - root_path: str
      Directory to start searching.
    - pattern: str
      Filename pattern (glob) to match.

    **Error Handling**:
    - Returns an error if the path is invalid or not a directory.

    Returns:
    - A list of matching file paths, or 'No matches found.' if none.
    """
    try:
        matches = search_files(root_path, pattern)
        return "\n".join(matches) if matches else "No matches found."
    except Exception as e:
        return f"Error searching files: {e}"

@mcp.tool()
def tool_get_file_info(file_path: str) -> str:
    """
    Return metadata about a file (size, timestamps, type, permissions).

    **When to use 'tool_get_file_info':**
    1. You need quick stats about a file, like creation time or size.

    **Parameters**:
    - file_path: str
      Path to the file.

    **Error Handling**:
    - Returns an error if the path doesn't exist or can't be accessed.
    """
    try:
        info = get_file_info(file_path)
        return str(info)
    except Exception as e:
        return f"Error getting file info: {e}"

def read_multiple_files(paths: List[str]) -> Dict[str, Any]:
    """Helper to read multiple files with metadata."""
    output = {}
    for path in paths:
        output[path] = read_file(path, return_metadata=True)
    return output

@mcp.tool()
def tool_read_multiple_files(paths: List[str]) -> str:
    """
    Read multiple files, returning content & metadata for each.

    **When to use 'tool_read_multiple_files':**
    1. You have a list of files and need to read them all, possibly images too.

    **Parameters**:
    - paths: List[str]
      A list of file paths to read.

    **Error Handling**:
    - Returns an error if any file cannot be read.
    - Continues reading subsequent files if possible.

    Returns:
    - A stringified dictionary mapping each path to its metadata.
    """
    try:
        results = read_multiple_files(paths)
        return str(results)
    except Exception as e:
        return f"Error reading multiple files: {e}"

@mcp.tool()
def tool_create_directory(dir_path: str) -> str:
    """
    Recursively create a directory.

    **When to use 'tool_create_directory':**
    1. You want to ensure a folder (and its parents) exist before writing files.

    **Parameters**:
    - dir_path: str
      The directory path to create.

    **Error Handling**:
    - Returns an error if creation fails (e.g., permission issues).
    """
    try:
        create_directory(dir_path)
        return f"Directory '{dir_path}' created successfully."
    except Exception as e:
        return f"Error creating directory: {e}"

def run_command(command: str) -> str:
    """Helper to run a shell command, capturing STDOUT/STDERR and exit code."""
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return f"Exit Code: {result.returncode}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"

@mcp.tool()
def tool_run_command(command: str) -> str:
    """
    Execute a shell command locally, capturing output and exit code.

    **When to use 'tool_run_command':**
    1. You want to run a system command (shell) and get full stdout/stderr back.

    **Parameters**:
    - command: str
      The shell command to execute.

    **Error Handling**:
    - Returns an error message if execution fails or times out.
    """
    try:
        return run_command(command)
    except Exception as e:
        return f"Error running command: {e}"

@mcp.tool()
def tool_diff_files(file1: str, file2: str) -> str:
    """
    Produce a unified diff between two text files.

    **When to use 'tool_diff_files':**
    1. You want to quickly see changes between two versions of a file.

    **Parameters**:
    - file1: str
      Path to the original file.
    - file2: str
      Path to the updated file.

    **Error Handling**:
    - Returns an error if reading fails or if binary files are encountered.
    """
    return diff_files(file1, file2)

@mcp.tool()
def tool_replace_line(file_path: str, line_number: int, new_line: str) -> str:
    """
    Replace a specific line in a file (1-based index).

    **When to use 'tool_replace_line':**
    1. You only need to change one line in a text file.

    **Parameters**:
    - file_path: str
      Path to the file.
    - line_number: int
      1-based line number to replace.
    - new_line: str
      The new line text.

    **Error Handling**:
    - Returns an error if the line_number is out of range or if I/O fails.
    """
    return replace_line(file_path, line_number, new_line)

@mcp.tool()
def tool_replace_block(file_path: str, search_block: str, replacement_block: str, use_regex: bool = False) -> str:
    """
    Replace a multi-line block of text within a file, optionally using regex for advanced matching.

    **When to use 'tool_replace_block':**
    1. You need to replace a chunk of text that is less than ~30% of the file's content.
       (For bigger edits, consider a complete file replacement or patch approach.)
    2. A smaller, line-level edit or single-string search/replace won't suffice.
    3. You want to ensure the entire matching context is replaced in one go, especially with multi-line changes.

    **Parameters**:
    - file_path: str  
      Path to the file you want to edit.
    - search_block: str  
      The exact block or regex pattern to match.
    - replacement_block: str  
      The text that will overwrite the matched block.
    - use_regex: bool (default=False)  
      If True, interpret search_block as a regex in DOTALL mode.

    **Error Handling**:
    - Returns an error if the block is not found or if multiple matches exist (can't disambiguate).
    - Overwrites the first or unique match only.

    **Cautions**:
    - If the file changes drastically (>30%), consider a complete replacement or patch approach.
    - If you only need to fix a single line, see `tool_replace_line`.
    - For small single-string edits, try `tool_search_replace`.

    **Examples**:
    1) Non-Regex:
      {
        "file_path": "path/to/code.py",
        "search_block": "oldFunction()\\n    pass",
        "replacement_block": "newFunction()\\n    print('Hello')",
        "use_regex": false
      }

    2) Regex:
      {
        "file_path": "path/to/config.json",
        "search_block": "\"version\": \\d+",
        "replacement_block": "\"version\": 42",
        "use_regex": true
      }

    Returns:
    - Success or error message.
    """
    return replace_block(file_path, search_block, replacement_block, use_regex)

@mcp.tool()
def tool_apply_patch(patch_text: str) -> str:
    """
    Apply a unified diff patch using the system's patch command with strict context matching.

    **When to use 'tool_apply_patch':**
    1. You have a unified diff that must match exactly (no fuzz) to apply changes.

    **Parameters**:
    - patch_text: str
      The unified diff text.

    **Error Handling**:
    - Returns error if `patch` is unavailable or if the patch fails to apply.
    """
    return apply_patch(patch_text)

# ------------------- Process & Code Search Tools ------------------- #

@mcp.tool()
def tool_list_processes() -> str:
    """
    List current system processes.

    **When to use 'tool_list_processes':**
    1. You want to see a snapshot of what's running on the system.

    Returns:
    - A string containing the output of tasklist or ps aux.
    """
    return list_processes()

@mcp.tool()
def tool_kill_process(pid: int) -> str:
    """
    Kill a process by PID using signal 9 (force kill).

    **When to use 'tool_kill_process':**
    1. You need to forcibly stop a process that won't respond otherwise.

    **Parameters**:
    - pid: int
      The PID of the process to kill.

    **Error Handling**:
    - Returns an error if the kill operation fails.
    """
    return kill_process(pid)

@mcp.tool()
def tool_search_code(rootPath: str, pattern: str, filePattern: str = "", ignoreCase: bool = True,
                     maxResults: int = 1000, includeHidden: bool = False, contextLines: int = 0) -> str:
    """
    Search file contents for a text or regex pattern, using ripgrep if available.

    **When to use 'tool_search_code':**
    1. You want to locate lines in code matching a pattern across multiple files.
    2. You can limit search scope with filename patterns, case sensitivity, etc.

    **Parameters**:
    - rootPath: str  
      The directory to start searching in.
    - pattern: str  
      The text/regex pattern to find.
    - filePattern: str (default="")
      A file name filter (e.g., "*.py").
    - ignoreCase: bool (default=True)
      Case-insensitive match if True.
    - maxResults: int (default=1000)
      The maximum number of matches to return.
    - includeHidden: bool (default=False)
      Whether to also search hidden files.
    - contextLines: int (default=0)
      Number of lines of context around each match.

    **Error Handling**:
    - If ripgrep is missing or fails, it falls back to a Python-based search.

    Returns:
    - A list of matches, each line in the format "file (Line X): match".
    - Or 'No matches found.' if none.
    """
    options = {
        "rootPath": rootPath,
        "pattern": pattern,
        "filePattern": filePattern,
        "ignoreCase": ignoreCase,
        "maxResults": maxResults,
        "includeHidden": includeHidden,
        "contextLines": contextLines
    }
    results = search_code(options)
    if not results:
        return "No matches found."
    return "\n".join(f"{res['file']} (Line {res['line']}): {res['match']}" for res in results)

@mcp.tool()
def tool_search_replace(filePath: str, search: str, replace: str) -> str:
    """
    Perform a single-target search and replace in a file.

    **When to use 'tool_search_replace':**
    1. You want to replace the first occurrence of a string in a file.
    2. For multi-line changes, consider `tool_replace_block`.

    **Parameters**:
    - filePath: str
      The file to edit.
    - search: str
      The substring to look for.
    - replace: str
      The new substring to insert.

    **Error Handling**:
    - Returns an error if the substring is not found.
    """
    return search_replace(filePath, search, replace)

# ---------------------------------------------------------------------
# Additional Tools: Linting & Static Analysis for JSON / Python
# ---------------------------------------------------------------------

@mcp.tool()
def tool_lint_json(file_path: str) -> str:
    """
    Validate if a file is valid JSON.

    **When to use 'tool_lint_json':**
    1. You have a JSON file and want to ensure it has no syntax errors.

    **Parameters**:
    - file_path: str
      The JSON file path.

    **Error Handling**:
    - Returns 'Linting Error' with details if invalid.

    Returns:
    - 'Linting Passed' if the file is valid JSON.
    """
    return lint_json_file(file_path)

@mcp.tool()
def tool_lint_python(file_path: str) -> str:
    """
    Lint a Python file using flake8 for style and syntax checks.

    **When to use 'tool_lint_python':**
    1. You want quick warnings about code style or minor issues.

    **Parameters**:
    - file_path: str
      The .py file to check.

    **Error Handling**:
    - Returns an error message if flake8 cannot be run.

    Returns:
    - Lint results, or 'No linting issues found.' if clean.
    """
    return lint_python_file(file_path)

@mcp.tool()
def tool_static_analysis_python(file_path: str) -> str:
    """
    Perform deeper static analysis on a Python file using pylint.

    **When to use 'tool_static_analysis_python':**
    1. You want a more robust check for potential bugs and best practices.

    **Parameters**:
    - file_path: str
      The Python file to analyze.

    **Error Handling**:
    - If pylint fails, returns an error message.

    Returns:
    - Pylint's report, or 'No static analysis issues found.' if empty.
    """
    return static_analysis_python(file_path)

@mcp.tool()
def tool_line_python_file(file_path: str) -> str:
    """
    Return a Python file's contents with line numbers.

    **When to use 'tool_line_python_file':**
    1. You want to display file lines with indices before partial edits.

    **Parameters**:
    - file_path: str
      The Python file to number.

    **Error Handling**:
    - Returns an error if reading fails.
    """
    return line_number_python_file(file_path)

# ---------------------------------------------------------------------
# Run the FastMCP Server
# ---------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
