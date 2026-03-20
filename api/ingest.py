"""
Ingestion API endpoints for document upload and processing.
"""

import asyncio
import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect

from src.chunker import IntelligentChunker
from src.config import settings
from src.file_utils import check_directory_writable, check_disk_space
from src.ingestion_progress import IngestionProgress
from src.logging_config import get_logger
from src.metrics import get_metrics
from src.pdf_parser import PDFParser
from src.validation import ValidationError, validate_filename
from src.vector_db import VectorDatabase

router = APIRouter()
logger = get_logger()

# Global state for tracking ingestion
ingestion_status = {"is_running": False, "progress": 0, "message": "", "files_processed": []}


@router.post("/upload")
async def upload_pdfs(files: list[UploadFile] = File(...)) -> dict[str, Any]:
    """
    Upload PDF files to the pdf folder.

    Args:
        files: List of uploaded PDF files

    Returns:
        Dictionary with upload status and file list
    """
    try:
        pdf_dir = Path(settings.pdf_folder)
        pdf_dir.mkdir(parents=True, exist_ok=True)

        uploaded_files = []
        failed_files = []

        for file in files:
            try:
                # Validate filename for security
                validated_filename = validate_filename(
                    file.filename,
                    allowed_extensions=settings.allowed_file_extensions
                )
            except ValidationError as e:
                failed_files.append({"file": file.filename, "error": str(e)})
                continue

            # Check file size
            content = await file.read()
            max_size_bytes = settings.max_upload_file_size_mb * 1024 * 1024
            if len(content) > max_size_bytes:
                failed_files.append({
                    "file": validated_filename,
                    "error": f"File size exceeds {settings.max_upload_file_size_mb}MB"
                })
                continue

            # Save file with validated filename
            file_path = pdf_dir / validated_filename
            with open(file_path, "wb") as f:
                f.write(content)

            uploaded_files.append(validated_filename)
            logger.info(f"Uploaded: {validated_filename}")

        return {
            "success": True,
            "uploaded": uploaded_files,
            "failed": failed_files,
            "total": len(uploaded_files),
        }

    except Exception as e:
        logger.error(f"Upload error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest")
async def start_ingestion(reset: bool = False) -> dict[str, Any]:
    """
    Start the ingestion pipeline (non-blocking).

    Args:
        reset: Whether to reset the vector database

    Returns:
        Status message
    """
    global ingestion_status

    if ingestion_status["is_running"]:
        return {"success": False, "error": "Ingestion already running"}

    # Reset status
    ingestion_status = {"is_running": True, "progress": 0, "message": "Starting ingestion...", "files_processed": []}

    # Start ingestion in background (will be handled by WebSocket)
    return {"success": True, "message": "Ingestion started. Connect to WebSocket for progress updates."}


@router.get("/status")
async def get_ingestion_status() -> dict[str, Any]:
    """
    Get current ingestion status.

    Returns:
        Current ingestion status
    """
    return ingestion_status


@router.websocket("/stream")
async def websocket_ingestion(websocket: WebSocket):
    """
    WebSocket endpoint for real-time ingestion progress updates.
    """
    global ingestion_status

    await websocket.accept()
    logger.info("WebSocket connection established")

    try:
        # Wait for start signal
        data = await websocket.receive_text()
        params = json.loads(data)
        reset = params.get("reset", False)

        # Start ingestion
        ingestion_status["is_running"] = True
        await websocket.send_json({"type": "status", "message": "Ingestion started", "progress": 0})

        # Run ingestion with progress updates
        try:
            await run_ingestion_pipeline(websocket, reset)
            ingestion_status["is_running"] = False
            await websocket.send_json({"type": "complete", "message": "Ingestion complete", "progress": 100})

        except Exception as e:
            logger.error(f"Ingestion error: {e}", exc_info=True)
            ingestion_status["is_running"] = False
            await websocket.send_json({"type": "error", "message": str(e), "progress": 0})

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
        ingestion_status["is_running"] = False
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ingestion_status["is_running"] = False


