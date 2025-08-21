"""Main CLI entry point for Groq CLI Agent."""

import sys
import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from typing import Optional

from .config import ConfigurationManager
from .api_client import GroqAPIClient
from .chat_session import InteractiveChatSession
from .enhanced_chat import EnhancedChatSession
from .intelligent_agent import IntelligentAgent
from .model_selector import ModelSelector
from .file_operations import FileOperations


@click.group(invoke_without_command=True)
@click.option('--model', '-m', help='AI model to use')
@click.option('--select-model', is_flag=True, help='Interactively select a model')
@click.option('--api-key', help='Groq API key')
@click.option('--config-dir', help='Configuration directory')
@click.option('--version', is_flag=True, help='Show version information')
@click.pass_context
def main(ctx, model: Optional, select_model: bool, api_key: Optional, 
         config_dir: Optional, version: bool):
    """Groq CLI Agent - Interactive AI assistant powered by Groq."""
    
    if version:
        from . import __version__
        console = Console()
        console.print(f"Groq CLI Agent v{__version__} — GitHub: TM NABEEL @tmnabeel30 created")
        return
    
    # Initialize configuration
    config = ConfigurationManager(config_dir)
    
    # Set API key if provided
    if api_key:
        config.set_api_key(api_key)
    
    # Initialize API client
    try:
        api_client = GroqAPIClient(config)
    except ValueError as e:
        console = Console()
        console.print(f"Configuration Error: {e}")
        console.print("\nPlease set your API key using one of these methods:")
        console.print("1. Set GROQ_API_KEY environment variable")
        console.print("2. Use --api-key option")
        console.print("3. Configure in ~/.groq/config.yaml")
        sys.exit(1)
    
    # Store context objects
    ctx.obj = {
        'config': config,
        'api_client': api_client
    }
    
    # Handle model selection
    if select_model:
        model_selector = ModelSelector(api_client)
        selected_model = model_selector.select_model(config.get_default_model())
        if selected_model:
            config.set_default_model(selected_model)
            console = Console()
            console.print(f"Default model set to: {selected_model} [dim](GitHub: TM NABEEL @tmnabeel30 created)[/dim]")
        return
    
    # Set model if provided
    if model:
        config.set_default_model(model)
    
    # If no subcommand is provided, start interactive chat (default behavior)
    if ctx.invoked_subcommand is None:
        start_interactive_chat(config, api_client)


@main.command()
@click.option('--model', '-m', help='AI model to use')
@click.option('--temperature', '-t', type=float, default=0.7, help='Sampling temperature')
@click.option('--max-tokens', type=int, help='Maximum tokens to generate')
@click.argument('prompt', required=False)
@click.pass_context
def chat(ctx, model: Optional, temperature: float, max_tokens: Optional, prompt: Optional):
    """Start an interactive chat session or send a single message."""
    
    config = ctx.obj['config']
    api_client = ctx.obj['api_client']
    
    # Use provided model or default
    current_model = model or config.get_default_model()
    
    if prompt:
        # Single message mode
        send_single_message(api_client, current_model, prompt, temperature, max_tokens)
    else:
        # Interactive chat mode
        start_interactive_chat(config, api_client, current_model)


@main.command()
@click.option('--model', '-m', help='AI model to use')
@click.option('--type', '-t', 
              type=click.Choice(['comprehensive', 'security', 'performance', 'general']),
              default='comprehensive',
              help='Type of analysis to perform')
@click.argument('file_path', type=click.Path(exists=True))
@click.pass_context
def analyze(ctx, model: Optional, type: str, file_path: str):
    """Analyze a file and provide insights without modifying it."""
    
    config = ctx.obj['config']
    api_client = ctx.obj['api_client']
    
    # Use provided model or default
    current_model = model or config.get_default_model()
    
    file_ops = FileOperations(api_client)
    success = file_ops.analyze_file(file_path, current_model, type)
    
    if not success:
        sys.exit(1)


