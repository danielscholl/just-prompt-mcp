"""
Tests for Gemini provider.
"""

import pytest
import os
import re
from dotenv import load_dotenv
from just_prompt.atoms.llm_providers import gemini

# Load environment variables
load_dotenv()

# Skip tests if API key not available
if not os.environ.get("GEMINI_API_KEY"):
    pytest.skip("Gemini API key not available", allow_module_level=True)


def test_list_models():
    """Test listing Gemini models."""
    models = gemini.list_models()
    
    # Assertions
    assert isinstance(models, list)
    assert len(models) > 0
    assert all(isinstance(model, str) for model in models)
    
    # Check for at least one expected model containing gemini
    gemini_models = [model for model in models if "gemini" in model.lower()]
    assert len(gemini_models) > 0, "No Gemini models found"


def test_prompt():
    """Test sending prompt to Gemini."""
    # Using a common gemini model for testing
    response = gemini.prompt("What is the capital of France?", "gemini-1.5-flash")
    
    # Assertions
    assert isinstance(response, str)
    assert len(response) > 0
    assert "paris" in response.lower() or "Paris" in response


def test_parse_thinking_suffix():
    """Test parsing thinking suffix from model name."""
    # Test with no suffix
    base_model, thinking_budget = gemini.parse_thinking_suffix("gemini-2.5-flash-preview-04-17")
    assert base_model == "gemini-2.5-flash-preview-04-17"
    assert thinking_budget == 0
    
    # Test with k suffix
    base_model, thinking_budget = gemini.parse_thinking_suffix("gemini-2.5-flash-preview-04-17:4k")
    assert base_model == "gemini-2.5-flash-preview-04-17"
    assert thinking_budget == 4096
    
    # Test with numeric suffix
    base_model, thinking_budget = gemini.parse_thinking_suffix("gemini-2.5-flash-preview-04-17:8000")
    assert base_model == "gemini-2.5-flash-preview-04-17"
    assert thinking_budget == 8000
    
    # Test with unsupported model
    base_model, thinking_budget = gemini.parse_thinking_suffix("gemini-1.5-flash:4k")
    assert base_model == "gemini-1.5-flash"
    assert thinking_budget == 0
    
    # Test with invalid suffix
    base_model, thinking_budget = gemini.parse_thinking_suffix("gemini-2.5-flash-preview-04-17:invalid")
    assert base_model == "gemini-2.5-flash-preview-04-17"
    assert thinking_budget == 0
    
    # Test with out of range values (should be clamped)
    base_model, thinking_budget = gemini.parse_thinking_suffix("gemini-2.5-flash-preview-04-17:30000")
    assert base_model == "gemini-2.5-flash-preview-04-17"
    assert thinking_budget == 24576  # Clamped to max value


@pytest.mark.skipif("gemini-2.5-flash-preview-04-17" not in gemini.list_models(), 
                   reason="gemini-2.5-flash-preview-04-17 model not available")
def test_prompt_with_thinking():
    """Test sending prompt to Gemini with thinking budget."""
    # Test with thinking budget
    response = gemini.prompt("What is the capital of France?", "gemini-2.5-flash-preview-04-17:1k")
    
    # Assertions
    assert isinstance(response, str)
    assert len(response) > 0
    assert "paris" in response.lower() or "Paris" in response