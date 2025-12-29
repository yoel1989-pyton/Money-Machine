"""
===============================================================================
SCENE STITCHER - Multi-Scene Video Assembly Engine
===============================================================================
Stitches multiple scene images/videos into a single cinematic video.
Adds motion (Ken Burns), transitions, and audio synchronization.

This is the Hollywood secret: NOT one background, but 10-25 unique scenes.
===============================================================================
"""

import os
import json
import asyncio
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import random

# Directories
TEMP_DIR = Path(__file__).parent.parent / "data" / "temp"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "output"

TEMP_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class SceneSpec:
    """Specification for a single scene."""
    index: int
    image_path: str
    duration: float
    start_time: float
    end_time: float
    text: str
    motion_type: str = "zoom_in"  # zoom_in, zoom_out, pan_left, pan_right, pan_up, ken_burns
    transition: str = "cut"  # cut, fade, crossfade


@dataclass
class StitchResult:
    """Result of video stitching."""
    video_path: str
    success: bool
    scene_count: int
    total_duration: float
    unique_visuals: int
    error: Optional[str] = None


# Motion presets (Ken Burns variations)
MOTION_PRESETS = {
    "zoom_in": {
        "start_scale": 1.0,
        "end_scale": 1.15,
        "start_x": 0.5,
        "end_x": 0.5,
        "start_y": 0.5,
        "end_y": 0.5
    },
    "zoom_out": {
        "start_scale": 1.15,
        "end_scale": 1.0,
        "start_x": 0.5,
        "end_x": 0.5,
        "start_y": 0.5,
        "end_y": 0.5
    },
    "pan_left": {
        "start_scale": 1.2,
        "end_scale": 1.2,
        "start_x": 0.7,
        "end_x": 0.3,
        "start_y": 0.5,
        "end_y": 0.5
    },
    "pan_right": {
        "start_scale": 1.2,
        "end_scale": 1.2,
        "start_x": 0.3,
        "end_x": 0.7,
        "start_y": 0.5,
        "end_y": 0.5
    },
    "pan_up": {
        "start_scale": 1.2,
        "end_scale": 1.2,
        "start_x": 0.5,
        "end_x": 0.5,
        "start_y": 0.6,
        "end_y": 0.4
    },
    "ken_burns": {
        "start_scale": 1.0,
        "end_scale": 1.2,
        "start_x": 0.4,
        "end_x": 0.6,
        "start_y": 0.4,
        "end_y": 0.6
    }
}


