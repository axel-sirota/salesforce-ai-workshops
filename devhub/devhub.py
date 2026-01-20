"""
DevHub - Internal Developer Knowledge Assistant
===============================================

VERSION: V0 (no observability - students will add it)

This is the main entry point for DevHub. The application helps developers
find information about APIs, service owners, and system status.

INTENTIONAL PROBLEMS (for workshop debugging):
- Random latency spikes in VectorDB (10%)
- Connection failures in VectorDB (5%)
- Stale data in TeamDB (10%)
- Low similarity results in VectorDB (15%)
- Status API timeouts (2%)

Students will:
1. Session 1: Add OpenTelemetry tracing to find these problems
2. Session 2: Add DeepEval testing to catch regressions
"""

from config import Config


def main():
    """Main entry point - to be implemented in Phase 8."""
    print("DevHub V0 - Coming soon!")
    Config.print_config()

    issues = Config.validate()
    if issues:
        print("\nConfiguration Issues:")
        for issue in issues:
            print(f"  - {issue}")


if __name__ == "__main__":
    main()
