#!/usr/bin/env python3
"""
============================================================
MONEY MACHINE AI - UNIVERSAL JOB ENTRYPOINT
============================================================
THE SPINE OF THE DISTRIBUTED SYSTEM

This is THE ONLY entrypoint for all orchestration.
n8n (cloud or local), webhooks, CLI — all go through here.

Usage:
    python workflows/run_job.py --json '{"mode":"shorts","topic":"..."}'
    python workflows/run_job.py --mode shorts --topic "Why the Rich Use Debt"
    echo '{"mode":"shorts"}' | python workflows/run_job.py --stdin

Modes:
    - shorts: Elite YouTube Short (30 min cycle)
    - longform: 4K Documentary (6 hour cycle)  
    - replicate: Clone winner DNA to new niche
    - analytics: Scan winners/losers
    - health: System status check

Returns JSON:
{
    "status": "SUCCESS|FAILED",
    "video_path": "...",
    "youtube_url": "...",
    "bitrate": 8200000,
    "duration": 42.1,
    "dna": {...}
}
============================================================
"""

import os
import sys
import json
import asyncio
import argparse
import uuid
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env", override=True)

# Import engines
from engines.aave_engine import AAVEEngine, VisualDNA, TopicPool
from engines.elite_builder import EliteVideoBuilder, BuildConfig
from engines.video_builder import build_video, validate_visual_entropy
from engines.uploaders import YouTubeUploader
from engines.quality_gates import QualityGate

# Import longform if available
try:
    from engines.longform_builder import LongformDocumentaryBuilder
    HAS_LONGFORM = True
except ImportError:
    HAS_LONGFORM = False

# Directories
OUTPUT_DIR = PROJECT_ROOT / "data" / "output"
AUDIO_DIR = PROJECT_ROOT / "data" / "audio"
SCRIPTS_DIR = PROJECT_ROOT / "data" / "scripts"
DNA_DIR = PROJECT_ROOT / "data" / "dna"
LOGS_DIR = PROJECT_ROOT / "data" / "logs"

for d in [OUTPUT_DIR, AUDIO_DIR, SCRIPTS_DIR, DNA_DIR, LOGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)


# ============================================================
# CORE JOB EXECUTOR
# ============================================================

