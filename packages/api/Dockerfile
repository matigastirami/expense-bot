FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy ALL project files needed for dependencies
COPY pyproject.toml /app/
COPY packages/api/pyproject.toml /app/packages/api/

# Install root project dependencies
RUN pip install --no-cache-dir -e .

# Install API-specific dependencies
RUN pip install --no-cache-dir -e packages/api/

# Copy shared libraries
COPY libs/ /app/libs/

# Copy API package
COPY packages/api/ /app/packages/api/

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose API port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health').read()" || exit 1

# Run the API
CMD ["python", "packages/api/run.py"]
