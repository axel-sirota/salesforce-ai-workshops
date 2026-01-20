"""
DevHub Configuration
====================

Workshop configuration - instructors can adjust these values
to create different failure scenarios for debugging exercises.
"""

import os


class Config:
    """
    Configuration for DevHub with intentional failure modes.

    Failure rates are configurable to control workshop difficulty:
    - Higher rates = more failures to debug
    - Lower rates = smoother demos.
    """

    # ==========================================================================
    # LATENCY SIMULATION (milliseconds)
    # ==========================================================================

    # VectorDB latency range
    VECTOR_DB_LATENCY_MIN = 50
    VECTOR_DB_LATENCY_MAX = 200
    VECTOR_DB_SLOW_QUERY_LATENCY = 3000  # 3 seconds when "slow"

    # TeamDB latency range
    TEAM_DB_LATENCY_MIN = 20
    TEAM_DB_LATENCY_MAX = 100

    # StatusAPI latency range
    STATUS_API_LATENCY_MIN = 30
    STATUS_API_LATENCY_MAX = 150
    STATUS_API_TIMEOUT_LATENCY = 5000  # 5 seconds before timeout

    # ==========================================================================
    # FAILURE RATES (0.0 to 1.0)
    # ==========================================================================

    # VectorDB failure modes
    VECTOR_DB_FAILURE_RATE = 0.05        # 5% connection failures
    VECTOR_DB_SLOW_QUERY_RATE = 0.10     # 10% slow queries
    VECTOR_DB_LOW_SIMILARITY_RATE = 0.15  # 15% bad retrieval

    # TeamDB failure modes
    TEAM_DB_STALE_DATA_RATE = 0.10       # 10% stale contacts

    # StatusAPI failure modes
    STATUS_API_TIMEOUT_RATE = 0.02       # 2% timeouts

    # ==========================================================================
    # QUALITY THRESHOLDS
    # ==========================================================================

    LOW_SIMILARITY_THRESHOLD = 0.5  # Below = bad retrieval

    # ==========================================================================
    # LLM SETTINGS (OpenAI)
    # ==========================================================================

    LLM_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    LLM_MAX_TOKENS = 1024
    LLM_TEMPERATURE = 0.3

    # API Key (from environment)
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

    # ==========================================================================
    # DATA PATHS
    # ==========================================================================

    DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
    DOCS_PATH = os.path.join(DATA_DIR, "docs.json")
    TEAMS_PATH = os.path.join(DATA_DIR, "teams.json")
    STATUS_PATH = os.path.join(DATA_DIR, "status.json")

    @classmethod
    def validate(cls) -> list[str]:
        """Validate configuration and return list of issues."""
        issues = []

        if not cls.OPENAI_API_KEY:
            issues.append("OPENAI_API_KEY environment variable not set")

        if not os.path.exists(cls.DATA_DIR):
            issues.append(f"Data directory not found: {cls.DATA_DIR}")

        return issues

    @classmethod
    def print_config(cls):
        """Print current configuration for debugging."""
        print("=" * 60)
        print("DevHub Configuration")
        print("=" * 60)
        print(f"LLM Model: {cls.LLM_MODEL}")
        print(f"Data Dir: {cls.DATA_DIR}")
        print()
        print("Failure Rates:")
        print(f"  VectorDB Slow Query: {cls.VECTOR_DB_SLOW_QUERY_RATE * 100:.0f}%")
        print(f"  VectorDB Connection Failure: {cls.VECTOR_DB_FAILURE_RATE * 100:.0f}%")
        print(f"  VectorDB Low Similarity: {cls.VECTOR_DB_LOW_SIMILARITY_RATE * 100:.0f}%")
        print(f"  TeamDB Stale Data: {cls.TEAM_DB_STALE_DATA_RATE * 100:.0f}%")
        print(f"  StatusAPI Timeout: {cls.STATUS_API_TIMEOUT_RATE * 100:.0f}%")
        print("=" * 60)
