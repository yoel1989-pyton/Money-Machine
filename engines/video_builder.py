"""
MONEY MACHINE - VIDEO BUILDER v2.0
Uses REAL video backgrounds with visual entropy validation.
"""

import subprocess
import random
import os
import uuid
import json
import asyncio
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

BG_DIR = Path(__file__).parent.parent / "data" / "assets" / "backgrounds"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "output"
TEMP_DIR = Path(__file__).parent.parent / "data" / "temp"
DEFAULT_DURATION = 58


def pick_background() -> str:
    """Pick a random real video background, excluding deprecated folders."""
    BG_DIR.mkdir(parents=True, exist_ok=True)
    videos = []
    for root, dirs, files in os.walk(BG_DIR):
        if "_deprecated" in root or "synthetic" in root.lower():
            continue
        for f in files:
            if f.endswith(('.mp4', '.mov', '.webm', '.mkv')):
                videos.append(os.path.join(root, f))
    if not videos:
        raise RuntimeError(f"NO REAL BACKGROUNDS in {BG_DIR}")
    return random.choice(videos)


def validate_visual_entropy(video_path: str, min_bitrate: int = 500_000) -> Tuple[bool, dict]:
    """Validate video has sufficient visual entropy for YouTube."""
    try:
        cmd = f'ffprobe -v error -select_streams v:0 -show_entries stream=bit_rate,nb_frames,codec_name -show_entries format=bit_rate -of json "{video_path}"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        data = json.loads(result.stdout)
        stream = data.get("streams", [{}])[0]
        fmt = data.get("format", {})
        bitrate = int(stream.get("bit_rate") or fmt.get("bit_rate") or 0)
        nb_frames = int(stream.get("nb_frames") or 0)
        codec = stream.get("codec_name", "unknown")
        passed = bitrate >= min_bitrate and nb_frames >= 500 and codec in ["h264", "hevc", "vp9", "av1"]
        return passed, {"bitrate": bitrate, "nb_frames": nb_frames, "codec": codec, "passed": passed}
    except Exception as e:
        return False, {"error": str(e), "passed": False}


