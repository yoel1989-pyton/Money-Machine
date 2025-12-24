#!/usr/bin/env python3
"""
════════════════════════════════════════════════════════════════
🛡️ ELITE RUN - Blocking Authority Wrapper
════════════════════════════════════════════════════════════════
Bypasses Python 3.14 asyncio issues by running production
synchronously with full process control.

Usage:
    python ELITE_RUN.py --topic "Why the Rich Use Debt as a Weapon"
    python ELITE_RUN.py --elite  # Random elite topic
════════════════════════════════════════════════════════════════
"""

import os
import sys
import json
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

# ============================================================
# CONFIGURATION
# ============================================================

DATA_DIR = Path(__file__).parent / "data"
TEMP_DIR = DATA_DIR / "temp"
OUTPUT_DIR = DATA_DIR / "output"
ASSETS_DIR = DATA_DIR / "assets" / "backgrounds"

TEMP_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def get_elite_topic():
    """Get elite topic from AAVE engine."""
    from engines.aave_engine import AAVEEngine
    aave = AAVEEngine()
    topic_data, dna = aave.select_elite_topic()
    return topic_data["topic"], topic_data.get("visual_intent", "power_finance")


def generate_script_sync(topic: str) -> str:
    """Generate script synchronously."""
    import openai
    
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """You are a viral YouTube Shorts scriptwriter. Write punchy, 
high-retention scripts about money, wealth, and financial systems.
Rules:
- 90-110 words max
- Start with a hook (question or shocking statement)
- Use short sentences (5-12 words)
- End with a thought-provoking statement
- NO emojis, hashtags, or timestamps
- Write in conversational, authoritative voice"""
            },
            {"role": "user", "content": f"Write a viral 60-second script about: {topic}"}
        ],
        temperature=0.8
    )
    
    return response.choices[0].message.content.strip()


def generate_voice_sync(script: str, output_path: str) -> bool:
    """Generate voice using edge-tts subprocess."""
    import asyncio
    import edge_tts
    
    async def _generate():
        communicate = edge_tts.Communicate(script, "en-US-AndrewNeural")
        await communicate.save(output_path)
    
    # Run in isolated event loop
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_generate())
        return True
    except Exception as e:
        print(f"   ❌ TTS Error: {e}")
        return False
    finally:
        loop.close()


def get_audio_duration(audio_path: str) -> float:
    """Get audio duration using ffprobe."""
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "json", audio_path],
        capture_output=True, text=True
    )
    try:
        return float(json.loads(result.stdout)["format"]["duration"])
    except:
        return 45.0


def get_broll_path(visual_intent: str) -> str:
    """Get B-roll path based on visual intent."""
    intent_to_folder = {
        "power_finance": "money",
        "systems_control": "tech",
        "wealth_hacks": "money",
        "psychology": "people",
    }
    
    folder = intent_to_folder.get(visual_intent, "money")
    folder_path = ASSETS_DIR / folder
    
    if folder_path.exists():
        videos = list(folder_path.glob("*.mp4"))
        if videos:
            # Prefer "real" footage
            real_videos = [v for v in videos if "real" in v.name.lower()]
            return str(real_videos[0] if real_videos else videos[0])
    
    # Fallback to any available video
    for folder in ASSETS_DIR.iterdir():
        if folder.is_dir():
            videos = list(folder.glob("*.mp4"))
            if videos:
                return str(videos[0])
    
    return None


