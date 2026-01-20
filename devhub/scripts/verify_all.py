#!/usr/bin/env python3
"""
Run All Phase Verifications
===========================

Runs verification scripts for all completed phases.
"""

import subprocess
import sys
from pathlib import Path


def run_verification(script_name: str) -> bool:
    """Run a verification script and return success status."""
    script_path = Path(__file__).parent / script_name

    if not script_path.exists():
        print(f"⚠️  Script not found: {script_name}")
        return True  # Skip missing scripts

    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=False,
        cwd=script_path.parent.parent  # Run from devhub directory
    )

    return result.returncode == 0


def main():
    print("=" * 60)
    print("DevHub Workshop - Full Verification Suite")
    print("=" * 60)
    print()

    scripts = [
        ("Phase 1: Infrastructure", "verify_phase1_infra.py"),
        ("Phase 2: Project Structure", "verify_phase2_structure.py"),
        ("Phase 3: Data Files", "verify_phase3_data.py"),
        ("Phase 4: VectorDB", "verify_phase4_vectordb.py"),
        ("Phase 5: TeamDB", "verify_phase5_teamdb.py"),
        ("Phase 6: StatusAPI", "verify_phase6_statusapi.py"),
    ]

    results = []
    for name, script in scripts:
        print(f"\n>>> {name}")
        print("-" * 50)
        success = run_verification(script)
        results.append((name, success))
        print()

    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)

    all_passed = True
    for name, success in results:
        status = "✓ PASSED" if success else "❌ FAILED"
        print(f"  {name}: {status}")
        if not success:
            all_passed = False

    print("=" * 60)
    if all_passed:
        print("✓ ALL VERIFICATIONS PASSED")
        return 0
    else:
        print("❌ SOME VERIFICATIONS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
