#!/usr/bin/env python3
"""
Generate audio for practice sentences using Japanese TTS.

Options:
  --tts edge      Use Microsoft Edge TTS - good quality, free (RECOMMENDED)
  --tts macos     Use macOS built-in voice (Kyoko) - no setup required
  --tts voicevox  Use VOICEVOX - best quality, requires VOICEVOX app running

Usage:
    # Good quality, free, no setup (recommended)
    pip install edge-tts
    python generate_audio.py --tts edge

    # Quick fallback with macOS built-in
    python generate_audio.py --tts macos

    # Best quality (requires VOICEVOX app running)
    python generate_audio.py --tts voicevox

Requirements:
    pip install edge-tts        # for Edge TTS (recommended)
    pip install requests        # for VOICEVOX API

Note: Kokoro ONNX does NOT properly support Japanese (espeak limitation).
"""

import json
import subprocess
import argparse
import wave
from pathlib import Path
import time
import re

# Lazy imports for optional dependencies
requests = None
piper = None

def ensure_requests():
    global requests
    if requests is None:
        import requests as req
        requests = req

def clean_text(text: str) -> str:
    """Remove bracketed readings from text (e.g., 漢字[かんじ] -> 漢字)."""
    # Remove [text] or (text) or （text）
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'\(.*?\)', '', text)
    text = re.sub(r'（.*?）', '', text)
    return text.strip()

def generate_edge(text: str, output_path: Path) -> bool:
    """Generate audio using Microsoft Edge TTS (free, good quality)."""
    try:
        import asyncio
        import edge_tts

        async def _generate():
            # Japanese female voice - Nanami is natural sounding
            voice = "ja-JP-NanamiNeural"
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(str(output_path))

        asyncio.run(_generate())
        return True
    except ImportError:
        print("    edge-tts not installed. Run: pip install edge-tts")
        return False
    except Exception as e:
        print(f"    Edge TTS error: {e}")
        return False

def generate_kokoro(text: str, output_path: Path) -> bool:
    """Generate audio using Kokoro ONNX (on-device, good quality)."""
    try:
        from kokoro_onnx import Kokoro
        import soundfile as sf

        # Model paths
        model_dir = Path(__file__).parent / "models"
        model_path = model_dir / "kokoro-v1.0.onnx"
        voices_path = model_dir / "voices.bin"

        if not model_path.exists() or not voices_path.exists():
            print(f"    Kokoro models not found. Download to {model_dir}/")
            print("    curl -L -o models/kokoro-v1.0.onnx https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx")
            print("    curl -L -o models/voices.bin https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin")
            return False

        # Initialize Kokoro
        kokoro = Kokoro(str(model_path), str(voices_path))

        # Generate audio - use Japanese voice
        # Note: Don't pass lang parameter - espeak doesn't support Japanese phonemization
        # The Japanese voice (jf_alpha) handles Japanese text natively
        samples, sample_rate = kokoro.create(
            text,
            voice="jf_alpha",  # Japanese Female voice
            speed=1.0
        )

        # Save as WAV first
        wav_path = output_path.with_suffix('.wav')
        sf.write(str(wav_path), samples, sample_rate)

        # Convert to MP3 if ffmpeg available
        try:
            subprocess.run([
                'ffmpeg', '-i', str(wav_path),
                '-codec:a', 'libmp3lame', '-qscale:a', '2',
                str(output_path), '-y'
            ], check=True, capture_output=True)
            wav_path.unlink(missing_ok=True)
        except FileNotFoundError:
            output_path = wav_path  # Keep as WAV

        return True
    except ImportError:
        print("    Kokoro not installed. Run: pip install kokoro-onnx soundfile")
        return False
    except Exception as e:
        print(f"    Kokoro TTS error: {e}")
        return False

def generate_macos(text: str, output_path: Path) -> bool:
    """Generate audio using macOS say command with Kyoko voice."""
    try:
        # Use Kyoko (Japanese female voice)
        # First generate AIFF, then convert to MP3
        aiff_path = output_path.with_suffix('.aiff')

        subprocess.run([
            'say', '-v', 'Kyoko',
            '-o', str(aiff_path),
            text
        ], check=True, capture_output=True)

        # Convert to MP3 using afconvert
        subprocess.run([
            'afconvert', '-f', 'mp4f', '-d', 'aac',
            str(aiff_path), str(output_path.with_suffix('.m4a'))
        ], check=True, capture_output=True)

        # Clean up AIFF
        aiff_path.unlink(missing_ok=True)

        # Rename m4a to mp3 (or keep as m4a)
        m4a_path = output_path.with_suffix('.m4a')
        if m4a_path.exists():
            m4a_path.rename(output_path)

        return True
    except Exception as e:
        print(f"    macOS TTS error: {e}")
        return False

