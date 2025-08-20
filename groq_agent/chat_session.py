"""Interactive chat session component for Groq CLI Agent."""

import sys
import os
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
from rich.prompt import Prompt
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text

from .config import ConfigurationManager
from .api_client import GroqAPIClient
from .model_selector import ModelSelector


class InteractiveChatSession:
    """Manages interactive chat sessions with the Groq API."""
    
    def __init__(self, config: ConfigurationManager, api_client: GroqAPIClient):
        """Initialize the chat session.
        
        Args:
            config: Configuration manager instance
            api_client: Groq API client instance
        """
        self.config = config
        self.api_client = api_client
        self.model_selector = ModelSelector(api_client)
        self.console = Console()
        self.prompt_style = Style.from_dict({
            'prompt': 'bold ansicyan',
            'toolbar': 'reverse ansimagenta'
        })
        
        # Chat state
        self.current_model = config.get_default_model()
        self.messages: List[Dict[str, str]] = []
        self.max_history = config.get_max_history()
        
        # Setup history file
        history_file = config.config_dir / "chat_history.txt"
        self.history = FileHistory(str(history_file))
        
        # Command completions
        self.command_completer = WordCompleter([
            '/help', '/model', '/exit', '/clear', '/history', '/save', '/load'
        ])
    
    def start(self) -> None:
        """Start the interactive chat session."""
        self._show_welcome()
        
        # Check if we need to select a model
        if not self.current_model:
            self._select_initial_model()
        
        # Main chat loop
        while True:
            try:
                # Get user input
                user_input = self._get_user_input()
                
                if not user_input.strip():
                    continue
                
                # Handle commands
                if user_input.startswith('/'):
                    if self._handle_command(user_input):
                        break
                    continue
                
                # Send message to API
                response = self._send_message(user_input)
                if response:
                    self._display_response(response)
                
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Use /exit to quit the chat session[/yellow]")
            except EOFError:
                break
            except Exception as e:
                self.console.print(f"[red]Error: {e}[/red]")
    
    def _show_welcome(self) -> None:
        """Display welcome message."""
        welcome_text = """
[bold blue]Welcome to Groq CLI Agent![/bold blue]

This is an interactive chat session powered by Groq's AI models.
You can start chatting immediately or use slash commands for additional features.

[bold]Available commands:[/bold]
• /help - Show this help message
• /model - Change the AI model
• /clear - Clear chat history
• /history - Show recent messages
• /exit - Exit the chat session

[bold]Current model:[/bold] {model}

Type your message and press Enter to start chatting!
        """.format(model=self.current_model or "Not set")
        
        panel = Panel(
            welcome_text,
            title="Groq CLI Agent",
            subtitle="GitHub: TM NABEEL @tmnabeel30 created",
            subtitle_align="right",
            border_style="blue",
            padding=(1, 2)
        )
        
        self.console.print(panel)
        self.console.print()
    
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
    
    def _get_user_input(self) -> str:
        """Get user input with command completion."""
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
    
    def _handle_command(self, command: str) -> bool:
        """Handle slash commands.
        
        Args:
            command: The command string
            
        Returns:
            True if should exit, False otherwise
        """
        parts = command.split(' ', 1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        if cmd == '/help':
            self._show_help()
        elif cmd == '/model':
            self._change_model()
        elif cmd == '/clear':
            self._clear_history()
        elif cmd == '/history':
            self._show_history()
        elif cmd == '/file':
            self._handle_file_command(args)
        elif cmd == '/exit':
            return True
        else:
            self.console.print(f"[red]Unknown command: {cmd}[/red]")
            self.console.print("Type /help for available commands")
        
        return False
    
    def _handle_file_command(self, args: str) -> None:
        """Handle file-related commands.
        
        Args:
            args: Command arguments
        """
        if not args:
            self.console.print("[red]Usage: /file <command> [args][/red]")
            self.console.print("Available file commands:")
            self.console.print("  /file load <path> - Load file content into context")
            self.console.print("  /file show - Show currently loaded file")
            self.console.print("  /file clear - Clear file context")
            return
        
        file_parts = args.split(' ', 1)
        file_cmd = file_parts[0].lower()
        file_args = file_parts[1] if len(file_parts) > 1 else ""
        
        if file_cmd == 'load':
            if not file_args:
                self.console.print("[red]Please specify a file path[/red]")
                return
            self._load_file_context(file_args)
        elif file_cmd == 'show':
            self._show_file_context()
        elif file_cmd == 'clear':
            self._clear_file_context()
        else:
            self.console.print(f"[red]Unknown file command: {file_cmd}[/red]")
    
    def _load_file_context(self, file_path: str) -> None:
        """Load a file into the chat context.
        
        Args:
            file_path: Path to the file to load
        """
        try:
            if not os.path.exists(file_path):
                self.console.print(f"[red]File not found: {file_path}[/red]")
                return
            
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Store file context
            self.current_file = {
                'path': file_path,
                'content': content,
                'name': os.path.basename(file_path)
            }
            
            # Show file preview
            self.console.print(f"[green]Loaded file: {file_path}[/green]")
            self.console.print(f"[dim]Size: {len(content)} characters, Lines: {len(content.splitlines())}[/dim]")
            
            # Show a preview of the file
            preview_lines = content.splitlines()[:10]
            preview = '\n'.join(preview_lines)
            if len(content.splitlines()) > 10:
                preview += f"\n... ({len(content.splitlines()) - 10} more lines)"
            
            self.console.print(f"\n[bold]File Preview:[/bold]")
            self.console.print(f"[dim]{preview}[/dim]")
            
            # Add system message about the loaded file
            system_msg = f"""A file has been loaded into the conversation context:
File: {file_path}
Content length: {len(content)} characters
Lines: {len(content.splitlines())}

The user can now ask questions about this file or request modifications to it."""
            
            self.messages.append({"role": "system", "content": system_msg})
            
        except Exception as e:
            self.console.print(f"[red]Error loading file: {e}[/red]")
    
    def _show_file_context(self) -> None:
        """Show information about the currently loaded file."""
        if not hasattr(self, 'current_file') or not self.current_file:
            self.console.print("[yellow]No file currently loaded[/yellow]")
            return
        
        file_info = self.current_file
        self.console.print(f"[bold]Currently loaded file:[/bold] {file_info['path']}")
        self.console.print(f"[dim]Size: {len(file_info['content'])} characters[/dim]")
        self.console.print(f"[dim]Lines: {len(file_info['content'].splitlines())}[/dim]")
    
    def _clear_file_context(self) -> None:
        """Clear the current file context."""
        if hasattr(self, 'current_file'):
            self.current_file = None
        self.console.print("[green]File context cleared[/green]")
    
    def _show_help(self) -> None:
        """Show help information."""
        help_text = """
[bold]Available Commands:[/bold]

[cyan]/help[/cyan] - Show this help message
[cyan]/model[/cyan] - Change the AI model (interactive selection)
[cyan]/clear[/cyan] - Clear the current chat history
[cyan]/history[/cyan] - Show recent message history
[cyan]/file[/cyan] - File context commands (see /file for details)
[cyan]/exit[/cyan] - Exit the chat session

[bold]File Commands:[/bold]
[cyan]/file load <path>[/cyan] - Load a file into chat context
[cyan]/file show[/cyan] - Show currently loaded file info
[cyan]/file clear[/cyan] - Clear file context

[bold]Usage Tips:[/bold]
• Just type your message and press Enter to chat
• Use Ctrl+C to cancel a request in progress
• Load a file with /file load to discuss it with the AI
• Commands are case-insensitive
        """
        
        panel = Panel(
            help_text,
            title="Help",
            border_style="green",
            padding=(1, 2)
        )
        
        self.console.print(panel)
    
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
        if Prompt.ask("Are you sure you want to clear the chat history?", default=False):
            self.messages.clear()
            self.console.print("[green]Chat history cleared[/green]")
        else:
            self.console.print("[yellow]Operation cancelled[/yellow]")
    
    def _show_history(self) -> None:
        """Show recent chat history."""
        if not self.messages:
            self.console.print("[yellow]No chat history[/yellow]")
            return
        
        self.console.print(f"\n[bold]Recent Messages ({len(self.messages)}):[/bold]")
        
        for i, message in enumerate(self.messages[-10:], 1):  # Show last 10 messages
            role = message["role"]
            content = message["content"][:100] + "..." if len(message["content"]) > 100 else message["content"]
            
            if role == "user":
                self.console.print(f"[cyan]{i}. You:[/cyan] {content}")
            else:
                self.console.print(f"[green]{i}. Assistant:[/green] {content}")
    
    def _send_message(self, user_input: str) -> Optional[str]:
        """Send message to API and get response.
        
        Args:
            user_input: User's message
            
        Returns:
            API response or None if error
        """
        # Add user message to history
        self.messages.append({"role": "user", "content": user_input})
        
        # Add file context if available
        if hasattr(self, 'current_file') and self.current_file:
            file_context = f"""
Current file context:
File: {self.current_file['path']}
Content:
{self.current_file['content']}

User message: {user_input}

Please consider the file content when responding to the user's message.
"""
            # Replace the last user message with context-enhanced version
            self.messages[-1] = {"role": "user", "content": file_context}
        
        # Trim history if needed
        if len(self.messages) > self.max_history * 2:  # *2 because each exchange is 2 messages
            self.messages = self.messages[-self.max_history * 2:]
        
        # Show typing indicator
        with Live(Spinner("dots", text="Thinking..."), console=self.console):
            try:
                response = self.api_client.chat_completion(
                    messages=self.messages,
                    model=self.current_model,
                    temperature=0.7
                )
                
                response_content = response.choices[0].message.content
                
                # Add assistant response to history
                self.messages.append({"role": "assistant", "content": response_content})
                
                return response_content
                
            except Exception as e:
                self.console.print(f"[red]Error getting response: {e}[/red]")
                # Remove the user message from history since it failed
                if self.messages:
                    self.messages.pop()
                return None
    
    def _display_response(self, response: str) -> None:
        """Display the API response.
        
        Args:
            response: Response content to display
        """
        # Try to detect if response contains code
        if self._contains_code(response):
            self._display_code_response(response)
        else:
            self._display_text_response(response)
    
    def _contains_code(self, text: str) -> bool:
        """Check if text contains code blocks.
        
        Args:
            text: Text to check
            
        Returns:
            True if contains code blocks
        """
        return "```" in text or any(keyword in text.lower() for keyword in [
            "def ", "class ", "import ", "from ", "function ", "var ", "const ",
            "if __name__", "public class", "private ", "public ", "def main"
        ])
    
    def _display_code_response(self, response: str) -> None:
        """Display response that contains code.
        
        Args:
            response: Response containing code
        """
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
                        title=f"Code ({language})",
                        border_style="yellow",
                        padding=(1, 2)
                    )
                    
                    self.console.print(panel)
    
    def _display_text_response(self, response: str) -> None:
        """Display text-only response.
        
        Args:
            response: Text response to display
        """
        md = Markdown(response)
        self.console.print(md)
    
    def get_messages(self) -> List[Dict[str, str]]:
        """Get current chat messages.
        
        Returns:
            List of message dictionaries
        """
        return self.messages.copy()
    
    def add_message(self, role: str, content: str) -> None:
        """Add a message to the chat history.
        
        Args:
            role: Message role ('user' or 'assistant')
            content: Message content
        """
        self.messages.append({"role": role, "content": content})
        
        # Trim history if needed
        if len(self.messages) > self.max_history * 2:
            self.messages = self.messages[-self.max_history * 2:]
