# Just Prompt - Development Guidelines

## Project Overview
Just Prompt is a lightweight MCP server wrapper around multiple LLM providers including OpenAI, Anthropic, Gemini, Groq, DeepSeek, and Ollama.

## Documentation
- Specification files are located in the `specs/` directory
- AI documentation is located in the `ai_docs/` directory
- Reference these documents when implementing new features or making changes

## Key Concepts
- Provider prefixes use format: `provider:model_name` or `shortcode:model_name`
- Short codes: 
  - o: OpenAI
  - a: Anthropic
  - g: Gemini
  - q: Groq
  - d: DeepSeek
  - l: Ollama

## Development Environment
- Python 3.12+ required
- Use environment variables for API keys
- Validate provider API keys on startup
- Use dotenv for loading environment variables
- Use `load_dotenv()` in all tests

## Build & Test Commands
- Install dependencies: `pip install -e .`
- Install dev dependencies: `pip install -e ".[test]"`
- Run all tests: `pytest`
- Run specific test: `pytest path/to/test_file.py::test_function_name`

## Code Style Guidelines
- Use clear docstrings for all functions and classes
- Use typing for function parameters and return values
- Use Pydantic for data models and validation
- Naming conventions:
  - snake_case for functions/variables
  - PascalCase for classes
- Error handling:
  - Use try/except blocks with specific logging in LLM calls
  - Handle model corrections via weak_provider_and_model parameter

## Architecture
- Follow atoms/molecules architecture pattern:
  - atoms/: Core provider implementations and shared utilities
  - molecules/: Higher-level functionality combining atoms
- Tests mirror the source structure

## Testing Guidelines
- Use real API tests with common prompts (no mocking)
- Preserve existing code behavior when making changes
- Validate provider API keys on startup
- Handle model corrections via weak_provider_and_model parameter

## Important Notes
- Don't mock tests - use real API calls with simple prompts
- Use environment variables for API keys
- Validate provider API keys on startup
- Handle model corrections via weak_provider_and_model parameter
- Format provider prefixes consistently
- Preserve existing code behavior when making changes