class SceneStitcher:
    """
    Multi-scene video assembly engine.
    Combines scene images with motion into Hollywood-quality video.
    """
    
    def __init__(self, temp_dir: str = None):
        self.temp_dir = Path(temp_dir) if temp_dir else TEMP_DIR
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Quality settings (Hollywood standard)
        self.resolution = (1080, 1920)  # 9:16 vertical
        self.fps = 30
        self.bitrate = "8M"
        self.min_bitrate = "6M"
        self.max_bitrate = "10M"
    
    def _get_audio_duration(self, audio_path: str) -> float:
        """Get audio file duration."""
        try:
            result = subprocess.run([
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "json", audio_path
            ], capture_output=True, text=True)
            return float(json.loads(result.stdout)["format"]["duration"])
        except:
            return 60.0
    
    def _assign_scene_timings(
        self, 
        scene_images: List[str], 
        audio_duration: float,
        min_duration: float = 1.5,
        max_duration: float = 3.0
    ) -> List[SceneSpec]:
        """Assign timing and motion to each scene."""
        
        n_scenes = len(scene_images)
        if n_scenes == 0:
            return []
        
        # Calculate base duration per scene
        base_duration = audio_duration / n_scenes
        
        # Clamp to min/max range
        base_duration = max(min_duration, min(max_duration, base_duration))
        
        # Recalculate number of scenes that fit
        n_usable = int(audio_duration / base_duration)
        n_usable = min(n_usable, n_scenes)
        
        scenes = []
        current_time = 0.0
        motion_types = list(MOTION_PRESETS.keys())
        
        for i in range(n_usable):
            # Vary duration slightly for natural rhythm
            duration = base_duration * random.uniform(0.85, 1.15)
            
            # Don't exceed audio length
            if current_time + duration > audio_duration:
                duration = audio_duration - current_time
            
            if duration < 0.5:
                break
            
            scenes.append(SceneSpec(
                index=i,
                image_path=scene_images[i % len(scene_images)],
                duration=duration,
                start_time=current_time,
                end_time=current_time + duration,
                text="",
                motion_type=random.choice(motion_types),
                transition="cut" if i == 0 else random.choice(["cut", "cut", "fade"])
            ))
            
            current_time += duration
        
        return scenes
    
    async def _render_scene_with_motion(
        self, 
        scene: SceneSpec, 
        video_id: str
    ) -> Optional[str]:
        """Render a single scene with Ken Burns motion effect."""
        
        output_path = self.temp_dir / f"{video_id}_motion_{scene.index:03d}.mp4"
        
        if not Path(scene.image_path).exists():
            return None
        
        preset = MOTION_PRESETS.get(scene.motion_type, MOTION_PRESETS["zoom_in"])
        
        # Calculate zoompan parameters
        duration_frames = int(scene.duration * self.fps)
        
        # Zoompan filter for Ken Burns effect
        # The filter interpolates zoom and position over the duration
        start_zoom = preset["start_scale"]
        end_zoom = preset["end_scale"]
        
        # Calculate zoom per frame (expressed as multiplier of initial zoom)
        zoom_expr = f"'min(max(zoom+{(end_zoom - start_zoom) / duration_frames},1),2)'"
        
        # Position expressions (ih = input height, iw = input width)
        start_x = preset["start_x"]
        end_x = preset["end_x"]
        start_y = preset["start_y"]
        end_y = preset["end_y"]
        
        # Build filter complex
        filter_complex = (
            f"scale=8000:-1,"  # Scale up for smooth zoom
            f"zoompan=z={zoom_expr}:x='iw*{start_x}-(iw/zoom/2)':y='ih*{start_y}-(ih/zoom/2)':"
            f"d={duration_frames}:s={self.resolution[0]}x{self.resolution[1]}:fps={self.fps},"
            f"setsar=1,format=yuv420p"
        )
        
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", scene.image_path,
            "-t", str(scene.duration),
            "-vf", filter_complex,
            "-c:v", "libx264", "-preset", "fast",
            "-b:v", "10M", "-minrate", "8M", "-maxrate", "12M", "-bufsize", "20M",
            "-pix_fmt", "yuv420p",
            "-an",
            str(output_path)
        ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            _, stderr = await process.communicate()
            
            if output_path.exists() and output_path.stat().st_size > 1000:
                return str(output_path)
            else:
                # Fallback: simple loop without complex motion
                return await self._render_scene_simple(scene, video_id)
                
        except Exception as e:
            print(f"Motion render failed for scene {scene.index}: {e}")
            return await self._render_scene_simple(scene, video_id)
    
    async def _render_scene_simple(
        self, 
        scene: SceneSpec, 
        video_id: str
    ) -> Optional[str]:
        """Simple scene render without complex motion (fallback)."""
        
        output_path = self.temp_dir / f"{video_id}_simple_{scene.index:03d}.mp4"
        
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", scene.image_path,
            "-t", str(scene.duration),
            "-vf", f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps={self.fps}",
            "-c:v", "libx264", "-preset", "fast",
            "-b:v", "10M", "-minrate", "8M", "-maxrate", "12M", "-bufsize", "20M",
            "-pix_fmt", "yuv420p",
            "-an",
            str(output_path)
        ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            
            if output_path.exists():
                return str(output_path)
        except:
            pass
        
        return None
    
    async def _concatenate_scenes(
        self, 
        scene_videos: List[str], 
        video_id: str
    ) -> Optional[str]:
        """Concatenate all scene videos into one."""
        
        concat_file = self.temp_dir / f"{video_id}_concat.txt"
        output_path = self.temp_dir / f"{video_id}_video_only.mp4"
        
        # Write concat file
        with open(concat_file, 'w') as f:
            for video in scene_videos:
                # Escape path for FFmpeg
                escaped_path = video.replace("\\", "/").replace("'", "'\\''")
                f.write(f"file '{escaped_path}'\n")
        
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
            await process.communicate()
            
            if output_path.exists():
                return str(output_path)
        except:
            pass
        
        return None
    
    async def _add_audio(
        self, 
        video_path: str, 
        audio_path: str, 
        output_path: str
    ) -> Optional[str]:
        """Add audio to video with Hollywood-grade encoding."""
        
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", audio_path,
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-c:v", "libx264",
            "-preset", "slow",
            "-profile:v", "high",
            "-level", "4.2",
            "-b:v", self.bitrate,
            "-minrate", self.min_bitrate,
            "-maxrate", self.max_bitrate,
            "-bufsize", "16M",
            "-g", "60",
            "-keyint_min", "60",
            "-sc_threshold", "0",
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
            await process.communicate()
            
            if Path(output_path).exists():
                return output_path
        except:
            pass
        
        return None
    
    async def stitch_scenes(
        self,
        scene_images: List[str],
        audio_path: str,
        output_path: str,
        video_id: str = None,
        parallel: int = 4
    ) -> StitchResult:
        """
        Stitch multiple scene images into a single video with audio.
        
        Args:
            scene_images: List of paths to scene images
            audio_path: Path to audio file
            output_path: Where to save final video
            video_id: Unique identifier for temp files
            parallel: Max parallel scene renders
        
        Returns:
            StitchResult with video path and metadata
        """
        
        if not video_id:
            import uuid
            video_id = uuid.uuid4().hex[:8]
        
        # Filter valid images
        valid_images = [p for p in scene_images if Path(p).exists()]
        
        if not valid_images:
            return StitchResult(
                video_path="",
                success=False,
                scene_count=0,
                total_duration=0,
                unique_visuals=0,
                error="No valid scene images provided"
            )
        
        # Get audio duration
        audio_duration = self._get_audio_duration(audio_path)
        
        # Assign scene timings
        scenes = self._assign_scene_timings(valid_images, audio_duration)
        
        if not scenes:
            return StitchResult(
                video_path="",
                success=False,
                scene_count=0,
                total_duration=0,
                unique_visuals=0,
                error="Failed to assign scene timings"
            )
        
        print(f"🎬 Rendering {len(scenes)} scenes with motion...")
        
        # Render scenes with motion (parallel but limited)
        semaphore = asyncio.Semaphore(parallel)
        
        async def render_with_limit(scene: SceneSpec):
            async with semaphore:
                return await self._render_scene_with_motion(scene, video_id)
        
        tasks = [render_with_limit(scene) for scene in scenes]
        scene_videos = await asyncio.gather(*tasks)
        
        # Filter successful renders
        valid_scene_videos = [v for v in scene_videos if v and Path(v).exists()]
        
        if not valid_scene_videos:
            return StitchResult(
                video_path="",
                success=False,
                scene_count=len(scenes),
                total_duration=0,
                unique_visuals=0,
                error="All scene renders failed"
            )
        
        print(f"🎬 Concatenating {len(valid_scene_videos)} scene clips...")
        
        # Concatenate scenes
        video_only = await self._concatenate_scenes(valid_scene_videos, video_id)
        
        if not video_only:
            return StitchResult(
                video_path="",
                success=False,
                scene_count=len(scenes),
                total_duration=0,
                unique_visuals=len(valid_scene_videos),
                error="Scene concatenation failed"
            )
        
        print(f"🎬 Adding audio and finalizing...")
        
        # Add audio
        final_video = await self._add_audio(video_only, audio_path, output_path)
        
        if not final_video:
            return StitchResult(
                video_path="",
                success=False,
                scene_count=len(scenes),
                total_duration=audio_duration,
                unique_visuals=len(valid_scene_videos),
                error="Audio mixing failed"
            )
        
        # Cleanup temp files
        self._cleanup(video_id)
        
        return StitchResult(
            video_path=final_video,
            success=True,
            scene_count=len(scenes),
            total_duration=audio_duration,
            unique_visuals=len(set(valid_images))
        )
    
    def _cleanup(self, video_id: str):
        """Clean up temporary files."""
        for pattern in [f"{video_id}_motion_*.mp4", f"{video_id}_simple_*.mp4",
                       f"{video_id}_concat.txt", f"{video_id}_video_only.mp4"]:
            for f in self.temp_dir.glob(pattern):
                try:
                    f.unlink()
                except:
                    pass


# Convenience function
async def stitch_scenes_to_video(
    scene_images: List[str],
    audio_path: str,
    output_path: str
) -> StitchResult:
    """Stitch scene images into a video with audio."""
    stitcher = SceneStitcher()
    return await stitcher.stitch_scenes(scene_images, audio_path, output_path)
