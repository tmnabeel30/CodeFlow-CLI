"""Configuration management for Groq CLI Agent."""

import os
import yaml
from pathlib import Path
from typing import Optional, Dict, Any


class ConfigurationManager:
    """Manages user configuration and API settings."""
    
    def __init__(self, config_dir: Optional[str] = None):
        """Initialize configuration manager.
        
        Args:
            config_dir: Directory to store configuration files. Defaults to ~/.groq
        """
        if config_dir is None:
            config_dir = os.path.expanduser("~/.groq")
        
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "config.yaml"
        self._ensure_config_dir()
        self._config = self._load_config()
    
    def _ensure_config_dir(self) -> None:
        """Ensure configuration directory exists."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if not self.config_file.exists():
            return self._get_default_config()
        
        try:
            with open(self.config_file, 'r') as f:
                config = yaml.safe_load(f) or {}
                # Merge with defaults to ensure all keys exist
                default_config = self._get_default_config()
                default_config.update(config)
                return default_config
        except (yaml.YAMLError, IOError) as e:
            print(f"Warning: Could not load config file: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "api_key": "",
            "default_model": "llama-2-70B",
            "interactive_mode": True,
            "theme": "default",
            "max_history": 200,
            "auto_save": True,
            "codeflow_first_run": True
        }
    
    def _save_config(self) -> None:
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                yaml.dump(self._config, f, default_flow_style=False)
        except IOError as e:
            print(f"Warning: Could not save config file: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key doesn't exist
            
        Returns:
            Configuration value
        """
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value.
        
        Args:
            key: Configuration key
            value: Value to set
        """
        self._config[key] = value
        self._save_config()
    
    def get_api_key(self) -> Optional[str]:
        """Get API key from config or environment."""
        # First try config file
        api_key = self.get("api_key")
        if api_key:
            return api_key
        
        # Then try environment variable
        return os.getenv("GROQ_API_KEY")
    
    def set_api_key(self, api_key: str) -> None:
        """Set API key in configuration."""
        self.set("api_key", api_key)
    
    def get_default_model(self) -> str:
        """Get default model from configuration."""
        return self.get("default_model", "llama-2-70B")
    
    def set_default_model(self, model: str) -> None:
        """Set default model in configuration."""
        self.set("default_model", model)
    
    def is_interactive_mode(self) -> bool:
        """Check if interactive mode is enabled."""
        return self.get("interactive_mode", True)
    
    def set_interactive_mode(self, enabled: bool) -> None:
        """Set interactive mode setting."""
        self.set("interactive_mode", enabled)
    
    def get_theme(self) -> str:
        """Get current theme setting."""
        return self.get("theme", "default")
    
    def get_max_history(self) -> int:
        """Get maximum chat history length."""
        return self.get("max_history", 100)
    
    def is_auto_save(self) -> bool:
        """Check if auto-save is enabled."""
        return self.get("auto_save", True)


