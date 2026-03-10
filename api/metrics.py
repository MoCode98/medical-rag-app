"""
Metrics API endpoints for system statistics and monitoring.
"""

from typing import Any

from fastapi import APIRouter, HTTPException

from src.config import settings
from src.ingestion_progress import IngestionProgress
from src.logging_config import get_logger
from src.metrics import get_metrics
from src.vector_db import VectorDatabase

router = APIRouter()
logger = get_logger()


@router.get("/stats")
async def get_all_stats() -> dict[str, Any]:
    """
    Get all system statistics.

    Returns:
        Dictionary with database, cache, and ingestion stats
    """
    try:
        # Database stats
        vector_db = VectorDatabase()
        db_stats = vector_db.get_collection_stats()

        # Ingestion progress
        progress = IngestionProgress()
        progress_status = progress.get_status()

        # Embedding cache stats
        cache_stats = None
        try:
            from src.embeddings import OllamaEmbeddings
            embeddings = OllamaEmbeddings()
            if hasattr(embeddings, "cache") and embeddings.cache:
                cache_stats = embeddings.cache.get_stats()
        except Exception:
            pass

        # Metrics
        metrics = get_metrics()
        all_metrics = metrics.get_all_metrics()

        return {
            "success": True,
            "database": {
                "total_chunks": db_stats.get("total_chunks", 0),
                "collection_name": db_stats.get("collection_name", ""),
                "db_path": db_stats.get("db_path", ""),
                "sample_files": db_stats.get("sample_files", [])
            },
            "ingestion": {
                "total_processed": progress_status.get("total_processed", 0),
                "total_failed": progress_status.get("total_failed", 0),
                "failed_files": progress_status.get("failed_files", [])
            },
            "cache": cache_stats if cache_stats else {
                "hits": 0,
                "misses": 0,
                "hit_rate_percent": 0.0,
                "total_requests": 0
            },
            "metrics": all_metrics
        }

    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/database")
async def get_database_stats() -> dict[str, Any]:
    """
    Get database-specific statistics.

    Returns:
        Database statistics
    """
    try:
        vector_db = VectorDatabase()
        stats = vector_db.get_collection_stats()

        return {
            "success": True,
            "stats": stats
        }

    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache")
async def get_cache_stats() -> dict[str, Any]:
    """
    Get embedding cache statistics.

    Returns:
        Cache statistics
    """
    try:
        from src.embeddings import OllamaEmbeddings
        embeddings = OllamaEmbeddings()

        if hasattr(embeddings, "cache") and embeddings.cache:
            cache_stats = embeddings.cache.get_stats()
            cache_size = embeddings.cache.get_cache_size()

            return {
                "success": True,
                "stats": cache_stats,
                "size": cache_size
            }
        else:
            return {
                "success": False,
                "error": "Cache not available",
                "stats": {
                    "hits": 0,
                    "misses": 0,
                    "hit_rate_percent": 0.0,
                    "total_requests": 0
                }
            }

    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        return {
            "success": False,
            "error": str(e),
            "stats": {
                "hits": 0,
                "misses": 0,
                "hit_rate_percent": 0.0,
                "total_requests": 0
            }
        }


@router.get("/health")
async def health_check() -> dict[str, Any]:
    """
    Health check endpoint.

    Returns:
        System health status
    """
    try:
        # Check database
        vector_db = VectorDatabase()
        db_stats = vector_db.get_collection_stats()
        db_healthy = db_stats.get("total_chunks", 0) > 0

        # Check Ollama
        ollama_healthy = False
        try:
            import requests
            response = requests.get(f"{settings.ollama_base_url}/api/tags", timeout=5)
            ollama_healthy = response.status_code == 200
        except Exception:
            pass

        return {
            "success": True,
            "status": "healthy" if (db_healthy and ollama_healthy) else "degraded",
            "components": {
                "database": "healthy" if db_healthy else "empty",
                "ollama": "healthy" if ollama_healthy else "unreachable",
                "api": "healthy"
            },
            "database_chunks": db_stats.get("total_chunks", 0)
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "success": False,
            "status": "unhealthy",
            "error": str(e)
        }
