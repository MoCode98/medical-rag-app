# Medical Research RAG Pipeline

A complete, fully-local Retrieval-Augmented Generation (RAG) system for medical research papers. This pipeline allows you to query medical literature using natural language and get evidence-based answers with source citations.

## Features

- **100% Local**: All processing runs locally using Ollama - no external API calls
- **Intelligent PDF Parsing**: Preserves document structure (titles, sections, abstracts)
- **Section-Aware Chunking**: Smart text splitting that respects document hierarchy
- **Vector Search**: ChromaDB with Ollama embeddings (nomic-embed-text)
- **Source Citation**: Automatic citation with document name and page numbers
- **Fine-Tuning Support**: Generate datasets for custom model training
- **Interactive & Batch Modes**: Multiple query interfaces

## Architecture

```
PDFs → Parse (pymupdf4llm) → Chunk (section-aware) → Embed (nomic-embed-text) →
→ Store (ChromaDB) → Retrieve (semantic search) → Generate (Ollama LLM) → Answer
```

## Prerequisites

1. **Python 3.10+**
2. **Ollama** installed and running:
   ```bash
   # Install Ollama (macOS)
   brew install ollama

   # Start Ollama server
   ollama serve

   # Pull required models (in a new terminal)
   ollama pull nomic-embed-text
   ollama pull deepseek-r1:7b  # or your preferred model
   ```

## Quick Start

### 1. Installation

```bash
# Clone or navigate to project directory
cd "healthcare project"

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Choose Your Interface

**Option A: Web UI (Recommended)**

```bash
# Start the web server
python app.py

