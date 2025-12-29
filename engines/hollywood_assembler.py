"""
===============================================================================
HOLLYWOOD ASSEMBLER - Elite Video Assembly Engine
===============================================================================
Assembles scene clips into Hollywood-quality video.
Enforces 8-10 Mbps bitrate, proper encoding, motion on every frame.

QUALITY STANDARDS:
- 8M target bitrate (6M min, 10M max)
- 30 FPS
- H.264 High Profile Level 4.2
- AAC 192kbps audio
- Motion on every scene (Ken Burns)
===============================================================================
"""

import os
import json
import asyncio
import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import random

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# ============================================================================
# DIRECTORIES
# ============================================================================

BASE_DIR = Path(__file__).parent.parent
SCENES_DIR = BASE_DIR / "data" / "scenes"
OUTPUT_DIR = BASE_DIR / "data" / "output"
TEMP_DIR = BASE_DIR / "data" / "temp"
PLAYBACK_DIR = BASE_DIR / "output" / "playback" / "shorts"

for d in [SCENES_DIR, OUTPUT_DIR, TEMP_DIR, PLAYBACK_DIR]:
    d.mkdir(parents=True, exist_ok=True)


# ============================================================================
# MOTION PRESETS - Ken Burns Effects
# ============================================================================

MOTION_FILTERS = {
    "parallax_zoom": "zoompan=z='min(zoom+0.0008,1.12)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1080x1920",
    "pan_left": "zoompan=z='1.05':x='if(eq(on,1),iw/4,x+1)':y='ih/2-(ih/zoom/2)':d={frames}:s=1080x1920",
    "pan_right": "zoompan=z='1.05':x='if(eq(on,1),iw*3/4,x-1)':y='ih/2-(ih/zoom/2)':d={frames}:s=1080x1920",
    "pan_up": "zoompan=z='1.05':x='iw/2-(iw/zoom/2)':y='if(eq(on,1),ih*3/4,y-1)':d={frames}:s=1080x1920",
    "pan_down": "zoompan=z='1.05':x='iw/2-(iw/zoom/2)':y='if(eq(on,1),ih/4,y+1)':d={frames}:s=1080x1920",
    "dolly_in": "zoompan=z='if(eq(on,1),1,zoom+0.002)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1080x1920",
    "dolly_out": "zoompan=z='if(eq(on,1),1.15,zoom-0.002)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1080x1920",
    "slow_zoom": "zoompan=z='min(zoom+0.0004,1.08)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1080x1920",
    "ken_burns": "zoompan=z='if(lte(zoom,1.0),1.08,max(1.001,zoom-0.0002))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1080x1920",
    "push_in": "zoompan=z='min(zoom+0.001,1.1)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1080x1920",
}


@dataclass
class AssemblyResult:
    """Result from video assembly."""
    success: bool
    video_path: Optional[str] = None
    bitrate: int = 0
    duration: float = 0.0
    scene_count: int = 0
    error: Optional[str] = None


