#!/usr/bin/env python3
"""Setup script for Groq CLI Agent."""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file robustly regardless of CWD
here = Path(__file__).parent
readme_path = here / "README.md"
try:
    long_description = readme_path.read_text(encoding="utf-8")
except FileNotFoundError:
    long_description = "Groq CLI Agent"

# Read requirements from pyproject.toml
def get_requirements():
    """Get requirements from pyproject.toml."""
    requirements = [
        "groq>=0.4.0",
        "click>=8.0.0",
        "rich>=13.0.0",
        "prompt-toolkit>=3.0.0",
        "pyyaml>=6.0",
        "colorama>=0.4.6",
        "typer>=0.9.0",
    ]
    return requirements

setup(
    name="codeflow-cli",
    version="0.1.1",
    author="Groq CLI Team",
    description="Interactive CLI agent for Groq API with chat, model selection, and file diff capabilities",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/codeflow-cli",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=get_requirements(),
    entry_points={
        "console_scripts": [
            "groq-agent=groq_agent.cli:main",
            "codeflow=groq_agent.cli:main",
        ],
    },
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    include_package_data=True,
    license_files=[],
    zip_safe=False,
)

