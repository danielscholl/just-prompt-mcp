"""
CEO and board prompt functionality for just-prompt.
"""

from typing import List, Dict
import logging
import os
from pathlib import Path
import json

from .prompt_from_file_to_file import prompt_from_file_to_file
from .prompt import prompt
from ..atoms.shared.utils import DEFAULT_MODEL

logger = logging.getLogger(__name__)

# Default CEO model
DEFAULT_CEO_MODEL = "openai:o3"

# Default CEO decision prompt template
DEFAULT_CEO_DECISION_PROMPT = """
<purpose>
    You are a CEO of a company. You are given a list of responses from your board of directors. Your job is to take in the original question prompt, and each of the board members' responses, and choose the best direction for your company.
</purpose>
<instructions>
    <instruction>Each board member has proposed an answer to the question posed in the prompt.</instruction>
    <instruction>Given the original question prompt, and each of the board members' responses, choose the best answer.</instruction>
    <instruction>Tally the votes of the board members, choose the best direction, and explain why you chose it.</instruction>
    <instruction>To preserve anonymity, we will use model names instead of real names of your board members. When responding, use the model names in your response.</instruction>
    <instruction>As a CEO, you breakdown the decision into several categories including: risk, reward, timeline, and resources. In addition to these guiding categories, you also consider the board members' expertise and experience. As a bleeding edge CEO, you also invent new dimensions of decision making to help you make the best decision for your company.</instruction>
    <instruction>Your final CEO response should be in markdown format with a comprehensive explanation of your decision. Start the top of the file with a title that says "CEO Decision", include a table of contents, briefly describe the question/problem at hand then dive into several sections. One of your first sections should be a quick summary of your decision, then breakdown each of the boards decisions into sections with your commentary on each. Where we lead into your decision with the categories of your decision making process, and then we lead into your final decision.</instruction>
</instructions>
        
<original-question>{original_prompt}</original-question>
        
<board-decisions>
{board_responses}
</board-decisions>
"""


def ceo_and_board_prompt(
    from_file: str, 
    output_dir: str = ".", 
    models_prefixed_by_provider: List[str] = None,
    ceo_model: str = DEFAULT_CEO_MODEL,
    ceo_decision_prompt: str = DEFAULT_CEO_DECISION_PROMPT
) -> str:
    """
    Process a prompt file with multiple models as a "board of directors",
    then have a "CEO" model make a final decision based on all responses.
    
    Args:
        from_file: Path to the text file containing the prompt
        output_dir: Directory to save response files (default: current directory)
        models_prefixed_by_provider: List of model strings for the "board"
                                   If None, uses the DEFAULT_MODELS environment variable
        ceo_model: Model string for the CEO decision-maker
        ceo_decision_prompt: Template for the CEO decision prompt
        
    Returns:
        Path to the CEO decision file
    """
    # Validate output directory
    output_path = Path(output_dir)
    if not output_path.exists():
        output_path.mkdir(parents=True, exist_ok=True)
    
    if not output_path.is_dir():
        raise ValueError(f"Not a directory: {output_dir}")
    
    # Step 1: Get board member responses
    board_response_files = prompt_from_file_to_file(
        from_file, 
        models_prefixed_by_provider, 
        output_dir
    )
    
    # Get the original prompt from the file
    try:
        with open(from_file, 'r', encoding='utf-8') as f:
            original_prompt = f.read()
    except Exception as e:
        logger.error(f"Error reading original prompt file: {e}")
        raise ValueError(f"Could not read prompt file: {from_file}")
    
    # Get the models that were actually used
    models_used = models_prefixed_by_provider
    if not models_used:
        default_models = os.environ.get("DEFAULT_MODELS", DEFAULT_MODEL)
        models_used = [model.strip() for model in default_models.split(",")]
    
    # Step 2: Read in board member responses
    board_responses_xml = ""
    
    for i, response_file in enumerate(board_response_files):
        try:
            with open(response_file, 'r', encoding='utf-8') as f:
                response_content = f.read()
                
            # Format as XML for the CEO prompt
            model_name = models_used[i]
            board_responses_xml += f"""
    <board-response>
        <model-name>{model_name}</model-name>
        <response>{response_content}</response>
    </board-response>
"""
        except Exception as e:
            logger.error(f"Error reading response file {response_file}: {e}")
            board_responses_xml += f"""
    <board-response>
        <model-name>{models_used[i]}</model-name>
        <response>ERROR: Could not read response file.</response>
    </board-response>
"""
    
    # Step 3: Format CEO prompt with the original prompt and board responses
    ceo_prompt = ceo_decision_prompt.format(
        original_prompt=original_prompt,
        board_responses=board_responses_xml
    )
    
    # Step 4: Send to CEO model for decision
    ceo_response = prompt(ceo_prompt, [ceo_model])[0]
    
    # Step 5: Write CEO decision to file
    ceo_decision_file = output_path / "ceo_decision.md"
    try:
        with open(ceo_decision_file, 'w', encoding='utf-8') as f:
            f.write(ceo_response)
        logger.info(f"CEO decision written to {ceo_decision_file}")
    except Exception as e:
        logger.error(f"Error writing CEO decision to {ceo_decision_file}: {e}")
        raise ValueError(f"Could not write CEO decision file: {ceo_decision_file}")
    
    return str(ceo_decision_file)