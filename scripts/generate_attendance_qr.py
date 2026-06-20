#!/usr/bin/env python3
"""Generate attendance QR code payloads for display on a projector/TV."""

import argparse

from supabase import create_client


def main():
    parser = argparse.ArgumentParser(description="Generate attendance QR payloads")
    parser.add_argument("--url", required=True, help="Supabase URL")
    parser.add_argument("--key", required=True, help="Supabase service key")
    parser.add_argument("--game-id", help="Specific game ID (optional)")
    args = parser.parse_args()

    db = create_client(args.url, args.key)
    query = db.table("games").select("id, home_team, away_team, attendance_qr_secret")
    if args.game_id:
        query = query.eq("id", args.game_id)
    games = query.order("sort_order").execute().data

    for g in games:
        payload = f"wc26-attendance:{g['id']}:{g['attendance_qr_secret']}"
        print(f"\n{g['home_team']} vs {g['away_team']}")
        print(f"  Payload: {payload}")
        print(f"  QR URL:  https://api.qrserver.com/v1/create-qr-code/?size=400x400&data={payload}")


if __name__ == "__main__":
    main()