async def run_ingestion_pipeline(websocket: WebSocket, reset: bool = False):
    """
    Run the complete ingestion pipeline with progress updates.

    Args:
        websocket: WebSocket connection for progress updates
        reset: Whether to reset the database
    """
    metrics = get_metrics()
    metrics.start_timer("total_ingestion")

    # Step 1: Validate environment
    await websocket.send_json({"type": "log", "message": "Validating environment..."})
    pdf_dir = Path(settings.pdf_folder)
    check_directory_writable(Path(settings.data_folder), create_if_missing=True)
    check_disk_space(Path(settings.data_folder), required_mb=500)

    # Step 2: Get PDF files
    await websocket.send_json({"type": "log", "message": "Scanning PDF folder...", "progress": 10})
    pdf_parser = PDFParser()
    pdf_files = pdf_parser.get_pdf_files()

    if not pdf_files:
        raise Exception(f"No PDF files found in {settings.pdf_folder}")

    # Check ingestion progress
    progress = IngestionProgress()
    if reset:
        progress.clear()
        await websocket.send_json({"type": "log", "message": "Database reset requested"})

    remaining_files = progress.get_remaining_files(pdf_files)
    await websocket.send_json({
        "type": "log",
        "message": f"Found {len(pdf_files)} PDFs ({len(remaining_files)} to process)",
        "progress": 20
    })

    if not remaining_files:
        await websocket.send_json({"type": "log", "message": "All PDFs already processed"})
        return

    # Step 3: Parse PDFs
    await websocket.send_json({"type": "log", "message": "Parsing PDFs...", "progress": 30})
    documents = []
    total_files = len(remaining_files)

    for idx, pdf_file in enumerate(remaining_files):
        try:
            await websocket.send_json({
                "type": "log",
                "message": f"Processing: {pdf_file.name} ({idx + 1}/{total_files})"
            })

            # Run PDF parsing in executor to avoid blocking
            loop = asyncio.get_event_loop()
            doc = await loop.run_in_executor(None, pdf_parser.parse_pdf, pdf_file)

            if doc:
                documents.append(doc)
                progress.mark_processed(str(pdf_file))
                await websocket.send_json({
                    "type": "log",
                    "message": f"✓ Completed: {pdf_file.name}",
                    "progress": 30 + int((idx + 1) / total_files * 20)
                })
            else:
                progress.mark_failed(str(pdf_file), "No content extracted")
                await websocket.send_json({"type": "log", "message": f"⚠ No content: {pdf_file.name}"})

        except Exception as e:
            progress.mark_failed(str(pdf_file), str(e))
            await websocket.send_json({"type": "log", "message": f"✗ Failed: {pdf_file.name} - {e}"})

    if not documents:
        raise Exception("Failed to parse any documents")

    await websocket.send_json({"type": "log", "message": f"Parsed {len(documents)} documents", "progress": 50})

    # Step 4: Chunk documents
    await websocket.send_json({"type": "log", "message": "Chunking documents...", "progress": 60})
    chunker = IntelligentChunker(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        min_chunk_size=settings.min_chunk_size,
    )

    loop = asyncio.get_event_loop()
    chunks = await loop.run_in_executor(None, chunker.chunk_documents, documents)

    if not chunks:
        raise Exception("Failed to create chunks")

    avg_chunk_size = sum(c.token_count for c in chunks) / len(chunks)
    await websocket.send_json({
        "type": "log",
        "message": f"Created {len(chunks)} chunks (avg: {avg_chunk_size:.1f} tokens)",
        "progress": 70
    })

    # Step 5: Store in vector database
    await websocket.send_json({"type": "log", "message": "Storing in vector database...", "progress": 80})
    vector_db = VectorDatabase(reset=reset)

    # Add chunks (this may take a while with embeddings)
    await loop.run_in_executor(None, vector_db.add_chunks, chunks)

    stats = vector_db.get_collection_stats()
    await websocket.send_json({
        "type": "log",
        "message": f"Database now contains {stats['total_chunks']} chunks",
        "progress": 95
    })

    # Get embedding cache stats
    try:
        from src.embeddings import OllamaEmbeddings
        embeddings = OllamaEmbeddings()
        if hasattr(embeddings, "cache") and embeddings.cache:
            cache_stats = embeddings.cache.get_stats()
            await websocket.send_json({
                "type": "log",
                "message": f"Cache hit rate: {cache_stats['hit_rate_percent']:.1f}%"
            })
    except Exception:
        pass

    metrics.stop_timer("total_ingestion")
    await websocket.send_json({"type": "log", "message": "Ingestion complete!", "progress": 100})
