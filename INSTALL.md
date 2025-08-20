# Installation Guide

## Prerequisites

- Python 3.8 or higher
- A Groq API key (get one at https://console.groq.com/)

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

## Quick Start

### 1. Start interactive chat (default behavior)
```bash
codeflow
```

### 2. Send a single message
```bash
codeflow chat "Hello, how can you help me?"
```

### 3. Review a file
```bash
codeflow review myfile.py
```

### 4. List available models
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

## Next Steps

1. Read the [README.md](README.md) for detailed usage instructions
2. Try the interactive chat: `codeflow`
3. Review some code: `codeflow review yourfile.py`
4. Explore available models: `codeflow models`

## Support

If you encounter any issues:
1. Check the troubleshooting section above
2. Run `codeflow --help` for command options
3. Check the logs in `~/.groq/` directory
4. Open an issue on the project repository
