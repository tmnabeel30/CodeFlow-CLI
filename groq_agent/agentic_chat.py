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
        
        # Context Optimization - Full 64k context utilization
        self.operation_history: List[Dict[str, Any]] = []
        self.task_context: Dict[str, Any] = {}
        self.session_state: Dict[str, Any] = {}
        self.context_buffer: List[Dict[str, Any]] = []
        self.max_context_tokens = 64000  # Full context window
        self.current_context_size = 0
        self.context_optimization_enabled = True
        
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
            '/context', '/undo', '/redo', '/plan', '/execute', '/qna', '/agent', '/mode',
            '/fast', '/balanced', '/powerful', '/ultra', '/mixtral', '/gemma',
            '/compound', '/compound-mini', '/next', '/prev', '/shortcuts',
            '/files', '/scan', '/workspace'
        ])
        
        # Initialize workspace
        self._initialize_workspace()
        
        # Initialize context optimization
        self._initialize_context_optimization()
    
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
                
                # Update task context for persistent state
                self._update_task_context(user_input)
                
                # Process request with context optimization
                response = self._process_agentic_request_with_context(user_input)
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
        elif cmd == '/shortcuts':
            self.model_selector.show_quick_shortcuts()
        elif cmd in ['/fast', '/balanced', '/powerful', '/ultra', '/mixtral', '/gemma', '/compound', '/compound-mini']:
            shortcut = cmd[1:]  # Remove the leading '/'
            new_model = self.model_selector.quick_switch_model(shortcut)
            if new_model:
                self.current_model = new_model
                self.config.set_default_model(new_model)
                self.console.print(f"[green]Switched to model: {new_model}[/green]")
        elif cmd == '/next':
            next_model = self.model_selector.get_next_model(self.current_model)
            if next_model:
                self.current_model = next_model
                self.config.set_default_model(next_model)
                self.console.print(f"[green]Switched to next model: {next_model}[/green]")
            else:
                self.console.print("[red]Could not switch to next model[/red]")
        elif cmd == '/prev':
            prev_model = self.model_selector.get_previous_model(self.current_model)
            if prev_model:
                self.current_model = prev_model
                self.config.set_default_model(prev_model)
                self.console.print(f"[green]Switched to previous model: {prev_model}[/green]")
            else:
                self.console.print("[red]Could not switch to previous model[/red]")
        elif cmd == '/files':
            self._list_accessible_files()
        elif cmd == '/scan':
            self._rescan_workspace()
        elif cmd == '/workspace':
            self._show_workspace_info()
        elif cmd == '/search':
            self._handle_search(args)
        elif cmd == '/read':
            self._handle_read(args)
        elif cmd == '/edit':
            self._handle_edit(args)
        elif cmd == '/create':
            self._handle_create(args)
        elif cmd == '/delete':
            self._handle_delete(args)
        elif cmd == '/analyze':
            self._handle_analyze(args)
        elif cmd == '/status':
            self._show_status()
        elif cmd == '/tools':
            self._show_tools()
        elif cmd == '/context':
            self._show_context_status()  # Updated to show context optimization status
        elif cmd == '/history':
            self._show_history()
        # Mode switching
        elif cmd == '/qna' or (cmd == '/mode' and args.strip().lower() == 'qna'):
            self._switch_to_mode = 'qna'
            return True
        elif cmd == '/agent' or (cmd == '/mode' and args.strip().lower() == 'agent'):
            self._switch_to_mode = 'agent'
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
    
    def _process_agentic_request_with_context(self, user_input: str) -> Optional[str]:
        """Process user request using advanced agentic capabilities with full context optimization."""
        try:
            if len(self.messages) > self.max_history:
                self.messages = self.messages[-self.max_history:]

            smart_context = self._build_smart_context(user_input)
            optimized_context = self._optimize_context_for_64k(smart_context)

            self._add_to_operation_history({
                'type': 'user_request',
                'description': user_input,
                'context_size': len(optimized_context) // 4,
                'context_utilization': self.session_state['context_utilization']
            })

            if self._is_file_modification_request(user_input):
                return self._handle_file_modification_request(user_input)

            context_message = {"role": "system", "content": optimized_context}
            user_message = {"role": "user", "content": user_input}
            self.session_state['models_used'].add(self.current_model)

            messages = self.messages + [context_message, user_message]

            with Status("[bold green]🤖 Processing with 64k context optimization...", console=self.console):
                response = self.api_client.chat_completion(
                    messages=messages,
                    model=self.current_model,
                    temperature=0.7,
                    max_tokens=30000
                )

            if not response or not response.choices or not response.choices[0].message:
                self.console.print("[red]Error: Received empty response from API[/red]")
                return None

            response_content = response.choices[0].message.content
            if not response_content or not response_content.strip():
                self.console.print("[red]Error: Received empty response content from API[/red]")
                return None

            self.messages.append(user_message)
            self.messages.append({"role": "assistant", "content": response_content})
            if len(self.messages) > self.max_history:
                self.messages = self.messages[-self.max_history:]

            self._add_to_operation_history({
                'type': 'ai_response',
                'description': f"Generated response for: {user_input[:50]}...",
                'response_length': len(response_content)
            })

            return response_content

        except Exception as e:
            return f"❌ Error processing request with context: {str(e)}"

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
                    max_tokens=30000
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
            'make', 'build', 'generate',
            'button', 'function', 'component', 'page', 'file', 'code', 'feature',
            'website', 'app'
        ]
        
        user_lower = user_input.lower()
        
        # Check for modification keywords
        if any(keyword in user_lower for keyword in modification_keywords):
            return True
        
        # Check for pronouns that suggest modification of existing content
        pronouns = ['it', 'this', 'that', 'the', 'these', 'those']
        if any(pronoun in user_lower for pronoun in pronouns):
            # Check if there are recent changes or files to modify
            if self.recent_changes or self.task_context.get('files_modified'):
                return True
        
        # Check for context continuation keywords
        continuation_keywords = ['make it', 'change it to', 'update it', 'modify it', 'add to it']
        if any(keyword in user_lower for keyword in continuation_keywords):
            return True
        
        # Check for theme/style modifications (these should modify existing files)
        style_keywords = ['red', 'black', 'blue', 'green', 'theme', 'color', 'style', 'css']
        if any(keyword in user_lower for keyword in style_keywords):
            # If we have existing files, this should modify them
            if self.recent_changes or self.task_context.get('files_modified'):
                return True
        
        # Check if this seems like a continuation of previous work
        if self.task_context.get('task_continuation', False):
            return True
        
        # Check if essential context suggests we should modify existing files
        essential_context = self._extract_essential_context()
        if essential_context and ('Website/HTML project' in essential_context or 'HTML/Website' in essential_context):
            # If we have a website project and user mentions content, modify existing files
            content_keywords = ['college', 'school', 'university', 'delhi', 'mumbai', 'bangalore']
            if any(keyword in user_lower for keyword in content_keywords):
                return True
        
        return False
    
    def _handle_file_modification_request(self, user_input: str) -> Optional[str]:
        """Handle file modification requests with diff preview and user confirmation."""
        self.console.print(f"[cyan]🔧 Processing file modification request: {user_input}[/cyan]")
        
        # Check if this is a multi-file creation request
        if self._is_multi_file_creation_request(user_input):
            return self._handle_multi_file_creation_request(user_input)
        
        # Use the file operations system to handle the request
        try:
            # Try to find relevant files based on the request
            relevant_files = self._find_relevant_files(user_input)
            
            if not relevant_files:
                # Check if this is a modification request for non-existent files
                modification_keywords = ['modify', 'change', 'update', 'edit', 'add', 'remove', 'fix', 'improve']
                user_lower = user_input.lower()
                
                if any(keyword in user_lower for keyword in modification_keywords):
                    self.console.print("[yellow]No existing files found for modification.[/yellow]")
                    create_new = Prompt.ask(
                        "Would you like to create new files instead? (y/n)", 
                        choices=["y", "n"], 
                        default="y"
                    )
                    
                    if create_new.lower() == "y":
                        return self._handle_multi_file_creation_request(user_input)
                    else:
                        return "❌ No files to modify. Please specify existing files or create new ones."
                else:
                    # Default to creation for ambiguous requests
                    return self._handle_multi_file_creation_request(user_input)

            # Handle multiple files if found
            if len(relevant_files) > 1:
                self.console.print(f"[cyan]Found {len(relevant_files)} relevant files:[/cyan]")
                for i, file_path in enumerate(relevant_files, 1):
                    self.console.print(f"  {i}. {file_path}")
                
                choice = Prompt.ask(
                    "Which file(s) would you like to modify? (comma-separated numbers, or 'all')",
                    default="all"
                )
                
                if choice.lower() == "all":
                    target_files = relevant_files
                else:
                    try:
                        indices = [int(x.strip()) - 1 for x in choice.split(",")]
                        target_files = [relevant_files[i] for i in indices if 0 <= i < len(relevant_files)]
                    except (ValueError, IndexError):
                        self.console.print("[red]Invalid selection. Using first file.[/red]")
                        target_files = [relevant_files[0]]
            else:
                target_files = relevant_files

            # Process each target file with diff preview
            results = {}
            for target_file in target_files:
                self.console.print(f"[cyan]Processing: {target_file}[/cyan]")
                
                # Always use file operations with diff preview (never auto-apply)
                success = self.file_ops.review_file(
                    target_file,
                    self.current_model,
                    user_input,
                    auto_apply=False  # Always show diffs, never overwrite silently
                )
                
                results[target_file] = success
                
                if success:
                    self.recent_changes.append({
                        'file': target_file,
                        'timestamp': time.time(),
                        'action': 'modified'
                    })

            # Show summary and ask for confirmation
            successful_files = [f for f, success in results.items() if success]
            failed_files = [f for f, success in results.items() if not success]
            
            if successful_files:
                self.console.print(f"[green]✅ Successfully processed: {', '.join(successful_files)}[/green]")
            if failed_files:
                self.console.print(f"[red]❌ Failed to process: {', '.join(failed_files)}[/red]")
            
            # Single confirmation for the entire task
            if successful_files:
                self._ask_for_single_task_confirmation(user_input, successful_files)
            
            return f"✅ Task completed. {len(successful_files)} files processed successfully."
                
        except Exception as e:
            return f"❌ Error processing file modification: {str(e)}"

    def _is_multi_file_creation_request(self, user_input: str) -> bool:
        """Check if user input is requesting creation of multiple files."""
        creation_keywords = [
            'create', 'make', 'build', 'generate', 'set up', 'initialize',
            'website', 'app', 'project', 'structure', 'framework', 'new'
        ]
        
        modification_keywords = [
            'modify', 'change', 'update', 'edit', 'add', 'remove', 'fix', 'improve',
            'enhance', 'adjust', 'alter', 'revise', 'amend'
        ]
        
        user_lower = user_input.lower()
        
        # If it explicitly mentions creation keywords, it's a creation request
        if any(keyword in user_lower for keyword in creation_keywords):
            return True
        
        # If it mentions modification keywords, it's likely a modification request
        if any(keyword in user_lower for keyword in modification_keywords):
            return False
        
        # Default behavior: check if relevant files exist
        relevant_files = self._find_relevant_files(user_input)
        return len(relevant_files) == 0

    def _handle_multi_file_creation_request(self, user_input: str) -> Optional[str]:
        """Handle multi-file creation requests intelligently."""
        self.console.print(f"[cyan]🏗️ Processing multi-file creation request: {user_input}[/cyan]")
        
        # Use AI to determine what files are needed
        file_specs = self._determine_required_files(user_input)
        
        if not file_specs:
            return "❌ Could not determine required files for this request."
        
        self.console.print(f"[green]📋 Determined {len(file_specs)} files needed for this project[/green]")
        
        # Create files with diff preview (always show changes)
        results = {}
        if hasattr(self.file_ops, "create_multiple_files_from_prompt"):
            results = self.file_ops.create_multiple_files_from_prompt(
                file_specs,
                self.current_model,
                auto_apply=False
            )
        else:  # Fallback for simpler file operation implementations
            spec = file_specs[0]
            path = spec.get("path")
            prompt = spec.get("prompt", "")
            file_type = spec.get("type")
            success = self.file_ops.create_file_from_prompt(
                path,
                self.current_model,
                prompt,
                file_type,
            )
            results[path] = success
        
        # Track successful creations
        successful_files = []
        for file_path, success in results.items():
            if success:
                self.recent_changes.append({
                    'file': file_path,
                    'timestamp': time.time(),
                    'action': 'created'
                })
                self.accessible_files.add(file_path)
                successful_files.append(file_path)
        
        # Single confirmation for the entire task
        if successful_files:
            self._ask_for_single_task_confirmation(user_input, successful_files)

        if len(successful_files) == 1:
            return f"✅ Created new file: {successful_files[0]}"
        return f"✅ Created {len(successful_files)} files successfully: {', '.join(successful_files)}"

    def _determine_required_files(self, user_input: str) -> List[Dict[str, str]]:
        """Use AI to determine what files are needed for the request."""
        self.console.print("[cyan]🤖 Analyzing request to determine required files...[/cyan]")
        
        # Build context for AI analysis
        context = f"""
User Request: {user_input}

Project Context:
- Workspace: {self.workspace_path}
- Project Type: {self.project_structure.get('type', 'unknown')}
- Existing Files: {len(self.accessible_files)} files

IMPORTANT: Analyze this request carefully and create ONLY the files that are absolutely necessary to complete the task. 

CRITICAL RULES:
1. Do NOT create README.md, documentation, or configuration files unless explicitly requested
2. Do NOT create unnecessary files like .gitignore, package.json (unless it's a Node.js project), or requirements.txt (unless it's a Python project with dependencies)
3. Focus on the MINIMAL set of files needed for the specific task
4. If the user asks for a simple website, create only index.html and maybe styles.css
5. If the user asks for a data file, create only the data file
6. If the user asks for a script, create only the script file

Consider:
1. What is the MINIMAL set of files needed to complete this task?
2. What type of project is this (website, app, script, data file, etc.)?
3. What are the ESSENTIAL files for functionality?
4. Avoid creating documentation files unless explicitly needed
5. Focus on functional files that serve the user's specific request

Return a JSON array of file specifications with 'path' and 'prompt' keys.
Only include files that are truly necessary.

Examples:
- For a simple website: [{{"path": "index.html", "prompt": "Main HTML file"}}]
- For a data file: [{{"path": "data.json", "prompt": "JSON data file"}}]
- For a simple script: [{{"path": "script.py", "prompt": "Python script"}}]
- For a list of schools: [{{"path": "schools.json", "prompt": "JSON data with school information"}}]

Be minimal and focused. Only create what's needed.
"""
        
        try:
            # Get AI response for file structure
            response = self.api_client.chat_completion(
                messages=[{"role": "user", "content": context}],
                model=self.current_model,
                temperature=0.3,
                max_tokens=30000
            )

            if not response or not response.choices or not response.choices[0].message:
                return self._get_default_file_specs(user_input)

            response_content = response.choices[0].message.content
            
            # Try to parse JSON from response
            import json
            import re
            
            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', response_content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON array in the text
                json_match = re.search(r'\[.*?\]', response_content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    return self._get_default_file_specs(user_input)
            
            file_specs = json.loads(json_str)
            
            # Validate file specifications
            valid_specs = []
            for spec in file_specs:
                if isinstance(spec, dict) and 'path' in spec and 'prompt' in spec:
                    valid_specs.append(spec)
            
            if valid_specs:
                return valid_specs
            else:
                return self._get_default_file_specs(user_input)
                
        except Exception as e:
            self.console.print(f"[yellow]Warning: Could not parse AI response, using default structure: {e}[/yellow]")
            return self._get_default_file_specs(user_input)

    def _get_default_file_specs(self, user_input: str) -> List[Dict[str, str]]:
        """Get minimal default file specifications based on request keywords."""
        user_lower = user_input.lower()
        
        # Analyze the request more intelligently
        if any(keyword in user_lower for keyword in ['website', 'web', 'html', 'page']):
            # For websites, only create essential files
            if 'simple' in user_lower or 'basic' in user_lower:
                return [
                    {"path": "index.html", "prompt": f"Simple HTML file for: {user_input}"}
                ]
            else:
                return [
                    {"path": "index.html", "prompt": f"Main HTML file for: {user_input}"},
                    {"path": "styles.css", "prompt": "CSS styling for the website"}
                ]
        elif any(keyword in user_lower for keyword in ['app', 'application', 'react', 'vue', 'angular']):
            # For apps, only create essential files
            return [
                {"path": "package.json", "prompt": "Node.js package configuration"},
                {"path": "src/main.js", "prompt": f"Main application file for: {user_input}"}
            ]
        elif any(keyword in user_lower for keyword in ['python', 'script', 'tool']):
            # For Python scripts, only create the main file
            return [
                {"path": "main.py", "prompt": f"Python script for: {user_input}"}
            ]
        elif any(keyword in user_lower for keyword in ['data', 'json', 'csv', 'xml']):
            # For data files, create only the data file
            if 'json' in user_lower:
                return [{"path": "data.json", "prompt": f"JSON data for: {user_input}"}]
            elif 'csv' in user_lower:
                return [{"path": "data.csv", "prompt": f"CSV data for: {user_input}"}]
            else:
                return [{"path": "data.json", "prompt": f"Data file for: {user_input}"}]
        elif any(keyword in user_lower for keyword in ['config', 'settings', 'configuration']):
            # For configuration files
            return [{"path": "config.json", "prompt": f"Configuration for: {user_input}"}]
        else:
            # For unknown requests, create a single main file
            return [
                {"path": "main.html", "prompt": f"Main file for: {user_input}"}
            ]

    def _ask_for_single_task_confirmation(self, task_description: str, affected_files: List[str]) -> None:
        """Ask user for single confirmation after completing a task."""
        self.console.print(f"\n[bold cyan]🎉 Task completed: {task_description}[/bold cyan]")
        
        # Show brief project summary
        self._show_brief_project_summary(affected_files)
        
        self.console.print("\n[bold]What would you like to do?[/bold]")
        
        table = Table(show_header=False, box=None)
        table.add_column("Option", style="cyan")
        table.add_column("Description")
        
        table.add_row("A", "Accept all changes and continue")
        table.add_row("R", "Review changes in detail")
        table.add_row("C", "Continue with next task")
        
        self.console.print(table)
        
        choice = Prompt.ask(
            "Choose an option",
            choices=["A", "R", "C"],
            default="C"
        )
        
        if choice == "R":
            self._review_changes(affected_files)
        elif choice == "A":
            self.console.print("[green]✅ All changes accepted. Ready for next task.[/green]")
        else:  # C
            self.console.print("[cyan]Continuing with next task...[/cyan]")

    def _ask_for_task_confirmation(self, task_description: str, affected_files: List[str]) -> None:
        """Ask user for confirmation after completing a task."""
        self.console.print(f"\n[bold cyan]🎉 Task completed: {task_description}[/bold cyan]")
        
        # Show project structure summary
        self._show_project_summary(affected_files)
        
        self.console.print("\n[bold]What would you like to do next?[/bold]")
        
        table = Table(show_header=False, box=None)
        table.add_column("Option", style="cyan")
        table.add_column("Description")
        
        table.add_row("A", "Accept all changes and continue")
        table.add_row("R", "Review the changes in detail")
        table.add_row("M", "Make additional modifications")
        table.add_row("E", "Edit specific files")
        table.add_row("C", "Continue with next task")
        
        self.console.print(table)
        
        choice = Prompt.ask(
            "Choose an option",
            choices=["A", "R", "M", "E", "C"],
            default="C"
        )
        
        if choice == "R":
            self._review_changes(affected_files)
        elif choice == "M":
            self.console.print("[cyan]You can now make additional modifications using /edit or natural language.[/cyan]")
        elif choice == "E":
            self._edit_specific_files(affected_files)
        elif choice == "A":
            self.console.print("[green]✅ All changes accepted. Ready for next task.[/green]")
        else:  # C
            self.console.print("[cyan]Continuing with next task...[/cyan]")

    def _show_brief_project_summary(self, affected_files: List[str]) -> None:
        """Show a brief summary of the project structure."""
        self.console.print(f"\n[bold cyan]📊 Project Summary:[/bold cyan]")
        
        # Show file structure
        structure_table = Table(title="📁 Created Files", show_header=True, header_style="bold magenta")
        structure_table.add_column("#", style="dim", width=4)
        structure_table.add_column("File Path", style="cyan")
        structure_table.add_column("Type", style="green")
        structure_table.add_column("Status", style="yellow")
        
        for i, file_path in enumerate(affected_files, 1):
            path = Path(file_path)
            file_type = path.suffix or "No extension"
            
            # Check if file exists and get size
            try:
                if path.exists():
                    size = path.stat().st_size
                    status = f"✅ {size} bytes"
                else:
                    status = "❌ Not found"
            except:
                status = "❓ Unknown"
            
            structure_table.add_row(str(i), str(path), file_type, status)
        
        self.console.print(structure_table)

    def _show_project_summary(self, affected_files: List[str]) -> None:
        """Show a summary of the project structure."""
        self.console.print(f"\n[bold cyan]📊 Project Summary:[/bold cyan]")
        
        # Show file structure
        structure_table = Table(title="📁 Created Files", show_header=True, header_style="bold magenta")
        structure_table.add_column("#", style="dim", width=4)
        structure_table.add_column("File Path", style="cyan")
        structure_table.add_column("Type", style="green")
        structure_table.add_column("Status", style="yellow")
        
        for i, file_path in enumerate(affected_files, 1):
            path = Path(file_path)
            file_type = path.suffix or "No extension"
            
            # Check if file exists and get size
            try:
                if path.exists():
                    size = path.stat().st_size
                    status = f"✅ {size} bytes"
                else:
                    status = "❌ Not found"
            except:
                status = "❓ Unknown"
            
            structure_table.add_row(str(i), str(path), file_type, status)
        
        self.console.print(structure_table)
        
        # Show project statistics
        total_files = len(affected_files)
        total_size = sum(Path(f).stat().st_size for f in affected_files if Path(f).exists())
        
        stats_info = f"""
[bold]📈 Project Statistics:[/bold]
• Total Files: {total_files}
• Total Size: {total_size} bytes
• Project Type: {self.project_structure.get('type', 'unknown')}
• Workspace: {self.workspace_path}
        """.strip()
        
        panel = Panel(
            stats_info,
            title="📊 Project Stats",
            border_style="blue",
            padding=(1, 2)
        )
        
        self.console.print(panel)

    def _edit_specific_files(self, affected_files: List[str]) -> None:
        """Allow editing of specific files."""
        self.console.print(f"\n[bold cyan]✏️ Edit Specific Files:[/bold cyan]")
        
        # Show file list
        for i, file_path in enumerate(affected_files, 1):
            self.console.print(f"  {i}. {file_path}")
        
        choice = Prompt.ask(
            "Enter file number to edit (or 'all' for all files)",
            default="all"
        )
        
        if choice.lower() == "all":
            files_to_edit = affected_files
        else:
            try:
                file_index = int(choice) - 1
                if 0 <= file_index < len(affected_files):
                    files_to_edit = [affected_files[file_index]]
                else:
                    self.console.print("[red]Invalid file number.[/red]")
                    return
            except ValueError:
                self.console.print("[red]Invalid input.[/red]")
                return
        
        # Edit each file
        for file_path in files_to_edit:
            self.console.print(f"\n[cyan]Editing: {file_path}[/cyan]")
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                edited_content = self.file_ops._edit_file_content(file_path, content)
                if edited_content is not None:
                    with open(file_path, 'w') as f:
                        f.write(edited_content)
                    self.console.print(f"[green]✅ Updated: {file_path}[/green]")
                else:
                    self.console.print(f"[yellow]⚠️ No changes made to: {file_path}[/yellow]")
                    
            except Exception as e:
                self.console.print(f"[red]Error editing {file_path}: {e}[/red]")

    def _review_changes(self, affected_files: List[str]) -> None:
        """Review changes made to files."""
        self.console.print(f"\n[bold cyan]Reviewing changes for {len(affected_files)} files:[/bold cyan]")
        
        for file_path in affected_files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                self.console.print(f"\n[bold yellow]{file_path}:[/bold yellow]")
                self.file_ops.diff_manager.show_file_preview(file_path, content, "Current Content")
                
            except Exception as e:
                self.console.print(f"[red]Error reading {file_path}: {e}[/red]")
    
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
[bold magenta]🚀 Advanced Agent Commands[/bold magenta]

[bold cyan]File Operations:[/bold cyan]
  /files              - List all accessible files
  /scan               - Rescan workspace for new files
  /read <file>        - Read and preview a file
  /edit <file1> [file2 ...] - Edit one or more files (always shows diffs)
  /create <file1> [file2 ...] - Create one or more files (always shows diffs)
  /delete <file>      - Delete a file
  /analyze <file>     - Analyze code structure and quality

[bold cyan]Workspace:[/bold cyan]
  /workspace          - Show workspace information
  /status             - Show system status
  /tools              - Display available tools
  /context            - Show 64k context optimization status
  /history            - Show recent changes

[bold cyan]Model Management:[/bold cyan]
  /model              - Change AI model interactively
  /shortcuts          - Show quick model switching shortcuts
  /fast, /balanced, /powerful, /ultra - Quick model switches
  /next, /prev        - Cycle through models

[bold cyan]Mode Switching:[/bold cyan]
  /qna                - Switch to Q&A mode (read-only)
  /agent              - Switch to Agent mode (file modifications)
  /mode <mode>        - Switch to specified mode

[bold cyan]Search & Analysis:[/bold cyan]
  /search <query>     - Semantic codebase search

[bold cyan]General:[/bold cyan]
  /help               - Show this help
  /clear              - Clear chat history
  /exit               - Quit CodeFlow

[bold yellow]💡 Tip:[/bold yellow] You can edit multiple files simultaneously with /edit file1 file2 file3
[bold yellow]💡 Tip:[/bold yellow] Use natural language to describe file changes
[bold yellow]💡 Tip:[/bold yellow] All changes are shown as diffs: [bold green]+ Green[/bold green] for additions, [bold red]- Red[/bold red] for deletions
        """
        
        panel = Panel(
            help_text,
            title="🛠️ Advanced Agent Help",
            border_style="magenta",
            padding=(1, 2)
        )
        
        self.console.print(panel)

    def _list_accessible_files(self) -> None:
        """List all accessible files in the workspace."""
        if not self.accessible_files:
            self.console.print("[yellow]No accessible files found in workspace[/yellow]")
            return
        
        table = Table(title="📁 Accessible Files", show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim", width=4)
        table.add_column("File Path", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Size", style="yellow")
        
        for i, file_path in enumerate(sorted(self.accessible_files), 1):
            path = Path(file_path)
            file_type = path.suffix or "No extension"
            try:
                size = path.stat().st_size
                size_str = self._format_file_size(size)
            except OSError:
                size_str = "Unknown"
            
            table.add_row(str(i), str(path), file_type, size_str)
        
        self.console.print(table)

    def _rescan_workspace(self) -> None:
        """Rescan the workspace for files."""
        with Status("[bold green]Rescanning workspace...", console=self.console):
            self._scan_workspace()
        
        self.console.print(f"[green]Found {len(self.accessible_files)} accessible files[/green]")

    def _show_workspace_info(self) -> None:
        """Show workspace information."""
        workspace_info = f"""
[bold]Workspace Path:[/bold] {self.workspace_path}
[bold]Accessible Files:[/bold] {len(self.accessible_files)}
[bold]Current Model:[/bold] {self.current_model}
[bold]Project Type:[/bold] {self.project_structure.get('type', 'unknown')}
        """.strip()
        
        panel = Panel(
            workspace_info,
            title="📊 Workspace Information",
            border_style="blue",
            padding=(1, 2)
        )
        
        self.console.print(panel)

    def _handle_create(self, file_paths: str) -> None:
        """Handle create command for one or more files."""
        if not file_paths:
            self.console.print("[red]Please specify one or more file paths[/red]")
            self.console.print("Usage: /create <file1> [file2 ...]")
            return
        
        requested = file_paths.split()
        
        if len(requested) == 1:
            # Single file creation
            file_path = requested[0]
            prompt = Prompt.ask("What should this file contain?")
            if not prompt:
                self.console.print("[yellow]File creation cancelled[/yellow]")
                return
            
            success = self.file_ops.create_file_from_prompt(
                file_path,
                self.current_model,
                prompt
            )
            
            if success:
                self.console.print(f"[green]✓ File created successfully: {file_path}[/green]")
                self.recent_changes.append({
                    'file': file_path,
                    'timestamp': time.time(),
                    'action': 'created'
                })
                # Add to accessible files
                self.accessible_files.add(file_path)
            else:
                self.console.print(f"[red]✗ Failed to create file: {file_path}[/red]")
        else:
            # Multiple file creation
            self.console.print(f"[cyan]Creating {len(requested)} files...[/cyan]")
            
            file_specs = []
            for file_path in requested:
                prompt = Prompt.ask(f"What should {file_path} contain?")
                if prompt:
                    file_specs.append({
                        'path': file_path,
                        'prompt': prompt
                    })
            
            if not file_specs:
                self.console.print("[yellow]No files to create[/yellow]")
                return
            
            results = self.file_ops.create_multiple_files_from_prompt(
                file_specs,
                self.current_model,
                auto_apply=False
            )
            
            # Track successful creations
            for file_path, success in results.items():
                if success:
                    self.recent_changes.append({
                        'file': file_path,
                        'timestamp': time.time(),
                        'action': 'created'
                    })
                    # Add to accessible files
                    self.accessible_files.add(file_path)

    def _handle_delete(self, file_path: str) -> None:
        """Handle delete command."""
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
        
        if Prompt.ask(f"Are you sure you want to delete {target_file}?", default=False):
            try:
                Path(target_file).unlink()
                self.console.print(f"[green]✓ File deleted: {target_file}[/green]")
                self.accessible_files.remove(target_file)
                self.recent_changes.append({
                    'file': target_file,
                    'timestamp': time.time(),
                    'action': 'deleted'
                })
            except Exception as e:
                self.console.print(f"[red]Error deleting file: {e}[/red]")
        else:
            self.console.print("[yellow]File deletion cancelled[/yellow]")

    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

    # ============================================================================
    # CONTEXT OPTIMIZATION METHODS - Full 64k Context Window Utilization
    # ============================================================================

    def _initialize_context_optimization(self) -> None:
        """Initialize context optimization for full 64k context window usage."""
        self.console.print("[cyan]🔧 Initializing Context Optimization (64k tokens)...[/cyan]")
        
        # Initialize context tracking
        self.operation_history = []
        self.task_context = {
            'current_task': None,
            'task_start_time': None,
            'files_modified': [],
            'operations_performed': [],
            'context_summary': '',
            'session_id': str(int(time.time()))
        }
        
        self.session_state = {
            'total_operations': 0,
            'files_accessed': set(),
            'models_used': set(),
            'context_utilization': 0.0
        }
        
        self.context_buffer = []
        self.current_context_size = 0
        
        self.console.print("[green]✅ Context optimization initialized[/green]")

    def _add_to_operation_history(self, operation: Dict[str, Any]) -> None:
        """Add operation to history for context building."""
        operation['timestamp'] = time.time()
        operation['session_id'] = self.task_context['session_id']
        
        self.operation_history.append(operation)
        self.session_state['total_operations'] += 1
        
        # Update context size estimation
        self._update_context_size()

    def _update_context_size(self) -> None:
        """Update current context size estimation."""
        # Rough estimation: 1 token ≈ 4 characters
        total_chars = sum(len(str(op)) for op in self.operation_history)
        self.current_context_size = total_chars // 4
        
        # Calculate utilization percentage
        self.session_state['context_utilization'] = (self.current_context_size / self.max_context_tokens) * 100

    def _build_smart_context(self, user_input: str) -> str:
        """Build smart context using full 64k context window effectively."""
        context_parts = []
        
        # 1. CONVERSATION HISTORY (highest priority - maintain continuity)
        if self.messages:
            context_parts.append("=== CONVERSATION HISTORY ===")
            # Include last 5 conversation exchanges for context continuity
            recent_messages = self.messages[-10:]  # Last 10 messages (5 exchanges)
            for msg in recent_messages:
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')
                if role == 'user':
                    context_parts.append(f"USER: {content}")
                elif role == 'assistant':
                    context_parts.append(f"ASSISTANT: {content}")
                elif role == 'system':
                    context_parts.append(f"SYSTEM: {content}")
            context_parts.append("=== END CONVERSATION HISTORY ===\n")
        
        # 2. CURRENT TASK CONTEXT (high priority)
        if self.task_context['current_task']:
            context_parts.append("=== CURRENT TASK CONTEXT ===")
            context_parts.append(f"Current Task: {self.task_context['current_task']}")
            context_parts.append(f"Task Start Time: {self.task_context['task_start_time']}")
            context_parts.append(f"Files Modified: {', '.join(self.task_context['files_modified'])}")
            context_parts.append("=== END TASK CONTEXT ===\n")
        
        # 3. RECENT OPERATIONS (medium priority)
        recent_ops = self.operation_history[-15:]  # Last 15 operations for better continuity
        if recent_ops:
            context_parts.append("=== RECENT OPERATIONS ===")
            for op in recent_ops:
                op_type = op.get('type', 'unknown')
                description = op.get('description', '')
                timestamp = time.strftime('%H:%M:%S', time.localtime(op.get('timestamp', 0)))
                context_parts.append(f"- [{timestamp}] {op_type}: {description}")
            context_parts.append("=== END RECENT OPERATIONS ===\n")
        
        # 4. PROJECT CONTEXT (medium priority)
        context_parts.append("=== PROJECT CONTEXT ===")
        context_parts.append(f"Workspace Path: {self.workspace_path}")
        context_parts.append(f"Accessible Files: {len(self.accessible_files)}")
        context_parts.append(f"Project Type: {self.project_structure.get('type', 'Unknown')}")
        
        # Add recent file changes for context
        if self.recent_changes:
            context_parts.append("Recent File Changes:")
            for change in self.recent_changes[-5:]:  # Last 5 changes
                file_name = Path(change['file']).name
                action = change.get('action', 'modified')
                timestamp = time.strftime('%H:%M:%S', time.localtime(change['timestamp']))
                context_parts.append(f"  - [{timestamp}] {file_name} ({action})")
        context_parts.append("=== END PROJECT CONTEXT ===\n")
        
        # 5. SESSION STATE (low priority)
        context_parts.append("=== SESSION STATE ===")
        context_parts.append(f"Total Operations: {self.session_state['total_operations']}")
        context_parts.append(f"Files Accessed: {len(self.session_state['files_accessed'])}")
        context_parts.append(f"Context Utilization: {self.session_state['context_utilization']:.1f}%")
        context_parts.append(f"Current Model: {self.current_model}")
        context_parts.append("=== END SESSION STATE ===\n")
        
        # 6. CURRENT USER REQUEST (highest priority)
        context_parts.append("=== CURRENT USER REQUEST ===")
        context_parts.append(f"User Input: {user_input}")
        context_parts.append("=== END CURRENT USER REQUEST ===\n")
        
        # 7. ESSENTIAL CONTEXT PRESERVATION (highest priority)
        essential_context = self._extract_essential_context()
        if essential_context:
            context_parts.append("=== ESSENTIAL CONTEXT (CRITICAL) ===")
            context_parts.append("CRITICAL: The following information MUST be preserved in all operations:")
            context_parts.append(essential_context)
            context_parts.append("=== END ESSENTIAL CONTEXT ===\n")
        
        # 8. CONTEXT INSTRUCTIONS (high priority)
        context_parts.append("=== CONTEXT INSTRUCTIONS ===")
        context_parts.append("IMPORTANT: Maintain continuity with previous conversation and tasks.")
        context_parts.append("If the user refers to previous work (like 'change it to', 'make it', etc.),")
        context_parts.append("refer to the conversation history and current task context above.")
        context_parts.append("Do not lose track of what was previously created or modified.")
        context_parts.append("When modifying existing files, preserve the current content and enhance it.")
        context_parts.append("CRITICAL: Always preserve the ESSENTIAL CONTEXT above in all operations.")
        context_parts.append("Do not remove or replace existing content unless explicitly requested.")
        context_parts.append("=== END CONTEXT INSTRUCTIONS ===")
        
        return "\n".join(context_parts)

    def _extract_essential_context(self) -> str:
        """Extract essential context that must be preserved across all operations."""
        essential_parts = []
        
        # Extract from conversation history
        if self.messages:
            # Look for key information in recent messages
            recent_messages = self.messages[-6:]  # Last 6 messages (3 exchanges)
            
            for msg in recent_messages:
                content = msg.get('content', '').lower()
                role = msg.get('role', '')
                
                # Extract website/HTML context
                if 'website' in content or 'html' in content or 'web' in content:
                    essential_parts.append("PROJECT TYPE: Website/HTML project")
                    break
                
                # Extract location context (Delhi, etc.)
                if 'delhi' in content or 'location' in content or 'city' in content:
                    essential_parts.append(f"LOCATION: {self._extract_location_from_content(content)}")
                
                # Extract content type context (schools, colleges, etc.)
                if 'school' in content or 'college' in content or 'university' in content:
                    content_type = self._extract_content_type_from_content(content)
                    if content_type:
                        essential_parts.append(f"CONTENT TYPE: {content_type}")
                
                # Extract file type context
                if 'json' in content:
                    essential_parts.append("FILE TYPE: JSON data structure")
                elif 'html' in content or 'website' in content:
                    essential_parts.append("FILE TYPE: HTML/Website")
        
        # Extract from task context
        current_task = self.task_context.get('current_task', '')
        if current_task:
            task_lower = current_task.lower()
            
            # Extract website context from task
            if 'website' in task_lower or 'html' in task_lower:
                essential_parts.append("PROJECT TYPE: Website/HTML project")
            
            # Extract location from task
            if 'delhi' in task_lower:
                essential_parts.append("LOCATION: Delhi")
            
            # Extract content type from task
            if 'school' in task_lower:
                essential_parts.append("CONTENT TYPE: Schools")
            elif 'college' in task_lower:
                essential_parts.append("CONTENT TYPE: Colleges")
        
        # Extract from recent operations
        recent_ops = self.operation_history[-5:]  # Last 5 operations
        for op in recent_ops:
            description = op.get('description', '').lower()
            
            # Check for file creation/modification
            if 'html' in description or 'website' in description:
                essential_parts.append("PROJECT TYPE: Website/HTML project")
            
            # Check for content type
            if 'school' in description:
                essential_parts.append("CONTENT TYPE: Schools")
            elif 'college' in description:
                essential_parts.append("CONTENT TYPE: Colleges")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_parts = []
        for part in essential_parts:
            if part not in seen:
                seen.add(part)
                unique_parts.append(part)
        
        return "\n".join(unique_parts) if unique_parts else ""

    def _extract_location_from_content(self, content: str) -> str:
        """Extract location information from content."""
        import re
        
        # Look for city names
        cities = ['delhi', 'mumbai', 'bangalore', 'chennai', 'kolkata', 'hyderabad', 'pune', 'ahmedabad']
        for city in cities:
            if city in content:
                return city.title()
        
        # Look for location patterns
        location_patterns = [
            r'in\s+([A-Za-z]+)',  # "in Delhi"
            r'of\s+([A-Za-z]+)',  # "of Delhi"
            r'([A-Za-z]+)\s+schools',  # "Delhi schools"
            r'([A-Za-z]+)\s+colleges'  # "Delhi colleges"
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1).title()
        
        return "Unknown"

    def _extract_content_type_from_content(self, content: str) -> str:
        """Extract content type information from content."""
        if 'school' in content:
            return "Schools"
        elif 'college' in content:
            return "Colleges"
        elif 'university' in content:
            return "Universities"
        elif 'institute' in content:
            return "Institutes"
        return ""

    def _optimize_context_for_64k(self, context: str) -> str:
        """Optimize context to fit within 64k token limit while preserving important information."""
        # Estimate current context size
        estimated_tokens = len(context) // 4
        
        if estimated_tokens <= self.max_context_tokens:
            return context
        
        # If context is too large, prioritize information
        self.console.print(f"[yellow]⚠️ Context size ({estimated_tokens} tokens) approaching limit. Optimizing...[/yellow]")
        
        # Priority-based context trimming
        priority_sections = [
            "=== ESSENTIAL CONTEXT (CRITICAL) ===",
            "=== CONVERSATION HISTORY ===",
            "=== CURRENT USER REQUEST ===",
            "=== CURRENT TASK CONTEXT ===",
            "=== CONTEXT INSTRUCTIONS ===",
            "=== RECENT OPERATIONS ===",
            "=== PROJECT CONTEXT ===",
            "=== SESSION STATE ==="
        ]
        
        optimized_context = []
        remaining_tokens = self.max_context_tokens
        
        for section in priority_sections:
            section_content = self._extract_section(context, section)
            section_tokens = len(section_content) // 4
            
            if section_tokens <= remaining_tokens:
                optimized_context.append(section_content)
                remaining_tokens -= section_tokens
            else:
                # Truncate section to fit
                truncated_content = section_content[:remaining_tokens * 4]
                optimized_context.append(truncated_content + "\n[Context truncated for optimization]")
                break
        
        return "\n".join(optimized_context)

    def _extract_section(self, context: str, section_name: str) -> str:
        """Extract a specific section from context."""
        lines = context.split('\n')
        section_lines = []
        in_section = False
        
        for line in lines:
            if line.startswith(section_name):
                in_section = True
                section_lines.append(line)
            elif in_section and line.strip() and not line.startswith('- '):
                # End of section
                break
            elif in_section:
                section_lines.append(line)
        
        return '\n'.join(section_lines)

    def _update_task_context(self, task_description: str, files_affected: List[str] = None) -> None:
        """Update current task context for persistent state."""
        # Check if this is a continuation of a previous task
        previous_task = self.task_context.get('current_task', '')
        
        # If the new task seems related to the previous one, maintain continuity
        if previous_task and any(keyword in task_description.lower() for keyword in ['change', 'modify', 'update', 'make', 'add', 'remove', 'it', 'this', 'that']):
            # This is likely a continuation/modification of the previous task
            self.task_context['current_task'] = f"{previous_task} → {task_description}"
            self.task_context['task_continuation'] = True
        else:
            # This is a new task
            self.task_context['current_task'] = task_description
            self.task_context['task_continuation'] = False
        
        self.task_context['task_start_time'] = time.time()
        
        if files_affected:
            self.task_context['files_modified'].extend(files_affected)
            # Keep only unique files
            self.task_context['files_modified'] = list(set(self.task_context['files_modified']))
        
        # Add to operation history with enhanced tracking
        self._add_to_operation_history({
            'type': 'task_update',
            'description': f"Task: {task_description}",
            'files_affected': files_affected or [],
            'is_continuation': self.task_context.get('task_continuation', False),
            'previous_task': previous_task
        })

    def _get_context_summary(self) -> str:
        """Get a summary of current context for display."""
        summary = f"""
[bold cyan]📊 Context Summary (64k Token Optimization)[/bold cyan]

[bold]Current Task:[/bold] {self.task_context.get('current_task', 'None')}
[bold]Session ID:[/bold] {self.task_context.get('session_id', 'Unknown')}
[bold]Total Operations:[/bold] {self.session_state['total_operations']}
[bold]Context Utilization:[/bold] {self.session_state['context_utilization']:.1f}%
[bold]Files Modified:[/bold] {len(self.task_context.get('files_modified', []))}
[bold]Recent Operations:[/bold] {len(self.operation_history[-5:])} in last 5
        """.strip()
        
        return summary

    def _show_context_status(self) -> None:
        """Show current context status and optimization info."""
        summary = self._get_context_summary()
        panel = Panel(
            summary,
            title="🔧 Context Optimization Status",
            border_style="cyan",
            padding=(1, 2)
        )
        self.console.print(panel)
