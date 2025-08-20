"""Enhanced interactive chat session with automatic file access and better UI."""

import sys
import os
import glob
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


class EnhancedChatSession:
    """Enhanced chat session with automatic file access and better UI.

    Supports an optional read-only mode to prevent file modifications.
    """
    
    def __init__(self, config: ConfigurationManager, api_client: GroqAPIClient, read_only: bool = False):
        """Initialize the enhanced chat session.
        
        Args:
            config: Configuration manager instance
            api_client: Groq API client instance
        """
        self.config = config
        self.api_client = api_client
        self.model_selector = ModelSelector(api_client)
        self.file_ops = FileOperations(api_client)
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
        
        # Setup history file
        history_file = config.config_dir / "chat_history.txt"
        self.history = FileHistory(str(history_file))
        
        # Enhanced command completions
        base_commands = ['/help', '/model', '/exit', '/clear', '/history', '/files', '/scan', '/read', '/workspace', '/clear-context']
        if not self.read_only:
            base_commands.append('/edit')
        self.command_completer = WordCompleter(base_commands)
        
        # Auto-scan workspace on startup
        self._scan_workspace()
    
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
                
                # Send message to API with file context
                response = self._send_enhanced_message(user_input)
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
            ("/files", "List accessible files"),
            ("/scan", "Rescan workspace for files"),
            ("/read <file>", "Read and analyze a file"),
            ("/clear-context", "Clear file context"),
            ("/workspace", "Show workspace information"),
            ("/clear", "Clear chat history"),
            ("/exit", "Exit the chat session")
        ]
        if not self.read_only:
            commands.insert(5, ("/edit <file>", "Edit a file with AI assistance"))
        
        for cmd, desc in commands:
            commands_table.add_row(cmd, desc)
        
        commands_panel = Panel(
            commands_table,
            title="⚡ Available Commands",
            border_style="yellow",
            padding=(1, 2)
        )
        
        # Tips
        tips = """
[bold]💡 Tips:[/bold]
• I can automatically see all files in your workspace
• Just ask me to read, analyze, or modify any file
• Use /read <filename> to focus on a specific file
• I can suggest improvements and apply them directly
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
                self._edit_file(args)
        elif cmd == '/clear-context':
            self._clear_file_context()
        elif cmd == '/agent' or (cmd == '/mode' and args.strip().lower() == 'agent'):
            # Switch to Agent mode
            self._switch_to_mode = 'agent'
            return True
        elif cmd == '/qna' or (cmd == '/mode' and args.strip().lower() == 'qna'):
            self.console.print("[yellow]Already in Q&A mode[/yellow]")
        elif cmd == '/workspace':
            self._show_workspace_info()
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
    
    def _edit_file(self, file_path: str) -> None:
        """Edit a file with AI assistance."""
        if self.read_only:
            self.console.print("[yellow]Edit is disabled in Q&A (read-only) mode[/yellow]")
            return
        if not file_path:
            self.console.print("[red]Please specify a file path[/red]")
            self.console.print("Usage: /edit <file_path>")
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
        
        # Get edit prompt from user
        edit_prompt = Prompt.ask("What changes would you like to make to this file?")
        
        if not edit_prompt:
            self.console.print("[yellow]Edit cancelled[/yellow]")
            return
        
        # Perform the edit
        success = self.file_ops.review_file(
            target_file, 
            self.current_model, 
            edit_prompt, 
            auto_apply=False
        )
        
        if success:
            self.console.print(f"[green]✓ File edited successfully: {target_file}[/green]")
        else:
            self.console.print(f"[red]✗ Failed to edit file: {target_file}[/red]")
    
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
                    max_tokens=4000
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
                        max_tokens=4000
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
• /edit <file> - Edit a file with AI assistance
• /clear-context - Clear current file context

[cyan]Chat & Model:[/cyan]
• /model - Change the AI model (interactive selection)
• /clear - Clear the current chat history
• /workspace - Show workspace information

[cyan]General:[/cyan]
• /help - Show this help message
• /exit - Exit the chat session

[bold]💡 Enhanced Features:[/bold]
• Automatic file scanning on startup
• Full workspace context awareness
• Direct file reading and editing
• Beautiful UI with rich formatting
• File modification capabilities

[bold]Usage Tips:[/bold]
• I can see all files in your workspace automatically
• Just ask me to read, analyze, or modify any file
• Use /read <filename> to focus on a specific file
• I can suggest improvements and apply them directly
• Use /clear-context if responses become slow or unreliable
        """
        
        panel = Panel(
            help_text,
            title="🚀 Enhanced Help",
            border_style="green",
            padding=(1, 2)
        )
        
        self.console.print(panel)
