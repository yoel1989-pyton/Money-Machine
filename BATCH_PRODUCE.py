#!/usr/bin/env python3
"""
BATCH_PRODUCE.py - Mass Elite Short Production
================================================
Produces multiple Elite Shorts and stores them locally for:
- Manual upload later
- Auto-scheduled upload
- Local review before publishing

Usage:
    python BATCH_PRODUCE.py              # Produce 5 videos (default)
    python BATCH_PRODUCE.py --count 10   # Produce 10 videos
    python BATCH_PRODUCE.py --continuous # Keep producing until stopped
"""

import subprocess
import sys
import os
import json
import argparse
import random
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from openai import OpenAI
from dotenv import load_dotenv
from engines.error_handler import send_success_alert, send_status_update

load_dotenv()

# =============================================================================
# CONFIGURATION
# =============================================================================
OUTPUT_DIR = Path("data/output/queue")  # Queue folder for pending uploads
TEMP_DIR = Path("data/temp")
BROLL_ROOT = Path("data/assets/backgrounds")  # Root for all B-roll folders
MANIFEST_PATH = Path("data/output/upload_queue.json")

# Used B-roll tracking to avoid repeats
USED_BROLL = set()

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Elite topics pool - rotate through these
ELITE_TOPICS = [
    {"topic": "Why the Rich Use Debt as a Weapon", "archetype": "system_reveal"},
    {"topic": "How I Turn Debt Into Monthly Income", "archetype": "lifestyle_arbitrage"},
    {"topic": "Investing at 20 vs 40: The Shocking Math", "archetype": "comparative_narrative"},
    {"topic": "Why Poor People Pay More Taxes Than Billionaires", "archetype": "hidden_tax_logic"},
    {"topic": "The Credit Card Hack Banks Don't Want You to Know", "archetype": "lifestyle_arbitrage"},
    {"topic": "Why Your 401k Is a Trap", "archetype": "system_reveal"},
    {"topic": "How the Fed Makes You Poorer Every Year", "archetype": "hidden_tax_logic"},
    {"topic": "The $100 Weekly Investment That Builds Millions", "archetype": "comparative_narrative"},
    {"topic": "Why Banks Want You Broke", "archetype": "system_reveal"},
    {"topic": "The 3 Assets Rich People Never Sell", "archetype": "lifestyle_arbitrage"},
    {"topic": "Why Saving Money Makes You Poor", "archetype": "hidden_tax_logic"},
    {"topic": "How to Pay Zero Taxes Legally", "archetype": "system_reveal"},
    {"topic": "The Side Hustle That Replaced My Salary", "archetype": "lifestyle_arbitrage"},
    {"topic": "Why Your Boss Wants You in Debt", "archetype": "hidden_tax_logic"},
    {"topic": "The Investing Mistake 90% of People Make", "archetype": "comparative_narrative"},
]

# B-roll category mapping for topic archetypes
BROLL_MAPPING = {
    "system_reveal": ["city", "tech", "money"],
    "lifestyle_arbitrage": ["lifestyle", "city", "money"],
    "comparative_narrative": ["money", "people", "tech"],
    "hidden_tax_logic": ["city", "money", "tech"],
}


def get_all_broll_files() -> list:
    """Scan all available B-roll files"""
    broll_files = []
    exclude_folders = ["_deprecated", "test"]
    
    for folder in BROLL_ROOT.iterdir():
        if folder.is_dir() and folder.name not in exclude_folders:
            for f in folder.glob("*.mp4"):
                if f.stat().st_size > 500_000:  # At least 500KB
                    broll_files.append({
                        "path": f,
                        "category": folder.name,
                        "size_mb": f.stat().st_size / (1024 * 1024)
                    })
    return broll_files


def pick_diverse_broll(archetype: str) -> Path:
    """Pick B-roll with diversity - never repeat until all used"""
    global USED_BROLL
    
    all_broll = get_all_broll_files()
    
    if not all_broll:
        raise FileNotFoundError("No B-roll files found!")
    
    # Preferred categories for this archetype
    preferred = BROLL_MAPPING.get(archetype, ["money", "city", "tech"])
    
    # Filter to unused B-roll in preferred categories
    candidates = [
        b for b in all_broll 
        if b["category"] in preferred and str(b["path"]) not in USED_BROLL
    ]
    
    # If all preferred used, try any unused
    if not candidates:
        candidates = [b for b in all_broll if str(b["path"]) not in USED_BROLL]
    
    # If ALL used, reset tracking
    if not candidates:
        USED_BROLL.clear()
        candidates = [b for b in all_broll if b["category"] in preferred]
        if not candidates:
            candidates = all_broll
    
    # Random selection
    selected = random.choice(candidates)
    USED_BROLL.add(str(selected["path"]))
    
    return selected["path"]


