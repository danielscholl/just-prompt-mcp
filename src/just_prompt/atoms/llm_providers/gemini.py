"""
Google Gemini provider implementation.
"""

import os
import re
from typing import List, Tuple
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Try different import approaches for google.genai
# Note: There are two different packages that provide Google Gemini functionality:
# 1. google-genai: Using "from google import genai" approach (newer Client API)
# 2. google-generativeai: Using "import google.generativeai as genai" approach (older API)
# We support both to ensure compatibility in different environments
try:
    # First try the google-genai package approach with Client API
    from google import genai
    logger.info("Successfully imported from google import genai")
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    USE_CLIENT_API = True
except ImportError:
    try:
        # Fallback to google.generativeai package
        import google.generativeai as genai
        logger.info("Successfully imported google.generativeai")
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
        USE_CLIENT_API = False
    except ImportError:
        logger.error("Failed to import any Gemini module")
        # If neither package is available, log a clear error message
        raise ImportError("Failed to import Google Gemini APIs. Make sure either 'google-genai' or 'google-generativeai' package is installed.")

# Models that support thinking_budget
THINKING_ENABLED_MODELS = ["gemini-2.5-flash-preview-04-17"]


def parse_thinking_suffix(model: str) -> Tuple[str, int]:
    """
    Parse a model name to check for thinking token budget suffixes.
    Only works with the models in THINKING_ENABLED_MODELS.
    
    Supported formats:
    - model:1k, model:4k, model:24k
    - model:1000, model:1054, model:24576, etc. (any value between 0-24576)
    
    Args:
        model: The model name potentially with a thinking suffix
        
    Returns:
        Tuple of (base_model_name, thinking_budget)
        If no thinking suffix is found, thinking_budget will be 0
    """
    # Look for patterns like ":1k", ":4k", ":24k" or ":1000", ":1054", etc.
    pattern = r'^(.+?)(?::(.+))?$'
    match = re.match(pattern, model)
    
    if not match:
        return model, 0
    
    base_model = match.group(1)
    thinking_suffix = match.group(2)
    
    # Validate the model - only supported models get thinking
    if base_model not in THINKING_ENABLED_MODELS:
        logger.warning(f"Model {model} does not support thinking, ignoring thinking suffix")
        return base_model, 0
    
    if not thinking_suffix:
        return base_model, 0
    
    # Handle valid numeric thinking budgets
    if thinking_suffix and re.match(r'^\d+k?$', thinking_suffix):
        try:
            # Remove 'k' suffix if present and convert to int
            if thinking_suffix.endswith('k'):
                thinking_budget = int(thinking_suffix[:-1]) * 1024
            else:
                thinking_budget = int(thinking_suffix)
                
            # If a small number like 1, 4, 16 is provided without 'k', assume it's in "k"
            if thinking_budget < 100:
                thinking_budget *= 1024
                
            # Adjust values outside the range
            if thinking_budget < 0:
                logger.warning(f"Thinking budget {thinking_budget} below minimum (0), using 0 instead")
                thinking_budget = 0
            elif thinking_budget > 24576:
                logger.warning(f"Thinking budget {thinking_budget} above maximum (24576), using 24576 instead")
                thinking_budget = 24576
                
            logger.info(f"Using thinking budget of {thinking_budget} tokens for model {base_model}")
            return base_model, thinking_budget
        except ValueError:
            logger.warning(f"Invalid thinking budget format: {thinking_suffix}, ignoring")
            return base_model, 0
    else:
        # Handle invalid thinking suffixes
        if thinking_suffix:
            logger.warning(f"Invalid thinking budget format: {thinking_suffix}, ignoring")
        return base_model, 0


def prompt_with_thinking(text: str, model: str, thinking_budget: int) -> str:
    """
    Send a prompt to Google Gemini with thinking enabled and get a response.
    
    Args:
        text: The prompt text
        model: The base model name (without thinking suffix)
        thinking_budget: The token budget for thinking
        
    Returns:
        Response string from the model
    """
    try:
        logger.info(f"Sending prompt to Gemini model {model} with thinking budget {thinking_budget}")
        
        if USE_CLIENT_API:
            # Using google-genai Client API
            response = client.models.generate_content(
                model=model,
                contents=text,
                config=genai.types.GenerateContentConfig(
                    thinking_config=genai.types.ThinkingConfig(
                        thinking_budget=thinking_budget
                    )
                )
            )
        else:
            # Using google.generativeai API
            gemini_model = genai.GenerativeModel(model_name=model)
            response = gemini_model.generate_content(
                text,
                generation_config=genai.GenerationConfig(
                    # The old API may not support thinking_config directly
                    # This is a placeholder - actual implementation may vary
                    # depending on the API version
                )
            )
        
        return response.text
    except Exception as e:
        logger.error(f"Error sending prompt with thinking to Gemini: {e}")
        raise ValueError(f"Failed to get response from Gemini with thinking: {str(e)}")


def prompt(text: str, model: str) -> str:
    """
    Send a prompt to Google Gemini and get a response.
    
    Automatically handles thinking suffixes in the model name (e.g., gemini-2.5-flash-preview-04-17:4k)
    
    Args:
        text: The prompt text
        model: The model name, optionally with thinking suffix
        
    Returns:
        Response string from the model
    """
    # Parse the model name to check for thinking suffixes
    base_model, thinking_budget = parse_thinking_suffix(model)
    
    # If thinking budget is specified, use prompt_with_thinking
    if thinking_budget > 0:
        return prompt_with_thinking(text, base_model, thinking_budget)
    
    # Otherwise, use regular prompt
    try:
        logger.info(f"Sending prompt to Gemini model: {base_model}")
        
        if USE_CLIENT_API:
            # Using google-genai Client API
            response = client.models.generate_content(
                model=base_model,
                contents=text
            )
        else:
            # Using google.generativeai API
            gemini_model = genai.GenerativeModel(model_name=base_model)
            response = gemini_model.generate_content(text)
        
        return response.text
    except Exception as e:
        logger.error(f"Error sending prompt to Gemini: {e}")
        raise ValueError(f"Failed to get response from Gemini: {str(e)}")


def list_models() -> List[str]:
    """
    List available Google Gemini models.
    
    Returns:
        List of model names
    """
    try:
        logger.info("Listing Gemini models")
        
        # Get the list of models
        models = []
        
        if USE_CLIENT_API:
            # Using google-genai Client API
            available_models = client.list_models()
            for m in available_models:
                if "generateContent" in m.supported_generation_methods:
                    models.append(m.name)
        else:
            # Using google.generativeai API
            for m in genai.list_models():
                if "generateContent" in m.supported_generation_methods:
                    models.append(m.name)
                
        # Format model names - strip the "models/" prefix if present
        formatted_models = [model.replace("models/", "") for model in models]
        
        return formatted_models
    except Exception as e:
        logger.error(f"Error listing Gemini models: {e}")
        # Return some known models if API fails
        logger.info("Returning hardcoded list of known Gemini models")
        return [
            "gemini-2.5-flash-preview-04-17",
            "gemini-2.5-pro-preview-03-25"
        ]