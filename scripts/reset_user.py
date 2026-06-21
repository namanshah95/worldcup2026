#!/usr/bin/env python3
"""Reset a user by email — clears scores, captain, bingo, and unregisters them."""

import argparse
import json
import os
import sys

import httpx


def main():
    parser = argparse.ArgumentParser(description="Reset a watch party user by email")
    parser.add_argument("email", help="User email address")
    parser.add_argument(
        "--api-url",
        default=os.environ.get("API_URL", "http://localhost:8000"),
        help="Backend base URL (default: API_URL env or http://localhost:8000)",
    )
    parser.add_argument(
        "--admin-secret",
        default=os.environ.get("ADMIN_SECRET", ""),
        help="Admin secret (default: ADMIN_SECRET env)",
    )
    args = parser.parse_args()

    if not args.admin_secret:
        print("Error: set ADMIN_SECRET or pass --admin-secret", file=sys.stderr)
        sys.exit(1)

    url = f"{args.api_url.rstrip('/')}/api/admin/users/reset"
    response = httpx.post(
        url,
        headers={"X-Admin-Secret": args.admin_secret},
        json={"email": args.email},
        timeout=30.0,
    )

    if response.status_code >= 400:
        print(response.text, file=sys.stderr)
        sys.exit(1)

    print(json.dumps(response.json(), indent=2))


if __name__ == "__main__":
    main()
