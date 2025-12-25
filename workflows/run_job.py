#!/usr/bin/env python3
"""
════════════════════════════════════════════════════════════════════════════════
💎 MONEY MACHINE AI — UNIFIED JOB RUNNER
════════════════════════════════════════════════════════════════════════════════
THE SINGLE ENTRYPOINT FOR ALL PRODUCTION

This is the spine of the distributed system:
- n8n Cloud DECIDES what to make
- This script EXECUTES with Hollywood quality
- Returns structured JSON for logging/evolution

Usage:
    python workflows/run_job.py --json '{"mode": "shorts", "topic": "..."}'
    python workflows/run_job.py --file payload.json
    echo '{"mode": "shorts"}' | python workflows/run_job.py --stdin

Modes:
    shorts    - 60-second elite Shorts (default)
    longform  - 10-15 minute documentary
    expand    - Expand winning Short to documentary

════════════════════════════════════════════════════════════════════════════════
"""

import os
import sys
import json
import uuid
import asyncio
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

# ════════════════════════════════════════════════════════════════════════════════
# CONFIGURATION — HOLLYWOOD STANDARDS (NON-NEGOTIABLE)
# ════════════════════════════════════════════════════════════════════════════════

DATA_DIR = Path(__file__).parent.parent / "data"
TEMP_DIR = DATA_DIR / "temp"
OUTPUT_DIR = DATA_DIR / "output"
LOGS_DIR = DATA_DIR / "logs"
DNA_DIR = DATA_DIR / "dna"

