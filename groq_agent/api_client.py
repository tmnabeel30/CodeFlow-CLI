"""Groq API client for the CLI agent."""

import groq
from typing import List, Dict, Any, Optional
from .config import ConfigurationManager


class GroqAPIClient:
    """Client for interacting with the Groq API."""
    
    def __init__(self, config: ConfigurationManager):
        """Initialize the API client.
        
        Args:
            config: Configuration manager instance
        """
        self.config = config
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize the Groq client with API key."""
        api_key = self.config.get_api_key()
        if not api_key:
            raise ValueError(
                "No API key found. Please set GROQ_API_KEY environment variable "
                "or configure it in ~/.groq/config.yaml"
            )
        
        self.client = groq.Groq(api_key=api_key)
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models from Groq API.
        
        Returns:
            List of model information dictionaries
        """
        try:
            models = self.client.models.list()
            return [
                {
                    "id": model.id,
                    "name": model.id,  # Use ID as name for consistency
                    "description": self._get_model_description(model.id),
                    "capabilities": self._get_model_capabilities(model.id)
                }
                for model in models.data
            ]
        except Exception as e:
            print(f"Error fetching models: {e}")
            # Return a fallback list of known models
            return self._get_fallback_models()
    
    def _get_model_description(self, model_id: str) -> str:
        """Get human-readable description for a model.
        
        Args:
            model_id: Model identifier
            
        Returns:
            Model description
        """
        descriptions = {
            "llama-2-70B": "High-performance 70B parameter model",
            "llama-3.1-8B": "Fast 8B parameter model for quick responses",
            "llama-3.1-70B": "High-capability 70B parameter model",
            "llama-3.1-405B": "Ultra-high-capability 405B parameter model",
            "mixtral-8x7b-32768": "Mixture of experts model with 32K context",
            "gemma-7b-it": "Google's Gemma 7B instruction-tuned model",
            "compound-beta": "Multi-tool, high-capability model",
            "compound-beta-mini": "Single-tool, low-latency model"
        }
        return descriptions.get(model_id, f"Model: {model_id}")
    
    def _get_model_capabilities(self, model_id: str) -> List[str]:
        """Get capabilities for a model.
        
        Args:
            model_id: Model identifier
            
        Returns:
            List of capabilities
        """
        capabilities = {
            "llama-2-70B": ["text-generation", "chat", "code-generation"],
            "llama-3.1-8B": ["text-generation", "chat", "fast-inference"],
            "llama-3.1-70B": ["text-generation", "chat", "code-generation", "reasoning"],
            "llama-3.1-405B": ["text-generation", "chat", "code-generation", "reasoning", "high-accuracy"],
            "mixtral-8x7b-32768": ["text-generation", "chat", "long-context"],
            "gemma-7b-it": ["text-generation", "chat", "instruction-following"],
            "compound-beta": ["text-generation", "chat", "multi-tool", "high-capability"],
            "compound-beta-mini": ["text-generation", "chat", "single-tool", "low-latency"]
        }
        return capabilities.get(model_id, ["text-generation", "chat"])
    
    def _get_fallback_models(self) -> List[Dict[str, Any]]:
        """Get fallback list of models when API call fails.
        
        Returns:
            List of fallback model information
        """
        return [
            {
                "id": "llama-2-70B",
                "name": "llama-2-70B",
                "description": "High-performance 70B parameter model",
                "capabilities": ["text-generation", "chat", "code-generation"]
            },
            {
                "id": "llama-3.1-8B",
                "name": "llama-3.1-8B",
                "description": "Fast 8B parameter model for quick responses",
                "capabilities": ["text-generation", "chat", "fast-inference"]
            },
            {
                "id": "compound-beta",
                "name": "compound-beta",
                "description": "Multi-tool, high-capability model",
                "capabilities": ["text-generation", "chat", "multi-tool", "high-capability"]
            }
        ]
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> Any:
        """Send chat completion request to Groq API.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Model to use for completion
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            
        Returns:
            Chat completion response
        """
        try:
            params = {
                "messages": messages,
                "model": model,
                "temperature": temperature,
                "stream": stream
            }
            
            if max_tokens:
                params["max_tokens"] = max_tokens
            
            return self.client.chat.completions.create(**params)
        
        except Exception as e:
            raise RuntimeError(f"Error in chat completion: {e}")
    
    def generate_code_suggestions(
        self,
        file_content: str,
        prompt: str,
        model: str,
        temperature: float = 0.3
    ) -> str:
        """Generate code suggestions for a file.
        
        Args:
            file_content: Current file content
            prompt: Prompt describing what changes to make
            model: Model to use for generation
            temperature: Sampling temperature
            
        Returns:
            Generated code suggestions
        """
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a helpful programming assistant. "
                    "Provide code suggestions and improvements. "
                    "Return only the modified code, not explanations. "
                    "Do NOT wrap your response in markdown code blocks (```). "
                    "Return the raw code content only."
                )
            },
            {
                "role": "user",
                "content": f"File content:\n{file_content}\n\nRequest: {prompt}"
            }
        ]
        
        try:
            response = self.chat_completion(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=4000
            )
            content = response.choices[0].message.content
            
            # Clean up markdown code blocks if present
            content = self._clean_markdown_code_blocks(content)
            
            return content
        except Exception as e:
            raise RuntimeError(f"Error generating code suggestions: {e}")

    def _clean_markdown_code_blocks(self, content: str) -> str:
        """Remove markdown code blocks from AI response.
        
        Args:
            content: Raw AI response content
            
        Returns:
            Cleaned content without markdown code blocks
        """
        import re
        
        # Remove markdown code blocks (```language ... ```)
        content = re.sub(r'```[a-zA-Z]*\n', '', content)
        content = re.sub(r'```\s*$', '', content)
        
        # Remove any leading/trailing whitespace
        content = content.strip()
        
        return content
    
    def validate_api_key(self) -> bool:
        """Validate that the API key is working.
        
        Returns:
            True if API key is valid, False otherwise
        """
        try:
            # Try to list models as a simple validation
            self.client.models.list()
            return True
        except Exception:
            return False