def log(msg: str, level: str = "INFO"):
    ts = datetime.now().strftime("%H:%M:%S")
    prefix = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "WARN": "⚠️", "BATCH": "📦"}.get(level, "•")
    print(f"[{ts}] {prefix} {msg}")


def load_manifest() -> dict:
    """Load upload queue manifest"""
    if MANIFEST_PATH.exists():
        return json.loads(MANIFEST_PATH.read_text())
    return {"pending": [], "uploaded": [], "failed": []}


def save_manifest(manifest: dict):
    """Save upload queue manifest"""
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2))


def add_to_queue(video_info: dict):
    """Add video to upload queue"""
    manifest = load_manifest()
    manifest["pending"].append(video_info)
    save_manifest(manifest)
    log(f"Added to queue: {video_info['filename']} ({len(manifest['pending'])} pending)", "BATCH")


def generate_script(topic: str, archetype: str) -> str:
    """Generate script using GPT-4o-mini"""
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    prompts = {
        "system_reveal": "You expose hidden financial systems. Be provocative.",
        "lifestyle_arbitrage": "You show practical money hacks. Be specific with numbers.",
        "comparative_narrative": "You use comparisons to shock. Show stark contrasts.",
        "hidden_tax_logic": "You reveal tax secrets. Be slightly conspiratorial.",
    }
    
    system_prompt = f"""You are an elite finance content creator. {prompts.get(archetype, '')}

RULES:
- Write for YouTube Shorts (40-55 seconds)
- 90-110 words MAXIMUM
- Start with a provocative hook
- Use simple language
- End with curiosity gap
- NO hashtags, NO emojis"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Write a viral script about: {topic}"}
        ],
        max_tokens=250,
        temperature=0.85
    )
    
    return response.choices[0].message.content.strip()


def generate_voice(script: str, output_path: Path) -> float:
    """Generate voice using Edge-TTS"""
    cmd = [
        sys.executable, "-m", "edge_tts",
        "--voice", "en-US-GuyNeural",
        "--rate", "+5%",
        "--text", script,
        "--write-media", str(output_path)
    ]
    
    subprocess.run(cmd, capture_output=True, timeout=120)
    
    # Get duration
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(output_path)],
        capture_output=True, text=True
    )
    return float(json.loads(probe.stdout)["format"]["duration"])


def render_video(audio: Path, output: Path, duration: float, archetype: str) -> bool:
    """Render video using PowerShell isolation with Hollywood scene cuts"""
    target_duration = min(duration + 2, 58)
    
    # Pick multiple B-roll clips for scene cuts (1.5-3 second segments)
    scene_clips = []
    remaining = target_duration
    
    while remaining > 0:
        broll = pick_diverse_broll(archetype)
        scene_duration = random.uniform(1.5, 3.0)  # Hollywood cut timing
        scene_duration = min(scene_duration, remaining)
        scene_clips.append((broll, scene_duration))
        remaining -= scene_duration
    
    log(f"   Using {len(scene_clips)} scene cuts from diverse B-roll")
    
    # Create concat list file for FFmpeg
    concat_file = TEMP_DIR / f"concat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    with open(concat_file, "w") as f:
        for clip, dur in scene_clips:
            # Escape path for FFmpeg
            safe_path = str(clip).replace("\\", "/").replace("'", "'\\''")
            f.write(f"file '{safe_path}'\n")
            f.write(f"inpoint 0\n")
            f.write(f"outpoint {dur:.2f}\n")
    
    # FFmpeg concat demuxer with audio overlay
    safe_concat = str(concat_file).replace("\\", "/")
    safe_audio = str(audio).replace("\\", "/")
    safe_output = str(output).replace("\\", "/")
    
    ffmpeg_args = (
        f'-y -f concat -safe 0 -i "{safe_concat}" -i "{safe_audio}" '
        f'-map 0:v:0 -map 1:a:0 -t {target_duration:.1f} '
        f'-vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,eq=contrast=1.08:saturation=1.12" '
        f'-c:v libx264 -profile:v high -preset fast -b:v 8M -minrate 6M -maxrate 10M -bufsize 16M '
        f'-c:a aac -b:a 192k "{safe_output}"'
    )
    
    ps_command = f"Start-Process -NoNewWindow -Wait -FilePath 'ffmpeg' -ArgumentList '{ffmpeg_args}'"
    
    result = subprocess.run(
        ["powershell", "-Command", ps_command],
        capture_output=True, timeout=600
    )
    
    # Cleanup concat file
    concat_file.unlink(missing_ok=True)
    
    if output.exists():
        size_mb = output.stat().st_size / (1024 * 1024)
        return size_mb > 15  # Quality gate
    return False


def produce_one(topic_data: dict, batch_num: int) -> dict:
    """Produce a single Elite Short"""
    topic = topic_data["topic"]
    archetype = topic_data["archetype"]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    log(f"[{batch_num}] Producing: {topic[:40]}...")
    
    try:
        # Generate script
        script = generate_script(topic, archetype)
        word_count = len(script.split())
        log(f"[{batch_num}] Script: {word_count} words")
        
        # Save script
        script_path = TEMP_DIR / f"batch_{ts}_script.txt"
        script_path.write_text(script)
        
        # Generate voice
        audio_path = TEMP_DIR / f"batch_{ts}_voice.mp3"
        duration = generate_voice(script, audio_path)
        log(f"[{batch_num}] Voice: {duration:.1f}s")
        
        # Render with diverse B-roll + Hollywood cuts
        output_filename = f"elite_{ts}_{topic[:20].replace(' ', '_')}.mp4"
        output_path = OUTPUT_DIR / output_filename
        
        log(f"[{batch_num}] Rendering with scene cuts...")
        success = render_video(audio_path, output_path, duration, archetype)
        
        if success:
            size_mb = output_path.stat().st_size / (1024 * 1024)
            log(f"[{batch_num}] ✅ Complete: {size_mb:.1f} MB", "SUCCESS")
            
            # Create video info for queue
            video_info = {
                "filename": output_filename,
                "path": str(output_path),
                "topic": topic,
                "archetype": archetype,
                "duration": duration,
                "size_mb": round(size_mb, 2),
                "created": datetime.now().isoformat(),
                "status": "pending",
                "title": f"{topic} #shorts #money #finance",
                "description": f"🔥 {topic}\n\n💰 Subscribe for daily wealth wisdom!\n\n#shorts #finance #money #investing",
                "script": script
            }
            
            # Add to upload queue
            add_to_queue(video_info)
            
            return {"success": True, "video": video_info}
        else:
            log(f"[{batch_num}] ❌ Render failed", "ERROR")
            return {"success": False, "error": "Render failed"}
            
    except Exception as e:
        log(f"[{batch_num}] ❌ Error: {e}", "ERROR")
        return {"success": False, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Batch produce Elite Shorts")
    parser.add_argument("--count", type=int, default=5, help="Number of videos to produce")
    parser.add_argument("--continuous", action="store_true", help="Keep producing until stopped")
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("   📦 BATCH ELITE PRODUCER")
    print("   Videos will be stored in: data/output/queue/")
    print("="*60 + "\n")
    
    produced = 0
    failed = 0
    topic_index = 0
    
    try:
        while True:
            # Get next topic (rotate through pool)
            topic_data = ELITE_TOPICS[topic_index % len(ELITE_TOPICS)]
            topic_index += 1
            
            # Produce
            result = produce_one(topic_data, produced + 1)
            
            if result["success"]:
                produced += 1
            else:
                failed += 1
            
            # Check if we should continue
            if not args.continuous and produced >= args.count:
                break
            
            # Small delay between productions
            if args.continuous or produced < args.count:
                log(f"Completed {produced}/{args.count if not args.continuous else '∞'} | Failed: {failed}")
                
    except KeyboardInterrupt:
        log("\n⚠️ Stopped by user", "WARN")
    
    # Summary
    manifest = load_manifest()
    print("\n" + "="*60)
    print(f"   📊 BATCH COMPLETE")
    print(f"   Produced: {produced} | Failed: {failed}")
    print(f"   Queue: {len(manifest['pending'])} videos pending upload")
    print(f"   Location: {OUTPUT_DIR}")
    print("="*60 + "\n")
    
    # Send Telegram summary
    send_success_alert(
        f"Batch Production Complete!\n\n"
        f"📦 Produced: {produced} videos\n"
        f"❌ Failed: {failed}\n"
        f"📋 Queue: {len(manifest['pending'])} pending\n"
        f"📁 Location: data/output/queue/"
    )
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
