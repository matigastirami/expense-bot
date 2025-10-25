FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy ALL project files needed for dependencies
COPY pyproject.toml /app/

# Install root project dependencies (includes all agent dependencies)
RUN pip install --no-cache-dir -e .

# Copy shared libraries
COPY libs/ /app/libs/

# Copy agent package
COPY packages/agent/ /app/packages/agent/

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Health check - verify agent can import successfully
HEALTHCHECK --interval=60s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "from packages.agent.agent import FinanceAgent; print('OK')" || exit 1

# Default to REPL mode (can be overridden)
CMD ["python", "packages/agent/repl.py"]