# Open http://localhost:8000 in your browser
```

The Web UI provides:
- 📄 **Ingest Tab**: Drag-and-drop PDF upload with real-time progress
- 💬 **Query Tab**: Chat interface with source citations
- 📊 **Metrics Tab**: Database stats, cache performance, and system health

**Option B: Command Line Interface**

Continue with steps 2-4 below for CLI usage.

### 3. Add Your PDFs (CLI)

```bash
# Copy your medical research PDFs to the pdf folder
cp /path/to/your/papers/*.pdf ./pdf/
```

### 4. Ingest Documents (CLI)

```bash
# Parse PDFs, chunk, and store in vector database
python ingest.py

# Optional: Reset database and regenerate
python ingest.py --reset

# Optional: Generate fine-tuning dataset
python ingest.py --generate-finetune
```

### 5. Query the System (CLI)

```bash
# Interactive mode (recommended for exploration)
python query.py --interactive

# Single query
python query.py "What are the main findings about treatment efficacy?"

# Batch queries from file
python query.py --batch queries.txt --output results.json

# Adjust retrieval parameters
python query.py --top-k 10 "Describe the methodology"
```

## Docker Deployment

Run the complete system using Docker with a single command - perfect for Windows, Linux, or cloud deployment.

### Quick Start with Docker

```bash
# Start everything (Ollama + RAG App)
docker compose up -d

# Download AI models (one-time setup)
docker compose exec ollama ollama pull nomic-embed-text
docker compose exec ollama ollama pull deepseek-r1:7b

# Access the Web UI
# Open http://localhost:8000 in your browser
```

### What You Get

- **Complete Stack**: Ollama and RAG application in isolated containers
- **Cross-Platform**: Works on Windows, macOS, and Linux (built for `linux/amd64`)
- **Persistent Data**: Vector database, caches, and models persist between restarts
- **Auto-Ingestion**: Drop PDFs in `./pdfs/` folder for automatic processing on startup

### Docker Commands

```bash
# Start services
docker compose up -d

# View logs
docker compose logs -f rag-app

# Stop (preserves data)
docker compose stop

# Stop and remove containers (volumes remain)
docker compose down

# Complete cleanup (⚠️ DELETES ALL DATA)
docker compose down -v

# Restart a service
docker compose restart rag-app
```

### Requirements

- **Docker Desktop** (Windows/Mac) or **Docker Engine** (Linux)
- **20GB** free disk space (for Docker images + AI models)
- **8GB RAM** minimum (16GB recommended)

### Volume Mounts

- `./pdfs` → `/app/pdfs` - Drop PDFs here for auto-ingestion
- `./logs` → `/app/logs` - Application logs
- `vector_db` (named volume) - ChromaDB database (persistent)
- `data_cache` (named volume) - Embedding cache (persistent)
- `ollama_data` (named volume) - Ollama models (persistent)

### Environment Configuration

Edit `docker-compose.yml` to customize:

```yaml
environment:
  - OLLAMA_MODEL=deepseek-r1:7b        # Change AI model
  - OLLAMA_EMBEDDING_MODEL=nomic-embed-text
  - CHUNK_SIZE=512                      # Chunking parameters
  - TOP_K_RESULTS=5                     # Retrieval settings
  - TEMPERATURE=0.7                     # AI creativity
```

### Windows Users

See [DOCKER_SETUP.md](DOCKER_SETUP.md) for a complete step-by-step guide including:
- Docker Desktop installation
- Troubleshooting common issues
- Performance optimization
- Backup and restore procedures

## Web UI Features

The web interface (`python app.py`) provides a complete GUI for the RAG pipeline:

### Ingest Tab
- **Drag & Drop Upload**: Upload PDFs directly through the browser
- **Real-time Progress**: WebSocket-powered live updates during ingestion
- **Process Logs**: Terminal-style log viewer showing each step
- **Database Reset**: Option to clear and rebuild the vector database

### Query Tab
- **Chat Interface**: Conversational Q&A with message history
- **Advanced Options**: Configure model, top-k results, and temperature
- **Source Citations**: Automatic references with file names, page numbers, and similarity scores
- **Markdown Support**: Rich text formatting in responses
- **Query Performance**: Real-time query execution time display

### Metrics Tab
- **System Stats**: Total chunks, cache hit rate, files processed
- **Cache Performance**: Visual chart showing cache efficiency
- **Database Info**: Collection details and sample files
- **Auto-refresh**: Metrics update every 5 seconds
- **Health Monitoring**: Real-time system status indicator

### API Documentation
Access interactive API docs at `http://localhost:8000/docs` (Swagger UI)

## Project Structure

```
healthcare project/
├── pdf/                          # Place your PDF files here
├── vector_db/                    # ChromaDB storage (auto-generated)
├── data/                         # Parsed documents and datasets
│   ├── parsed_documents.json     # Parsed PDF metadata
│   ├── finetune_alpaca.jsonl     # Fine-tuning data (Alpaca format)
│   ├── finetune_chatml.jsonl     # Fine-tuning data (ChatML format)
│   └── FINETUNING_INSTRUCTIONS.md
├── logs/                         # Application logs
│   └── rag_pipeline.log
├── src/                          # Source code
│   ├── __init__.py
│   ├── config.py                 # Configuration management
│   ├── logger.py                 # Logging setup
│   ├── pdf_parser.py             # PDF parsing with pymupdf4llm
│   ├── chunker.py                # Intelligent text chunking
│   ├── embeddings.py             # Ollama embeddings wrapper
│   ├── vector_db.py              # ChromaDB interface
│   ├── rag_pipeline.py           # RAG query pipeline
│   └── finetune_dataset.py       # Fine-tuning dataset generator
├── api/                          # Web API (NEW)
│   ├── __init__.py
│   ├── ingest.py                 # Ingestion endpoints
│   ├── query.py                  # Query endpoints
│   └── metrics.py                # Metrics endpoints
├── static/                       # Web UI (NEW)
│   └── index.html                # Single-page application
├── app.py                        # FastAPI web server (NEW)
├── ingest.py                     # Data ingestion script (CLI)
├── query.py                      # Query interface script (CLI)
├── query_enhanced.py             # Enhanced query with advanced features (CLI)
├── Modelfile                     # Ollama custom model definition
├── requirements.txt              # Python dependencies
├── pyproject.toml                # Development tools configuration
├── .env                          # Configuration (auto-generated)
└── README.md                     # This file
```

## Configuration

Edit [.env](.env) to customize settings:

```bash
# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=deepseek-r1:7b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text

# Chunking Configuration
CHUNK_SIZE=512                    # Tokens per chunk
CHUNK_OVERLAP=50                  # Overlap between chunks
MIN_CHUNK_SIZE=100                # Minimum chunk size

# RAG Configuration
TOP_K_RESULTS=5                   # Number of chunks to retrieve
TEMPERATURE=0.1                   # LLM temperature (0-2)
MAX_TOKENS=2048                   # Maximum response length
```

## Usage Examples

### Interactive Mode

```bash
python query.py --interactive
```

```
Medical Research RAG Assistant - Interactive Session
================================================================================
Model: deepseek-r1:7b
Database: medical_research (234 chunks)

Your question: What are the inclusion criteria for the study?

ANSWER:
The study included patients aged 18-75 with confirmed diagnosis of type 2
diabetes mellitus, HbA1c levels between 7.0% and 10.0%, and no history of
cardiovascular events in the past 6 months. [Source: diabetes_rct_2024.pdf, Page: 5]

SOURCES:
1. File: diabetes_rct_2024.pdf
   Section: Methods - Study Population
   Page(s): 5, 6
   Similarity: 0.887
```

### Single Query with Verbose Output

```bash
python query.py --verbose "What is the primary outcome measure?"
```

### Batch Processing

Create [queries.txt](queries.txt):
```
What is the study design?
What were the main findings?
What are the limitations?
```

Run batch queries:
```bash
python query.py --batch queries.txt --output results.json
```

### Using Different Models

```bash
# Use a different Ollama model
python query.py --model llama3.2 --interactive

# Or create custom medical model first
ollama create medical-assistant -f Modelfile
python query.py --model medical-assistant --interactive
```

## Creating a Custom Ollama Model

The included [Modelfile](Modelfile) defines a medical research assistant with optimized prompts:

```bash
# Build the custom model
ollama create medical-assistant -f Modelfile

# Test it
ollama run medical-assistant

# Update .env to use it by default
# OLLAMA_MODEL=medical-assistant
```

## Fine-Tuning (Optional)

Generate a fine-tuning dataset from your PDFs:

```bash
python ingest.py --generate-finetune
```

This creates:
- `data/finetune_alpaca.jsonl` - Alpaca format dataset
- `data/finetune_chatml.jsonl` - ChatML format dataset
- `data/FINETUNING_INSTRUCTIONS.md` - Complete fine-tuning guide

Follow the instructions in `FINETUNING_INSTRUCTIONS.md` to:
1. Fine-tune a model using Unsloth
2. Export to GGUF format
3. Import back into Ollama

## Troubleshooting

### Ollama Connection Error

```
Error: Cannot connect to Ollama at http://localhost:11434
```

**Solution**: Start Ollama server:
```bash
ollama serve
```

### Embedding Model Not Found

```
Error: Embedding model 'nomic-embed-text' not found
```

**Solution**: Pull the embedding model:
```bash
ollama pull nomic-embed-text
```

### Empty Database Error

```
Error: Vector database is empty
```

**Solution**: Run ingestion first:
```bash
python ingest.py
```

### PDF Parsing Errors

If certain PDFs fail to parse:
1. Check if the PDF is corrupted or password-protected
2. Try re-downloading the PDF
3. The parser will skip failed PDFs and continue with others

### Out of Memory

For large PDF collections:
1. Reduce `CHUNK_SIZE` in .env
2. Process PDFs in batches
3. Use a smaller embedding model

## Performance Tips

1. **Model Selection**:
   - Fast queries: `gemma3:4b` or `llama3.2`
   - Better quality: `deepseek-r1:7b` or `mistral`
   - Medical-specific: `biomistral` (if available)

2. **Retrieval Tuning**:
   - Increase `TOP_K_RESULTS` for broader context
   - Decrease for faster, more focused answers

3. **Chunk Size**:
   - Larger chunks (1024): Better context preservation
   - Smaller chunks (512): More precise retrieval

## API Reference

### Python API

```python
from src import MedicalRAG, VectorDatabase

# Initialize
db = VectorDatabase()
rag = MedicalRAG(vector_db=db)

# Query
response = rag.query(
    question="What are the main findings?",
    top_k=5
)

print(response.answer)
for source in response.sources:
    print(f"{source['file']}, Page {source['pages']}")
```

### Command-Line Options

#### ingest.py
```
python ingest.py [--reset] [--generate-finetune]

Options:
  --reset              Delete existing database and start fresh
  --generate-finetune  Generate fine-tuning dataset from PDFs
```

#### query.py
```
python query.py [question] [options]

Options:
  -i, --interactive        Interactive Q&A session
  -b, --batch FILE         Batch query mode from file
  -o, --output FILE        Output file for batch results (JSON)
  -m, --model MODEL        Ollama model to use
  -k, --top-k N            Number of chunks to retrieve
  -t, --temperature T      Generation temperature (0-2)
  -v, --verbose            Show context chunks
```

## Advanced Features

### Custom Metadata Filtering

```python
# Filter by specific document
response = rag.query(
    question="What is the methodology?",
    filter_metadata={"source_file": "specific_paper.pdf"}
)
```

### Database Statistics

```python
from src import VectorDatabase

db = VectorDatabase()
stats = db.get_collection_stats()
print(f"Total chunks: {stats['total_chunks']}")
print(f"Sample files: {stats['sample_files']}")
```

## Contributing

This is a complete, production-ready system. Potential enhancements:

- [ ] Add support for more document formats (DOCX, HTML)
- [ ] Implement re-ranking for better retrieval
- [ ] Add conversation history for multi-turn queries
- [ ] Web UI using Streamlit or Gradio
- [ ] Support for Qdrant vector database
- [ ] Implement hybrid search (vector + keyword)

## License

This project is provided as-is for research and educational purposes.

## Acknowledgments

- **Ollama**: Local LLM inference
- **ChromaDB**: Vector database
- **pymupdf4llm**: PDF parsing
- **LangChain**: RAG framework inspiration

## Support

For issues or questions:
1. Check the Troubleshooting section above
2. Review logs in `logs/rag_pipeline.log`
3. Ensure Ollama is running and models are pulled
4. Verify PDFs are in the correct format

---

**Built with ❤️ for medical research**