class JobExecutor:
    """
    Universal job executor for all Money Machine operations.
    This is what n8n webhooks call.
    """
    
    def __init__(self):
        self.aave = AAVEEngine()
        self.quality_gate = QualityGate()
        self.youtube = YouTubeUploader()
        self.job_id = None
        
    async def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a job from payload.
        
        Expected payload:
        {
            "job_id": "uuid",
            "mode": "shorts|longform|replicate|analytics|health",
            "topic": "optional topic override",
            "script": "optional pre-generated script",
            "visual_intent": "power_finance|tech_disrupt|etc",
            "force_upload": true,
            "elite": true
        }
        """
        self.job_id = payload.get("job_id", uuid.uuid4().hex[:12])
        mode = payload.get("mode", "shorts")
        
        self._log(f"[JOB:{self.job_id}] Starting mode={mode}")
        
        try:
            if mode == "shorts":
                return await self._execute_shorts(payload)
            elif mode == "longform":
                return await self._execute_longform(payload)
            elif mode == "replicate":
                return await self._execute_replicate(payload)
            elif mode == "analytics":
                return await self._execute_analytics(payload)
            elif mode == "health":
                return self._execute_health(payload)
            else:
                return {"status": "FAILED", "error": f"Unknown mode: {mode}"}
        except Exception as e:
            self._log(f"[JOB:{self.job_id}] FAILED: {e}")
            return {"status": "FAILED", "error": str(e), "job_id": self.job_id}
    
    # ========================================================
    # SHORTS MODE (PRIMARY - Every 30 min)
    # ========================================================
    
    async def _execute_shorts(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Build and upload an elite YouTube Short."""
        
        # 1. Select topic (AAVE weighted selection)
        topic = payload.get("topic")
        if not topic:
            topic, weight = self.aave.select_topic()
            self._log(f"[AAVE] Selected topic: {topic} (weight: {weight})")
        
        visual_intent = payload.get("visual_intent", self._infer_visual_intent(topic))
        
        # 2. Generate script (or use provided)
        script = payload.get("script")
        if not script:
            script = await self._generate_script(topic, visual_intent)
        
        # Save script
        script_path = SCRIPTS_DIR / f"job_{self.job_id}.txt"
        script_path.write_text(script)
        
        # 3. Generate audio
        audio_path = await self._generate_audio(script)
        if not audio_path:
            return {"status": "FAILED", "error": "Audio generation failed"}
        
        # 4. Build video (Elite FFmpeg pipeline)
        video_path = await self._build_elite_video(audio_path, script, topic, visual_intent)
        if not video_path:
            return {"status": "FAILED", "error": "Video build failed"}
        
        # 5. Quality gate check
        passed, report = self._quality_check(video_path)
        if not passed and not payload.get("force_upload"):
            return {
                "status": "FAILED", 
                "error": "Quality gate failed",
                "report": report,
                "video_path": video_path
            }
        
        # 6. Upload to YouTube
        youtube_url = None
        if payload.get("force_upload", True) and self.youtube.is_configured():
            upload_result = await self._upload_youtube(video_path, topic, script)
            youtube_url = upload_result.get("url")
        
        # 7. Extract & log DNA
        dna = self._extract_dna(topic, visual_intent, script, report)
        self._log_dna(dna)
        
        # 8. Return result
        return {
            "status": "SUCCESS",
            "job_id": self.job_id,
            "mode": "shorts",
            "video_path": str(video_path),
            "youtube_url": youtube_url,
            "bitrate": report.get("bitrate", 0),
            "duration": report.get("duration", 0),
            "topic": topic,
            "visual_intent": visual_intent,
            "dna": dna,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    # ========================================================
    # LONGFORM MODE (Every 6 hours - Winners only)
    # ========================================================
    
    async def _execute_longform(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Build 4K documentary from winner DNA."""
        
        if not HAS_LONGFORM:
            return {"status": "FAILED", "error": "Longform builder not available"}
        
        # Get winner topic or specified topic
        topic = payload.get("topic")
        if not topic:
            winners = self.aave.get_winners()
            if not winners:
                return {"status": "SKIPPED", "reason": "No winners to expand"}
            topic = winners[0].get("topic")
        
        self._log(f"[LONGFORM] Building documentary: {topic}")
        
        try:
            builder = LongformDocumentaryBuilder()
            result = await builder.build(topic=topic)
            
            if result.get("success"):
                # Upload if configured
                youtube_url = None
                if self.youtube.is_configured():
                    upload_result = await self.youtube.upload_short(
                        video_path=result["video_path"],
                        title=result.get("title", topic)[:100],
                        description=f"Documentary: {topic}\n\n#wealth #finance #money",
                        privacy="public"
                    )
                    youtube_url = upload_result.get("url")
                
                return {
                    "status": "SUCCESS",
                    "mode": "longform",
                    "video_path": result["video_path"],
                    "youtube_url": youtube_url,
                    "duration": result.get("duration"),
                    "topic": topic
                }
            else:
                return {"status": "FAILED", "error": result.get("error", "Build failed")}
                
        except Exception as e:
            return {"status": "FAILED", "error": str(e)}
    
    # ========================================================
    # REPLICATE MODE (Clone winners to new niches)
    # ========================================================
    
    async def _execute_replicate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Clone winner DNA into new niche."""
        
        source_topic = payload.get("source_topic")
        target_niche = payload.get("target_niche", "tech")
        
        if not source_topic:
            winners = self.aave.get_winners()
            if not winners:
                return {"status": "SKIPPED", "reason": "No winners to replicate"}
            source_topic = winners[0].get("topic")
        
        # Mutate topic for new niche
        niche_mutations = {
            "tech": "technology and AI disruption",
            "careers": "career and job market",
            "economy": "economic systems",
            "crypto": "cryptocurrency and blockchain"
        }
        
        mutated_topic = f"{source_topic} ({niche_mutations.get(target_niche, target_niche)})"
        
        # Build with mutated topic
        payload["topic"] = mutated_topic
        payload["mode"] = "shorts"
        
        return await self._execute_shorts(payload)
    
    # ========================================================
    # ANALYTICS MODE (Scan YouTube for winners/losers)
    # ========================================================
    
    async def _execute_analytics(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Scan analytics and evolve topic weights."""
        
        # This would integrate with YouTube Analytics API
        # For now, return current AAVE state
        
        return {
            "status": "SUCCESS",
            "mode": "analytics",
            "winners": self.aave.get_winners()[:5],
            "losers": self.aave.get_losers()[:5],
            "topic_weights": self.aave.get_topic_weights()
        }
    
    # ========================================================
    # HEALTH MODE (System status)
    # ========================================================
    
    def _execute_health(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Check system health."""
        
        checks = {
            "youtube_configured": self.youtube.is_configured(),
            "ffmpeg_available": self._check_ffmpeg(),
            "output_dir_writable": OUTPUT_DIR.exists() and os.access(OUTPUT_DIR, os.W_OK),
            "broll_available": self._count_broll() > 0,
            "aave_active": True
        }
        
        all_healthy = all(checks.values())
        
        return {
            "status": "HEALTHY" if all_healthy else "DEGRADED",
            "mode": "health",
            "checks": checks,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    # ========================================================
    # HELPER METHODS
    # ========================================================
    
    async def _generate_script(self, topic: str, visual_intent: str) -> str:
        """Generate elite script using OpenAI."""
        
        try:
            import httpx
            
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                return self._fallback_script(topic)
            
            prompt = f"""Write a 45-second YouTube Short script about: {topic}

STRUCTURE (STRICT):
1. HOOK (first 3 seconds): Pattern interrupt. Must create open loop.
2. MECHANISM (10 sec): Explain the hidden system
3. PROOF (10 sec): Example or data point  
4. TWIST (10 sec): The thing they don't tell you
5. CTA (5 sec): Subscribe hook

RULES:
- 120 words MAX
- Short punchy sentences
- No fluff words
- Visual intent: {visual_intent}
- Target: 80%+ retention

Write ONLY the script, no labels or directions."""

            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={
                        "model": "gpt-4o-mini",
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 300,
                        "temperature": 0.8
                    }
                )
                
                if response.status_code == 200:
                    return response.json()["choices"][0]["message"]["content"].strip()
                    
        except Exception as e:
            self._log(f"[SCRIPT] OpenAI failed: {e}")
        
        return self._fallback_script(topic)
    
    def _fallback_script(self, topic: str) -> str:
        """Fallback script if OpenAI fails."""
        return f"""Here's what they don't want you to know about {topic}.

The system is designed this way for a reason.
And once you see it, you can't unsee it.

Most people will ignore this.
But if you're watching this, you're not most people.

The wealthy understand this.
The poor never learn it.

Which side will you be on?

Follow for more truths they hide from you."""
    
    async def _generate_audio(self, script: str) -> Optional[str]:
        """Generate audio using ElevenLabs or edge-tts."""
        
        audio_path = AUDIO_DIR / f"job_{self.job_id}.mp3"
        
        # Try ElevenLabs first
        elevenlabs_key = os.getenv("ELEVENLABS_API_KEY")
        if elevenlabs_key:
            try:
                import httpx
                
                async with httpx.AsyncClient(timeout=60) as client:
                    response = await client.post(
                        "https://api.elevenlabs.io/v1/text-to-speech/pNInz6obpgDQGcFmaJgB",
                        headers={
                            "xi-api-key": elevenlabs_key,
                            "Content-Type": "application/json"
                        },
                        json={
                            "text": script,
                            "model_id": "eleven_monolingual_v1",
                            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
                        }
                    )
                    
                    if response.status_code == 200:
                        audio_path.write_bytes(response.content)
                        self._log(f"[AUDIO] ElevenLabs success: {audio_path}")
                        return str(audio_path)
                        
            except Exception as e:
                self._log(f"[AUDIO] ElevenLabs failed: {e}")
        
        # Fallback to edge-tts
        try:
            cmd = f'edge-tts --voice en-US-AndrewNeural --text "{script[:4000]}" --write-media "{audio_path}"'
            process = await asyncio.create_subprocess_shell(
                cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            
            if audio_path.exists():
                self._log(f"[AUDIO] Edge-TTS success: {audio_path}")
                return str(audio_path)
                
        except Exception as e:
            self._log(f"[AUDIO] Edge-TTS failed: {e}")
        
        return None
    
    async def _build_elite_video(
        self, 
        audio_path: str, 
        script: str, 
        topic: str,
        visual_intent: str
    ) -> Optional[str]:
        """Build elite video using scene-based cutting."""
        
        output_path = OUTPUT_DIR / f"elite_{self.job_id}.mp4"
        
        try:
            # Use elite builder with AAVE DNA
            config = BuildConfig(
                target_bitrate="8M",
                max_bitrate="10M",
                crf=18,
                min_scene_duration=1.2,
                max_scene_duration=2.8,
                enable_zoompan=True,
                enable_color_grade=True,
                contrast=1.08,
                saturation=1.12
            )
            
            builder = EliteVideoBuilder(config)
            result = await builder.build(
                audio_path=audio_path,
                script=script,
                topic=topic,
                output_path=str(output_path)
            )
            
            if Path(result).exists():
                self._log(f"[VIDEO] Elite build success: {result}")
                return result
                
        except Exception as e:
            self._log(f"[VIDEO] Elite builder failed: {e}, trying fallback")
        
        # Fallback to simple video builder
        try:
            result = await build_video(audio_path, str(OUTPUT_DIR))
            self._log(f"[VIDEO] Fallback build success: {result}")
            return result
        except Exception as e:
            self._log(f"[VIDEO] All builds failed: {e}")
            return None
    
    def _quality_check(self, video_path: str) -> tuple:
        """Run quality gate checks."""
        
        passed, report = validate_visual_entropy(video_path, min_bitrate=6_000_000)
        
        # Additional checks
        try:
            cmd = f'ffprobe -v error -show_entries format=duration,bit_rate -of json "{video_path}"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            data = json.loads(result.stdout)
            fmt = data.get("format", {})
            
            report["duration"] = float(fmt.get("duration", 0))
            report["bitrate"] = int(fmt.get("bit_rate", 0))
            
            # Check Hollywood standards
            if report["bitrate"] < 6_000_000:
                passed = False
                report["fail_reason"] = "Bitrate below 6 Mbps"
            elif report["duration"] < 15:
                passed = False
                report["fail_reason"] = "Duration under 15 seconds"
            elif report["duration"] > 60:
                passed = False
                report["fail_reason"] = "Duration over 60 seconds for Short"
                
        except Exception as e:
            report["quality_check_error"] = str(e)
        
        return passed, report
    
    async def _upload_youtube(
        self, 
        video_path: str, 
        topic: str, 
        script: str
    ) -> Dict[str, Any]:
        """Upload to YouTube."""
        
        title = topic[:100]
        description = f"""{script[:500]}

🔔 Subscribe for daily wealth insights
📈 Follow the Money Machine

#shorts #money #wealth #finance #investing"""
        
        tags = ["shorts", "money", "wealth", "finance", "investing", "rich", "success"]
        
        result = await self.youtube.upload_short(
            video_path=video_path,
            title=title,
            description=description,
            tags=tags,
            privacy="public"
        )
        
        if result.get("success"):
            video_id = result.get("video_id")
            return {"url": f"https://youtube.com/shorts/{video_id}", "video_id": video_id}
        
        return {"error": result.get("error", "Upload failed")}
    
    def _infer_visual_intent(self, topic: str) -> str:
        """Infer visual intent from topic."""
        
        topic_lower = topic.lower()
        
        if any(w in topic_lower for w in ["rich", "wealth", "millionaire", "billionaire"]):
            return "luxury_wealth"
        elif any(w in topic_lower for w in ["debt", "credit", "loan", "bank"]):
            return "power_finance"
        elif any(w in topic_lower for w in ["system", "rigged", "control", "hidden"]):
            return "system_expose"
        elif any(w in topic_lower for w in ["poor", "broke", "struggle", "class"]):
            return "class_divide"
        elif any(w in topic_lower for w in ["future", "collapse", "warning", "2025"]):
            return "future_threat"
        else:
            return "power_finance"
    
    def _extract_dna(
        self, 
        topic: str, 
        visual_intent: str, 
        script: str,
        report: Dict
    ) -> Dict[str, Any]:
        """Extract DNA from video for AAVE evolution."""
        
        return {
            "topic": topic,
            "visual_intent": visual_intent,
            "word_count": len(script.split()),
            "bitrate": report.get("bitrate", 0),
            "duration": report.get("duration", 0),
            "hook_type": self._detect_hook_type(script),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "job_id": self.job_id
        }
    
    def _detect_hook_type(self, script: str) -> str:
        """Detect hook archetype from script."""
        
        first_sentence = script.split('.')[0].lower() if script else ""
        
        if "don't" in first_sentence or "never" in first_sentence:
            return "contrarian_fear"
        elif "secret" in first_sentence or "hidden" in first_sentence:
            return "system_reveal"
        elif "truth" in first_sentence or "lie" in first_sentence:
            return "myth_destruction"
        elif "?" in first_sentence:
            return "curiosity_gap"
        else:
            return "threat"
    
    def _log_dna(self, dna: Dict[str, Any]):
        """Log DNA to file for AAVE."""
        
        dna_file = DNA_DIR / "pool.json"
        
        try:
            pool = json.loads(dna_file.read_text()) if dna_file.exists() else []
        except:
            pool = []
        
        pool.append(dna)
        
        # Keep last 1000 entries
        pool = pool[-1000:]
        
        dna_file.write_text(json.dumps(pool, indent=2))
    
    def _log(self, message: str):
        """Log message to file and stdout."""
        
        log_file = LOGS_DIR / f"jobs_{datetime.now().strftime('%Y%m%d')}.log"
        timestamp = datetime.now().isoformat()
        
        line = f"[{timestamp}] {message}"
        print(line)
        
        with open(log_file, "a") as f:
            f.write(line + "\n")
    
    def _check_ffmpeg(self) -> bool:
        """Check if FFmpeg is available."""
        try:
            result = subprocess.run(["ffmpeg", "-version"], capture_output=True)
            return result.returncode == 0
        except:
            return False
    
    def _count_broll(self) -> int:
        """Count available B-roll files."""
        broll_dir = PROJECT_ROOT / "data" / "assets" / "backgrounds"
        if not broll_dir.exists():
            return 0
        
        count = 0
        for ext in ['*.mp4', '*.mov', '*.webm']:
            count += len(list(broll_dir.rglob(ext)))
        return count


# ============================================================
# CLI INTERFACE
# ============================================================

def parse_args():
    parser = argparse.ArgumentParser(description="Money Machine Job Executor")
    parser.add_argument("--json", type=str, help="JSON payload")
    parser.add_argument("--stdin", action="store_true", help="Read JSON from stdin")
    parser.add_argument("--mode", type=str, default="shorts", 
                       choices=["shorts", "longform", "replicate", "analytics", "health"])
    parser.add_argument("--topic", type=str, help="Override topic")
    parser.add_argument("--force-upload", action="store_true", help="Upload even if quality gate fails")
    parser.add_argument("--no-upload", action="store_true", help="Don't upload, save locally only")
    return parser.parse_args()


async def main():
    args = parse_args()
    
    # Build payload
    if args.json:
        payload = json.loads(args.json)
    elif args.stdin:
        payload = json.loads(sys.stdin.read())
    else:
        payload = {
            "mode": args.mode,
            "topic": args.topic,
            "force_upload": args.force_upload and not args.no_upload
        }
    
    # Execute job
    executor = JobExecutor()
    result = await executor.execute(payload)
    
    # Output JSON result
    print("\n" + "="*60)
    print("JOB RESULT:")
    print("="*60)
    print(json.dumps(result, indent=2))
    
    return result


if __name__ == "__main__":
    asyncio.run(main())
