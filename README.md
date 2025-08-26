
https://github.com/user-attachments/assets/7eea7aab-147f-4e79-a3dc-0a72db44181f
# CodeFlow CLI

A powerful, terminal-first AI coding assistant with **advanced agentic capabilities**. CodeFlow helps you read, explore, analyze, and improve your codebase with an enhanced chat UI, intelligent tools, and safe, confirmed edits.


https://github.com/user-attachments/assets/55cf24aa-082c-459d-876a-d41bababb7fe




## 🚀 Why CodeFlow?

- **Advanced Agent Mode**: Enhanced AI capabilities with intelligent tool orchestration
- **Stunning terminal UI** with rich colors, syntax-highlighting, and interactive panels
- **Three powerful modes** that fit any workflow:
  - **Q&A Mode** (read-only): Ask questions about the codebase without making changes
  - **Agent Mode** (write): Propose and apply changes with diff previews and confirmati


on  
  - **Advanced Agent** (enhanced): Smart tools, semantic search, code analysis, and intelligent automation
- **Smart codebase understanding**: Automatic project structure analysis and context awareness
- **Semantic search capabilities**: Find code by meaning, not just text matching
- **Advanced code analysis**: Structure analysis, complexity metrics, and issue detection
- **Tool execution tracking**: Monitor and manage all AI operations with full transparency
- **Enhanced file operations**: Read, edit, create, and delete files with intelligent assistance
- **Real-time collaboration**: Switch between modes seamlessly during chat sessions

## Install

```bash
pip install codeflow-cli
```

## Quick Start

```bash
codeflow
```

On start, pick a mode:
- **Q&A Mode** (`1` or `qna`) - Read-only questions about your codebase
- **Agent Mode** (`2` or `agent`) - Propose/apply improvements with confirmation
- **Advanced Agent** (`3` or `advanced`) - Enhanced AI with smart tools and analysis

Switch modes anytime during chat:
- `/qna` - Switch to Q&A mode
- `/agent` - Switch to Agent mode
- `/mode <mode_name>` - Switch to specified mode

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

## 🛠️ Common Commands

### Universal Commands (All Modes)
- `/help` - Show mode-specific help and available commands
- `/model` - Change AI model with interactive selection
- `/clear` - Clear chat history
- `/exit` - Quit CodeFlow

### Q&A & Agent Mode Commands
- `/files` - List accessible files in workspace
- `/scan` - Rescan workspace for new files
- `/read <file>` - Read and preview a file with syntax highlighting
- `/workspace` - Show workspace information

### Agent Mode Commands
- `/edit <file1> [file2 ...]` - Propose/apply edits with diff preview and confirmation across multiple files

### 🚀 Advanced Agent Commands
- `/search <query>` - Semantic codebase search by meaning
- `/analyze <file>` - Analyze code structure, complexity, and quality
- `/read <file>` - Read file with enhanced analysis
- `/edit <file1> [file2 ...]` - Intelligent multi-file editing with AI assistance
- `/create <file1> [file2 ...]` - Create one or more files with AI assistance
- `/delete <file>` - Delete files with confirmation
- `/files` - List all accessible files with details
- `/scan` - Rescan workspace for new files
- `/workspace` - Show workspace information
- `/status` - Show comprehensive system status
- `/tools` - Display all available agentic tools
- `/context` - Show current workspace context
- `/history` - Show recent changes and operations
- `/shortcuts` - Show quick model switching shortcuts

### 🔄 Quick Model Switching
- `/fast`, `/balanced`, `/powerful`, `/ultra` - Quick model switches
- `/next`, `/prev` - Cycle through available models

### 🔀 Mode Switching (Available in all modes)
- `/qna` - Switch to Q&A mode (read-only analysis)
- `/agent` - Switch to Agent mode (file modifications)
- `/advanced` - Switch to Advanced Agent mode (enhanced AI capabilities)

## 📚 Examples

### Q&A Mode (Read-Only Analysis)
```bash
# Start CodeFlow and select Q&A mode
codeflow
> Select mode: 1 (Q&A Mode)

# Ask questions about your codebase
You: Where is the CLI entry point defined?
AI: The CLI entry point is defined in `groq_agent/cli.py`...

# Read and preview files
/read groq_agent/cli.py

# Switch to other modes anytime
/agent      # Switch to Agent mode
/advanced   # Switch to Advanced Agent mode
```

