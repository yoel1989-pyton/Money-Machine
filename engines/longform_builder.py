"""
LONG-FORM DOCUMENTARY BUILDER v1.0
Converts winning Shorts DNA into 10-20 minute elite documentaries.

The Revenue Leap:
- Shorts RPM: $0.02-0.08
- Long-form RPM: $12-30+
- One 15-min doc with 100k views = more than 10M Shorts views

5-ACT FRAMEWORK:
1. Hook (0-2 min) - Shorts-level intensity
2. Mechanism (2-6 min) - How the system works
3. Players (6-10 min) - Who benefits, who loses
4. Consequences (10-14 min) - Why this affects viewer
5. Resolution (14-20 min) - Strategic understanding
"""

import subprocess
import os
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

# Production constants
LF_BITRATE = "18M"  # 4K-ready bitrate
LF_MINRATE = "12M"
LF_MAXRATE = "24M"
LF_BUFSIZE = "36M"
LF_PRESET = "slow"
TARGET_DURATION = 900  # 15 minutes default

BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "data" / "output" / "longform"
ASSETS_DIR = BASE_DIR / "data" / "assets"

# 5-Act structure with timing
ACT_STRUCTURE = {
    "hook": {"start": 0, "end": 120, "intensity": "extreme", "visual_density": "high"},
    "mechanism": {"start": 120, "end": 360, "intensity": "educational", "visual_density": "medium"},
    "players": {"start": 360, "end": 600, "intensity": "narrative", "visual_density": "high"},
    "consequences": {"start": 600, "end": 840, "intensity": "escalating", "visual_density": "high"},
    "resolution": {"start": 840, "end": 1200, "intensity": "conclusive", "visual_density": "medium"},
}


@dataclass
class DocumentaryDNA:
    """DNA extracted from winning Shorts for documentary expansion."""
    topic: str
    theme: str
    hook_structure: str
    emotional_trigger: str
    visual_intent: str
    curiosity_gaps: List[str]
    retention_pattern: str
    rpm_score: float
    source_short_id: Optional[str] = None


@dataclass
class ActContent:
    """Content for a single documentary act."""
    act_name: str
    narration: str
    visual_instructions: List[Dict[str, str]]
    transitions: List[str]
    duration_seconds: int
    music_mood: str


