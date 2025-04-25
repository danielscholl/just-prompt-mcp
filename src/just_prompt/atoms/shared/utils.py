"""
Utility functions for just-prompt.
"""

from typing import Tuple, List
import os
import re
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Load environment variables
load_dotenv()

# Default model constants
DEFAULT_MODEL = "anthropic:claude-3-7-sonnet-20250219"


def split_provider_and_model(model_string: str) -> Tuple[str, str]:
    """
    Split a model string into provider and model name.
    
    Note: This only splits the first colon in the model string and leaves the rest of the string
    as the model name. Models will have additional colons in the string and we want to ignore them
    and leave them for the model name.
    
    Args:
        model_string: String in format "provider:model"
        
    Returns:
        Tuple containing (provider, model)
    """
    parts = model_string.split(":", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid model string format: {model_string}. Expected format: 'provider:model'")
    
    provider, model = parts
    return provider, model


def parse_reasoning_effort(model: str) -> Tuple[str, str]:
    """
    Parse a model name to check for reasoning effort levels.
    Only works with supported OpenAI models (o3-mini, o4-mini, o3, etc.).
    
    Supported formats:
    - model:low, model:medium, model:high
    
    Args:
        model: The model name potentially with a reasoning effort suffix
        
    Returns:
        Tuple of (base_model_name, reasoning_effort)
        If no reasoning suffix is found, reasoning_effort will be None
    """
    pattern = r'^(.+?)(?::(.+))?$'
    match = re.match(pattern, model)
    
    if not match:
        return model, None
    
    base_model = match.group(1)
    reasoning_suffix = match.group(2)
    
    if not reasoning_suffix:
        return base_model, None
        
    # Only accept low, medium, high for the reasoning suffix
    if reasoning_suffix.lower() in ['low', 'medium', 'high']:
        return base_model, reasoning_suffix.lower()
    
    # If suffix doesn't match expected values, ignore it
    return base_model, None


def get_provider_from_prefix(prefix: str) -> str:
    """
    Get the full provider name from a prefix.
    
    Args:
        prefix: Provider prefix (short or full name)
        
    Returns:
        Full provider name
    """
    from .data_types import ModelProviders
    
    provider = ModelProviders.from_name(prefix)
    if provider is None:
        raise ValueError(f"Unknown provider prefix: {prefix}")
    
    return provider.full_name


def get_models_prefixed_by_provider(provider_prefix: str, model_name: str) -> str:
    """
    Format a model string with provider prefix.
    
    Args:
        provider_prefix: The provider prefix (short or full name)
        model_name: The model name
        
    Returns:
        Formatted string in "provider:model" format
    """
    provider = get_provider_from_prefix(provider_prefix)
    return f"{provider}:{model_name}"


def get_api_key(provider: str) -> str:
    """
    Get the API key for a provider from environment variables.
    
    Args:
        provider: Provider name (full name)
        
    Returns:
        API key as string
    """
    key_mapping = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "gemini": "GEMINI_API_KEY",
        "groq": "GROQ_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY"
    }
    
    env_var = key_mapping.get(provider)
    if not env_var:
        return None
    
    return os.environ.get(env_var)