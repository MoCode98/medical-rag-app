# Dockerfile for Medical Research RAG Pipeline
# Build for linux/amd64 platform (Windows compatibility)

FROM --platform=linux/amd64 python:3.12-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# No additional system dependencies needed
# (All dependencies are Python-based)

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
# Exclude development tools in production by installing only what's needed
RUN pip install --no-cache-dir -r requirements.txt && \
    # Remove test/dev dependencies to slim down image
    pip uninstall -y black ruff mypy pytest pytest-cov || true

# Copy application code
COPY src/ ./src/
COPY api/ ./api/
COPY static/ ./static/
COPY app.py ingest.py query.py query_enhanced.py ./

# Copy entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Create directories for volumes
# These will be mounted as volumes but need to exist in the image
# Use 777 permissions to ensure write access across different host systems (Windows/Mac/Linux)
RUN mkdir -p pdfs vector_db data logs && \
    chmod 777 pdfs vector_db data logs

# Create non-root user for security
# Using UID 1000 which is common on Linux/Mac/Windows
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app && \
    # Ensure volume mount points are writable
    chmod 777 /app/pdfs /app/vector_db /app/data /app/logs

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
# Poll the /health endpoint to verify service is running
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import httpx; exit(0 if httpx.get('http://localhost:8000/health').status_code == 200 else 1)"

# Use entrypoint script to check permissions before starting app
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

# Run application
CMD ["python", "app.py"]
