#!/usr/bin/env python3
"""
ELITE_RUN_STABLE.py - Production Elite Short Generator
Uses PowerShell Start-Process to bypass Python 3.14 asyncio/signal issues

This is the GOLD STANDARD production script that:
1. Generates elite scripts using Gold Standard DNA
2. Synthesizes voice via Edge-TTS
3. Renders via FFmpeg using PowerShell isolation
4. Validates file integrity before upload
"""

import subprocess
import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from openai import OpenAI
from dotenv import load_dotenv
from engines.error_handler import (
    with_error_handling, 
    handle_error, 
    send_success_alert,
    send_status_update
)

load_dotenv()

# =============================================================================
# GOLD STANDARD ELITE TOPICS (Kiyosaki/Graham/Jikh/Minority DNA)
# =============================================================================
ELITE_TOPICS = [
    {"topic": "Why the Rich Use Debt as a Weapon", "archetype": "system_reveal"},
    {"topic": "How I Turn Debt Into Monthly Income", "archetype": "lifestyle_arbitrage"},
    {"topic": "Investing at 20 vs 40: The Shocking Math", "archetype": "comparative_narrative"},
    {"topic": "Why Poor People Pay More Taxes Than Billionaires", "archetype": "hidden_tax_logic"},
    {"topic": "The Credit Card Hack Banks Don't Want You to Know", "archetype": "lifestyle_arbitrage"},
    {"topic": "Why Your 401k Is a Trap", "archetype": "system_reveal"},
    {"topic": "How the Fed Makes You Poorer Every Year", "archetype": "hidden_tax_logic"},
    {"topic": "The $100 Weekly Investment That Builds Millions", "archetype": "comparative_narrative"},
]

# Visual mapping for B-roll selection
ARCHETYPE_VISUALS = {
    "system_reveal": ["money", "city"],
    "lifestyle_arbitrage": ["money", "lifestyle"],
    "comparative_narrative": ["people", "city"],
    "hidden_tax_logic": ["money", "tech"],
}

# =============================================================================
# CONFIGURATION
# =============================================================================
OUTPUT_DIR = Path("data/output")
TEMP_DIR = Path("data/temp")
BROLL_DIR = Path("data/assets/backgrounds/money")
MIN_FILE_SIZE_MB = 15  # Size guard for 8Mbps @ 40s

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)


def log(msg: str, level: str = "INFO"):
    """Timestamped logging"""
    ts = datetime.now().strftime("%H:%M:%S")
    prefix = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "WARN": "⚠️"}.get(level, "•")
    print(f"[{ts}] {prefix} {msg}")


