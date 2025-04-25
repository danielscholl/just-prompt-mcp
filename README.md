# Just Prompt - MCP Server (Experimental)

A lightweight MCP server providing unified access to popular LLM providers including OpenAI, Anthropic, Google Gemini, Groq, DeepSeek, and Ollama.

## Setup

### Installation

```bash
# Clone and install
git clone https://github.com/danielscholl/just-prompt-mcp.git
cd just-prompt
uv sync

# Install
uv pip install -e .

# Run tests to verify installation
uv run pytest
```

### Docker Setup

You can build and run Just Prompt using Docker:

```bash
# Build the Docker image
docker build -t just-prompt .
```

#### Integration with MCP Clients

To use Just Prompt with MCP clients, add the following configuration to your client's settings:

```json
{
  "mcpServers": {
    "just-prompt": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "--mount", "type=bind,source=<YOUR_WORKSPACE_PATH>,target=/workspace",
        "-e", "OPENAI_API_KEY=<YOUR_OPENAI_KEY>",
        "-e", "ANTHROPIC_API_KEY=<YOUR_ANTHROPIC_KEY>",
        "-e", "GEMINI_API_KEY=<YOUR_GEMINI_KEY>",
        "-e", "GROQ_API_KEY=<YOUR_GROQ_KEY>",
        "-e", "DEEPSEEK_API_KEY=<YOUR_DEEPSEEK_KEY>",
        "-e", "OLLAMA_HOST=http://host.docker.internal:11434",
        "just-prompt"
      ]
    }
  }
}
```

Note: Replace `<YOUR_WORKSPACE_PATH>` with the absolute path to your workspace directory and add your API keys as needed.

### Environment Configuration

Create and edit your `.env` file with your API keys:

```bash
# Create environment file from template
cp .env.sample .env
```

Required API keys in your `.env` file:
```
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
GROQ_API_KEY=your_groq_api_key_here
DEEPSEEK_API_KEY=your_deepseek_api_key_here
OLLAMA_HOST=http://localhost:11434
```

### Claude Code Setup

Setting up Just Prompt with Claude Code:

> Note: "--directory" would be the path to the source code if not in the same directory.

```bash
# Copy this JSON configuration
{
    "command": "uv",
    "args": ["--directory", ".", "run", "just-prompt", "--default-models", "anthropic:claude-3-7-sonnet-20250219"]
}

# Then run this command in Claude Code
claude mcp add just-prompt "$(pbpaste)"
```

To remove the configuration later:
```bash
claude mcp remove just-prompt
```

## Available LLM Providers

| Provider | Short Prefix | Full Prefix | Example Usage |
|----------|--------------|-------------|--------------|
| OpenAI   | `o`          | `openai`    | `o:gpt-4o-mini` |
| Anthropic | `a`         | `anthropic` | `a:claude-3-5-haiku` |
| Google Gemini | `g`     | `gemini`    | `g:gemini-2.5-pro-exp-03-25` |
| Groq     | `q`          | `groq`      | `q:llama-3.1-70b-versatile` |
| DeepSeek | `d`          | `deepseek`  | `d:deepseek-coder` |
| Ollama   | `l`          | `ollama`    | `l:llama3.1` |

## MCP Tools

### Send Prompts to Models

Send text prompts to one or more LLM models and receive responses.

```bash
# Basic prompt with default model
prompt: "Your prompt text here"

# Specify model(s)
prompt: "Your prompt text here" "openai:gpt-4o"

# Examples with thinking capability
prompt: "Develop a strategy for learning how to create MCP Servers for AI" "anthropic:claude-3-7-sonnet-20250219:4k"

prompt: "Write a function to calculate the factorial of a number" "openai:o4-mini:high"
```

### List Available Options

Check which providers and models are available for use.

```bash
# List all providers
list-providers

# List models for a specific provider
list-models: "openai"
```

### Work with Files

Process prompts from files and save responses to files for batch processing.

```bash
# Send prompt from file
prompt-from-file: "prompt.txt"

# Save responses to files
prompt-from-file-to-file: "prompt.txt" "./responses"
```

## Thinking and Reasoning Capabilities

Each provider offers special capabilities to enhance reasoning on complex questions:

| Provider | Model | Capability | Format | Range | Example |
|----------|-------|------------|--------|-------|---------|
| Anthropic | claude-3-7-sonnet-20250219 | Thinking tokens | `:Nk` or `:N` | 1024-16000 | `anthropic:claude-3-7-sonnet-20250219:4k` |
| OpenAI | o3-mini, o4-mini, o3 | Reasoning effort | `:level` | low, medium, high | `openai:o3-mini:high` |
| Google | gemini-2.5-flash-preview-04-17 | Thinking budget | `:Nk` or `:N` | 0-24576 | `gemini:gemini-2.5-flash-preview-04-17:4k` |

**Usage examples:**
```bash
# Claude with 4k thinking tokens
prompt: "Analyze quantum computing applications" "anthropic:claude-3-7-sonnet-20250219:4k"

# OpenAI with high reasoning effort
prompt: "Solve this complex math problem" "openai:o3-mini:high"

# Gemini with 8k thinking budget
prompt: "Evaluate climate change solutions" "gemini:gemini-2.5-flash-preview-04-17:8k"
```