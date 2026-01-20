#!/usr/bin/env python3
"""
Phase 3 Verification: Data Files
================================

Verifies:
- All JSON files valid
- Correct number of entries
- Workshop scenarios configured (David Kim inactive, staging degraded)
"""

import json
import sys
from pathlib import Path


def load_json(filename):
    """Load JSON file from data directory."""
    data_dir = Path(__file__).parent.parent / "data"
    with open(data_dir / filename) as f:
        return json.load(f)


def verify_docs():
    """Verify docs.json has 8 entries with varied categories."""
    try:
        docs = load_json("docs.json")
        assert len(docs) == 8, f"Expected 8 docs, got {len(docs)}"

        categories = set(d["category"] for d in docs)
        assert len(categories) >= 4, f"Expected 4+ categories, got {categories}"

        print(f"✓ docs.json: {len(docs)} documents, {len(categories)} categories")
        return True
    except Exception as e:
        print(f"❌ docs.json error: {e}")
        return False


def verify_teams():
    """Verify teams.json structure and David Kim is inactive."""
    try:
        data = load_json("teams.json")

        assert len(data["teams"]) == 4, f"Expected 4 teams, got {len(data['teams'])}"
        assert len(data["owners"]) == 5, f"Expected 5 owners, got {len(data['owners'])}"

        david = next(o for o in data["owners"] if "David" in o["name"])
        assert david["is_active"] is False, "David Kim should be inactive"

        print(f"✓ teams.json: {len(data['teams'])} teams, {len(data['owners'])} owners")
        print(f"  ✓ David Kim is_active: {david['is_active']} (workshop scenario)")
        return True
    except Exception as e:
        print(f"❌ teams.json error: {e}")
        return False


def verify_status():
    """Verify status.json and staging is degraded."""
    try:
        data = load_json("status.json")

        assert len(data["services"]) == 5, f"Expected 5 services, got {len(data['services'])}"

        staging = next(s for s in data["services"] if s["name"] == "staging")
        assert staging["status"] == "degraded", "staging should be degraded"

        print(f"✓ status.json: {len(data['services'])} services")
        print(f"  ✓ staging status: {staging['status']} (workshop scenario)")
        return True
    except Exception as e:
        print(f"❌ status.json error: {e}")
        return False


def main():
    print("=" * 50)
    print("Phase 3 Verification: Data Files")
    print("=" * 50)

    results = [
        verify_docs(),
        verify_teams(),
        verify_status(),
    ]

    print("=" * 50)
    if all(results):
        print("✓ Phase 3 PASSED")
        return 0
    else:
        print("❌ Phase 3 FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
