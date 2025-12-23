"""
============================================================
ELITE VISUAL GUARANTEE - GLOBAL VIDEO BUILDER
The Single Source of Truth for All Video Creation
============================================================
Zero chance of audio-only Shorts across all paths:
- Local runs, Railway, n8n, all APIs
- YouTube, TikTok, Instagram, all platforms
- All creators (TTS, NotebookLM, Veo, CapCut replacements)
============================================================
"""

import subprocess
import os
import json
import uuid

# ============================================================
# CONFIGURATION
# ============================================================

SAFE_DURATION = 58  # Max Shorts duration
MIN_FRAMES = 900    # Minimum frames to ensure video stream exists
DEFAULT_FPS = 30.0  # Default frame rate when unable to determine from metadata
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920

# Visual enhancement settings
ZOOM_INCREMENT = 0.0005  # Subtle zoom rate for engagement
ZOOM_MAX = 1.08          # Maximum zoom level

# Configurable branding - sanitize to prevent injection
_raw_fallback_text = os.getenv("VIDEO_FALLBACK_TEXT", "Money Machine AI")
# Remove potentially dangerous characters for FFmpeg filter
FALLBACK_TEXT = ''.join(c for c in _raw_fallback_text if c.isalnum() or c in ' -_.')[:50]

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def run(cmd: list):
    """Execute command as list and check for errors."""
    try:
        result = subprocess.run(cmd, check=True, capture_output=True)
        return result
    except subprocess.CalledProcessError as e:
        # Log error details for debugging
        error_msg = e.stderr.decode() if e.stderr else "No error details"
        print(f"[VIDEO_BUILDER] Command failed: {' '.join(cmd[:3])}...")
        print(f"[VIDEO_BUILDER] Error: {error_msg[:200]}")
        raise


def validate_video(path: str) -> bool:
    """
    Validate that a video file has a proper video stream with frames.
    Returns True if video is valid, False otherwise.
    
    Checks:
    - Video stream exists
    - Has minimum number of frames
    - Has valid dimensions (width > 0, height > 0)
    """
    if not os.path.exists(path):
        print(f"[VIDEO_BUILDER] ❌ File does not exist: {path}")
        return False
    
    if os.path.getsize(path) < 1024:
        print(f"[VIDEO_BUILDER] ❌ File too small: {path}")
        return False
    
    cmd = [
        "ffprobe", "-v", "error", "-select_streams", "v",
        "-show_entries", "stream=nb_frames,width,height,r_frame_rate:format=duration",
        "-of", "json", path
    ]
    
    try:
        # Use stderr=DEVNULL to avoid mixing error output with JSON
        result = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
        data = json.loads(result)
        
        streams = data.get("streams", [])
        if not streams:
            print(f"[VIDEO_BUILDER] ❌ No video stream found in: {path}")
            return False
        
        s = streams[0]
        # Handle nb_frames safely - may not be present or could be invalid
        # If unavailable, we'll use duration-based validation as fallback
        try:
            nb_frames = int(s.get("nb_frames", 0))
        except (ValueError, TypeError):
            nb_frames = 0
        
        width = int(s.get("width", 0))
        height = int(s.get("height", 0))
        
        if width <= 0 or height <= 0:
            print(f"[VIDEO_BUILDER] ❌ Invalid dimensions: {width}x{height}")
            return False
        
        # Validate frame count - use duration as fallback
        if nb_frames > 0:
            # Direct frame count available
            if nb_frames < MIN_FRAMES:
                print(f"[VIDEO_BUILDER] ❌ Frame count too low: {nb_frames} < {MIN_FRAMES}")
                return False
            print(f"[VIDEO_BUILDER] ✅ Valid video: {nb_frames} frames, {width}x{height}")
        else:
            # Frame count unavailable - estimate from duration
            format_info = data.get("format", {})
            try:
                duration = float(format_info.get("duration", 0))
            except (ValueError, TypeError):
                print(f"[VIDEO_BUILDER] ❌ Unable to determine video duration")
                return False
            
            # Parse frame rate (e.g., "30/1" or "25/1")
            fps_str = s.get("r_frame_rate", f"{DEFAULT_FPS}/1")
            try:
                # Ensure fps_str is a string before splitting
                if not isinstance(fps_str, str) or '/' not in fps_str:
                    raise ValueError("Invalid FPS format")
                num, denom = fps_str.split('/')
                fps = float(num) / float(denom)
                if fps <= 0:
                    raise ValueError("Invalid FPS value")
            except (ValueError, ZeroDivisionError, AttributeError, TypeError):
                fps = DEFAULT_FPS
            
            # Estimate minimum duration needed for MIN_FRAMES
            min_duration = MIN_FRAMES / fps
            
            if duration < min_duration:
                print(f"[VIDEO_BUILDER] ❌ Duration too short: {duration:.1f}s < {min_duration:.1f}s (estimated from {MIN_FRAMES} frames @ {fps}fps)")
                return False
            
            print(f"[VIDEO_BUILDER] ✅ Valid video: {width}x{height}, {duration:.1f}s @ {fps}fps")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"[VIDEO_BUILDER] ❌ ffprobe failed: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"[VIDEO_BUILDER] ❌ JSON parse error: {e}")
        return False
    except Exception as e:
        print(f"[VIDEO_BUILDER] ❌ Validation error: {e}")
        return False


