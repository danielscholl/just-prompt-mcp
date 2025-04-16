"""
OpenAI provider implementation.
"""

import os
from openai import OpenAI
from typing import List
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def prompt(text: str, model: str) -> str:
    """
    Send a prompt to OpenAI and get a response.

    Args:
        text: The prompt text
        model: The model name

    Returns:
        Response string from the model
    """
    try:
        logger.info(f"Sending prompt to OpenAI model: {model}")
        response = client.chat.completions.create(
            model=model,
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
