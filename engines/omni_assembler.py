"""
OMNI ASSEMBLER - Elite Omni Pipeline Stage 2
=============================================
VS Code / Local assembly layer.

Reads OPAL output and:
- Decides stitch order
- Applies re-timing
- Adds music/branding
- Executes merges via ffmpeg

MINIMAL WORK because:
- Clips are already elite
- Errors are already resolved
- Prompts are already optimized
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class AssemblyConfig:
    """Configuration for video assembly."""
    output_name: str = "final_video"
    output_format: str = "mp4"
    target_duration: Optional[float] = None  # Auto-calculate if None
    transition_type: str = "fade"
    transition_duration: float = 0.3
    add_music: bool = True
    music_path: Optional[str] = None
    music_volume: float = 0.3
    add_branding: bool = False
    brand_intro_path: Optional[str] = None
    brand_outro_path: Optional[str] = None


class OmniAssembler:
    """
    OMNI ASSEMBLER - Stateless assembly layer.
    Reads structured OPAL output and produces final videos.
    """
    
    def __init__(self, opal_output_dir: str):
        """
        Initialize with an OPAL output directory.
        
        Args:
            opal_output_dir: Path to OPAL run output (contains clips/, metadata.json, etc.)
        """
        self.opal_dir = Path(opal_output_dir)
        self.clips_dir = self.opal_dir / "clips"
        
        # Load OPAL intelligence
        self.metadata = self._load_json("metadata.json")
        self.prompts = self._load_json("prompts.json")
        self.failures = self._load_json("failure_log.json")
        
        # Validate
        if not self.clips_dir.exists():
            raise ValueError(f"No clips directory found at {self.clips_dir}")
            
        print(f"📦 Loaded OPAL output: {self.opal_dir.name}")
        print(f"   Clips: {self.metadata.get('successful_clips', 0)}")
        print(f"   Mode: {self.metadata.get('operating_mode', 'UNKNOWN')}")
        
    def _load_json(self, filename: str) -> Dict:
        """Load a JSON file from OPAL output."""
        path = self.opal_dir / filename
        if path.exists():
            with open(path) as f:
                return json.load(f)
        return {}
    
    def _get_clip_files(self) -> List[Path]:
        """Get all clip files in order."""
        clips = sorted(self.clips_dir.glob("clip_*.mp4"))
        return clips
    
    def _check_ffmpeg(self) -> bool:
        """Verify ffmpeg is available."""
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def analyze_clips(self) -> Dict[str, Any]:
        """
        Analyze available clips and return assembly recommendations.
        
        Returns:
            Analysis with clip inventory, duration estimates, and recommendations
        """
        clips = self._get_clip_files()
        clip_duration = self.metadata.get("duration_per_clip", 8.0)
        
        analysis = {
            "total_clips": len(clips),
            "estimated_duration": len(clips) * clip_duration,
            "clips_available": [c.stem for c in clips],
            "failed_clips": list(self.failures.keys()),
            "recovery_stats": {
                "recovered": len([f for f in self.failures.values() if f.get("status") == "RECOVERED"]),
                "failed": len([f for f in self.failures.values() if f.get("status") == "FAILED"])
            },
            "recommendations": []
        }
        
        # Add recommendations
        if analysis["estimated_duration"] < 30:
            analysis["recommendations"].append("Short video - ideal for YouTube Shorts / TikTok")
        elif analysis["estimated_duration"] < 60:
            analysis["recommendations"].append("Standard short - good for Reels / Shorts")
        elif analysis["estimated_duration"] < 180:
            analysis["recommendations"].append("Medium video - consider chapter markers")
        else:
            analysis["recommendations"].append("Long-form content - add intro/outro and chapters")
            
        if analysis["recovery_stats"]["failed"] > 0:
            analysis["recommendations"].append(
                f"⚠️ {analysis['recovery_stats']['failed']} clips failed - consider placeholders or re-run"
            )
            
        return analysis
    
    def generate_concat_file(self, output_path: Optional[Path] = None) -> Path:
        """
        Generate ffmpeg concat demuxer file.
        
        Args:
            output_path: Where to save the concat file
            
        Returns:
            Path to the concat file
        """
        clips = self._get_clip_files()
        
        if output_path is None:
            output_path = self.opal_dir / "concat.txt"
            
        with open(output_path, "w") as f:
            for clip in clips:
                # ffmpeg concat requires forward slashes and escaped quotes
                clip_path = str(clip.absolute()).replace("\\", "/")
                f.write(f"file '{clip_path}'\n")
                
        print(f"📝 Generated concat file: {output_path}")
        return output_path
    
    def assemble_simple(
        self,
        output_path: Optional[str] = None,
        config: Optional[AssemblyConfig] = None
    ) -> Path:
        """
        Simple concatenation assembly using ffmpeg.
        
        Args:
            output_path: Where to save the final video
            config: Assembly configuration
            
        Returns:
            Path to the assembled video
        """
        if not self._check_ffmpeg():
            raise RuntimeError("ffmpeg not found. Please install ffmpeg.")
            
        config = config or AssemblyConfig()
        clips = self._get_clip_files()
        
        if not clips:
            raise ValueError("No clips available for assembly")
            
        # Generate concat file
        concat_file = self.generate_concat_file()
        
        # Output path
        if output_path is None:
            output_path = self.opal_dir / f"{config.output_name}.{config.output_format}"
        else:
            output_path = Path(output_path)
            
        # Build ffmpeg command
        cmd = [
            "ffmpeg",
            "-y",  # Overwrite
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_file),
            "-c", "copy",  # Stream copy (fast, no re-encode)
            str(output_path)
        ]
        
        print(f"\n🎬 Assembling {len(clips)} clips...")
        print(f"   Output: {output_path}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Assembly complete: {output_path}")
            return output_path
        else:
            print(f"❌ Assembly failed: {result.stderr[:200]}")
            raise RuntimeError(f"ffmpeg failed: {result.stderr}")
    
    def assemble_with_transitions(
        self,
        output_path: Optional[str] = None,
        config: Optional[AssemblyConfig] = None
    ) -> Path:
        """
        Assembly with crossfade transitions using ffmpeg filter_complex.
        
        This is slower but produces smoother results.
        """
        if not self._check_ffmpeg():
            raise RuntimeError("ffmpeg not found. Please install ffmpeg.")
            
        config = config or AssemblyConfig()
        clips = self._get_clip_files()
        
        if not clips:
            raise ValueError("No clips available for assembly")
            
        if len(clips) == 1:
            # Just copy the single clip
            return self.assemble_simple(output_path, config)
            
        # Output path
        if output_path is None:
            output_path = self.opal_dir / f"{config.output_name}_transitions.{config.output_format}"
        else:
            output_path = Path(output_path)
            
        # Build complex filter for crossfades
        inputs = []
        for i, clip in enumerate(clips):
            inputs.extend(["-i", str(clip)])
            
        # Build filter graph
        filter_parts = []
        current_output = "[0:v]"
        
        for i in range(1, len(clips)):
            next_input = f"[{i}:v]"
            output_label = f"[v{i}]" if i < len(clips) - 1 else "[outv]"
            
            filter_parts.append(
                f"{current_output}{next_input}xfade=transition={config.transition_type}:"
                f"duration={config.transition_duration}:offset={i * 7.7}{output_label}"
            )
            current_output = output_label
            
        filter_complex = ";".join(filter_parts)
        
        cmd = [
            "ffmpeg",
            "-y",
            *inputs,
            "-filter_complex", filter_complex,
            "-map", "[outv]",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            str(output_path)
        ]
        
        print(f"\n🎬 Assembling {len(clips)} clips with {config.transition_type} transitions...")
        print(f"   Output: {output_path}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Assembly complete: {output_path}")
            return output_path
        else:
            print(f"❌ Assembly failed: {result.stderr[:500]}")
            # Fallback to simple assembly
            print("⚠️ Falling back to simple concatenation...")
            return self.assemble_simple(output_path, config)
    
    def add_audio_track(
        self,
        video_path: str,
        audio_path: str,
        output_path: Optional[str] = None,
        audio_volume: float = 0.3
    ) -> Path:
        """
        Add an audio track to the assembled video.
        
        Args:
            video_path: Path to the video
            audio_path: Path to the audio file (mp3, wav, etc.)
            output_path: Where to save the result
            audio_volume: Volume level for the audio (0.0 - 1.0)
            
        Returns:
            Path to the video with audio
        """
        if not self._check_ffmpeg():
            raise RuntimeError("ffmpeg not found.")
            
        video_path = Path(video_path)
        audio_path = Path(audio_path)
        
        if output_path is None:
            output_path = video_path.parent / f"{video_path.stem}_with_audio{video_path.suffix}"
        else:
            output_path = Path(output_path)
            
        cmd = [
            "ffmpeg",
            "-y",
            "-i", str(video_path),
            "-i", str(audio_path),
            "-filter_complex", f"[1:a]volume={audio_volume}[a]",
            "-map", "0:v",
            "-map", "[a]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            str(output_path)
        ]
        
        print(f"\n🎵 Adding audio track...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Audio added: {output_path}")
            return output_path
        else:
            print(f"❌ Failed to add audio: {result.stderr[:200]}")
            raise RuntimeError(f"ffmpeg failed: {result.stderr}")
    
    def export_assembly_report(self, output_path: Optional[str] = None) -> Path:
        """
        Export a JSON report of the assembly process.
        
        This is useful for:
        - Debugging
        - Automation
        - Monetization tracking
        """
        report = {
            "assembly_timestamp": datetime.now().isoformat(),
            "opal_run_id": self.metadata.get("run_id"),
            "opal_metadata": self.metadata,
            "clip_analysis": self.analyze_clips(),
            "prompt_lineage": self.prompts,
            "failure_log": self.failures
        }
        
        if output_path is None:
            output_path = self.opal_dir / "assembly_report.json"
        else:
            output_path = Path(output_path)
            
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)
            
        print(f"📊 Assembly report: {output_path}")
        return output_path


# ============================================================
# CLI INTERFACE
# ============================================================

def main():
    """CLI entry point for OMNI Assembler."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="OMNI Assembler - Assemble OPAL clip output into final videos"
    )
    parser.add_argument(
        "opal_dir",
        help="Path to OPAL output directory"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output video path"
    )
    parser.add_argument(
        "--transitions",
        action="store_true",
        help="Use crossfade transitions (slower)"
    )
    parser.add_argument(
        "--music",
        help="Path to music/audio file to add"
    )
    parser.add_argument(
        "--analyze-only",
        action="store_true",
        help="Only analyze clips, don't assemble"
    )
    
    args = parser.parse_args()
    
    assembler = OmniAssembler(args.opal_dir)
    
    if args.analyze_only:
        analysis = assembler.analyze_clips()
        print("\n📊 CLIP ANALYSIS")
        print("=" * 40)
        for key, value in analysis.items():
            print(f"  {key}: {value}")
        return
        
    # Assemble
    if args.transitions:
        video_path = assembler.assemble_with_transitions(args.output)
    else:
        video_path = assembler.assemble_simple(args.output)
        
    # Add music if specified
    if args.music:
        video_path = assembler.add_audio_track(str(video_path), args.music)
        
    # Export report
    assembler.export_assembly_report()
    
    print(f"\n🎉 Final video: {video_path}")


if __name__ == "__main__":
    main()
