"""File operations component for code review and suggestions."""

import os
import stat
from pathlib import Path
from typing import Optional, List, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from datetime import datetime

from .api_client import GroqAPIClient
from .diff_manager import SuggestionDiffManager


class FileOperations:
    """Handles file-based operations like code review and suggestions."""
    
    def __init__(self, api_client: GroqAPIClient):
        """Initialize file operations.
        
        Args:
            api_client: Groq API client instance
        """
        self.api_client = api_client
        self.diff_manager = SuggestionDiffManager()
        self.console = Console()
    
    def analyze_file(
        self,
        file_path: str,
        model: str,
        analysis_type: str = "comprehensive"
    ) -> bool:
        """Analyze a file and provide insights without modifying it.
        
        Args:
            file_path: Path to the file to analyze
            model: Model to use for analysis
            analysis_type: Type of analysis (comprehensive, security, performance, etc.)
            
        Returns:
            True if analysis was successful, False otherwise
        """
        try:
            # Read the file
            if not os.path.exists(file_path):
                self.console.print(f"[red]File not found: {file_path}[/red]")
                return False
            
            with open(file_path, 'r') as f:
                file_content = f.read()
            
            # Get file metadata
            file_info = self._get_file_info(file_path)
            
            # Display file information
            self._display_file_info(file_info)
            
            # Show file preview
            self.console.print(f"\n[bold]File Content Preview:[/bold]")
            self.diff_manager.show_file_preview(file_path, file_content)
            
            # Generate analysis prompt
            analysis_prompt = self._generate_analysis_prompt(file_path, file_content, file_info, analysis_type)
            
            # Perform analysis
            self.console.print(f"\n[bold]Analyzing file with {model}...[/bold]")
            analysis_result = self.api_client.chat_completion(
                messages=[{"role": "user", "content": analysis_prompt}],
                model=model,
                temperature=0.3,
                max_tokens=2000
            )
            
            analysis_content = analysis_result.choices[0].message.content
            
            # Display analysis results
            self._display_analysis_results(analysis_content, analysis_type)
            
            return True
            
        except Exception as e:
            self.console.print(f"[red]Error analyzing file: {e}[/red]")
            return False
    
    def _get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get comprehensive file information.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary containing file metadata
        """
        path = Path(file_path)
        stat_info = path.stat()
        
        # Determine file type
        file_ext = path.suffix.lower()
        if file_ext in ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h', '.hpp']:
            file_type = "source_code"
        elif file_ext in ['.html', '.css', '.scss', '.sass']:
            file_type = "web"
        elif file_ext in ['.json', '.yaml', '.yml', '.toml', '.ini']:
            file_type = "configuration"
        elif file_ext in ['.md', '.txt', '.rst']:
            file_type = "documentation"
        else:
            file_type = "other"
        
        return {
            "path": str(path),
            "name": path.name,
            "extension": file_ext,
            "file_type": file_type,
            "size_bytes": stat_info.st_size,
            "size_human": self._format_file_size(stat_info.st_size),
            "lines": len(file_content.splitlines()) if 'file_content' in locals() else 0,
            "created": datetime.fromtimestamp(stat_info.st_ctime),
            "modified": datetime.fromtimestamp(stat_info.st_mtime),
            "permissions": oct(stat_info.st_mode)[-3:],
            "is_readable": os.access(file_path, os.R_OK),
            "is_writable": os.access(file_path, os.W_OK),
            "is_executable": os.access(file_path, os.X_OK)
        }
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format.
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            Formatted size string
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def _display_file_info(self, file_info: Dict[str, Any]) -> None:
        """Display file information in a table.
        
        Args:
            file_info: File metadata dictionary
        """
        table = Table(title="File Information", show_header=True, header_style="bold magenta")
        table.add_column("Property", style="cyan")
        table.add_column("Value")
        
        table.add_row("File Path", file_info["path"])
        table.add_row("File Name", file_info["name"])
        table.add_row("Extension", file_info["extension"])
        table.add_row("File Type", file_info["file_type"])
        table.add_row("Size", file_info["size_human"])
        table.add_row("Lines", str(file_info["lines"]))
        table.add_row("Created", file_info["created"].strftime("%Y-%m-%d %H:%M:%S"))
        table.add_row("Modified", file_info["modified"].strftime("%Y-%m-%d %H:%M:%S"))
        table.add_row("Permissions", file_info["permissions"])
        table.add_row("Readable", "✓" if file_info["is_readable"] else "✗")
        table.add_row("Writable", "✓" if file_info["is_writable"] else "✗")
        table.add_row("Executable", "✓" if file_info["is_executable"] else "✗")
        
        self.console.print(table)
    
    def _generate_analysis_prompt(self, file_path: str, file_content: str, file_info: Dict[str, Any], analysis_type: str) -> str:
        """Generate analysis prompt based on file type and analysis type.
        
        Args:
            file_path: Path to the file
            file_content: File content
            file_info: File metadata
            analysis_type: Type of analysis to perform
            
        Returns:
            Generated analysis prompt
        """
        base_prompt = f"""