for d in [TEMP_DIR, OUTPUT_DIR, LOGS_DIR, DNA_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Quality gates — if any fail, NO UPLOAD
QUALITY_STANDARDS = {
    "shorts": {
        "resolution": (1080, 1920),
        "min_bitrate": 1_500_000,  # 1.5 Mbps floor (realistic for source material)
        "target_bitrate": 4_000_000,  # 4 Mbps target
        "max_bitrate": 10_000_000,  # 10 Mbps ceiling
        "fps": 30,
        "audio_bitrate": 192_000,
        "min_duration": 15,
        "max_duration": 65,  # Allow slight overage
        "scene_duration": (1.2, 2.8),  # Cut every 1.2-2.8 seconds
    },
    "longform": {
        "resolution": (3840, 2160),  # 4K
        "min_bitrate": 8_000_000,
        "target_bitrate": 18_000_000,
        "max_bitrate": 25_000_000,
        "fps": 30,
        "audio_bitrate": 320_000,
        "min_duration": 300,  # 5 minutes minimum
        "max_duration": 1800,  # 30 minutes max
    }
}


# ════════════════════════════════════════════════════════════════════════════════
# JOB RUNNER — THE EXECUTION ENGINE
# ════════════════════════════════════════════════════════════════════════════════

class JobRunner:
    """
    Unified job execution engine.
    
    Receives job from n8n Cloud webhook.
    Executes with full quality enforcement.
    Returns structured result for evolution.
    """
    
    def __init__(self):
        self.job_id = None
        self.start_time = None
        self.dna = {}
        self._load_engines()
    
    def _load_engines(self):
        """Lazy load all engines."""
        try:
            from engines.aave_engine import AAVEEngine
            self.aave = AAVEEngine()
        except ImportError:
            self.aave = None
        
        try:
            from engines.elite_builder import EliteVideoBuilder
            self.elite_builder = EliteVideoBuilder()
        except ImportError:
            self.elite_builder = None
        
        try:
            from engines.longform_builder import LongformBuilder
            self.longform_builder = LongformBuilder()
        except ImportError:
            self.longform_builder = None
        
        try:
            from engines.uploaders import YouTubeUploader
            self.uploader = YouTubeUploader()
        except ImportError:
            self.uploader = None
        
        try:
            from engines.quality_gates import QualityGate, VideoValidator
            self.quality_gate = QualityGate()
            self.video_validator = VideoValidator
        except ImportError:
            self.quality_gate = None
            self.video_validator = None
    
    async def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute job and return structured result.
        
        This is the ONLY function n8n calls.
        """
        self.job_id = payload.get("job_id", str(uuid.uuid4())[:8])
        self.start_time = datetime.now(timezone.utc)
        
        result = {
            "job_id": self.job_id,
            "status": "PENDING",
            "started_at": self.start_time.isoformat(),
            "completed_at": None,
            "video_path": None,
            "youtube_url": None,
            "bitrate": None,
            "duration": None,
            "dna": {},
            "error": None
        }
        
        try:
            mode = payload.get("mode", "shorts")
            
            if mode == "shorts":
                result = await self._run_shorts(payload, result)
            elif mode == "longform":
                result = await self._run_longform(payload, result)
            elif mode == "expand":
                result = await self._run_expand(payload, result)
            else:
                raise ValueError(f"Unknown mode: {mode}")
            
            result["status"] = "SUCCESS"
            
        except Exception as e:
            result["status"] = "FAILED"
            result["error"] = str(e)
            self._log_error(e, payload)
        
        result["completed_at"] = datetime.now(timezone.utc).isoformat()
        self._log_result(result)
        
        return result
    
    async def _run_shorts(self, payload: Dict, result: Dict) -> Dict:
        """Execute Shorts production pipeline."""
        
        # ═══════════════════════════════════════════════════════════
        # STEP 1: TOPIC SELECTION (AAVE Intelligence)
        # ═══════════════════════════════════════════════════════════
        
        topic = payload.get("topic")
        visual_intent = payload.get("visual_intent", "power_finance")
        
        if not topic and self.aave:
            topic_data, dna = self.aave.select_elite_topic()
            topic = topic_data["topic"]
            visual_intent = topic_data.get("visual_intent", "power_finance")
            self.dna = {
                "id": dna.get_id() if hasattr(dna, "get_id") else str(uuid.uuid4())[:8],
                "topic": topic,
                "visual_intent": visual_intent,
                "hook_type": topic_data.get("hook", {}).value if hasattr(topic_data.get("hook", {}), "value") else "system_reveal",
                "archetype": topic_data.get("archetype", "wealth_psychology")
            }
        else:
            self.dna = {
                "id": str(uuid.uuid4())[:8],
                "topic": topic or "Why the Rich Use Debt as a Weapon",
                "visual_intent": visual_intent,
                "hook_type": "system_reveal",
                "archetype": "wealth_psychology"
            }
            topic = self.dna["topic"]
        
        print(f"[JOB:{self.job_id}] 🎯 Topic: {topic}")
        print(f"[JOB:{self.job_id}] 🧬 DNA: {self.dna['id']}")
        
        # ═══════════════════════════════════════════════════════════
        # STEP 2: SCRIPT GENERATION
        # ═══════════════════════════════════════════════════════════
        
        script = payload.get("script")
        
        if not script:
            script = await self._generate_script(topic, self.dna)
        
        print(f"[JOB:{self.job_id}] 📝 Script: {len(script.split())} words")
        
        # ═══════════════════════════════════════════════════════════
        # STEP 3: VOICE SYNTHESIS
        # ═══════════════════════════════════════════════════════════
        
        audio_path = await self._generate_voice(script)
        print(f"[JOB:{self.job_id}] 🎙️ Audio: {Path(audio_path).name}")
        
        # ═══════════════════════════════════════════════════════════
        # STEP 4: VIDEO ASSEMBLY (HOLLYWOOD QUALITY)
        # ═══════════════════════════════════════════════════════════
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = str(OUTPUT_DIR / f"elite_{timestamp}_{self.job_id}.mp4")
        
        video_path = await self._build_video(audio_path, script, topic, output_path)
        print(f"[JOB:{self.job_id}] 🎬 Video: {Path(video_path).name}")
        
        # ═══════════════════════════════════════════════════════════
        # STEP 5: QUALITY GATE (MANDATORY)
        # ═══════════════════════════════════════════════════════════
        
        validation = await self._validate_video(video_path, "shorts")
        result["bitrate"] = validation.get("bitrate")
        result["duration"] = validation.get("duration")
        
        if not validation["passed"]:
            raise ValueError(f"Quality gate FAILED: {validation['reason']}")
        
        print(f"[JOB:{self.job_id}] ✅ Quality: {validation['bitrate'] / 1_000_000:.1f} Mbps")
        
        result["video_path"] = video_path
        result["dna"] = self.dna
        
        # ═══════════════════════════════════════════════════════════
        # STEP 6: UPLOAD (IF ENABLED)
        # ═══════════════════════════════════════════════════════════
        
        if payload.get("force_upload", True):
            youtube_url = await self._upload_video(video_path, topic)
            result["youtube_url"] = youtube_url
            print(f"[JOB:{self.job_id}] 📤 Uploaded: {youtube_url}")
        
        return result
    
    async def _run_longform(self, payload: Dict, result: Dict) -> Dict:
        """Execute Longform documentary pipeline."""
        
        topic = payload.get("topic")
        if not topic:
            raise ValueError("Longform mode requires a topic")
        
        print(f"[JOB:{self.job_id}] 🎬 Longform: {topic}")
        
        if self.longform_builder:
            # Use existing longform builder
            video_path = await self.longform_builder.build(
                topic=topic,
                style="documentary"
            )
        else:
            # Fallback to manual assembly
            script = await self._generate_longform_script(topic)
            audio_path = await self._generate_voice(script)
            video_path = await self._build_longform_video(audio_path, script, topic)
        
        validation = await self._validate_video(video_path, "longform")
        result["bitrate"] = validation.get("bitrate")
        result["duration"] = validation.get("duration")
        result["video_path"] = video_path
        
        if payload.get("force_upload", False):
            youtube_url = await self._upload_video(video_path, topic, is_longform=True)
            result["youtube_url"] = youtube_url
        
        return result
    
    async def _run_expand(self, payload: Dict, result: Dict) -> Dict:
        """Expand a winning Short into a documentary."""
        
        source_dna = payload.get("source_dna", {})
        topic = source_dna.get("topic", payload.get("topic"))
        
        if not topic:
            raise ValueError("Expand mode requires source topic/DNA")
        
        print(f"[JOB:{self.job_id}] 📈 Expanding: {topic}")
        
        # Generate expanded documentary script
        script = await self._generate_longform_script(topic, is_expansion=True)
        audio_path = await self._generate_voice(script)
        video_path = await self._build_longform_video(audio_path, script, topic)
        
        result["video_path"] = video_path
        result["dna"] = {
            "source": source_dna.get("id", "unknown"),
            "expanded_topic": topic,
            "type": "expansion"
        }
        
        return result
    
    # ════════════════════════════════════════════════════════════════
    # INTERNAL METHODS
    # ════════════════════════════════════════════════════════════════
    
    async def _generate_script(self, topic: str, dna: Dict) -> str:
        """Generate elite script using GPT-4o."""
        import openai
        
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        hook_type = dna.get("hook_type", "system_reveal")
        archetype = dna.get("archetype", "wealth_psychology")
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """You are an elite YouTube Shorts scriptwriter. Your scripts achieve 80%+ retention.

**GOLD STANDARD DNA (Graham Stephan, Jake Tran, ColdFusion):**

1. HOOK (0-3s) - Pattern Interrupt:
   - "You're being lied to about..."
   - Shocking stat or counterintuitive claim
   - Create cognitive dissonance

2. AGITATION (3-15s) - Open the Wound:
   - "Every time you..." / "While you sleep..."
   - Make the problem feel personal
   - Build emotional investment

3. MECHANISM (15-40s) - The Hidden Truth:
   - Reveal the "how" nobody talks about
   - Simple metaphors
   - Each sentence earns the next

4. PAYOFF (40-55s) - The Revelation:
   - Deliver the insight they came for
   - Make them feel smarter
   - Paradigm shift

5. LOOP (55-60s) - Engagement:
   - Open question OR
   - Tease next video OR
   - Challenge beliefs

**VOICE:**
- Short sentences (5-12 words)
- Conversational, not preachy
- Power words: exposed, rigged, weapon, hidden
- NO emojis, hashtags, timestamps
- 90-115 words total"""
                },
                {
                    "role": "user",
                    "content": f"Write an elite viral script about: {topic}\nHook Type: {hook_type}\nArchetype: {archetype}"
                }
            ],
            temperature=0.75,
            max_tokens=350
        )
        
        script = response.choices[0].message.content.strip()
        
        # Sanitize for TTS
        script = (script
            .replace("**", "")
            .replace("#", "")
            .replace("_", "")
            .replace("\n\n", " ")
            .replace("\n", " ")
            .strip())
        
        return script
    
    async def _generate_longform_script(self, topic: str, is_expansion: bool = False) -> str:
        """Generate documentary-style script."""
        import openai
        
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        prompt = f"""Write a 10-15 minute documentary script about: {topic}

Structure (5-Act):
1. COLD OPEN (30s) - Shocking hook
2. SETUP (2-3min) - Context and stakes
3. CONFLICT (4-5min) - The problem revealed
4. RESOLUTION (3-4min) - The hidden truth
5. CALL TO ACTION (1min) - What to do now

Style: ColdFusion / Jake Tran cinematic narration
Word count: 1500-2000 words
NO timestamps, stage directions, or labels."""

        if is_expansion:
            prompt += "\n\nThis is an EXPANSION of a successful Short. Go deeper."
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a documentary scriptwriter."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=3000
        )
        
        return response.choices[0].message.content.strip()
    
    async def _generate_voice(self, script: str) -> str:
        """Generate voice with ElevenLabs or Edge-TTS fallback."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        audio_path = str(TEMP_DIR / f"voice_{self.job_id}_{timestamp}.mp3")
        
        # Try ElevenLabs first
        elevenlabs_key = os.getenv("ELEVENLABS_API_KEY")
        if elevenlabs_key:
            try:
                import httpx
                async with httpx.AsyncClient(timeout=120) as client:
                    response = await client.post(
                        "https://api.elevenlabs.io/v1/text-to-speech/pNInz6obpgDQGcFmaJgB",
                        headers={"xi-api-key": elevenlabs_key},
                        json={
                            "text": script,
                            "model_id": "eleven_multilingual_v2",
                            "voice_settings": {
                                "stability": 0.45,
                                "similarity_boost": 0.85,
                                "style": 0.35
                            }
                        }
                    )
                    if response.status_code == 200:
                        Path(audio_path).write_bytes(response.content)
                        return audio_path
            except Exception as e:
                print(f"[JOB:{self.job_id}] ⚠️ ElevenLabs failed: {e}")
        
        # Fallback to Edge-TTS
        import edge_tts
        communicate = edge_tts.Communicate(script, "en-US-AndrewNeural")
        await communicate.save(audio_path)
        
        return audio_path
    
    async def _build_video(self, audio_path: str, script: str, topic: str, output_path: str) -> str:
        """Build Hollywood-quality video."""
        
        if self.elite_builder:
            try:
                return await self.elite_builder.build(
                    audio_path=audio_path,
                    script=script,
                    topic=topic,
                    output_path=output_path
                )
            except Exception as e:
                print(f"[JOB:{self.job_id}] ⚠️ Elite builder failed: {e}")
        
        # Fallback to direct FFmpeg
        return await self._ffmpeg_build(audio_path, topic, output_path)
    
    async def _ffmpeg_build(self, audio_path: str, topic: str, output_path: str) -> str:
        """Direct FFmpeg build with Hollywood settings."""
        
        # Find best B-roll (prefer higher quality sources)
        broll_dir = DATA_DIR / "assets" / "backgrounds"
        broll_files = list(broll_dir.rglob("*.mp4"))
        
        if not broll_files:
            raise RuntimeError("No B-roll available")
        
        # Prefer clips from non-deprecated folders with higher quality
        preferred_folders = ["money", "city", "tech", "people", "lifestyle"]
        
        preferred = [f for f in broll_files if any(p in str(f.parent) for p in preferred_folders)]
        
        import random
        broll = random.choice(preferred) if preferred else random.choice(broll_files)
        
        # Get audio duration
        duration = await self._get_audio_duration(audio_path)
        
        # Hollywood FFmpeg command - CRF-based quality (more reliable)
        # Using CRF 18 for high quality, let bitrate be natural
        cmd = [
            "ffmpeg", "-y",
            "-stream_loop", "-1",
            "-i", str(broll),
            "-i", audio_path,
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-t", str(duration + 0.5),
            "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,eq=contrast=1.08:saturation=1.12:brightness=0.02",
            "-c:v", "libx264",
            "-preset", "slow",
            "-crf", "18",
            "-profile:v", "high",
            "-level", "4.2",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-ar", "48000",
            "-movflags", "+faststart",
            output_path
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        _, stderr = await process.communicate()
        
        if not Path(output_path).exists():
            raise RuntimeError(f"FFmpeg failed: {stderr.decode()[-500:]}")
        
        return output_path
    
    async def _build_longform_video(self, audio_path: str, script: str, topic: str) -> str:
        """Build 4K documentary video."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = str(OUTPUT_DIR / "longform" / f"doc_{timestamp}_{self.job_id}.mp4")
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Similar to shorts but with 4K settings
        broll_dir = DATA_DIR / "assets" / "backgrounds"
        broll_files = list(broll_dir.rglob("*.mp4"))
        
        if not broll_files:
            raise RuntimeError("No B-roll for longform")
        
        import random
        broll = random.choice(broll_files)
        duration = await self._get_audio_duration(audio_path)
        
        cmd = [
            "ffmpeg", "-y",
            "-stream_loop", "-1",
            "-i", str(broll),
            "-i", audio_path,
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-t", str(duration + 1),
            "-vf", "scale=3840:2160:force_original_aspect_ratio=increase,crop=3840:2160",
            "-c:v", "libx264",
            "-preset", "slow",
            "-crf", "18",
            "-b:v", "18M",
            "-c:a", "aac",
            "-b:a", "320k",
            "-movflags", "+faststart",
            output_path
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        await process.communicate()
        
        return output_path
    
    async def _get_audio_duration(self, audio_path: str) -> float:
        """Get audio duration using ffprobe."""
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            audio_path
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, _ = await process.communicate()
        return float(stdout.decode().strip())
    
    async def _validate_video(self, video_path: str, mode: str) -> Dict:
        """Validate video against Hollywood standards."""
        
        standards = QUALITY_STANDARDS.get(mode, QUALITY_STANDARDS["shorts"])
        
        # Get video info
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration,bit_rate",
            "-show_entries", "stream=width,height",
            "-of", "json",
            video_path
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, _ = await process.communicate()
        info = json.loads(stdout.decode())
        
        format_info = info.get("format", {})
        stream_info = info.get("streams", [{}])[0]
        
        bitrate = int(format_info.get("bit_rate", 0))
        duration = float(format_info.get("duration", 0))
        width = stream_info.get("width", 0)
        height = stream_info.get("height", 0)
        
        result = {
            "passed": True,
            "bitrate": bitrate,
            "duration": duration,
            "resolution": (width, height),
            "reason": None
        }
        
        # Check bitrate
        if bitrate < standards["min_bitrate"]:
            result["passed"] = False
            result["reason"] = f"Bitrate {bitrate/1_000_000:.1f}Mbps below minimum {standards['min_bitrate']/1_000_000}Mbps"
        
        # Check duration
        if duration < standards.get("min_duration", 0):
            result["passed"] = False
            result["reason"] = f"Duration {duration:.1f}s below minimum"
        
        return result
    
    async def _upload_video(self, video_path: str, topic: str, is_longform: bool = False) -> Optional[str]:
        """Upload to YouTube."""
        
        if not self.uploader or not self.uploader.is_configured():
            print(f"[JOB:{self.job_id}] 📁 LOCAL MODE: Saved to {video_path}")
            return None
        
        title = topic[:95] + "..." if len(topic) > 95 else topic
        
        if is_longform:
            description = f"""{topic}

🎬 Full documentary on wealth, power, and financial systems.

💰 Subscribe for more deep dives
📈 Turn on notifications

#Finance #Wealth #Documentary #Money"""
        else:
            description = f"""{topic}

🎯 Master your money. Build real wealth.

💰 Follow for daily wealth insights
📈 No fluff. Just truth.

#Shorts #Money #Wealth #Finance"""
        
        tags = ["money", "wealth", "finance", "investing", "shorts"]
        
        try:
            result = await self.uploader.upload_short(
                video_path=video_path,
                title=title,
                description=description,
                tags=tags
            )
            
            # Handle both dict and string return types
            if isinstance(result, dict):
                video_id = result.get("video_id")
            else:
                video_id = result
            
            if video_id:
                return f"https://youtube.com/shorts/{video_id}"
        except Exception as e:
            print(f"[JOB:{self.job_id}] ❌ Upload failed: {e}")
        
        return None
    
    def _log_result(self, result: Dict):
        """Log job result for analytics."""
        log_file = LOGS_DIR / f"job_{self.job_id}.json"
        log_file.write_text(json.dumps(result, indent=2))
        
        # Also log DNA for evolution
        if result.get("dna"):
            dna_file = DNA_DIR / f"dna_{self.dna.get('id', 'unknown')}.json"
            dna_data = {
                **self.dna,
                "job_id": self.job_id,
                "status": result["status"],
                "youtube_url": result.get("youtube_url"),
                "bitrate": result.get("bitrate"),
                "created_at": result.get("started_at")
            }
            dna_file.write_text(json.dumps(dna_data, indent=2))
    
    def _log_error(self, error: Exception, payload: Dict):
        """Log error for debugging."""
        error_file = LOGS_DIR / f"error_{self.job_id}.json"
        error_file.write_text(json.dumps({
            "job_id": self.job_id,
            "error": str(error),
            "payload": payload,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }, indent=2))


# ════════════════════════════════════════════════════════════════════════════════
# CLI INTERFACE
# ════════════════════════════════════════════════════════════════════════════════

async def main():
    parser = argparse.ArgumentParser(description="Money Machine Job Runner")
    parser.add_argument("--json", type=str, help="JSON payload string")
    parser.add_argument("--file", type=str, help="JSON payload file")
    parser.add_argument("--stdin", action="store_true", help="Read JSON from stdin")
    parser.add_argument("--mode", type=str, default="shorts", help="Production mode")
    parser.add_argument("--topic", type=str, help="Topic override")
    parser.add_argument("--no-upload", action="store_true", help="Skip upload")
    args = parser.parse_args()
    
    # Parse payload
    if args.json:
        payload = json.loads(args.json)
    elif args.file:
        payload = json.loads(Path(args.file).read_text())
    elif args.stdin:
        payload = json.loads(sys.stdin.read())
    else:
        payload = {}
    
    # Apply CLI overrides
    if args.mode:
        payload["mode"] = args.mode
    if args.topic:
        payload["topic"] = args.topic
    if args.no_upload:
        payload["force_upload"] = False
    
    # Default to shorts with upload
    payload.setdefault("mode", "shorts")
    payload.setdefault("force_upload", True)
    
    # Run job
    runner = JobRunner()
    result = await runner.run(payload)
    
    # Output JSON result (for n8n to consume)
    print(json.dumps(result, indent=2))
    
    # Exit with appropriate code
    sys.exit(0 if result["status"] == "SUCCESS" else 1)


if __name__ == "__main__":
    asyncio.run(main())
