#!/usr/bin/env python3
"""
Fetch vocabulary from WaniKani API.
Filters to apprentice/guru level words (actively learning).

Usage:
    export WANIKANI_API_KEY="your-key-here"
    python fetch_vocab.py
"""

import os
import json
import requests
from pathlib import Path

API_KEY = os.environ.get("WANIKANI_API_KEY")
BASE_URL = "https://api.wanikani.com/v2"

def get_headers():
    return {"Authorization": f"Bearer {API_KEY}"}

def fetch_assignments():
    """Fetch all vocabulary assignments at apprentice/guru level."""
    url = f"{BASE_URL}/assignments"
    params = {
        "subject_types": "vocabulary",
        "srs_stages": "1,2,3,4,5,6",  # Apprentice 1-4, Guru 1-2
    }

    assignments = []
    while url:
        response = requests.get(url, headers=get_headers(), params=params)
        response.raise_for_status()
        data = response.json()
        assignments.extend(data["data"])
        url = data["pages"].get("next_url")
        params = {}  # Clear params for pagination
        print(f"Fetched {len(assignments)} assignments...")

    return assignments

def fetch_subjects(subject_ids):
    """Fetch subject details for given IDs."""
    subjects = {}
    # API allows up to 1000 IDs per request
    for i in range(0, len(subject_ids), 500):
        batch = subject_ids[i:i+500]
        url = f"{BASE_URL}/subjects"
        params = {"ids": ",".join(map(str, batch))}

        response = requests.get(url, headers=get_headers(), params=params)
        response.raise_for_status()
        data = response.json()

        for item in data["data"]:
            subjects[item["id"]] = item

        print(f"Fetched {len(subjects)} subjects...")

    return subjects

def extract_vocab_data(assignments, subjects):
    """Extract clean vocab data for sentence generation."""
    vocab_list = []

    for assignment in assignments:
        subject_id = assignment["data"]["subject_id"]
        if subject_id not in subjects:
            continue

        subject = subjects[subject_id]
        data = subject["data"]

        # Get primary reading and meaning
        primary_reading = next(
            (r["reading"] for r in data.get("readings", []) if r.get("primary")),
            data.get("readings", [{}])[0].get("reading", "")
        )
        primary_meaning = next(
            (m["meaning"] for m in data.get("meanings", []) if m.get("primary")),
            data.get("meanings", [{}])[0].get("meaning", "")
        )

        vocab_list.append({
            "id": subject_id,
            "characters": data.get("characters", ""),
            "reading": primary_reading,
            "meaning": primary_meaning,
            "level": data.get("level", 0),
            "srs_stage": assignment["data"]["srs_stage"],
        })

    # Sort by SRS stage (lower = needs more practice)
    vocab_list.sort(key=lambda x: (x["srs_stage"], x["level"]))

    return vocab_list

def main():
    if not API_KEY:
        print("Error: Set WANIKANI_API_KEY environment variable")
        print("  export WANIKANI_API_KEY='your-key-here'")
        return

    print("Fetching WaniKani assignments...")
    assignments = fetch_assignments()

    if not assignments:
        print("No vocabulary found at apprentice/guru level.")
        return

    subject_ids = [a["data"]["subject_id"] for a in assignments]
    print(f"\nFetching details for {len(subject_ids)} vocabulary items...")
    subjects = fetch_subjects(subject_ids)

    vocab_list = extract_vocab_data(assignments, subjects)

    # Save to JSON
    output_path = Path(__file__).parent / "data" / "vocab.json"
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(vocab_list, f, ensure_ascii=False, indent=2)

    print(f"\nSaved {len(vocab_list)} vocabulary items to {output_path}")
    print(f"Lowest SRS items (need most practice):")
    for v in vocab_list[:5]:
        print(f"  {v['characters']} ({v['reading']}) - {v['meaning']} [SRS {v['srs_stage']}]")

if __name__ == "__main__":
    main()
