# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build/Test/Lint Commands
- Install dependencies: `pip install -e .`
- Install dev dependencies: `pip install -e ".[test]"`
- Run all tests: `pytest`
- Run a specific test: `pytest path/to/test_file.py::test_function_name`
- Use dotenv in tests: Make sure to use `load_dotenv()` in all tests

## Code Style Guidelines
- Python 3.10+ required
- Use clear docstrings for all functions and classes
- Use typing for function parameters and return values (Pydantic for data models)
- Format provider prefixes as: `provider:model_name` or `shortcode:model_name`
- Error handling: Use try/except blocks with specific logging in LLM calls
- Naming: snake_case for functions/variables, PascalCase for classes
- Structure: Follow the atoms/molecules architecture pattern
- Testing: Real API tests with common prompts, no mocking