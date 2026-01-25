# WaniKani Prediction Trainer - Project Context

## Overview
This project is a personal Japanese learning tool designed to train vocabulary production using neuroscience-based principles (prediction error, situation-based learning). It is a hybrid application with a Python-based data processing backend and a vanilla JavaScript Progressive Web App (PWA) frontend.

**Key Features:**
*   **Prediction-First:** Users must predict the missing word in a sentence before seeing the answer.
*   **WaniKani Integration:** Fetches user-specific vocabulary (Apprentice/Guru levels).
*   **AI Generation:** Uses local LLMs (via LM Studio) to generate context sentences.
*   **TTS Integration:** Generates audio for sentences using Piper TTS.
*   **Offline PWA:** Runs locally or on mobile (via iCloud Sync) without internet access.
*   **Two-way Sync:** Syncs "Easy" ratings back to WaniKani to advance SRS progress.

## Architecture

### Backend (Python)
The backend is a series of scripts that form a data pipeline:
1.  `fetch_vocab.py`: Pulls active vocabulary from WaniKani API (`data/vocab.json`).
2.  `generate_sentences.py`: Connects to a local LLM server (LM Studio, port 1234) to generate practice sentences (`data/sentences.json`).
3.  `generate_audio.py`: Uses Piper TTS (or macOS/VoiceVox) to generate audio files for sentences.
4.  `sync_to_pwa.py`: Aggregates data and audio, copying them to the `pwa/` directory.
5.  `sync_to_wanikani.py`: Reads `easy_reviews.json` from the PWA and submits correct reviews to WaniKani.

### Frontend (PWA)
Located in the `pwa/` directory.
*   **Tech Stack:** Vanilla HTML, CSS, JavaScript.
*   **Entry Point:** `pwa/index.html`.
*   **Data Source:** Reads `sentences.json` and plays audio from `audio/` directory.
*   **Offline:** Uses Service Worker (`sw.js`) and Manifest (`manifest.json`) for installation and offline capability.

## Development & Usage

### Setup
1.  **Dependencies:** `pip install requests piper-tts`.
2.  **Environment:** Set `WANIKANI_API_KEY`.
3.  **LLM:** Start LM Studio server on port 1234.

### Key Commands
*   **Fetch Data:** `python fetch_vocab.py`
*   **Generate Sentences:** `python generate_sentences.py [--limit N]`
*   **Generate Audio:** `python generate_audio.py [--limit N] [--tts macos|voicevox]`
*   **Deploy to PWA:** `python sync_to_pwa.py`
*   **Sync Reviews:** `python sync_to_wanikani.py`
*   **Local Test:** `python -m http.server 8000` (Access at `http://localhost:8000/pwa/`)

### Directory Structure
*   `app/`: (Legacy/Alternative frontend?)
*   `data/`: Intermediate data storage (JSONs).
*   `models/`: Directory for ML/TTS models.
*   `pwa/`: Production-ready PWA assets (HTML, JS, Audio, JSON).

## Conventions
*   **Code Style:** Python (PEP 8 implied), Standard JS/CSS.
*   **Data Flow:** Unidirectional for content (Python -> Data -> PWA). Feedback loop for reviews (PWA -> JSON -> Python -> WaniKani).
*   **Deployment:** "Deployment" consists of copying the `pwa` folder to a location accessible by the mobile device (e.g., iCloud Drive).
