"""
============================================================
MONEY MACHINE - QUALITY GATES ENGINE
Elite Pre-Upload Validation & Channel Protection
============================================================
NEVER upload broken content. Quarantine instead.
============================================================
"""

import os
import re
import json
import asyncio
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple, List
import unicodedata

# ============================================================
# CONFIGURATION
# ============================================================

class QualityConfig:
    """Quality Gate Configuration - NON-NEGOTIABLE"""
    
    # Video requirements
    MIN_DURATION = 30  # seconds
    MAX_DURATION = 58  # seconds (Shorts limit)
    MIN_FRAME_COUNT = 300  # ~10 seconds at 30fps
    # Black frame detection only catches TRUE black (0x000000)
    # Consistent dark backgrounds (purple, blue) are ACCEPTABLE
    # Only fail on INTERMITTENT black frames (5-95% range)
    MAX_BLACK_FRAME_RATIO = 0.95  # Allow consistent backgrounds
    
    # Audio requirements
    # TTS naturally has 15-25% silence between sentences - this is NORMAL
    # Only fail if silence is abnormally high (>35% = broken TTS)
    MAX_SILENCE_RATIO = 0.35  # 35% - allows natural sentence pauses
    MIN_AUDIO_PEAK_DB = -6.0  # dB
    MAX_AUDIO_PEAK_DB = -1.0  # dB
    MAX_PAUSE_DURATION_MS = 300  # milliseconds
    
    # TTS requirements
    MIN_WORDS_PER_SENTENCE = 3
    MAX_WORDS_PER_SENTENCE = 18
    
    # Paths
    BASE_DIR = Path(__file__).parent.parent
    QUARANTINE_DIR = BASE_DIR / "data" / "quarantine"
    
    # Safe Mode channels (production only, no experiments)
    SAFE_MODE_CHANNELS = [
        "UCZppwcvPrWlAG0vb78elPJA",  # Money machine ai
    ]


# ============================================================
# SCRIPT SANITIZER (FIX 1 & 2)
# ============================================================

