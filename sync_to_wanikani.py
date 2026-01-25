#!/usr/bin/env python3
"""
Sync "Easy" ratings from the trainer back to WaniKani.

This pushes items you rated "Easy" as correct reviews, advancing their SRS stage.

Usage:
    export WANIKANI_API_KEY="your-key-here"
    python sync_to_wanikani.py

The script reads from pwa/easy_reviews.json, which is created by the PWA
when you finish a training session.
"""

import os
import json
import requests
from pathlib import Path
from datetime import datetime

API_KEY = os.environ.get("WANIKANI_API_KEY")
BASE_URL = "https://api.wanikani.com/v2"

def get_headers():
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

def create_review(subject_id: int) -> bool:
    """Submit a correct review for a subject."""
    url = f"{BASE_URL}/reviews"
    payload = {
        "review": {
            "subject_id": subject_id,
            "incorrect_meaning_answers": 0,
            "incorrect_reading_answers": 0
        }
    }

    try:
        response = requests.post(url, headers=get_headers(), json=payload, timeout=30)

        if response.status_code == 201:
            return True
        elif response.status_code == 422:
            # Subject not ready for review (already reviewed or not unlocked)
            print(f"    Subject {subject_id}: Not available for review")
            return False
        else:
            print(f"    Subject {subject_id}: Error {response.status_code}")
            return False

    except Exception as e:
        print(f"    Subject {subject_id}: {e}")
        return False

def main():
    if not API_KEY:
        print("Error: Set WANIKANI_API_KEY environment variable")
        print("  export WANIKANI_API_KEY='your-key-here'")
        return

    # Load easy reviews from PWA
    reviews_path = Path(__file__).parent / "pwa" / "easy_reviews.json"

    if not reviews_path.exists():
        print("No easy_reviews.json found.")
        print("Complete a training session and tap 'Sync to WaniKani' first.")
        return

    with open(reviews_path, "r", encoding="utf-8") as f:
        easy_reviews = json.load(f)

    if not easy_reviews:
        print("No reviews to sync.")
        return

    print(f"Found {len(easy_reviews)} items rated 'Easy'")
    print("Syncing to WaniKani...\n")

    success = 0
    failed = 0

    for item in easy_reviews:
        subject_id = item.get("subject_id")
        word = item.get("word", "unknown")

        if not subject_id:
            print(f"  {word}: No subject_id, skipping")
            failed += 1
            continue

        print(f"  {word} (id: {subject_id})...", end=" ")

        if create_review(subject_id):
            print("✓ Synced")
            success += 1
        else:
            failed += 1

    print(f"\nDone! Synced: {success}, Failed/Skipped: {failed}")

    # Archive the synced reviews
    if success > 0:
        archive_dir = Path(__file__).parent / "data" / "synced_reviews"
        archive_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_path = archive_dir / f"synced_{timestamp}.json"

        with open(archive_path, "w", encoding="utf-8") as f:
            json.dump({
                "synced_at": datetime.now().isoformat(),
                "success": success,
                "failed": failed,
                "items": easy_reviews
            }, f, ensure_ascii=False, indent=2)

        print(f"Archived to: {archive_path}")

        # Clear the easy_reviews.json
        reviews_path.unlink()
        print("Cleared easy_reviews.json")

if __name__ == "__main__":
    main()
