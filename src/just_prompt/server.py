"""
MCP server for just-prompt.
"""

import asyncio
import logging
import os
from typing import List, Dict, Any, Optional
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from pydantic import BaseModel, Field
from .atoms.shared.utils import DEFAULT_MODEL
from .atoms.shared.validator import print_provider_availability
from .molecules.prompt import prompt
from .molecules.prompt_from_file import prompt_from_file
from .molecules.prompt_from_file_to_file import prompt_from_file_to_file
from .molecules.ceo_and_board_prompt import ceo_and_board_prompt, DEFAULT_CEO_MODEL, DEFAULT_CEO_DECISION_PROMPT
from .molecules.business_analyst_prompt import business_analyst_prompt, DEFAULT_ANALYST_MODEL, DEFAULT_ANALYST_PROMPT
from .molecules.list_providers import list_providers as list_providers_func
from .molecules.list_models import list_models as list_models_func
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Tool names enum
class JustPromptTools:
    PROMPT = "prompt"
    PROMPT_FROM_FILE = "prompt_from_file"
    PROMPT_FROM_FILE_TO_FILE = "prompt_from_file_to_file"
    CEO_AND_BOARD = "ceo_and_board_prompt"
    BUSINESS_ANALYST = "business_analyst_prompt"
    LIST_PROVIDERS = "list_providers"
    LIST_MODELS = "list_models"

# Schema classes for MCP tools
class PromptSchema(BaseModel):
    text: str = Field(..., description="The prompt text")
    models_prefixed_by_provider: Optional[List[str]] = Field(
        None, 
        description="List of models with provider prefixes (e.g., 'openai:gpt-4o' or 'o:gpt-4o'). If not provided, uses default models."
    )

class PromptFromFileSchema(BaseModel):
    file: str = Field(..., description="Path to the file containing the prompt")
    models_prefixed_by_provider: Optional[List[str]] = Field(
        None, 
        description="List of models with provider prefixes (e.g., 'openai:gpt-4o' or 'o:gpt-4o'). If not provided, uses default models."
    )

class PromptFromFileToFileSchema(BaseModel):
    file: str = Field(..., description="Path to the file containing the prompt")
    models_prefixed_by_provider: Optional[List[str]] = Field(
        None, 
        description="List of models with provider prefixes (e.g., 'openai:gpt-4o' or 'o:gpt-4o'). If not provided, uses default models."
    )
    output_dir: str = Field(
        default=".", 
        description="Directory to save the response files to (default: current directory)"
    )

class ListProvidersSchema(BaseModel):
    pass

class ListModelsSchema(BaseModel):
    provider: str = Field(..., description="Provider to list models for (e.g., 'openai' or 'o')")

class CEOAndBoardSchema(BaseModel):
    file: str = Field(..., description="Path to the file containing the prompt")
    models_prefixed_by_provider: Optional[List[str]] = Field(
        None, 
        description="List of models with provider prefixes (e.g., 'openai:gpt-4o' or 'o:gpt-4o') for the board members. If not provided, uses default models."
    )
    output_dir: str = Field(
        default=".", 
        description="Directory to save the response files to (default: current directory)"
    )
    ceo_model: str = Field(
        default=DEFAULT_CEO_MODEL,
        description=f"Model for the CEO to make the final decision (default: {DEFAULT_CEO_MODEL})"
    )

class BusinessAnalystSchema(BaseModel):
    file: str = Field(..., description="Path to the file containing the prompt")
    models_prefixed_by_provider: Optional[List[str]] = Field(
        None, 
        description="List of models with provider prefixes (e.g., 'openai:gpt-4o' or 'o:gpt-4o') for the analysts. If not provided, uses default models."
    )
    output_dir: str = Field(
        default=".", 
        description="Directory to save the response files to (default: current directory)"
    )
    analyst_model: str = Field(
        default=DEFAULT_ANALYST_MODEL,
        description=f"Model for the business analyst to create the final brief (default: {DEFAULT_ANALYST_MODEL})"
    )


