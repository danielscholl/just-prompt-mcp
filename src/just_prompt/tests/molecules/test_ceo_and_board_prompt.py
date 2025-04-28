"""
Tests for the CEO and board prompt functionality.
"""

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from just_prompt.molecules.ceo_and_board_prompt import ceo_and_board_prompt


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield tmpdirname


@pytest.fixture
def prompt_file():
    """Create a temporary prompt file."""
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=False) as tmp:
        tmp.write("What is the best strategy for our company's growth?")
        tmp_path = tmp.name
    
    yield tmp_path
    os.unlink(tmp_path)


@patch('just_prompt.molecules.ceo_and_board_prompt.prompt_from_file_to_file')
@patch('just_prompt.molecules.ceo_and_board_prompt.prompt')
def test_ceo_and_board_prompt(mock_prompt, mock_prompt_from_file_to_file, temp_dir, prompt_file):
    """Test the ceo_and_board_prompt function."""
    # Setup test data
    test_models = ["model1", "model2"]
    ceo_model = "ceo_model"
    
    # Create mock response files
    response_file1 = os.path.join(temp_dir, "prompt_model1.md")
    response_file2 = os.path.join(temp_dir, "prompt_model2.md")
    
    with open(response_file1, 'w') as f:
        f.write("Response from model 1")
    with open(response_file2, 'w') as f:
        f.write("Response from model 2")
    
    # Mock the prompt_from_file_to_file function
    mock_prompt_from_file_to_file.return_value = [response_file1, response_file2]
    
    # Mock the prompt function (CEO response)
    mock_prompt.return_value = ["CEO's final decision"]
    
    # Call the function under test
    result = ceo_and_board_prompt(
        prompt_file, 
        output_dir=temp_dir,
        models_prefixed_by_provider=test_models,
        ceo_model=ceo_model
    )
    
    # Verify prompt_from_file_to_file was called correctly
    mock_prompt_from_file_to_file.assert_called_once_with(
        prompt_file, 
        test_models, 
        temp_dir
    )
    
    # Verify prompt was called with the correct CEO prompt
    mock_prompt.assert_called_once()
    # The CEO prompt is complex, so we just check that it contains key elements
    ceo_prompt_arg = mock_prompt.call_args[0][0]
    assert "<purpose>" in ceo_prompt_arg
    assert "<original-question>" in ceo_prompt_arg
    assert "<board-decisions>" in ceo_prompt_arg
    assert "<model-name>model1</model-name>" in ceo_prompt_arg
    assert "<model-name>model2</model-name>" in ceo_prompt_arg
    
    # Verify CEO decision file was created
    ceo_decision_file = os.path.join(temp_dir, "ceo_decision.md")
    assert result == ceo_decision_file
    assert os.path.exists(ceo_decision_file)
    
    # Verify CEO decision content
    with open(ceo_decision_file, 'r') as f:
        content = f.read()
        assert content == "CEO's final decision"


@patch('just_prompt.molecules.ceo_and_board_prompt.prompt_from_file_to_file')
@patch('just_prompt.molecules.ceo_and_board_prompt.prompt')
def test_ceo_and_board_prompt_with_defaults(mock_prompt, mock_prompt_from_file_to_file, temp_dir, prompt_file):
    """Test the ceo_and_board_prompt function with default parameters."""
    # Setup environment variable for default models
    os.environ["DEFAULT_MODELS"] = "default_model1,default_model2"
    
    # Create mock response files
    response_file1 = os.path.join(temp_dir, "prompt_default_model1.md")
    response_file2 = os.path.join(temp_dir, "prompt_default_model2.md")
    
    with open(response_file1, 'w') as f:
        f.write("Response from default model 1")
    with open(response_file2, 'w') as f:
        f.write("Response from default model 2")
    
    # Mock the prompt_from_file_to_file function
    mock_prompt_from_file_to_file.return_value = [response_file1, response_file2]
    
    # Mock the prompt function (CEO response)
    mock_prompt.return_value = ["CEO's final decision with defaults"]
    
    # Call the function under test with default parameters
    result = ceo_and_board_prompt(
        prompt_file, 
        output_dir=temp_dir
    )
    
    # Verify prompt_from_file_to_file was called with None for models
    mock_prompt_from_file_to_file.assert_called_once_with(
        prompt_file, 
        None, 
        temp_dir
    )
    
    # Verify prompt was called with the default CEO model
    mock_prompt.assert_called_once()
    model_arg = mock_prompt.call_args[0][1]
    assert model_arg == ["openai:o3"]
    
    # Verify CEO decision file was created
    ceo_decision_file = os.path.join(temp_dir, "ceo_decision.md")
    assert result == ceo_decision_file
    assert os.path.exists(ceo_decision_file)
    
    # Verify CEO decision content
    with open(ceo_decision_file, 'r') as f:
        content = f.read()
        assert content == "CEO's final decision with defaults"
    
    # Clean up environment
    del os.environ["DEFAULT_MODELS"]