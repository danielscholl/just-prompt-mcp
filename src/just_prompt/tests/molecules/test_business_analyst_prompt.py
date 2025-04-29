"""
Tests for business analyst prompt functionality.
"""

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from just_prompt.molecules.business_analyst_prompt import business_analyst_prompt, DEFAULT_ANALYST_PROMPT
from just_prompt.atoms.shared.utils import DEFAULT_MODEL

# Sample test prompt
TEST_PROMPT = "Create a business case for a new mobile fitness application."

# Sample model response
SAMPLE_RESPONSE = "This is a sample model response for testing."

# Sample business analyst response
SAMPLE_BA_RESPONSE = """
# Business Case: Mobile Fitness Application

## Executive Summary
This document outlines the business case for developing a new mobile fitness application...
"""


@pytest.fixture
def temp_prompt_file():
    """Create a temporary prompt file for testing."""
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.txt') as f:
        f.write(TEST_PROMPT)
        temp_file_path = f.name
    
    yield temp_file_path
    
    # Clean up
    if os.path.exists(temp_file_path):
        os.remove(temp_file_path)


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@patch('just_prompt.molecules.business_analyst_prompt.prompt_from_file_to_file')
@patch('just_prompt.molecules.business_analyst_prompt.prompt')
def test_business_analyst_prompt(mock_prompt, mock_prompt_from_file_to_file, temp_prompt_file, temp_output_dir):
    """Test business analyst prompt functionality."""
    # Setup mocks
    mock_response_file = os.path.join(temp_output_dir, "response_file.md")
    with open(mock_response_file, 'w') as f:
        f.write(SAMPLE_RESPONSE)
    
    mock_prompt_from_file_to_file.return_value = [mock_response_file]
    mock_prompt.return_value = [SAMPLE_BA_RESPONSE]
    
    # Test with default parameters
    result = business_analyst_prompt(temp_prompt_file, temp_output_dir)
    
    # Verify prompt_from_file_to_file was called correctly
    mock_prompt_from_file_to_file.assert_called_once_with(
        temp_prompt_file, 
        None, 
        temp_output_dir
    )
    
    # Verify prompt was called with correct template
    prompt_call_args = mock_prompt.call_args[0]
    assert prompt_call_args[1] == ["openai:o3"]  # Default analyst model
    
    # Verify prompt contains the original request
    assert TEST_PROMPT in prompt_call_args[0]
    
    # Verify research material is included
    assert "<research-material>" in prompt_call_args[0]
    assert SAMPLE_RESPONSE in prompt_call_args[0]
    
    # Check that the output file was created
    expected_output_file = os.path.join(temp_output_dir, "business_analyst_brief.md")
    assert result == expected_output_file
    assert os.path.exists(expected_output_file)
    
    # Verify content of output file
    with open(expected_output_file, 'r') as f:
        content = f.read()
        assert content == SAMPLE_BA_RESPONSE


@patch('just_prompt.molecules.business_analyst_prompt.prompt_from_file_to_file')
@patch('just_prompt.molecules.business_analyst_prompt.prompt')
def test_business_analyst_prompt_with_custom_model(mock_prompt, mock_prompt_from_file_to_file, temp_prompt_file, temp_output_dir):
    """Test business analyst prompt with custom model and parameters."""
    # Setup mocks
    mock_response_file = os.path.join(temp_output_dir, "response_file.md")
    with open(mock_response_file, 'w') as f:
        f.write(SAMPLE_RESPONSE)
    
    mock_prompt_from_file_to_file.return_value = [mock_response_file]
    mock_prompt.return_value = [SAMPLE_BA_RESPONSE]
    
    custom_models = ["anthropic:claude-3-7-sonnet-20250219"]
    custom_analyst_model = "openai:o4-mini"
    
    # Test with custom parameters
    result = business_analyst_prompt(
        temp_prompt_file, 
        temp_output_dir,
        models_prefixed_by_provider=custom_models,
        analyst_model=custom_analyst_model
    )
    
    # Verify prompt_from_file_to_file was called with custom models
    mock_prompt_from_file_to_file.assert_called_once_with(
        temp_prompt_file, 
        custom_models, 
        temp_output_dir
    )
    
    # Verify prompt was called with custom analyst model
    prompt_call_args = mock_prompt.call_args[0]
    assert prompt_call_args[1] == [custom_analyst_model]
    
    # Check that the output file was created
    expected_output_file = os.path.join(temp_output_dir, "business_analyst_brief.md")
    assert result == expected_output_file
    assert os.path.exists(expected_output_file)


@patch('pathlib.Path.exists')
@patch('pathlib.Path.is_dir')
def test_invalid_output_directory(mock_is_dir, mock_exists, temp_prompt_file):
    """Test with an invalid output directory."""
    # Setup the mocks
    mock_exists.return_value = True  # Pretend the path exists
    mock_is_dir.return_value = False  # But it's not a directory
    
    with pytest.raises(ValueError, match="Not a directory"):
        business_analyst_prompt(temp_prompt_file, "/path/does/not/matter")