@main.command()
@click.option('--model', '-m', help='AI model to use')
@click.option('--prompt', '-p', help='Custom review prompt')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation and apply changes')
@click.option('--improvement', '-i', 
              type=click.Choice(['performance', 'security', 'readability', 'documentation', 'testing', 'refactoring']),
              help='Type of improvement to suggest')
@click.argument('file_path', type=click.Path(exists=True))
@click.pass_context
def review(ctx, model: Optional, prompt: Optional, yes: bool, improvement: Optional, file_path: str):
    """Review a file and suggest improvements."""
    
    config = ctx.obj['config']
    api_client = ctx.obj['api_client']
    
    # Use provided model or default
    current_model = model or config.get_default_model()
    
    file_ops = FileOperations(api_client)
    
    if improvement:
        success = file_ops.suggest_improvements(file_path, current_model, improvement, yes)
    else:
        success = file_ops.review_file(file_path, current_model, prompt, yes)
    
    if not success:
        sys.exit(1)


@main.command()
@click.option('--model', '-m', help='AI model to use')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation')
@click.argument('file_paths', nargs=-1, type=click.Path(exists=True))
@click.pass_context
def batch(ctx, model: Optional, yes: bool, file_paths):
    """Review multiple files in batch."""
    
    if not file_paths:
        console = Console()
        console.print("No files specified [dim](GitHub: TM NABEEL @tmnabeel30 created)[/dim]")
        console.print("Usage: groq-agent batch file1.py file2.py ...")
        sys.exit(1)
    
    config = ctx.obj['config']
    api_client = ctx.obj['api_client']
    
    # Use provided model or default
    current_model = model or config.get_default_model()
    
    file_ops = FileOperations(api_client)
    results = file_ops.batch_review(list(file_paths), current_model, auto_apply=yes)
    
    # Exit with error if any files failed
    if not all(results.values()):
        sys.exit(1)


@main.command()
@click.option('--model', '-m', help='AI model to use')
@click.option('--type', '-t', help='File type hint')
@click.argument('file_path', type=click.Path())
@click.argument('prompt')
@click.pass_context
def create(ctx, model: Optional, type: Optional, file_path: str, prompt: str):
    """Create a new file based on a prompt."""
    
    config = ctx.obj['config']
    api_client = ctx.obj['api_client']
    
    # Use provided model or default
    current_model = model or config.get_default_model()
    
    file_ops = FileOperations(api_client)
    success = file_ops.create_file_from_prompt(file_path, current_model, prompt, type)
    
    if not success:
        sys.exit(1)


@main.command()
@click.pass_context
def models(ctx):
    """List available models."""
    
    api_client = ctx.obj['api_client']
    model_selector = ModelSelector(api_client)
    model_selector.list_models()


@main.command()
@click.argument('model_id')
@click.pass_context
def model_info(ctx, model_id: str):
    """Show detailed information about a specific model."""
    
    api_client = ctx.obj['api_client']
    model_selector = ModelSelector(api_client)
    model_selector.display_model_info(model_id)


@main.command()
@click.option('--api-key', prompt=True, hide_input=True, help='Groq API key')
@click.pass_context
def configure(ctx, api_key: str):
    """Configure the CLI (API key, default model, etc.)."""
    
    config = ctx.obj['config']
    console = Console()
    
    # Set API key
    config.set_api_key(api_key)
    console.print("API key configured successfully [dim](GitHub: TM NABEEL @tmnabeel30 created)[/dim]")
    
    # Test API key
    api_client = ctx.obj['api_client']
    if api_client.validate_api_key():
        console.print("API key is valid [dim](GitHub: TM NABEEL @tmnabeel30 created)[/dim]")
        
        # Offer to set default model
        if Prompt.ask("Would you like to set a default model?", default=True):
            model_selector = ModelSelector(api_client)
            selected_model = model_selector.select_model()
            if selected_model:
                config.set_default_model(selected_model)
                console.print(f"Default model set to: {selected_model} [dim](GitHub: TM NABEEL @tmnabeel30 created)[/dim]")
    else:
        console.print("API key validation failed [dim](GitHub: TM NABEEL @tmnabeel30 created)[/dim]")
        sys.exit(1)