@with_error_handling("ScriptGenerator", max_retries=3)
def generate_elite_script(topic: str, archetype: str) -> str:
    """Generate Gold Standard script using GPT-4o-mini"""
    log(f"Generating script: {topic}")
    
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    prompts = {
        "system_reveal": "You expose hidden financial systems. Be provocative. Challenge conventional wisdom.",
        "lifestyle_arbitrage": "You show practical money hacks. Be specific. Include real numbers.",
        "comparative_narrative": "You use comparisons to shock. Show stark contrasts. Make math visual.",
        "hidden_tax_logic": "You reveal tax secrets. Be slightly conspiratorial. Back up with logic.",
    }
    
    system_prompt = f"""You are an elite finance content creator. {prompts.get(archetype, '')}

RULES:
- Write for YouTube Shorts (40-55 seconds)
- 90-110 words MAXIMUM
- Start with a provocative hook (first 3 seconds critical)
- Use simple language, avoid jargon
- End with curiosity gap or call to action
- NO hashtags, NO emojis, NO timestamps"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Write a viral script about: {topic}"}
        ],
        max_tokens=250,
        temperature=0.8
    )
    
    script = response.choices[0].message.content.strip()
    word_count = len(script.split())
    log(f"Script generated: {word_count} words", "SUCCESS")
    return script


@with_error_handling("VoiceGenerator", max_retries=3)
def generate_voice(script: str, output_path: Path) -> float:
    """Generate voice using Edge-TTS (blocking)"""
    log(f"Generating voice: {output_path.name}")
    
    # Use Edge-TTS via subprocess (blocking)
    cmd = [
        sys.executable, "-m", "edge_tts",
        "--voice", "en-US-GuyNeural",
        "--rate", "+5%",
        "--text", script,
        "--write-media", str(output_path)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    
    if result.returncode != 0:
        log(f"Edge-TTS error: {result.stderr}", "ERROR")
        raise RuntimeError("Voice generation failed")
    
    # Get duration via ffprobe
    probe_cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json", str(output_path)
    ]
    probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)
    duration = float(json.loads(probe_result.stdout)["format"]["duration"])
    
    log(f"Voice generated: {duration:.1f}s, {output_path.stat().st_size / 1024:.1f} KB", "SUCCESS")
    return duration


@with_error_handling("BrollSelector", max_retries=1)
def select_broll(archetype: str) -> Path:
    """Select B-roll based on archetype"""
    categories = ARCHETYPE_VISUALS.get(archetype, ["money"])
    
    # For now, use money_real_1.mp4 as proven Gold Standard
    broll = BROLL_DIR / "money_real_1.mp4"
    if broll.exists():
        log(f"B-roll selected: {broll.name}")
        return broll
    
    # Fallback: find any mp4
    for mp4 in BROLL_DIR.glob("*.mp4"):
        log(f"B-roll fallback: {mp4.name}")
        return mp4
    
    raise FileNotFoundError("No B-roll found!")


@with_error_handling("VideoRenderer", max_retries=2)
def render_video_powershell(broll: Path, audio: Path, output: Path, duration: float):
    """
    Render video using PowerShell Start-Process to ISOLATE from Python's signal handling.
    This is the critical fix for Python 3.14's broken asyncio on Windows.
    """
    log(f"Rendering video via PowerShell isolation...")
    
    # Target duration slightly longer than audio to prevent cuts
    target_duration = min(duration + 2, 58)  # Max 58s for Shorts
    
    # Build FFmpeg command
    ffmpeg_args = (
        f'-y '
        f'-stream_loop -1 -i "{broll}" '
        f'-i "{audio}" '
        f'-map 0:v:0 -map 1:a:0 '
        f'-t {target_duration:.1f} '
        f'-vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,eq=contrast=1.08:saturation=1.12" '
        f'-c:v libx264 -profile:v high -preset fast '
        f'-b:v 8M -minrate 6M -maxrate 10M -bufsize 16M '
        f'-c:a aac -b:a 192k '
        f'"{output}"'
    )
    
    # Use PowerShell Start-Process to fully isolate FFmpeg
    ps_command = f'Start-Process -NoNewWindow -Wait -FilePath "ffmpeg" -ArgumentList \'{ffmpeg_args}\''
    
    log(f"Target: {target_duration:.1f}s @ 8Mbps")
    
    result = subprocess.run(
        ["powershell", "-Command", ps_command],
        capture_output=True,
        text=True,
        timeout=600  # 10 minute timeout for safety
    )
    
    # Verify output
    if not output.exists():
        log("FFmpeg produced no output!", "ERROR")
        raise RuntimeError("Render failed")
    
    size_mb = output.stat().st_size / (1024 * 1024)
    
    if size_mb < MIN_FILE_SIZE_MB:
        log(f"File too small: {size_mb:.1f} MB (min: {MIN_FILE_SIZE_MB} MB)", "ERROR")
        raise RuntimeError(f"Render corrupted: {size_mb:.1f} MB < {MIN_FILE_SIZE_MB} MB")
    
    log(f"Render complete: {size_mb:.1f} MB", "SUCCESS")
    return output


def validate_final_video(video_path: Path) -> dict:
    """Validate video meets YouTube Shorts requirements"""
    log("Validating final video...")
    
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration,bit_rate,size",
        "-show_entries", "stream=width,height,codec_name",
        "-of", "json", str(video_path)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    data = json.loads(result.stdout)
    
    fmt = data["format"]
    streams = data["streams"]
    video_stream = next((s for s in streams if s.get("codec_name") == "h264"), None)
    
    validation = {
        "path": str(video_path),
        "size_mb": int(fmt["size"]) / (1024 * 1024),
        "duration": float(fmt["duration"]),
        "bitrate_mbps": int(fmt["bit_rate"]) / 1_000_000,
        "width": video_stream["width"] if video_stream else 0,
        "height": video_stream["height"] if video_stream else 0,
    }
    
    # Check requirements
    checks = [
        ("Size > 15MB", validation["size_mb"] > 15),
        ("Duration ≤ 60s", validation["duration"] <= 60),
        ("Resolution 1080x1920", validation["width"] == 1080 and validation["height"] == 1920),
        ("Bitrate > 5 Mbps", validation["bitrate_mbps"] > 5),
    ]
    
    all_passed = True
    for check_name, passed in checks:
        status = "✅" if passed else "❌"
        log(f"  {status} {check_name}")
        if not passed:
            all_passed = False
    
    if all_passed:
        log("Video validated - READY FOR UPLOAD!", "SUCCESS")
    else:
        log("Video validation FAILED", "ERROR")
    
    validation["valid"] = all_passed
    return validation


def main():
    """Main production flow"""
    print("\n" + "="*60)
    print("   💰 ELITE SHORT GENERATOR - GOLD STANDARD")
    print("="*60 + "\n")
    
    # Select topic (can be overridden via CLI)
    topic_idx = 0
    if len(sys.argv) > 1:
        for i, t in enumerate(ELITE_TOPICS):
            if sys.argv[1].lower() in t["topic"].lower():
                topic_idx = i
                break
    
    topic_data = ELITE_TOPICS[topic_idx]
    topic = topic_data["topic"]
    archetype = topic_data["archetype"]
    
    log(f"Topic: {topic}")
    log(f"Archetype: {archetype}")
    
    # Generate timestamp for this run
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        # Step 1: Generate script
        script = generate_elite_script(topic, archetype)
        
        # Save script for reference
        script_path = TEMP_DIR / f"elite_{ts}_script.txt"
        script_path.write_text(script)
        
        # Step 2: Generate voice
        audio_path = TEMP_DIR / f"elite_{ts}_voice.mp3"
        duration = generate_voice(script, audio_path)
        
        # Step 3: Select B-roll
        broll = select_broll(archetype)
        
        # Step 4: Render video (PowerShell isolation)
        output_path = OUTPUT_DIR / f"elite_{ts}_video.mp4"
        render_video_powershell(broll, audio_path, output_path, duration)
        
        # Step 5: Validate
        validation = validate_final_video(output_path)
        
        print("\n" + "="*60)
        if validation["valid"]:
            print("   🏆 ELITE SHORT READY FOR UPLOAD!")
            print(f"   📁 {output_path}")
            print(f"   📊 {validation['size_mb']:.1f} MB | {validation['duration']:.1f}s | {validation['bitrate_mbps']:.1f} Mbps")
            
            # Step 6: Upload to YouTube
            upload_result = None
            try:
                import asyncio
                from engines.uploaders import MasterUploader
                uploader = MasterUploader()
                
                # Generate title and description
                title = f"{topic} #shorts #money #finance"
                description = f"""🔥 {topic}

