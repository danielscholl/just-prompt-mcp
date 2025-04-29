"""
Business Analyst prompt functionality for just-prompt.
"""

from typing import List
import logging
import os
from pathlib import Path

from .prompt_from_file_to_file import prompt_from_file_to_file
from .prompt import prompt
from ..atoms.shared.utils import DEFAULT_MODEL

logger = logging.getLogger(__name__)

# Default Business Analyst model
DEFAULT_ANALYST_MODEL = "openai:o3"

# Default Business Analyst prompt template
DEFAULT_ANALYST_PROMPT = """
<purpose>
    You are a world-class expert Market & Business Analyst and also the best research assistant I have ever met, possessing deep expertise in both comprehensive market research and collaborative project definition. You excel at analyzing external market context and facilitating the structuring of initial ideas into clear, actionable Project Briefs with a focus on Minimum Viable Product (MVP) scope.
</purpose>

<capabilities>
    <capability>Data analysis and business needs understanding</capability>
    <capability>Market opportunity and pain point identification</capability>
    <capability>Competitor analysis</capability>
    <capability>Target audience definition</capability>
    <capability>Clear communication and structured dialogue</capability>
</capabilities>

<modes>
    <mode>
        <n>Market Research Mode</n>
        <description>Conduct deep research on a provided product concept or market area</description>
        <outputs>
            <o>Market Needs/Pain Points</o>
            <o>Competitor Landscape</o>
            <o>Target User Demographics/Behaviors</o>
        </outputs>
        <tone>Professional, analytical, informative, objective</tone>
    </mode>
    
    <mode>
        <n>Project Briefing Mode</n>
        <description>Collaboratively guide the user through brainstorming and definition</description>
        <outputs>
            <o>Core Problem</o>
            <o>Goals</o>
            <o>Audience</o>
            <o>Core Concept/Features (High-Level)</o>
            <o>MVP Scope (In/Out)</o>
            <o>Initial Technical Leanings (Optional)</o>
        </outputs>
        <tone>Collaborative, inquisitive, structured, helpful</tone>
    </mode>
</modes>

<instructions>
    <instruction>Identify the required mode (Market Research or Project Briefing) based on the user's request. If unclear, ask for clarification.</instruction>
    <instruction>For Market Research Mode: Focus on executing deep research based on the provided concept. Present findings clearly and concisely in the final report.</instruction>
    <instruction>For Project Briefing Mode: Engage in a dialogue, asking targeted clarifying questions about the concept, problem, goals, users, and MVP scope.</instruction>
    <instruction>Use structured formats (lists, sections) for outputs and avoid ambiguity.</instruction>
    <instruction>Prioritize understanding user needs and project goals.</instruction>
    <instruction>Be capable of explaining market concepts or analysis techniques clearly if requested.</instruction>
</instructions>

<interaction-flow>
    <step>Identify Mode: Determine if the user needs Market Research or Project Briefing</step>
    <step>Input Gathering: Collect necessary information based on the identified mode</step>
    <step>Execution: Perform research or guide through project definition</step>
    <step>Output Generation: Structure findings into appropriate format</step>
    <step>Presentation: Present final report or Project Brief document</step>
</interaction-flow>

<exclusions>
    <exclude>Do not include any metadata, headers, footers, or formatting that isn't part of the actual project brief or market research report.</exclude>
    <exclude>Only include the content directly relevant to the requested output.</exclude>
</exclusions>

<analyst-request>{analyst_request}</analyst-request>
"""


def business_analyst_prompt(
    from_file: str, 
    output_dir: str = ".", 
    models_prefixed_by_provider: List[str] = None,
    analyst_model: str = DEFAULT_ANALYST_MODEL,
    business_analyst_prompt: str = DEFAULT_ANALYST_PROMPT
) -> str:
    """
    Process a prompt file with multiple models as analysts,
    then have a business analyst model create a product brief.
    
    Args:
        from_file: Path to the text file containing the prompt
        output_dir: Directory to save response files (default: current directory)
        models_prefixed_by_provider: List of model strings for the analysis
                               If None, uses the DEFAULT_MODELS environment variable
        analyst_model: Model string for the business analyst
        business_analyst_prompt: Template for the business analyst prompt
        
    Returns:
        Path to the business analyst brief file
    """
    # Validate output directory
    output_path = Path(output_dir)
    if not output_path.exists():
        output_path.mkdir(parents=True, exist_ok=True)
    
    if not output_path.is_dir():
        raise ValueError(f"Not a directory: {output_dir}")
    
    # Step 1: Get analyst responses
    analyst_response_files = prompt_from_file_to_file(
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
    
    # Step 2: Read in analyst responses
    analyst_responses = ""
    
    for i, response_file in enumerate(analyst_response_files):
        try:
            with open(response_file, 'r', encoding='utf-8') as f:
                response_content = f.read()
            # Format for the business analyst prompt
            model_name = models_used[i]
            analyst_responses += f"\n\n--- Response from {model_name} ---\n\n{response_content}\n\n"
        except Exception as e:
            logger.error(f"Error reading response file {response_file}: {e}")
            analyst_responses += f"\n\n--- Response from {models_used[i]} ---\n\nERROR: Could not read response file.\n\n"
    
    # Step 3: Format business analyst prompt with the original prompt
    final_prompt = business_analyst_prompt.format(
        analyst_request=original_prompt
    )
    
    # Add the analyst responses to the original prompt
    final_prompt += f"\n\n<research-material>\n{analyst_responses}\n</research-material>"
    
    # Step 4: Send to business analyst model for project brief
    analyst_response = prompt(final_prompt, [analyst_model])[0]
    
    # Step 5: Write business analyst brief to file
    brief_file = output_path / "business_analyst_brief.md"
    try:
        with open(brief_file, 'w', encoding='utf-8') as f:
            f.write(analyst_response)
        logger.info(f"Business analyst brief written to {brief_file}")
    except Exception as e:
        logger.error(f"Error writing business analyst brief to {brief_file}: {e}")
        raise ValueError(f"Could not write business analyst brief file: {brief_file}")
    
    return str(brief_file)