Analyze the following file and provide detailed insights:

File: {file_path}
Type: {file_info['file_type']}
Size: {file_info['size_human']}
Lines: {file_info['lines']}

File Content:
{file_content}

Please provide a comprehensive analysis including:
"""
        
        if analysis_type == "comprehensive":
            analysis_prompt = base_prompt + """
1. **Code Quality Assessment**
   - Readability and maintainability
   - Code structure and organization
   - Naming conventions
   - Documentation quality

2. **Technical Analysis**
   - Potential bugs or issues
   - Performance considerations
   - Security vulnerabilities
   - Best practices compliance

3. **Architecture & Design**
   - Design patterns used
   - Coupling and cohesion
   - Scalability considerations
   - Testability

4. **Improvement Suggestions**
   - Specific recommendations
   - Refactoring opportunities
   - Optimization suggestions
   - Documentation improvements

5. **Risk Assessment**
   - Potential issues
   - Maintenance concerns
   - Technical debt indicators

Please provide actionable insights and specific recommendations.
"""
        elif analysis_type == "security":
            analysis_prompt = base_prompt + """
Focus on security analysis:

1. **Security Vulnerabilities**
   - Input validation issues
   - Authentication/authorization problems
   - Data exposure risks
   - Injection vulnerabilities

2. **Security Best Practices**
   - Secure coding practices
   - Data protection measures
   - Error handling security
   - Logging and monitoring

3. **Risk Assessment**
   - Critical security issues
   - Medium priority concerns
   - Low priority recommendations

4. **Remediation Steps**
   - Specific fixes needed
   - Security improvements
   - Testing recommendations
"""
        elif analysis_type == "performance":
            analysis_prompt = base_prompt + """
Focus on performance analysis:

1. **Performance Issues**
   - Bottlenecks and inefficiencies
   - Resource usage problems
   - Algorithm complexity
   - Memory management

2. **Optimization Opportunities**
   - Code optimizations
   - Data structure improvements
   - Caching strategies
   - Parallelization potential

3. **Performance Metrics**
   - Time complexity analysis
   - Space complexity analysis
   - Resource usage patterns

4. **Performance Recommendations**
   - Specific optimizations
   - Best practices
   - Monitoring suggestions
"""
        else:
            analysis_prompt = base_prompt + """
