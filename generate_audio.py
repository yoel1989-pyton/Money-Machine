#!/usr/bin/env python3
"""
Standalone audio generator for longform documentaries.
Uses subprocess to avoid asyncio timeout issues.
"""
import subprocess
import sys
import os
from pathlib import Path
import re

# Paths
BASE_DIR = Path(__file__).parent
SCRIPTS_DIR = BASE_DIR / "data" / "scripts"
AUDIO_DIR = BASE_DIR / "data" / "audio" / "longform"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

def clean_script(script: str) -> str:
    """Remove visual cues and headers from script."""
    cleaned = re.sub(r'\[VISUAL:.*?\]', '', script, flags=re.DOTALL)
    cleaned = re.sub(r'\[ACT.*?\]', '', cleaned)
    cleaned = re.sub(r'\[NARRATOR\]', '', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

def generate_audio_sync(script_path: str, output_path: str, voice: str = "en-US-AndrewNeural"):
    """Generate audio using edge-tts via the async wrapper."""
    import asyncio
    import edge_tts
    
    # Read and clean script
    with open(script_path, 'r', encoding='utf-8') as f:
        script = f.read()
    
    cleaned = clean_script(script)
    word_count = len(cleaned.split())
    print(f"[AUDIO] Script: {word_count} words")
    print(f"[AUDIO] Estimated duration: {word_count / 150:.1f} minutes")
    print(f"[AUDIO] Voice: {voice}")
    print(f"[AUDIO] Output: {output_path}")
    
    async def generate():
        communicate = edge_tts.Communicate(cleaned, voice, rate="+0%")
        await communicate.save(output_path)
    
    print("[AUDIO] Generating (this may take 1-3 minutes)...")
    
    # Use asyncio with increased timeout
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(asyncio.wait_for(generate(), timeout=300))  # 5 min timeout
    finally:
        loop.close()
    
    if os.path.exists(output_path):
        size = os.path.getsize(output_path) / 1024
        print(f"[AUDIO] Success! {size:.1f} KB")
        return True
    return False

if __name__ == "__main__":
    # Find latest script
    scripts = list(SCRIPTS_DIR.glob("elite_*.txt"))
    if not scripts:
        print("No scripts found in data/scripts/")
        sys.exit(1)
    
    latest = max(scripts, key=lambda x: x.stat().st_mtime)
    output = AUDIO_DIR / f"{latest.stem}.mp3"
    
    print(f"[AUDIO] Processing: {latest.name}")
    
    try:
        success = generate_audio_sync(str(latest), str(output))
        if success:
            print(f"\n[SUCCESS] Audio: {output}")
        else:
            print("\n[FAILED]")
    except asyncio.TimeoutError:
        print("[ERROR] Timeout - script too long or network issue")
    except Exception as e:
        print(f"[ERROR] {e}")
