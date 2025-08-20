# CodeFlow CLI

A beautiful, terminal-first AI coding assistant that works right inside your shell. CodeFlow helps you read, explore, and improve your codebase with an enhanced chat UI, diff previews, and safe, confirmed edits.

## Why CodeFlow?

- Stunning terminal UI with rich colors and syntax-highlighting
- Two modes that fit any workflow:
  - Q&A mode (read-only): ask questions about the codebase without making changes
  - Agent mode (write): propose and apply changes with diff previews and confirmation
- First-run CODEFLOW banner, helpful toolbar, and model-aware prompts
- File-aware assistance: list, read, preview, and edit files directly from chat
- Clear preview with green (+) and red (–) lines for diffs
- Slash commands with auto-completion in both modes

## Install

```bash
pip install codeflow-cli
```

## Quick Start

```bash
codeflow
```

On start, pick a mode:
- `qna` (read-only) to ask questions about your codebase
- `agent` (can modify files) to propose/apply improvements with confirmation

Switch modes anytime:
- `/agent` or `/mode agent`
- `/qna` or `/mode qna`

## Configuration

Set your Groq API key one of the following ways:

```bash
# Recommended: environment variable
export GROQ_API_KEY="your-groq-api-key"

# Or interactively
codeflow configure

# Or via flag
codeflow --api-key "your-groq-api-key"
```

## Common Commands

- `/help` show help
- `/files` list accessible files
- `/scan` rescan workspace
- `/read <file>` read and preview a file
- `/edit <file>` propose/apply edits (Agent mode)
- `/workspace` show workspace info
- `/model` change model
- `/clear` clear chat history
- `/exit` quit

## Examples

```bash
# Ask questions about the codebase
codeflow
You: Where is the CLI entry point defined?

# Read and preview a file
/read groq_agent/cli.py

# Propose an edit (Agent mode)
/agent
/edit groq_agent/enhanced_chat.py
"Improve the prompt styling and add a bottom toolbar."
```

## Uninstall

```bash
pip uninstall codeflow-cli
```

## Troubleshooting

- If `codeflow` isn’t found, ensure your Python scripts directory (e.g., `~/.local/bin` or `/opt/anaconda3/bin`) is on your PATH.
- If the Groq API key isn’t detected, export `GROQ_API_KEY` or run `codeflow configure`.
- For publishing guidance (maintainers), see `INSTALL.md`.

## License

MIT
