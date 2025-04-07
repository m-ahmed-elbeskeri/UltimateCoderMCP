# UltimateCoder MCP

Local-first automation server for developers and engineers — automate terminal commands, edit files, and power up your AI tools.

<p align="left">
  <a href="https://buymeacoffee.com/m.ahmed.elbesk?new=1"><img src="https://img.shields.io/badge/Buy%20Me%20a%20Coffee-support-yellow?style=flat-square" alt="Buy Me a Coffee"></a>
  <a href="https://smithery.ai/server/@m-ahmed-elbeskeri/ultimatecodermcp"><img src="https://img.shields.io/badge/Smithery-Deployed-blue?style=flat-square" alt="Smithery"></a>
  <a href="https://github.com/m-ahmed-elbeskeri/UltimateCoderMCP/releases"><img src="https://img.shields.io/github/downloads/m-ahmed-elbeskeri/UltimateCoderMCP/total?style=flat-square" alt="Downloads"></a>
  <a href="https://github.com/m-ahmed-elbeskeri/UltimateCoderMCP/stargazers"><img src="https://img.shields.io/github/stars/m-ahmed-elbeskeri/UltimateCoderMCP?style=flat-square" alt="Stars"></a>
</p>

Smithery link: [https://smithery.ai/server/@m-ahmed-elbeskeri/ultimatecodermcp](https://smithery.ai/server/@m-ahmed-elbeskeri/ultimatecodermcp)

UltimateCoder turns your local machine into a surgical code command center.  
Built on  [fastmcp](https://github.com/jlowin/fastmcp), UltimateCoder delivers total control over your filesystem, processes, and codebase — with AI-enhanced precision.

Run terminal commands, edit thousands of files at once, apply unified diffs safely, or let your AI assistant intelligently refactor your project.  
All locally, instantly, and securely.

No cloud latency. No data leaving your machine. No compromises.

Built for builders. Loved by automation architects. Trusted by power users.


## What Makes UltimateCoder Different

- MCP-native, fully local server — AI assistants (like Claude) gain real-time read/write power over your projects.
- Fast, Safe File Editing — Single lines, blocks, or entire files. Precise changes, full control.
- Advanced Patch & Diff Engine — Unified diffs apply with strict context matching, so you never apply mistakes blindly.
- Process Control — List, monitor, and kill running processes programmatically.
- Supercharged Search — Ripgrep-backed recursive search with smart fallbacks.
- Multi-file Operations — Process thousands of files across your codebase. Batch edits, mass linting, intelligent replacements.
- Ready for Automation — Ideal for scripting, automation, and human-in-the-loop AI workflows.
- Built on [fastmcp](https://github.com/jlowin/fastmcp) — Lightning-fast, extensible MCP core.


## What Can It Do

| Feature | Benefit | Typical Use Case |
|---------|----------|-----------------|
| Terminal Execution | Run any local shell command with full output capture | Automate build scripts, deploy, run tests, manage local tools |
| Process Management | List and kill processes by PID | Manage runaway processes, automate cleanup |
| File Operations | Read, write, move, and delete files & directories | Automate file handling tasks, backups, or migrations |
| File Metadata Retrieval | Get size, timestamps, permissions | Auditing, automation pipelines |
| Precise Line/Block Replacement | Make targeted file edits (supports regex) | Fix configuration files, update code snippets programmatically |
| Unified Diff Patching | Safely apply diffs with strict context matching | Automated refactoring, safe code migrations |
| Mass Code Search | Ripgrep-powered search across files | Explore codebases, find usages, audit security-sensitive patterns |
| JSON and Python Linting | Instant feedback for common formats | Validate configs, ensure code hygiene |
| Static Python Analysis | Deeper pylint insights | Spot bugs before they happen |
| Read Python with Line Numbers | Contextual code review or AI-assisted editing | AI understands context better, human reviews are faster |
| Batch File Processing | Work on thousands of files at once | Large-scale refactoring or analysis |
| AI-Enhanced Workflows | Fully compatible with Claude Desktop and MCP clients | Let your AI assistant become a local dev co-pilot |


## Example Use Cases

- Refactor 10,000+ files safely using unified diff patches with context validation.
- Audit your entire project for deprecated functions in seconds.
- Automate cleanup: list, analyze, and kill idle processes from batch scripts.
- Enhance your AI workflows: give Claude or custom MCP clients real filesystem and terminal power.
- Work on sensitive codebases: UltimateCoder runs 100% locally, no data leaves your machine.
- Automate migrations: JSON schemas, Python packages, configs — all editable programmatically.
- Lint and validate at scale: automate linting pipelines before commits or deployments.


## Installation

### Requirements

- Python 3.8+
- Core dependency: [fastmcp](https://github.com/jlowin/fastmcp)

### Steps

```bash
git clone https://github.com/m-ahmed-elbeskeri/UltimateCoderMCP.git
cd UltimateCoder
python main.py
```

You now have a fully operational MCP server running locally.


## Tool Reference

| Tool | Summary |
|------|----------|
| `tool_run_command` | Execute local shell commands |
| `tool_list_processes` | List system processes |
| `tool_kill_process` | Kill a process by PID |
| `tool_read_file` | Read file content (text or image) |
| `tool_write_file` | Write/overwrite file content |
| `tool_create_directory` | Make directories recursively |
| `tool_list_files` | List files and folders (with recursion option) |
| `tool_move_file` | Move or rename files/folders |
| `tool_get_file_info` | Fetch metadata about a file |
| `tool_replace_line` | Replace a specific line in a file |
| `tool_replace_block` | Replace a text block (with optional regex) |
| `tool_apply_patch` | Apply unified diff patches safely |
| `tool_search_code` | Ripgrep-based recursive code search |
| `tool_lint_json` | Validate JSON files |
| `tool_lint_python` | Run flake8 linter on Python files |
| `tool_static_analysis_python` | Static analysis with pylint |
| `tool_read_multiple_files` | Batch-read multiple files |
| `tool_process_files` | Async batch file processing |
| `tool_search_files` | Pattern-based filename search |
| `tool_search_replace` | Search and replace text in a file |
| `tool_line_python_file` | Read Python file with line numbers for better context |


## Roadmap

- Multi-language linting (JS, TS, CSS, Shell scripts)
- Advanced multi-file diffing and patching
- Smithery
- CLI companion tool
- Claude Desktop templates
- Performance enhancements for enterprise-scale repositories


## Contribute

We’re building UltimateCoder to be a developer-first, automation-friendly powerhouse.

- Star the repo to support development
- Open issues for bugs or ideas
- Submit PRs to improve functionality
- Share feedback and ideas in Discussions

Every contribution matters.


## License

MIT License.  
Use it, build on it, and make it your own.



