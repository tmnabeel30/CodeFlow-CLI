"""Tests for configuration management."""

import pytest
import tempfile
import os
from pathlib import Path
from groq_agent.config import ConfigurationManager


class TestConfigurationManager:
    """Test cases for ConfigurationManager."""
    
    def test_default_config(self):
        """Test default configuration values."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = ConfigurationManager(temp_dir)
            
            assert config.get("api_key") == ""
            assert config.get("default_model") == "llama-2-70B"
            assert config.get("interactive_mode") is True
            assert config.get("theme") == "default"
            assert config.get("max_history") == 200
            assert config.get("auto_save") is True
    
    def test_set_and_get(self):
        """Test setting and getting configuration values."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = ConfigurationManager(temp_dir)
            
            config.set("test_key", "test_value")
            assert config.get("test_key") == "test_value"
            
            config.set("number_key", 42)
            assert config.get("number_key") == 42
    
    def test_api_key_from_env(self):
        """Test API key retrieval from environment variable."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = ConfigurationManager(temp_dir)
            
            # Test with environment variable
            os.environ["GROQ_API_KEY"] = "test_api_key"
            api_key = config.get_api_key()
            assert api_key == "test_api_key"
            
            # Clean up
            del os.environ["GROQ_API_KEY"]
    
    def test_api_key_from_config(self):
        """Test API key retrieval from config file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = ConfigurationManager(temp_dir)
            
            # Set API key in config
            config.set_api_key("config_api_key")
            api_key = config.get_api_key()
            assert api_key == "config_api_key"
    
    def test_model_management(self):
        """Test model-related configuration methods."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = ConfigurationManager(temp_dir)
            
            # Test default model
            assert config.get_default_model() == "llama-2-70B"
            
            # Test setting model
            config.set_default_model("test-model")
            assert config.get_default_model() == "test-model"
    
    def test_interactive_mode(self):
        """Test interactive mode configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = ConfigurationManager(temp_dir)
            
            assert config.is_interactive_mode() is True
            
            config.set_interactive_mode(False)
            assert config.is_interactive_mode() is False


