FROM python:3.13-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock README.md ./

# Install dependencies
RUN uv sync --frozen --no-cache

# Copy source code
COPY . .

# Expose port (configurable via APP_PORT, defaults to 8000)
EXPOSE ${APP_PORT:-8000}

# Health check using Python instead of curl
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen(f'http://localhost:{os.getenv(\"APP_PORT\", \"8000\")}/').read()" || exit 1

# Run the application
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "${APP_PORT:-8000}"]
