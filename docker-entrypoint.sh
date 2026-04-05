#!/bin/bash
set -e

echo "=========================================="
echo "Medical RAG - Docker Container Starting"
echo "=========================================="

# Fix permissions on mounted volumes for Windows compatibility
echo "Setting permissions on data directories..."
chmod -R 777 /app/pdfs /app/logs /app/vector_db /app/data 2>/dev/null || true

# Wait for Ollama service to be ready
echo "Waiting for Ollama service to be ready..."
OLLAMA_URL="${OLLAMA_BASE_URL:-http://ollama:11434}"
MAX_RETRIES=30
RETRY_COUNT=0

until curl -s "$OLLAMA_URL/" > /dev/null 2>&1; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "ERROR: Ollama service did not become ready in time"
        exit 1
    fi
    echo "Waiting for Ollama... (attempt $RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

echo "✓ Ollama service is ready"

# Pull required models if not already present
echo "Checking required models..."
MODELS=("${OLLAMA_MODEL:-deepseek-llm:7b-chat}" "${OLLAMA_EMBEDDING_MODEL:-nomic-embed-text}")

for MODEL in "${MODELS[@]}"; do
    echo "Checking model: $MODEL"
    if ! curl -s "$OLLAMA_URL/api/tags" | grep -q "\"name\":\"$MODEL\""; then
        echo "Pulling model: $MODEL (this may take several minutes)..."
        curl -X POST "$OLLAMA_URL/api/pull" \
            -H "Content-Type: application/json" \
            -d "{\"name\":\"$MODEL\"}" \
            --no-buffer | while read -r line; do
                # Extract and display progress if available
                if echo "$line" | grep -q '"status"'; then
                    STATUS=$(echo "$line" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
                    echo "  $STATUS"
                fi
            done
        echo "✓ Model $MODEL pulled successfully"
    else
        echo "✓ Model $MODEL already present"
    fi
done

# Check if PDFs directory has files
PDF_COUNT=$(find /app/pdfs -type f -name "*.pdf" 2>/dev/null | wc -l)
echo "Found $PDF_COUNT PDF file(s) in /app/pdfs"

# Graceful shutdown handler
shutdown_handler() {
    echo ""
    echo "=========================================="
    echo "Shutting down gracefully..."
    echo "=========================================="
    # Kill the Python process gracefully
    kill -SIGTERM "$PID" 2>/dev/null || true
    wait "$PID" 2>/dev/null || true
    echo "Shutdown complete"
    exit 0
}

# Register shutdown handler
trap shutdown_handler SIGTERM SIGINT

# Start the FastAPI application
echo "=========================================="
echo "Starting Medical RAG Application"
echo "=========================================="
echo "Web interface will be available at: http://localhost:8000"
echo ""

# Run the application in the background
python3 app.py &
PID=$!

# Wait for the application process
wait "$PID"
