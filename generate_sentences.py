#!/usr/bin/env python3
"""
Generate contextual sentences for WaniKani vocabulary using local LLM.

Requires: Local LLM running (Ollama, LM Studio, or compatible API)

Usage:
    # With Ollama:
    python generate_sentences.py --api ollama --model mistral

    # With LM Studio:
    python generate_sentences.py --api lmstudio

    # Limit to N words (for testing):
    python generate_sentences.py --limit 20
"""

import json
import argparse
import requests
from pathlib import Path
from typing import Optional

def call_ollama(prompt: str, model: str = "mistral") -> str:
    """Call Ollama API."""
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": model, "prompt": prompt, "stream": False},
        timeout=120
    )
    response.raise_for_status()
    return response.json()["response"]

def call_lmstudio(prompt: str) -> str:
    """Call LM Studio API (OpenAI-compatible)."""
    response = requests.post(
        "http://localhost:1234/v1/completions",
        json={
            "prompt": prompt,
            "max_tokens": 500,
            "temperature": 0.7,
        },
        timeout=120
    )
    response.raise_for_status()
    return response.json()["choices"][0]["text"]

def call_openai_compatible(prompt: str, base_url: str) -> str:
    """Call any OpenAI-compatible API."""
    response = requests.post(
        f"{base_url}/v1/completions",
        json={
            "prompt": prompt,
            "max_tokens": 500,
            "temperature": 0.7,
        },
        timeout=120
    )
    response.raise_for_status()
    return response.json()["choices"][0]["text"]

def generate_sentences(word: dict, call_llm) -> dict:
    """Generate practice sentences for a vocabulary word."""

    prompt = f"""You are a Japanese language teacher using neuroscience-based learning. Create 2 example sentences using this vocabulary word.

    **CORE RULE: HIGH VALENCE.**
    Human memory prioritizes information associated with strong emotions, danger, absurdity, or humor.
    DO NOT create boring, standard textbook sentences like "I went to the library."

    Instead, use themes like:
    - Danger / Urgency (e.g., zombies, explosions, running away)
    - Absurdity / Surrealism (e.g., talking animals, flying sushi)
    - Strong Emotion (e.g., intense love, furious anger, crushing despair)
    - Social Taboo / Embarrassment

Word: {word['characters']}
Reading: {word['reading']}
Meaning: {word['meaning']}

Requirements:
1. Sentence 1: A situation involving **Danger or Urgency**.
2. Sentence 2: A situation involving **Absurdity or Humor**.
3. Use simple grammar (JLPT N5-N4 level).
4. Include furigana in parentheses for any kanji not in the target word.

Format your response EXACTLY like this:
SENTENCE1_JP: [Japanese sentence]
SENTENCE1_EN: [English translation]
SENTENCE2_JP: [Japanese sentence]
SENTENCE2_EN: [English translation]

Example for 病院 (びょういん) - hospital:
SENTENCE1_JP: ゾンビに噛(か)まれたので、急いで病院に行きました！
SENTENCE1_EN: I was bitten by a zombie, so I went to the hospital in a hurry!
SENTENCE2_JP: この病院の院長(いんちょう)は、実は宇宙人(うちゅうじん)です。
SENTENCE2_EN: The director of this hospital is actually an alien.
"""

    try:
        response = call_llm(prompt)

        # Parse response
        lines = response.strip().split("\n")
        sentences = []

        current = {}
        for line in lines:
            line = line.strip()
            if line.startswith("SENTENCE1_JP:"):
                current["japanese"] = line.replace("SENTENCE1_JP:", "").strip()
            elif line.startswith("SENTENCE1_EN:"):
                current["english"] = line.replace("SENTENCE1_EN:", "").strip()
                if "japanese" in current:
                    sentences.append(current.copy())
                    current = {}
            elif line.startswith("SENTENCE2_JP:"):
                current["japanese"] = line.replace("SENTENCE2_JP:", "").strip()
            elif line.startswith("SENTENCE2_EN:"):
                current["english"] = line.replace("SENTENCE2_EN:", "").strip()
                if "japanese" in current:
                    sentences.append(current.copy())

        return {
            "subject_id": word.get("id"),
            "word": word["characters"],
            "reading": word["reading"],
            "meaning": word["meaning"],
            "level": word["level"],
            "sentences": sentences
        }

    except Exception as e:
        print(f"  Error generating for {word['characters']}: {e}")
        return {
            "subject_id": word.get("id"),
            "word": word["characters"],
            "reading": word["reading"],
            "meaning": word["meaning"],
            "level": word["level"],
            "sentences": []
        }

def main():
    parser = argparse.ArgumentParser(description="Generate sentences for WaniKani vocab")
    parser.add_argument("--api", choices=["ollama", "lmstudio", "custom"], default="lmstudio")
    parser.add_argument("--model", default="mistral", help="Model name for Ollama")
    parser.add_argument("--base-url", default="http://localhost:1234", help="Base URL for custom API")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of words (0=all)")
    parser.add_argument("--input", default="data/vocab.json", help="Input vocab file")
    parser.add_argument("--output", default="data/sentences.json", help="Output sentences file")
    args = parser.parse_args()

    # Set up LLM caller
    if args.api == "ollama":
        call_llm = lambda p: call_ollama(p, args.model)
        print(f"Using Ollama with model: {args.model}")
    elif args.api == "lmstudio":
        call_llm = call_lmstudio
        print("Using LM Studio")
    else:
        call_llm = lambda p: call_openai_compatible(p, args.base_url)
        print(f"Using custom API at: {args.base_url}")

    # Load vocab
    input_path = Path(__file__).parent / args.input
    if not input_path.exists():
        print(f"Error: {input_path} not found. Run fetch_vocab.py first.")
        return

    with open(input_path, "r", encoding="utf-8") as f:
        vocab = json.load(f)

    if args.limit > 0:
        vocab = vocab[:args.limit]

    print(f"\nGenerating sentences for {len(vocab)} words...")

    results = []
    for i, word in enumerate(vocab):
        print(f"[{i+1}/{len(vocab)}] {word['characters']} ({word['reading']})...")
        result = generate_sentences(word, call_llm)
        results.append(result)

        # Progress save every 10 words
        if (i + 1) % 10 == 0:
            output_path = Path(__file__).parent / args.output
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

    # Final save
    output_path = Path(__file__).parent / args.output
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    total_sentences = sum(len(r["sentences"]) for r in results)
    print(f"\nDone! Generated {total_sentences} sentences for {len(results)} words.")
    print(f"Saved to: {output_path}")

if __name__ == "__main__":
    main()
