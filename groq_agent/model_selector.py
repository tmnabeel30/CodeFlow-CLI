"""Interactive model selection component for Groq CLI Agent."""

from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.shortcuts import radiolist_dialog
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout, HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.containers import FloatContainer, Float
from prompt_toolkit.widgets import RadioList
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from typing import List, Dict, Any, Optional
from .api_client import GroqAPIClient


class ModelSelector:
    """Interactive model selection component."""
    
    def __init__(self, api_client: GroqAPIClient):
        """Initialize the model selector.
        
        Args:
            api_client: Groq API client instance
        """
        self.api_client = api_client
        self.console = Console()
        
        # Quick model shortcuts for easy switching
        self.quick_models = {
            'fast': 'llama-3.1-8B',
            'balanced': 'llama-2-70B', 
            'powerful': 'llama-3.1-70B',
            'ultra': 'llama-3.1-405B',
            'mixtral': 'mixtral-8x7b-32768',
            'gemma': 'gemma-7b-it',
            'compound': 'compound-beta',
            'compound-mini': 'compound-beta-mini'
        }
    
    def select_model(self, current_model: Optional[str] = None) -> Optional[str]:
        """Present interactive model selection menu with arrow key navigation.
        
        Args:
            current_model: Currently selected model (if any)
            
        Returns:
            Selected model ID or None if cancelled
        """
        try:
            models = self.api_client.get_available_models()
            if not models:
                self.console.print("[red]Error: No models available[/red]")
                return None
            
            # Create selection options for RadioList
            options = []
            current_index = 0
            
            for i, model in enumerate(models):
                model_id = model["id"]
                description = model["description"]
                capabilities = ", ".join(model["capabilities"])
                
                # Mark current model
                if current_model and model_id == current_model:
                    current_index = i
                    display_name = f"{model_id} (current)"
                else:
                    display_name = model_id
                
                options.append((
                    model_id,
                    f"{display_name} - {description}\n  Capabilities: {capabilities}"
                ))
            
            # Create RadioList widget with proper navigation
            radio_list = RadioList(options)
            radio_list.current_value = current_index
            
            # Create key bindings
            kb = KeyBindings()
            
            @kb.add('up')
            def _(event):
                """Move selection up."""
                if radio_list.current_value > 0:
                    radio_list.current_value -= 1
            
            @kb.add('down')
            def _(event):
                """Move selection down."""
                if radio_list.current_value < len(options) - 1:
                    radio_list.current_value += 1
            
            @kb.add('enter')
            def _(event):
                """Confirm selection."""
                event.app.exit(result=options[radio_list.current_value][0])
            
            @kb.add('escape')
            def _(event):
                """Cancel selection."""
                event.app.exit(result=None)
            
            @kb.add('tab')
            def _(event):
                """Move to next item (same as down)."""
                if radio_list.current_value < len(options) - 1:
                    radio_list.current_value += 1
            
            @kb.add('s-tab')
            def _(event):
                """Move to previous item (same as up)."""
                if radio_list.current_value > 0:
                    radio_list.current_value -= 1
            
            # Create layout
            title = FormattedTextControl("Select a Model (Use ↑↓ arrows, Tab, Enter to confirm, Esc to cancel)")
            model_list = Window(radio_list, wrap_lines=True)
            
            layout = Layout(
                HSplit([
                    Window(title, height=1),
                    model_list
                ])
            )
            
            # Show interactive selection
            from prompt_toolkit import Application
            app = Application(
                layout=layout,
                key_bindings=kb,
                full_screen=False,
                mouse_support=True
            )
            
            selected = app.run()
            
            if selected:
                self.console.print(f"[green]Selected model: {selected}[/green]")
                return selected
            else:
                self.console.print("[yellow]Model selection cancelled[/yellow]")
                return None
                
        except Exception as e:
            self.console.print(f"[red]Error in model selection: {e}[/red]")
            return self._fallback_selection(models if 'models' in locals() else [])
    
    def _fallback_selection(self, models: List[Dict[str, Any]]) -> Optional[str]:
        """Fallback to simple text-based selection.
        
        Args:
            models: List of available models
            
        Returns:
            Selected model ID or None if cancelled
        """
        if not models:
            return None
        
        self.console.print("\n[bold]Available models:[/bold]")
        
        # Create a table for better display
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim")
        table.add_column("Model ID")
        table.add_column("Description")
        table.add_column("Capabilities")
        
        for i, model in enumerate(models, 1):
            capabilities = ", ".join(model["capabilities"])
            table.add_row(
                str(i),
                model["id"],
                model["description"],
                capabilities
            )
        
        self.console.print(table)
        
        # Simple number-based selection
        while True:
            try:
                choice = prompt(
                    f"\nEnter model number (1-{len(models)}) or 'q' to quit: ",
                    completer=WordCompleter([str(i) for i in range(1, len(models) + 1)] + ['q'])
                )
                
                if choice.lower() == 'q':
                    return None
                
                choice_num = int(choice)
                if 1 <= choice_num <= len(models):
                    selected_model = models[choice_num - 1]["id"]
                    self.console.print(f"[green]Selected model: {selected_model}[/green]")
                    return selected_model
                else:
                    self.console.print("[red]Invalid selection. Please try again.[/red]")
                    
            except ValueError:
                self.console.print("[red]Please enter a valid number.[/red]")
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Selection cancelled[/yellow]")
                return None
    
    def display_model_info(self, model_id: str) -> None:
        """Display detailed information about a specific model.
        
        Args:
            model_id: Model identifier
        """
        try:
            models = self.api_client.get_available_models()
            model_info = next((m for m in models if m["id"] == model_id), None)
            
            if not model_info:
                self.console.print(f"[red]Model '{model_id}' not found[/red]")
                return
            
            # Create a detailed panel
            content = f"""
[bold]Model ID:[/bold] {model_info['id']}
[bold]Description:[/bold] {model_info['description']}
[bold]Capabilities:[/bold] {', '.join(model_info['capabilities'])}
            """.strip()
            
            panel = Panel(
                content,
                title="Model Information",
                border_style="blue"
            )
            
            self.console.print(panel)
            
        except Exception as e:
            self.console.print(f"[red]Error displaying model info: {e}[/red]")
    
    def list_models(self) -> None:
        """Display all available models in a table format."""
        try:
            models = self.api_client.get_available_models()
            
            if not models:
                self.console.print("[red]No models available[/red]")
                return
            
            table = Table(
                title="Available Groq Models",
                show_header=True,
                header_style="bold magenta"
            )
            table.add_column("Model ID", style="cyan")
            table.add_column("Description")
            table.add_column("Capabilities")
            
            for model in models:
                capabilities = ", ".join(model["capabilities"])
                table.add_row(
                    model["id"],
                    model["description"],
                    capabilities
                )
            
            self.console.print(table)
            
        except Exception as e:
            self.console.print(f"[red]Error listing models: {e}[/red]")
    
    def quick_switch_model(self, shortcut: str) -> Optional[str]:
        """Quickly switch to a model using shortcuts.
        
        Args:
            shortcut: Quick model shortcut (e.g., 'fast', 'powerful', 'ultra')
            
        Returns:
            Model ID if valid shortcut, None otherwise
        """
        if shortcut.lower() in self.quick_models:
            model_id = self.quick_models[shortcut.lower()]
            self.console.print(f"[green]Quick switch to: {model_id}[/green]")
            return model_id
        else:
            self.console.print(f"[red]Unknown shortcut: {shortcut}[/red]")
            self.show_quick_shortcuts()
            return None
    
    def show_quick_shortcuts(self) -> None:
        """Display available quick model shortcuts."""
        table = Table(
            title="Quick Model Shortcuts",
            show_header=True,
            header_style="bold green"
        )
        table.add_column("Shortcut", style="cyan")
        table.add_column("Model", style="yellow")
        table.add_column("Description")
        
        shortcuts_info = {
            'fast': ('llama-3.1-8B', 'Fast 8B model for quick responses'),
            'balanced': ('llama-2-70B', 'Balanced 70B model for general use'),
            'powerful': ('llama-3.1-70B', 'Powerful 70B model for complex tasks'),
            'ultra': ('llama-3.1-405B', 'Ultra 405B model for maximum capability'),
            'mixtral': ('mixtral-8x7b-32768', 'Mixture of experts with 32K context'),
            'gemma': ('gemma-7b-it', 'Google Gemma 7B instruction-tuned'),
            'compound': ('compound-beta', 'Multi-tool high-capability model'),
            'compound-mini': ('compound-beta-mini', 'Single-tool low-latency model')
        }
        
        for shortcut, (model, desc) in shortcuts_info.items():
            table.add_row(shortcut, model, desc)
        
        self.console.print(table)
    
    def get_next_model(self, current_model: str) -> Optional[str]:
        """Get the next model in the list for easy cycling.
        
        Args:
            current_model: Current model ID
            
        Returns:
            Next model ID or None if not found
        """
        try:
            models = self.api_client.get_available_models()
            if not models:
                return None
            
            model_ids = [m["id"] for m in models]
            if current_model in model_ids:
                current_index = model_ids.index(current_model)
                next_index = (current_index + 1) % len(model_ids)
                return model_ids[next_index]
            else:
                return model_ids[0] if model_ids else None
                
        except Exception:
            return None
    
    def get_previous_model(self, current_model: str) -> Optional[str]:
        """Get the previous model in the list for easy cycling.
        
        Args:
            current_model: Current model ID
            
        Returns:
            Previous model ID or None if not found
        """
        try:
            models = self.api_client.get_available_models()
            if not models:
                return None
            
            model_ids = [m["id"] for m in models]
            if current_model in model_ids:
                current_index = model_ids.index(current_model)
                prev_index = (current_index - 1) % len(model_ids)
                return model_ids[prev_index]
            else:
                return model_ids[0] if model_ids else None
                
        except Exception:
            return None


