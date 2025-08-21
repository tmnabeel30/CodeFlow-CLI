"""Interactive chat session component for Groq CLI Agent."""

import sys
import os
import time
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
        
        # Context Optimization - Full 60k context utilization
        self.operation_history: List[Dict[str, Any]] = []
        self.task_context: Dict[str, Any] = {}
        self.session_state: Dict[str, Any] = {}
        self.context_buffer: List[Dict[str, Any]] = []
        self.max_context_tokens = 60000  # Full context window
        self.current_context_size = 0
        self.context_optimization_enabled = True
        
        # Setup history file
        history_file = config.config_dir / "chat_history.txt"
        self.history = FileHistory(str(history_file))
        
        # Command completions
        self.command_completer = WordCompleter([
            '/help', '/model', '/exit', '/clear', '/history', '/save', '/load', '/context'
        ])
        
        # Initialize context optimization
        self._initialize_context_optimization()
    
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
                
                # Update task context for persistent state
                self._update_task_context(user_input)
                
                # Send message to API with context optimization
                response = self._send_message_with_context(user_input)
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
        elif cmd == '/context':
            self._show_context_status()  # Show context optimization status
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
[cyan]/context[/cyan] - Show 60k context optimization status
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
    
    def _send_message_with_context(self, user_input: str) -> Optional[str]:
        """Send message to API with full 60k context optimization.
        
        Args:
            user_input: User's message
            
        Returns:
            API response or None if error
        """
        try:
            # Build smart context using full 60k context window
            smart_context = self._build_smart_context(user_input)
            
            # Optimize context for 60k token limit
            optimized_context = self._optimize_context_for_60k(smart_context)
            
            # Add to operation history
            self._add_to_operation_history({
                'type': 'user_request',
                'description': user_input,
                'context_size': len(optimized_context) // 4,
                'context_utilization': self.session_state['context_utilization']
            })
            
            # Add user message to history with optimized context
            self.messages.append({"role": "user", "content": optimized_context})
            
            # Track model usage
            self.session_state['models_used'].add(self.current_model)
            
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
            
            # Show typing indicator with context optimization
            with Live(Spinner("dots", text="🤖 Processing with 60k context optimization..."), console=self.console):
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
                    
                    # Add assistant response to history
                    self.messages.append({"role": "assistant", "content": response_content})
                    
                    # Track successful response in context
                    self._add_to_operation_history({
                        'type': 'ai_response',
                        'description': f"Generated response for: {user_input[:50]}...",
                        'response_length': len(response_content)
                    })
                    
                    return response_content
                    
                except Exception as e:
                    self.console.print(f"[red]Error getting response: {e}[/red]")
                    # Remove the user message from history since it failed
                    if self.messages:
                        self.messages.pop()
                    return None
                    
        except Exception as e:
            return f"❌ Error processing request with context: {str(e)}"

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

    # ============================================================================
    # CONTEXT OPTIMIZATION METHODS - Full 60k Context Window Utilization
    # ============================================================================

    def _initialize_context_optimization(self) -> None:
        """Initialize context optimization for full 60k context window usage."""
        self.console.print("[cyan]🔧 Initializing Context Optimization (60k tokens)...[/cyan]")
        
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
        """Build smart context using full 60k context window effectively."""
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
        
        # 4. CHAT CONTEXT (medium priority)
        context_parts.append("=== CHAT CONTEXT ===")
        context_parts.append(f"Current Model: {self.current_model}")
        context_parts.append(f"Message History: {len(self.messages)} messages")
        context_parts.append(f"Max History: {self.max_history}")
        
        # Add current file context if available
        if hasattr(self, 'current_file') and self.current_file:
            context_parts.append(f"Current File: {self.current_file.get('name', 'Unknown')}")
            context_parts.append(f"File Path: {self.current_file.get('path', 'Unknown')}")
        context_parts.append("=== END CHAT CONTEXT ===\n")
        
        # 5. SESSION STATE (low priority)
        context_parts.append("=== SESSION STATE ===")
        context_parts.append(f"Total Operations: {self.session_state['total_operations']}")
        context_parts.append(f"Files Accessed: {len(self.session_state['files_accessed'])}")
        context_parts.append(f"Context Utilization: {self.session_state['context_utilization']:.1f}%")
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

    def _optimize_context_for_60k(self, context: str) -> str:
        """Optimize context to fit within 60k token limit while preserving important information."""
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
            "=== CHAT CONTEXT ===",
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
[bold cyan]📊 Context Summary (60k Token Optimization)[/bold cyan]

[bold]Current Task:[/bold] {self.task_context.get('current_task', 'None')}
[bold]Session ID:[/bold] {self.task_context.get('session_id', 'Unknown')}
[bold]Total Operations:[/bold] {self.session_state['total_operations']}
[bold]Context Utilization:[/bold] {self.session_state['context_utilization']:.1f}%
[bold]Files Modified:[/bold] {len(self.task_context.get('files_modified', []))}
[bold]Recent Operations:[/bold] {len(self.operation_history[-5:])} in last 5
[bold]Current Model:[/bold] {self.current_model}
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
