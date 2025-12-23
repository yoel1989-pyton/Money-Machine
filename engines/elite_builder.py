"""
ELITE VIDEO BUILDER v3.0 - Cut-Based Scene Sequencing
Hollywood-grade video builder using all elite engines.
"""

import os
import uuid
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

from engines.scene_planner import ScenePlanner, VideoTimeline
from engines.captions import generate_phrase_captions, estimate_word_timestamps

OUTPUT_DIR = Path(__file__).parent.parent / "data" / "output"
TEMP_DIR = Path(__file__).parent.parent / "data" / "temp"
BROLL_DIR = Path(__file__).parent.parent / "data" / "assets" / "backgrounds"


@dataclass
class BuildConfig:
    target_bitrate: str = "7M"
    max_bitrate: str = "8M"
    crf: int = 18
    min_scene_duration: float = 1.2
    max_scene_duration: float = 2.8
    enable_zoompan: bool = True
    enable_color_grade: bool = True
    contrast: float = 1.07
    saturation: float = 1.12
    enable_captions: bool = True
    enable_hook: bool = True
    resolution: str = "1080x1920"
    fps: int = 30


class EliteVideoBuilder:
    def __init__(self, config: BuildConfig = None):
        self.config = config or BuildConfig()
        self.scene_planner = ScenePlanner(broll_dir=str(BROLL_DIR), output_dir=str(TEMP_DIR))
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        TEMP_DIR.mkdir(parents=True, exist_ok=True)
    
    async def build(self, audio_path: str, script: str, topic: str = "", output_path: str = None, words: List[Dict] = None) -> str:
        video_id = uuid.uuid4().hex[:8]
        if output_path is None:
            output_path = str(OUTPUT_DIR / f"elite_{video_id}.mp4")
        
        timeline = await self.scene_planner.plan_video(video_id=video_id, script=script, audio_path=audio_path, topic=topic, words=words)
        scene_clips = await self._render_scenes(timeline)
        video_only = await self._concatenate_scenes(video_id, scene_clips)
        final = await self._finalize_video(video_id, video_only, audio_path, timeline, output_path)
        self._cleanup(video_id)
        return final
    
    async def _render_scenes(self, timeline: VideoTimeline) -> List[str]:
        scene_clips = []
        for i, scene in enumerate(timeline.scenes):
            output = TEMP_DIR / f"{timeline.video_id}_scene_{i:03d}.mp4"
            duration = scene.duration
            filters = ["scale=1080:1920:force_original_aspect_ratio=increase", "crop=1080:1920"]
            if self.config.enable_zoompan:
                zoom_frames = int(duration * self.config.fps)
                filters.append(f"zoompan=z='min(zoom+0.0008,1.04)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={zoom_frames}:s=1080x1920")
            if self.config.enable_color_grade:
                filters.append(f"eq=contrast={self.config.contrast}:saturation={self.config.saturation}")
            cmd = ["ffmpeg", "-y", "-ss", "0", "-t", str(duration), "-i", scene.clip_path, "-vf", ",".join(filters),
                "-c:v", "libx264", "-preset", "fast", "-crf", str(self.config.crf), "-pix_fmt", "yuv420p", "-an", str(output)]
            process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            await process.communicate()
            if output.exists():
                scene_clips.append(str(output))
        return scene_clips
    
    async def _concatenate_scenes(self, video_id: str, scene_clips: List[str]) -> str:
        if not scene_clips:
            raise RuntimeError("No scene clips to concatenate")
        concat_file = TEMP_DIR / f"{video_id}_concat.txt"
        concat_file.write_text("\n".join([f"file '{p}'" for p in scene_clips]))
        output = TEMP_DIR / f"{video_id}_video_only.mp4"
        cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c", "copy", str(output)]
        process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        await process.communicate()
        return str(output)
    
    async def _finalize_video(self, video_id: str, video_path: str, audio_path: str, timeline: VideoTimeline, output_path: str) -> str:
        filter_parts = []
        if self.config.enable_captions and timeline.caption_file and Path(timeline.caption_file).exists():
            filter_parts.append(f"ass='{timeline.caption_file.replace(chr(92), '/')}'")
        if self.config.enable_hook and timeline.hook_overlay.get("ass_path") and Path(timeline.hook_overlay["ass_path"]).exists():
            filter_parts.append(f"ass='{timeline.hook_overlay['ass_path'].replace(chr(92), '/')}'")
        filter_args = ["-vf", ",".join(filter_parts)] if filter_parts else []
        cmd = ["ffmpeg", "-y", "-i", video_path, "-i", audio_path, *filter_args, "-map", "0:v", "-map", "1:a",
            "-c:v", "libx264", "-preset", "slow", "-crf", str(self.config.crf), "-profile:v", "high", "-level", "4.2",
            "-pix_fmt", "yuv420p", "-b:v", self.config.target_bitrate, "-maxrate", self.config.max_bitrate, "-bufsize", "12M",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", "-shortest", output_path]
        process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            cmd = ["ffmpeg", "-y", "-i", video_path, "-i", audio_path, "-map", "0:v", "-map", "1:a",
                "-c:v", "libx264", "-preset", "slow", "-crf", str(self.config.crf), "-c:a", "aac", "-b:a", "192k",
                "-movflags", "+faststart", "-shortest", output_path]
            process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            await process.communicate()
        if not Path(output_path).exists():
            raise RuntimeError("Final video was not created")
        return output_path
    
    def _cleanup(self, video_id: str):
        for f in TEMP_DIR.glob(f"{video_id}*"):
            try: f.unlink()
            except: pass


async def build_elite_video(audio_path: str, script: str, topic: str = "", output_path: str = None) -> str:
    return await EliteVideoBuilder().build(audio_path, script, topic, output_path)


def build_elite_video_sync(audio_path: str, script: str, topic: str = "", output_path: str = None) -> str:
    return asyncio.run(build_elite_video(audio_path, script, topic, output_path))
