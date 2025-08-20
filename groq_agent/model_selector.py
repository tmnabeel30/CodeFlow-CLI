"""Interactive model selection component for Groq CLI Agent."""

from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.shortcuts import radiolist_dialog
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
    
    def select_model(self, current_model: Optional[str] = None) -> Optional[str]:
        """Present interactive model selection menu.
        
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
            
            # Create selection options for radiolist_dialog
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
            
            # Show interactive selection dialog
            selected = radiolist_dialog(
                title="Select a Model",
                text="Choose a model from the list below:",
                values=options,
                default=current_index
            ).run()
            
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