💰 Subscribe for daily wealth wisdom!

#shorts #finance #money #investing #wealth #financialfreedom #millionaire"""
                
                log("Uploading to YouTube...")
                
                # Run async upload in sync context
                async def do_upload():
                    return await uploader.upload_youtube_only(
                        video_path=str(output_path),
                        title=title[:100],
                        description=description,
                        tags=["shorts", "money", "finance", "investing", "wealth"]
                    )
                
                upload_result = asyncio.run(do_upload())
                
                if upload_result and upload_result.get("success"):
                    log(f"✅ UPLOADED: {upload_result.get('url', 'Success')}", "SUCCESS")
                else:
                    log(f"Upload returned: {upload_result}", "WARN")
                    
            except Exception as upload_err:
                log(f"Upload failed: {upload_err}", "WARN")
                upload_result = {"success": False, "error": str(upload_err)}
            
            # Send success alert to Telegram
            upload_status = "✅ UPLOADED" if (upload_result and upload_result.get("success")) else "⏳ Ready for manual upload"
            send_success_alert(
                f"Elite Short Complete!\n\n"
                f"📹 Topic: {topic}\n"
                f"📊 {validation['size_mb']:.1f} MB | {validation['duration']:.1f}s | {validation['bitrate_mbps']:.1f} Mbps\n"
                f"📁 {output_path.name}\n"
                f"🎬 Status: {upload_status}"
            )
        else:
            print("   ❌ VALIDATION FAILED - CHECK LOGS")
            handle_error(Exception("Video validation failed"), "VideoValidator")
        print("="*60 + "\n")
        
        return 0 if validation["valid"] else 1
        
    except Exception as e:
        log(f"FATAL: {e}", "ERROR")
        handle_error(e, "EliteRunMain")
        return 1


if __name__ == "__main__":
    sys.exit(main())
