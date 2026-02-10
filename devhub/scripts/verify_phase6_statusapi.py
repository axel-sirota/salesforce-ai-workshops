#!/usr/bin/env python3
"""
Phase 6 Verification: StatusAPI Service
========================================

Verifies:
- Status data loads from status.json
- check_status returns correct results
- get_degraded_services works
- Timeout mode is configured
"""

import sys

# Add parent to path for imports
sys.path.insert(0, str(__file__).rsplit("/scripts", 1)[0])

from config import Config


def verify_initialization():
    """Verify StatusAPI initializes correctly."""
    try:
        from services.status_api import StatusAPI
        api = StatusAPI()
        assert api.service_count == 5, f"Expected 5 services, got {api.service_count}"
        print(f"✓ StatusAPI initialized with {api.service_count} services")
        return True
    except Exception as e:
        print(f"❌ Initialization error: {e}")
        return False


def verify_check_status_staging():
    """Verify check_status returns degraded for staging."""
    try:
        from services.status_api import StatusAPI

        # Disable timeout for this test
        orig_rate = Config.STATUS_API_TIMEOUT_RATE
        Config.STATUS_API_TIMEOUT_RATE = 0

        api = StatusAPI()
        result = api.check_status("staging")

        Config.STATUS_API_TIMEOUT_RATE = orig_rate

        assert result["found"], "Staging not found"
        assert result["service"]["status"] == "degraded", f"Wrong status: {result['service']['status']}"
        assert "Database connection pool" in result["service"]["incident_description"], "Wrong incident"

        print(f"✓ check_status('staging') = {result['service']['status']}")
        print(f"  Incident: {result['service']['incident_description'][:50]}...")
        return True
    except Exception as e:
        print(f"❌ check_status staging error: {e}")
        return False


def verify_check_status_healthy():
    """Verify check_status returns healthy for payments-api."""
    try:
        from services.status_api import StatusAPI

        # Disable timeout for this test
        orig_rate = Config.STATUS_API_TIMEOUT_RATE
        Config.STATUS_API_TIMEOUT_RATE = 0

        api = StatusAPI()
        result = api.check_status("payments-api")

        Config.STATUS_API_TIMEOUT_RATE = orig_rate

        assert result["found"], "payments-api not found"
        assert result["service"]["status"] == "healthy", f"Wrong status: {result['service']['status']}"

        print(f"✓ check_status('payments-api') = {result['service']['status']}")
        return True
    except Exception as e:
        print(f"❌ check_status healthy error: {e}")
        return False


def verify_get_all_services():
    """Verify get_all_services returns all services."""
    try:
        from services.status_api import StatusAPI
        api = StatusAPI()

        services = api.get_all_services()
        assert len(services) == 5, f"Expected 5 services, got {len(services)}"

        service_names = [s["name"] for s in services]
        assert "staging" in service_names, "Missing staging"
        assert "payments-api" in service_names, "Missing payments-api"

        print(f"✓ get_all_services() returns {len(services)} services")
        return True
    except Exception as e:
        print(f"❌ get_all_services error: {e}")
        return False


def verify_get_degraded_services():
    """Verify get_degraded_services returns staging."""
    try:
        from services.status_api import StatusAPI
        api = StatusAPI()

        degraded = api.get_degraded_services()
        assert len(degraded) == 1, f"Expected 1 degraded service, got {len(degraded)}"
        assert degraded[0]["name"] == "staging", f"Wrong degraded service: {degraded[0]['name']}"

        print(f"✓ get_degraded_services() returns ['staging']")
        return True
    except Exception as e:
        print(f"❌ get_degraded_services error: {e}")
        return False


def verify_timeout_config():
    """Verify timeout configuration is set."""
    try:
        assert Config.STATUS_API_TIMEOUT_RATE == 0.02, "Wrong timeout rate"
        assert Config.STATUS_API_TIMEOUT_LATENCY == 5000, "Wrong timeout latency"
        print(f"✓ Timeout rate configured: {Config.STATUS_API_TIMEOUT_RATE*100:.0f}%")
        print(f"  Timeout latency: {Config.STATUS_API_TIMEOUT_LATENCY}ms")
        return True
    except Exception as e:
        print(f"❌ Timeout config error: {e}")
        return False


def verify_timeout_injection():
    """Verify timeout injection mechanism works."""
    try:
        from services.status_api import StatusAPI

        # Force 100% timeout
        Config.STATUS_API_TIMEOUT_RATE = 1.0

        api = StatusAPI()

        try:
            api.check_status("staging")
            # Reset before asserting
            Config.STATUS_API_TIMEOUT_RATE = 0.02
            print("❌ Timeout injection not working - no exception raised")
            return False
        except TimeoutError as e:
            # Reset
            Config.STATUS_API_TIMEOUT_RATE = 0.02
            assert "timeout" in str(e).lower(), "Wrong error message"
            print("✓ Timeout injection mechanism verified")
            return True

    except Exception as e:
        Config.STATUS_API_TIMEOUT_RATE = 0.02
        print(f"❌ Timeout injection error: {e}")
        return False


def main():
    print("=" * 50)
    print("Phase 6 Verification: StatusAPI Service")
    print("=" * 50)

    results = [
        verify_initialization(),
        verify_check_status_staging(),
        verify_check_status_healthy(),
        verify_get_all_services(),
        verify_get_degraded_services(),
        verify_timeout_config(),
        verify_timeout_injection(),
    ]

    print("=" * 50)
    if all(results):
        print("✓ Phase 6 PASSED")
        return 0
    else:
        print("❌ Phase 6 FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