### Agent Mode (File Modifications)
```bash
# Switch to Agent mode
/agent

# Propose edits with diff preview
# Edit multiple files with shared context
/edit groq_agent/enhanced_chat.py groq_agent/agentic_chat.py
What changes? Improve the prompt styling and add a bottom toolbar.
# Shows diff, asks for confirmation before applying

# Switch to other modes anytime
/qna        # Switch to Q&A mode
/advanced   # Switch to Advanced Agent mode
```

### 🚀 Advanced Agent Mode
```bash
# Start with Advanced Agent mode
codeflow
> Select mode: 3 (Advanced Agent)

# Semantic search across codebase
/search "user authentication logic"
# Finds relevant code by meaning, not just keywords

# Analyze code structure and quality
/analyze groq_agent/api_client.py
# Shows metrics: complexity, structure, potential issues

# Get comprehensive system status
/status
# Shows workspace info, recent changes, tool usage

# Intelligent file editing with diff preview
/edit src/main.py tests/test_main.py
What changes? Add error handling for API calls and update tests accordingly
# AI shows diffs with green + for additions, red - for removals

# Natural language file modifications
"Add green color to website" → Modifies existing files with diff preview
"Change button style" → Shows changes with + and - indicators

# Intelligent minimal file creation
"Create a website for top schools in Delhi"
# AI automatically:
# 1. Determines ONLY the files needed (e.g., just index.html and styles.css)
# 2. Creates minimal file structure (no unnecessary README.md, etc.)
# 3. Generates content for each file
# 4. Shows preview of all files
# 5. Asks for your action (Accept/Reject/Review/Edit)

# Examples of intelligent file creation:
"Create a list of schools" → Creates only schools.json
"Make a simple website" → Creates only index.html
"Create a Python script" → Creates only main.py

# Command-line multi-file creation
/create src/main.py src/config.py src/utils.py
# AI automatically determines content for each file

# List and manage files
/files       # List all accessible files
/scan        # Rescan workspace for new files
/workspace   # Show workspace information

# Switch to other modes anytime
/qna         # Switch to Q&A mode
/agent       # Switch to Agent mode
```

### Quick Model Switching
```bash
# Quick switches during any mode
/fast      # Switch to fastest model
/powerful  # Switch to most capable model
/next      # Cycle to next model
/shortcuts # Show all quick commands
```

## Uninstall

```bash
pip uninstall codeflow-cli
```

## 🎯 Key Features

### 🤖 Advanced AI Capabilities
- **Semantic Understanding**: Search code by meaning, not just text
- **Context Awareness**: AI understands your project structure and recent changes
- **Smart File Creation**: Creates only the files you actually need (no unnecessary README.md, etc.)
- **Tool Orchestration**: Coordinate multiple operations intelligently
- **Change Tracking**: Monitor all modifications with full history
- **Quality Analysis**: Automated code structure and complexity analysis

### 🎨 Enhanced User Experience
- **Rich Terminal UI**: Beautiful panels, tables, and syntax highlighting
- **Interactive Model Selection**: Easy model switching with arrow key navigation
- **Command Auto-completion**: Intelligent slash command suggestions
- **Real-time Status**: Progress indicators and system status updates
- **Mode Flexibility**: Seamless switching between Q&A, Agent, and Agentic modes

### 🔧 Smart Development Tools
- **Project Structure Analysis**: Automatic detection of project type and architecture
- **File Operations**: Enhanced read, edit, create, and delete with AI assistance
- **Diff Previews**: Clear visualization of changes before applying
- **Workspace Awareness**: Intelligent file filtering and context building
- **Error Recovery**: Robust error handling with helpful suggestions

## 🚨 Troubleshooting

- **Command not found**: Ensure your Python scripts directory (e.g., `~/.local/bin` or `/opt/anaconda3/bin`) is on your PATH
- **API key issues**: Export `GROQ_API_KEY` or run `codeflow configure`
- **Model selection problems**: Try using arrow keys, Tab, or Enter in the model selector
- **Advanced Agent mode not available**: Update to the latest version with `pip install --upgrade codeflow-cli`
- **Publishing guidance** (maintainers): See `INSTALL.md`

## 📄 License

MIT License - Created by **TM NABEEL @tmnabeel30**

---

**CodeFlow CLI** - Bringing advanced AI capabilities to your terminal 🚀
