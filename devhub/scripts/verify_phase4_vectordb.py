#!/usr/bin/env python3
"""
Phase 4 Verification: VectorDB Service
=======================================

Verifies:
- ChromaDB initializes correctly
- Documents load from docs.json
- Search returns relevant results
- Failure modes are configured
"""

import sys

# Add parent to path for imports
sys.path.insert(0, str(__file__).rsplit("/scripts", 1)[0])

from config import Config


def verify_initialization():
    """Verify VectorDB initializes with ChromaDB."""
    try:
        from services.vector_db import VectorDB
        vdb = VectorDB()
        assert vdb.document_count == 8, f"Expected 8 docs, got {vdb.document_count}"
        print(f"✓ VectorDB initialized with {vdb.document_count} documents")
        return True
    except Exception as e:
        print(f"❌ Initialization error: {e}")
        return False


def verify_search():
    """Verify search returns relevant results."""
    try:
        from services.vector_db import VectorDB

        # Disable failures for this test
        orig_rate = Config.VECTOR_DB_FAILURE_RATE
        Config.VECTOR_DB_FAILURE_RATE = 0

        vdb = VectorDB()
        result = vdb.search("payments authentication")

        Config.VECTOR_DB_FAILURE_RATE = orig_rate

        assert len(result["documents"]) > 0, "No results returned"
        assert "Payments" in result["metadatas"][0]["title"], "Wrong top result"
        assert "latency_ms" in result, "Missing latency_ms"

        print(f"✓ Search works: top result = {result['metadatas'][0]['title']}")
        return True
    except Exception as e:
        print(f"❌ Search error: {e}")
        return False


def verify_failure_modes():
    """Verify failure modes are configured correctly."""
    try:
        assert Config.VECTOR_DB_FAILURE_RATE == 0.05, "Wrong failure rate"
        assert Config.VECTOR_DB_SLOW_QUERY_RATE == 0.10, "Wrong slow query rate"
        assert Config.VECTOR_DB_LOW_SIMILARITY_RATE == 0.15, "Wrong low similarity rate"
        assert Config.VECTOR_DB_SLOW_QUERY_LATENCY == 3000, "Wrong slow latency"

        print("✓ Failure modes configured:")
        print(f"  - Connection failure: {Config.VECTOR_DB_FAILURE_RATE*100:.0f}%")
        print(f"  - Slow query: {Config.VECTOR_DB_SLOW_QUERY_RATE*100:.0f}%")
        print(f"  - Low similarity: {Config.VECTOR_DB_LOW_SIMILARITY_RATE*100:.0f}%")
        return True
    except Exception as e:
        print(f"❌ Failure mode config error: {e}")
        return False


def verify_failure_injection():
    """Verify failure injection mechanism works."""
    try:
        from services.vector_db import VectorDB

        # Test low similarity injection
        Config.VECTOR_DB_LOW_SIMILARITY_RATE = 1.0
        Config.VECTOR_DB_FAILURE_RATE = 0
        Config.VECTOR_DB_SLOW_QUERY_RATE = 0

        vdb = VectorDB()
        result = vdb.search("payments")

        # Reset
        Config.VECTOR_DB_LOW_SIMILARITY_RATE = 0.15

        assert result["distances"][0] > 0.5, "Low similarity injection not working"
        print("✓ Failure injection mechanism verified")
        return True
    except Exception as e:
        print(f"❌ Failure injection error: {e}")
        return False


def main():
    print("=" * 50)
    print("Phase 4 Verification: VectorDB Service")
    print("=" * 50)

    results = [
        verify_initialization(),
        verify_search(),
        verify_failure_modes(),
        verify_failure_injection(),
    ]

    print("=" * 50)
    if all(results):
        print("✓ Phase 4 PASSED")
        return 0
    else:
        print("❌ Phase 4 FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
