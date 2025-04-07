# Generated by https://smithery.ai. See: https://smithery.ai/docs/config#dockerfile
FROM python:3.10-slim

# Install necessary system packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy project files
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir fastmcp pandas numpy flake8 pylint

# Start the MCP server
CMD ["python", "server.py"]