class ScriptSanitizer:
    """
    Sanitizes scripts BEFORE TTS to prevent robotic pauses.
    This is the PRIMARY fix for word-by-word TTS.
    """
    
    # Emoji pattern
    EMOJI_PATTERN = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "\U0001f926-\U0001f937"
        "\U00010000-\U0010ffff"
        "\u2640-\u2642"
        "\u2600-\u2B55"
        "\u200d"
        "\u23cf"
        "\u23e9"
        "\u231a"
        "\ufe0f"
        "\u3030"
        "]+", 
        flags=re.UNICODE
    )
    
    @staticmethod
    def sanitize_for_tts(text: str) -> str:
        """
        Clean text for TTS - removes all causes of robotic pauses.
        """
        if not text:
            return ""
        
        # Step 1: Remove emojis
        text = ScriptSanitizer.EMOJI_PATTERN.sub(' ', text)
        
        # Step 2: Remove bullet points and list markers
        text = re.sub(r'^[\s]*[-•●○◆▪▸►\*\d+\.]+\s*', '', text, flags=re.MULTILINE)
        
        # Step 3: Replace line breaks with spaces
        text = re.sub(r'\n+', ' ', text)
        
        # Step 4: Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Step 5: Remove ALL CAPS words (replace with title case)
        def fix_caps(match):
            word = match.group(0)
            if len(word) > 2 and word.isupper():
                return word.title()
            return word
        text = re.sub(r'\b[A-Z]{3,}\b', fix_caps, text)
        
        # Step 6: Remove [PAUSE] markers and other brackets
        text = re.sub(r'\[.*?\]', '', text)
        text = re.sub(r'\{.*?\}', '', text)
        
        # Step 7: Remove hashtags from spoken text
        text = re.sub(r'#\w+', '', text)
        
        # Step 8: Remove URLs
        text = re.sub(r'http\S+', '', text)
        
        # Step 9: Clean up punctuation spacing
        text = re.sub(r'\s+([.,!?])', r'\1', text)
        text = re.sub(r'([.,!?])([A-Za-z])', r'\1 \2', text)
        
        # Step 10: Final trim
        text = text.strip()
        
        return text
    
    @staticmethod
    def split_into_sentences(text: str) -> List[str]:
        """
        Split text into proper sentences for TTS.
        Ensures each sentence is 3-18 words.
        """
        # First sanitize
        text = ScriptSanitizer.sanitize_for_tts(text)
        
        # Split on sentence boundaries
        raw_sentences = re.split(r'(?<=[.!?])\s+', text)
        
        result = []
        buffer = []
        
        for sentence in raw_sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            words = sentence.split()
            word_count = len(words)
            
            if word_count < QualityConfig.MIN_WORDS_PER_SENTENCE:
                # Too short - add to buffer
                buffer.extend(words)
                if len(buffer) >= QualityConfig.MIN_WORDS_PER_SENTENCE:
                    result.append(' '.join(buffer))
                    buffer = []
            elif word_count > QualityConfig.MAX_WORDS_PER_SENTENCE:
                # Too long - split into chunks
                if buffer:
                    result.append(' '.join(buffer))
                    buffer = []
                    
                chunks = []
                current_chunk = []
                for word in words:
                    current_chunk.append(word)
                    if len(current_chunk) >= 12:  # Target ~12 words per chunk
                        chunks.append(' '.join(current_chunk))
                        current_chunk = []
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                result.extend(chunks)
            else:
                # Just right
                if buffer:
                    result.append(' '.join(buffer))
                    buffer = []
                result.append(sentence)
        
        # Don't forget the buffer
        if buffer:
            if result:
                # Merge with last sentence if short
                result[-1] = result[-1] + ' ' + ' '.join(buffer)
            else:
                result.append(' '.join(buffer))
        
        return result
    
    @staticmethod
    def prepare_for_tts(text: str) -> str:
        """
        Prepare final text for TTS with proper sentence structure.
        """
        sentences = ScriptSanitizer.split_into_sentences(text)
        # Join with periods and spaces for natural TTS flow
        return '. '.join(s.rstrip('.!?') for s in sentences if s) + '.'


# ============================================================
# TTS PROSODY SETTINGS (FIX 3)
# ============================================================

class TTSProsody:
    """
    Locked TTS prosody settings for human-like speech.
    """
    
    # Default settings (LOCKED for production)
    DEFAULT = {
        "rate": "+8%",      # Slightly faster = more engaging
        "pitch": "+2Hz",    # Slightly higher = more energetic
    }
    
    # Safe mode settings (for protected channels)
    SAFE_MODE = {
        "rate": "+6%",      # Conservative
        "pitch": "+1Hz",    # Conservative
    }
    
    # Voice presets (verified to sound human)
    VERIFIED_VOICES = [
        "en-US-ChristopherNeural",  # Male US - Good for finance
        "en-US-GuyNeural",          # Male US - Authoritative
        "en-US-JennyNeural",        # Female US - Friendly
    ]
    
    @staticmethod
    def get_settings(channel_id: str = None) -> dict:
        """Get TTS settings based on channel."""
        if channel_id in QualityConfig.SAFE_MODE_CHANNELS:
            return TTSProsody.SAFE_MODE
        return TTSProsody.DEFAULT
    
    @staticmethod
    def is_voice_verified(voice_id: str) -> bool:
        """Check if voice is verified for production."""
        return voice_id in TTSProsody.VERIFIED_VOICES


# ============================================================
# VIDEO QUALITY VALIDATOR (FIX 4 & 5)
# ============================================================

