"""
StatusAPI Service
=================

Mock service status API for checking service health.

INTENTIONAL PROBLEM (for workshop debugging):
- 2% timeout: 5-second delay followed by TimeoutError

Students will add OpenTelemetry tracing to detect timeout issues.
"""

import json
import random
import time
from pathlib import Path

from config import Config


class StatusAPI:
    """
    Mock API for checking service status.

    Loads status from JSON file and simulates API behavior.
    Has intentional timeout problem for workshop exercises.
    """

    def __init__(self, status_path: str | None = None):
        """
        Initialize StatusAPI.

        Args:
            status_path: Path to status.json. Defaults to Config.STATUS_PATH.
        """
        self.status_path = status_path or Config.STATUS_PATH
        self._services = {}
        self._load_status()

    def _load_status(self):
        """Load status data from JSON."""
        status_file = Path(self.status_path)
        if not status_file.exists():
            raise FileNotFoundError(f"Status file not found: {self.status_path}")

        with open(status_file) as f:
            data = json.load(f)

        # Index services by name for quick lookup
        for service in data.get("services", []):
            self._services[service["name"].lower()] = service

        self._service_count = len(self._services)

    def check_status(self, service_name: str) -> dict:
        """
        Check the status of a service.

        Args:
            service_name: Name of the service to check

        Returns:
            dict with keys: found, service, latency_ms

        Raises:
            TimeoutError: Simulated timeout (2% rate)
        """
        start_time = time.time()

        # === INTENTIONAL PROBLEM: Timeout (2%) ===
        if random.random() < Config.STATUS_API_TIMEOUT_RATE:
            # Simulate slow response that times out
            time.sleep(Config.STATUS_API_TIMEOUT_LATENCY / 1000)
            raise TimeoutError(f"StatusAPI timeout: {service_name} check exceeded 5s")

        # Normal latency simulation
        latency = random.randint(
            Config.STATUS_API_LATENCY_MIN,
            Config.STATUS_API_LATENCY_MAX
        )
        time.sleep(latency / 1000)

        # Look up service (case-insensitive)
        service_key = service_name.lower()

        # Also try partial matches
        matched_service = None
        if service_key in self._services:
            matched_service = self._services[service_key]
        else:
            # Try partial match
            for name, service in self._services.items():
                if service_key in name or name in service_key:
                    matched_service = service
                    break

        latency_ms = int((time.time() - start_time) * 1000)

        if not matched_service:
            return {
                "found": False,
                "service": None,
                "latency_ms": latency_ms
            }

        return {
            "found": True,
            "service": {
                "name": matched_service["name"],
                "status": matched_service["status"],
                "uptime_percent": matched_service["uptime_percent"],
                "last_incident": matched_service.get("last_incident"),
                "incident_description": matched_service.get("incident_description")
            },
            "latency_ms": latency_ms
        }

    def get_all_services(self) -> list[dict]:
        """Get status of all services."""
        return list(self._services.values())

    def get_degraded_services(self) -> list[dict]:
        """Get list of services with degraded or unhealthy status."""
        return [
            s for s in self._services.values()
            if s["status"] in ("degraded", "unhealthy", "down")
        ]

    @property
    def service_count(self) -> int:
        """Return number of services in the database."""
        return self._service_count
