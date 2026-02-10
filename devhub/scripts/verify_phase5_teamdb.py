#!/usr/bin/env python3
"""
Phase 5 Verification: TeamDB Service
=====================================

Verifies:
- SQLite initializes correctly
- Data loads from teams.json
- find_owner returns correct results
- Stale data mode is configured
"""

import sys

# Add parent to path for imports
sys.path.insert(0, str(__file__).rsplit("/scripts", 1)[0])

from config import Config


def verify_initialization():
    """Verify TeamDB initializes with SQLite."""
    try:
        from services.team_db import TeamDB
        tdb = TeamDB()
        assert tdb.team_count == 4, f"Expected 4 teams, got {tdb.team_count}"
        assert tdb.owner_count == 5, f"Expected 5 owners, got {tdb.owner_count}"
        print(f"✓ TeamDB initialized with {tdb.team_count} teams, {tdb.owner_count} owners")
        return True
    except Exception as e:
        print(f"❌ Initialization error: {e}")
        return False


def verify_find_owner():
    """Verify find_owner returns correct results."""
    try:
        from services.team_db import TeamDB

        # Disable stale data for this test
        orig_rate = Config.TEAM_DB_STALE_DATA_RATE
        Config.TEAM_DB_STALE_DATA_RATE = 0

        tdb = TeamDB()

        # Test billing owner
        result = tdb.find_owner("billing")
        assert result["found"], "Billing owner not found"
        assert result["owner"]["name"] == "Sarah Chen", f"Wrong owner: {result['owner']['name']}"
        assert result["team"]["name"] == "Payments Team", f"Wrong team: {result['team']['name']}"
        print(f"✓ find_owner('billing') = {result['owner']['name']} ({result['team']['name']})")

        # Test vector-search owner (should be Emily Johnson - active)
        result = tdb.find_owner("vector-search")
        assert result["found"], "Vector-search owner not found"
        # Should return Emily Johnson (active) since we ORDER BY is_active DESC
        assert result["owner"]["name"] == "Emily Johnson", f"Wrong owner: {result['owner']['name']}"
        print(f"✓ find_owner('vector-search') = {result['owner']['name']} (active={result['owner']['is_active']})")

        Config.TEAM_DB_STALE_DATA_RATE = orig_rate
        return True
    except Exception as e:
        print(f"❌ find_owner error: {e}")
        return False


def verify_get_all_teams():
    """Verify get_all_teams returns all teams."""
    try:
        from services.team_db import TeamDB
        tdb = TeamDB()

        teams = tdb.get_all_teams()
        assert len(teams) == 4, f"Expected 4 teams, got {len(teams)}"

        team_names = [t["name"] for t in teams]
        assert "Payments Team" in team_names, "Missing Payments Team"
        assert "Data Platform Team" in team_names, "Missing Data Platform Team"

        print(f"✓ get_all_teams() returns {len(teams)} teams")
        return True
    except Exception as e:
        print(f"❌ get_all_teams error: {e}")
        return False


def verify_get_team_owners():
    """Verify get_team_owners returns owners for a team."""
    try:
        from services.team_db import TeamDB
        tdb = TeamDB()

        owners = tdb.get_team_owners("team-data")
        assert len(owners) == 2, f"Expected 2 owners for team-data, got {len(owners)}"

        owner_names = [o["name"] for o in owners]
        assert "David Kim" in owner_names, "Missing David Kim"
        assert "Emily Johnson" in owner_names, "Missing Emily Johnson"

        print(f"✓ get_team_owners('team-data') returns {len(owners)} owners")
        return True
    except Exception as e:
        print(f"❌ get_team_owners error: {e}")
        return False


def verify_stale_data_config():
    """Verify stale data configuration is set."""
    try:
        assert Config.TEAM_DB_STALE_DATA_RATE == 0.10, "Wrong stale data rate"
        print(f"✓ Stale data rate configured: {Config.TEAM_DB_STALE_DATA_RATE*100:.0f}%")
        return True
    except Exception as e:
        print(f"❌ Stale data config error: {e}")
        return False


def verify_stale_data_injection():
    """Verify stale data injection mechanism works."""
    try:
        from services.team_db import TeamDB

        # Force 100% stale data
        Config.TEAM_DB_STALE_DATA_RATE = 1.0

        tdb = TeamDB()
        result = tdb.find_owner("billing")

        # Reset
        Config.TEAM_DB_STALE_DATA_RATE = 0.10

        # Sarah Chen is active in data, so with 100% stale rate, should be flipped
        # The is_active should now be False (flipped from True)
        assert result["found"], "Owner not found"
        assert result["owner"]["is_active"] == False, "Stale data injection not working - is_active should be flipped"

        print("✓ Stale data injection mechanism verified")
        return True
    except Exception as e:
        print(f"❌ Stale data injection error: {e}")
        return False


def main():
    print("=" * 50)
    print("Phase 5 Verification: TeamDB Service")
    print("=" * 50)

    results = [
        verify_initialization(),
        verify_find_owner(),
        verify_get_all_teams(),
        verify_get_team_owners(),
        verify_stale_data_config(),
        verify_stale_data_injection(),
    ]

    print("=" * 50)
    if all(results):
        print("✓ Phase 5 PASSED")
        return 0
    else:
        print("❌ Phase 5 FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
