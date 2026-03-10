# Web UI Setup Guide

## Quick Start

### 1. Install Web UI Dependencies

```bash
# Make sure you're in the project directory with venv activated
cd "healthcare project"
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install/upgrade dependencies including FastAPI
pip install -r requirements.txt
```

### 2. Start the Web Server

```bash
python app.py
```

You should see:
```
================================================================================
Medical Research RAG - Web UI
================================================================================

Starting server...
  • UI:  http://localhost:8000
  • API: http://localhost:8000/docs

Press CTRL+C to stop
================================================================================
```

### 3. Open the UI

Navigate to **http://localhost:8000** in your web browser.

---

## Using the Web UI

### Tab 1: Ingest 📄

1. **Upload PDFs**:
   - Drag and drop PDF files into the upload zone
   - Or click to browse and select files
   - Maximum 50MB per file

2. **Start Ingestion**:
   - Check "Reset database" if you want to start fresh
   - Click "Start Ingestion"
   - Watch real-time progress and logs

3. **Monitor Progress**:
   - Progress bar shows overall completion
   - Logs terminal displays each processing step
   - Green checkmarks (✓) indicate success
   - Red X marks (✗) show failures

### Tab 2: Query 💬

1. **Configure Settings** (optional):
   - **Model**: Choose from available Ollama models
   - **Top-K**: Number of context chunks to retrieve (1-20)
   - **Temperature**: LLM creativity (0 = focused, 2 = creative)

2. **Ask Questions**:
   - Type your question in the input box
   - Press Enter or click "Send"
   - Wait for the AI to respond

3. **View Results**:
   - Answer appears with markdown formatting
   - Sources section shows:
     - Document name
     - Title and section
     - Page numbers
     - Similarity score
   - Query time displayed at bottom

4. **Chat History**:
   - Previous Q&A pairs remain visible
   - Click "Clear chat" to start fresh

### Tab 3: Metrics 📊

Real-time system statistics:

- **Total Chunks**: Number of text chunks in database
- **Cache Hit Rate**: Embedding cache efficiency
- **Files Processed**: Successfully ingested PDFs
- **Failed Files**: PDFs that couldn't be processed

**Cache Performance Chart**: Visual breakdown of cache hits vs misses

**Database Info**: Collection name, path, and sample files

**Auto-refresh**: Updates every 5 seconds

---

## API Endpoints

### Interactive Documentation

FastAPI provides automatic interactive API docs:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Available Endpoints

**Ingestion:**
- `POST /api/ingest/upload` - Upload PDF files
- `POST /api/ingest/ingest` - Start ingestion
- `GET /api/ingest/status` - Get ingestion status
- `WS /api/ingest/stream` - WebSocket for real-time progress

**Query:**
- `POST /api/query/query` - Submit a RAG query
- `GET /api/query/models` - List available Ollama models
- `POST /api/query/reset` - Reset RAG instance

**Metrics:**
- `GET /api/metrics/stats` - Get all system stats
- `GET /api/metrics/database` - Database statistics
- `GET /api/metrics/cache` - Cache statistics
- `GET /api/metrics/health` - Health check

---

## Troubleshooting

### Server Won't Start

**Error**: `ModuleNotFoundError: No module named 'fastapi'`
```bash
# Solution: Install dependencies
pip install -r requirements.txt
```

**Error**: `Address already in use`
```bash
# Solution: Port 8000 is occupied
# Option 1: Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Option 2: Change port in app.py (line ~80)
# Change: port=8000  →  port=8001
```

### Database Empty

**Issue**: "Vector database is empty" error when querying

**Solution**:
1. Go to Ingest tab
2. Upload PDFs
3. Click "Start Ingestion"
4. Wait for completion
5. Go to Query tab

### WebSocket Connection Failed

**Issue**: Ingestion progress doesn't update

**Solution**:
- Check browser console for errors
- Ensure no firewall blocking WebSocket
- Try refreshing the page
- Restart the server

### Ollama Connection Failed

**Issue**: "Could not connect to Ollama" in model list

**Solution**:
```bash
# Start Ollama service
ollama serve

# In another terminal, verify it's running
ollama list

# Pull required models if missing
ollama pull nomic-embed-text
ollama pull deepseek-r1:7b
```

---

## Production Deployment

### Using Uvicorn Directly

For production with multiple workers:

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

### Using Gunicorn + Uvicorn

```bash
pip install gunicorn

gunicorn app:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

### Docker Deployment

Create `Dockerfile`:
```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["python", "app.py"]
```

Build and run:
```bash
docker build -t medical-rag-ui .
docker run -p 8000:8000 -v $(pwd)/pdf:/app/pdf medical-rag-ui
```

---

## Security Notes

### Development vs Production

The current configuration is for **local development** only:
- CORS allows all origins (`*`)
- No authentication
- No rate limiting

### For Production

Before deploying publicly:

1. **Restrict CORS** in `app.py`:
   ```python
   allow_origins=["https://yourdomain.com"]
   ```

2. **Add Authentication**:
   - Install: `pip install fastapi-users`
   - Add OAuth2/JWT authentication
   - Protect sensitive endpoints

3. **Enable Rate Limiting**:
   ```bash
   pip install slowapi
   ```

4. **Use HTTPS**:
   - Add TLS certificate
   - Use reverse proxy (nginx/traefik)

5. **Validate File Uploads**:
   - Already limited to PDF, 50MB max
   - Consider adding virus scanning

---

## Performance Tips

### Ingestion Speed

- **Faster**: Use smaller models (e.g., `qwen:0.5b`)
- **Better quality**: Use larger models (e.g., `deepseek-r1:70b`)
- **Balance**: Default `deepseek-r1:7b` is a good middle ground

### Query Speed

- **Reduce top-k**: Fewer chunks = faster (but less context)
- **Use caching**: Embedding cache speeds up repeat queries
- **Smaller models**: Faster generation but potentially lower quality

### Database Performance

- ChromaDB is already optimized for local use
- For 10,000+ documents, consider PostgreSQL with pgvector
- SSD storage highly recommended

---

## CLI Still Works!

The web UI doesn't replace the CLI - both work independently:

```bash
# CLI ingestion (no web server needed)
python ingest.py --reset

# CLI query (no web server needed)
python query.py --interactive

# CLI enhanced features
python query_enhanced.py --all-features --interactive
```

Choose the interface that fits your workflow!
