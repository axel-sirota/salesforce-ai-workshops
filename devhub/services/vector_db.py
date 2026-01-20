"""
VectorDB Service
================

ChromaDB-based semantic search for documentation.

INTENTIONAL PROBLEMS (for workshop debugging):
- 10% slow queries (3000ms latency)
- 5% connection failures
- 15% low similarity results (bad retrieval)

Students will add OpenTelemetry tracing to find these issues.
"""

import json
import random
import time
from pathlib import Path

import chromadb
from chromadb.config import Settings

from config import Config


class VectorDB:
    """
    Vector database for semantic document search.

    Uses ChromaDB with sentence-transformer embeddings.
    Has intentional failure modes for workshop exercises.
    """

    def __init__(self, docs_path: str | None = None):
        """
        Initialize VectorDB with ChromaDB.

        Args:
            docs_path: Path to docs.json. Defaults to Config.DOCS_PATH.
        """
        self.docs_path = docs_path or Config.DOCS_PATH

        # Initialize ChromaDB with ephemeral storage
        self._client = chromadb.Client(Settings(
            anonymized_telemetry=False,
            allow_reset=True
        ))

        # Create or get collection
        self._collection = self._client.get_or_create_collection(
            name="devhub_docs",
            metadata={"hnsw:space": "cosine"}
        )

        # Load documents
        self._load_documents()

    def _load_documents(self):
        """Load documents from JSON into ChromaDB."""
        docs_file = Path(self.docs_path)
        if not docs_file.exists():
            raise FileNotFoundError(f"Documents file not found: {self.docs_path}")

        with open(docs_file) as f:
            documents = json.load(f)

        # Add documents to collection
        ids = []
        texts = []
        metadatas = []

        for doc in documents:
            ids.append(doc["id"])
            texts.append(doc["content"])
            metadatas.append({
                "id": doc["id"],
                "title": doc["title"],
                "category": doc["category"]
            })

        # Upsert to handle re-initialization
        self._collection.upsert(
            ids=ids,
            documents=texts,
            metadatas=metadatas
        )

        self._doc_count = len(documents)

    def search(self, query: str, top_k: int = 3) -> dict:
        """
        Search for documents matching the query.

        Args:
            query: Search query text
            top_k: Number of results to return

        Returns:
            dict with keys: documents, metadatas, distances, latency_ms

        Raises:
            ConnectionError: Simulated connection failure (5% rate)
        """
        start_time = time.time()

        # === INTENTIONAL PROBLEM 1: Connection Failure (5%) ===
        if random.random() < Config.VECTOR_DB_FAILURE_RATE:
            raise ConnectionError("VectorDB connection failed: ECONNREFUSED")

        # === INTENTIONAL PROBLEM 2: Slow Query (10%) ===
        if random.random() < Config.VECTOR_DB_SLOW_QUERY_RATE:
            # Simulate slow query
            time.sleep(Config.VECTOR_DB_SLOW_QUERY_LATENCY / 1000)
        else:
            # Normal latency
            latency = random.randint(
                Config.VECTOR_DB_LATENCY_MIN,
                Config.VECTOR_DB_LATENCY_MAX
            )
            time.sleep(latency / 1000)

        # Perform the actual search
        results = self._collection.query(
            query_texts=[query],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )

        # === INTENTIONAL PROBLEM 3: Low Similarity (15%) ===
        distances = results["distances"][0] if results["distances"] else []
        if random.random() < Config.VECTOR_DB_LOW_SIMILARITY_RATE:
            # Artificially inflate distances (lower similarity)
            distances = [d + 0.5 for d in distances]  # Push above threshold

        latency_ms = int((time.time() - start_time) * 1000)

        return {
            "documents": results["documents"][0] if results["documents"] else [],
            "metadatas": results["metadatas"][0] if results["metadatas"] else [],
            "distances": distances,
            "latency_ms": latency_ms
        }

    @property
    def document_count(self) -> int:
        """Return number of documents in the collection."""
        return self._doc_count
