"""
Query API endpoints for RAG queries.
"""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.config import settings
from src.logging_config import get_logger
from src.metrics import get_metrics
from src.rag_pipeline import MedicalRAG
from src.validation import ValidationError, validate_query
from src.vector_db import VectorDatabase

router = APIRouter()
logger = get_logger()

# Global RAG instance (lazy loaded)
_rag_instance: MedicalRAG | None = None


def get_rag() -> MedicalRAG:
    """Get or create RAG instance."""
    global _rag_instance
    if _rag_instance is None:
        try:
            vector_db = VectorDatabase()
            stats = vector_db.get_collection_stats()

            if stats["total_chunks"] == 0:
                raise HTTPException(
                    status_code=400,
                    detail="Vector database is empty. Please ingest documents first."
                )

            _rag_instance = MedicalRAG(vector_db=vector_db)
            logger.info(f"RAG initialized with {stats['total_chunks']} chunks")

        except Exception as e:
            logger.error(f"Failed to initialize RAG: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to initialize RAG: {str(e)}")

    return _rag_instance


class QueryRequest(BaseModel):
    """Request model for query endpoint."""
    question: str
    top_k: int = 5
    model: str | None = None
    temperature: float | None = None
    return_context: bool = False


class QueryResponse(BaseModel):
    """Response model for query endpoint."""
    question: str
    answer: str
    sources: list[dict[str, Any]]
    context_chunks: list[str] | None = None
    model_used: str
    query_time: float


@router.post("/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest) -> QueryResponse:
    """
    Submit a query to the RAG system.

    Args:
        request: Query request with question and parameters

    Returns:
        Query response with answer and sources
    """
    metrics = get_metrics()

    try:
        # Validate query
        question = validate_query(request.question)

        # Get RAG instance
        rag = get_rag()

        # Override model/temperature if specified
        if request.model:
            rag.model = request.model
        if request.temperature is not None:
            rag.temperature = request.temperature

        # Execute query
        metrics.start_timer("api_query")
        response = rag.query(
            question=question,
            top_k=request.top_k,
            return_context=request.return_context
        )
        query_time = metrics.stop_timer("api_query")

        logger.info(f"Query processed in {query_time:.2f}s: {question[:50]}...")

        return QueryResponse(
            question=response.question,
            answer=response.answer,
            sources=response.sources,
            context_chunks=response.context_chunks if request.return_context else None,
            model_used=response.model_used,
            query_time=query_time
        )

    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Query error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models")
async def get_available_models() -> dict[str, Any]:
    """
    Get list of available Ollama models.

    Returns:
        Dictionary with available models
    """
    try:
        import requests
        response = requests.get(f"{settings.ollama_base_url}/api/tags", timeout=5)
        response.raise_for_status()
        models = response.json().get("models", [])

        return {
            "success": True,
            "models": [m["name"] for m in models],
            "default": settings.ollama_model
        }

    except Exception as e:
        logger.error(f"Failed to fetch models: {e}")
        return {
            "success": False,
            "models": [settings.ollama_model],
            "default": settings.ollama_model,
            "error": "Could not connect to Ollama"
        }


@router.post("/reset")
async def reset_rag() -> dict[str, Any]:
    """
    Reset the RAG instance (force reload).

    Returns:
        Status message
    """
    global _rag_instance
    _rag_instance = None
    logger.info("RAG instance reset")

    return {"success": True, "message": "RAG instance reset successfully"}
