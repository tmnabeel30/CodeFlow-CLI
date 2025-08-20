"""Diff management component for reviewing and applying file changes."""

import difflib
import tempfile
import subprocess
import os
from pathlib import Path
from typing import Optional, Tuple, List
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.prompt import Prompt, Confirm
from rich.table import Table


class SuggestionDiffManager:
    """Manages diff review and file editing for AI-generated suggestions."""
    
    def __init__(self):
        """Initialize the diff manager."""
        self.console = Console()
    
    def show_diff(
        self,
        original_content: str,
        suggested_content: str,
        file_path: Optional[str] = None
    ) -> str:
        """Show diff between original and suggested content.
        
        Args:
            original_content: Original file content
            suggested_content: AI-suggested content
            file_path: Path to the file being modified (for display purposes)
            
        Returns:
            User's choice: 'accept', 'edit', or 'cancel'
        """
        # Create unified diff
        diff_lines = list(difflib.unified_diff(
            original_content.splitlines(keepends=True),
            suggested_content.splitlines(keepends=True),
            fromfile=f"Original {file_path or 'content'}",
            tofile=f"Modified {file_path or 'content'}",
            lineterm=""
        ))
        
        if not diff_lines:
            self.console.print("[yellow]No changes detected[/yellow]")
            return "cancel"
        
        # Display the diff
        self._display_diff(diff_lines, file_path)
        
        # Prompt for user action
        return self._prompt_user_action()
    
    def _display_diff(self, diff_lines: List[str], file_path: Optional[str] = None) -> None:
        """Display the diff in a formatted way.
        
        Args:
            diff_lines: List of diff lines
            file_path: Path to the file being modified
        """
        title = f"Changes for {file_path}" if file_path else "Proposed Changes"
        
        # Create a panel with the diff
        diff_text = "".join(diff_lines)
        
        # Use syntax highlighting for better readability
        syntax = Syntax(
            diff_text,
            "diff",
            theme="monokai",
            line_numbers=True,
            word_wrap=True
        )
        
        panel = Panel(
            syntax,
            title=title,
            border_style="blue",
            padding=(1, 2)
        )
        
        self.console.print(panel)
    
    def _prompt_user_action(self) -> str:
        """Prompt user for action after showing diff.
        
        Returns:
            User's choice: 'accept', 'edit', or 'cancel'
        """
        self.console.print("\n[bold]What would you like to do?[/bold]")
        
        table = Table(show_header=False, box=None)
        table.add_column("Option", style="cyan")
        table.add_column("Description")
        
        table.add_row("A", "Accept changes and apply to file")
        table.add_row("E", "Edit the suggested changes")
        table.add_row("C", "Cancel (no changes)")
        
        self.console.print(table)
        
        while True:
            choice = Prompt.ask(
                "Choose an option",
                choices=["A", "E", "C"],
                default="C"
            )
            
            if choice == "A":
                return "accept"
            elif choice == "E":
                return "edit"
            elif choice == "C":
                return "cancel"
    
    def edit_suggestions(
        self,
        original_content: str,
        suggested_content: str,
        file_path: Optional[str] = None
    ) -> Optional[str]:
        """Open suggestions in an editor for manual editing.
        
        Args:
            original_content: Original file content
            suggested_content: AI-suggested content
            file_path: Path to the file being modified
            
        Returns:
            Edited content or None if cancelled
        """
        # Create a temporary file with the suggested content
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.tmp',
            delete=False,
            prefix='groq_suggestion_'
        ) as temp_file:
            temp_file.write(suggested_content)
            temp_file_path = temp_file.name
        
        try:
            # Get the editor to use
            editor = self._get_editor()
            
            # Open the file in the editor
            self.console.print(f"\n[green]Opening suggestions in {editor}...[/green]")
            self.console.print("[dim]Make your changes and save the file, then close the editor.[/dim]")
            
            # Run the editor
            result = subprocess.run([editor, temp_file_path])
            
            if result.returncode != 0:
                self.console.print("[red]Editor exited with an error[/red]")
                return None
            
            # Read the edited content
            with open(temp_file_path, 'r') as f:
                edited_content = f.read()
            
            # Show diff between original and edited content
            if edited_content != suggested_content:
                self.console.print("\n[bold]Changes made in editor:[/bold]")
                self._display_diff(
                    list(difflib.unified_diff(
                        suggested_content.splitlines(keepends=True),
                        edited_content.splitlines(keepends=True),
                        fromfile="AI Suggestion",
                        tofile="Your Edit",
                        lineterm=""
                    )),
                    file_path
                )
                
                if Confirm.ask("Apply these edited changes?"):
                    return edited_content
                else:
                    return None
            else:
                self.console.print("[yellow]No changes made in editor[/yellow]")
                return suggested_content
                
        except Exception as e:
            self.console.print(f"[red]Error opening editor: {e}[/red]")
            return None
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except OSError:
                pass
    
    def _get_editor(self) -> str:
        """Get the editor to use for editing suggestions.
        
        Returns:
            Editor command
        """
        # Check environment variables
        for env_var in ['EDITOR', 'VISUAL']:
            editor = os.getenv(env_var)
            if editor:
                return editor
        
        # Fallback to common editors
        common_editors = ['nano', 'vim', 'vi', 'code', 'subl']
        
        for editor in common_editors:
            try:
                subprocess.run([editor, '--version'], capture_output=True, check=True)
                return editor
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
        
        # Final fallback
        return 'nano'
    
    def apply_changes(
        self,
        file_path: str,
        new_content: str,
        backup: bool = True
    ) -> bool:
        """Apply changes to a file.
        
        Args:
            file_path: Path to the file to modify
            new_content: New content to write
            backup: Whether to create a backup of the original file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            file_path = Path(file_path)
            
            # Create backup if requested
            if backup and file_path.exists():
                backup_path = file_path.with_suffix(file_path.suffix + '.backup')
                file_path.rename(backup_path)
                self.console.print(f"[green]Backup created: {backup_path}[/green]")
            
            # Write the new content
            with open(file_path, 'w') as f:
                f.write(new_content)
            
            self.console.print(f"[green]Changes applied to {file_path}[/green]")
            return True
            
        except Exception as e:
            self.console.print(f"[red]Error applying changes: {e}[/red]")
            return False
    
    def review_and_apply(
        self,
        file_path: str,
        original_content: str,
        suggested_content: str,
        auto_apply: bool = False
    ) -> bool:
        """Complete workflow: show diff, get user input, and apply changes.
        
        Args:
            file_path: Path to the file being modified
            original_content: Original file content
            suggested_content: AI-suggested content
            auto_apply: Whether to skip user confirmation
            
        Returns:
            True if changes were applied, False otherwise
        """
        if auto_apply:
            return self.apply_changes(file_path, suggested_content)
        
        # Show diff and get user choice
        choice = self.show_diff(original_content, suggested_content, file_path)
        
        if choice == "accept":
            return self.apply_changes(file_path, suggested_content)
        elif choice == "edit":
            edited_content = self.edit_suggestions(
                original_content, suggested_content, file_path
            )
            if edited_content:
                return self.apply_changes(file_path, edited_content)
        elif choice == "cancel":
            self.console.print("[yellow]Changes cancelled[/yellow]")
        
        return False
    
    def show_file_preview(
        self,
        file_path: str,
        content: str,
        title: Optional[str] = None
    ) -> None:
        """Show a preview of file content.
        
        Args:
            file_path: Path to the file
            content: File content to display
            title: Optional title for the preview
        """
        if not title:
            title = f"Preview: {file_path}"
        
        # Determine syntax highlighting based on file extension
        syntax_name = self._get_syntax_name(file_path)
        
        syntax = Syntax(
            content,
            syntax_name,
            theme="monokai",
            line_numbers=True,
            word_wrap=True
        )
        
        panel = Panel(
            syntax,
            title=title,
            border_style="green",
            padding=(1, 2)
        )
        
        self.console.print(panel)
    
    def _get_syntax_name(self, file_path: str) -> str:
        """Get syntax highlighting name based on file extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Syntax highlighting name
        """
        ext = Path(file_path).suffix.lower()
        
        syntax_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'jsx',
            '.tsx': 'tsx',
            '.html': 'html',
            '.css': 'css',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.md': 'markdown',
            '.txt': 'text',
            '.sh': 'bash',
            '.bash': 'bash',
            '.zsh': 'bash',
            '.fish': 'bash',
            '.c': 'c',
            '.cpp': 'cpp',
            '.h': 'c',
            '.hpp': 'cpp',
            '.java': 'java',
            '.go': 'go',
            '.rs': 'rust',
            '.php': 'php',
            '.rb': 'ruby',
            '.sql': 'sql',
            '.xml': 'xml',
            '.toml': 'toml',
            '.ini': 'ini',
            '.conf': 'ini'
        }
        
        return syntax_map.get(ext, 'text')


