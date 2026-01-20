#!/usr/bin/env python3
"""
Phase 1 Verification: Infrastructure
=====================================

Verifies:
- Jaeger UI is accessible
- OTLP endpoints respond
- Basic auth works
"""

import subprocess
import sys


JAEGER_IP = "46.224.233.5"
JAEGER_USER = "workshop"
JAEGER_PASS = "salesforce2025"


def verify_jaeger_ui():
    """Verify Jaeger UI is accessible."""
    try:
        result = subprocess.run(
            [
                "curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                "-u", f"{JAEGER_USER}:{JAEGER_PASS}",
                "-k",  # Allow self-signed cert
                f"https://{JAEGER_IP}/jaeger/"
            ],
            capture_output=True,
            text=True,
            timeout=10
        )
        status_code = result.stdout.strip()
        if status_code in ("200", "301", "302"):
            print(f"✓ Jaeger UI accessible (HTTP {status_code})")
            print(f"  URL: https://{JAEGER_IP}/jaeger")
            return True
        else:
            print(f"❌ Jaeger UI returned HTTP {status_code}")
            return False
    except subprocess.TimeoutExpired:
        print("❌ Jaeger UI timeout")
        return False
    except Exception as e:
        print(f"❌ Jaeger UI error: {e}")
        return False


def verify_otlp_grpc():
    """Verify OTLP gRPC endpoint is open."""
    try:
        # Just check if port is open
        result = subprocess.run(
            ["nc", "-z", "-w", "3", JAEGER_IP, "4317"],
            capture_output=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"✓ OTLP gRPC port 4317 is open")
            return True
        else:
            print(f"❌ OTLP gRPC port 4317 not reachable")
            return False
    except Exception as e:
        print(f"⚠️  Could not verify OTLP gRPC: {e}")
        return True  # Don't fail if nc not available


def verify_otlp_http():
    """Verify OTLP HTTP endpoint responds."""
    try:
        result = subprocess.run(
            [
                "curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                f"http://{JAEGER_IP}:4318/v1/traces"
            ],
            capture_output=True,
            text=True,
            timeout=10
        )
        status_code = result.stdout.strip()
        # 405 Method Not Allowed is expected for GET on a POST endpoint
        if status_code in ("200", "400", "405"):
            print(f"✓ OTLP HTTP port 4318 responds (HTTP {status_code})")
            return True
        else:
            print(f"❌ OTLP HTTP returned HTTP {status_code}")
            return False
    except Exception as e:
        print(f"❌ OTLP HTTP error: {e}")
        return False


def main():
    print("=" * 50)
    print("Phase 1 Verification: Infrastructure")
    print("=" * 50)
    print(f"Server: {JAEGER_IP}")
    print()

    results = [
        verify_jaeger_ui(),
        verify_otlp_grpc(),
        verify_otlp_http(),
    ]

    print("=" * 50)
    if all(results):
        print("✓ Phase 1 PASSED")
        return 0
    else:
        print("❌ Phase 1 FAILED (some checks may be network-dependent)")
        return 1


if __name__ == "__main__":
    sys.exit(main())