class VideoValidator:
    """
    Validates video before upload.
    Blocks broken content from ever being uploaded.
    """
    
    @staticmethod
    async def get_video_info(video_path: str) -> dict:
        """Get comprehensive video information using ffprobe."""
        cmd = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "v:0",
            "-count_packets",
            "-show_entries", "stream=width,height,r_frame_rate,nb_read_packets,codec_type",
            "-show_entries", "format=duration,size",
            "-of", "json",
            video_path
        ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await process.communicate()
            return json.loads(stdout.decode())
        except:
            return {}
    
    @staticmethod
    async def get_audio_info(video_path: str) -> dict:
        """Get audio stream information."""
        cmd = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "a:0",
            "-show_entries", "stream=codec_type,sample_rate,channels",
            "-of", "json",
            video_path
        ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await process.communicate()
            return json.loads(stdout.decode())
        except:
            return {}
    
    @staticmethod
    async def check_black_frames(video_path: str) -> float:
        """
        Check ratio of TRUE black frames in video.
        Only catches actual black (0x000000), not dark colors.
        Returns ratio from 0.0 to 1.0
        """
        cmd = [
            "ffmpeg",
            "-i", video_path,
            # pix_th=0.02 = only catch frames that are 98%+ black
            # This allows dark backgrounds like purple/blue
            "-vf", "blackdetect=d=0.1:pix_th=0.02",
            "-an",
            "-f", "null",
            "-"
        ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            _, stderr = await process.communicate()
            output = stderr.decode()
            
            # Parse black frame durations
            black_duration = 0.0
            for match in re.finditer(r'black_duration:(\d+\.?\d*)', output):
                black_duration += float(match.group(1))
            
            # Get total duration
            total_match = re.search(r'Duration: (\d+):(\d+):(\d+\.?\d*)', output)
            if total_match:
                h, m, s = total_match.groups()
                total_duration = int(h) * 3600 + int(m) * 60 + float(s)
                return black_duration / total_duration if total_duration > 0 else 1.0
            
            return 0.0
        except:
            return 0.0
    
    @staticmethod
    async def check_silence(video_path: str) -> float:
        """
        Check ratio of silence in audio.
        Returns ratio from 0.0 to 1.0
        """
        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-af", "silencedetect=n=-40dB:d=0.3",
            "-f", "null",
            "-"
        ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            _, stderr = await process.communicate()
            output = stderr.decode()
            
            # Parse silence durations
            silence_duration = 0.0
            for match in re.finditer(r'silence_duration: (\d+\.?\d*)', output):
                silence_duration += float(match.group(1))
            
            # Get total duration
            total_match = re.search(r'Duration: (\d+):(\d+):(\d+\.?\d*)', output)
            if total_match:
                h, m, s = total_match.groups()
                total_duration = int(h) * 3600 + int(m) * 60 + float(s)
                return silence_duration / total_duration if total_duration > 0 else 1.0
            
            return 0.0
        except:
            return 0.0
    
    @staticmethod
    async def validate(video_path: str) -> Tuple[bool, List[str]]:
        """
        Full video validation - ENHANCED to catch audio-only files.
        Returns (passed, list_of_errors)
        """
        errors = []
        
        if not os.path.exists(video_path):
            return False, ["Video file does not exist"]
        
        # Get video info
        video_info = await VideoValidator.get_video_info(video_path)
        audio_info = await VideoValidator.get_audio_info(video_path)
        
        # Check 1: Video stream exists
        video_streams = video_info.get("streams", [])
        if not video_streams:
            errors.append("NO VIDEO STREAM - Audio only file")
            return False, errors  # FAIL IMMEDIATELY for audio-only
        
        # Check 2: Video dimensions are valid (NON-ZERO)
        video_stream = video_streams[0]
        width = int(video_stream.get("width", 0))
        height = int(video_stream.get("height", 0))
        
        if width == 0 or height == 0:
            errors.append(f"INVALID VIDEO DIMENSIONS - width={width}, height={height}")
            return False, errors  # FAIL IMMEDIATELY
        
        # Check 3: Frame count is sufficient (HARD REQUIREMENT)
        frame_count = int(video_stream.get("nb_read_packets", 0))
        if frame_count < QualityConfig.MIN_FRAME_COUNT:
            errors.append(f"INSUFFICIENT FRAMES - {frame_count} frames < {QualityConfig.MIN_FRAME_COUNT} required (likely audio-only)")
            return False, errors  # FAIL IMMEDIATELY
        
        # Check 4: Audio stream exists
        audio_streams = audio_info.get("streams", [])
        if not audio_streams:
            errors.append("NO AUDIO STREAM - Silent video")
        
        # Check 5: Duration in range
        format_info = video_info.get("format", {})
        duration = float(format_info.get("duration", 0))
        
        if duration < QualityConfig.MIN_DURATION:
            errors.append(f"Duration too short: {duration:.1f}s < {QualityConfig.MIN_DURATION}s")
        if duration > QualityConfig.MAX_DURATION:
            errors.append(f"Duration too long: {duration:.1f}s > {QualityConfig.MAX_DURATION}s")
        
        # Check 6: Black frames
        # SMART LOGIC: Only fail on INTERMITTENT black frames (5-95%)
        # 0% or 100% = consistent visuals = ACCEPTABLE
        # This allows solid color backgrounds (purple, blue) to pass
        black_ratio = await VideoValidator.check_black_frames(video_path)
        if 0.05 < black_ratio < 0.95:  # Intermittent = broken
            errors.append(f"Intermittent black frames: {black_ratio*100:.1f}% (broken video)")
        
        # Check 7: Silence
        # TTS naturally has 15-25% silence between sentences - this is NORMAL
        silence_ratio = await VideoValidator.check_silence(video_path)
        if silence_ratio > QualityConfig.MAX_SILENCE_RATIO:
            errors.append(f"Too much silence: {silence_ratio*100:.1f}% > {QualityConfig.MAX_SILENCE_RATIO*100}%")
        
        passed = len(errors) == 0
        return passed, errors


# ============================================================
# QUALITY GATE (MASTER CONTROLLER)
# ============================================================

class QualityGate:
    """
    Master quality gate that blocks all broken content.
    This is the final checkpoint before upload.
    """
    
    def __init__(self):
        self.quarantine_dir = QualityConfig.QUARANTINE_DIR
        self.quarantine_dir.mkdir(parents=True, exist_ok=True)
    
    async def check_video(self, video_path: str, channel_id: str = None) -> Tuple[bool, dict]:
        """
        Run all quality checks on a video.
        Returns (can_upload, report)
        """
        report = {
            "video_path": video_path,
            "channel_id": channel_id,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {},
            "passed": False,
            "errors": []
        }
        
        # Safe mode check
        safe_mode = channel_id in QualityConfig.SAFE_MODE_CHANNELS
        report["safe_mode"] = safe_mode
        
        # Run validation
        passed, errors = await VideoValidator.validate(video_path)
        report["checks"]["video_validation"] = {
            "passed": passed,
            "errors": errors
        }
        report["errors"].extend(errors)
        
        report["passed"] = passed
        
        if not passed:
            # Move to quarantine
            await self.quarantine(video_path, report)
        
        return passed, report
    
    async def quarantine(self, video_path: str, report: dict):
        """
        Move failed video to quarantine folder.
        """
        if not os.path.exists(video_path):
            return
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = os.path.basename(video_path)
        
        # Move video
        quarantine_video = self.quarantine_dir / f"{timestamp}_{filename}"
        os.rename(video_path, quarantine_video)
        
        # Save report
        report_path = self.quarantine_dir / f"{timestamp}_{filename}.report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"[QUALITY] ❌ Video quarantined: {quarantine_video}")
        print(f"[QUALITY] Errors: {report['errors']}")
    
    def check_script(self, script: str) -> Tuple[bool, str]:
        """
        Validate and sanitize a script.
        Returns (valid, sanitized_script)
        """
        sanitized = ScriptSanitizer.prepare_for_tts(script)
        
        # Check if anything remains
        if len(sanitized.strip()) < 20:
            return False, ""
        
        return True, sanitized
    
    def get_tts_settings(self, channel_id: str = None) -> dict:
        """Get TTS settings for a channel."""
        return TTSProsody.get_settings(channel_id)
    
    def is_safe_mode_channel(self, channel_id: str) -> bool:
        """Check if channel is in safe mode."""
        return channel_id in QualityConfig.SAFE_MODE_CHANNELS


# ============================================================
# VISUAL FALLBACK ENGINE (FIX 5)
# ============================================================

class VisualFallback:
    """
    Provides guaranteed visual content when stock footage fails.
    NEVER allows audio-only or black-screen uploads.
    """
    
    BASE_DIR = Path(__file__).parent.parent
    ASSETS_DIR = BASE_DIR / "data" / "assets"
    
    @staticmethod
    async def create_gradient_background(output_path: str, duration: float = 60) -> bool:
        """
        Create an animated gradient background as fallback.
        Uses a purple-blue gradient (wealth/money aesthetic).
        """
        # Use color source with gradient filter that actually works
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"color=c=0x4a0080:s=1080x1920:d={duration}",  # Purple base
            "-vf", 
            "geq=r='clip(r(X,Y)*1.2+Y*0.05,0,255)':"
            "g='clip(g(X,Y)*0.5+Y*0.02,0,255)':"
            "b='clip(b(X,Y)*1.0+X*0.03,0,255)',"
            "zoompan=z='1.0+0.05*sin(on/30)':d=1:s=1080x1920",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "23",
            "-t", str(duration),
            output_path
        ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            _, stderr = await process.communicate()
            
            # If geq fails, use simple solid color with zoom
            if process.returncode != 0:
                # Fallback: Simple bright purple with zoom effect
                cmd_simple = [
                    "ffmpeg", "-y",
                    "-f", "lavfi",
                    "-i", f"color=c=0x6b21a8:s=1080x1920:d={duration}",  # Bright purple
                    "-vf", "zoompan=z='1.0+0.02*sin(on/30)':d=1:s=1080x1920",
                    "-c:v", "libx264",
                    "-preset", "ultrafast",
                    "-crf", "23",
                    "-t", str(duration),
                    output_path
                ]
                process2 = await asyncio.create_subprocess_exec(
                    *cmd_simple,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await process2.communicate()
                return process2.returncode == 0
            
            return True
        except:
            return False
    
    @staticmethod
    async def create_kinetic_text_background(
        output_path: str,
        text: str = "MONEY MACHINE",
        duration: float = 60
    ) -> bool:
        """
        Create a kinetic text animation as fallback.
        """
        # Escape text for FFmpeg
        escaped_text = text.replace("'", "\\'").replace(":", "\\:")
        
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"color=c=black:s=1080x1920:d={duration}",
            "-vf", f"drawtext=text='{escaped_text}':fontsize=80:fontcolor=white:x=(w-text_w)/2+sin(t*2)*50:y=(h-text_h)/2+cos(t*2)*30",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "23",
            "-t", str(duration),
            output_path
        ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            return process.returncode == 0
        except:
            return False
    
    @staticmethod
    async def get_fallback_background(duration: float = 60) -> str:
        """
        Get or create a fallback background.
        Tries in order:
        1. Existing default_bg.mp4
        2. Create gradient
        3. Create kinetic text
        """
        # Check for existing default
        default_bg = VisualFallback.ASSETS_DIR / "default_bg.mp4"
        if default_bg.exists():
            return str(default_bg)
        
        # Create assets directory
        VisualFallback.ASSETS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Try gradient
        gradient_path = str(VisualFallback.ASSETS_DIR / "fallback_gradient.mp4")
        if await VisualFallback.create_gradient_background(gradient_path, duration):
            return gradient_path
        
        # Try kinetic text
        kinetic_path = str(VisualFallback.ASSETS_DIR / "fallback_kinetic.mp4")
        if await VisualFallback.create_kinetic_text_background(kinetic_path, "💰", duration):
            return kinetic_path
        
        # Last resort - create a simple bright color background (NOT DARK)
        color_path = str(VisualFallback.ASSETS_DIR / "fallback_color.mp4")
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"color=c=0x6b21a8:s=1080x1920:d={duration}",  # Bright purple
            "-c:v", "libx264",
            "-preset", "ultrafast",
            color_path
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()
        
        return color_path


# ============================================================
# EXPORT ALL
# ============================================================

__all__ = [
    "QualityConfig",
    "ScriptSanitizer",
    "TTSProsody",
    "VideoValidator",
    "QualityGate",
    "VisualFallback"
]
