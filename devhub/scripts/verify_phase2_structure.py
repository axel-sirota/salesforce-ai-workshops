#!/usr/bin/env python3
"""
Phase 2 Verification: Project Structure & Dependencies
=======================================================

Verifies:
- Directory structure exists
- Config class loads correctly
- All dependencies installed
"""

import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def verify_structure():
    """Verify project structure exists."""
    base = Path(__file__).parent.parent
    required = [
        "__init__.py",
        "config.py",
        "devhub.py",
        "services/__init__.py",
        "data/.gitkeep",
        "requirements.txt",
        "pyproject.toml",
    ]

    missing = []
    for f in required:
        if not (base / f).exists():
            missing.append(f)

    if missing:
        print(f"❌ Missing files: {missing}")
        return False

    print("✓ Directory structure complete")
    return True


def verify_config():
    """Verify config loads correctly."""
    try:
        from config import Config
        assert Config.LLM_MODEL == "gpt-4o-mini"
        assert Config.VECTOR_DB_FAILURE_RATE == 0.05
        assert Config.VECTOR_DB_SLOW_QUERY_RATE == 0.10
        assert Config.TEAM_DB_STALE_DATA_RATE == 0.10
        assert Config.STATUS_API_TIMEOUT_RATE == 0.02
        print("✓ Config loads correctly")
        print(f"  LLM Model: {Config.LLM_MODEL}")
        return True
    except Exception as e:
        print(f"❌ Config error: {e}")
        return False


def verify_dependencies():
    """Verify key dependencies are installed."""
    deps = ["openai", "chromadb", "opentelemetry", "deepeval", "pytest", "rich"]
    missing = []

    for dep in deps:
        try:
            __import__(dep.replace("-", "_"))
        except ImportError:
            missing.append(dep)

    if missing:
        print(f"❌ Missing dependencies: {missing}")
        return False

    print("✓ All dependencies installed")
    return True


def main():
    print("=" * 50)
    print("Phase 2 Verification: Project Structure")
    print("=" * 50)

    results = [
        verify_structure(),
        verify_config(),
        verify_dependencies(),
    ]

    print("=" * 50)
    if all(results):
        print("✓ Phase 2 PASSED")
        return 0
    else:
        print("❌ Phase 2 FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
