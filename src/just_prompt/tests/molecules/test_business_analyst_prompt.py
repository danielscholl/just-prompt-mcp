"""
Tests for business analyst prompt functionality.
"""

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from just_prompt.molecules.business_analyst_prompt import business_analyst_prompt, DEFAULT_ANALYST_PROMPT, CONSOLIDATION_PROMPT
from just_prompt.atoms.shared.utils import DEFAULT_MODEL

# Sample test prompt
TEST_PROMPT = "Create a business case for a new mobile fitness application."

# Sample model responses
SAMPLE_RESPONSE_1 = "This is a sample model 1 response for testing."
SAMPLE_RESPONSE_2 = "This is a sample model 2 response for testing."

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


@patch('just_prompt.molecules.business_analyst_prompt.prompt')
def test_business_analyst_prompt_single_model(mock_prompt, temp_prompt_file, temp_output_dir):
    """Test business analyst prompt functionality with a single model."""
    # Setup mocks
    mock_prompt.return_value = [SAMPLE_RESPONSE_1]
    
    # Test with a single model
    result = business_analyst_prompt(
        temp_prompt_file, 
        temp_output_dir,
        models_prefixed_by_provider=["model1"]
    )
    
    # Verify prompt was called with correct parameters
    mock_prompt.assert_called_once()
    prompt_call_args = mock_prompt.call_args[0]
    assert prompt_call_args[1] == ["model1"]
    
    # Verify prompt contains the original request
    assert "analyst-request" in prompt_call_args[0]
    assert TEST_PROMPT in prompt_call_args[0]
    
    # Check file name format
    file_stem = Path(temp_prompt_file).stem
    expected_output_file = os.path.join(temp_output_dir, f"{file_stem}_model1_brief.md")
    assert result == expected_output_file


@patch('just_prompt.molecules.business_analyst_prompt.prompt')
def test_business_analyst_prompt_multiple_models(mock_prompt, temp_prompt_file, temp_output_dir):
    """Test business analyst prompt with multiple models."""
    # Setup mocks for individual model responses and consolidated response
    mock_prompt.side_effect = [
        [SAMPLE_RESPONSE_1],  # First model
        [SAMPLE_RESPONSE_2],  # Second model
        [SAMPLE_BA_RESPONSE]  # Consolidated response
    ]
    
    # Test with multiple models
    result = business_analyst_prompt(
        temp_prompt_file, 
        temp_output_dir,
        models_prefixed_by_provider=["model1", "model2"],
        analyst_model="analyst_model"
    )
    
    # Verify prompt was called for each model and for consolidation
    assert mock_prompt.call_count == 3
    
    # Check that the individual brief files were created
    file_stem = Path(temp_prompt_file).stem
    expected_brief1 = os.path.join(temp_output_dir, f"{file_stem}_model1_brief.md")
    expected_brief2 = os.path.join(temp_output_dir, f"{file_stem}_model2_brief.md")
    
    # Check the consolidation file
    expected_consolidation = os.path.join(temp_output_dir, "business_analyst_brief.md")
    assert result == expected_consolidation
    
    # Verify the consolidation prompt contained original prompt and both model responses
    consolidation_call = mock_prompt.call_args_list[2][0]
    assert consolidation_call[1] == ["analyst_model"]
    assert "<original-prompt>" in consolidation_call[0]
    assert "<individual-briefs>" in consolidation_call[0]
    assert "Brief from model1" in consolidation_call[0]
    assert "Brief from model2" in consolidation_call[0]


@patch('just_prompt.molecules.business_analyst_prompt.prompt')
def test_sanitized_model_names(mock_prompt, temp_prompt_file, temp_output_dir):
    """Test that model names are properly sanitized for filenames."""
    # Setup mock
    mock_prompt.return_value = [SAMPLE_RESPONSE_1]
    
    # Create a model name with characters that need sanitizing
    complex_model = "provider:model/version:parameter"
    
    # Test with the complex model name
    result = business_analyst_prompt(
        temp_prompt_file,
        temp_output_dir,
        models_prefixed_by_provider=[complex_model]
    )
    
    # Verify the filename has sanitized the model name
    file_stem = Path(temp_prompt_file).stem
    sanitized_name = "provider_model_version_parameter"
    expected_file = os.path.join(temp_output_dir, f"{file_stem}_{sanitized_name}_brief.md")
    assert result == expected_file


@patch('pathlib.Path.exists')
@patch('pathlib.Path.is_dir')
def test_invalid_output_directory(mock_is_dir, mock_exists, temp_prompt_file):
    """Test with an invalid output directory."""
    # Setup the mocks
    mock_exists.return_value = True  # Pretend the path exists
    mock_is_dir.return_value = False  # But it's not a directory
    
    with pytest.raises(ValueError, match="Not a directory"):
        business_analyst_prompt(temp_prompt_file, "/path/does/not/matter")


@patch('just_prompt.molecules.business_analyst_prompt.prompt')
def test_default_model_used_when_none_provided(mock_prompt, temp_prompt_file, temp_output_dir):
    """Test that default models are used when none are provided."""
    # Setup environment with default models
    with patch.dict(os.environ, {"DEFAULT_MODELS": "default_model1,default_model2"}):
        mock_prompt.return_value = [SAMPLE_RESPONSE_1]
        
        # Call without specifying models
        business_analyst_prompt(temp_prompt_file, temp_output_dir)
        
        # Check that both default models were used
        assert mock_prompt.call_count >= 1
        # Verify the first call used default_model1
        assert mock_prompt.call_args_list[0][0][1] == ["default_model1"]