def start_interactive_chat(config: ConfigurationManager, api_client: GroqAPIClient, 
                          model: Optional = None) -> None:
    """Start an interactive chat session."""
    
    # Set model if provided
    if model:
        config.set_default_model(model)
    
    # Always show CODEFLOW banner
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.text import Text
        console = Console()
        # Big "CODEFLOW" banner (clear C and D, E not duplicated)
        logo = Text("""
 ██████╗  ██████╗ ██████╗ ███████╗███████╗██╗      ██████╗ ██╗      ██████╗ ██╗    ██╗
██╔════╝ ██╔═══██╗██╔══██╗██╔════╝██╔════╝██║     ██╔═══██╗██║     ██╔═══██╗██║    ██║
██║      ██║   ██║██████╔╝█████╗  █████╗  ██║     ██║   ██║██║     ██║   ██║██║ █╗ ██║
██║      ██║   ██║██╔══██╗██╔══╝  ██╔══╝  ██║     ██║   ██║██║     ██║   ██║██║███╗██║
╚██████╗ ╚██████╔╝██║  ██║███████╗███████╗███████╗╚██████╔╝███████╗╚██████╔╝╚███╔███╔╝
 ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝ ╚═════╝ ╚══════╝ ╚═════╝  ╚══╝╚══╝ 
        """.rstrip(), style="bold magenta")
        subtitle = "GitHub: TM NABEEL @tmnabeel30 created"
        panel = Panel(logo, title="CODEFLOW", subtitle=subtitle, subtitle_align="right", border_style="magenta", padding=(1,2))
        console.print(panel)
    except Exception:
        pass
    
    # Choose mode: Q&A (read-only), Agent (modify files), or Agentic (advanced)
    try:
        from rich.prompt import Prompt
        console.print("\n[bold cyan]Select your mode:[/bold cyan]")
        console.print("1. [green]Q&A Mode[/green] - Ask questions about your codebase (read-only)")
        console.print("2. [blue]Agent Mode[/blue] - AI agent that can modify files")
        console.print("3. [magenta]Advanced Agent[/magenta] - Enhanced AI with smart tools and analysis")
        
        choice = Prompt.ask(
            "\nSelect mode",
            choices=["1", "2", "3"],
            default="1"
        )
        
        # Map choice to mode
        if choice == "1":
            mode = "qna"
        elif choice == "2":
            mode = "agent"
        elif choice == "3":
            mode = "agentic"
        else:
            mode = "qna"
    except Exception:
        mode = "qna"

    while True:
        if mode == "qna":
            # Start enhanced chat in read-only mode
            session = EnhancedChatSession(config, api_client, read_only=True)
            switch = session.start()
            if switch == 'agent':
                mode = 'agent'
                continue
            elif switch == 'agentic':
                mode = 'agentic'
                continue
            break
        elif mode == "agent":
            # Start intelligent agent mode (can modify files)
            agent = IntelligentAgent(config, api_client)
            switch = agent.start_interactive_mode()
            if switch == 'qna':
                mode = 'qna'
                continue
            elif switch == 'agentic':
                mode = 'agentic'
                continue
            break
        elif mode == "agentic":
            # Start advanced agent mode
            try:
                from .agentic_chat import AgenticChat
                agentic_chat = AgenticChat(config, api_client)
                switch = agentic_chat.start()
                if switch == 'qna':
                    mode = 'qna'
                    continue
                elif switch == 'agent':
                    mode = 'agent'
                    continue
                break
            except ImportError:
                console.print("[red]Advanced Agent mode not available. Falling back to Agent mode.[/red]")
                mode = 'agent'
                continue
        else:
            mode = "qna"
            continue


def send_single_message(api_client: GroqAPIClient, model: str, prompt: str, 
                       temperature: float, max_tokens: Optional) -> None:
    """Send a single message and display the response."""
    
    console = Console()
    
    try:
        # Show typing indicator
        with console.status("Generating response..."):
            response = api_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )
        
        # Display response
        response_content = response.choices[0].message.content
        console.print("\nResponse:")
        console.print(response_content)
        
    except Exception as e:
        console.print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()