"""
Vector database module using ChromaDB for local storage and retrieval.
Stores document chunks with embeddings for semantic search.
"""

import json
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings

from src.chunker import TextChunk
from src.config import settings
from src.embeddings import OllamaEmbeddings
from src.logger import logger


class VectorDatabase:
    """
    Vector database for storing and retrieving document chunks.
    Uses ChromaDB with Ollama embeddings.
    """

    def __init__(
        self, db_path: str = None, collection_name: str = "medical_research", reset: bool = False
    ):
        """
        Initialize the vector database.

        Args:
            db_path: Path to persist the database
            collection_name: Name of the collection
            reset: Whether to reset (delete) existing database
        """
        self.db_path = Path(db_path or settings.vector_db_path)
        self.collection_name = collection_name

        # Create directory if it doesn't exist
        self.db_path.mkdir(parents=True, exist_ok=True)

        # Initialize Ollama embeddings
        self.embeddings = OllamaEmbeddings()

        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(
            path=str(self.db_path),
            settings=ChromaSettings(anonymized_telemetry=False, allow_reset=True),
        )

        # Reset if requested
        if reset:
            logger.warning(f"Resetting vector database at {self.db_path}")
            try:
                self.client.delete_collection(name=self.collection_name)
                logger.info(f"Deleted existing collection '{self.collection_name}'")
            except Exception as e:
                logger.info(f"No existing collection to delete: {e}")

        # Get or create collection
        try:
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},  # Use cosine similarity
            )
            logger.info(
                f"Initialized collection '{self.collection_name}' "
                f"with {self.collection.count()} documents"
            )
        except Exception as e:
            logger.error(f"Error creating collection: {e}")
            raise

    def add_chunks(self, chunks: list[TextChunk], batch_size: int | None = None) -> None:
        """
        Add text chunks to the vector database.

        Args:
            chunks: List of TextChunk objects
            batch_size: Number of chunks to process in each batch
        """
        if batch_size is None:
            batch_size = settings.vector_db_batch_size
        if not chunks:
            logger.warning("No chunks to add to database")
            return

        logger.info(f"Adding {len(chunks)} chunks to vector database...")

        # Process in batches to avoid memory issues
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]

            # Prepare data for batch
            documents = [chunk.content for chunk in batch]
            ids = [chunk.chunk_id for chunk in batch]
            metadatas = []

            for chunk in batch:
                # Prepare metadata (ChromaDB requires simple types)
                metadata = {
                    "source_file": chunk.source_file,
                    "source_title": chunk.source_title,
                    "section_title": chunk.section_title or "N/A",
                    "chunk_index": chunk.chunk_index,
                    "total_chunks": chunk.total_chunks,
                    "token_count": chunk.token_count,
                    "page_numbers": json.dumps(chunk.page_numbers),  # Store as JSON string
                    "file_path": chunk.metadata.get("file_path", ""),
                }
                metadatas.append(metadata)

            # Generate embeddings for batch
            try:
                embeddings = self.embeddings.embed_texts(documents, show_progress=False)

                # Add to collection
                self.collection.add(
                    documents=documents, embeddings=embeddings, ids=ids, metadatas=metadatas
                )

                logger.info(f"Added batch {i//batch_size + 1}/{(len(chunks)-1)//batch_size + 1}")

            except Exception as e:
                logger.error(f"Error adding batch starting at index {i}: {e}")
                raise

        logger.info(
            f"Successfully added {len(chunks)} chunks. "
            f"Total documents in database: {self.collection.count()}"
        )

    def query(
        self, query_text: str, top_k: int = None, filter_metadata: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """
        Query the vector database for relevant chunks.

        Args:
            query_text: Query string
            top_k: Number of results to return (defaults to config)
            filter_metadata: Optional metadata filters

        Returns:
            List of results with documents, metadata, and distances
        """
        top_k = top_k or settings.top_k_results

        try:
            # Generate query embedding
            query_embedding = self.embeddings.embed_query(query_text)

            # Query the collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filter_metadata,
                include=["documents", "metadatas", "distances"],
            )

            # Format results
            formatted_results = []
            for i in range(len(results["documents"][0])):
                result = {
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i],
                    "similarity": 1 - results["distances"][0][i],  # Convert distance to similarity
                }

                # Parse page numbers from JSON
                if "page_numbers" in result["metadata"]:
                    try:
                        result["metadata"]["page_numbers"] = json.loads(
                            result["metadata"]["page_numbers"]
                        )
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse page_numbers JSON: {e}")
                        result["metadata"]["page_numbers"] = []

                formatted_results.append(result)

            logger.info(f"Found {len(formatted_results)} results for query: '{query_text[:50]}...'")
            return formatted_results

        except Exception as e:
            logger.error(f"Error querying database: {e}")
            raise

    def get_collection_stats(self) -> dict[str, Any]:
        """
        Get statistics about the vector database collection.

        Returns:
            Dictionary with collection statistics
        """
        count = self.collection.count()

        # Get sample documents to analyze
        if count > 0:
            sample = self.collection.peek(limit=min(10, count))
            unique_files = set()

            for metadata in sample.get("metadatas", []):
                if "source_file" in metadata:
                    unique_files.add(metadata["source_file"])

            stats = {
                "total_chunks": count,
                "collection_name": self.collection_name,
                "db_path": str(self.db_path),
                "sample_files": list(unique_files),
            }
        else:
            stats = {
                "total_chunks": 0,
                "collection_name": self.collection_name,
                "db_path": str(self.db_path),
            }

        return stats

    def hybrid_search(
        self,
        query_text: str,
        top_k: int = None,
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3,
        filter_metadata: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Hybrid search combining vector similarity and keyword matching.

        Args:
            query_text: Query string
            top_k: Number of results to return (defaults to config)
            vector_weight: Weight for vector similarity (0-1)
            keyword_weight: Weight for keyword matching (0-1)
            filter_metadata: Optional metadata filters

        Returns:
            List of results with hybrid scores
        """
        top_k = top_k or settings.top_k_results

        # Get more results for re-ranking
        vector_results = self.query(
            query_text,
            top_k=top_k * 2,  # Retrieve more for keyword filtering
            filter_metadata=filter_metadata,
        )

        # Extract keywords from query (simple tokenization)
        keywords = set(query_text.lower().split())

        # Calculate hybrid scores
        for result in vector_results:
            content_lower = result["content"].lower()

            # Keyword matching score
            matched_keywords = sum(1 for kw in keywords if kw in content_lower)
            keyword_score = matched_keywords / len(keywords) if keywords else 0

            # Combine scores
            result["keyword_score"] = keyword_score
            result["hybrid_score"] = (
                result["similarity"] * vector_weight + keyword_score * keyword_weight
            )

        # Re-rank by hybrid score
        reranked = sorted(vector_results, key=lambda x: x["hybrid_score"], reverse=True)

        logger.info(
            f"Hybrid search completed: {len(reranked[:top_k])} results "
            f"(vector_weight={vector_weight}, keyword_weight={keyword_weight})"
        )

        return reranked[:top_k]

    def delete_collection(self) -> None:
        """Delete the entire collection."""
        try:
            self.client.delete_collection(name=self.collection_name)
            logger.info(f"Deleted collection '{self.collection_name}'")
        except Exception as e:
            logger.error(f"Error deleting collection: {e}")
            raise


if __name__ == "__main__":
    # Test vector database
    from src.chunker import IntelligentChunker
    from src.pdf_parser import PDFParser

    # Parse PDFs
    parser = PDFParser()
    docs = parser.parse_all(save_json=False)

    if docs:
        # Chunk documents
        chunker = IntelligentChunker()
        chunks = chunker.chunk_documents(docs)

        if chunks:
            # Initialize database
            db = VectorDatabase(reset=True)

            # Add chunks
            db.add_chunks(chunks)

            # Test query
            results = db.query("What are the main findings?", top_k=3)

            print("\nQuery Results:")
            for i, result in enumerate(results, 1):
                print(f"\n{i}. Similarity: {result['similarity']:.3f}")
                print(f"   Source: {result['metadata']['source_file']}")
                print(f"   Section: {result['metadata']['section_title']}")
                print(f"   Content: {result['content'][:200]}...")

            # Show stats
            stats = db.get_collection_stats()
            print(f"\nDatabase Stats: {stats}")
