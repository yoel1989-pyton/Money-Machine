"""
===============================================================================
ENTROPY GATE - Visual Diversity Validation
===============================================================================
Ensures videos have sufficient visual entropy to avoid algorithm suppression.

YouTube's algorithm detects:
- Repeated visual frames
- Low scene diversity
- Static backgrounds with only audio changes

This gate ENFORCES minimum visual entropy for all videos.
===============================================================================
"""

import os
import json
import subprocess
import hashlib
from pathlib import Path
from typing import Tuple, Dict, List, Optional
from dataclasses import dataclass


@dataclass
class EntropyReport:
    """Report from entropy validation."""
    passed: bool
    scene_count: int
    unique_frames: int
    visual_diversity: float  # 0-1 score
    scene_change_rate: float  # Changes per second
    issues: List[str]
    recommendations: List[str]


# Minimum thresholds for different content types
ENTROPY_THRESHOLDS = {
    "shorts": {
        "min_scenes": 8,
        "min_diversity": 0.6,
        "min_scene_rate": 0.3,  # At least 0.3 scene changes per second
        "max_static_duration": 4.0,  # Max seconds of static visual
    },
    "longform": {
        "min_scenes": 50,
        "min_diversity": 0.5,
        "min_scene_rate": 0.15,
        "max_static_duration": 10.0,
    }
}


def detect_scene_changes(video_path: str, threshold: float = 0.3) -> List[float]:
    """
    Detect scene changes in video using FFmpeg scene detection.
    
    Returns list of timestamps where scene changes occur.
    """
    
    try:
        # Use FFmpeg's scene detection filter
        cmd = [
            "ffmpeg", "-i", video_path,
            "-vf", f"select='gt(scene,{threshold})',showinfo",
            "-f", "null", "-"
        ]
        
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=120
        )
        
        # Parse scene timestamps from stderr
        scene_times = []
        for line in result.stderr.split('\n'):
            if 'pts_time:' in line:
                try:
                    # Extract pts_time value
                    pts_match = line.split('pts_time:')[1].split()[0]
                    scene_times.append(float(pts_match))
                except:
                    pass
        
        return scene_times
        
    except Exception as e:
        print(f"Scene detection error: {e}")
        return []


def calculate_frame_diversity(video_path: str, sample_count: int = 30) -> float:
    """
    Calculate visual diversity by sampling frames and comparing hashes.
    
    Returns diversity score 0-1 (1 = all frames unique, 0 = all identical).
    """
    
    try:
        # Get video duration
        probe_cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "json", video_path
        ]
        result = subprocess.run(probe_cmd, capture_output=True, text=True)
        duration = float(json.loads(result.stdout)["format"]["duration"])
        
        # Sample frames at regular intervals
        frame_hashes = set()
        interval = duration / sample_count
        
        for i in range(sample_count):
            timestamp = i * interval
            
            # Extract frame as raw pixels and hash
            cmd = [
                "ffmpeg", "-ss", str(timestamp),
                "-i", video_path,
                "-vframes", "1",
                "-f", "rawvideo",
                "-pix_fmt", "gray",
                "-s", "64x64",  # Small size for fast hashing
                "-"
            ]
            
            result = subprocess.run(
                cmd, capture_output=True, timeout=10
            )
            
            if result.stdout:
                # Hash the frame data
                frame_hash = hashlib.md5(result.stdout).hexdigest()[:12]
                frame_hashes.add(frame_hash)
        
        # Diversity = unique frames / total samples
        diversity = len(frame_hashes) / sample_count if sample_count > 0 else 0
        
        return diversity
        
    except Exception as e:
        print(f"Frame diversity error: {e}")
        return 0.5  # Default middle value


def validate_visual_entropy(
    video_path: str,
    mode: str = "shorts"
) -> Tuple[bool, EntropyReport]:
    """
    Validate that video has sufficient visual entropy.
    
    Args:
        video_path: Path to video file
        mode: "shorts" or "longform"
    
    Returns:
        Tuple of (passed, EntropyReport)
    """
    
    thresholds = ENTROPY_THRESHOLDS.get(mode, ENTROPY_THRESHOLDS["shorts"])
    issues = []
    recommendations = []
    
    # Get video duration
    try:
        probe_cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "json", video_path
        ]
        result = subprocess.run(probe_cmd, capture_output=True, text=True)
        duration = float(json.loads(result.stdout)["format"]["duration"])
    except:
        duration = 30.0  # Assume default
    
    # Detect scene changes
    scene_times = detect_scene_changes(video_path)
    scene_count = len(scene_times) + 1  # +1 for initial scene
    
    # Calculate scene change rate
    scene_rate = (len(scene_times) / duration) if duration > 0 else 0
    
    # Calculate frame diversity
    diversity = calculate_frame_diversity(video_path)
    
    # Evaluate against thresholds
    passed = True
    
    if scene_count < thresholds["min_scenes"]:
        passed = False
        issues.append(f"Too few scene changes: {scene_count} < {thresholds['min_scenes']} required")
        recommendations.append("Use scene-based visual generation to create more unique visuals")
    
    if diversity < thresholds["min_diversity"]:
        passed = False
        issues.append(f"Low visual diversity: {diversity:.2f} < {thresholds['min_diversity']} required")
        recommendations.append("Ensure each scene has a unique AI-generated visual")
    
    if scene_rate < thresholds["min_scene_rate"]:
        passed = False
        issues.append(f"Slow scene pacing: {scene_rate:.2f}/s < {thresholds['min_scene_rate']}/s required")
        recommendations.append("Reduce scene duration to 1.5-2.5 seconds")
    
    # Check for long static sections
    if scene_times:
        max_gap = 0
        prev_time = 0
        for t in scene_times:
            gap = t - prev_time
            max_gap = max(max_gap, gap)
            prev_time = t
        max_gap = max(max_gap, duration - prev_time)
        
        if max_gap > thresholds["max_static_duration"]:
            issues.append(f"Static section too long: {max_gap:.1f}s > {thresholds['max_static_duration']}s")
            recommendations.append("Add more visual cuts in long sections")
    
    # Build report
    report = EntropyReport(
        passed=passed,
        scene_count=scene_count,
        unique_frames=int(diversity * 30),  # Approximate from sampling
        visual_diversity=diversity,
        scene_change_rate=scene_rate,
        issues=issues,
        recommendations=recommendations
    )
    
    return passed, report


def enforce_entropy_gate(
    video_path: str,
    mode: str = "shorts",
    strict: bool = True
) -> Tuple[bool, Dict]:
    """
    Enforce entropy gate - reject videos that don't meet standards.
    
    Args:
        video_path: Path to video
        mode: Content type
        strict: If True, fail hard. If False, just warn.
    
    Returns:
        Tuple of (passed, details_dict)
    """
    
    passed, report = validate_visual_entropy(video_path, mode)
    
    details = {
        "passed": passed,
        "scene_count": report.scene_count,
        "visual_diversity": round(report.visual_diversity, 3),
        "scene_rate": round(report.scene_change_rate, 3),
        "issues": report.issues,
        "recommendations": report.recommendations
    }
    
    if not passed:
        if strict:
            details["action"] = "REJECTED - Video does not meet entropy standards"
        else:
            details["action"] = "WARNING - Video may be suppressed by algorithm"
    else:
        details["action"] = "APPROVED - Video meets entropy standards"
    
    return passed, details


# Convenience for SOVEREIGN.py integration
def check_entropy(video_path: str, mode: str = "shorts") -> Tuple[bool, Dict]:
    """Quick entropy check for integration."""
    return enforce_entropy_gate(video_path, mode, strict=False)