def assemble_video_sync(audio_path: str, bg_path: str, output_path: str, duration: float) -> bool:
    """
    🛡️ BLOCKING AUTHORITY - Full FFmpeg execution with no interruption.
    """
    duration = min(duration, 58.0)
    
    cmd = (
        f'ffmpeg -y -stream_loop -1 -i "{bg_path}" -i "{audio_path}" '
        f'-map 0:v:0 -map 1:a:0 -t {duration} '
        f'-vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,'
        f'eq=contrast=1.08:saturation=1.12,noise=alls=20:allf=t+u,format=yuv420p" '
        f'-c:v libx264 -profile:v high -level 4.2 -preset slow -pix_fmt yuv420p '
        f'-b:v 8M -minrate 6M -maxrate 10M -bufsize 16M -g 60 -keyint_min 60 -sc_threshold 0 '
        f'-c:a aac -b:a 192k -ar 48000 -movflags +faststart "{output_path}"'
    )
    
    print(f"   🎬 [AUTHORITY] Starting Blocking Render...")
    print(f"   ⏳ Duration: {duration:.1f}s - This may take 2-3 minutes...")
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        
        if result.returncode != 0:
            # Check if file exists anyway (FFmpeg sometimes exits non-zero but succeeds)
            if os.path.exists(output_path):
                size_mb = os.path.getsize(output_path) / (1024 * 1024)
                if size_mb > 15:
                    print(f"   ⚠️ FFmpeg returned error but file seems valid ({size_mb:.1f}MB)")
                    return True
            print(f"   ❌ FFmpeg error")
            return False
        
        return True
        
    except subprocess.TimeoutExpired:
        print(f"   ❌ FFmpeg timeout (10 min)")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def validate_output(output_path: str) -> bool:
    """Validate the output file."""
    if not os.path.exists(output_path):
        print(f"   🚫 File not found")
        return False
    
    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    
    if size_mb < 15:
        print(f"   🚫 [GATE] Integrity FAILED: {size_mb:.2f}MB < 15MB minimum")
        return False
    
    # Verify with ffprobe
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration,bit_rate",
         "-of", "json", output_path],
        capture_output=True, text=True
    )
    
    try:
        data = json.loads(result.stdout)
        duration = float(data["format"]["duration"])
        bitrate = int(data["format"]["bit_rate"]) / 1_000_000
        
        print(f"   💎 [GATE] Verified: {size_mb:.1f}MB | {duration:.1f}s | {bitrate:.2f}Mbps")
        return True
    except:
        print(f"   🚫 Could not verify file metadata")
        return False


def main():
    parser = argparse.ArgumentParser(description="Elite Money Machine - Blocking Authority")
    parser.add_argument("--topic", type=str, help="Forced topic")
    parser.add_argument("--elite", action="store_true", help="Use AAVE elite topic")
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("🛡️ ELITE RUN - BLOCKING AUTHORITY MODE")
    print("="*60)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Step 1: Get topic
    if args.topic:
        topic = args.topic
        visual_intent = "power_finance"
        print(f"\n🎯 FORCED TOPIC: {topic}")
    elif args.elite:
        topic, visual_intent = get_elite_topic()
        print(f"\n🔥 ELITE TOPIC: {topic}")
        print(f"   Visual Intent: {visual_intent}")
    else:
        topic = "Why the Rich Use Debt as a Weapon"
        visual_intent = "power_finance"
        print(f"\n📝 DEFAULT TOPIC: {topic}")
    
    # Step 2: Generate script
    print(f"\n📝 Generating script...")
    script = generate_script_sync(topic)
    word_count = len(script.split())
    print(f"   ✓ {word_count} words")
    
    # Step 3: Generate voice
    audio_path = str(TEMP_DIR / f"elite_{timestamp}_voice.mp3")
    print(f"\n🎙️ Generating voice...")
    if not generate_voice_sync(script, audio_path):
        print("   ❌ Voice generation failed")
        return 1
    
    audio_size = os.path.getsize(audio_path) / 1024
    print(f"   ✓ {audio_size:.1f} KB")
    
    # Step 4: Get B-roll
    print(f"\n🎬 Selecting B-roll...")
    bg_path = get_broll_path(visual_intent)
    if not bg_path:
        print("   ❌ No B-roll found")
        return 1
    print(f"   ✓ {Path(bg_path).name}")
    
    # Step 5: Get duration
    duration = get_audio_duration(audio_path)
    print(f"   ⏱️ Audio duration: {duration:.1f}s")
    
    # Step 6: Assemble video (BLOCKING)
    output_path = str(OUTPUT_DIR / f"elite_{timestamp}_video.mp4")
    print(f"\n🎥 Assembling video...")
    
    if not assemble_video_sync(audio_path, bg_path, output_path, duration):
        print("\n❌ ASSEMBLY FAILED")
        return 1
    
    # Step 7: Validate
    print(f"\n🔍 Validating output...")
    if not validate_output(output_path):
        print("\n❌ VALIDATION FAILED")
        return 1
    
    print("\n" + "="*60)
    print("✅ ELITE SHORT COMPLETE")
    print("="*60)
    print(f"📁 Output: {output_path}")
    print(f"📝 Topic: {topic}")
    print("="*60 + "\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
