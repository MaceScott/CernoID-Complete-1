#!/usr/bin/env python3
import argparse
import socket
import time
import sys
import os
from urllib.parse import urlparse

def wait_for_port(host: str, port: int, timeout: float = 30.0) -> bool:
    """Wait for a port to become available."""
    start_time = time.time()
    while True:
        try:
            with socket.create_connection((host, port), timeout=1.0):
                return True
        except OSError:
            time.sleep(1)
            if time.time() - start_time >= timeout:
                return False

def get_service_details(service: str) -> tuple[str, int]:
    """Get host and port for a service from environment variables."""
    if service == "db":
        url = os.getenv("DATABASE_URL", "postgresql://localhost:5432")
        parsed = urlparse(url)
        return parsed.hostname or "localhost", parsed.port or 5432
    elif service == "redis":
        url = os.getenv("REDIS_URL", "redis://localhost:6379")
        parsed = urlparse(url)
        return parsed.hostname or "localhost", parsed.port or 6379
    else:
        raise ValueError(f"Unknown service: {service}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--service", required=True, choices=["db", "redis"])
    parser.add_argument("--timeout", type=float, default=30.0)
    args = parser.parse_args()

    try:
        host, port = get_service_details(args.service)
        print(f"Waiting for {args.service} at {host}:{port}...")
        
        if wait_for_port(host, port, args.timeout):
            print(f"{args.service} is available!")
            sys.exit(0)
        else:
            print(f"Timeout waiting for {args.service}", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 