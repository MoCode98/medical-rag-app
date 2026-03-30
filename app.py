#!/usr/bin/env python3
"""
Medical Research RAG - Web UI Application

FastAPI server that provides a web interface for the RAG pipeline.
Includes document ingestion, query interface, and metrics dashboard.

Usage:
    # Standard mode (development):
    python app.py

    # Desktop mode (production/bundled):
    python app.py --desktop

Then open http://localhost:8000 in your browser.
"""

import argparse
import asyncio
import sys
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from api import ingest, metrics, query
from src.config import settings
from src.logging_config import get_logger, setup_logging
from src.user_data import get_user_data_manager

# Desktop mode flag
IS_DESKTOP_MODE = False

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

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    enabled=settings.rate_limit_enabled,
    default_limits=[f"{settings.rate_limit_per_minute}/minute"]
)

# Create FastAPI app
app = FastAPI(
    title="Medical Research RAG",
    description="Retrieval-Augmented Generation system for medical research documents",
    version="1.0.0",
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
    """Get status of background auto-ingestion with detailed file information."""
    # Get progress tracking information
    from src.ingestion_progress import IngestionProgress
    progress = IngestionProgress()
    progress_status = progress.get_status()

    # Combine with current auto-ingestion status
    status = auto_ingestion_status.copy()
    status["processed_files"] = progress_status.get("processed_files", [])
    status["failed_files"] = progress_status.get("failed_files", [])
    status["total_processed"] = progress_status.get("total_processed", 0)
    status["total_failed"] = progress_status.get("total_failed", 0)

    return status


async def run_auto_ingestion():
    """Background task to auto-ingest PDFs from pdfs/ folder."""
    global auto_ingestion_status

    try:
        from src.pdf_parser import PDFParser
        from src.chunker import IntelligentChunker
        from src.vector_db import VectorDatabase
        from src.ingestion_progress import IngestionProgress

        # Ensure pdfs directory exists
        if IS_DESKTOP_MODE:
            # Desktop mode: use user data directory
            user_data = get_user_data_manager()
            pdf_dir = user_data.get_pdfs_dir()
            logger.info(f"Auto-ingestion: Using PDF directory: {pdf_dir}")
        else:
            # Development mode: use local pdfs/ folder
            pdf_dir = Path("pdfs")
            pdf_dir.mkdir(exist_ok=True)
            logger.info(f"Auto-ingestion: Using PDF directory: {pdf_dir.absolute()}")

        # Get all PDF files
        pdf_files = list(pdf_dir.glob("*.pdf"))
        logger.info(f"Auto-ingestion: Found {len(pdf_files)} PDF files in {pdf_dir}")

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

                # Parse PDF (pass Path object, not string)
                document = await asyncio.get_event_loop().run_in_executor(
                    None, pdf_parser.parse_pdf, pdf_path
                )

                # Chunk text
                chunks = text_chunker.chunk_document(document)

                # Add to vector database
                await asyncio.get_event_loop().run_in_executor(
                    None, vector_db.add_chunks, chunks
                )

                # Mark as processed
                progress.mark_processed(pdf_path.name)

                auto_ingestion_status["files_processed"] = idx

                logger.info(f"Auto-ingestion: Successfully processed {pdf_path.name} ({len(chunks)} chunks)")

            except Exception as e:
                logger.error(f"Auto-ingestion: Failed to process {pdf_path.name}: {e}")
                progress.mark_failed(pdf_path.name, str(e))

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
    if IS_DESKTOP_MODE:
        # Desktop mode: wait for ingestion to complete before opening browser
        logger.info("Starting auto-ingestion (will open browser when complete)...")
        await run_auto_ingestion()
    else:
        # Server mode: run in background
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


def run_desktop():
    """Run in desktop mode with launcher checks."""
    global IS_DESKTOP_MODE
    IS_DESKTOP_MODE = True

    # Import desktop launcher
    from src.desktop_launcher import DesktopLauncher

    # Initialize launcher
    launcher = DesktopLauncher()

    # Check prerequisites (Ollama, models, etc.)
    if not launcher.check_prerequisites():
        logger.error("Prerequisites not met. Exiting.")
        sys.exit(1)

    # Show storage info
    info = launcher.user_data.get_storage_info()
    logger.info(f"User data directory: {info['base_directory']}")

    # Launch server
    logger.info("=" * 80)
    logger.info("Medical Research RAG - Desktop Application")
    logger.info("=" * 80)
    logger.info("")
    logger.info("Starting server...")
    logger.info("  • UI:  http://localhost:8000")
    logger.info("  • API: http://localhost:8000/docs")
    logger.info("")
    logger.info("The application will open in your browser shortly...")
    logger.info("Press CTRL+C to stop")
    logger.info("=" * 80)

    # Open browser after ingestion completes
    import threading

    def delayed_browser():
        import time
        # Wait for server to start
        time.sleep(3)

        # Wait for auto-ingestion to complete
        max_wait = 300  # Maximum 5 minutes
        waited = 0
        while waited < max_wait:
            if auto_ingestion_status.get("complete", False):
                # Ingestion complete
                num_files = auto_ingestion_status.get("files_processed", 0)
                if num_files > 0:
                    logger.info(f"Auto-ingestion complete: {num_files} PDF(s) processed")
                break
            time.sleep(1)
            waited += 1

        # Open browser
        launcher.open_browser()

    browser_thread = threading.Thread(target=delayed_browser, daemon=True)
    browser_thread.start()

    # Run server
    uvicorn.run(
        app,
        host="127.0.0.1",  # Desktop mode: only localhost
        port=8000,
        log_level="info",
        access_log=False,  # Less verbose for desktop
    )


if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Medical Research RAG Application")
    parser.add_argument(
        "--desktop",
        action="store_true",
        help="Run in desktop mode with Ollama checks and auto-browser"
    )
    args = parser.parse_args()

    try:
        if args.desktop:
            run_desktop()
        else:
            main()
    except KeyboardInterrupt:
        logger.info("\n\nServer stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"\nServer failed: {e}", exc_info=True)
        sys.exit(1)
