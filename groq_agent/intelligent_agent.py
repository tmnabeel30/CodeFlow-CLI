"""Intelligent Agent that can read, understand, and modify files automatically."""

import sys
import os
import glob
import re
import difflib
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple
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
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text
from rich.table import Table
from rich.status import Status
from rich import box
import time

from .config import ConfigurationManager
from .api_client import GroqAPIClient
from .model_selector import ModelSelector
from .file_operations import FileOperations
from .handbook_manager import HandbookManager
from .recursive_agent import RecursiveAgent


class IntelligentAgent:
    """Intelligent agent that can read, understand, and modify files automatically."""
    
    def __init__(self, config: ConfigurationManager, api_client: GroqAPIClient, 
                 handbook_manager: Optional[HandbookManager] = None):
        """Initialize the intelligent agent.
        
        Args:
            config: Configuration manager instance
            api_client: Groq API client instance
            handbook_manager: Optional handbook manager instance
        """
        self.config = config
        self.api_client = api_client
        self.model_selector = ModelSelector(api_client)
        self.file_ops = FileOperations(api_client)
        self.handbook_manager = handbook_manager
        self.console = Console()
        
        # Input styling and history (align with Q&A UI)
        history_file = config.config_dir / "agent_history.txt"
        self.history = FileHistory(str(history_file))
        self.prompt_style = Style.from_dict({
            'prompt': 'bold ansicyan',
            'toolbar': 'reverse ansimagenta'
        })
        self.command_completer = WordCompleter([
            '/help', '/files', '/structure', '/model', '/status', '/exit', '/qna', '/mode',
            '/handbook', '/recursive', '/goals', '/context'
        ])
        
        # Agent state
        self.current_model = config.get_default_model()
        self.workspace_path = Path.cwd()
        self.accessible_files: Set[str] = set()
        self.file_contents: Dict[str, str] = {}
        self.project_structure: Dict[str, Any] = {}
        
        # Recursive agent integration
        self.recursive_agent: Optional[RecursiveAgent] = None
        
        # Auto-scan workspace
        self._scan_workspace()
        self._analyze_project_structure()
    
    def _scan_workspace(self) -> None:
        """Scan workspace for all accessible files."""
        with Status("[bold green]🔍 Scanning workspace...", console=self.console):
            self.accessible_files = self._get_accessible_files()
    
    def _get_accessible_files(self) -> Set[str]:
        """Get all accessible files in the workspace."""
        files = set()
        
        # Common file extensions
        extensions = {
            '*.py', '*.js', '*.ts', '*.jsx', '*.tsx', '*.html', '*.css', 
            '*.json', '*.yaml', '*.yml', '*.md', '*.txt', '*.sh', '*.bash',
            '*.java', '*.cpp', '*.c', '*.h', '*.hpp', '*.go', '*.rs', '*.php',
            '*.rb', '*.sql', '*.xml', '*.toml', '*.ini', '*.conf'
        }
        
        # Scan for files
        for ext in extensions:
            files.update(glob.glob(str(self.workspace_path / "**" / ext), recursive=True))
        
        # Important files without extensions
        important_files = ['Dockerfile', 'Makefile', 'README', 'LICENSE', '.env', '.gitignore']
        for file in important_files:
            files.update(glob.glob(str(self.workspace_path / "**" / file), recursive=True))
        
        # Filter out common directories
        ignore_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', 'env', '.pytest_cache'}
        filtered_files = set()
        
        for file_path in files:
            path = Path(file_path)
            if not any(ignore_dir in path.parts for ignore_dir in ignore_dirs):
                filtered_files.add(str(path))
        
        return filtered_files
    
    def _analyze_project_structure(self) -> None:
        """Analyze the project structure and key files."""
        with Status("[bold blue]🧠 Analyzing project structure...", console=self.console):
            self.project_structure = {
                'type': self._detect_project_type(),
                'main_files': self._find_main_files(),
                'config_files': self._find_config_files(),
                'source_files': self._find_source_files(),
                'test_files': self._find_test_files()
            }
    
    def _detect_project_type(self) -> str:
        """Detect the type of project."""
        files = [Path(f).name for f in self.accessible_files]
        
        if any(f.endswith('.py') for f in files):
            return 'python'
        elif any(f.endswith('.js') or f.endswith('.ts') for f in files):
            return 'javascript'
        elif any(f.endswith('.html') for f in files):
            return 'web'
        elif any(f.endswith('.java') for f in files):
            return 'java'
        else:
            return 'unknown'
    
    def _find_main_files(self) -> List[str]:
        """Find main application files."""
        main_files = []
        for file_path in self.accessible_files:
            path = Path(file_path)
            if any(name in path.name.lower() for name in ['main', 'app', 'index', 'server']):
                main_files.append(str(path))
        return main_files
    
    def _find_config_files(self) -> List[str]:
        """Find configuration files."""
        config_files = []
        for file_path in self.accessible_files:
            path = Path(file_path)
            if any(name in path.name.lower() for name in ['config', 'settings', 'package.json', 'requirements.txt']):
                config_files.append(str(file_path))
        return config_files
    
    def _find_source_files(self) -> List[str]:
        """Find source code files."""
        source_files = []
        for file_path in self.accessible_files:
            path = Path(file_path)
            if path.suffix in ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c']:
                source_files.append(str(file_path))
        return source_files
    
    def _find_test_files(self) -> List[str]:
        """Find test files."""
        test_files = []
        for file_path in self.accessible_files:
            path = Path(file_path)
            if 'test' in path.name.lower() or 'spec' in path.name.lower():
                test_files.append(str(file_path))
        return test_files
    
    def _read_file_content(self, file_path: str) -> str:
        """Read file content with caching."""
        if file_path not in self.file_contents:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.file_contents[file_path] = f.read()
            except Exception as e:
                self.console.print(f"[red]Error reading {file_path}: {e}[/red]")
                return ""
        return self.file_contents[file_path]
    
    def _get_relevant_files(self, query: str) -> List[str]:
        """Get files relevant to the user's query."""
        query_lower = query.lower()
        relevant_files = []
        
        # Critical system files that should never be modified
        protected_files = {
            'groq_agent/cli.py',
            'groq_agent/__init__.py',
            'pyproject.toml',
            'setup.py',
            'requirements.txt',
            'README.md',
            '.gitignore',
            'Makefile'
        }
        
        # Keywords that might indicate specific file types
        keywords = {
            'task': ['task', 'todo', 'job', 'assignment'],
            'employee': ['employee', 'user', 'worker', 'staff'],
            'employer': ['employer', 'manager', 'admin', 'boss'],
            'database': ['db', 'database', 'model', 'schema'],
            'api': ['api', 'route', 'endpoint', 'controller'],
            'frontend': ['frontend', 'ui', 'component', 'page'],
            'backend': ['backend', 'server', 'service']
        }
        
        for file_path in self.accessible_files:
            # Skip protected system files
            if file_path in protected_files:
                continue
                
            path = Path(file_path)
            file_content = self._read_file_content(file_path)
            file_content_lower = file_content.lower()
            
            # Check if file name or content matches query
            if (any(keyword in path.name.lower() for keyword in query_lower.split()) or
                any(keyword in file_content_lower for keyword in query_lower.split())):
                relevant_files.append(file_path)
        
        return relevant_files[:5]  # Limit to top 5 most relevant
    
    def process_request(self, user_input: str) -> str:
        """Process user request intelligently."""
        
        # Get relevant files
        relevant_files = self._get_relevant_files(user_input)
        
        # Build context from relevant files
        context = self._build_context(relevant_files, user_input)
        
        # Create intelligent prompt
        prompt = self._create_intelligent_prompt(user_input, context, relevant_files)
        
        # Get AI response with timeout protection
        self.console.print("[bold green]🤖 Analyzing and processing...[/bold green]")
        
        try:
            # Add timeout to prevent infinite processing
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError("Request timed out after 60 seconds")
            
            # Set timeout for 60 seconds
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(60)
            
            try:
                response = self.api_client.chat_completion(
                    messages=[{"role": "user", "content": prompt}],
                    model=self.current_model,
                    temperature=0.3,
                    max_tokens=30000
                )
                
                response_content = response.choices[0].message.content
                
                # Cancel the alarm
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
                
                # Check if response contains file modifications
                self.console.print(f"\n[dim]🔍 Checking for file modifications in response...[/dim]")
                
                if self._should_apply_changes(response_content):
                    self.console.print(f"[green]✅ Found file modifications, showing preview...[/green]")
                    return self._apply_changes(response_content, relevant_files)
                else:
                    self.console.print(f"[yellow]⚠️ No file modifications found in response[/yellow]")
                    self.console.print(f"[dim]Response contains '=== MODIFY:': {'=== MODIFY:' in response_content}[/dim]")
                    self.console.print(f"[dim]Response contains '=== CREATE:': {'=== CREATE:' in response_content}[/dim]")
                    return response_content
                    
            except TimeoutError:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
                return "❌ Request timed out after 60 seconds. Please try again with a simpler request."
            except Exception as e:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
                return f"❌ Error processing request: {str(e)}"
                
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def _build_context(self, relevant_files: List[str], query: str) -> str:
        """Build context from relevant files."""
        context_parts = []
        
        # Project overview
        context_parts.append(f"Project Type: {self.project_structure['type']}")
        context_parts.append(f"Main Files: {', '.join(self.project_structure['main_files'])}")
        context_parts.append(f"Total Files: {len(self.accessible_files)}")
        
        # Relevant files content
        for file_path in relevant_files:
            content = self._read_file_content(file_path)
            if content:
                # Truncate content if too long
                if len(content) > 2000:
                    content = content[:2000] + "... [truncated]"
                context_parts.append(f"\nFile: {file_path}\nContent:\n{content}")
        
        return "\n".join(context_parts)
    
    def _create_intelligent_prompt(self, user_input: str, context: str, relevant_files: List[str]) -> str:
        """Create an intelligent prompt for the AI."""
        
        prompt = f"""
You are an intelligent coding assistant with access to a codebase. Your job is to FIX BUGS and MODIFY FILES.

CONTEXT:
{context}

USER REQUEST:
{user_input}

RELEVANT FILES:
{', '.join(relevant_files)}

CRITICAL INSTRUCTIONS:
1. If the user reports a bug or requests changes, you MUST provide file modifications
2. You MUST use the exact format below for ANY file changes:

=== MODIFY: filename ===
[COMPLETE file content with your changes]
=== END MODIFY ===

=== CREATE: filename ===
[COMPLETE new file content]
=== END CREATE ===

3. Do NOT provide just analysis - you MUST include the actual file modifications
4. The content between === markers should be the COMPLETE file content
5. If you need to modify multiple files, include multiple === MODIFY: === blocks

EXAMPLE:
If you need to fix a bug in taskManager.js, your response should look like:

=== MODIFY: taskManager.js ===
// Fixed task management
function addTask(task) {{
    return firestore.collection('tasks').add(task);
}}

function getTasks(employeeId) {{
    // Now filters by employee
    return firestore.collection('tasks').where('employeeId', '==', employeeId).get();
}}
=== END MODIFY ===

DO NOT provide just text analysis. ALWAYS include the actual file modifications using the === format above.
"""
        
        return prompt
    
    def _should_apply_changes(self, response: str) -> bool:
        """Check if response contains file modifications."""
        return "=== MODIFY:" in response or "=== CREATE:" in response
    
    def _apply_changes(self, response: str, relevant_files: List[str]) -> str:
        """Apply changes suggested by the AI with user confirmation."""
        
        # Extract modifications
        modifications = self._extract_modifications(response)
        
        if not modifications:
            return response
        
        # Show preview of all changes first
        self._show_changes_preview(modifications)
        
        # Ask user what to do
        action = self._get_user_confirmation(modifications)
        
        if action == 'none':
            return f"""
❌ No changes applied. User cancelled.

Original response:
{response}
"""
        
        # Apply changes based on user choice
        applied_changes = []
        all_diffs = []
        
        if action == 'all':
            # Apply all changes
            for mod in modifications:
                diff_info = self._apply_modification_with_diff(mod, apply_changes=True)
                if diff_info['success']:
                    applied_changes.append(mod['file'])
                    if diff_info['diff']:
                        all_diffs.append(diff_info)
        else:
            # Apply changes one by one
            for i, mod in enumerate(modifications):
                file_path = mod['file']
                change_type = mod['type']
                
                # Show diff for this file
                self._show_single_file_preview(mod)
                
                # Ask for this specific file
                apply_this = Confirm.ask(f"Apply changes to {file_path}?", default=False)
                
                if apply_this:
                    diff_info = self._apply_modification_with_diff(mod, apply_changes=True)
                    if diff_info['success']:
                        applied_changes.append(file_path)
                        if diff_info['diff']:
                            all_diffs.append(diff_info)
                else:
                    self.console.print(f"[yellow]⏭️ Skipped: {file_path}[/yellow]")
        
        # Show final summary
        if applied_changes:
            self._show_detailed_diff_summary(applied_changes, all_diffs)
            return f"""
✅ Changes applied successfully!

Modified files:
{chr(10).join(f"• {file}" for file in applied_changes)}

Original response:
{response}
"""
        else:
            return f"""
❌ No changes applied.

Original response:
{response}
"""
    
    def _extract_modifications(self, response: str) -> List[Dict[str, str]]:
        """Extract file modifications from AI response."""
        modifications = []
        
        # Extract MODIFY blocks
        modify_pattern = r"=== MODIFY: (.+?) ===\n(.*?)\n=== END MODIFY ==="
        for match in re.finditer(modify_pattern, response, re.DOTALL):
            modifications.append({
                'type': 'modify',
                'file': match.group(1).strip(),
                'content': match.group(2).strip()
            })
        
        # Extract CREATE blocks
        create_pattern = r"=== CREATE: (.+?) ===\n(.*?)\n=== END CREATE ==="
        for match in re.finditer(create_pattern, response, re.DOTALL):
            modifications.append({
                'type': 'create',
                'file': match.group(1).strip(),
                'content': match.group(2).strip()
            })
        
        return modifications
    
    def _apply_modification_with_diff(self, modification: Dict[str, str], apply_changes: bool = False) -> Dict[str, Any]:
        """Apply a single modification and return diff information."""
        try:
            file_path = modification['file']
            
            if modification['type'] == 'create':
                if apply_changes:
                    # Create new file
                    with open(file_path, 'w') as f:
                        f.write(modification['content'])
                    self.console.print(f"[green]✅ Created: {file_path}[/green]")
                
                return {
                    'success': True,
                    'file': file_path,
                    'diff': True,
                    'type': 'create',
                    'content': modification['content']
                }
            
            elif modification['type'] == 'modify':
                # Modify existing file
                if os.path.exists(file_path):
                    # Read current content
                    with open(file_path, 'r') as f:
                        current_content = f.read()
                    
                    # Store original content for diff
                    original_content = current_content
                    new_content = modification['content']
                    
                    if apply_changes:
                        # Write new content
                        with open(file_path, 'w') as f:
                            f.write(new_content)
                        self.console.print(f"[green]✅ Modified: {file_path}[/green]")
                    
                    return {
                        'success': True,
                        'file': file_path,
                        'diff': True,
                        'type': 'modify',
                        'original': original_content,
                        'new': new_content
                    }
                else:
                    self.console.print(f"[red]❌ File not found: {file_path}[/red]")
                    return {'success': False, 'file': file_path, 'diff': False}
        
        except Exception as e:
            self.console.print(f"[red]❌ Error applying modification: {e}[/red]")
            return {'success': False, 'file': file_path, 'diff': False, 'error': str(e)}
    
    def _show_file_diff(self, file_path: str, original_content: str, new_content: str, change_type: str) -> None:
        """Show detailed diff for a file with colored output."""
        
        # Create diff
        diff_lines = list(difflib.unified_diff(
            original_content.splitlines(keepends=True),
            new_content.splitlines(keepends=True),
            fromfile=f"Original {file_path}",
            tofile=f"Modified {file_path}",
            lineterm=""
        ))
        
        if not diff_lines:
            self.console.print(f"[yellow]No changes detected in {file_path}[/yellow]")
            return
        
        # Show diff header
        self.console.print(f"\n[bold blue]📄 {change_type}: {file_path}[/bold blue]")
        self.console.print("=" * 80)
        
        # Display diff with colors
        for line in diff_lines:
            if line.startswith('+'):
                # Added line - green
                self.console.print(f"[green]+ {line[1:]}[/green]", end="")
            elif line.startswith('-'):
                # Removed line - red
                self.console.print(f"[red]- {line[1:]}[/red]", end="")
            elif line.startswith('@'):
                # Diff header - blue
                self.console.print(f"[blue]{line}[/blue]", end="")
            else:
                # Context line - white
                self.console.print(f"  {line}", end="")
        
        self.console.print("\n" + "=" * 80)
    
    def _show_changes_preview(self, modifications: List[Dict[str, str]]) -> None:
        """Show a preview of all proposed changes with actual code diffs."""
        
        self.console.print("\n[bold yellow]🔍 PREVIEW: Proposed Changes[/bold yellow]")
        self.console.print("=" * 80)
        
        # Create preview table
        table = Table(title="📋 Files to be Modified", show_header=True, header_style="bold blue")
        table.add_column("#", style="cyan")
        table.add_column("File", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Action", style="yellow")
        
        for i, mod in enumerate(modifications, 1):
            file_path = mod['file']
            change_type = mod['type'].upper()
            action = "Create" if change_type == "CREATE" else "Modify"
            
            table.add_row(str(i), file_path, change_type, action)
        
        self.console.print(table)
        
        # Show summary
        total_files = len(modifications)
        created_files = len([m for m in modifications if m['type'] == 'create'])
        modified_files = len([m for m in modifications if m['type'] == 'modify'])
        
        summary = f"""
📊 Summary:
• Total files: {total_files}
• Files to create: {created_files}
• Files to modify: {modified_files}
        """.strip()
        
        panel = Panel(summary, title="📊 Preview Summary", border_style="yellow")
        self.console.print(panel)
        
        # Show actual code diffs for each file
        self.console.print("\n[bold cyan]📄 CODE CHANGES PREVIEW:[/bold cyan]")
        self.console.print("=" * 80)
        
        for i, mod in enumerate(modifications, 1):
            self.console.print(f"\n[bold blue]{i}. {mod['type'].upper()}: {mod['file']}[/bold blue]")
            self.console.print("-" * 60)
            
            if mod['type'] == 'create':
                # Show new file content
                self.console.print("[green]New file content:[/green]")
                syntax = Syntax(mod['content'], "python", theme="monokai", line_numbers=True)
                self.console.print(syntax)
            else:
                # Show diff for modification
                if os.path.exists(mod['file']):
                    with open(mod['file'], 'r') as f:
                        original_content = f.read()
                    
                    # Create diff
                    diff_lines = list(difflib.unified_diff(
                        original_content.splitlines(keepends=True),
                        mod['content'].splitlines(keepends=True),
                        fromfile=f"Original {mod['file']}",
                        tofile=f"Modified {mod['file']}",
                        lineterm=""
                    ))
                    
                    if diff_lines:
                        self.console.print("[yellow]Proposed changes:[/yellow]")
                        for line in diff_lines:
                            if line.startswith('+'):
                                self.console.print(f"[green]+ {line[1:]}[/green]", end="")
                            elif line.startswith('-'):
                                self.console.print(f"[red]- {line[1:]}[/red]", end="")
                            elif line.startswith('@'):
                                self.console.print(f"[blue]{line}[/blue]", end="")
                            else:
                                self.console.print(f"  {line}", end="")
                    else:
                        self.console.print("[yellow]No changes detected[/yellow]")
                else:
                    self.console.print(f"[red]File not found: {mod['file']}[/red]")
            
            self.console.print("\n" + "-" * 60)
    
    def _get_user_confirmation(self, modifications: List[Dict[str, str]]) -> str:
        """Get user confirmation for applying changes."""
        
        self.console.print("\n[bold cyan]🤔 What would you like to do?[/bold cyan]")
        
        options = [
            ("1", "Apply ALL changes at once"),
            ("2", "Review and apply changes one by one"),
            ("3", "Cancel - don't apply any changes")
        ]
        
        for key, description in options:
            self.console.print(f"  {key}. {description}")
        
        try:
            # Add timeout for user input to prevent hanging
            import signal
            
            def input_timeout_handler(signum, frame):
                raise TimeoutError("User input timed out")
            
            old_handler = signal.signal(signal.SIGALRM, input_timeout_handler)
            signal.alarm(300)  # 5 minutes timeout for user input
            
            try:
                choice = Prompt.ask("\nEnter your choice", choices=["1", "2", "3"], default="3")
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
                
                if choice == "1":
                    return "all"
                elif choice == "2":
                    return "individual"
                elif choice == "3":
                    return "none"
                    
            except TimeoutError:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
                self.console.print("\n[yellow]⚠️ Input timeout. Cancelling changes.[/yellow]")
                return "none"
                
        except Exception as e:
            self.console.print(f"\n[red]❌ Error getting user input: {e}[/red]")
            return "none"
    
    def _show_single_file_preview(self, modification: Dict[str, str]) -> None:
        """Show preview for a single file modification."""
        
        file_path = modification['file']
        change_type = modification['type']
        content = modification['content']
        
        self.console.print(f"\n[bold blue]📄 {change_type.upper()}: {file_path}[/bold blue]")
        self.console.print("=" * 80)
        
        if change_type == 'create':
            # Show new file content
            self.console.print("[green]New file content:[/green]")
            syntax = Syntax(content, "python", theme="monokai", line_numbers=True)
            self.console.print(syntax)
        else:
            # Show diff for modification
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    original_content = f.read()
                
                # Create diff
                diff_lines = list(difflib.unified_diff(
                    original_content.splitlines(keepends=True),
                    content.splitlines(keepends=True),
                    fromfile=f"Original {file_path}",
                    tofile=f"Modified {file_path}",
                    lineterm=""
                ))
                
                if diff_lines:
                    self.console.print("[yellow]Proposed changes:[/yellow]")
                    for line in diff_lines:
                        if line.startswith('+'):
                            self.console.print(f"[green]+ {line[1:]}[/green]", end="")
                        elif line.startswith('-'):
                            self.console.print(f"[red]- {line[1:]}[/red]", end="")
                        elif line.startswith('@'):
                            self.console.print(f"[blue]{line}[/blue]", end="")
                        else:
                            self.console.print(f"  {line}", end="")
                else:
                    self.console.print("[yellow]No changes detected[/yellow]")
            else:
                self.console.print(f"[red]File not found: {file_path}[/red]")
        
        self.console.print("\n" + "=" * 80)
    
    def _show_detailed_diff_summary(self, modified_files: List[str], all_diffs: List[Dict[str, Any]]) -> None:
        """Show a summary of all changes made."""
        
        if not all_diffs:
            return
        
        # Create summary table
        table = Table(title="📊 Changes Summary", show_header=True, header_style="bold magenta")
        table.add_column("File", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Status", style="yellow")
        
        for diff_info in all_diffs:
            file_path = diff_info['file']
            change_type = diff_info['type'].upper()
            status = "✅ Applied"
            
            table.add_row(file_path, change_type, status)
        
        self.console.print(table)
        
        # Show statistics
        total_files = len(modified_files)
        created_files = len([d for d in all_diffs if d['type'] == 'create'])
        modified_files_count = len([d for d in all_diffs if d['type'] == 'modify'])
        
        stats = f"""
📈 Change Statistics:
• Total files affected: {total_files}
• Files created: {created_files}
• Files modified: {modified_files_count}
        """.strip()
        
        panel = Panel(stats, title="📈 Statistics", border_style="green")
        self.console.print(panel)
    
    def start_interactive_mode(self) -> Optional[str]:
        """Start interactive mode with intelligent processing.

        Returns 'qna' if user requested switching to Q&A mode, otherwise None.
        """
        
        # Show enhanced welcome (same as Q&A look-and-feel)
        self._show_welcome()
        
        # Main loop
        self._switch_to_mode: Optional[str] = None
        while True:
            try:
                # Show enhanced input prompt
                self._show_input_prompt()
                
                # Get user input with enhanced styling
                user_input = self._get_enhanced_user_input()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.startswith('/'):
                    if self._handle_command(user_input):
                        break
                    continue
                
                # Process request intelligently
                response = self.process_request(user_input)
                self._display_response(response)
                
            except KeyboardInterrupt:
                self._show_exit_message()
            except EOFError:
                break
            except Exception as e:
                self.console.print(f"[red]Error: {e}[/red]")
        return self._switch_to_mode
    def _show_input_prompt(self) -> None:
        """Show enhanced input prompt."""
        # Create a beautiful input prompt
        prompt_panel = Panel(
            f"[bold blue]💬[/bold blue] [bold white]Ask me anything about your code...[/bold white]\n"
            f"[dim]Type /help for commands, /exit to quit[/dim]",
            border_style="blue",
            padding=(0, 1)
        )
        self.console.print(prompt_panel)
    
    def _get_enhanced_user_input(self) -> str:
        """Get user input with enhanced styling."""
        # Create a styled input prompt
        prompt_tokens = FormattedText([
            ('class:prompt', f"You ({self.current_model}) [Agent]: ")
        ])

        bottom_toolbar = FormattedText([
            ('class:toolbar', ' GitHub: TM NABEEL @tmnabeel30 created  •  MODE: Agent (Can modify files) ')
        ])

        try:
            return prompt(
                prompt_tokens,
                history=self.history,
                completer=self.command_completer,
                multiline=False,
                style=self.prompt_style,
                bottom_toolbar=bottom_toolbar
            ).strip()
        except Exception:
            return input(f"\nYou ({self.current_model}) [Agent]: ").strip()
    
    def _show_exit_message(self) -> None:
        """Show enhanced exit message."""
        exit_panel = Panel(
            "[yellow]🔄 Press Ctrl+C again to exit, or type /exit[/yellow]",
            border_style="yellow",
            padding=(0, 1)
        )
        self.console.print(exit_panel)
    
    def _show_welcome(self) -> None:
        """Show enhanced welcome message."""
        
        # Create a beautiful welcome header
        header = Panel(
            "[bold blue]🚀[/bold blue] [bold white]Intelligent Groq CLI Agent[/bold white]\n"
            "[dim]Your AI-powered coding assistant[/dim]",
            subtitle="GitHub: TM NABEEL @tmnabeel30 created",
            subtitle_align="right",
            border_style="blue",
            padding=(0, 1)
        )
        self.console.print(header)
        
        # Show workspace info in a table
        workspace_table = Table(show_header=False, box=box.ROUNDED)
        workspace_table.add_column("Property", style="cyan", width=15)
        workspace_table.add_column("Value", style="white")
        
        workspace_table.add_row("📁 Workspace", str(self.workspace_path))
        workspace_table.add_row("📄 Files Found", str(len(self.accessible_files)))
        workspace_table.add_row("🧠 Project Type", self.project_structure['type'].title())
        workspace_table.add_row("🤖 Model", self.current_model)
        
        self.console.print(workspace_table)
        
        # Show capabilities
        capabilities = Panel(
            "[bold green]💡[/bold green] [bold white]I can help you with:[/bold white]\n\n"
            "• [green]🔍[/green] Read and understand your entire codebase\n"
            "• [green]🐛[/green] Identify bugs and issues automatically\n"
            "• [green]🔧[/green] Suggest and apply fixes\n"
            "• [green]📝[/green] Modify multiple files as needed\n"
            "• [green]✨[/green] Create new files when required\n"
            "• [green]🎨[/green] Show detailed diffs with green (+) and red (-) lines\n"
            "• [green]✅[/green] Ask for confirmation before applying changes",
            title="[bold green]Capabilities[/bold green]",
            border_style="green",
            padding=(0, 1)
        )
        self.console.print(capabilities)
        
        # Show quick start guide
        quick_start = Panel(
            "[bold yellow]🚀[/bold yellow] [bold white]Quick Start:[/bold white]\n\n"
            "Just describe your issue or request, and I'll analyze and fix it!\n"
            "Examples:\n"
            "• \"Fix the bug where tasks don't show up for employees\"\n"
            "• \"Add error handling to the login function\"\n"
            "• \"Create a new API endpoint for user profiles\"",
            title="[bold yellow]Quick Start[/bold yellow]",
            border_style="yellow",
            padding=(0, 1)
        )
        self.console.print(quick_start)
        
        # Show separator
        self.console.print("\n" + "─" * 80 + "\n")
    
    def _handle_command(self, command: str) -> bool:
        """Handle slash commands."""
        if command == '/exit':
            self._show_goodbye()
            return True
        elif command == '/help':
            self._show_help()
        elif command == '/files':
            self._list_files()
        elif command == '/structure':
            self._show_structure()
        elif command == '/model':
            self._show_model_info()
        elif command == '/status':
            self._show_status()
        elif command == '/handbook':
            self.show_handbook_status()
        elif command == '/goals':
            self.show_goals_status()
        elif command == '/context':
            self.show_context_chain()
        elif command.startswith('/recursive'):
            self._handle_recursive_command(command)
        elif command == '/qna' or (command.startswith('/mode') and 'qna' in command):
            # Switch back to Q&A mode
            self._switch_to_mode = 'qna'
            return True
        else:
            self.console.print(f"[red]❌ Unknown command: {command}[/red]")
            self.console.print("[yellow]💡 Type /help to see available commands[/yellow]")
        
        return False
    
    def _show_help(self) -> None:
        """Show help information."""
        help_panel = Panel(
            "[bold blue]📚[/bold blue] [bold white]Available Commands:[/bold white]\n\n"
            "[cyan]/help[/cyan]     - Show this help message\n"
            "[cyan]/files[/cyan]    - List all accessible files\n"
            "[cyan]/structure[/cyan] - Show project structure\n"
            "[cyan]/model[/cyan]    - Show current AI model info\n"
            "[cyan]/status[/cyan]   - Show current status\n"
            "[cyan]/handbook[/cyan] - Show handbook status\n"
            "[cyan]/goals[/cyan]    - Show recent goals\n"
            "[cyan]/context[/cyan]  - Show context chain\n"
            "[cyan]/recursive[/cyan] - Execute recursive goal\n"
            "[cyan]/exit[/cyan]     - Exit the application\n\n"
            "[dim]Just type your question or describe a bug to get started![/dim]",
            title="[bold blue]Help[/bold blue]",
            border_style="blue",
            padding=(0, 1)
        )
        self.console.print(help_panel)
    
    def _show_model_info(self) -> None:
        """Show current model information."""
        model_panel = Panel(
            f"[bold green]🤖[/bold green] [bold white]Current AI Model:[/bold white]\n\n"
            f"Model: [cyan]{self.current_model}[/cyan]\n"
            f"Status: [green]✅ Active[/green]\n\n"
            f"[dim]This model will analyze your code and provide intelligent solutions.[/dim]",
            title="[bold green]Model Info[/bold green]",
            border_style="green",
            padding=(0, 1)
        )
        self.console.print(model_panel)
    
    def _show_status(self) -> None:
        """Show current status."""
        status_table = Table(title="📊 Current Status", box=box.ROUNDED)
        status_table.add_column("Property", style="cyan")
        status_table.add_column("Value", style="white")
        
        status_table.add_row("Workspace", str(self.workspace_path))
        status_table.add_row("Files Found", str(len(self.accessible_files)))
        status_table.add_row("Project Type", self.project_structure['type'].title())
        status_table.add_row("AI Model", self.current_model)
        status_table.add_row("Status", "🟢 Ready")
        
        self.console.print(status_table)
    
    def _show_goodbye(self) -> None:
        """Show goodbye message."""
        goodbye_panel = Panel(
            "[bold green]👋[/bold green] [bold white]Thanks for using Groq CLI Agent![/bold white]\n\n"
            "[dim]Your code is now smarter and more robust.[/dim]\n"
            "[dim]Come back anytime for more AI-powered assistance![/dim]",
            subtitle="GitHub: TM NABEEL @tmnabeel30 created",
            subtitle_align="right",
            title="[bold green]Goodbye![/bold green]",
            border_style="green",
            padding=(0, 1)
        )
        self.console.print(goodbye_panel)
    
    def _list_files(self) -> None:
        """List accessible files with enhanced display."""
        # Group files by type
        file_groups = {
            'Python': [],
            'JavaScript/TypeScript': [],
            'Configuration': [],
            'Documentation': [],
            'Other': []
        }
        
        for file_path in sorted(self.accessible_files):
            path = Path(file_path)
            suffix = path.suffix.lower()
            
            if suffix in ['.py']:
                file_groups['Python'].append(str(path))
            elif suffix in ['.js', '.ts', '.jsx', '.tsx']:
                file_groups['JavaScript/TypeScript'].append(str(path))
            elif suffix in ['.json', '.yaml', '.yml', '.toml', '.ini', '.cfg']:
                file_groups['Configuration'].append(str(path))
            elif suffix in ['.md', '.txt', '.rst']:
                file_groups['Documentation'].append(str(path))
            else:
                file_groups['Other'].append(str(path))
        
        # Create enhanced table
        table = Table(title="📁 Accessible Files", box=box.ROUNDED)
        table.add_column("Type", style="cyan", width=20)
        table.add_column("Files", style="white")
        table.add_column("Count", style="green", justify="right")
        
        for file_type, files in file_groups.items():
            if files:
                # Show first few files, then count
                if len(files) <= 5:
                    files_display = "\n".join(files)
                else:
                    files_display = "\n".join(files[:3]) + f"\n... and {len(files) - 3} more"
                
                table.add_row(file_type, files_display, str(len(files)))
        
        self.console.print(table)
    
    def _show_structure(self) -> None:
        """Show enhanced project structure."""
        # Create detailed structure table
        structure_table = Table(title="📊 Project Structure Analysis", box=box.ROUNDED)
        structure_table.add_column("Component", style="cyan")
        structure_table.add_column("Count", style="green", justify="right")
        structure_table.add_column("Details", style="white")
        
        structure_table.add_row(
            "Project Type", 
            "1", 
            self.project_structure['type'].title()
        )
        structure_table.add_row(
            "Main Files", 
            str(len(self.project_structure['main_files'])), 
            ", ".join(self.project_structure['main_files'][:3]) + ("..." if len(self.project_structure['main_files']) > 3 else "")
        )
        structure_table.add_row(
            "Config Files", 
            str(len(self.project_structure['config_files'])), 
            ", ".join(self.project_structure['config_files'][:3]) + ("..." if len(self.project_structure['config_files']) > 3 else "")
        )
        structure_table.add_row(
            "Source Files", 
            str(len(self.project_structure['source_files'])), 
            f"{len([f for f in self.project_structure['source_files'] if f.endswith('.py')])} Python, "
            f"{len([f for f in self.project_structure['source_files'] if f.endswith(('.js', '.ts'))])} JS/TS"
        )
        structure_table.add_row(
            "Test Files", 
            str(len(self.project_structure['test_files'])), 
            ", ".join(self.project_structure['test_files'][:3]) + ("..." if len(self.project_structure['test_files']) > 3 else "")
        )
        
        self.console.print(structure_table)
    
    def _display_response(self, response: str) -> None:
        """Display response."""
        if "✅" in response or "❌" in response:
            # Show as markdown for better formatting
            md = Markdown(response)
            self.console.print(md)
        else:
            # Regular text
            self.console.print(response)
        
        # Add a separator after response
        self.console.print("\n" + "─" * 80)
    
    def set_recursive_agent(self, recursive_agent: RecursiveAgent) -> None:
        """Set the recursive agent for integration."""
        self.recursive_agent = recursive_agent
    
    def execute_recursive_goal(self, user_prompt: str, goal_description: str) -> Dict[str, Any]:
        """Execute a goal using the recursive agent system."""
        if not self.recursive_agent:
            return {
                'success': False,
                'error': 'Recursive agent not initialized'
            }
        
        try:
            result = self.recursive_agent.execute_goal(user_prompt, goal_description)
            return result
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def show_handbook_status(self) -> None:
        """Show the current handbook status."""
        if not self.handbook_manager:
            self.console.print("[red]Handbook manager not available[/red]")
            return
        
        handbook_path = self.handbook_manager.handbook_path
        if handbook_path.exists():
            self.console.print(f"[green]✓ Handbook found: {handbook_path}[/green]")
            
            # Show recent changes
            if self.handbook_manager.change_history:
                self.console.print(f"[cyan]Recent changes: {len(self.handbook_manager.change_history)}[/cyan]")
                for change in self.handbook_manager.change_history[-3:]:
                    self.console.print(f"  • {change.timestamp}: {change.goal}")
            else:
                self.console.print("[yellow]No changes recorded yet[/yellow]")
        else:
            self.console.print(f"[red]Handbook not found: {handbook_path}[/red]")
    
    def show_goals_status(self) -> None:
        """Show the status of recent goals."""
        if not self.recursive_agent:
            self.console.print("[red]Recursive agent not available[/red]")
            return
        
        recent_goals = self.recursive_agent.get_recent_goals()
        if recent_goals:
            self.console.print("[green]Recent Goals:[/green]")
            for goal_info in recent_goals:
                status_color = "green" if goal_info['status'] == 'completed' else "yellow"
                self.console.print(f"  • {goal_info['id']}: {goal_info['description']} [{status_color}]{goal_info['status']}[/{status_color}]")
        else:
            self.console.print("[yellow]No goals executed yet[/yellow]")
    
    def show_context_chain(self) -> None:
        """Show the current context chain."""
        if not self.recursive_agent:
            self.console.print("[red]Recursive agent not available[/red]")
            return
        
        context_chain = self.recursive_agent.context_chain
        if context_chain:
            self.console.print("[green]Context Chain:[/green]")
            for i, context in enumerate(context_chain[-5:], 1):
                self.console.print(f"  {i}. {context['sub_goal_id']}: {context['description']}")
                if context.get('files_changed'):
                    self.console.print(f"     Files: {', '.join(context['files_changed'])}")
        else:
            self.console.print("[yellow]No context chain available[/yellow]")
    
    def _handle_recursive_command(self, command: str) -> None:
        """Handle recursive agent commands."""
        parts = command.split(' ', 2)
        if len(parts) < 3:
            self.console.print("[red]Usage: /recursive <goal> <prompt>[/red]")
            self.console.print("[yellow]Example: /recursive 'Add new feature' 'I want to add a new function to handle user input'[/yellow]")
            return
        
        goal = parts[1]
        prompt = parts[2]
        
        self.console.print(f"[bold green]🎯 Executing Recursive Goal:[/bold green] {goal}")
        self.console.print(f"[dim]Prompt:[/dim] {prompt}")
        
        try:
            result = self.execute_recursive_goal(prompt, goal)
            
            if result['success']:
                self.console.print(f"[green]✅ Recursive goal completed successfully![/green]")
                self.console.print(f"[dim]Goal ID:[/dim] {result.get('goal_id', 'N/A')}")
                self.console.print(f"[dim]Files changed:[/dim] {len(result.get('files_changed', []))}")
                self.console.print(f"[dim]Sub-goals completed:[/dim] {result.get('sub_goals_completed', 0)}")
            else:
                self.console.print(f"[red]❌ Recursive goal failed: {result.get('error', 'Unknown error')}[/red]")
                
        except Exception as e:
            self.console.print(f"[red]❌ Error executing recursive goal: {str(e)}[/red]")
