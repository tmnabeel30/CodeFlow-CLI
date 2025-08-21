"""Agentic AI System with Cursor AI-style capabilities for CodeFlow CLI."""

import sys
import os
import glob
import re
import difflib
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import FormattedText
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.prompt import Prompt, Confirm
from rich.text import Text
from rich.table import Table
from rich.status import Status
from rich import box

from .config import ConfigurationManager
from .api_client import GroqAPIClient
from .model_selector import ModelSelector
from .file_operations import FileOperations


class ToolType(Enum):
    """Types of tools available to the agentic system."""
    SEARCH = "search"
    READ = "read"
    WRITE = "write"
    EDIT = "edit"
    CREATE = "create"
    DELETE = "delete"
    ANALYZE = "analyze"
    EXECUTE = "execute"
    DEBUG = "debug"


@dataclass
class ToolCall:
    """Represents a tool call with parameters and results."""
    tool_name: str
    tool_type: ToolType
    parameters: Dict[str, Any]
    result: Optional[Any] = None
    success: bool = False
    error_message: Optional[str] = None
    execution_time: float = 0.0


@dataclass
class AgenticContext:
    """Context information for the agentic system."""
    workspace_path: Path
    accessible_files: Set[str] = field(default_factory=set)
    current_file_context: Optional[Dict[str, Any]] = None
    recent_changes: List[Dict[str, Any]] = field(default_factory=list)
    tool_calls: List[ToolCall] = field(default_factory=list)
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    project_structure: Dict[str, Any] = field(default_factory=dict)
    debugging_info: Dict[str, Any] = field(default_factory=dict)


