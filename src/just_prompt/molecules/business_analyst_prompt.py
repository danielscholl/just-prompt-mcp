"""
Business Analyst prompt functionality for just-prompt.
"""

from typing import List
import logging
import os
from pathlib import Path

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

# Consolidation prompt template for merging multiple model briefs
CONSOLIDATION_PROMPT = """
<purpose>
    You are a Lead Business Analyst responsible for consolidating multiple business briefs from different models into a single comprehensive project brief. Your task is to analyze multiple perspectives, identify commonalities and unique insights, and create a unified brief that captures the best aspects of each.
</purpose>

<instructions>
    <instruction>Review each of the individual briefs provided below.</instruction>
    <instruction>Identify key points, recommendations, and insights from each brief.</instruction>
    <instruction>Consolidate the information into a single comprehensive brief that includes the most valuable insights from all sources.</instruction>
    <instruction>Ensure your final brief is well-structured, clear, and actionable.</instruction>
    <instruction>Include all relevant sections from the original briefs: Core Problem, Goals, Target Audience, Core Concept/Features, MVP Scope, and Technical Leanings.</instruction>
    <instruction>Resolve any contradictions between the briefs by selecting the most well-reasoned approach.</instruction>
</instructions>

<original-prompt>
{original_prompt}
</original-prompt>

<individual-briefs>
{individual_briefs}
</individual-briefs>
"""


def business_analyst_prompt(
    from_file: str, 
    output_dir: str = ".", 
    models_prefixed_by_provider: List[str] = None,
    analyst_model: str = DEFAULT_ANALYST_MODEL,
    business_analyst_prompt: str = DEFAULT_ANALYST_PROMPT
) -> str:
    """
    Process a prompt file with each specified model to create individual briefs.
    If multiple models are specified, also create a consolidated final brief.
    
    Args:
        from_file: Path to the text file containing the prompt
        output_dir: Directory to save response files (default: current directory)
        models_prefixed_by_provider: List of model strings for creating briefs
                             If None, uses the DEFAULT_MODEL environment variable
        analyst_model: Model string for the consolidation (if multiple models used)
        business_analyst_prompt: Template for the business analyst prompt
        
    Returns:
        Path to the final business analyst brief file
    """
    # Validate output directory
    output_path = Path(output_dir)
    if not output_path.exists():
        output_path.mkdir(parents=True, exist_ok=True)
    
    if not output_path.is_dir():
        raise ValueError(f"Not a directory: {output_dir}")
    
    # Determine which models to use
    models_used = models_prefixed_by_provider
    if not models_used:
        default_models = os.environ.get("DEFAULT_MODELS", DEFAULT_MODEL)
        models_used = [model.strip() for model in default_models.split(",")]
    
    # Get the original prompt from the file
    try:
        with open(from_file, 'r', encoding='utf-8') as f:
            original_prompt = f.read()
    except Exception as e:
        logger.error(f"Error reading original prompt file: {e}")
        raise ValueError(f"Could not read prompt file: {from_file}")
    
    # Format business analyst prompt with the original prompt
    formatted_prompt = business_analyst_prompt.format(
        analyst_request=original_prompt
    )
    
    # Step 1: Get individual briefs from each model
    brief_files = []
    briefs_content = []
    
    # Get name of file without extension for naming output files
    from_file_name = Path(from_file).stem
    
    # Generate a brief from each model
    for model in models_used:
        model_display_name = model.replace(":", "_").replace("/", "_")
        brief_filename = f"{from_file_name}_{model_display_name}_brief.md"
        brief_file_path = output_path / brief_filename
        
        # Get response from this model
        model_response = prompt(formatted_prompt, [model])[0]
        
        # Save this model's brief
        try:
            with open(brief_file_path, 'w', encoding='utf-8') as f:
                f.write(model_response)
            logger.info(f"Brief from {model} written to {brief_file_path}")
            brief_files.append(brief_file_path)
            briefs_content.append(f"--- Brief from {model} ---\n\n{model_response}\n\n")
        except Exception as e:
            logger.error(f"Error writing brief from {model} to {brief_file_path}: {e}")
            raise ValueError(f"Could not write brief file: {brief_file_path}")
    
    # Step 2: If multiple models were used, create a consolidated brief
    final_brief_file = output_path / "business_analyst_brief.md"
    
    if len(models_used) > 1:
        # Format consolidation prompt
        consolidation_prompt = CONSOLIDATION_PROMPT.format(
            original_prompt=original_prompt,
            individual_briefs="\n\n".join(briefs_content)
        )
        
        # Get consolidated response
        consolidated_response = prompt(consolidation_prompt, [analyst_model])[0]
        
        # Save consolidated brief
        try:
            with open(final_brief_file, 'w', encoding='utf-8') as f:
                f.write(consolidated_response)
            logger.info(f"Consolidated business analyst brief written to {final_brief_file}")
        except Exception as e:
            logger.error(f"Error writing consolidated brief to {final_brief_file}: {e}")
            raise ValueError(f"Could not write consolidated brief file: {final_brief_file}")
    else:
        # If only one model was used, the final brief is the same as the individual brief
        final_brief_file = brief_files[0]
    
    return str(final_brief_file)