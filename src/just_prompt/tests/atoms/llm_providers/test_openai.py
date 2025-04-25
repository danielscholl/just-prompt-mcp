"""
Tests for OpenAI provider.
"""

import pytest
import os
from dotenv import load_dotenv
from just_prompt.atoms.llm_providers import openai
from just_prompt.atoms.shared.utils import parse_reasoning_effort

# Load environment variables
load_dotenv()

# Skip tests if API key not available
if not os.environ.get("OPENAI_API_KEY"):
    pytest.skip("OpenAI API key not available", allow_module_level=True)


def test_list_models():
    """Test listing OpenAI models."""
    models = openai.list_models()
    
    # Assertions
    assert isinstance(models, list)
    assert len(models) > 0
    assert all(isinstance(model, str) for model in models)
    
    # Check for at least one expected model
    gpt_models = [model for model in models if "gpt" in model.lower()]
    assert len(gpt_models) > 0, "No GPT models found"


def test_parse_reasoning_effort():
    """Test parsing reasoning effort from model name."""
    # Test with model name only
    base_model, reasoning_effort = parse_reasoning_effort("o3-mini")
    assert base_model == "o3-mini"
    assert reasoning_effort is None
    
    # Test with low reasoning effort
    base_model, reasoning_effort = parse_reasoning_effort("o3-mini:low")
    assert base_model == "o3-mini"
    assert reasoning_effort == "low"
    
    # Test with medium reasoning effort
    base_model, reasoning_effort = parse_reasoning_effort("o4-mini:medium")
    assert base_model == "o4-mini"
    assert reasoning_effort == "medium"
    
    # Test with high reasoning effort
    base_model, reasoning_effort = parse_reasoning_effort("o3:high")
    assert base_model == "o3"
    assert reasoning_effort == "high"
    
    # Test with invalid reasoning effort
    base_model, reasoning_effort = parse_reasoning_effort("o3-mini:invalid")
    assert base_model == "o3-mini"
    assert reasoning_effort is None
    
    # Test with capitalized reasoning effort (should be normalized)
    base_model, reasoning_effort = parse_reasoning_effort("o3-mini:HIGH")
    assert base_model == "o3-mini"
    assert reasoning_effort == "high"


def test_prompt():
    """Test sending prompt to OpenAI."""
    response = openai.prompt("What is the capital of France?", "gpt-4o-mini")
    
    # Assertions
    assert isinstance(response, str)
    assert len(response) > 0
    assert "paris" in response.lower() or "Paris" in response


def test_prompt_with_reasoning():
    """Test sending prompt to OpenAI with reasoning effort."""
    # Use a simple math problem that benefits from reasoning
    prompt = "What is 15 × 17?"
    
    # Test with different reasoning levels
    for reasoning_level in ["low", "medium", "high"]:
        model = f"o4-mini:{reasoning_level}"
        response = openai.prompt(prompt, model)
        
        # Check that we got a valid response
        assert isinstance(response, str)
        assert len(response) > 0
        
        # The correct answer should be 255
        assert "255" in response
    
    # Test with invalid reasoning level - should default to regular prompt
    response = openai.prompt(prompt, "o4-mini:invalid")
    assert isinstance(response, str)
    assert len(response) > 0