class AgenticSystem:
    """Advanced agentic AI system with Cursor AI-style capabilities."""
    
    def __init__(self, config: ConfigurationManager, api_client: GroqAPIClient):
        """Initialize the agentic system.
        
        Args:
            config: Configuration manager instance
            api_client: Groq API client instance
        """
        self.config = config
        self.api_client = api_client
        self.model_selector = ModelSelector(api_client)
        self.file_ops = FileOperations(api_client)
        self.console = Console()
        
        # Agentic context
        self.context = AgenticContext(workspace_path=Path.cwd())
        
        # Input styling and history
        history_file = config.config_dir / "agentic_history.txt"
        self.history = FileHistory(str(history_file))
        self.prompt_style = Style.from_dict({
            'prompt': 'bold ansicyan',
            'toolbar': 'reverse ansimagenta'
        })
        
        # Enhanced command completions with agentic tools
        self.command_completer = WordCompleter([
            '/help', '/files', '/structure', '/model', '/status', '/exit', '/qna', '/mode',
            '/search', '/read', '/edit', '/create', '/delete', '/analyze', '/debug',
            '/context', '/history', '/undo', '/redo', '/tools', '/plan', '/execute'
        ])
        
        # Agent state
        self.current_model = config.get_default_model()
        self.is_debugging = False
        self.execution_plan: List[Dict[str, Any]] = []
        
        # Auto-initialize
        self._initialize_workspace()
    
    def _initialize_workspace(self) -> None:
        """Initialize the workspace with comprehensive scanning."""
        with Status("[bold green]🔍 Initializing Agentic Workspace...", console=self.console):
            self._scan_workspace()
            self._analyze_project_structure()
            self._build_context_index()
    
    def _scan_workspace(self) -> None:
        """Comprehensive workspace scanning."""
        self.context.accessible_files = self._get_accessible_files()
        self.console.print(f"[green]✓ Found {len(self.context.accessible_files)} accessible files[/green]")
    
    def _get_accessible_files(self) -> Set[str]:
        """Get all accessible files with enhanced filtering."""
        files = set()
        
        # Extended file extensions
        extensions = {
            '*.py', '*.js', '*.ts', '*.jsx', '*.tsx', '*.html', '*.css', '*.scss',
            '*.json', '*.yaml', '*.yml', '*.md', '*.txt', '*.sh', '*.bash',
            '*.java', '*.cpp', '*.c', '*.h', '*.hpp', '*.go', '*.rs', '*.php',
            '*.rb', '*.sql', '*.xml', '*.toml', '*.ini', '*.conf', '*.vue',
            '*.svelte', '*.r', '*.m', '*.swift', '*.kt', '*.scala', '*.clj'
        }
        
        # Scan for files
        for ext in extensions:
            files.update(glob.glob(str(self.context.workspace_path / "**" / ext), recursive=True))
        
        # Important files without extensions
        important_files = [
            'Dockerfile', 'Makefile', 'README', 'LICENSE', '.env', '.gitignore',
            'package.json', 'requirements.txt', 'Cargo.toml', 'pom.xml',
            'build.gradle', 'Gemfile', 'composer.json', 'pubspec.yaml'
        ]
        for file in important_files:
            files.update(glob.glob(str(self.context.workspace_path / "**" / file), recursive=True))
        
        # Filter out common directories
        ignore_dirs = {
            '.git', '__pycache__', 'node_modules', '.venv', 'venv', 'env',
            '.pytest_cache', '.mypy_cache', 'dist', 'build', 'target',
            '.idea', '.vscode', 'coverage', '.coverage'
        }
        filtered_files = set()
        
        for file_path in files:
            path = Path(file_path)
            if not any(ignore_dir in path.parts for ignore_dir in ignore_dirs):
                filtered_files.add(str(path))
        
        return filtered_files
    
    def _analyze_project_structure(self) -> None:
        """Analyze project structure and categorize files."""
        structure = {
            'type': 'unknown',
            'main_files': [],
            'config_files': [],
            'source_files': [],
            'test_files': [],
            'documentation': [],
            'dependencies': []
        }
        
        for file_path in self.context.accessible_files:
            path = Path(file_path)
            file_name = path.name.lower()
            
            # Categorize files
            if file_name in ['package.json', 'requirements.txt', 'cargo.toml', 'pom.xml']:
                structure['dependencies'].append(str(path))
            elif file_name.startswith('readme') or file_name.endswith('.md'):
                structure['documentation'].append(str(path))
            elif 'test' in file_name or 'spec' in file_name:
                structure['test_files'].append(str(path))
            elif file_name in ['dockerfile', 'docker-compose.yml', 'makefile']:
                structure['config_files'].append(str(path))
            elif path.suffix in ['.py', '.js', '.ts', '.java', '.cpp', '.go']:
                structure['source_files'].append(str(path))
            
            # Determine project type
            if file_name == 'package.json':
                structure['type'] = 'nodejs'
            elif file_name == 'requirements.txt':
                structure['type'] = 'python'
            elif file_name == 'cargo.toml':
                structure['type'] = 'rust'
            elif file_name == 'pom.xml':
                structure['type'] = 'java'
        
        # Set main files
        if structure['type'] == 'python':
            structure['main_files'] = [f for f in structure['source_files'] if 'main' in f.lower() or 'app' in f.lower()]
        elif structure['type'] == 'nodejs':
            structure['main_files'] = [f for f in structure['source_files'] if 'index' in f.lower() or 'app' in f.lower()]
        
        self.context.project_structure = structure
    
    def _build_context_index(self) -> None:
        """Build a searchable index of file contents."""
        self.context.file_index = {}
        for file_path in list(self.context.accessible_files)[:50]:  # Limit to first 50 files
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.context.file_index[file_path] = {
                        'content': content,
                        'size': len(content),
                        'lines': content.count('\n') + 1
                    }
            except Exception:
                continue
    
    def search_codebase(self, query: str, target_directories: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Semantic search through the codebase."""
        results = []
        query_lower = query.lower()
        
        # Search in file names and contents
        for file_path, file_info in self.context.file_index.items():
            if target_directories:
                if not any(target_dir in file_path for target_dir in target_directories):
                    continue
            
            # Search in file name
            if query_lower in Path(file_path).name.lower():
                results.append({
                    'file': file_path,
                    'match_type': 'filename',
                    'relevance': 0.8
                })
            
            # Search in content
            content = file_info['content']
            if query_lower in content.lower():
                # Find matching lines
                lines = content.split('\n')
                matching_lines = []
                for i, line in enumerate(lines, 1):
                    if query_lower in line.lower():
                        matching_lines.append({
                            'line_number': i,
                            'content': line.strip()
                        })
                
                if matching_lines:
                    results.append({
                        'file': file_path,
                        'match_type': 'content',
                        'relevance': 0.6,
                        'matching_lines': matching_lines[:5]  # Limit to first 5 matches
                    })
        
        # Sort by relevance
        results.sort(key=lambda x: x['relevance'], reverse=True)
        return results[:10]  # Return top 10 results
    
    def read_file(self, file_path: str, start_line: Optional[int] = None, end_line: Optional[int] = None) -> Dict[str, Any]:
        """Read file contents with optional line range."""
        try:
            if file_path not in self.context.accessible_files:
                return {'error': f'File not accessible: {file_path}'}
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            result = {
                'file': file_path,
                'content': content,
                'size': len(content),
                'lines': content.count('\n') + 1
            }
            
            if start_line is not None or end_line is not None:
                lines = content.split('\n')
                start = start_line or 1
                end = end_line or len(lines)
                result['content'] = '\n'.join(lines[start-1:end])
                result['line_range'] = f'{start}-{end}'
            
            return result
        except Exception as e:
            return {'error': f'Error reading file: {str(e)}'}
    
    def edit_file(self, file_path: str, changes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Apply edits to a file with detailed change tracking."""
        try:
            if file_path not in self.context.accessible_files:
                return {'error': f'File not accessible: {file_path}'}
            
            # Read current content
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Apply changes
            new_content = original_content
            applied_changes = []
            
            for change in changes:
                change_type = change.get('type', 'replace')
                
                if change_type == 'replace':
                    old_text = change.get('old_text', '')
                    new_text = change.get('new_text', '')
                    if old_text in new_content:
                        new_content = new_content.replace(old_text, new_text)
                        applied_changes.append({
                            'type': 'replace',
                            'old_text': old_text,
                            'new_text': new_text
                        })
                
                elif change_type == 'insert':
                    position = change.get('position', 0)
                    text = change.get('text', '')
                    if position <= len(new_content):
                        new_content = new_content[:position] + text + new_content[position:]
                        applied_changes.append({
                            'type': 'insert',
                            'position': position,
                            'text': text
                        })
                
                elif change_type == 'delete':
                    start = change.get('start', 0)
                    end = change.get('end', 0)
                    if start < end <= len(new_content):
                        deleted_text = new_content[start:end]
                        new_content = new_content[:start] + new_content[end:]
                        applied_changes.append({
                            'type': 'delete',
                            'start': start,
                            'end': end,
                            'deleted_text': deleted_text
                        })
            
            # Write changes
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            # Track change
            self.context.recent_changes.append({
                'file': file_path,
                'timestamp': time.time(),
                'changes': applied_changes,
                'original_size': len(original_content),
                'new_size': len(new_content)
            })
            
            return {
                'success': True,
                'file': file_path,
                'changes_applied': len(applied_changes),
                'changes': applied_changes
            }
            
        except Exception as e:
            return {'error': f'Error editing file: {str(e)}'}
    
    def create_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """Create a new file."""
        try:
            # Ensure directory exists
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Add to accessible files
            self.context.accessible_files.add(file_path)
            
            # Track creation
            self.context.recent_changes.append({
                'file': file_path,
                'timestamp': time.time(),
                'action': 'created',
                'size': len(content)
            })
            
            return {
                'success': True,
                'file': file_path,
                'size': len(content)
            }
            
        except Exception as e:
            return {'error': f'Error creating file: {str(e)}'}
    
    def delete_file(self, file_path: str) -> Dict[str, Any]:
        """Delete a file."""
        try:
            if file_path not in self.context.accessible_files:
                return {'error': f'File not accessible: {file_path}'}
            
            # Backup content before deletion
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Delete file
            Path(file_path).unlink()
            
            # Remove from accessible files
            self.context.accessible_files.discard(file_path)
            
            # Track deletion
            self.context.recent_changes.append({
                'file': file_path,
                'timestamp': time.time(),
                'action': 'deleted',
                'backup_content': content
            })
            
            return {
                'success': True,
                'file': file_path,
                'backup_available': True
            }
            
        except Exception as e:
            return {'error': f'Error deleting file: {str(e)}'}
    
    def analyze_code(self, file_path: str) -> Dict[str, Any]:
        """Analyze code structure and quality."""
        try:
            if file_path not in self.context.accessible_files:
                return {'error': f'File not accessible: {file_path}'}
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            analysis = {
                'file': file_path,
                'size': len(content),
                'lines': content.count('\n') + 1,
                'language': self._detect_language(file_path),
                'complexity': self._analyze_complexity(content),
                'structure': self._analyze_structure(content),
                'issues': self._detect_issues(content)
            }
            
            return analysis
            
        except Exception as e:
            return {'error': f'Error analyzing file: {str(e)}'}
    
    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension."""
        ext = Path(file_path).suffix.lower()
        language_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.jsx': 'React JSX',
            '.tsx': 'React TSX',
            '.html': 'HTML',
            '.css': 'CSS',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.go': 'Go',
            '.rs': 'Rust',
            '.php': 'PHP',
            '.rb': 'Ruby',
            '.sql': 'SQL'
        }
        return language_map.get(ext, 'Unknown')
    
    def _analyze_complexity(self, content: str) -> Dict[str, Any]:
        """Analyze code complexity."""
        lines = content.split('\n')
        
        # Basic complexity metrics
        complexity = {
            'total_lines': len(lines),
            'code_lines': len([l for l in lines if l.strip() and not l.strip().startswith('#')]),
            'comment_lines': len([l for l in lines if l.strip().startswith('#')]),
            'empty_lines': len([l for l in lines if not l.strip()]),
            'functions': len(re.findall(r'def\s+\w+', content)),
            'classes': len(re.findall(r'class\s+\w+', content)),
            'imports': len(re.findall(r'import\s+', content))
        }
        
        return complexity
    
    def _analyze_structure(self, content: str) -> Dict[str, Any]:
        """Analyze code structure."""
        structure = {
            'has_main': 'if __name__' in content,
            'has_functions': 'def ' in content,
            'has_classes': 'class ' in content,
            'has_imports': 'import ' in content,
            'has_docstrings': '"""' in content or "'''" in content
        }
        
        return structure
    
    def _detect_issues(self, content: str) -> List[Dict[str, Any]]:
        """Detect potential issues in code."""
        issues = []
        
        # Check for common issues
        if len(content) > 10000:
            issues.append({
                'type': 'large_file',
                'severity': 'warning',
                'message': 'File is very large (>10KB)'
            })
        
        if content.count('\n') > 500:
            issues.append({
                'type': 'many_lines',
                'severity': 'warning',
                'message': 'File has many lines (>500)'
            })
        
        # Check for TODO/FIXME comments
        todos = re.findall(r'#\s*(TODO|FIXME|HACK|XXX).*', content, re.IGNORECASE)
        for todo in todos:
            issues.append({
                'type': 'todo_comment',
                'severity': 'info',
                'message': f'Found {todo} comment'
            })
        
        return issues
    
    def execute_tool_call(self, tool_call: ToolCall) -> ToolCall:
        """Execute a tool call and return results."""
        start_time = time.time()
        
        try:
            if tool_call.tool_type == ToolType.SEARCH:
                results = self.search_codebase(
                    tool_call.parameters.get('query', ''),
                    tool_call.parameters.get('target_directories')
                )
                tool_call.result = results
                tool_call.success = True
            
            elif tool_call.tool_type == ToolType.READ:
                result = self.read_file(
                    tool_call.parameters.get('file_path', ''),
                    tool_call.parameters.get('start_line'),
                    tool_call.parameters.get('end_line')
                )
                tool_call.result = result
                tool_call.success = 'error' not in result
            
            elif tool_call.tool_type == ToolType.EDIT:
                result = self.edit_file(
                    tool_call.parameters.get('file_path', ''),
                    tool_call.parameters.get('changes', [])
                )
                tool_call.result = result
                tool_call.success = result.get('success', False)
            
            elif tool_call.tool_type == ToolType.CREATE:
                result = self.create_file(
                    tool_call.parameters.get('file_path', ''),
                    tool_call.parameters.get('content', '')
                )
                tool_call.result = result
                tool_call.success = result.get('success', False)
            
            elif tool_call.tool_type == ToolType.DELETE:
                result = self.delete_file(tool_call.parameters.get('file_path', ''))
                tool_call.result = result
                tool_call.success = result.get('success', False)
            
            elif tool_call.tool_type == ToolType.ANALYZE:
                result = self.analyze_code(tool_call.parameters.get('file_path', ''))
                tool_call.result = result
                tool_call.success = 'error' not in result
            
            else:
                tool_call.error_message = f'Unknown tool type: {tool_call.tool_type}'
                tool_call.success = False
        
        except Exception as e:
            tool_call.error_message = str(e)
            tool_call.success = False
        
        tool_call.execution_time = time.time() - start_time
        self.context.tool_calls.append(tool_call)
        
        return tool_call
    
    def show_status(self) -> None:
        """Display comprehensive system status."""
        status_info = f"""
[bold]🤖 Agentic System Status[/bold]

[cyan]Workspace:[/cyan] {self.context.workspace_path}
[cyan]Project Type:[/cyan] {self.context.project_structure.get('type', 'Unknown')}
[cyan]Files:[/cyan] {len(self.context.accessible_files)} accessible
[cyan]Current Model:[/cyan] {self.current_model}
[cyan]Tool Calls:[/cyan] {len(self.context.tool_calls)} executed
[cyan]Recent Changes:[/cyan] {len(self.context.recent_changes)} files modified
[cyan]Debug Mode:[/cyan] {'Active' if self.is_debugging else 'Inactive'}

[cyan]Project Structure:[/cyan]
• Main Files: {len(self.context.project_structure.get('main_files', []))}
• Source Files: {len(self.context.project_structure.get('source_files', []))}
• Test Files: {len(self.context.project_structure.get('test_files', []))}
• Config Files: {len(self.context.project_structure.get('config_files', []))}
        """.strip()
        
        panel = Panel(
            status_info,
            title="📊 Agentic System Status",
            border_style="blue",
            padding=(1, 2)
        )
        
        self.console.print(panel)
    
    def show_tools(self) -> None:
        """Display available tools and their usage."""
        tools_info = """
[bold]🛠️ Available Agentic Tools[/bold]

[cyan]Search & Analysis:[/cyan]
• /search <query> - Semantic codebase search
• /analyze <file> - Analyze code structure and quality
• /read <file> [start:end] - Read file contents

[cyan]File Operations:[/cyan]
• /edit <file> - Edit file with intelligent changes
• /create <file> - Create new file
• /delete <file> - Delete file (with backup)

[cyan]Context & History:[/cyan]
• /context - Show current context
• /history - Show recent changes
• /undo - Undo last change
• /redo - Redo last undone change

[cyan]Planning & Execution:[/cyan]
• /plan - Create execution plan
• /execute - Execute planned actions
• /debug - Enable/disable debug mode
        """.strip()
        
        panel = Panel(
            tools_info,
            title="🛠️ Agentic Tools",
            border_style="green",
            padding=(1, 2)
        )
        
        self.console.print(panel)