Provide a general analysis covering:
- Code quality and structure
- Potential issues and improvements
- Best practices compliance
- Specific recommendations
"""
        
        return analysis_prompt
    
    def _display_analysis_results(self, analysis_content: str, analysis_type: str) -> None:
        """Display analysis results in a formatted way.
        
        Args:
            analysis_content: Analysis results from AI
            analysis_type: Type of analysis performed
        """
        title = f"Analysis Results ({analysis_type.title()})"
        
        panel = Panel(
            analysis_content,
            title=title,
            border_style="green",
            padding=(1, 2)
        )
        
        self.console.print(panel)
    
    def review_file(
        self,
        file_path: str,
        model: str,
        prompt: Optional[str] = None,
        auto_apply: bool = False
    ) -> bool:
        """Review and suggest improvements for a file.
        
        Args:
            file_path: Path to the file to review
            model: Model to use for suggestions
            prompt: Optional custom prompt for the review
            auto_apply: Whether to skip user confirmation
            
        Returns:
            True if changes were applied, False otherwise
        """
        try:
            # Read the file
            if not os.path.exists(file_path):
                self.console.print(f"[red]File not found: {file_path}[/red]")
                return False
            
            with open(file_path, 'r') as f:
                original_content = f.read()
            
            # Get file information
            file_info = self._get_file_info(file_path)
            
            # Show file preview
            self.console.print(f"\n[bold]Reviewing file: {file_path}[/bold]")
            self.console.print(f"[dim]File size: {file_info['size_human']}, Lines: {file_info['lines']}[/dim]")
            self.diff_manager.show_file_preview(file_path, original_content)
            
            # Generate review prompt
            if not prompt:
                prompt = self._generate_review_prompt(file_path, original_content, file_info)
            
            # Get user confirmation for the review
            if not auto_apply:
                self.console.print(f"\n[bold]Review prompt:[/bold] {prompt}")
                if not Prompt.ask("Proceed with this review?", default=True):
                    self.console.print("[yellow]Review cancelled[/yellow]")
                    return False
            
            # Generate suggestions
            self.console.print("\n[bold]Generating suggestions...[/bold]")
            suggested_content = self.api_client.generate_code_suggestions(
                file_content=original_content,
                prompt=prompt,
                model=model,
                temperature=0.3
            )
            
            if not suggested_content:
                self.console.print("[red]No suggestions generated[/red]")
                return False
            
            # Review and apply changes
            return self.diff_manager.review_and_apply(
                file_path=file_path,
                original_content=original_content,
                suggested_content=suggested_content,
                auto_apply=auto_apply
            )
            
        except Exception as e:
            self.console.print(f"[red]Error reviewing file: {e}[/red]")
            return False

    def review_files(
        self,
        file_paths: List[str],
        model: str,
        prompt: Optional[str] = None,
        auto_apply: bool = False,
    ) -> Dict[str, bool]:
        """Review and suggest improvements for multiple files with context.

        Args:
            file_paths: List of file paths to review
            model: Model to use for suggestions
            prompt: Optional custom prompt for the review
            auto_apply: Whether to skip user confirmation

        Returns:
            Dictionary mapping file paths to success status
        """
        results: Dict[str, bool] = {}

        # Read contents of all files first for cross-file context
        file_contents: Dict[str, str] = {}
        for path in file_paths:
            if not os.path.exists(path):
                self.console.print(f"[red]File not found: {path}[/red]")
                results[path] = False
                continue
            with open(path, "r") as f:
                file_contents[path] = f.read()

        for path in file_paths:
            if path not in file_contents:
                continue

            # Build context from other files
            other_context = "".join(
                f"\n\nFile: {p}\n{file_contents[p]}" for p in file_paths if p != path and p in file_contents
            )
            contextual_prompt = prompt or "Review and modify the file as requested."
            if other_context:
                contextual_prompt = (
                    f"{contextual_prompt}\n\nConsider the following related files for context:{other_context}"
                )

            success = self.review_file(path, model, contextual_prompt, auto_apply)
            results[path] = success

        return results
    
    def _generate_review_prompt(self, file_path: str, file_content: str, file_info: Dict[str, Any]) -> str:
        """Generate a review prompt based on file type and content.
        
        Args:
            file_path: Path to the file
            file_content: File content
            file_info: File metadata
            
        Returns:
            Generated review prompt
        """
        file_ext = Path(file_path).suffix.lower()
        
        # Enhanced prompt with file context
        context_info = f"""
