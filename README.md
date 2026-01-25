# WaniKani Prediction Trainer

Train Japanese production using neuroscience-based learning principles.

## Philosophy

This is **not** another flashcard app. Key differences:

- **Prediction-first**: You must attempt to predict the word before seeing it (3-second forced delay)
- **Situation-based**: Words appear in context, not isolation
- **Production over recognition**: Focus on constructing, not just recognizing
- **Offline mobile**: Works on your phone without internet, with audio

## Complete Setup Guide

### Step 1: Install dependencies

```bash
cd ~/life/wanikani_trainer
pip install requests piper-tts
```

### Step 2: Fetch your WaniKani vocabulary

```bash
export WANIKANI_API_KEY="your-api-key-here"
python fetch_vocab.py
```

This pulls your apprentice/guru level vocab (words you're actively learning).

### Step 3: Start LM Studio

1. Open LM Studio
2. Load a model (Mistral recommended)
3. Start the local server (should be on port 1234)

### Step 4: Generate sentences

```bash
# Start with 20 words for testing
python generate_sentences.py --limit 20

# Once confirmed working, remove limit for all vocab
python generate_sentences.py
```

### Step 5: Generate audio

```bash
# Uses Piper TTS (on-device, good quality)
# First run downloads Japanese voice model (~50MB)
python generate_audio.py --limit 20

# Or use macOS built-in (faster, lower quality)
python generate_audio.py --tts macos --limit 20
```

### Step 6: Sync to PWA

```bash
python sync_to_pwa.py
```

### Step 7: Test locally

```bash
python -m http.server 8000
# Open http://localhost:8000/pwa/
```

### Step 8: Get it on your phone (iCloud method)

1. Copy the entire `pwa` folder to iCloud Drive
2. On iPhone: Files app → iCloud Drive → pwa
3. Tap `index.html` - opens in Safari
4. Tap Share → Add to Home Screen
5. Now it works like an app, with audio, offline!

## Weekly Refresh

When you want new sentences based on WaniKani progress:

```bash
cd ~/life/wanikani_trainer
python fetch_vocab.py
python generate_sentences.py
python generate_audio.py
python sync_to_pwa.py
# iCloud auto-syncs to your phone
```

## How It Works

1. **See sentence with blank**: 「昨日、___に行きました。」
2. **3-second forced delay**: Your brain must attempt prediction
3. **Reveal answer**: 病院 (びょういん) - hospital + audio plays
4. **Rate difficulty**: Easy / Medium / Hard
5. **Play Audio**: Tap to replay Japanese pronunciation

The forced delay creates **prediction error** → dopamine spike → stronger memory encoding.

## Sync Easy Ratings to WaniKani

When you rate a word as "Easy", you can sync it back to WaniKani as a correct review. This advances the SRS stage and removes it from your review queue.

1. Complete a training session
2. Tap "Export Easy Reviews for WaniKani" on the complete screen
3. Save the `easy_reviews.json` file to the `pwa/` folder
4. Run the sync script:

```bash
export WANIKANI_API_KEY="your-api-key-here"
python sync_to_wanikani.py
```

The script will:
- Submit each Easy item as a correct review
- Archive synced reviews to `data/synced_reviews/`
- Clear the easy_reviews.json file

**Note**: Only items actually available for review in WaniKani will be synced. Items not yet unlocked or already reviewed will be skipped.

## Audio Options

| TTS Engine | Quality | Setup | Command |
|------------|---------|-------|---------|
| **Piper** (default) | Good | `pip install piper-tts` | `python generate_audio.py` |
| macOS Kyoko | OK | None | `python generate_audio.py --tts macos` |
| VOICEVOX | Excellent | Download app | `python generate_audio.py --tts voicevox` |

Piper is recommended: good quality, on-device, no external app needed.

## Files

```
wanikani_trainer/
├── fetch_vocab.py        # Pull vocab from WaniKani API
├── generate_sentences.py # Generate sentences via LM Studio
├── generate_audio.py     # Generate Japanese TTS audio (Piper default)
├── sync_to_pwa.py        # Sync data + audio to PWA folder
├── sync_to_wanikani.py   # Sync Easy ratings back to WaniKani
├── data/
│   ├── vocab.json        # Your WaniKani vocabulary
│   ├── sentences.json    # Generated practice sentences
│   └── synced_reviews/   # Archive of synced WaniKani reviews
├── pwa/
│   ├── index.html        # Mobile PWA with audio playback
│   ├── sw.js             # Service worker for offline
│   ├── manifest.json     # PWA manifest
│   ├── sentences.json    # Synced sentence data
│   ├── easy_reviews.json # Exported Easy ratings (from PWA)
│   └── audio/            # Generated MP3 files
│       └── manifest.json # Audio file mapping
└── README.md
```

## Troubleshooting

**"No data file found"**: Run `python sync_to_pwa.py` to copy sentences.json to pwa folder

**Audio not playing**: Make sure you ran `python generate_audio.py` and the `pwa/audio/` folder has MP3 files

**LM Studio not connecting**: Ensure local server is running on port 1234

**Piper not installed**: Run `pip install piper-tts`

## Future Enhancements

- [ ] Dead Time mode (audio-only, hands-free)
- [ ] Sleep Sandwich mode (bedtime/morning sessions)
- [x] WaniKani sync for Easy ratings (done!)