class LongformBuilder:
    """
    Hollywood-grade documentary assembler.
    Converts Short DNA into cinematic long-form content.
    """
    
    def __init__(self):
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        self.broll_engine = None
        self._load_broll_engine()
    
    def _load_broll_engine(self):
        """Load B-roll engine for visual selection."""
        try:
            from engines.broll_engine import BRollEngine
            self.broll_engine = BRollEngine()
        except ImportError:
            print("[LONGFORM] Warning: BRollEngine not available")
    
    def extract_dna_from_short(self, short_data: Dict) -> DocumentaryDNA:
        """
        Extract documentary DNA from a winning Short.
        This is where Shorts become documentaries.
        """
        return DocumentaryDNA(
            topic=short_data.get("topic", ""),
            theme=self._detect_theme(short_data.get("topic", "")),
            hook_structure=short_data.get("hook_type", "curiosity_threat"),
            emotional_trigger=self._detect_emotion(short_data.get("script", "")),
            visual_intent=short_data.get("visual_intent", "power_finance"),
            curiosity_gaps=self._extract_curiosity_gaps(short_data.get("script", "")),
            retention_pattern=short_data.get("retention_pattern", "front_loaded"),
            rpm_score=short_data.get("rpm", 0.0),
            source_short_id=short_data.get("video_id")
        )
    
    def _detect_theme(self, topic: str) -> str:
        """Detect documentary theme from topic."""
        topic_lower = topic.lower()
        if any(w in topic_lower for w in ["rich", "wealth", "money", "billion"]):
            return "wealth_inequality"
        if any(w in topic_lower for w in ["system", "control", "design", "algorithm"]):
            return "systemic_manipulation"
        if any(w in topic_lower for w in ["bank", "fed", "reserve", "credit"]):
            return "financial_power"
        if any(w in topic_lower for w in ["ai", "future", "obsolete", "automation"]):
            return "technological_disruption"
        return "hidden_truth"
    
    def _detect_emotion(self, script: str) -> str:
        """Detect primary emotional trigger."""
        script_lower = script.lower()
        if any(w in script_lower for w in ["unfair", "rigged", "designed"]):
            return "injustice"
        if any(w in script_lower for w in ["secret", "hidden", "never told"]):
            return "revelation"
        if any(w in script_lower for w in ["disappear", "collapse", "end"]):
            return "urgency"
        return "curiosity"
    
    def _extract_curiosity_gaps(self, script: str) -> List[str]:
        """Extract unanswered questions for expansion."""
        gaps = []
        if "how" not in script.lower():
            gaps.append("How does this actually work?")
        if "who" not in script.lower():
            gaps.append("Who benefits from this?")
        if "why" not in script.lower():
            gaps.append("Why was this designed this way?")
        gaps.append("What can you do about it?")
        gaps.append("What happens next?")
        return gaps
    
    async def expand_to_documentary(
        self,
        dna: DocumentaryDNA,
        audio_path: str,
        output_path: str = None
    ) -> str:
        """
        Expand Short DNA into full documentary.
        This is the main production method.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = output_path or str(OUTPUT_DIR / f"doc_{timestamp}.mp4")
        
        print(f"[LONGFORM] 🎬 Building documentary: {dna.topic}")
        print(f"[LONGFORM] Theme: {dna.theme}")
        print(f"[LONGFORM] Emotional trigger: {dna.emotional_trigger}")
        
        # Get audio duration
        duration = await self._get_audio_duration(audio_path)
        print(f"[LONGFORM] Duration: {duration/60:.1f} minutes")
        
        # Select B-roll for each act
        broll_clips = await self._select_broll_for_acts(dna, duration)
        
        # Build the documentary
        success = await self._assemble_documentary(
            audio_path=audio_path,
            broll_clips=broll_clips,
            output_path=output_path,
            duration=duration,
            dna=dna
        )
        
        if success and os.path.exists(output_path):
            file_size = os.path.getsize(output_path) / (1024 * 1024)
            print(f"[LONGFORM] ✅ Documentary created: {file_size:.1f} MB")
            return output_path
        
        raise RuntimeError("Documentary assembly failed")
    
    async def _get_audio_duration(self, audio_path: str) -> float:
        """Get audio file duration."""
        try:
            result = subprocess.run([
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "json", audio_path
            ], capture_output=True, text=True)
            return float(json.loads(result.stdout)["format"]["duration"])
        except:
            return TARGET_DURATION
    
    async def _select_broll_for_acts(
        self,
        dna: DocumentaryDNA,
        duration: float
    ) -> List[Dict[str, Any]]:
        """Select appropriate B-roll for each act."""
        clips = []
        
        # Visual intent to B-roll category mapping
        intent_categories = {
            "power_finance": ["money", "city"],
            "systems_control": ["tech", "city"],
            "future_warning": ["tech", "city"],
            "wealth": ["money", "lifestyle"],
            "psychology": ["people"],
        }
        
        categories = intent_categories.get(dna.visual_intent, ["money", "tech", "city"])
        
        # Get clips for each act
        num_clips_needed = max(15, int(duration / 30))  # ~1 clip per 30 seconds
        
        if self.broll_engine:
            used = set()
            for i in range(num_clips_needed):
                category = categories[i % len(categories)]
                clip = await self.broll_engine.get_clip(category, exclude=used)
                if clip:
                    clips.append({
                        "path": clip,
                        "category": category,
                        "start_time": i * (duration / num_clips_needed)
                    })
                    used.add(clip)
        
        return clips
    
    async def _assemble_documentary(
        self,
        audio_path: str,
        broll_clips: List[Dict],
        output_path: str,
        duration: float,
        dna: DocumentaryDNA
    ) -> bool:
        """
        Assemble the final documentary with cinematic treatment.
        Uses Hollywood-grade FFmpeg pipeline.
        """
        # If no B-roll, use a single background with Ken Burns effect
        if not broll_clips:
            # Get any available background
            from engines.quality_gates import VisualFallback
            bg_path = await VisualFallback.get_fallback_background(duration=duration)
            
            cmd = [
                "ffmpeg", "-y",
                "-stream_loop", "-1",
                "-i", bg_path,
                "-i", audio_path,
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-t", str(duration),
                "-vf", (
                    "scale=3840:2160:force_original_aspect_ratio=increase,"
                    "crop=3840:2160,"
                    "fps=30,"
                    "zoompan=z='min(zoom+0.0002,1.15)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=3840x2160,"
                    "eq=contrast=1.08:saturation=1.10:brightness=0.02,"
                    "format=yuv420p"
                ),
                "-c:v", "libx264",
                "-profile:v", "high",
                "-level", "5.1",
                "-preset", LF_PRESET,
                "-b:v", LF_BITRATE,
                "-minrate", LF_MINRATE,
                "-maxrate", LF_MAXRATE,
                "-bufsize", LF_BUFSIZE,
                "-c:a", "aac",
                "-b:a", "256k",
                "-ar", "48000",
                "-movflags", "+faststart",
                output_path
            ]
        else:
            # Concatenate B-roll clips with transitions
            # For now, use the first clip as main background
            bg_path = broll_clips[0]["path"]
            
            cmd = [
                "ffmpeg", "-y",
                "-stream_loop", "-1",
                "-i", bg_path,
                "-i", audio_path,
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-t", str(duration),
                "-vf", (
                    "scale=3840:2160:force_original_aspect_ratio=increase,"
                    "crop=3840:2160,"
                    "fps=30,"
                    "zoompan=z='min(zoom+0.0003,1.2)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=3840x2160,"
                    "eq=contrast=1.10:saturation=1.12:brightness=0.02,"
                    "unsharp=5:5:0.8,"
                    "format=yuv420p"
                ),
                "-c:v", "libx264",
                "-profile:v", "high",
                "-level", "5.1",
                "-preset", LF_PRESET,
                "-b:v", LF_BITRATE,
                "-minrate", LF_MINRATE,
                "-maxrate", LF_MAXRATE,
                "-bufsize", LF_BUFSIZE,
                "-c:a", "aac",
                "-b:a", "256k",
                "-ar", "48000",
                "-movflags", "+faststart",
                output_path
            ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        return process.returncode == 0


class DocumentaryScriptExpander:
    """
    Expands Short scripts into full documentary narration.
    150 words → 2,500+ words using the 5-Act framework.
    """
    
    def __init__(self):
        self.openai_client = None
        self._init_openai()
    
    def _init_openai(self):
        """Initialize OpenAI client."""
        try:
            import openai
            self.openai_client = openai.OpenAI()
        except:
            pass
    
    async def expand_script(
        self,
        short_script: str,
        dna: DocumentaryDNA,
        target_duration_minutes: int = 15
    ) -> str:
        """
        Expand Short script into documentary narration.
        """
        if not self.openai_client:
            return self._fallback_expansion(short_script, dna)
        
        target_words = target_duration_minutes * 150  # ~150 words/minute
        
        prompt = f"""Expand this Short script into a {target_duration_minutes}-minute documentary narration.