File: {file_path}
Type: {file_info['file_type']}
Size: {file_info['size_human']}
Lines: {file_info['lines']}
"""
        
        # Customize prompt based on file type
        if file_ext == '.py':
            return context_info + """
Please review this Python code and suggest improvements for:
1) Code quality and readability
2) Performance optimizations
3) Best practices and PEP 8 compliance
4) Error handling and robustness
5) Documentation and docstrings
6) Type hints and modern Python features
7) Security considerations
8) Testability and maintainability

Return the improved code with all enhancements applied.
"""
        elif file_ext in ['.js', '.ts', '.jsx', '.tsx']:
            return context_info + """
Please review this JavaScript/TypeScript code and suggest improvements for:
1) Code quality and readability
2) Type safety (if TypeScript)
3) Modern JavaScript/ES6+ features
4) Error handling and async patterns
5) Performance optimizations
6) Security best practices
7) Testing considerations
8) Documentation and comments

Return the improved code with all enhancements applied.
"""
        elif file_ext in ['.html', '.css']:
            return context_info + """
Please review this HTML/CSS code and suggest improvements for:
1) Accessibility (WCAG compliance)
2) Semantic HTML structure
3) CSS organization and maintainability
4) Responsive design principles
5) Performance optimizations
6) Cross-browser compatibility
7) Best practices and standards
8) SEO considerations

Return the improved code with all enhancements applied.
"""
        elif file_ext in ['.md', '.txt']:
            return context_info + """
Please review this text and suggest improvements for:
1) Clarity and readability
2) Grammar and spelling
3) Structure and organization
4) Professional tone and style
5) Content completeness
6) Formatting consistency
7) Accessibility considerations

Return the improved text with all enhancements applied.
"""
        else:
            return context_info + """
Please review this code and suggest improvements for:
1) Code quality and readability
2) Best practices and standards
3) Error handling and robustness
4) Performance optimizations
5) Security considerations
6) Documentation and comments
7) Maintainability and testability

