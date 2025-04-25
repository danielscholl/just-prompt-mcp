FROM python:3.12-slim

# Install uv as root
RUN pip install uv

# Copy the project files
COPY . /app/

# Install packages as root
RUN cd /app && uv pip install --system -e .

# Create a non-root user
RUN useradd -m -s /bin/bash justprompt
USER justprompt

# Set the working directory
WORKDIR /workspace

# Command to run the MCP server
CMD ["uv", "run", "just-prompt"] 