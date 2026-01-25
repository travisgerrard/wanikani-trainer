# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

WaniKani Prediction Trainer is a Japanese learning tool that trains vocabulary production using prediction-first learning. It has a Python data pipeline backend and a vanilla JavaScript PWA frontend.

## Architecture

**Data Flow (Unidirectional Pipeline):**
```
WaniKani API → fetch_vocab.py → data/vocab.json
                    ↓
LM Studio (port 1234) → generate_sentences.py → data/sentences.json
                    ↓
TTS (Piper/macOS/VOICEVOX) → generate_audio.py → pwa/audio/*.mp3
                    ↓
sync_to_pwa.py → pwa/sentences.json + pwa/audio/
                    ↓
PWA (user rates Easy/Medium/Hard) → pwa/easy_reviews.json
                    ↓
sync_to_wanikani.py → WaniKani API (submits correct reviews)
```

**Backend:** Python scripts with no framework, uses `requests` and `piper-tts`

**Frontend:** Vanilla HTML/CSS/JS PWA in `pwa/` directory. No build system, no npm, no TypeScript.

## Common Commands

```bash
# Setup
pip install requests piper-tts
export WANIKANI_API_KEY="your-key"

# Data pipeline (run in order)
python fetch_vocab.py                              # Pull vocab from WaniKani
python generate_sentences.py [--limit N]           # Generate sentences via LM Studio
python generate_audio.py [--limit N] [--tts TYPE]  # Generate TTS audio (TYPE: piper|macos|voicevox|qwen)
python sync_to_pwa.py                              # Copy data to PWA folder

# Sync user reviews back to WaniKani
python sync_to_wanikani.py

# Local testing
python -m http.server 8000    # Access at http://localhost:8000/pwa/
```

## Key Data Structures

**vocab.json:**
```json
{"id": 7677, "characters": "見当たる", "reading": "みあたる", "meaning": "To Be Found", "level": 7, "srs_stage": 1}
```

**sentences.json:**
```json
{"subject_id": 3778, "word": "猫", "reading": "ねこ", "meaning": "Cat", "level": 15, "sentences": [{"japanese": "屋根の上で猫が寝ています。", "english": "The cat is sleeping on the roof."}]}
```

## External Dependencies

- **LM Studio:** Must be running on port 1234 for sentence generation
- **WaniKani API:** Requires `WANIKANI_API_KEY` environment variable
- **TTS options:** Piper (default, pip install), macOS Kyoko (built-in), VOICEVOX (external app)

## Directory Structure

- `data/` - Intermediate JSON data and synced review archives
- `pwa/` - Production PWA (index.html, sw.js, audio/, sentences.json)
- `models/` - ML/TTS models (gitignored)
- `app/` - Legacy/alternative frontend

## PWA Details

- Service Worker (`sw.js`) provides offline capability with cache-first strategy
- Mobile deployment: Copy `pwa/` folder to iCloud Drive, open in Safari, Add to Home Screen
- No framework dependencies - pure vanilla JS