def generate_voicevox(text: str, output_path: Path, speaker_id: int = 1) -> bool:
    """Generate audio using VOICEVOX API (must be running locally)."""
    ensure_requests()
    try:
        base_url = "http://localhost:50021"

        # Create audio query
        query_response = requests.post(
            f"{base_url}/audio_query",
            params={"text": text, "speaker": speaker_id},
            timeout=30
        )
        query_response.raise_for_status()
        query = query_response.json()

        # Generate audio
        audio_response = requests.post(
            f"{base_url}/synthesis",
            params={"speaker": speaker_id},
            json=query,
            timeout=60
        )
        audio_response.raise_for_status()

        # Save as WAV
        wav_path = output_path.with_suffix('.wav')
        with open(wav_path, 'wb') as f:
            f.write(audio_response.content)

        # Convert to MP3 using ffmpeg if available, otherwise keep WAV
        try:
            subprocess.run([
                'ffmpeg', '-i', str(wav_path),
                '-codec:a', 'libmp3lame', '-qscale:a', '2',
                str(output_path), '-y'
            ], check=True, capture_output=True)
            wav_path.unlink(missing_ok=True)
        except FileNotFoundError:
            # ffmpeg not installed, keep WAV
            wav_path.rename(output_path.with_suffix('.wav'))

        return True
    except requests.exceptions.ConnectionError:
        print("    VOICEVOX not running. Start it first.")
        return False
    except Exception as e:
        print(f"    VOICEVOX error: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Generate audio for sentences")
    parser.add_argument("--tts", choices=["edge", "macos", "voicevox"], default="edge",
                       help="TTS engine to use (edge=recommended, macos=fallback, voicevox=best)")
    parser.add_argument("--input", default="data/sentences.json",
                       help="Input sentences file")
    parser.add_argument("--output-dir", default="pwa/audio",
                       help="Output directory for audio files")
    parser.add_argument("--limit", type=int, default=0,
                       help="Limit number of words (0=all)")
    parser.add_argument("--speaker", type=int, default=1,
                       help="VOICEVOX speaker ID (1=つくよみちゃん)")
    args = parser.parse_args()

    # Load sentences
    input_path = Path(__file__).parent / args.input
    if not input_path.exists():
        print(f"Error: {input_path} not found")
        return

    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if args.limit > 0:
        data = data[:args.limit]

    # Create output directory
    output_dir = Path(__file__).parent / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    # Select TTS function
    if args.tts == "edge":
        tts_func = generate_edge
        print("Using Microsoft Edge TTS (ja-JP-NanamiNeural)")
    elif args.tts == "macos":
        tts_func = generate_macos
        print("Using macOS Kyoko voice")
    else:
        tts_func = lambda text, path: generate_voicevox(text, path, args.speaker)
        print(f"Using VOICEVOX (speaker {args.speaker})")

    # Generate audio
    audio_manifest = []
    total_sentences = sum(len(item.get('sentences', [])) for item in data)
    generated = 0

    for item in data:
        word = item['word']
        print(f"\n{word} ({item['reading']})")

        for i, sentence in enumerate(item.get('sentences', [])):
            filename = f"{word}_{i}.mp3"
            output_path = output_dir / filename

            print(f"  [{generated+1}/{total_sentences}] Generating audio...")

            cleaned_text = clean_text(sentence['japanese'])
            if not cleaned_text:
                print("    Skipping empty text")
                continue

            if tts_func(cleaned_text, output_path):
                audio_manifest.append({
                    "word": word,
                    "sentence_index": i,
                    "file": filename
                })
                generated += 1
            else:
                print(f"    Failed to generate audio")

            # Small delay to avoid overwhelming TTS
            time.sleep(0.2)

    # Save manifest
    manifest_path = output_dir / "manifest.json"
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(audio_manifest, f, ensure_ascii=False, indent=2)

    print(f"\n\nDone! Generated {generated} audio files")
    print(f"Output: {output_dir}")
    print(f"Manifest: {manifest_path}")

if __name__ == "__main__":
    main()
