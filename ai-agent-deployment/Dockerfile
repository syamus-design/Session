# Multi-stage build for Python AI Agent
FROM python:3.11-slim as base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY app/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ .

# Create non-root user for security
RUN useradd -m -u 1000 aiagent && chown -R aiagent:aiagent /app
USER aiagent

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "-m", "uvicorn", "agent:app", "--host", "0.0.0.0", "--port", "8000"]