async def build_video(audio_path: str, output_dir: str = None, duration: int = None, background_path: str = None) -> str:
    """Build YouTube-ready video with real motion background."""
    output_dir = Path(output_dir or OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    duration = duration or DEFAULT_DURATION
    bg = background_path or pick_background()
    output_path = str(output_dir / f"final_{uuid.uuid4().hex[:8]}.mp4")
    
    try:
        result = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", audio_path], capture_output=True, text=True)
        audio_duration = float(json.loads(result.stdout)["format"]["duration"])
        duration = min(duration, audio_duration + 1)
    except: pass
    
    cmd = [
        "ffmpeg", "-y", "-stream_loop", "-1", "-i", bg, "-i", audio_path,
        "-map", "0:v:0", "-map", "1:a:0", "-t", str(duration),
        "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,eq=contrast=1.05:saturation=1.1,format=yuv420p",
        "-c:v", "libx264", "-profile:v", "high", "-level", "4.1", "-preset", "fast", "-crf", "23",
        "-b:v", "6000k", "-maxrate", "8000k", "-bufsize", "12000k", "-r", "30", "-g", "60",
        "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-movflags", "+faststart", output_path
    ]
    
    process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    await process.communicate()
    if process.returncode != 0 or not os.path.exists(output_path):
        raise RuntimeError("FFmpeg failed")
    return output_path


def build_video_sync(audio_path: str, output_dir: str = None, duration: int = None, background_path: str = None) -> str:
    return asyncio.run(build_video(audio_path, output_dir, duration, background_path))


# ============================================================
# ELITE AAVE-INTEGRATED VIDEO BUILDER
# ============================================================

async def build_elite_short(
    audio_path: str,
    output_path: str = None,
    dna_params: Dict[str, Any] = None,
    background_path: str = None
) -> str:
    """
    Build an ELITE YouTube Short using AAVE Visual DNA parameters.
    
    This uses the exact FFmpeg pipeline that works for:
    - Finance Shorts
    - Motivation giants  
    - Faceless history channels
    - TikTok agencies
    
    Features:
    - zoompan = continuous cinematic motion
    - force_original_aspect_ratio=increase = no floating box
    - eq + unsharp = perceived detail (YouTube LOVES this)
    - 7-8 Mbps = Shorts sweet spot
    """
    output_dir = OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if output_path is None:
        output_path = str(output_dir / f"elite_{uuid.uuid4().hex[:8]}.mp4")
    
    bg = background_path or pick_background()
    
    # Default DNA params (can be overridden by AAVE)
    params = {
        "contrast": 1.07,
        "saturation": 1.12,
        "brightness": 0.02,
        "sharpness": 0.9,
        "zoom_rate": 0.0009,
        "zoom_max": 1.08,
    }
    if dna_params:
        params.update(dna_params)
    
    print(f"[ELITE] 🎬 Building elite short...")
    print(f"[ELITE] Background: {Path(bg).name}")
    
    # Get audio duration
    audio_duration = 58
    try:
        result = subprocess.run([
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "json", audio_path
        ], capture_output=True, text=True)
        audio_duration = float(json.loads(result.stdout)["format"]["duration"])
    except:
        pass
    
    # Calculate zoompan duration in frames (30fps)
    zoom_frames = int(audio_duration * 30)
    
    # Build the ELITE FFmpeg filter chain
    filter_complex = (
        f"[0:v]"
        f"scale=1920:1080,"
        f"scale=1080:1920:force_original_aspect_ratio=increase,"
        f"crop=1080:1920,"
        f"fps=30,"
        f"zoompan=z='min(zoom+{params['zoom_rate']},{params['zoom_max']})':"
        f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        f"d={zoom_frames}:s=1080x1920,"
        f"eq=contrast={params['contrast']}:saturation={params['saturation']}:"
        f"brightness={params['brightness']},"
        f"unsharp=5:5:{params['sharpness']}"
        f"[v];"
        f"[v]format=yuv420p[outv]"
    )
    
    cmd = [
        "ffmpeg", "-y",
        "-stream_loop", "-1",
        "-i", bg,
        "-i", audio_path,
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-map", "1:a",
        "-c:v", "libx264",
        "-profile:v", "high",
        "-level", "4.2",
        "-pix_fmt", "yuv420p",
        "-r", "30",
        "-g", "60",
        "-keyint_min", "60",
        "-b:v", "7M",
        "-maxrate", "8M",
        "-bufsize", "12M",
        "-c:a", "aac",
        "-b:a", "128k",
        "-movflags", "+faststart",
        "-shortest",
        output_path
    ]
    
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    
    if process.returncode != 0:
        print(f"[ELITE] ⚠️ Zoompan failed, using fallback...")
        return await build_video(audio_path, str(output_dir), background_path=bg)
    
    if not os.path.exists(output_path):
        raise RuntimeError("Elite video was not created")
    
    file_size = os.path.getsize(output_path) / (1024 * 1024)
    passed, details = validate_visual_entropy(output_path, min_bitrate=2_000_000)
    
    if passed:
        print(f"[ELITE] ✅ Elite short created: {output_path}")
        print(f"[ELITE] 📊 Size: {file_size:.2f} MB, Bitrate: {details['bitrate']/1_000_000:.2f} Mbps")
    
    return output_path


def build_elite_short_sync(
    audio_path: str,
    output_path: str = None,
    dna_params: Dict[str, Any] = None,
    background_path: str = None
) -> str:
    """Synchronous wrapper for build_elite_short."""
    return asyncio.run(build_elite_short(audio_path, output_path, dna_params, background_path))


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        audio = sys.argv[1]
        video = build_elite_short_sync(audio)
        print(f"Created: {video}")
    else:
        BG_DIR.mkdir(parents=True, exist_ok=True)
        vids = list(BG_DIR.glob("**/*.mp4"))
        print(f"Background videos: {len(vids)}")
        for v in vids[:5]:
            passed, details = validate_visual_entropy(str(v))
            status = "✅" if passed else "❌"
            print(f"  {status} {v.name}: {details.get('bitrate', 0)/1_000_000:.2f} Mbps")
