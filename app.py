#!/usr/bin/env python3
"""
Medical Research RAG - Web UI Application

FastAPI server that provides a web interface for the RAG pipeline.
Includes document ingestion, query interface, and metrics dashboard.

Usage:
    python app.py

Then open http://localhost:8000 in your browser.
"""

import asyncio
import sys
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from api import ingest, metrics, query
from src.config import settings
from src.logging_config import get_logger, setup_logging

# Global state for auto-ingestion
auto_ingestion_status = {
    "running": False,
    "complete": False,
    "files_found": 0,
    "files_processed": 0,
    "message": "Initializing...",
}

# Setup logging
setup_logging(log_level="INFO", log_file=Path(settings.log_file), log_to_console=True)
logger = get_logger()

# Create FastAPI app
app = FastAPI(
    title="Medical Research RAG",
    description="Retrieval-Augmented Generation system for medical research documents",
    version="1.0.0",
)

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
app.include_router(ingest.router, prefix="/api/ingest", tags=["Ingestion"])
app.include_router(query.router, prefix="/api/query", tags=["Query"])
app.include_router(metrics.router, prefix="/api/metrics", tags=["Metrics"])

# Serve static files
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)

# Root endpoint serves the UI
@app.get("/")
async def root():
    """Serve the main UI."""
    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    else:
        return {
            "message": "Medical Research RAG API",
            "status": "running",
            "docs": "/docs",
            "ui": "UI file not found. Please create static/index.html"
        }


# Health check
@app.get("/health")
async def health():
    """API health check."""
    return {"status": "healthy", "service": "Medical Research RAG"}


# Auto-ingestion status endpoint
@app.get("/api/auto-ingest/status")
async def get_auto_ingest_status():
    """Get status of background auto-ingestion."""
    return auto_ingestion_status


async def run_auto_ingestion():
    """Background task to auto-ingest PDFs from pdfs/ folder."""
    global auto_ingestion_status

    try:
        from src.pdf_parser import PDFParser
        from src.chunker import IntelligentChunker
        from src.vector_db import VectorDatabase
        from src.ingestion_progress import IngestionProgress

        # Ensure pdfs directory exists
        pdf_dir = Path("pdfs")
        pdf_dir.mkdir(exist_ok=True)

        # Get all PDF files
        pdf_files = list(pdf_dir.glob("*.pdf"))

        if not pdf_files:
            auto_ingestion_status.update({
                "running": False,
                "complete": True,
                "files_found": 0,
                "files_processed": 0,
                "message": "No PDFs found in pdfs/ folder. Drop PDFs there to auto-ingest on next startup.",
            })
            logger.info("Auto-ingestion: No PDFs found in pdfs/ folder")
            return

        # Check which files are already processed
        progress = IngestionProgress()
        progress_status = progress.get_status()
        processed_files = set(progress_status.get("processed_files", []))

        # Filter out already processed files
        new_files = [f for f in pdf_files if f.name not in processed_files]

        if not new_files:
            auto_ingestion_status.update({
                "running": False,
                "complete": True,
                "files_found": len(pdf_files),
                "files_processed": 0,
                "message": f"All {len(pdf_files)} PDFs already ingested. Ready to query.",
            })
            logger.info(f"Auto-ingestion: All {len(pdf_files)} PDFs already processed")
            return

        # Start ingestion
        auto_ingestion_status.update({
            "running": True,
            "complete": False,
            "files_found": len(new_files),
            "files_processed": 0,
            "message": f"Auto-ingesting {len(new_files)} new PDF(s)...",
        })

        logger.info(f"Auto-ingestion: Starting ingestion of {len(new_files)} new PDF(s)")

        # Initialize components
        pdf_parser = PDFParser()
        text_chunker = IntelligentChunker()
        vector_db = VectorDatabase()

        # Process each new file
        for idx, pdf_path in enumerate(new_files, 1):
            try:
                logger.info(f"Auto-ingestion: Processing {pdf_path.name} ({idx}/{len(new_files)})")

                auto_ingestion_status["message"] = f"Processing {pdf_path.name} ({idx}/{len(new_files)})..."

                # Parse PDF
                document = await asyncio.get_event_loop().run_in_executor(
                    None, pdf_parser.parse_pdf, str(pdf_path)
                )

                # Chunk text
                chunks = text_chunker.chunk_document(document)

                # Add to vector database
                await asyncio.get_event_loop().run_in_executor(
                    None, vector_db.add_chunks, chunks
                )

                # Mark as processed
                progress.mark_file_processed(pdf_path.name, len(chunks))

                auto_ingestion_status["files_processed"] = idx

                logger.info(f"Auto-ingestion: Successfully processed {pdf_path.name} ({len(chunks)} chunks)")

            except Exception as e:
                logger.error(f"Auto-ingestion: Failed to process {pdf_path.name}: {e}")
                progress.mark_file_failed(pdf_path.name, str(e))

        # Complete
        auto_ingestion_status.update({
            "running": False,
            "complete": True,
            "message": f"Auto-ingestion complete. Processed {auto_ingestion_status['files_processed']} of {len(new_files)} new PDF(s).",
        })

        logger.info(f"Auto-ingestion: Complete. Processed {auto_ingestion_status['files_processed']}/{len(new_files)} files")

    except Exception as e:
        logger.error(f"Auto-ingestion failed: {e}", exc_info=True)
        auto_ingestion_status.update({
            "running": False,
            "complete": True,
            "message": f"Auto-ingestion error: {str(e)}",
        })


@app.on_event("startup")
async def startup_event():
    """Run auto-ingestion on startup."""
    logger.info("Starting background auto-ingestion task...")
    asyncio.create_task(run_auto_ingestion())


def main():
    """Start the web server."""
    logger.info("=" * 80)
    logger.info("Medical Research RAG - Web UI")
    logger.info("=" * 80)
    logger.info("")
    logger.info("Starting server...")
    logger.info("  • UI:  http://localhost:8000")
    logger.info("  • API: http://localhost:8000/docs")
    logger.info("")
    logger.info("Press CTRL+C to stop")
    logger.info("=" * 80)

    # Run server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True,
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n\nServer stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"\nServer failed: {e}", exc_info=True)
        sys.exit(1)
