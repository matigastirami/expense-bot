FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY pyproject.toml .
RUN pip install -e .

# Copy source code
COPY src/ ./src/
COPY alembic.ini .

# Run alembic migrations and start app
CMD ["sh", "-c", "alembic upgrade head && python -m src.app"]