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

    with open(source, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Filter invalid sentences (where word is not in Japanese sentence)
    cleaned_data = []
    removed_count = 0
    
    for item in data:
        target_word = item['word']
        valid_sentences = []
        
        for sentence in item['sentences']:
            if target_word in sentence['japanese']:
                valid_sentences.append(sentence)
            else:
                removed_count += 1
                # print(f"Skipping invalid sentence for '{target_word}'")
        
        if valid_sentences:
            item['sentences'] = valid_sentences
            cleaned_data.append(item)
    
    data = cleaned_data

    # Save to PWA folder
    dest = pwa_dir / "sentences.json"
    with open(dest, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    word_count = len(data)
    sentence_count = sum(len(item.get('sentences', [])) for item in data)

    print(f"Synced to PWA: {word_count} words, {sentence_count} sentences")
    if removed_count > 0:
        print(f"  (Filtered out {removed_count} sentences where target word was missing)")
    print(f"  → {dest}")
    print()
    print("To use on mobile:")
    print("  1. Copy the 'pwa' folder to iCloud Drive")
    print("  2. On iPhone, open Files app → iCloud → pwa → index.html")
    print("  3. Or host on GitHub Pages for true PWA install")

if __name__ == "__main__":
    main()
