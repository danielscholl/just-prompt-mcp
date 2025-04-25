"""
OpenAI provider implementation.
"""

import os
from openai import OpenAI
from typing import List
import logging
from dotenv import load_dotenv
from ..shared.utils import parse_reasoning_effort

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Models that support reasoning effort
REASONING_ENABLED_MODELS = ["o3-mini", "o4-mini", "o3"]


def prompt_with_reasoning(text: str, model: str, reasoning_effort: str) -> str:
    """
    Send a prompt to OpenAI with reasoning effort level and get a response.

    Args:
        text: The prompt text
        model: The base model name (without reasoning effort suffix)
        reasoning_effort: The reasoning effort level (low, medium, high)
        
    Returns:
        Response string from the model
    """
    try:
        logger.info(f"Sending prompt to OpenAI model {model} with reasoning effort level {reasoning_effort}")
        response = client.chat.completions.create(
            model=model,
            reasoning_effort=reasoning_effort,
            messages=[{"role": "user", "content": text}],
        )

        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error sending prompt with reasoning to OpenAI: {e}")
        raise ValueError(f"Failed to get response from OpenAI with reasoning: {str(e)}")


def prompt(text: str, model: str) -> str:
    """
    Send a prompt to OpenAI and get a response.
    
    Automatically handles reasoning effort suffixes in the model name (e.g., o3-mini:low)

    Args:
        text: The prompt text
        model: The model name, optionally with reasoning effort suffix

    Returns:
        Response string from the model
    """
    # Parse the model name to check for reasoning effort suffixes
    base_model, reasoning_effort = parse_reasoning_effort(model)
    
    # Check if model supports reasoning effort
    if reasoning_effort and base_model in REASONING_ENABLED_MODELS:
        return prompt_with_reasoning(text, base_model, reasoning_effort)
    elif reasoning_effort and base_model not in REASONING_ENABLED_MODELS:
        logger.warning(f"Model {base_model} does not support reasoning effort, ignoring reasoning suffix")
    
    # Otherwise, use regular prompt
    try:
        logger.info(f"Sending prompt to OpenAI model: {base_model}")
        response = client.chat.completions.create(
            model=base_model,
            messages=[{"role": "user", "content": text}],
        )

        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error sending prompt to OpenAI: {e}")
        raise ValueError(f"Failed to get response from OpenAI: {str(e)}")


def list_models() -> List[str]:
    """
    List available OpenAI models.

    Returns:
        List of model names
    """
    try:
        logger.info("Listing OpenAI models")
        response = client.models.list()

        # Return all models without filtering
        models = [model.id for model in response.data]

        return models
    except Exception as e:
        logger.error(f"Error listing OpenAI models: {e}")
        raise ValueError(f"Failed to list OpenAI models: {str(e)}")
