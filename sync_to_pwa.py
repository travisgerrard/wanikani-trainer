#!/usr/bin/env python3
"""
Sync generated sentences to PWA folder for offline mobile use.

This copies sentences.json to the PWA's data folder, which can then
be synced to your phone via iCloud/Dropbox.

Usage:
    python sync_to_pwa.py

For iCloud sync:
    1. Move the 'pwa' folder to your iCloud Drive
    2. Run this script after generating new sentences
    3. Open the PWA on your phone - data will be available
"""

import json
import shutil
from pathlib import Path

def main():
    script_dir = Path(__file__).parent
    source = script_dir / "data" / "sentences.json"
    pwa_dir = script_dir / "pwa"

    if not source.exists():
        print("Error: data/sentences.json not found")
        print("Run fetch_vocab.py and generate_sentences.py first")
        return

    # Copy to PWA folder
    dest = pwa_dir / "sentences.json"
    shutil.copy(source, dest)

    # Also create a backup with word count in name
    with open(source, 'r', encoding='utf-8') as f:
        data = json.load(f)

    word_count = len(data)
    sentence_count = sum(len(item.get('sentences', [])) for item in data)

    print(f"Synced to PWA: {word_count} words, {sentence_count} sentences")
    print(f"  → {dest}")
    print()
    print("To use on mobile:")
    print("  1. Copy the 'pwa' folder to iCloud Drive")
    print("  2. On iPhone, open Files app → iCloud → pwa → index.html")
    print("  3. Or host on GitHub Pages for true PWA install")

if __name__ == "__main__":
    main()