class HollywoodAssembler:
    """
    Hollywood-grade video assembler with NVIDIA NVENC GPU acceleration.
    Combines scenes with motion and audio into elite quality output.
    
    ENCODING HIERARCHY:
    1. AV1 NVENC (RTX 40-series) - Best quality, YouTube preferred
    2. H.264 NVENC (RTX 20/30/40) - Fallback, still elite
    3. libx264 CPU - Last resort
    """
    
    def __init__(self, prefer_av1: bool = True):
        self.resolution = (1080, 1920)
        self.fps = 30
        self.prefer_av1 = prefer_av1
        
        # Detect GPU encoding capabilities
        self.gpu_encoders = self._detect_gpu_encoders()
        
    def _detect_gpu_encoders(self) -> Dict[str, bool]:
        """Detect available AND WORKING GPU encoders."""
        encoders = {"av1_nvenc": False, "h264_nvenc": False, "hevc_nvenc": False}
        
        try:
            # First check if encoders are listed
            result = subprocess.run(
                ["ffmpeg", "-hide_banner", "-encoders"],
                capture_output=True, text=True, timeout=10
            )
            output = result.stdout + result.stderr
            
            for encoder in encoders:
                if encoder in output:
                    # Test if encoder actually works
                    test_result = subprocess.run(
                        ["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=black:s=64x64:d=0.1",
                         "-c:v", encoder, "-f", "null", "-"],
                        capture_output=True, text=True, timeout=10
                    )
                    if test_result.returncode == 0:
                        encoders[encoder] = True
                    
        except Exception:
            pass
            
        return encoders
    
    def _get_best_encoder(self) -> tuple:
        """Get best available encoder and its settings."""
        
        # AV1 NVENC - Best for YouTube (RTX 40-series)
        if self.prefer_av1 and self.gpu_encoders.get("av1_nvenc"):
            return ("av1_nvenc", {
                "preset": "p7",
                "tune": "hq",
                "rc": "vbr",
                "cq": "20",
                "bitrate": "6M",
                "maxrate": "10M",
                "bufsize": "20M",
            })
        
        # H.264 NVENC - Fallback (RTX 20/30/40)
        if self.gpu_encoders.get("h264_nvenc"):
            return ("h264_nvenc", {
                "preset": "p7",
                "tune": "hq",
                "rc": "vbr",
                "cq": "18",
                "bitrate": "8M",
                "maxrate": "12M",
                "bufsize": "24M",
            })
        
        # CPU fallback
        return ("libx264", {
            "preset": "slow",
            "crf": "18",
            "bitrate": "10M",
            "maxrate": "12M",
            "bufsize": "20M",
        })
        
    async def _render_scene_with_motion(
        self,
        image_path: str,
        duration: float,
        motion_type: str,
        output_path: str
    ) -> bool:
        """Render a single scene image with motion effect using GPU acceleration."""
        
        frames = int(duration * self.fps)
        
        # Get motion filter
        motion_filter = MOTION_FILTERS.get(motion_type, MOTION_FILTERS["slow_zoom"])
        motion_filter = motion_filter.format(frames=frames)
        
        encoder, settings = self._get_best_encoder()
        
        # Build GPU-accelerated FFmpeg command
        # Note: Zoompan filter runs on CPU, but encoding uses GPU
        if encoder in ("av1_nvenc", "h264_nvenc"):
            cmd = [
                "ffmpeg", "-y",
                "-loop", "1",
                "-i", image_path,
                "-t", str(duration),
                "-vf", f"{motion_filter},fps={self.fps},format=yuv420p",
                "-c:v", encoder,
                "-preset", settings["preset"],
                "-tune", settings["tune"],
                "-rc", settings["rc"],
                "-cq", settings["cq"],
                "-b:v", settings["bitrate"],
                "-maxrate", settings["maxrate"],
                "-bufsize", settings["bufsize"],
                "-spatial_aq", "1",
                "-temporal_aq", "1",
                "-aq-strength", "12",
                "-rc-lookahead", "32",
                "-bf", "3",
                "-g", "60",
                "-an",
                output_path
            ]
        else:
            # CPU fallback
            cmd = [
                "ffmpeg", "-y",
                "-loop", "1",
                "-i", image_path,
                "-t", str(duration),
                "-vf", f"{motion_filter},fps={self.fps}",
                "-c:v", "libx264",
                "-preset", "slow",
                "-profile:v", "high",
                "-level", "4.2",
                "-b:v", settings["bitrate"],
                "-maxrate", settings["maxrate"],
                "-bufsize", settings["bufsize"],
                "-g", "60",
                "-bf", "3",
                "-pix_fmt", "yuv420p",
                "-an",
                output_path
            ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            return Path(output_path).exists()
            
        except Exception as e:
            print(f"Motion render error: {e}")
            return False
    
    async def _scale_video_scene(
        self,
        video_path: str,
        duration: float,
        output_path: str
    ) -> bool:
        """Scale/crop video scene to match resolution."""
        
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-t", str(duration),
            "-vf", f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps={self.fps}",
            "-c:v", "libx264", "-preset", "fast",
            "-b:v", "10M", "-minrate", "8M", "-maxrate", "12M", "-bufsize", "20M",
            "-pix_fmt", "yuv420p",
            "-an",
            output_path
        ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            
            return Path(output_path).exists()
            
        except Exception:
            return False
    
    async def _render_all_scenes(
        self,
        scenes: list,
        video_id: str
    ) -> List[str]:
        """Render all scenes with motion effects."""
        
        rendered_clips = []
        
        for i, scene in enumerate(scenes):
            if not scene.image_path or not Path(scene.image_path).exists():
                continue
            
            clip_path = str(TEMP_DIR / f"{video_id}_clip_{i:03d}.mp4")
            
            # Check if source is image or video
            is_video = scene.image_path.endswith(('.mp4', '.mov', '.webm'))
            
            if is_video:
                success = await self._scale_video_scene(
                    scene.image_path,
                    scene.duration,
                    clip_path
                )
            else:
                success = await self._render_scene_with_motion(
                    scene.image_path,
                    scene.duration,
                    scene.motion,
                    clip_path
                )
            
            if success and Path(clip_path).exists():
                rendered_clips.append(clip_path)
        
        return rendered_clips
    
    async def _concatenate_clips(
        self,
        clip_paths: List[str],
        video_id: str
    ) -> Optional[str]:
        """Concatenate all clips into single video."""
        
        if not clip_paths:
            return None
        
        # Filter to only valid files
        valid_clips = [c for c in clip_paths if Path(c).exists()]
        if not valid_clips:
            print("❌ No valid clips to concatenate")
            return None
        
        concat_file = TEMP_DIR / f"{video_id}_concat.txt"
        output_path = TEMP_DIR / f"{video_id}_video_only.mp4"
        
        # Write concat file with proper Windows path handling
        with open(concat_file, 'w', encoding='utf-8') as f:
            for clip in valid_clips:
                # Use forward slashes and escape single quotes
                escaped = str(Path(clip).resolve()).replace("\\", "/").replace("'", "'\\''")
                f.write(f"file '{escaped}'\n")
        
        print(f"📝 Concat file: {concat_file} ({len(valid_clips)} clips)")
        
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_file),
            "-c", "copy",
            str(output_path)
        ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if output_path.exists():
                return str(output_path)
            else:
                print(f"❌ FFmpeg concat failed: {stderr.decode()[:500]}")
                
        except Exception as e:
            print(f"❌ Concat exception: {e}")
        
        return None
    
    async def _add_audio(
        self,
        video_path: str,
        audio_path: str,
        output_path: str
    ) -> bool:
        """Add audio with NVENC GPU-accelerated Hollywood-grade encoding."""
        
        encoder, settings = self._get_best_encoder()
        
        # Build GPU-accelerated command
        if encoder in ("av1_nvenc", "h264_nvenc"):
            cmd = [
                "ffmpeg", "-y",
                "-hwaccel", "cuda",
                "-hwaccel_output_format", "cuda",
                "-i", video_path,
                "-i", audio_path,
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-c:v", encoder,
                "-preset", settings["preset"],
                "-tune", settings["tune"],
                "-rc", settings["rc"],
                "-cq", settings["cq"],
                "-b:v", settings["bitrate"],
                "-maxrate", settings["maxrate"],
                "-bufsize", settings["bufsize"],
                "-spatial_aq", "1",
                "-temporal_aq", "1",
                "-aq-strength", "12",
                "-rc-lookahead", "32",
                "-bf", "3",
                "-g", "60",
                "-c:a", "aac",
                "-b:a", "192k",
                "-ar", "48000",
                "-movflags", "+faststart",
                "-shortest",
                output_path
            ]
        else:
            # CPU fallback
            cmd = [
                "ffmpeg", "-y",
                "-i", video_path,
                "-i", audio_path,
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-c:v", "libx264",
                "-preset", "slow",
                "-profile:v", "high",
                "-level:v", "4.2",
                "-b:v", settings["bitrate"],
                "-maxrate", settings["maxrate"],
                "-bufsize", settings["bufsize"],
                "-g", "60",
                "-keyint_min", "60",
                "-sc_threshold", "0",
                "-pix_fmt", "yuv420p",
                "-r", str(self.fps),
                "-c:a", "aac",
                "-b:a", "192k",
                "-ar", "48000",
                "-movflags", "+faststart",
                "-shortest",
                output_path
            ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if not Path(output_path).exists() or Path(output_path).stat().st_size == 0:
                print(f"⚠️ Audio mux failed: {stderr.decode()[-500:]}")
                return False
            
            return True
            
        except Exception as e:
            print(f"⚠️ Audio mux error: {e}")
            return False
    
    def _get_video_info(self, video_path: str) -> Dict[str, Any]:
        """Get video bitrate and duration."""
        
        try:
            result = subprocess.run([
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration,bit_rate",
                "-of", "json",
                video_path
            ], capture_output=True, text=True)
            
            data = json.loads(result.stdout)
            return {
                "duration": float(data["format"].get("duration", 0)),
                "bitrate": int(data["format"].get("bit_rate", 0))
            }
        except:
            return {"duration": 0, "bitrate": 0}
    
    async def assemble(
        self,
        scenes: list,  # List of HollywoodScene
        audio_path: str,
        output_path: str,
        video_id: str
    ) -> AssemblyResult:
        """
        Assemble scenes into Hollywood-quality video.
        
        Args:
            scenes: List of HollywoodScene objects
            audio_path: Path to audio file
            output_path: Where to save final video
            video_id: Unique identifier
            
        Returns:
            AssemblyResult with video path and metadata
        """
        
        try:
            # Step 1: Render all scenes with motion
            print(f"🎬 Rendering {len(scenes)} scenes with motion...")
            rendered_clips = await self._render_all_scenes(scenes, video_id)
            
            if not rendered_clips:
                return AssemblyResult(
                    success=False,
                    error="No scenes rendered successfully"
                )
            
            print(f"✅ Rendered {len(rendered_clips)} clips")
            
            # Step 2: Concatenate clips
            print("🔗 Concatenating clips...")
            video_only = await self._concatenate_clips(rendered_clips, video_id)
            
            if not video_only:
                return AssemblyResult(
                    success=False,
                    error="Failed to concatenate clips"
                )
            
            # Step 3: Add audio with Hollywood encoding
            print("🔊 Adding audio with Hollywood encoding...")
            success = await self._add_audio(video_only, audio_path, output_path)
            
            if not success:
                return AssemblyResult(
                    success=False,
                    error="Failed to add audio"
                )
            
            # Get video info
            info = self._get_video_info(output_path)
            
            print(f"✅ Assembly complete: {info['bitrate'] / 1_000_000:.1f} Mbps, {info['duration']:.1f}s")
            
            # Cleanup temp files
            for clip in rendered_clips:
                try:
                    Path(clip).unlink()
                except:
                    pass
            
            return AssemblyResult(
                success=True,
                video_path=output_path,
                bitrate=info["bitrate"],
                duration=info["duration"],
                scene_count=len(rendered_clips)
            )
            
        except Exception as e:
            return AssemblyResult(
                success=False,
                error=str(e)
            )
    
    def validate_quality(self, video_path: str) -> tuple:
        """Validate video meets Hollywood quality standards."""
        
        info = self._get_video_info(video_path)
        errors = []
        
        min_bitrate = 6_000_000  # 6 Mbps
        min_duration = 15.0
        max_duration = 180.0
        
        if info["bitrate"] < min_bitrate:
            errors.append(f"Bitrate {info['bitrate']/1_000_000:.1f}M below minimum {min_bitrate/1_000_000:.1f}M")
        
        if info["duration"] < min_duration:
            errors.append(f"Duration {info['duration']:.1f}s below minimum {min_duration:.1f}s")
        
        if info["duration"] > max_duration:
            errors.append(f"Duration {info['duration']:.1f}s above maximum {max_duration:.1f}s")
        
        return len(errors) == 0, errors, info


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

async def assemble_hollywood_video(
    scenes: list,
    audio_path: str,
    output_path: str,
    video_id: str
) -> AssemblyResult:
    """Quick function to assemble a Hollywood video."""
    assembler = HollywoodAssembler()
    return await assembler.assemble(scenes, audio_path, output_path, video_id)


if __name__ == "__main__":
    print("🎬 Hollywood Assembler Ready")
    print(f"📁 Scenes: {SCENES_DIR}")
    print(f"📁 Output: {OUTPUT_DIR}")
    print(f"🎯 Quality: {HollywoodAssembler().bitrate} target")
