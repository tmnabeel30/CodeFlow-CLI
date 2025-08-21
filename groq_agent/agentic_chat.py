"""Advanced Agent Chat Interface with enhanced AI capabilities."""

import sys
import os
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
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

from .config import ConfigurationManager
from .api_client import GroqAPIClient
from .model_selector import ModelSelector
from .file_operations import FileOperations


class AgenticChat:
    """Advanced agent chat interface with enhanced AI capabilities."""
    
    def __init__(self, config: ConfigurationManager, api_client: GroqAPIClient):
        """Initialize the agentic chat interface."""
        self.config = config
        self.api_client = api_client
        self.model_selector = ModelSelector(api_client)
        self.file_ops = FileOperations(api_client)
        self.console = Console()
        
        # Chat state
        self.current_model = config.get_default_model()
        self.messages: List[Dict[str, str]] = []
        self.max_history = config.get_max_history()
        
        # Agentic state
        self.workspace_path = Path.cwd()
        self.accessible_files: set = set()
        self.recent_changes: List[Dict[str, Any]] = []
        self.tool_calls: List[Dict[str, Any]] = []
        
        # Input styling and history
        history_file = config.config_dir / "agentic_chat_history.txt"
        self.history = FileHistory(str(history_file))
        self.prompt_style = Style.from_dict({
            'prompt': 'bold ansicyan',
            'toolbar': 'reverse ansimagenta'
        })
        
        # Enhanced command completions
        self.command_completer = WordCompleter([
            '/help', '/model', '/exit', '/clear', '/history', '/status', '/tools',
            '/search', '/read', '/edit', '/create', '/delete', '/analyze', '/debug',
            '/context', '/undo', '/redo', '/plan', '/execute', '/qna', '/mode',
            '/fast', '/balanced', '/powerful', '/ultra', '/mixtral', '/gemma',
            '/compound', '/compound-mini', '/next', '/prev', '/shortcuts'
        ])
        
        # Initialize workspace
        self._initialize_workspace()
    
    def _initialize_workspace(self) -> None:
        """Initialize the workspace with comprehensive scanning."""
        with Status("[bold green]🔍 Initializing Agentic Workspace...", console=self.console):
            self._scan_workspace()
            self._analyze_project_structure()
    
    def _scan_workspace(self) -> None:
        """Scan workspace for accessible files."""
        import glob
        
        files = set()
        extensions = {
            '*.py', '*.js', '*.ts', '*.jsx', '*.tsx', '*.html', '*.css',
            '*.json', '*.yaml', '*.yml', '*.md', '*.txt', '*.sh', '*.java',
            '*.cpp', '*.c', '*.go', '*.rs', '*.php', '*.rb', '*.sql'
        }
        
        for ext in extensions:
            files.update(glob.glob(str(self.workspace_path / "**" / ext), recursive=True))
        
        # Filter out common directories
        ignore_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv'}
        filtered_files = set()
        
        for file_path in files:
            path = Path(file_path)
            if not any(ignore_dir in path.parts for ignore_dir in ignore_dirs):
                filtered_files.add(str(path))
        
        self.accessible_files = filtered_files
        self.console.print(f"[green]✓ Found {len(self.accessible_files)} accessible files[/green]")
    
    def _analyze_project_structure(self) -> None:
        """Analyze project structure."""
        self.project_structure = {
            'type': 'unknown',
            'main_files': [],
            'source_files': [],
            'config_files': []
        }
        
        for file_path in self.accessible_files:
            path = Path(file_path)
            file_name = path.name.lower()
            
            if file_name == 'package.json':
                self.project_structure['type'] = 'nodejs'
            elif file_name == 'requirements.txt':
                self.project_structure['type'] = 'python'
            elif file_name == 'cargo.toml':
                self.project_structure['type'] = 'rust'
            
            if path.suffix in ['.py', '.js', '.ts', '.java', '.cpp', '.go']:
                self.project_structure['source_files'].append(str(path))
    
    def start(self) -> Optional[str]:
        """Start the agentic chat session."""
        self._show_agentic_welcome()
        
        if not self.current_model:
            self._select_initial_model()
        
        self._switch_to_mode: Optional[str] = None
        while True:
            try:
                user_input = self._get_agentic_user_input()
                
                if not user_input.strip():
                    continue
                
                if user_input.startswith('/'):
                    if self._handle_agentic_command(user_input):
                        break
                    continue
                
                response = self._process_agentic_request(user_input)
                if response:
                    self._display_agentic_response(response)
                else:
                    self.console.print("[yellow]No response received. Try rephrasing your request.[/yellow]")
                
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Use /exit to quit the chat session[/yellow]")
            except EOFError:
                break
            except Exception as e:
                self.console.print(f"[red]Error: {e}[/red]")
        
        return self._switch_to_mode
    
    def _show_agentic_welcome(self) -> None:
        """Display advanced agent welcome message."""
        header_title = "🚀 CodeFlow Advanced Agent"
        header = Panel(
            Text(header_title, style="bold blue", justify="center"),
            subtitle="GitHub: TM NABEEL @tmnabeel30 created",
            subtitle_align="right",
            border_style="blue",
            padding=(1, 2)
        )
        
        workspace_info = f"""
[bold]Workspace:[/bold] {self.workspace_path}
[bold]Project Type:[/bold] {self.project_structure['type']}
[bold]Files:[/bold] {len(self.accessible_files)} accessible
[bold]Current Model:[/bold] {self.current_model or 'Not set'}
        """.strip()
        
        workspace_panel = Panel(
            workspace_info,
            title="📁 Workspace Information",
            border_style="green",
            padding=(1, 2)
        )
        
        capabilities_info = """
[bold]🤖 Advanced AI Capabilities:[/bold]
• Semantic codebase search
• Intelligent file operations
• Code analysis and debugging
• Context-aware responses
• Tool execution tracking
        """.strip()
        
        capabilities_panel = Panel(
            capabilities_info,
            title="🛠️ Advanced Tools",
            border_style="yellow",
            padding=(1, 2)
        )
        
        self.console.print(header)
        self.console.print()
        self.console.print(workspace_panel)
        self.console.print(capabilities_panel)
        self.console.print()
    
    def _get_agentic_user_input(self) -> str:
        """Get user input with advanced agent prompt styling."""
        prompt_tokens = FormattedText([
            ('class:prompt', f"Advanced ({self.current_model}): ")
        ])

        bottom_toolbar = FormattedText([
            ('class:toolbar', ' GitHub: TM NABEEL @tmnabeel30 created | Type /help for tools ')
        ])

        return prompt(
            prompt_tokens,
            history=self.history,
            completer=self.command_completer,
            multiline=False,
            style=self.prompt_style,
            bottom_toolbar=bottom_toolbar
        )
    
    def _handle_agentic_command(self, command: str) -> bool:
        """Handle advanced agent slash commands."""
        parts = command.split(' ', 1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        if cmd == '/help':
            self._show_agentic_help()
        elif cmd == '/model':
            self._change_model()
        elif cmd == '/status':
            self._show_status()
        elif cmd == '/tools':
            self._show_tools()
        elif cmd == '/search':
            self._handle_search(args)
        elif cmd == '/read':
            self._handle_read(args)
        elif cmd == '/edit':
            self._handle_edit(args)
        elif cmd == '/analyze':
            self._handle_analyze(args)
        elif cmd == '/context':
            self._show_context()
        elif cmd == '/history':
            self._show_history()
        elif cmd == '/qna' or (cmd == '/mode' and args.strip().lower() == 'qna'):
            self._switch_to_mode = 'qna'
            return True
        elif cmd == '/clear':
            self._clear_history()
        elif cmd == '/exit':
            return True
        else:
            self.console.print(f"[red]Unknown command: {cmd}[/red]")
            self.console.print("Type /help for available commands")
        
        return False
    
    def _handle_search(self, query: str) -> None:
        """Handle search command."""
        if not query:
            self.console.print("[red]Please provide a search query[/red]")
            return
        
        with Status("[bold green]🔍 Searching codebase...", console=self.console):
            results = []
            query_lower = query.lower()
            
            for file_path in self.accessible_files:
                path = Path(file_path)
                if query_lower in path.name.lower():
                    results.append({
                        'file': file_path,
                        'match_type': 'filename',
                        'relevance': 0.8
                    })
            
            # Limit results
            results = results[:10]
        
        if results:
            self._display_search_results(results)
        else:
            self.console.print("[yellow]No results found[/yellow]")
    
    def _display_search_results(self, results: List[Dict[str, Any]]) -> None:
        """Display search results."""
        table = Table(title="🔍 Search Results", show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim", width=4)
        table.add_column("File", style="cyan")
        table.add_column("Match Type", style="green")
        table.add_column("Relevance", style="yellow")
        
        for i, result in enumerate(results, 1):
            file_path = Path(result['file']).name
            match_type = result['match_type']
            relevance = f"{result['relevance']:.2f}"
            
            table.add_row(str(i), file_path, match_type, relevance)
        
        self.console.print(table)
    
    def _handle_read(self, file_path: str) -> None:
        """Handle read command."""
        if not file_path:
            self.console.print("[red]Please specify a file path[/red]")
            return
        
        # Find the file
        target_file = None
        for accessible_file in self.accessible_files:
            if file_path in accessible_file or Path(accessible_file).name == file_path:
                target_file = accessible_file
                break
        
        if not target_file:
            self.console.print(f"[red]File not found: {file_path}[/red]")
            return
        
        try:
            with open(target_file, 'r') as f:
                content = f.read()
            
            language = self._detect_language(target_file)
            syntax = Syntax(content, language, theme="monokai", line_numbers=True)
            
            panel = Panel(
                syntax,
                title=f"📄 {Path(target_file).name}",
                border_style="green",
                padding=(1, 2)
            )
            
            self.console.print(panel)
            
        except Exception as e:
            self.console.print(f"[red]Error reading file: {e}[/red]")
    
    def _detect_language(self, file_path: str) -> str:
        """Detect programming language."""
        ext = Path(file_path).suffix.lower()
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.html': 'html',
            '.css': 'css',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.md': 'markdown'
        }
        return language_map.get(ext, 'text')
    
    def _handle_edit(self, file_paths: str) -> None:
        """Handle edit command for one or more files with diff preview."""
        if not file_paths:
            self.console.print("[red]Please specify one or more file paths[/red]")
            return

        requested = file_paths.split()
        targets: List[str] = []
        for req in requested:
            target = None
            for accessible_file in self.accessible_files:
                if req in accessible_file or Path(accessible_file).name == req:
                    target = accessible_file
                    break
            if target:
                targets.append(target)
            else:
                self.console.print(f"[red]File not found: {req}[/red]")

        if not targets:
            self.console.print("[red]No valid files found[/red]")
            return

        instructions = Prompt.ask("What changes would you like to make?")
        if not instructions:
            self.console.print("[yellow]Edit cancelled[/yellow]")
            return

        results = self.file_ops.review_files(
            targets,
            self.current_model,
            instructions,
            auto_apply=False,
        )

        for target_file, success in results.items():
            if success:
                self.console.print(f"[green]✓ File edited successfully: {target_file}[/green]")
                self.recent_changes.append(
                    {
                        "file": target_file,
                        "timestamp": time.time(),
                        "action": "edited",
                    }
                )
            else:
                self.console.print(f"[red]✗ Failed to edit file: {target_file}[/red]")
    
    def _handle_analyze(self, file_path: str) -> None:
        """Handle analyze command."""
        if not file_path:
            self.console.print("[red]Please specify a file path[/red]")
            return
        
        # Find the file
        target_file = None
        for accessible_file in self.accessible_files:
            if file_path in accessible_file or Path(accessible_file).name == file_path:
                target_file = accessible_file
                break
        
        if not target_file:
            self.console.print(f"[red]File not found: {file_path}[/red]")
            return
        
        try:
            with open(target_file, 'r') as f:
                content = f.read()
            
            analysis = {
                'file': target_file,
                'size': len(content),
                'lines': content.count('\n') + 1,
                'language': self._detect_language(target_file)
            }
            
            self._display_analysis_results(analysis)
            
        except Exception as e:
            self.console.print(f"[red]Error analyzing file: {e}[/red]")
    
    def _display_analysis_results(self, analysis: Dict[str, Any]) -> None:
        """Display analysis results."""
        info_text = f"""
[bold]File:[/bold] {analysis['file']}
[bold]Language:[/bold] {analysis['language']}
[bold]Size:[/bold] {analysis['size']} characters
[bold]Lines:[/bold] {analysis['lines']}
        """.strip()
        
        panel = Panel(
            info_text,
            title="📊 Analysis Results",
            border_style="blue",
            padding=(1, 2)
        )
        
        self.console.print(panel)
    
    def _show_status(self) -> None:
        """Show system status."""
        status_info = f"""
[bold]🤖 Agentic System Status[/bold]

[cyan]Workspace:[/cyan] {self.workspace_path}
[cyan]Project Type:[/cyan] {self.project_structure['type']}
[cyan]Files:[/cyan] {len(self.accessible_files)} accessible
[cyan]Current Model:[/cyan] {self.current_model}
[cyan]Tool Calls:[/cyan] {len(self.tool_calls)} executed
[cyan]Recent Changes:[/cyan] {len(self.recent_changes)} files modified
        """.strip()
        
        panel = Panel(
            status_info,
            title="📊 Agentic System Status",
            border_style="blue",
            padding=(1, 2)
        )
        
        self.console.print(panel)
    
    def _show_tools(self) -> None:
        """Show available tools."""
        tools_info = """
[bold]🛠️ Available Agentic Tools[/bold]

[cyan]Search & Analysis:[/cyan]
• /search <query> - Semantic codebase search
• /analyze <file> - Analyze code structure and quality
• /read <file> - Read file contents

[cyan]File Operations:[/cyan]
• /edit <file1> [file2 ...] - Edit one or more files with intelligent changes

[cyan]Context & History:[/cyan]
• /context - Show current context
• /history - Show recent changes

[cyan]System & Tools:[/cyan]
• /status - Show system status
• /tools - Show available tools
        """.strip()
        
        panel = Panel(
            tools_info,
            title="🛠️ Agentic Tools",
            border_style="green",
            padding=(1, 2)
        )
        
        self.console.print(panel)
    
    def _show_context(self) -> None:
        """Show current context."""
        context_info = f"""
[bold]Current Context:[/bold]
• Workspace: {self.workspace_path}
• Files: {len(self.accessible_files)} accessible
• Tool Calls: {len(self.tool_calls)} executed
• Recent Changes: {len(self.recent_changes)} files modified
• Project Type: {self.project_structure['type']}
        """.strip()
        
        panel = Panel(
            context_info,
            title="📋 Current Context",
            border_style="cyan",
            padding=(1, 2)
        )
        
        self.console.print(panel)
    
    def _show_history(self) -> None:
        """Show recent changes history."""
        if not self.recent_changes:
            self.console.print("[yellow]No recent changes[/yellow]")
            return
        
        table = Table(title="📜 Recent Changes", show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim", width=4)
        table.add_column("File", style="cyan")
        table.add_column("Action", style="green")
        table.add_column("Time", style="yellow")
        
        for i, change in enumerate(self.recent_changes[-10:], 1):
            file_path = Path(change['file']).name
            action = change.get('action', 'modified')
            timestamp = time.strftime('%H:%M:%S', time.localtime(change['timestamp']))
            
            table.add_row(str(i), file_path, action, timestamp)
        
        self.console.print(table)
    
    def _process_agentic_request(self, user_input: str) -> Optional[str]:
        """Process user request with advanced agent capabilities."""
        # Check if this is a file modification request
        if self._is_file_modification_request(user_input):
            return self._handle_file_modification_request(user_input)
        
        self.messages.append({"role": "user", "content": user_input})
        
        # Build enhanced context
        context_parts = []
        context_parts.append(f"Workspace: {self.workspace_path}")
        context_parts.append(f"Project Type: {self.project_structure['type']}")
        context_parts.append(f"Files: {len(self.accessible_files)} accessible")
        
        # Add recent changes
        if self.recent_changes:
            recent_files = [Path(c['file']).name for c in self.recent_changes[-3:]]
            context_parts.append(f"Recent changes: {', '.join(recent_files)}")
        
        enhanced_message = f"""
Advanced Agent Context:
{chr(10).join(context_parts)}

User Request: {user_input}

You are an advanced AI assistant with access to powerful tools. You can:
- Search and analyze codebases
- Read and edit files with diff previews
- Understand project structure and context
- Provide intelligent code suggestions

Please respond intelligently to the user's request, using your tools when appropriate.
"""
        
        self.messages[-1] = {"role": "user", "content": enhanced_message}
        
        if len(self.messages) > self.max_history:
            self.messages = self.messages[-self.max_history:]
        
        with Status("[bold green]🤖 Processing with advanced AI...", console=self.console):
            try:
                response = self.api_client.chat_completion(
                    messages=self.messages,
                    model=self.current_model,
                    temperature=0.7,
                    max_tokens=4000
                )
                
                if not response or not response.choices or not response.choices[0].message:
                    self.console.print("[red]Error: Received empty response from API[/red]")
                    if self.messages:
                        self.messages.pop()
                    return None
                
                response_content = response.choices[0].message.content
                
                if not response_content or not response_content.strip():
                    self.console.print("[red]Error: Received empty response content from API[/red]")
                    if self.messages:
                        self.messages.pop()
                    return None
                
                self.messages.append({"role": "assistant", "content": response_content})
                return response_content
                
            except Exception as e:
                self.console.print(f"[red]Error getting response: {e}[/red]")
                if self.messages:
                    self.messages.pop()
                return None
    
    def _is_file_modification_request(self, user_input: str) -> bool:
        """Check if user input is requesting file modifications."""
        modification_keywords = [
            'add', 'create', 'modify', 'change', 'update', 'edit', 'fix', 'implement',
            'button', 'function', 'component', 'page', 'file', 'code', 'feature'
        ]
        
        user_lower = user_input.lower()
        return any(keyword in user_lower for keyword in modification_keywords)
    
    def _handle_file_modification_request(self, user_input: str) -> Optional[str]:
        """Handle file modification requests with diff preview."""
        self.console.print(f"[cyan]🔧 Processing file modification request: {user_input}[/cyan]")
        
        # Use the file operations system to handle the request
        try:
            # Try to find relevant files based on the request
            relevant_files = self._find_relevant_files(user_input)
            
            if not relevant_files:
                return "I couldn't find any relevant files for your request. Please specify the file path or provide more context about what you'd like to modify."
            
            # For now, let's try the first relevant file
            target_file = relevant_files[0]
            
            # Use file operations to handle the modification
            success = self.file_ops.review_file(
                target_file,
                self.current_model,
                user_input,
                auto_apply=False
            )
            
            if success:
                self.recent_changes.append({
                    'file': target_file,
                    'timestamp': time.time(),
                    'action': 'modified'
                })
                return f"✅ Successfully processed your request for {target_file}"
            else:
                return "❌ Failed to process the file modification request. Please try again with more specific instructions."
                
        except Exception as e:
            return f"❌ Error processing file modification: {str(e)}"
    
    def _find_relevant_files(self, user_input: str) -> List[str]:
        """Find files relevant to the user's request."""
        user_lower = user_input.lower()
        relevant_files = []
        
        for file_path in self.accessible_files:
            file_name = Path(file_path).name.lower()
            
            # Check if file name contains keywords from the request
            if any(keyword in file_name for keyword in ['task', 'button', 'page', 'component']):
                if any(keyword in user_lower for keyword in ['task', 'button', 'page', 'component']):
                    relevant_files.append(file_path)
            
            # Check for common file patterns
            elif 'task' in user_lower and 'task' in file_name:
                relevant_files.append(file_path)
            elif 'button' in user_lower and any(ext in file_name for ext in ['.js', '.jsx', '.ts', '.tsx', '.html']):
                relevant_files.append(file_path)
        
        return relevant_files[:3]  # Return top 3 relevant files
    
    def _display_agentic_response(self, response: str) -> None:
        """Display agentic response."""
        if "```" in response:
            self._display_code_response(response)
        else:
            self._display_text_response(response)
    
    def _display_code_response(self, response: str) -> None:
        """Display response with code."""
        parts = response.split("```")
        
        for i, part in enumerate(parts):
            if i % 2 == 0:  # Regular text
                if part.strip():
                    md = Markdown(part.strip())
                    self.console.print(md)
            else:  # Code block
                if part.strip():
                    lines = part.strip().split('\n', 1)
                    if len(lines) > 1 and lines[0].strip():
                        language = lines[0].strip()
                        code = lines[1]
                    else:
                        language = "text"
                        code = part.strip()
                    
                    syntax = Syntax(code, language, theme="monokai", line_numbers=True)
                    panel = Panel(syntax, title=f"💻 Code ({language})", border_style="yellow", padding=(1, 2))
                    self.console.print(panel)
    
    def _display_text_response(self, response: str) -> None:
        """Display text-only response."""
        md = Markdown(response)
        self.console.print(md)
    
    def _select_initial_model(self) -> None:
        """Select initial model."""
        self.console.print("[yellow]No default model configured. Please select one:[/yellow]")
        selected_model = self.model_selector.select_model()
        
        if selected_model:
            self.current_model = selected_model
            self.config.set_default_model(selected_model)
            self.console.print(f"[green]Model set to: {selected_model}[/green]")
        else:
            self.console.print("[red]No model selected. Exiting.[/red]")
            sys.exit(1)
    
    def _change_model(self) -> None:
        """Change the current model."""
        self.console.print(f"[yellow]Current model: {self.current_model}[/yellow]")
        selected_model = self.model_selector.select_model(self.current_model)
        
        if selected_model:
            self.current_model = selected_model
            self.config.set_default_model(selected_model)
            self.console.print(f"[green]Model changed to: {selected_model}[/green]")
        else:
            self.console.print("[yellow]Model selection cancelled[/yellow]")
    
    def _clear_history(self) -> None:
        """Clear chat history."""
        if Confirm.ask("Are you sure you want to clear the chat history?"):
            self.messages.clear()
            self.console.print("[green]Chat history cleared[/green]")
        else:
            self.console.print("[yellow]Operation cancelled[/yellow]")
    
    def _show_agentic_help(self) -> None:
        """Show agentic help information."""
        help_text = """
[bold]🤖 Advanced Agent Commands:[/bold]

[cyan]Search & Analysis:[/cyan]
• /search <query> - Semantic codebase search
• /analyze <file> - Analyze code structure and quality
• /read <file> - Read file contents

[cyan]File Operations:[/cyan]
• /edit <file1> [file2 ...] - Edit files with diff preview
• Natural language requests - "add button to task page"

[cyan]Context & History:[/cyan]
• /context - Show current context
• /history - Show recent changes

[cyan]System & Tools:[/cyan]
• /status - Show system status
• /tools - Show available tools

[cyan]General:[/cyan]
• /help - Show this help message
• /clear - Clear chat history
• /exit - Exit the chat session

[bold]💡 Advanced Features:[/bold]
• Intelligent code understanding with diff previews
• Context-aware responses
• Tool execution tracking
• Change history management
• Semantic search capabilities
• Natural language file modifications
        """
        
        panel = Panel(
            help_text,
            title="🤖 Advanced Agent Help",
            border_style="green",
            padding=(1, 2)
        )
        
        self.console.print(panel)
