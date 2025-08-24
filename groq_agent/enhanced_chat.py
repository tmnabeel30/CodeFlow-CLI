"""Enhanced interactive chat session with automatic file access and better UI."""

import sys
import os
import glob
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
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
from rich.layout import Layout
from rich.columns import Columns
from rich.align import Align
from rich.rule import Rule
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.status import Status

from .config import ConfigurationManager
from .api_client import GroqAPIClient
from .model_selector import ModelSelector
from .file_operations import FileOperations
from .handbook_manager import HandbookManager


class EnhancedChatSession:
    """Enhanced chat session with automatic file access and better UI.

    Supports an optional read-only mode to prevent file modifications.
    """
    
    def __init__(self, config: ConfigurationManager, api_client: GroqAPIClient, read_only: bool = False,
                 handbook_manager: Optional[HandbookManager] = None):
        """Initialize the enhanced chat session.
        
        Args:
            config: Configuration manager instance
            api_client: Groq API client instance
            read_only: Whether to run in read-only mode
            handbook_manager: Optional handbook manager instance
        """
        self.config = config
        self.api_client = api_client
        self.model_selector = ModelSelector(api_client)
        self.file_ops = FileOperations(api_client)
        self.handbook_manager = handbook_manager
        self.console = Console()
        self.read_only = read_only
        self.prompt_style = Style.from_dict({
            'prompt': 'bold ansicyan',
            'toolbar': 'reverse ansimagenta'
        })
        
        # Chat state
        self.current_model = config.get_default_model()
        self.messages: List[Dict[str, str]] = []
        self.max_history = config.get_max_history()
        
        # File context
        self.workspace_path = Path.cwd()
        self.accessible_files: Set[str] = set()
        self.current_file_context: Optional[Dict[str, Any]] = None
        
        # Context Optimization - Full 64k context utilization
        self.operation_history: List[Dict[str, Any]] = []
        self.task_context: Dict[str, Any] = {}
        self.session_state: Dict[str, Any] = {}
        self.context_buffer: List[Dict[str, Any]] = []
        self.max_context_tokens = 64000  # Full context window
        self.current_context_size = 0
        self.context_optimization_enabled = True
        
        # Setup history file
        history_file = config.config_dir / "chat_history.txt"
        self.history = FileHistory(str(history_file))
        
        # Enhanced command completions
        base_commands = [
            '/help', '/model', '/exit', '/clear', '/history', '/files', '/scan', '/read', '/workspace', '/clear-context',
            '/fast', '/balanced', '/powerful', '/ultra', '/mixtral', '/gemma', '/compound', '/compound-mini',
            '/next', '/prev', '/shortcuts', '/agent', '/advanced'
        ]
        if not self.read_only:
            base_commands.append('/edit')
        self.command_completer = WordCompleter(base_commands)
        
        # Auto-scan workspace on startup
        self._scan_workspace()
        
        # Initialize context optimization
        self._initialize_context_optimization()
    
    def _scan_workspace(self) -> None:
        """Automatically scan the workspace for accessible files."""
        with Status("[bold green]Scanning workspace for files...", console=self.console):
            self.accessible_files = self._get_accessible_files()
    
    def _get_accessible_files(self) -> Set[str]:
        """Get all accessible files in the workspace.
        
        Returns:
            Set of file paths
        """
        files = set()
        
        # Common file extensions to include
        extensions = {
            '*.py', '*.js', '*.ts', '*.jsx', '*.tsx', '*.html', '*.css', 
            '*.json', '*.yaml', '*.yml', '*.md', '*.txt', '*.sh', '*.bash',
            '*.java', '*.cpp', '*.c', '*.h', '*.hpp', '*.go', '*.rs', '*.php',
            '*.rb', '*.sql', '*.xml', '*.toml', '*.ini', '*.conf'
        }
        
        # Scan for files
        for ext in extensions:
            files.update(glob.glob(str(self.workspace_path / "**" / ext), recursive=True))
        
        # Also include files without extensions that might be important
        important_files = ['Dockerfile', 'Makefile', 'README', 'LICENSE', '.env', '.gitignore']
        for file in important_files:
            files.update(glob.glob(str(self.workspace_path / "**" / file), recursive=True))
        
        # Filter out common directories to ignore
        ignore_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', 'env', '.pytest_cache'}
        filtered_files = set()
        
        for file_path in files:
            path = Path(file_path)
            if not any(ignore_dir in path.parts for ignore_dir in ignore_dirs):
                filtered_files.add(str(path))
        
        return filtered_files
    
    def start(self) -> Optional[str]:
        """Start the enhanced interactive chat session.

        Returns 'agent' if user requested switching to Agent mode, otherwise None.
        """
        self._show_enhanced_welcome()
        
        # Check if we need to select a model
        if not self.current_model:
            self._select_initial_model()
        
        # Main chat loop
        self._switch_to_mode: Optional[str] = None
        while True:
            try:
                # Get user input with enhanced prompt
                user_input = self._get_enhanced_user_input()
                
                if not user_input.strip():
                    continue
                
                # Handle commands
                if user_input.startswith('/'):
                    if self._handle_enhanced_command(user_input):
                        break
                    continue
                
                # Update task context for persistent state
                self._update_task_context(user_input)
                
                # Send message to API with context optimization
                response = self._send_enhanced_message_with_context(user_input)
                if response:
                    self._display_enhanced_response(response)
                else:
                    # If no response was received, show a helpful message
                    self.console.print("[yellow]No response received. This could be due to:[/yellow]")
                    self.console.print("[yellow]• Network connectivity issues[/yellow]")
                    self.console.print("[yellow]• API rate limits[/yellow]")
                    self.console.print("[yellow]• Context length limits[/yellow]")
                    self.console.print("[yellow]Try asking a shorter question or use /clear to reset the conversation.[/yellow]")
                
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Use /exit to quit the chat session[/yellow]")
            except EOFError:
                break
            except Exception as e:
                self.console.print(f"[red]Error: {e}[/red]")
        return self._switch_to_mode
    def _show_enhanced_welcome(self) -> None:
        """Display enhanced welcome message with better UI."""
        
        # Create a beautiful welcome layout
        layout = Layout()
        
        # Header
        header_title = "🚀 Groq CLI Agent"
        if self.read_only:
            header_title += "  •  MODE: Q&A (Read-only)"
        else:
            header_title += "  •  MODE: Agent (Can modify files)"
        header = Panel(
            Align.center(
                Text(header_title, style="bold blue", justify="center")
            ),
            subtitle="GitHub: TM NABEEL @tmnabeel30 created",
            subtitle_align="right",
            border_style="blue",
            padding=(1, 2)
        )
        
        # Workspace info
        workspace_info = f"""
[bold]Workspace:[/bold] {self.workspace_path}
[bold]Files Found:[/bold] {len(self.accessible_files)} accessible files
[bold]Current Model:[/bold] {self.current_model or 'Not set'}
        """.strip()
        
        workspace_panel = Panel(
            workspace_info,
            title="📁 Workspace Information",
            border_style="green",
            padding=(1, 2)
        )
        
        # Available commands
        commands_table = Table(show_header=False, box=None, padding=(0, 1))
        commands_table.add_column("Command", style="cyan", no_wrap=True)
        commands_table.add_column("Description", style="white")
        
        commands = [
            ("/help", "Show this help message"),
            ("/model", "Change the AI model"),
            ("/fast", "Switch to fast model"),
            ("/powerful", "Switch to powerful model"),
            ("/next/prev", "Cycle through models"),
            ("/files", "List accessible files"),
            ("/scan", "Rescan workspace for files"),
            ("/read <file>", "Read and analyze a file"),
            ("/clear-context", "Clear file context"),
            ("/workspace", "Show workspace information"),
            ("/clear", "Clear chat history"),
            ("/exit", "Exit the chat session")
        ]
        if not self.read_only:
            commands.insert(5, ("/edit <file1> [file2 ...]", "Edit one or more files with AI assistance"))
        
        for cmd, desc in commands:
            commands_table.add_row(cmd, desc)
        
        commands_panel = Panel(
            commands_table,
            title="⚡ Available Commands",
            border_style="yellow",
            padding=(1, 2)
        )
        
        # Tips
        tips = f"""
[bold]💡 Tips:[/bold]
• I can automatically see all files in your workspace
• Just ask me to read, analyze, or modify any file
• Use /read <filename> to focus on a specific file
• I can suggest improvements and apply them directly
• Quick model switch: /fast, /balanced, /powerful, /ultra
• Current model: {self.current_model or 'Not set'}
        """.strip()
        
        tips_panel = Panel(
            tips,
            title="💡 Quick Tips",
            border_style="magenta",
            padding=(1, 2)
        )
        
        # Combine all panels
        welcome_content = Columns([
            workspace_panel,
            commands_panel,
            tips_panel
        ], equal=True, expand=True)
        
        self.console.print(header)
        self.console.print()
        self.console.print(welcome_content)
        self.console.print()
        self.console.print(Rule(style="blue"))
        self.console.print()
    
    def _get_enhanced_user_input(self) -> str:
        """Get user input with enhanced prompt styling."""
        prompt_tokens = FormattedText([
            ('class:prompt', f"You ({self.current_model}): ")
        ])

        bottom_toolbar = FormattedText([
            ('class:toolbar', ' GitHub: TM NABEEL @tmnabeel30 created ')
        ])

        return prompt(
            prompt_tokens,
            history=self.history,
            completer=self.command_completer,
            multiline=False,
            style=self.prompt_style,
            bottom_toolbar=bottom_toolbar
        )
    
    def _handle_enhanced_command(self, command: str) -> bool:
        """Handle enhanced slash commands.
        
        Args:
            command: The command string
            
        Returns:
            True if should exit, False otherwise
        """
        parts = command.split(' ', 1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        if cmd == '/help':
            self._show_enhanced_help()
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
        elif cmd == '/read':
            self._read_file(args)
        elif cmd == '/edit':
            if self.read_only:
                self.console.print("[yellow]Edit is disabled in Q&A (read-only) mode[/yellow]")
            else:
                self._edit_files(args)
        elif cmd == '/clear-context':
            self._clear_file_context()
        elif cmd == '/agent' or (cmd == '/mode' and args.strip().lower() == 'agent'):
            # Switch to Agent mode
            self._switch_to_mode = 'agent'
            return True
        elif cmd == '/advanced' or (cmd == '/mode' and args.strip().lower() == 'advanced'):
            # Switch to Advanced Agent mode
            self._switch_to_mode = 'agentic'
            return True
        elif cmd == '/qna' or (cmd == '/mode' and args.strip().lower() == 'qna'):
            self.console.print("[yellow]Already in Q&A mode[/yellow]")
        elif cmd == '/workspace':
            self._show_workspace_info()
        elif cmd == '/context':
            self._show_context_status()  # Show context optimization status
        elif cmd == '/clear':
            self._clear_history()
        elif cmd == '/exit':
            return True
        else:
            self.console.print(f"[red]Unknown command: {cmd}[/red]")
            self.console.print("Type /help for available commands")
        
        return False
    
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
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def _rescan_workspace(self) -> None:
        """Rescan the workspace for files."""
        with Status("[bold green]Rescanning workspace...", console=self.console):
            self.accessible_files = self._get_accessible_files()
        
        self.console.print(f"[green]Found {len(self.accessible_files)} accessible files[/green]")
    
    def _read_file(self, file_path: str) -> None:
        """Read and analyze a file."""
        if not file_path:
            self.console.print("[red]Please specify a file path[/red]")
            self.console.print("Usage: /read <file_path>")
            return
        
        # Try to find the file
        target_file = None
        for accessible_file in self.accessible_files:
            if file_path in accessible_file or Path(accessible_file).name == file_path:
                target_file = accessible_file
                break
        
        if not target_file:
            self.console.print(f"[red]File not found: {file_path}[/red]")
            self.console.print("Use /files to see available files")
            return
        
        # Read and display the file
        try:
            with open(target_file, 'r') as f:
                content = f.read()
            
            self.current_file_context = {
                'path': target_file,
                'content': content,
                'name': Path(target_file).name
            }
            
            # Show file info
            file_info = self.file_ops._get_file_info(target_file)
            self.file_ops._display_file_info(file_info)
            
            # Show file preview
            self.console.print(f"\n[bold]File Content:[/bold]")
            self.file_ops.diff_manager.show_file_preview(target_file, content)
            
            self.console.print(f"[green]✓ File loaded: {target_file}[/green]")
            
        except Exception as e:
            self.console.print(f"[red]Error reading file: {e}[/red]")
    
    def _edit_files(self, file_paths: str) -> None:
        """Edit one or more files with AI assistance."""
        if self.read_only:
            self.console.print("[yellow]Edit is disabled in Q&A (read-only) mode[/yellow]")
            return

        if not file_paths:
            self.console.print("[red]Please specify one or more file paths[/red]")
            self.console.print("Usage: /edit <file1> [file2 ...]")
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

        edit_prompt = Prompt.ask("What changes would you like to make to these files?")
        if not edit_prompt:
            self.console.print("[yellow]Edit cancelled[/yellow]")
            return

        results = self.file_ops.review_files(
            targets,
            self.current_model,
            edit_prompt,
            auto_apply=False,
        )

        for path, success in results.items():
            if success:
                self.console.print(f"[green]✓ File edited successfully: {path}[/green]")
            else:
                self.console.print(f"[red]✗ Failed to edit file: {path}[/red]")
    
    def _show_workspace_info(self) -> None:
        """Show workspace information."""
        workspace_info = f"""
[bold]Workspace Path:[/bold] {self.workspace_path}
[bold]Accessible Files:[/bold] {len(self.accessible_files)}
[bold]Current Model:[/bold] {self.current_model}
[bold]Current File Context:[/bold] {self.current_file_context['name'] if self.current_file_context else 'None'}
        """.strip()
        
        panel = Panel(
            workspace_info,
            title="📊 Workspace Information",
            border_style="blue",
            padding=(1, 2)
        )
        
        self.console.print(panel)
    
    def _send_enhanced_message_with_context(self, user_input: str) -> Optional[str]:
        """Send message to API with full 64k context optimization.

        Args:
            user_input: User's message

        Returns:
            API response or None if error
        """
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

    def _send_enhanced_message(self, user_input: str) -> Optional[str]:
        """Send message to API with enhanced file context.
        
        Args:
            user_input: User's message
            
        Returns:
            API response or None if error
        """
        # Add user message to history
        self.messages.append({"role": "user", "content": user_input})
        
        # Build enhanced context with file information
        context_parts = []
        
        # Add workspace context
        context_parts.append(f"Workspace: {self.workspace_path}")
        context_parts.append(f"Accessible files: {len(self.accessible_files)}")
        
        # Add current file context if available (increased content size)
        if self.current_file_context:
            context_parts.append(f"Current file: {self.current_file_context['path']}")
            # Include more file content (increased from 2000 to 8000 characters)
            file_content = self.current_file_context['content']
            if len(file_content) > 8000:
                file_content = file_content[:8000] + "\n... (content truncated for context)"
            context_parts.append(f"File content:\n{file_content}")
        
        # Add accessible files list for reference (increased from 5 to 15 files)
        if self.accessible_files:
            files_list = "\n".join(sorted(self.accessible_files)[:15])  # Limit to first 15
            context_parts.append(f"Available files:\n{files_list}")
        
        # Create enhanced message
        enhanced_message = f"""
Context:
{chr(10).join(context_parts)}

User message: {user_input}

Please consider the workspace context and available files when responding. 
If the user asks about files, you can reference the accessible files list.
If they ask to read or modify a file, you can use the /read or /edit commands.
"""
        
        # Replace the last user message with enhanced version
        self.messages[-1] = {"role": "user", "content": enhanced_message}
        
        # Trim history if needed (less aggressive trimming)
        if len(self.messages) > self.max_history * 2:
            # Keep more messages for better context
            self.messages = self.messages[-self.max_history * 2:]
        
        # Show typing indicator
        with Status("[bold green]🤔 Thinking...[/bold green]", console=self.console):
            try:
                # First attempt with full context
                response = self.api_client.chat_completion(
                    messages=self.messages,
                    model=self.current_model,
                    temperature=0.7,
                    max_tokens=30000
                )
                
                # Validate response
                if not response or not response.choices or not response.choices[0].message:
                    self.console.print("[red]Error: Received empty response from API[/red]")
                    if self.messages:
                        self.messages.pop()
                    return None
                
                response_content = response.choices[0].message.content
                
                # Check if response content is empty
                if not response_content or not response_content.strip():
                    # Try fallback with simplified context
                    self.console.print("[yellow]Trying with simplified context...[/yellow]")
                    simplified_messages = [
                        {"role": "system", "content": "You are a helpful AI assistant. Answer the user's question based on the available context."},
                        {"role": "user", "content": user_input}
                    ]
                    
                    fallback_response = self.api_client.chat_completion(
                        messages=simplified_messages,
                        model=self.current_model,
                        temperature=0.7,
                        max_tokens=30000
                    )
                    
                    if fallback_response and fallback_response.choices and fallback_response.choices[0].message:
                        fallback_content = fallback_response.choices[0].message.content
                        if fallback_content and fallback_content.strip():
                            # Add assistant response to history
                            self.messages.append({"role": "assistant", "content": fallback_content})
                            return fallback_content
                    
                    self.console.print("[red]Error: Received empty response content from API[/red]")
                    if self.messages:
                        self.messages.pop()
                    return None
                
                # Add assistant response to history
                self.messages.append({"role": "assistant", "content": response_content})
                return response_content
                
            except Exception as e:
                self.console.print(f"[red]Error getting response: {e}[/red]")
                self.console.print("[yellow]This might be due to network issues, API limits, or context length. Try asking a shorter question or use /clear to reset the conversation.[/yellow]")
                # Remove the user message from history since it failed
                if self.messages:
                    self.messages.pop()
                return None
    
    def _display_enhanced_response(self, response: str) -> None:
        """Display enhanced response with better formatting."""
        # Try to detect if response contains code
        if self._contains_code(response):
            self._display_code_response(response)
        else:
            self._display_text_response(response)
    
    def _contains_code(self, text: str) -> bool:
        """Check if text contains code blocks."""
        return "```" in text or any(keyword in text.lower() for keyword in [
            "def ", "class ", "import ", "from ", "function ", "var ", "const ",
            "if __name__", "public class", "private ", "public ", "def main"
        ])
    
    def _display_code_response(self, response: str) -> None:
        """Display response that contains code."""
        # Split by code blocks
        parts = response.split("```")
        
        for i, part in enumerate(parts):
            if i % 2 == 0:  # Regular text
                if part.strip():
                    md = Markdown(part.strip())
                    self.console.print(md)
            else:  # Code block
                if part.strip():
                    # Extract language if specified
                    lines = part.strip().split('\n', 1)
                    if len(lines) > 1 and lines[0].strip():
                        language = lines[0].strip()
                        code = lines[1]
                    else:
                        language = "text"
                        code = part.strip()
                    
                    syntax = Syntax(
                        code,
                        language,
                        theme="monokai",
                        line_numbers=True,
                        word_wrap=True
                    )
                    
                    panel = Panel(
                        syntax,
                        title=f"💻 Code ({language})",
                        border_style="yellow",
                        padding=(1, 2)
                    )
                    
                    self.console.print(panel)
    
    def _display_text_response(self, response: str) -> None:
        """Display text-only response."""
        md = Markdown(response)
        self.console.print(md)
    
    def _select_initial_model(self) -> None:
        """Select initial model if none is set."""
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
    
    def _clear_file_context(self) -> None:
        """Clear the current file context to reduce memory usage."""
        self.current_file_context = None
        self.console.print("[green]File context cleared[/green]")
    
    def _show_enhanced_help(self) -> None:
        """Show enhanced help information."""
        help_text = """
[bold]🚀 Enhanced Groq CLI Agent Commands:[/bold]

[cyan]File Operations:[/cyan]
• /files - List all accessible files in workspace
• /scan - Rescan workspace for new files
• /read <file> - Read and analyze a specific file
• /edit <file1> [file2 ...] - Edit one or more files with AI assistance
• /clear-context - Clear current file context

[cyan]Chat & Model:[/cyan]
• /model - Change the AI model (interactive selection)
• /fast, /balanced, /powerful, /ultra - Quick model switches
• /next, /prev - Cycle through models
• /shortcuts - Show all quick model shortcuts
• /clear - Clear the current chat history
• /workspace - Show workspace information
• /context - Show 64k context optimization status

[cyan]Mode Switching:[/cyan]
• /agent - Switch to Agent mode (file modifications)
• /advanced - Switch to Advanced Agent mode (enhanced AI capabilities)
• /qna - Switch to Q&A mode (read-only analysis)

[cyan]General:[/cyan]
• /help - Show this help message
• /exit - Exit the chat session

[bold]💡 Enhanced Features:[/bold]
• Automatic file scanning on startup
• Full workspace context awareness
• Direct file reading and editing
• Beautiful UI with rich formatting
• File modification capabilities
• Mode switching within chat
• 64k context window optimization
• Persistent task state and operation history

[bold]Usage Tips:[/bold]
• I can see all files in your workspace automatically
• Just ask me to read, analyze, or modify any file
• Use /read <filename> to focus on a specific file
• I can suggest improvements and apply them directly
• Use /clear-context if responses become slow or unreliable
• Switch between modes anytime with /agent, /advanced, or /qna
        """
        
        panel = Panel(
            help_text,
            title="🚀 Enhanced Help",
            border_style="green",
            padding=(1, 2)
        )
        
        self.console.print(panel)

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
        
        # 4. WORKSPACE CONTEXT (medium priority)
        context_parts.append("=== WORKSPACE CONTEXT ===")
        context_parts.append(f"Workspace Path: {self.workspace_path}")
        context_parts.append(f"Accessible Files: {len(self.accessible_files)}")
        context_parts.append(f"Read Only Mode: {self.read_only}")
        
        # Add current file context if available
        if self.current_file_context:
            context_parts.append(f"Current File: {self.current_file_context.get('name', 'Unknown')}")
            context_parts.append(f"File Path: {self.current_file_context.get('path', 'Unknown')}")
        context_parts.append("=== END WORKSPACE CONTEXT ===\n")
        
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
            "=== WORKSPACE CONTEXT ===",
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
[bold]Read Only Mode:[/bold] {self.read_only}
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