async def serve(default_models: str = DEFAULT_MODEL) -> None:
    """
    Start the MCP server.
    
    Args:
        default_models: Comma-separated list of default models to use for prompts and corrections
    """
    # Set global default models for prompts and corrections
    os.environ["DEFAULT_MODELS"] = default_models
    
    # Parse default models into a list
    default_models_list = [model.strip() for model in default_models.split(",")]
    
    # Set the first model as the correction model
    correction_model = default_models_list[0] if default_models_list else "o:gpt-4o-mini"
    os.environ["CORRECTION_MODEL"] = correction_model
    
    logger.info(f"Starting server with default models: {default_models}")
    logger.info(f"Using correction model: {correction_model}")
    
    # Check and log provider availability
    print_provider_availability()
    
    # Create the MCP server
    server = Server("just-prompt")
    
    @server.list_tools()
    async def list_tools() -> List[Tool]:
        """Register all available tools with the MCP server."""
        return [
            Tool(
                name=JustPromptTools.PROMPT,
                description="Send a prompt to multiple LLM models",
                inputSchema=PromptSchema.schema(),
            ),
            Tool(
                name=JustPromptTools.PROMPT_FROM_FILE,
                description="Send a prompt from a file to multiple LLM models",
                inputSchema=PromptFromFileSchema.schema(),
            ),
            Tool(
                name=JustPromptTools.PROMPT_FROM_FILE_TO_FILE,
                description="Send a prompt from a file to multiple LLM models and save responses to files",
                inputSchema=PromptFromFileToFileSchema.schema(),
            ),
            Tool(
                name=JustPromptTools.CEO_AND_BOARD,
                description="Send a prompt to multiple models as a 'board of directors', then have a 'CEO' model make a final decision",
                inputSchema=CEOAndBoardSchema.schema(),
            ),
            Tool(
                name=JustPromptTools.BUSINESS_ANALYST,
                description="Send a prompt to multiple models as analysts, then have a business analyst model create a product brief",
                inputSchema=BusinessAnalystSchema.schema(),
            ),
            Tool(
                name=JustPromptTools.LIST_PROVIDERS,
                description="List all available LLM providers",
                inputSchema=ListProvidersSchema.schema(),
            ),
            Tool(
                name=JustPromptTools.LIST_MODELS,
                description="List all available models for a specific LLM provider",
                inputSchema=ListModelsSchema.schema(),
            ),
        ]
    
    @server.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle tool calls from the MCP client."""
        logger.info(f"Tool call: {name}, arguments: {arguments}")
        
        try:
            if name == JustPromptTools.PROMPT:
                models_to_use = arguments.get("models_prefixed_by_provider")
                responses = prompt(arguments["text"], models_to_use)
                
                # Get the model names that were actually used
                models_used = models_to_use if models_to_use else [model.strip() for model in os.environ.get("DEFAULT_MODELS", DEFAULT_MODEL).split(",")]
                
                return [TextContent(
                    type="text",
                    text="\n".join([f"Model: {models_used[i]}\nResponse: {resp}" 
                                  for i, resp in enumerate(responses)])
                )]
                
            elif name == JustPromptTools.PROMPT_FROM_FILE:
                models_to_use = arguments.get("models_prefixed_by_provider")
                responses = prompt_from_file(arguments["file"], models_to_use)
                
                # Get the model names that were actually used
                models_used = models_to_use if models_to_use else [model.strip() for model in os.environ.get("DEFAULT_MODELS", DEFAULT_MODEL).split(",")]
                
                return [TextContent(
                    type="text",
                    text="\n".join([f"Model: {models_used[i]}\nResponse: {resp}" 
                                  for i, resp in enumerate(responses)])
                )]
                
            elif name == JustPromptTools.PROMPT_FROM_FILE_TO_FILE:
                output_dir = arguments.get("output_dir", ".")
                models_to_use = arguments.get("models_prefixed_by_provider")
                file_paths = prompt_from_file_to_file(
                    arguments["file"], 
                    models_to_use,
                    output_dir
                )
                return [TextContent(
                    type="text",
                    text=f"Responses saved to:\n" + "\n".join(file_paths)
                )]
                
            elif name == JustPromptTools.LIST_PROVIDERS:
                providers = list_providers_func()
                provider_text = "\nAvailable Providers:\n"
                for provider in providers:
                    provider_text += f"- {provider['name']}: full_name='{provider['full_name']}', short_name='{provider['short_name']}'\n"
                return [TextContent(
                    type="text",
                    text=provider_text
                )]
                
            elif name == JustPromptTools.LIST_MODELS:
                models = list_models_func(arguments["provider"])
                return [TextContent(
                    type="text",
                    text=f"Models for provider '{arguments['provider']}':\n" + 
                         "\n".join([f"- {model}" for model in models])
                )]

            elif name == JustPromptTools.CEO_AND_BOARD:
                file_path = arguments["file"]
                output_dir = arguments.get("output_dir", ".")
                models_to_use = arguments.get("models_prefixed_by_provider")
                ceo_model = arguments.get("ceo_model", DEFAULT_CEO_MODEL)
                
                # Run the CEO and board prompt process
                ceo_decision_file = ceo_and_board_prompt(
                    file_path,
                    output_dir=output_dir,
                    models_prefixed_by_provider=models_to_use,
                    ceo_model=ceo_model
                )
                
                return [TextContent(
                    type="text",
                    text=f"CEO decision saved to:\n{ceo_decision_file}\n\nBoard responses are available in the same directory."
                )]
                
            elif name == JustPromptTools.BUSINESS_ANALYST:
                file_path = arguments["file"]
                output_dir = arguments.get("output_dir", ".")
                models_to_use = arguments.get("models_prefixed_by_provider")
                analyst_model = arguments.get("analyst_model", DEFAULT_ANALYST_MODEL)
                
                # Run the Business Analyst prompt process
                analyst_brief_file = business_analyst_prompt(
                    file_path,
                    output_dir=output_dir,
                    models_prefixed_by_provider=models_to_use,
                    analyst_model=analyst_model
                )
                
                return [TextContent(
                    type="text",
                    text=f"Business Analyst brief saved to:\n{analyst_brief_file}\n\nAnalyst responses are available in the same directory."
                )]
                
            else:
                return [TextContent(
                    type="text",
                    text=f"Unknown tool: {name}"
                )]
                
        except Exception as e:
            logger.error(f"Error handling tool call: {name}, error: {e}")
            return [TextContent(
                type="text",
                text=f"Error: {str(e)}"
            )]
    
    # Initialize and run the server
    try:
        options = server.create_initialization_options()
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, options, raise_exceptions=True)
    except Exception as e:
        logger.error(f"Error running server: {e}")
        raise