ORIGINAL SHORT SCRIPT:
{short_script}

DOCUMENTARY DNA:
- Theme: {dna.theme}
- Emotional Trigger: {dna.emotional_trigger}
- Curiosity Gaps to Address: {', '.join(dna.curiosity_gaps)}

5-ACT STRUCTURE TO FOLLOW:

ACT 1 - THE HOOK (2 minutes):
- Open with the most provocative claim
- Create immediate tension
- Make viewer feel something is being hidden from them

ACT 2 - THE MECHANISM (4 minutes):
- Explain HOW this system actually works
- Use concrete examples
- Build understanding before judgment

ACT 3 - THE PLAYERS (4 minutes):
- Who designed this system and why
- Who benefits most
- Historical examples of this pattern

ACT 4 - THE CONSEQUENCES (4 minutes):
- Why this affects the viewer personally
- Future implications
- Escalate the stakes

ACT 5 - THE RESOLUTION (3 minutes):
- Strategic understanding (not motivational fluff)
- Intellectual closure
- Leave them thinking, not hoping

RULES:
- Tone: Authoritative, not preachy
- No motivational clichés
- Facts over inspiration
- Each section should flow naturally
- Target: {target_words} words total
- Write as continuous narration (no section headers in output)

OUTPUT THE DOCUMENTARY SCRIPT:"""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=4000
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"[LONGFORM] Script expansion error: {e}")
            return self._fallback_expansion(short_script, dna)
    
    def _fallback_expansion(self, short_script: str, dna: DocumentaryDNA) -> str:
        """Fallback expansion without API."""
        return f"""
{short_script}

But that's just the surface. Let me show you how deep this really goes.

The system wasn't designed by accident. Every rule, every regulation, every financial instrument 
was carefully constructed by people who understood one thing: how to make money move in their direction.

Think about it. When was the last time a major financial reform actually helped the average person? 
The 2008 bailouts went to the banks. The pandemic stimulus went to corporations first. 
The wealth gap didn't happen by chance—it was engineered.

Here's what they don't teach you: {dna.topic}. This isn't conspiracy. This is documented history. 
The same patterns repeat because the same people are in charge of the rules.

What does this mean for you? Everything you've been taught about money, success, and the "right way" 
to build wealth—most of it was designed to keep you in a specific lane.

The question isn't whether the system is fair. It's whether you understand the rules well enough 
to stop playing the game they designed for you.

{short_script}
"""


# Export for use in workflows
async def build_documentary_from_short(short_data: Dict, audio_path: str) -> str:
    """
    Main entry point: Convert winning Short into documentary.
    """
    builder = LongformBuilder()
    dna = builder.extract_dna_from_short(short_data)
    return await builder.expand_to_documentary(dna, audio_path)


if __name__ == "__main__":
    # Test the builder
    print("Long-Form Documentary Builder v1.0")
    print("=" * 50)
    print("ACT Structure:")
    for act, timing in ACT_STRUCTURE.items():
        print(f"  {act.upper()}: {timing['start']/60:.0f}-{timing['end']/60:.0f} min ({timing['intensity']})")