def generate_fallback(bg_out: str, duration: int = SAFE_DURATION):
    """
    Generate a fallback video background with branding.
    Used when stock footage fails or is unavailable.
    
    Creates a black background with centered white text.
    """
    print(f"[VIDEO_BUILDER] 🎨 Generating fallback background...")
    
    # Escape text for FFmpeg filter - escape single quotes, colons, backslashes
    # by replacing them with safe alternatives
    safe_text = FALLBACK_TEXT.replace("'", "").replace(":", "").replace("\\", "")
    
    cmd = [
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", f"color=c=black:s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:d={duration}",
        "-vf", f"drawtext=text='{safe_text}':fontcolor=white:fontsize=52:x=(w-text_w)/2:y=(h-text_h)/2",
        "-pix_fmt", "yuv420p", bg_out
    ]
    
    try:
        run(cmd)
        print(f"[VIDEO_BUILDER] ✅ Fallback generated: {bg_out}")
    except subprocess.CalledProcessError as e:
        print(f"[VIDEO_BUILDER] ❌ Fallback generation failed: {e}")
        raise


def assemble(bg: str, audio: str, out: str, duration: int = SAFE_DURATION):
    """
    Assemble final video from background and audio.
    
    Features:
    - Loops background to match audio length
    - Scales to vertical format (1080x1920)
    - Adds subtle zoom/pan for engagement
    - Optimized encoding for fast processing
    - Ensures YouTube compliance
    """
    print(f"[VIDEO_BUILDER] 🎬 Assembling video...")
    print(f"[VIDEO_BUILDER]   Background: {bg}")
    print(f"[VIDEO_BUILDER]   Audio: {audio}")
    print(f"[VIDEO_BUILDER]   Output: {out}")
    
    cmd = [
        "ffmpeg", "-y", "-stream_loop", "-1", "-i", bg, "-i", audio,
        "-map", "0:v:0", "-map", "1:a:0",
        "-t", str(duration),
        "-vf", f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT},format=yuv420p,zoompan=z='min(zoom+{ZOOM_INCREMENT},{ZOOM_MAX})':d=1",
        "-c:v", "libx264", "-profile:v", "high", "-level", "4.2",
        "-preset", "ultrafast", "-crf", "28",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart", out
    ]
    
    try:
        run(cmd)
        print(f"[VIDEO_BUILDER] ✅ Video assembled: {out}")
    except subprocess.CalledProcessError as e:
        print(f"[VIDEO_BUILDER] ❌ Assembly failed: {e}")
        raise


def build_video(bg: str, audio: str, out_dir: str) -> str:
    """
    Build a complete, validated video from background and audio.
    This is the ONLY approved way to create videos.
    
    Features:
    - Automatic fallback if background is missing/invalid
    - Validates output before returning
    - Retries with fallback if first attempt fails validation
    - Guarantees valid video or raises exception
    
    Args:
        bg: Path to background video
        audio: Path to audio file
        out_dir: Output directory for final video
    
    Returns:
        Path to validated final video
    
    Raises:
        AssertionError: If video validation fails after all retries
    """
    # Ensure output directory exists
    os.makedirs(out_dir, exist_ok=True)
    
    # Generate unique output filename
    out = os.path.join(out_dir, f"final_{uuid.uuid4().hex}.mp4")
    
    print(f"[VIDEO_BUILDER] 🚀 Building video...")
    print(f"[VIDEO_BUILDER]   Target: {out}")
    
    # Check if background exists and is valid
    if not os.path.exists(bg) or os.path.getsize(bg) < 1024:
        print(f"[VIDEO_BUILDER] ⚠️ Background missing or too small, using fallback")
        fallback = os.path.join(out_dir, "fallback_bg.mp4")
        generate_fallback(fallback)
        bg = fallback
    
    # First attempt: assemble with provided/fallback background
    try:
        assemble(bg, audio, out)
    except Exception as e:
        print(f"[VIDEO_BUILDER] ⚠️ First assembly attempt failed: {e}")
    
    # Validate the output
    if not validate_video(out):
        print(f"[VIDEO_BUILDER] ⚠️ First attempt failed validation, retrying with fallback")
        
        # Retry with guaranteed fallback
        fallback = os.path.join(out_dir, "fallback_bg.mp4")
        generate_fallback(fallback)
        assemble(fallback, audio, out)
        
        # Final validation
        if not validate_video(out):
            raise AssertionError(
                f"CRITICAL: Video validation failed after all retries. "
                f"Output: {out}"
            )
    
    print(f"[VIDEO_BUILDER] ✅ Video build complete and validated")
    return out


# ============================================================
# EXPORT
# ============================================================

__all__ = [
    "validate_video",
    "generate_fallback",
    "assemble",
    "build_video",
]
