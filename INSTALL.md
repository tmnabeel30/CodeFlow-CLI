# CodeFlow CLI - Installation Guide

**Cursor AI-style agentic capabilities for your terminal** 🚀

## Prerequisites

- Python 3.8 or higher
- A Groq API key (get one at https://console.groq.com/)
- Terminal with color support (most modern terminals)

## Installation Methods

### Method 1: Install from source (recommended for development)

```bash
# Clone the repository
git clone <repository-url>
cd codeflow

# Install in development mode
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

### Method 2: Install using pip

```bash
# Install directly from PyPI (when published)
pip install codeflow-cli
```

### Method 3: Install using requirements.txt

```bash
# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

## Configuration

### 1. Set up your API key

You can set your API key in several ways:

**Option A: Environment variable (recommended)**
```bash
export GROQ_API_KEY="your-api-key-here"
```

**Option B: During first run**
```bash
codeflow configure
```

**Option C: Command line**
```bash
codeflow --api-key "your-api-key-here"
```

### 2. Set a default model (optional)

```bash
# Interactive model selection
codeflow --select-model

# Or specify directly
codeflow --model llama-2-70B
```

## 🚀 Quick Start

### 1. Start CodeFlow (Interactive Mode Selection)
```bash
codeflow
```
You'll see three modes:
- **Q&A Mode** (1) - Read-only codebase questions
- **Agent Mode** (2) - File modifications with confirmation
- **Agentic Mode** (3) - Advanced Cursor AI-style capabilities

### 2. Try Agentic Mode (Recommended)
```bash
codeflow
# Select: 3 (Agentic Mode)

# Try these commands:
/search "authentication logic"     # Semantic search
/analyze src/main.py              # Code analysis
/status                           # System status
/tools                           # Show all tools
```

### 3. Send a single message (Legacy)
```bash
codeflow chat "Hello, how can you help me?"
```

### 4. Review a file (Legacy)
```bash
codeflow review myfile.py
```

### 5. List available models
```bash
codeflow models
```

## Development Setup

### 1. Install development dependencies
```bash
pip install -e ".[dev]"
```

### 2. Run tests
```bash
pytest
```

### 3. Format code
```bash
black .
flake8 .
mypy .
```

### 4. Run the example
```bash
python example_usage.py
```

## Troubleshooting

### Common Issues

1. **"No API key found" error**
   - Make sure you've set the GROQ_API_KEY environment variable
   - Or run `codeflow configure` to set it up

2. **Import errors**
   - Make sure you've installed all dependencies: `pip install -r requirements.txt`
   - Try installing in development mode: `pip install -e .`

3. **Permission errors**
   - On macOS/Linux, you might need to use `sudo pip install` or install in a virtual environment

### Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -e .

# Deactivate when done
deactivate
```

## Configuration File Location

The CLI stores configuration in:
- **macOS/Linux**: `~/.groq/config.yaml`
- **Windows**: `%USERPROFILE%\.groq\config.yaml`

You can customize the location using the `--config-dir` option.

## 🎯 Next Steps

1. **Read the [README.md](README.md)** for detailed usage instructions and examples
2. **Try Agentic Mode**: `codeflow` → Select mode 3 for advanced capabilities
3. **Explore semantic search**: Use `/search "your query"` to find code by meaning
4. **Analyze your code**: Use `/analyze filename.py` for structure insights
5. **Check system status**: Use `/status` to see workspace information
6. **Learn all commands**: Use `/help` in any mode for available commands

## 🚀 Agentic Mode Features

The new **Agentic Mode** brings Cursor AI-style capabilities:

- **Semantic Search**: Find code by meaning, not just text
- **Code Analysis**: Structure, complexity, and quality metrics
- **Context Awareness**: AI understands your project structure
- **Tool Orchestration**: Coordinate multiple operations intelligently
- **Change Tracking**: Monitor all modifications with history
- **Enhanced UI**: Rich terminal interface with panels and tables

## 📞 Support

If you encounter any issues:
1. **Check troubleshooting**: Review the troubleshooting section above
2. **Use help commands**: Run `codeflow --help` or `/help` in any mode
3. **Check logs**: Look in `~/.groq/` directory for detailed logs
4. **Model selection issues**: Try using arrow keys, Tab, or Enter in model selector
5. **Agentic mode problems**: Ensure you have the latest version
6. **Report issues**: Open an issue on the project repository

---

**CodeFlow CLI** - Created by **TM NABEEL @tmnabeel30** 🚀
