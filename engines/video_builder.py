"""
============================================================
MONEY MACHINE - GLOBAL VIDEO BUILDER
Elite Visual Guarantee System
============================================================
ENFORCES visuals across ALL video paths:
- Local runs
- Railway deployments
- n8n workers
- All APIs (YouTube, TikTok, Instagram)
- All creators (TTS, NotebookLM, Veo, CapCut)

BLOCKS audio-only shorts PERMANENTLY.
============================================================
"""

import subprocess
import os
import json
import uuid
import shutil
from pathlib import Path
from typing import Optional

# ============================================================
# CONFIGURATION
# ============================================================

SAFE_DURATION = 58  # Maximum duration for Shorts
MIN_FRAMES = 900    # Minimum frames to guarantee visual content (~30 seconds at 30fps)
MIN_FRAME_COUNT_VALIDATION = 900  # Validation threshold

# ============================================================
# COMMAND EXECUTION
# ============================================================

def run_command(cmd: list) -> None:
    """Execute command safely without shell injection."""
    subprocess.run(cmd, check=True)


# ============================================================
# VIDEO VALIDATION
# ============================================================

def validate_video(path: str) -> bool:
    """
    Validate video has visual stream with sufficient frames.
    
    Args:
        path: Path to video file
        
    Returns:
        True if video has valid visual stream, False otherwise
    """
    if not os.path.exists(path):
        return False
    
    if os.path.getsize(path) < 1024:
        return False
    
    # Use count_packets for more reliable frame counting
    cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        "-count_packets",
        "-show_entries", "stream=nb_read_packets,width,height",
        "-of", "json",
        path
    ]
    
    try:
        result = subprocess.check_output(cmd)
        data = json.loads(result)
        
        streams = data.get("streams", [])
        if not streams:
            return False
        
        s = streams[0]
        # Use nb_read_packets for accurate frame count
        nb_frames = int(s.get("nb_read_packets", 0))
        width = int(s.get("width", 0))
        height = int(s.get("height", 0))
        
        return (
            nb_frames >= MIN_FRAMES and
            width > 0 and
            height > 0
        )
    except Exception as e:
        print(f"[VIDEO_BUILDER] Validation error: {e}")
        return False


# ============================================================
# FALLBACK BACKGROUND GENERATION
# ============================================================

def generate_fallback(bg_out: str) -> None:
    """
    Generate fallback background when stock footage fails.
    Creates animated visual with text overlay.
    
    Args:
        bg_out: Output path for fallback video
    """
    cmd = [
        "ffmpeg",
        "-y",
        "-f", "lavfi",
        "-i", f"color=c=black:s=1080x1920:d={SAFE_DURATION}",
        "-vf", "drawtext=text='Money Machine AI':fontcolor=white:fontsize=52:x=(w-text_w)/2:y=(h-text_h)/2",
        "-pix_fmt", "yuv420p",
        bg_out
    ]
    run_command(cmd)


# ============================================================
# VIDEO ASSEMBLY
# ============================================================

def assemble(bg: str, audio: str, out: str) -> None:
    """
    Assemble final video from background and audio.
    Adds motion effects for engagement.
    
    Args:
        bg: Path to background video
        audio: Path to audio file
        out: Output path for final video
    """
    cmd = [
        "ffmpeg",
        "-y",
        "-stream_loop", "-1",
        "-i", bg,
        "-i", audio,
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-t", str(SAFE_DURATION),
        "-vf", "scale=1080:1920,format=yuv420p,zoompan=z='min(zoom+0.0005,1.08)':d=1",
        "-c:v", "libx264",
        "-profile:v", "high",
        "-level", "4.2",
        "-preset", "ultrafast",
        "-crf", "28",
        "-c:a", "aac",
        "-b:a", "128k",
        "-movflags", "+faststart",
        out
    ]
    run_command(cmd)


# ============================================================
# MASTER BUILD FUNCTION
# ============================================================

def build_video(bg: str, audio: str, out_dir: str) -> str:
    """
    Build final video with guaranteed visual content.
    
    This is the SINGLE SOURCE OF TRUTH for all video creation.
    ALL video paths must use this function.
    
    Args:
        bg: Path to background video
        audio: Path to audio file  
        out_dir: Output directory for final video
        
    Returns:
        Path to final validated video
        
    Raises:
        AssertionError: If video validation fails after assembly
    """
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f"final_{uuid.uuid4().hex}.mp4")
    
    # Check background video exists and is valid
    if not os.path.exists(bg) or os.path.getsize(bg) < 1024:
        print(f"[VIDEO_BUILDER] Background invalid, generating fallback...")
        fallback = os.path.join(out_dir, "fallback_bg.mp4")
        generate_fallback(fallback)
        bg = fallback
    
    # Assemble video
    print(f"[VIDEO_BUILDER] Assembling video: {out}")
    assemble(bg, audio, out)
    
    # Validate output
    if not validate_video(out):
        print(f"[VIDEO_BUILDER] ⚠️ First assembly failed validation, regenerating...")
        fallback = os.path.join(out_dir, "fallback_bg.mp4")
        generate_fallback(fallback)
        assemble(fallback, audio, out)
    
    # Final validation - MUST pass
    assert validate_video(out), "CRITICAL: video validation failed - visual stream missing"
    
    print(f"[VIDEO_BUILDER] ✅ Video validated: {out}")
    return out


# ============================================================
# LEGACY COMPATIBILITY
# ============================================================

def build(bg: str, audio: str, out_dir: str) -> str:
    """
    Legacy alias for build_video.
    Maintains backward compatibility.
    """
    return build_video(bg, audio, out_dir)


# ============================================================
# EXPORT
# ============================================================

__all__ = [
    "build_video",
    "build",
    "validate_video",
    "generate_fallback",
    "assemble"
]
