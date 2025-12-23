"""
SCENE PLANNER - The Brain of Elite Video Production
Orchestrates all engines to create a unified video timeline.
"""

import os
import json
import asyncio
import random
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, field, asdict

from engines.broll_engine import BRollEngine, extract_visual_keywords
from engines.rhythm_engine import RhythmEngine, detect_scene_beats, merge_beats_and_keywords
from engines.captions import generate_phrase_captions, estimate_word_timestamps
from engines.hook_engine import HookEngine


@dataclass
class SceneSegment:
    start: float
    end: float
    clip_path: str
    category: str = ""
    effect: str = "zoompan"
    zoom_intensity: float = 1.0
    transition: str = "cut"
    
    @property
    def duration(self) -> float:
        return self.end - self.start


@dataclass
class VideoTimeline:
    video_id: str
    duration: float
    scenes: List[SceneSegment] = field(default_factory=list)
    caption_file: str = ""
    hook_overlay: Dict = field(default_factory=dict)
    audio_path: str = ""
    emphasis_points: List[float] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        result["scenes"] = [asdict(s) for s in self.scenes]
        return result


class ScenePlanner:
    def __init__(self, broll_dir: str = "data/assets/backgrounds", output_dir: str = "data/temp"):
        self.broll_engine = BRollEngine(broll_dir)
        self.rhythm_engine = RhythmEngine()
        self.hook_engine = HookEngine(output_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.min_scene_duration, self.max_scene_duration = 1.2, 2.8
    
    async def plan_video(self, video_id: str, script: str, audio_path: str, topic: str = "", words: List[Dict] = None) -> VideoTimeline:
        beats = await asyncio.to_thread(detect_scene_beats, audio_path)
        audio_duration = self._get_audio_duration(audio_path)
        visual_keywords = extract_visual_keywords(script)
        scene_cuts = merge_beats_and_keywords(beats, list(visual_keywords.keys()), audio_duration)
        scene_cuts = self._optimize_scene_timing(scene_cuts, audio_duration)
        scenes = await self._assign_broll_to_scenes(scene_cuts, visual_keywords, audio_duration)
        emphasis_points = self.rhythm_engine.get_emphasis_points(audio_path)
        if words is None:
            words = estimate_word_timestamps(script, audio_duration)
        caption_path = self.output_dir / f"{video_id}_captions.ass"
        generate_phrase_captions(words, str(caption_path))
        hook_data = await self.hook_engine.create_hook_overlay(topic or script[:100], video_id)
        timeline = VideoTimeline(video_id=video_id, duration=audio_duration, scenes=scenes, caption_file=str(caption_path),
            hook_overlay=hook_data, audio_path=audio_path, emphasis_points=emphasis_points)
        return timeline
    
    def _get_audio_duration(self, audio_path: str) -> float:
        import subprocess
        try:
            result = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", audio_path], capture_output=True, text=True)
            return float(json.loads(result.stdout)["format"]["duration"])
        except:
            return 60.0
    
    def _optimize_scene_timing(self, cuts: List[float], duration: float) -> List[float]:
        if not cuts:
            num_scenes = int(duration / 2.0)
            return [i * 2.0 for i in range(num_scenes + 1)]
        if cuts[0] > 0.1: cuts.insert(0, 0.0)
        if cuts[-1] < duration - 0.5: cuts.append(duration)
        optimized = [cuts[0]]
        for cut in cuts[1:]:
            if cut - optimized[-1] >= self.min_scene_duration:
                optimized.append(cut)
        return optimized
    
    async def _assign_broll_to_scenes(self, cuts: List[float], keywords: Dict[str, str], duration: float) -> List[SceneSegment]:
        scenes = []
        used_clips = set()
        keyword_list = list(keywords.items()) if keywords else []
        for i in range(len(cuts) - 1):
            start, end = cuts[i], cuts[i + 1]
            progress = start / duration if duration > 0 else 0
            if keyword_list:
                idx = min(int(progress * len(keyword_list)), len(keyword_list) - 1)
                best_category = keyword_list[idx][1]
            else:
                best_category = random.choice(["tech", "city", "lifestyle"])
            clip = await self.broll_engine.get_clip(category=best_category, exclude=used_clips)
            if clip:
                used_clips.add(clip)
            else:
                clip = await self.broll_engine.get_random_clip(exclude=used_clips)
                if clip: used_clips.add(clip)
            if clip:
                scenes.append(SceneSegment(start=start, end=end, clip_path=clip, category=best_category))
        return scenes
