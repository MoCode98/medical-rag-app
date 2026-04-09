"""
RAG (Retrieval-Augmented Generation) pipeline for medical research queries.
Combines vector search with LLM generation using Ollama.
"""

import json
from dataclasses import dataclass
from typing import Any

import ollama

from src.config import settings
from src.logger import logger
from src.vector_db import VectorDatabase


@dataclass
class RAGResponse:
    """Response from the RAG pipeline."""

    question: str
    answer: str
    sources: list[dict[str, Any]]
    context_chunks: list[str]
    model_used: str


class MedicalRAG:
    """
    RAG pipeline for medical research question answering.
    Retrieves relevant context and generates answers using local Ollama models.
    """

    def __init__(
        self,
        vector_db: VectorDatabase = None,
        model: str = None,
        base_url: str | None = None,
        temperature: float = None,
        max_tokens: int = None,
        system_prompt: str = None,
    ):
        """
        Initialize the RAG pipeline.

        Args:
            vector_db: VectorDatabase instance (creates new if None)
            model: Ollama model name (defaults to config)
            base_url: Ollama base URL (defaults to config)
            temperature: Generation temperature (defaults to config)
            max_tokens: Maximum tokens to generate (defaults to config)
            system_prompt: Custom system prompt (uses default if None)
        """
        self.vector_db = vector_db or VectorDatabase()
        self.model = model or settings.ollama_model
        self.base_url = base_url or settings.ollama_base_url
        self.temperature = temperature or settings.temperature
        self.max_tokens = max_tokens or settings.max_tokens

        # Initialize Ollama client with correct host
        self.ollama_client = ollama.Client(host=self.base_url)

        # Default medical research assistant prompt
        self.system_prompt = system_prompt or self._get_default_system_prompt()

        # Check if model is available
        self._check_model_availability()

        logger.info(f"Initialized RAG pipeline with model: {self.model}")

    def _get_default_system_prompt(self) -> str:
        """Get the default system prompt for medical research assistant."""
        return """You are a knowledgeable medical research assistant. Your role is to:

1. Answer questions accurately based on the provided research context
2. Cite specific sources when making claims (reference document names and page numbers)
3. Acknowledge limitations and uncertainties in the research
4. Distinguish between established findings and preliminary results
5. Use clear, precise medical terminology while remaining accessible
6. Highlight any conflicting evidence or alternative interpretations

When answering:
- Base your response PRIMARILY on the provided context
- Always cite sources with [Source: filename, Page: X] format
- If the context doesn't fully answer the question, say so explicitly
- Do not make claims beyond what the research supports
- If appropriate, mention methodological considerations

Be rigorous, evidence-based, and transparent about the limitations of the available research."""

    def _check_model_availability(self) -> None:
        """Check if the configured model is available in Ollama."""
        try:
            response = self.ollama_client.list()
            available_models = [model["name"].split(":")[0] for model in response.get("models", [])]

            if self.model.split(":")[0] not in available_models:
                logger.warning(
                    f"Model '{self.model}' may not be available. "
                    f"Available models: {', '.join(available_models)}"
                )
        except Exception as e:
            logger.warning(f"Could not check model availability: {e}")

    def retrieve_context(
        self, query: str, top_k: int = None, filter_metadata: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """
        Retrieve relevant context for a query.

        Args:
            query: User question
            top_k: Number of chunks to retrieve (defaults to config)
            filter_metadata: Optional metadata filters

        Returns:
            List of retrieved chunks with metadata
        """
        top_k = top_k or settings.top_k_results

        try:
            results = self.vector_db.query(
                query_text=query, top_k=top_k, filter_metadata=filter_metadata
            )

            logger.info(f"Retrieved {len(results)} context chunks for query")
            return results

        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            raise

    def format_context(self, retrieved_chunks: list[dict[str, Any]]) -> str:
        """
        Format retrieved chunks into context string for the LLM.

        Args:
            retrieved_chunks: List of retrieved chunks with metadata

        Returns:
            Formatted context string
        """
        context_parts = []

        for i, chunk in enumerate(retrieved_chunks, 1):
            metadata = chunk["metadata"]
            source_file = metadata.get("source_file", "Unknown")
            section = metadata.get("section_title", "N/A")
            pages = metadata.get("page_numbers", [])
            page_str = f"Page(s): {', '.join(map(str, pages))}" if pages else "Page: Unknown"

            context_parts.append(
                f"[Context {i}]\n"
                f"Source: {source_file}\n"
                f"Section: {section}\n"
                f"{page_str}\n"
                f"Content: {chunk['content']}\n"
            )

        return "\n---\n".join(context_parts)

    def generate_answer(self, query: str, context: str, stream: bool = False) -> str:
        """
        Generate answer using Ollama model.

        Args:
            query: User question
            context: Retrieved context
            stream: Whether to stream the response

        Returns:
            Generated answer
        """
        # Construct the prompt
        user_message = f"""Based on the following research context, please answer the question.

CONTEXT:
{context}

QUESTION: {query}

ANSWER (remember to cite sources):"""

        try:
            response = self.ollama_client.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_message},
                ],
                options={
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens,
                },
            )

            answer = response["message"]["content"]
            logger.info(f"Generated answer ({len(answer)} chars)")

            return answer

        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            raise

    def query(
        self,
        question: str,
        top_k: int = None,
        filter_metadata: dict[str, Any] | None = None,
        return_context: bool = True,
    ) -> RAGResponse:
        """
        Complete RAG query: retrieve context and generate answer.

        Args:
            question: User question
            top_k: Number of chunks to retrieve
            filter_metadata: Optional metadata filters
            return_context: Whether to include context chunks in response

        Returns:
            RAGResponse with answer and sources
        """
        logger.info(f"Processing RAG query: '{question[:100]}...'")

        # Step 1: Retrieve context
        retrieved_chunks = self.retrieve_context(
            query=question, top_k=top_k, filter_metadata=filter_metadata
        )

        if not retrieved_chunks:
            logger.warning("No context retrieved for query")
            return RAGResponse(
                question=question,
                answer="I couldn't find relevant information in the available research documents to answer this question.",
                sources=[],
                context_chunks=[],
                model_used=self.model,
            )

        # Step 2: Format context
        context = self.format_context(retrieved_chunks)

        # Step 3: Generate answer
        answer = self.generate_answer(question, context)

        # Step 4: Prepare sources
        sources = []
        for chunk in retrieved_chunks:
            metadata = chunk["metadata"]
            sources.append(
                {
                    "file": metadata.get("source_file", "Unknown"),
                    "title": metadata.get("source_title", "Unknown"),
                    "section": metadata.get("section_title", "N/A"),
                    "pages": metadata.get("page_numbers", []),
                    "similarity": chunk.get("similarity", 0.0),
                    "context": chunk.get("content", ""),  # Include context text
                }
            )

        # Step 5: Create response
        response = RAGResponse(
            question=question,
            answer=answer,
            sources=sources,
            context_chunks=[c["content"] for c in retrieved_chunks] if return_context else [],
            model_used=self.model,
        )

        logger.info("RAG query completed successfully")
        return response

    def interactive_session(self) -> None:
        """
        Start an interactive Q&A session.
        """
        print("\n" + "=" * 80)
        print("Medical Research RAG Assistant - Interactive Session")
        print("=" * 80)
        print(f"Model: {self.model}")
        print(
            f"Database: {self.vector_db.collection_name} ({self.vector_db.collection.count()} chunks)"
        )
        print("\nType 'quit' or 'exit' to end the session.")
        print("Type 'stats' to see database statistics.")
        print("=" * 80 + "\n")

        while True:
            try:
                question = input("\nYour question: ").strip()

                if not question:
                    continue

                if question.lower() in ["quit", "exit", "q"]:
                    print("\nGoodbye!")
                    break

                if question.lower() == "stats":
                    stats = self.vector_db.get_collection_stats()
                    print("\nDatabase Statistics:")
                    print(json.dumps(stats, indent=2))
                    continue

                # Process query
                print("\n" + "-" * 80)
                print("Retrieving context and generating answer...")
                print("-" * 80 + "\n")

                response = self.query(question, return_context=False)

                # Display answer
                print(f"ANSWER:\n{response.answer}\n")

                # Display sources
                print("\nSOURCES:")
                for i, source in enumerate(response.sources, 1):
                    pages = ", ".join(map(str, source["pages"])) if source["pages"] else "Unknown"
                    print(
                        f"{i}. {source['file']} - {source['section']} "
                        f"(Page(s): {pages}, Similarity: {source['similarity']:.3f})"
                    )

                print("\n" + "-" * 80)

            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                logger.error(f"Error in interactive session: {e}")
                print(f"\nError: {e}\n")


if __name__ == "__main__":
    # Test RAG pipeline
    try:
        # Initialize RAG
        rag = MedicalRAG()

        # Check if database has data
        stats = rag.vector_db.get_collection_stats()
        if stats["total_chunks"] == 0:
            print("No data in vector database. Please run the ingestion pipeline first.")
            print("Run: python src/ingest.py")
        else:
            # Start interactive session
            rag.interactive_session()

    except Exception as e:
        logger.error(f"Error starting RAG pipeline: {e}")
        print(f"Error: {e}")
