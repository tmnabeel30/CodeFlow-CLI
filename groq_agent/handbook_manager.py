"""Handbook Manager for CodeFlowNinjaHandbook.md - Tracks all code logic and changes."""

import os
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
import re

from .config import ConfigurationManager


@dataclass
class FunctionInfo:
    """Information about a function in the codebase."""
    name: str
    file_path: str
    line_number: int
    description: str
    parameters: List[str] = field(default_factory=list)
    return_type: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    impact_level: str = "low"  # low, medium, high, critical
    last_modified: Optional[str] = None


@dataclass
class FileInfo:
    """Information about a file in the codebase."""
    path: str
    purpose: str
    functions: List[FunctionInfo] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    last_modified: Optional[str] = None
    size: int = 0
    lines: int = 0


@dataclass
class ChangeRecord:
    """Record of changes made to the codebase."""
    timestamp: str
    goal: str
    files_changed: List[str]
    changes_description: str
    impact_analysis: str
    context_passed: Dict[str, Any] = field(default_factory=dict)


class HandbookManager:
    """Manages the CodeFlowNinjaHandbook.md file and tracks all code changes."""
    
    def __init__(self, workspace_path: Path, config: ConfigurationManager):
        """Initialize the handbook manager.
        
        Args:
            workspace_path: Path to the workspace
            config: Configuration manager instance
        """
        self.workspace_path = workspace_path
        self.config = config
        self.handbook_path = workspace_path / "CodeFlowNinjaHandbook.md"
        self.handbook_data: Dict[str, Any] = {}
        self.change_history: List[ChangeRecord] = []
        
        # Initialize or load handbook
        self._initialize_handbook()
    
    def _initialize_handbook(self) -> None:
        """Initialize the handbook file if it doesn't exist."""
        if not self.handbook_path.exists():
            self._create_initial_handbook()
        else:
            # Always regenerate the handbook to ensure it's up to date
            self._create_initial_handbook()
    
    def _create_initial_handbook(self) -> None:
        """Create the initial CodeFlowNinjaHandbook.md file."""
        initial_content = self._generate_initial_handbook_content()
        
        with open(self.handbook_path, 'w', encoding='utf-8') as f:
            f.write(initial_content)
        
        self._load_handbook()
    
    def _generate_initial_handbook_content(self) -> str:
        """Generate the initial handbook content based on the current codebase."""
        # Analyze the current codebase
        project_info = self._analyze_codebase()
        
        return f"""# CodeFlowNinjaHandbook.md

## 📋 Project Overview
**Project Name:** {project_info['name']}  
**Project Type:** {project_info['type']}  
**Created:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Version:** {project_info.get('version', '1.0.0')}

## 🎯 Project Purpose
{project_info['description']}

## 🏗️ System Architecture

### Core Components
{project_info['core_components']}

## 📁 File Structure and Responsibilities

### Main Entry Points
{project_info['entry_points']}

### Core Modules
{project_info['core_modules']}

### Configuration Files
{project_info['config_files']}

### Documentation
{project_info['documentation']}

## 🔧 Function Analysis

### Critical Functions (High Impact)
{project_info['critical_functions']}

### Core Functions (Medium Impact)
{project_info['core_functions']}

### Utility Functions (Low Impact)
{project_info['utility_functions']}

## 🔄 Change Tracking

### Recent Changes
*To be populated as changes are made*

### Change History
*To be populated as changes are made*

## 🎯 Goal Tracking

### Current Goals
*To be populated during goal execution*

### Completed Goals
*To be populated as goals are completed*

### Goal Context Chain
*To be populated during recursive goal execution*

## 📊 System Metrics

### File Statistics
{project_info['file_statistics']}

### Code Quality Metrics
{project_info['code_quality_metrics']}

### Performance Metrics
{project_info['performance_metrics']}

## 🔍 Context Management

### Active Context
{project_info['active_context']}

### Context History
{project_info['context_history']}

---

*This handbook is automatically maintained by the CodeFlow system. Do not edit manually.*
"""
    
    def _load_handbook(self) -> None:
        """Load the handbook data from the markdown file."""
        try:
            with open(self.handbook_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse the handbook content
            self._parse_handbook_content(content)
        except Exception as e:
            print(f"Error loading handbook: {e}")
            self._create_initial_handbook()
    
    def _parse_handbook_content(self, content: str) -> None:
        """Parse the handbook markdown content into structured data."""
        # This is a simplified parser - in a real implementation, you'd use a proper markdown parser
        self.handbook_data = {
            'content': content,
            'last_updated': datetime.now().isoformat(),
            'sections': self._extract_sections(content)
        }
    
    def _extract_sections(self, content: str) -> Dict[str, str]:
        """Extract sections from the handbook content."""
        sections = {}
        current_section = ""
        current_content = []
        
        for line in content.split('\n'):
            if line.startswith('## '):
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = line[3:].strip()
                current_content = []
            elif current_section:
                current_content.append(line)
        
        if current_section:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections
    
    def update_handbook(self, changes: Dict[str, Any]) -> None:
        """Update the handbook with new information."""
        # Update the handbook data
        self.handbook_data.update(changes)
        self.handbook_data['last_updated'] = datetime.now().isoformat()
        
        # Regenerate the handbook content
        new_content = self._regenerate_handbook_content()
        
        # Write the updated content
        with open(self.handbook_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
    
    def _regenerate_handbook_content(self) -> str:
        """Regenerate the handbook content from the data."""
        # This would regenerate the markdown content from the structured data
        # For now, return the original content with updated timestamp
        content = self.handbook_data.get('content', '')
        content = re.sub(
            r'\*\*Last Updated:\*\* .*',
            f'**Last Updated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            content
        )
        return content
    
    def add_change_record(self, change: ChangeRecord) -> None:
        """Add a change record to the handbook."""
        self.change_history.append(change)
        
        # Update the handbook with the new change
        changes_section = self._format_change_record(change)
        self._update_changes_section(changes_section)
    
    def _format_change_record(self, change: ChangeRecord) -> str:
        """Format a change record for the handbook."""
        return f"""
### Change at {change.timestamp}
**Goal:** {change.goal}
**Files Changed:** {', '.join(change.files_changed)}
**Description:** {change.changes_description}
**Impact:** {change.impact_analysis}
**Context Passed:** {json.dumps(change.context_passed, indent=2)}
"""
    
    def _update_changes_section(self, new_change: str) -> None:
        """Update the changes section in the handbook."""
        # This would update the changes section in the handbook
        # For now, just update the data
        pass
    
    def get_context_for_goal(self, goal: str) -> Dict[str, Any]:
        """Get relevant context for a specific goal."""
        context = {
            'handbook_data': self.handbook_data,
            'recent_changes': self.change_history[-5:] if self.change_history else [],
            'file_structure': self._get_file_structure(),
            'function_impacts': self._get_function_impacts()
        }
        return context
    
    def _get_file_structure(self) -> Dict[str, Any]:
        """Get the current file structure."""
        # This would analyze the current file structure
        return {}
    
    def _get_function_impacts(self) -> Dict[str, Any]:
        """Get function impact analysis."""
        # This would analyze function impacts
        return {}
    
    def update_function_info(self, function_info: FunctionInfo) -> None:
        """Update function information in the handbook."""
        # This would update function information
        pass
    
    def update_file_info(self, file_info: FileInfo) -> None:
        """Update file information in the handbook."""
        # This would update file information
        pass
    
    def get_handbook_path(self) -> Path:
        """Get the path to the handbook file."""
        return self.handbook_path
    
    def _analyze_codebase(self) -> Dict[str, Any]:
        """Analyze the current codebase to generate project information."""
        project_info = {
            'name': 'Unknown Project',
            'type': 'Unknown',
            'description': 'A software project with various components and functionality.',
            'version': '1.0.0',
            'core_components': '',
            'entry_points': '',
            'core_modules': '',
            'config_files': '',
            'documentation': '',
            'dependencies': '',
            'languages': '',
            'frameworks': '',
            'build_tools': '',
            'dev_tools': '',
            'critical_functions': '*To be populated during code analysis*',
            'core_functions': '*To be populated during code analysis*',
            'utility_functions': '*To be populated during code analysis*',
            'recent_changes': '*To be populated as changes are made*',
            'change_history': '*To be populated as changes are made*',
            'current_goals': '*To be populated during goal execution*',
            'completed_goals': '*To be populated as goals are completed*',
            'goal_context_chain': '*To be populated during recursive goal execution*',
            'file_statistics': '*To be populated during analysis*',
            'code_quality_metrics': '*To be populated during analysis*',
            'performance_metrics': '*To be populated during analysis*',
            'active_context': '*To be populated during operations*',
            'context_history': '*To be populated during operations*',
            'file_descriptions': '*To be populated during analysis*',
            'function_documentation': '*To be populated during analysis*',
            'class_documentation': '*To be populated during analysis*',
            'internal_dependencies': '*To be populated during analysis*',
            'external_dependencies': '*To be populated during analysis*',
            'import_relationships': '*To be populated during analysis*'
        }
        
        # Get all files in the workspace (excluding virtual environments and common ignore patterns)
        all_files = []
        ignore_patterns = ['.venv', 'venv', 'env', '__pycache__', '.git', 'node_modules', '.pytest_cache']
        
        for ext in ['*.py', '*.js', '*.ts', '*.jsx', '*.tsx', '*.java', '*.cpp', '*.c', '*.go', '*.rs', '*.php', '*.rb']:
            for file_path in self.workspace_path.glob(f"**/{ext}"):
                # Skip files in ignored directories
                if not any(pattern in str(file_path) for pattern in ignore_patterns):
                    all_files.append(file_path)
        
        # Analyze project type based on files
        project_info.update(self._detect_project_type(all_files))
        
        # Analyze file structure
        project_info.update(self._analyze_file_structure(all_files))
        
        # Analyze dependencies
        project_info.update(self._analyze_dependencies())
        
        # Analyze technology stack
        project_info.update(self._analyze_tech_stack(all_files))
        
        # Generate core components
        project_info['core_components'] = self._generate_core_components(all_files)
        
        # Analyze functions and classes
        project_info.update(self._analyze_functions_and_classes(all_files))
        
        # Analyze file statistics
        project_info.update(self._analyze_file_statistics(all_files))
        
        return project_info
    
    def _detect_project_type(self, files: List[Path]) -> Dict[str, Any]:
        """Detect the type of project based on files present."""
        file_names = [f.name.lower() for f in files]
        file_paths = [str(f).lower() for f in files]
        
        # Check for common project indicators
        if any('package.json' in f for f in file_paths):
            return {
                'type': 'Node.js/JavaScript',
                'name': self._extract_project_name_from_package_json(),
                'description': 'A Node.js/JavaScript project with modern web development capabilities.'
            }
        elif any('requirements.txt' in f for f in file_paths) or any('pyproject.toml' in f for f in file_paths):
            return {
                'type': 'Python',
                'name': self._extract_project_name_from_python_files(),
                'description': 'A Python project with various modules and functionality.'
            }
        elif any('cargo.toml' in f for f in file_paths):
            return {
                'type': 'Rust',
                'name': self._extract_project_name_from_cargo_toml(),
                'description': 'A Rust project with system-level programming capabilities.'
            }
        elif any('pom.xml' in f for f in file_paths) or any('build.gradle' in f for f in file_paths):
            return {
                'type': 'Java',
                'name': self._extract_project_name_from_java_files(),
                'description': 'A Java project with enterprise-level capabilities.'
            }
        elif any('go.mod' in f for f in file_paths):
            return {
                'type': 'Go',
                'name': self._extract_project_name_from_go_mod(),
                'description': 'A Go project with high-performance networking capabilities.'
            }
        else:
            return {
                'type': 'Mixed/Unknown',
                'name': self.workspace_path.name,
                'description': 'A software project with various components and functionality.'
            }
    
    def _extract_project_name_from_package_json(self) -> str:
        """Extract project name from package.json."""
        try:
            package_json = self.workspace_path / 'package.json'
            if package_json.exists():
                import json
                with open(package_json, 'r') as f:
                    data = json.load(f)
                    return data.get('name', self.workspace_path.name)
        except:
            pass
        return self.workspace_path.name
    
    def _extract_project_name_from_python_files(self) -> str:
        """Extract project name from Python files."""
        try:
            # Check for setup.py
            setup_py = self.workspace_path / 'setup.py'
            if setup_py.exists():
                with open(setup_py, 'r') as f:
                    content = f.read()
                    import re
                    match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', content)
                    if match:
                        return match.group(1)
            
            # Check for pyproject.toml
            pyproject_toml = self.workspace_path / 'pyproject.toml'
            if pyproject_toml.exists():
                with open(pyproject_toml, 'r') as f:
                    content = f.read()
                    import re
                    match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', content)
                    if match:
                        return match.group(1)
        except:
            pass
        return self.workspace_path.name
    
    def _extract_project_name_from_cargo_toml(self) -> str:
        """Extract project name from Cargo.toml."""
        try:
            cargo_toml = self.workspace_path / 'Cargo.toml'
            if cargo_toml.exists():
                with open(cargo_toml, 'r') as f:
                    content = f.read()
                    import re
                    match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', content)
                    if match:
                        return match.group(1)
        except:
            pass
        return self.workspace_path.name
    
    def _extract_project_name_from_java_files(self) -> str:
        """Extract project name from Java files."""
        try:
            # Check for pom.xml
            pom_xml = self.workspace_path / 'pom.xml'
            if pom_xml.exists():
                with open(pom_xml, 'r') as f:
                    content = f.read()
                    import re
                    match = re.search(r'<artifactId>([^<]+)</artifactId>', content)
                    if match:
                        return match.group(1)
        except:
            pass
        return self.workspace_path.name
    
    def _extract_project_name_from_go_mod(self) -> str:
        """Extract project name from go.mod."""
        try:
            go_mod = self.workspace_path / 'go.mod'
            if go_mod.exists():
                with open(go_mod, 'r') as f:
                    content = f.read()
                    import re
                    match = re.search(r'module\s+([^\s]+)', content)
                    if match:
                        return match.group(1).split('/')[-1]
        except:
            pass
        return self.workspace_path.name
    
    def _analyze_file_structure(self, files: List[Path]) -> Dict[str, Any]:
        """Analyze the file structure and categorize files."""
        entry_points = []
        core_modules = []
        config_files = []
        documentation = []
        
        for file_path in files:
            file_str = str(file_path)
            file_name = file_path.name.lower()
            
            # Entry points
            if file_name in ['main.py', 'app.py', 'index.js', 'index.ts', 'main.rs', 'main.go', 'main.java']:
                entry_points.append(f"- `{file_str}` - Main entry point")
            elif 'main' in file_name or 'app' in file_name:
                entry_points.append(f"- `{file_str}` - Application entry point")
            
            # Core modules
            if file_path.suffix in ['.py', '.js', '.ts', '.java', '.cpp', '.go', '.rs']:
                core_modules.append(f"- `{file_str}` - Core module")
            
            # Config files
            if file_name in ['package.json', 'requirements.txt', 'cargo.toml', 'pom.xml', 'go.mod', 'setup.py', 'pyproject.toml']:
                config_files.append(f"- `{file_str}` - Configuration file")
            
            # Documentation
            if file_name in ['readme.md', 'readme.txt', 'license', 'changelog.md']:
                documentation.append(f"- `{file_str}` - Documentation")
        
        return {
            'entry_points': '\n'.join(entry_points) if entry_points else '- No main entry points detected',
            'core_modules': '\n'.join(core_modules[:10]) if core_modules else '- No core modules detected',
            'config_files': '\n'.join(config_files) if config_files else '- No configuration files detected',
            'documentation': '\n'.join(documentation) if documentation else '- No documentation files detected'
        }
    
    def _analyze_dependencies(self) -> Dict[str, Any]:
        """Analyze project dependencies."""
        dependencies = []
        
        # Check for various dependency files
        dep_files = {
            'package.json': 'Node.js dependencies',
            'requirements.txt': 'Python dependencies',
            'cargo.toml': 'Rust dependencies',
            'pom.xml': 'Java dependencies',
            'go.mod': 'Go dependencies'
        }
        
        for file_name, desc in dep_files.items():
            file_path = self.workspace_path / file_name
            if file_path.exists():
                dependencies.append(f"- `{file_name}` - {desc}")
        
        return {
            'dependencies': '\n'.join(dependencies) if dependencies else '- No dependency files detected'
        }
    
    def _analyze_tech_stack(self, files: List[Path]) -> Dict[str, Any]:
        """Analyze the technology stack used in the project."""
        languages = set()
        frameworks = set()
        build_tools = set()
        dev_tools = set()
        
        for file_path in files:
            ext = file_path.suffix.lower()
            
            # Languages
            if ext == '.py':
                languages.add('Python')
            elif ext in ['.js', '.jsx']:
                languages.add('JavaScript')
            elif ext in ['.ts', '.tsx']:
                languages.add('TypeScript')
            elif ext == '.java':
                languages.add('Java')
            elif ext in ['.cpp', '.c']:
                languages.add('C/C++')
            elif ext == '.go':
                languages.add('Go')
            elif ext == '.rs':
                languages.add('Rust')
            elif ext == '.php':
                languages.add('PHP')
            elif ext == '.rb':
                languages.add('Ruby')
            
            # Frameworks (based on file patterns)
            file_str = str(file_path).lower()
            if 'react' in file_str or '.jsx' in file_str:
                frameworks.add('React')
            if 'vue' in file_str or '.vue' in file_str:
                frameworks.add('Vue.js')
            if 'angular' in file_str:
                frameworks.add('Angular')
            if 'django' in file_str:
                frameworks.add('Django')
            if 'flask' in file_str:
                frameworks.add('Flask')
            if 'express' in file_str:
                frameworks.add('Express.js')
            if 'spring' in file_str:
                frameworks.add('Spring')
        
        # Build tools
        build_files = ['package.json', 'webpack.config.js', 'vite.config.js', 'rollup.config.js', 
                      'cargo.toml', 'pom.xml', 'build.gradle', 'go.mod', 'setup.py', 'pyproject.toml']
        for build_file in build_files:
            if (self.workspace_path / build_file).exists():
                if build_file == 'package.json':
                    build_tools.add('npm/yarn')
                elif build_file == 'cargo.toml':
                    build_tools.add('Cargo')
                elif build_file in ['pom.xml', 'build.gradle']:
                    build_tools.add('Maven/Gradle')
                elif build_file == 'go.mod':
                    build_tools.add('Go modules')
                elif build_file in ['setup.py', 'pyproject.toml']:
                    build_tools.add('pip/setuptools')
        
        # Dev tools
        dev_files = ['.gitignore', '.eslintrc', '.prettierrc', 'tsconfig.json', 'jest.config.js', 
                    'pytest.ini', '.pytest_cache', 'coverage', '.coverage']
        for dev_file in dev_files:
            if (self.workspace_path / dev_file).exists():
                if dev_file == '.gitignore':
                    dev_tools.add('Git')
                elif dev_file in ['.eslintrc', '.prettierrc']:
                    dev_tools.add('ESLint/Prettier')
                elif dev_file == 'tsconfig.json':
                    dev_tools.add('TypeScript')
                elif dev_file in ['jest.config.js', 'pytest.ini']:
                    dev_tools.add('Testing framework')
        
        return {
            'languages': ', '.join(sorted(languages)) if languages else 'Unknown',
            'frameworks': ', '.join(sorted(frameworks)) if frameworks else 'None detected',
            'build_tools': ', '.join(sorted(build_tools)) if build_tools else 'None detected',
            'dev_tools': ', '.join(sorted(dev_tools)) if dev_tools else 'None detected'
        }
    
    def _generate_core_components(self, files: List[Path]) -> str:
        """Generate core components section based on the codebase."""
        components = []
        
        # Analyze files to identify core components
        for i, file_path in enumerate(files[:10], 1):  # Limit to first 10 files
            file_str = str(file_path)
            file_name = file_path.name.lower()
            
            # Determine component type based on file name and path
            if 'main' in file_name or 'app' in file_name:
                component_type = "Main Application"
                description = "Main entry point and application logic"
            elif 'config' in file_name or 'settings' in file_name:
                component_type = "Configuration"
                description = "Configuration and settings management"
            elif 'api' in file_name or 'client' in file_name:
                component_type = "API/Client"
                description = "API communication and client functionality"
            elif 'model' in file_name or 'data' in file_name:
                component_type = "Data/Model"
                description = "Data models and business logic"
            elif 'util' in file_name or 'helper' in file_name:
                component_type = "Utilities"
                description = "Utility functions and helpers"
            elif 'test' in file_name:
                component_type = "Testing"
                description = "Test files and testing utilities"
            else:
                component_type = "Core Module"
                description = "Core functionality and business logic"
            
            components.append(f"{i}. **{component_type}** (`{file_str}`)\n   - {description}")
        
        if not components:
            components.append("1. **Main Application** - Core application functionality")
            components.append("2. **Configuration** - Settings and configuration management")
            components.append("3. **Core Modules** - Business logic and utilities")
        
        return '\n\n'.join(components)

    def _analyze_functions_and_classes(self, files: List[Path]) -> Dict[str, Any]:
        """Analyze functions and classes in the codebase."""
        critical_functions = []
        core_functions = []
        utility_functions = []
        classes = []
        
        # Handle empty file list
        if not files:
            return {
                'critical_functions': '*No files to analyze*',
                'core_functions': '*No files to analyze*',
                'utility_functions': '*No files to analyze*',
                'function_documentation': '*No functions found*',
                'class_documentation': '*No classes found*'
            }
        
        for file_path in files:
            if file_path.suffix.lower() in ['.py', '.js', '.ts', '.java', '.cpp', '.go', '.rs']:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Analyze Python files
                    if file_path.suffix.lower() == '.py':
                        self._analyze_python_file(content, str(file_path), critical_functions, core_functions, utility_functions, classes)
                    # Add other language analyzers here
                    
                except Exception:
                    continue
        
        return {
            'critical_functions': '\n'.join(critical_functions) if critical_functions else '*No critical functions detected*',
            'core_functions': '\n'.join(core_functions) if core_functions else '*No core functions detected*',
            'utility_functions': '\n'.join(utility_functions) if utility_functions else '*No utility functions detected*',
            'function_documentation': self._generate_function_documentation(critical_functions + core_functions + utility_functions),
            'class_documentation': '\n'.join(classes) if classes else '*No classes detected*'
        }
    
    def _analyze_python_file(self, content: str, file_path: str, critical_functions: List[str], 
                           core_functions: List[str], utility_functions: List[str], classes: List[str]) -> None:
        """Analyze a Python file for functions and classes."""
        import re
        
        # Find functions
        function_pattern = r'def\s+(\w+)\s*\([^)]*\)\s*:'
        functions = re.findall(function_pattern, content)
        
        # Find classes
        class_pattern = r'class\s+(\w+)'
        found_classes = re.findall(class_pattern, content)
        
        # Categorize functions based on name and context
        for func_name in functions:
            func_desc = f"- `{func_name}` in `{file_path}`"
            
            if any(keyword in func_name.lower() for keyword in ['main', 'init', 'setup', 'start', 'run', 'execute']):
                critical_functions.append(func_desc)
            elif any(keyword in func_name.lower() for keyword in ['get', 'set', 'create', 'update', 'delete', 'process']):
                core_functions.append(func_desc)
            else:
                utility_functions.append(func_desc)
        
        # Add classes
        for class_name in found_classes:
            classes.append(f"- `{class_name}` in `{file_path}`")
    
    def _generate_function_documentation(self, functions: List[str]) -> str:
        """Generate function documentation."""
        if not functions:
            return '*No functions documented*'
        
        return '\n'.join(functions[:20])  # Limit to first 20 functions
    
    def _analyze_file_statistics(self, files: List[Path]) -> Dict[str, Any]:
        """Analyze file statistics."""
        total_files = len(files)
        total_lines = 0
        total_size = 0
        file_types = {}
        
        # Handle empty file list
        if total_files == 0:
            return {
                'file_statistics': 'No files found to analyze',
                'code_quality_metrics': 'No files analyzed',
                'performance_metrics': 'No files found'
            }
        
        for file_path in files:
            try:
                # Get file size
                size = file_path.stat().st_size
                total_size += size
                
                # Count lines
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = len(f.readlines())
                    total_lines += lines
                
                # Count file types
                ext = file_path.suffix.lower()
                file_types[ext] = file_types.get(ext, 0) + 1
                
            except Exception:
                continue
        
        # Calculate metrics
        avg_lines_per_file = total_lines / total_files if total_files > 0 else 0
        avg_size_per_file = total_size / total_files if total_files > 0 else 0
        
        # Calculate code density safely
        code_density = (total_lines / total_size * 1000) if total_size > 0 else 0
        
        return {
            'file_statistics': f"""Total Files: {total_files}
Total Lines: {total_lines:,}
Total Size: {total_size / 1024:.1f} KB
Average Lines per File: {avg_lines_per_file:.1f}
Average Size per File: {avg_size_per_file / 1024:.1f} KB

File Types:
{chr(10).join([f'- {ext}: {count} files' for ext, count in sorted(file_types.items())])}""",
            'code_quality_metrics': f"""Lines of Code: {total_lines:,}
Files Analyzed: {total_files}
Code Density: {code_density:.1f} lines/KB""",
            'performance_metrics': f"""Project Size: {total_size / 1024:.1f} KB
File Count: {total_files}
Complexity: {'High' if total_lines > 10000 else 'Medium' if total_lines > 1000 else 'Low'}"""
        }