Return the improved code with all enhancements applied.
"""
    
    def suggest_improvements(
        self,
        file_path: str,
        model: str,
        improvement_type: str,
        auto_apply: bool = False
    ) -> bool:
        """Suggest specific improvements for a file.
        
        Args:
            file_path: Path to the file
            model: Model to use for suggestions
            improvement_type: Type of improvement to suggest
            auto_apply: Whether to skip user confirmation
            
        Returns:
            True if changes were applied, False otherwise
        """
        improvement_prompts = {
            "performance": "Analyze this code for performance issues and suggest optimizations. Focus on algorithms, data structures, and efficiency.",
            "security": "Review this code for security vulnerabilities and suggest improvements. Focus on input validation, authentication, and data protection.",
            "readability": "Improve the readability and maintainability of this code. Focus on clear variable names, function structure, and code organization.",
            "documentation": "Add comprehensive documentation to this code. Include docstrings, comments, and README-style documentation where appropriate.",
            "testing": "Suggest unit tests and test cases for this code. Include edge cases and error scenarios.",
            "refactoring": "Refactor this code to improve its structure and design. Focus on separation of concerns, SOLID principles, and clean architecture."
        }
        
        if improvement_type not in improvement_prompts:
            self.console.print(f"[red]Unknown improvement type: {improvement_type}[/red]")
            self.console.print(f"Available types: {', '.join(improvement_prompts.keys())}")
            return False
        
        prompt = improvement_prompts[improvement_type]
        return self.review_file(file_path, model, prompt, auto_apply)
    
    def batch_review(
        self,
        file_paths: List[str],
        model: str,
        prompt: Optional[str] = None,
        auto_apply: bool = False
    ) -> Dict[str, bool]:
        """Review multiple files in batch.
        
        Args:
            file_paths: List of file paths to review
            model: Model to use for suggestions
            prompt: Optional custom prompt for all reviews
            auto_apply: Whether to skip user confirmation
            
        Returns:
            Dictionary mapping file paths to success status
        """
        results = {}
        
        self.console.print(f"[bold]Batch reviewing {len(file_paths)} files...[/bold]")
        
        for file_path in file_paths:
            self.console.print(f"\n[bold]Reviewing: {file_path}[/bold]")
            
            success = self.review_file(
                file_path=file_path,
                model=model,
                prompt=prompt,
                auto_apply=auto_apply
            )
            
            results[file_path] = success
            
            if success:
                self.console.print(f"[green]✓ {file_path} - Changes applied[/green]")
            else:
                self.console.print(f"[red]✗ {file_path} - No changes[/red]")
        
        # Summary
        successful = sum(1 for success in results.values() if success)
        self.console.print(f"\n[bold]Batch review complete: {successful}/{len(file_paths)} files modified[/bold]")
        
        return results
    
    def create_file_from_prompt(
        self,
        file_path: str,
        model: str,
        prompt: str,
        file_type: Optional[str] = None
    ) -> bool:
        """Create a new file based on a prompt.
        
        Args:
            file_path: Path where the file should be created
            model: Model to use for generation
            prompt: Prompt describing what the file should contain
            file_type: Optional file type hint
            
        Returns:
            True if file was created successfully, False otherwise
        """
        try:
            # Check if file already exists
            if os.path.exists(file_path):
                if not Prompt.ask(f"File {file_path} already exists. Overwrite?", default=False):
                    self.console.print("[yellow]File creation cancelled[/yellow]")
                    return False
            
            # Generate file content
            self.console.print(f"\n[bold]Generating file: {file_path}[/bold]")
            
            # Enhance prompt with file type information
            enhanced_prompt = self._enhance_file_creation_prompt(prompt, file_path, file_type)
            
            content = self.api_client.generate_code_suggestions(
                file_content="",  # Empty for new file
                prompt=enhanced_prompt,
                model=model,
                temperature=0.7
            )
            
            if not content:
                self.console.print("[red]Failed to generate file content[/red]")
                return False
            
            # Show preview
            self.diff_manager.show_file_preview(file_path, content, "Generated File")
            
            # Confirm creation
            if Prompt.ask("Create this file?", default=True):
                # Ensure directory exists
                Path(file_path).parent.mkdir(parents=True, exist_ok=True)
                
                # Write file
                with open(file_path, 'w') as f:
                    f.write(content)
                
                self.console.print(f"[green]File created: {file_path}[/green]")
                return True
            else:
                self.console.print("[yellow]File creation cancelled[/yellow]")
                return False
                
        except Exception as e:
            self.console.print(f"[red]Error creating file: {e}[/red]")
            return False
    
    def _enhance_file_creation_prompt(
        self,
        prompt: str,
        file_path: str,
        file_type: Optional[str] = None
    ) -> str:
        """Enhance file creation prompt with context.
        
        Args:
            prompt: Original prompt
            file_path: Target file path
            file_type: Optional file type hint
            
        Returns:
            Enhanced prompt
        """
        file_ext = Path(file_path).suffix.lower()
        
        # Determine file type from extension if not provided
        if not file_type:
            if file_ext == '.py':
                file_type = 'Python'
            elif file_ext in ['.js', '.ts', '.jsx', '.tsx']:
                file_type = 'JavaScript/TypeScript'
            elif file_ext in ['.html', '.css']:
                file_type = 'HTML/CSS'
            elif file_ext == '.md':
                file_type = 'Markdown'
            elif file_ext == '.json':
                file_type = 'JSON'
            elif file_ext == '.yaml' or file_ext == '.yml':
                file_type = 'YAML'
            else:
                file_type = 'text'
        
        enhanced_prompt = f"""
Create a {file_type} file with the following requirements:

{prompt}

File path: {file_path}

Please provide complete, working code that:
1. Follows best practices for {file_type}
2. Includes appropriate documentation and comments
3. Is ready to use immediately
4. Handles edge cases and errors appropriately

Return only the file content, no explanations.
        """.strip()
        
        return enhanced_prompt
