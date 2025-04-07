# Base image: lightweight but with apt tools for ripgrep
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# System dependencies (ripgrep for fast code search)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ripgrep && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project files into the container
COPY . .

# Expose MCP server over STDIO
CMD ["python", "main.py"]
