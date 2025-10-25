FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (including ffmpeg for voice message processing)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy ALL project files needed for dependencies
COPY pyproject.toml /app/

# Install root project dependencies (includes all bot dependencies)
RUN pip install --no-cache-dir -e .

# Copy shared libraries
COPY libs/ /app/libs/

# Copy agent package (required by bot)
COPY packages/agent/ /app/packages/agent/

# Copy telegram package
COPY packages/telegram/ /app/packages/telegram/

# Copy bot entry point
COPY src/app.py /app/src/app.py

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Health check - verify bot can import successfully
HEALTHCHECK --interval=60s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "from packages.telegram.bot import dp; print('OK')" || exit 1

# Run the bot
CMD ["python", "packages/telegram/run.py"]
