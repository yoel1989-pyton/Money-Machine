#!/usr/bin/env python3
"""
============================================================
MONEY MACHINE AI - SOVEREIGN MEDIA ENGINE
============================================================
THE DISTRIBUTED, SELF-HEALING MEDIA SYSTEM

This is the final form. You don't post videos.
You run an organism.

Modes:
    --continuous    : Run forever (30 min shorts, 6 hr longform)
    --shorts        : Single short, save locally
    --longform      : Single documentary
    --health        : System check
    --local-only    : No upload, save files for playback

Example:
    python SOVEREIGN.py --continuous           # Full autonomous
    python SOVEREIGN.py --shorts --local-only  # Test locally
    python SOVEREIGN.py --health               # Check status
============================================================
"""

import os
import sys
import json
import asyncio
import argparse
import signal
import shutil
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List

# Fix Windows terminal encoding for emojis
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass  # Older Python or pipe mode

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env", override=True)

# Import engines
from engines.aave_engine import AAVEEngine, VisualDNA
from engines.elite_builder import EliteVideoBuilder, BuildConfig
from engines.video_builder import build_video, validate_visual_entropy
from engines.uploaders import YouTubeUploader
from engines.quality_gates import QualityGate

# Cinematic scene-based production (Hollywood mode)
try:
    from engines.cinematic_planner import CinematicScenePlanner, script_to_scene_prompts
    from engines.visual_engine import VisualEngine, generate_scene_visuals
    from engines.scene_stitcher import SceneStitcher, stitch_scenes_to_video
    HAS_CINEMATIC = True
except ImportError as e:
    print(f"⚠️ Cinematic mode not available: {e}")
    HAS_CINEMATIC = False

# Hollywood scene-based production (multi-provider)
try:
    from engines.hollywood_planner import HollywoodPlanner, create_hollywood_plan
    from engines.visual_adapters import HollywoodVisualFactory
    from engines.hollywood_assembler import HollywoodAssembler, assemble_hollywood_video
    HAS_HOLLYWOOD = True
except ImportError as e:
    print(f"⚠️ Hollywood mode not available: {e}")
    HAS_HOLLYWOOD = False

# Try to import longform
try:
    from engines.longform_builder import LongformDocumentaryBuilder
    HAS_LONGFORM = True
except ImportError:
    HAS_LONGFORM = False

# Gemini Trust Module (algorithm-native signals)
try:
    from engines.gemini_trust import GeminiTrustModule
    HAS_GEMINI_TRUST = True
except ImportError:
    HAS_GEMINI_TRUST = False

# Visual Grounding & Adaptive Narration (semantic intelligence layer)
try:
    from engines.visual_grounding import build_visual_plan, GroundedVisual
    from engines.adaptive_narration import full_script_mutation
    from engines.retention_analyzer import detect_drop_off, analyze_retention_pattern
    from engines.auto_mode_selector import select_visual_mode, ModeDecision
    HAS_VISUAL_GROUNDING = True
except ImportError as e:
    print(f"⚠️ Visual grounding not available: {e}")
    HAS_VISUAL_GROUNDING = False

# Directories
OUTPUT_DIR = PROJECT_ROOT / "data" / "output"
AUDIO_DIR = PROJECT_ROOT / "data" / "audio"
SCRIPTS_DIR = PROJECT_ROOT / "data" / "scripts"
DNA_DIR = PROJECT_ROOT / "data" / "dna"
LOGS_DIR = PROJECT_ROOT / "data" / "logs"
LOCAL_PLAYBACK_DIR = PROJECT_ROOT / "output" / "playback"

for d in [OUTPUT_DIR, AUDIO_DIR, SCRIPTS_DIR, DNA_DIR, LOGS_DIR, LOCAL_PLAYBACK_DIR]:
    d.mkdir(parents=True, exist_ok=True)


# ============================================================
# SOVEREIGN MEDIA ENGINE
# ============================================================

class SovereignMediaEngine:
    """
    The final form of the Money Machine AI.
    A distributed, self-healing media production system.
    """
    
    # Gold Standard Topics (injected from elite creators)
    ELITE_TOPICS = [
        # THREAT (Jake Tran style)
        {"topic": "The Hidden Tax Stealing Your Wealth Every Day", "weight": 1.0, "archetype": "threat", "visual": "surveillance"},
        {"topic": "Why Banks Want You Broke (And How They Do It)", "weight": 0.95, "archetype": "system_reveal", "visual": "power_finance"},
        {"topic": "You Will Own Nothing by 2030 (Here's Why)", "weight": 0.95, "archetype": "future_threat", "visual": "collapse"},
        
        # SYSTEM REVEAL (Minority Mindset style)
        {"topic": "Why the Rich Use Debt as a Weapon", "weight": 0.98, "archetype": "system_exploit", "visual": "luxury_wealth"},
        {"topic": "The Economy Is Rigged (Here's Proof)", "weight": 0.92, "archetype": "system_reveal", "visual": "class_divide"},
        {"topic": "Why the Middle Class Is Disappearing", "weight": 0.90, "archetype": "slow_burn_truth", "visual": "class_divide"},
        
        # AUTHORITY CONTRADICTION (Kiyosaki style)
        {"topic": "Cash Is Trash (Here's What the Rich Hold Instead)", "weight": 0.88, "archetype": "authority_contradiction", "visual": "power_finance"},
        {"topic": "Everything You Know About Money Is Wrong", "weight": 0.85, "archetype": "myth_destruction", "visual": "system_expose"},
        {"topic": "Why Saving Money Makes You Poorer", "weight": 0.85, "archetype": "contrarian_fear", "visual": "power_finance"},
        
        # PSYCHOLOGY (Deep patterns)
        {"topic": "The Psychology of Why You Stay Poor", "weight": 0.87, "archetype": "identity_trigger", "visual": "psychology"},
        {"topic": "How the Rich Think Differently About Money", "weight": 0.86, "archetype": "identity_trigger", "visual": "luxury_wealth"},
        {"topic": "The Wealth Transfer Happening Right Now", "weight": 0.90, "archetype": "urgency", "visual": "power_finance"},
        
        # MECHANISM (ColdFusion style)
        {"topic": "How Credit Cards Are Designed to Trap You", "weight": 0.83, "archetype": "mechanism", "visual": "power_finance"},
        {"topic": "The Federal Reserve Explained (Why It Matters)", "weight": 0.80, "archetype": "educational", "visual": "system_expose"},
        {"topic": "How Inflation Secretly Steals Your Wealth", "weight": 0.88, "archetype": "hidden_change", "visual": "power_finance"},
    ]
    
    # Hollywood Quality Standards
    QUALITY_SPEC = {
        "shorts": {
            "resolution": "1080x1920",
            "bitrate": "8M",
            "min_bitrate": 6_000_000,
            "fps": 30,
            "audio_bitrate": "192k",
            "min_duration": 15,
            "max_duration": 60,
            "scene_cuts": (1.2, 2.8),
        },
        "longform": {
            "resolution": "3840x2160",
            "bitrate": "18M",
            "min_bitrate": 12_000_000,
            "fps": 30,
            "audio_bitrate": "320k",
            "min_duration": 600,
            "max_duration": 1200,
        }
    }
    
    def __init__(self, local_only: bool = False, cinematic: bool = False, hollywood: bool = False,
                 visual_mode: str = "hybrid", auto_mode: bool = False, adaptive_narration: bool = False):
        self.aave = AAVEEngine()
        self.quality_gate = QualityGate()
        self.youtube = YouTubeUploader()
        self.local_only = local_only
        self.cinematic = cinematic and HAS_CINEMATIC  # Only enable if modules available
        self.hollywood = hollywood and HAS_HOLLYWOOD  # New Hollywood multi-provider mode
        self.running = True
        
        # Visual grounding & adaptive narration
        self.visual_mode = visual_mode
        self.auto_mode = auto_mode and HAS_VISUAL_GROUNDING
        self.adaptive_narration = adaptive_narration and HAS_VISUAL_GROUNDING
        
        self.stats = {
            "shorts_produced": 0,
            "shorts_uploaded": 0,
            "cinematic_produced": 0,
            "hollywood_produced": 0,
            "longform_produced": 0,
            "failures": 0,
            "started": datetime.now(timezone.utc).isoformat()
        }
        
        # Initialize Gemini Trust Module (algorithm-native signals)
        self.trust_module = None
        if HAS_GEMINI_TRUST:
            try:
                channel_id = os.getenv("YOUTUBE_CHANNEL_ID", "MoneyMachineAI")
                self.trust_module = GeminiTrustModule(channel_id=channel_id)
            except Exception as e:
                print(f"⚠️ Gemini Trust module init failed: {e}")
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        self._log("🛑 Shutdown signal received. Finishing current job...")
        self.running = False
    
    # ========================================================
    # MAIN PRODUCTION LOOPS
    # ========================================================
    
    async def run_continuous(self):
        """
        Run the sovereign media engine continuously.
        - Shorts every 30 minutes
        - Longform every 6 hours (winners only)
        """
        self._log("="*60)
        self._log("🚀 SOVEREIGN MEDIA ENGINE - ONLINE")
        self._log("="*60)
        self._log(f"Mode: {'LOCAL ONLY' if self.local_only else 'FULL PRODUCTION'}")
        self._log(f"YouTube: {'CONFIGURED' if self.youtube.is_configured() else 'NOT CONFIGURED'}")
        self._log("="*60)
        
        last_longform = datetime.now(timezone.utc) - timedelta(hours=6)
        shorts_interval = 30 * 60  # 30 minutes
        longform_interval = 6 * 60 * 60  # 6 hours
        
        while self.running:
            try:
                # Check if longform is due
                time_since_longform = (datetime.now(timezone.utc) - last_longform).total_seconds()
                
                if time_since_longform >= longform_interval and HAS_LONGFORM:
                    self._log("\n" + "="*60)
                    self._log("📽️ LONGFORM PRODUCTION CYCLE")
                    self._log("="*60)
                    await self.produce_longform()
                    last_longform = datetime.now(timezone.utc)
                
                # Produce a short
                self._log("\n" + "="*60)
                self._log("🎬 SHORTS PRODUCTION CYCLE")
                self._log("="*60)
                await self.produce_short()
                
                # Wait for next cycle
                self._log(f"\n⏳ Next cycle in {shorts_interval // 60} minutes...")
                for _ in range(shorts_interval):
                    if not self.running:
                        break
                    await asyncio.sleep(1)
                    
            except Exception as e:
                self._log(f"❌ Cycle error: {e}")
                self.stats["failures"] += 1
                await asyncio.sleep(60)  # Wait 1 min on error
        
        self._log("\n" + "="*60)
        self._log("🛑 SOVEREIGN ENGINE - SHUTDOWN")
        self._log(f"Stats: {json.dumps(self.stats, indent=2)}")
        self._log("="*60)
    
    async def produce_short(self, topic: str = None) -> Dict[str, Any]:
        """Produce a single elite YouTube Short."""
        
        job_id = f"short_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 1. Select topic (AAVE weighted)
        if not topic:
            topic_data = self._select_elite_topic()
            topic = topic_data["topic"]
            visual_intent = topic_data["visual"]
            archetype = topic_data["archetype"]
        else:
            visual_intent = "power_finance"
            archetype = "threat"
        
        self._log(f"📌 Topic: {topic}")
        self._log(f"🎨 Visual: {visual_intent} | Archetype: {archetype}")
        
        # 2. Generate script
        script = await self._generate_script(topic, visual_intent)
        
        # 2.5. Adaptive narration - mutate script based on performance data
        if self.adaptive_narration and HAS_VISUAL_GROUNDING:
            try:
                original_len = len(script)
                mutated_script = full_script_mutation(
                    script=script,
                    drop_off_points=None,  # Auto-detect weak points
                    trust_score=0.5,  # Neutral starting point
                    add_hooks=True
                )
                mutations = abs(len(mutated_script) - original_len)
                if mutations > 10:
                    script = mutated_script
                    self._log(f"🔄 Adaptive narration: Script optimized (+{mutations} chars)")
            except Exception as e:
                self._log(f"⚠️ Adaptive narration failed: {e}")
        
        script_path = SCRIPTS_DIR / f"{job_id}.txt"
        script_path.write_text(script)
        self._log(f"📝 Script: {len(script.split())} words")
        
        # 3. Generate audio
        audio_path = await self._generate_audio(script, job_id)
        if not audio_path:
            return {"status": "FAILED", "error": "Audio generation failed"}
        self._log(f"🔊 Audio: {audio_path}")
        
        # 4. Build video (HOLLYWOOD, CINEMATIC, or ELITE mode)
        if self.hollywood:
            self._log("🎬 Using HOLLYWOOD mode (multi-provider scene-based)")
            video_path = await self._build_hollywood_video(audio_path, script, topic, archetype, job_id)
        elif self.cinematic:
            self._log("🎬 Using CINEMATIC mode (scene-based AI visuals)")
            video_path = await self._build_cinematic_video(audio_path, script, topic, archetype, job_id)
        else:
            video_path = await self._build_elite_video(audio_path, script, topic, visual_intent, job_id)
        
        if not video_path:
            return {"status": "FAILED", "error": "Video build failed"}
        self._log(f"🎥 Video: {video_path}")
        
        # 5. Quality check
        passed, report = self._quality_check(video_path, "shorts")
        if not passed:
            self._log(f"❌ Quality check failed: {report.get('fail_reason', 'Unknown')}")
            self.stats["failures"] += 1
            return {"status": "FAILED", "error": "Quality gate failed", "report": report}
        
        self._log(f"✅ Quality: {report['bitrate']/1_000_000:.1f} Mbps, {report['duration']:.1f}s")
        
        # 6. Save locally for playback
        local_path = self._save_for_playback(video_path, topic, job_id)
        self._log(f"💾 Local: {local_path}")
        
        # 7. Upload (if not local-only)
        youtube_url = None
        if not self.local_only and self.youtube.is_configured():
            upload_result = await self._upload_youtube(video_path, topic, script)
            youtube_url = upload_result.get("url")
            if youtube_url:
                self._log(f"📺 YouTube: {youtube_url}")
                self.stats["shorts_uploaded"] += 1
        
        # 8. Log DNA
        production_mode = "hollywood" if self.hollywood else ("cinematic" if self.cinematic else "elite")
        dna = {
            "topic": topic,
            "visual_intent": visual_intent,
            "archetype": archetype,
            "mode": production_mode,
            "bitrate": report.get("bitrate", 0),
            "duration": report.get("duration", 0),
            "youtube_url": youtube_url,
            "local_path": str(local_path),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self._log_dna(dna)
        
        self.stats["shorts_produced"] += 1
        if self.hollywood:
            self.stats["hollywood_produced"] += 1
        elif self.cinematic:
            self.stats["cinematic_produced"] += 1
        
        # 9. Send notification
        mode_icon = "🎥" if self.hollywood else ("🎬" if self.cinematic else "⚡")
        await self._notify_telegram(
            f"{mode_icon} SHORT PRODUCED\n\n📌 {topic}\n\n📺 {youtube_url or 'Local only'}\n💾 {local_path.name}"
        )
        
        # 10. Generate Gemini Trust metadata
        trust_data = {}
        if self.trust_module:
            try:
                trust_data = self.trust_module.full_trust_check(
                    title=topic,
                    script=script,
                    description=f"Deep dive into {topic}"
                )
                if trust_data.get("passed"):
                    self._log(f"✅ Trust check passed: {trust_data['satisfaction']['overall']:.2f}")
                else:
                    self._log(f"⚠️ Trust check: {trust_data['satisfaction']['overall']:.2f}")
            except Exception as e:
                self._log(f"⚠️ Trust check failed: {e}")
        
        # Generate description with hashtags
        description = self._generate_description(topic, script, visual_intent)
        tags = self._generate_tags(topic, visual_intent, trust_data)
        
        return {
            "status": "SUCCESS",
            "job_id": job_id,
            "topic": topic,
            "title": topic,  # n8n uses this
            "description": description,
            "tags": tags,
            "mode": "hollywood" if self.hollywood else ("cinematic" if self.cinematic else "elite"),
            "video_path": str(video_path),
            "local_path": str(local_path),
            "youtube_url": youtube_url,
            "bitrate": report.get("bitrate"),
            "bitrate_mbps": round(report.get("bitrate", 0) / 1_000_000, 2),
            "duration": report.get("duration"),
            "word_count": len(script.split()),
            "archetype": archetype,
            "visual_intent": visual_intent,
            "providers_used": dna.get("providers_used", []),
            "styles_used": dna.get("styles_used", []),
            "scene_count": dna.get("scene_count", 0),
            "trust_score": trust_data.get("satisfaction", {}).get("overall", 0),
            "viewer_model": trust_data.get("viewer_model", {}).get("detected", "unknown"),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def produce_longform(self, topic: str = None) -> Dict[str, Any]:
        """Produce a 4K documentary from winner DNA."""
        
        if not HAS_LONGFORM:
            return {"status": "SKIPPED", "reason": "Longform builder not available"}
        
        job_id = f"longform_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Select winner topic
        if not topic:
            winners = self._get_winners()
            if not winners:
                return {"status": "SKIPPED", "reason": "No winners to expand"}
            topic = winners[0]["topic"]
        
        self._log(f"📽️ Longform Topic: {topic}")
        
        try:
            builder = LongformDocumentaryBuilder()
            result = await builder.build(topic=topic)
            
            if result.get("success"):
                video_path = result["video_path"]
                local_path = self._save_for_playback(video_path, topic, job_id, "longform")
                
                # Upload if configured
                youtube_url = None
                if not self.local_only and self.youtube.is_configured():
                    upload_result = await self.youtube.upload_short(
                        video_path=video_path,
                        title=f"Documentary: {topic}"[:100],
                        description=f"Full documentary on {topic}\n\n#documentary #wealth #finance",
                        privacy="public"
                    )
                    youtube_url = upload_result.get("url")
                
                self.stats["longform_produced"] += 1
                
                await self._notify_telegram(
                    f"📽️ DOCUMENTARY PRODUCED\n\n📌 {topic}\n\n📺 {youtube_url or 'Local only'}\n💾 {local_path.name}"
                )
                
                return {
                    "status": "SUCCESS",
                    "job_id": job_id,
                    "topic": topic,
                    "video_path": str(video_path),
                    "local_path": str(local_path),
                    "youtube_url": youtube_url
                }
            else:
                return {"status": "FAILED", "error": result.get("error", "Build failed")}
                
        except Exception as e:
            self._log(f"❌ Longform error: {e}")
            return {"status": "FAILED", "error": str(e)}
    
    def check_health(self) -> Dict[str, Any]:
        """Check system health."""
        
        # Check visual API availability
        visual_apis = {
            "stability_ai": bool(os.getenv("STABILITY_API_KEY")),
            "replicate": bool(os.getenv("REPLICATE_API_TOKEN")),
            "runway": bool(os.getenv("RUNWAYML_API_KEY")),
        }
        
        checks = {
            "youtube_configured": self.youtube.is_configured(),
            "ffmpeg_available": self._check_ffmpeg(),
            "output_dir_writable": OUTPUT_DIR.exists() and os.access(OUTPUT_DIR, os.W_OK),
            "broll_available": self._count_broll() > 0,
            "broll_count": self._count_broll(),
            "aave_active": True,
            "topics_loaded": len(self.ELITE_TOPICS),
            "longform_available": HAS_LONGFORM,
            "cinematic_available": HAS_CINEMATIC,
            "visual_apis": visual_apis,
            "visual_apis_active": sum(visual_apis.values()),
        }
        
        all_healthy = all([
            checks["ffmpeg_available"],
            checks["output_dir_writable"],
            checks["broll_available"] or checks["visual_apis_active"] > 0
        ])
        
        return {
            "status": "HEALTHY" if all_healthy else "DEGRADED",
            "mode": "cinematic" if self.cinematic else "elite",
            "checks": checks,
            "stats": self.stats,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    # ========================================================
    # HELPER METHODS
    # ========================================================
    
    def _select_elite_topic(self) -> Dict:
        """Select topic using weighted random selection."""
        import random
        
        total_weight = sum(t["weight"] for t in self.ELITE_TOPICS)
        r = random.random() * total_weight
        
        for topic in self.ELITE_TOPICS:
            r -= topic["weight"]
            if r <= 0:
                return topic
        
        return self.ELITE_TOPICS[0]
    
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
            self._log(f"Script generation error: {e}")
        
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
    
    async def _generate_audio(self, script: str, job_id: str) -> Optional[str]:
        """Generate audio using ElevenLabs or edge-tts."""
        
        audio_path = AUDIO_DIR / f"{job_id}.mp3"
        
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
                        return str(audio_path)
                        
            except Exception as e:
                self._log(f"ElevenLabs failed: {e}")
        
        # Fallback to edge-tts using Python module (not CLI)
        try:
            import edge_tts
            
            communicate = edge_tts.Communicate(script[:4000], "en-US-AndrewNeural")
            await communicate.save(str(audio_path))
            
            if audio_path.exists():
                self._log(f"🔊 Audio generated via edge-tts")
                return str(audio_path)
                
        except Exception as e:
            self._log(f"Edge-TTS module failed: {e}")
        
        # Final fallback: gTTS
        try:
            from gtts import gTTS
            tts = gTTS(text=script[:4000], lang='en')
            tts.save(str(audio_path))
            if audio_path.exists():
                self._log(f"🔊 Audio generated via gTTS")
                return str(audio_path)
        except Exception as e:
            self._log(f"gTTS failed: {e}")
        
        return None
    
    async def _build_elite_video(
        self, 
        audio_path: str, 
        script: str, 
        topic: str,
        visual_intent: str,
        job_id: str
    ) -> Optional[str]:
        """Build elite video with ENFORCED Hollywood bitrate."""
        
        output_path = OUTPUT_DIR / f"{job_id}.mp4"
        
        # Use the direct build_video which has enforced bitrate settings
        # This guarantees 8 Mbps with minrate 6M
        try:
            result = await build_video(audio_path, str(OUTPUT_DIR))
            if Path(result).exists():
                # Rename to match our job_id
                final_path = OUTPUT_DIR / f"{job_id}.mp4"
                Path(result).rename(final_path)
                return str(final_path)
        except Exception as e:
            self._log(f"Direct build failed: {e}, trying elite builder")
        
        # Fallback to elite builder
        try:
            config = BuildConfig(
                target_bitrate="8M",
                max_bitrate="10M",
                min_bitrate="6M",
                crf=16,  # Lower CRF for higher quality
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
                return result
                
        except Exception as e:
            self._log(f"Elite builder also failed: {e}")
            return None
    
    async def _build_cinematic_video(
        self,
        audio_path: str,
        script: str,
        topic: str,
        archetype: str,
        job_id: str
    ) -> Optional[str]:
        """
        Build video using SCENE-BASED VISUAL GENERATION.
        
        This is the Hollywood method:
        1. Split script into scenes
        2. Generate unique AI visual for each scene
        3. Add Ken Burns motion to each scene
        4. Stitch scenes together with audio
        
        Result: Every 1.5-3 seconds is a NEW visual = high entropy = algorithm loves it
        """
        
        if not HAS_CINEMATIC:
            self._log("⚠️ Cinematic mode not available, falling back to elite builder")
            return await self._build_elite_video(audio_path, script, topic, "power_finance", job_id)
        
        output_path = OUTPUT_DIR / f"{job_id}_cinematic.mp4"
        
        try:
            # Step 1: Plan scenes from script
            self._log("🎬 Scene Planning: Splitting script into visual scenes...")
            planner = CinematicScenePlanner()
            
            # Get audio duration for timing
            import subprocess
            result = subprocess.run([
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "json", audio_path
            ], capture_output=True, text=True)
            audio_duration = float(json.loads(result.stdout)["format"]["duration"])
            
            scene_plan = planner.plan_scenes(
                script=script,
                topic=topic,
                archetype=archetype,
                total_duration=audio_duration,
                video_id=job_id
            )
            
            self._log(f"📋 Planned {len(scene_plan.scenes)} scenes ({scene_plan.total_duration:.1f}s)")
            
            # Step 2: Generate unique visuals for each scene
            self._log("🎨 Generating AI visuals for each scene...")
            visual_engine = VisualEngine()
            
            scene_prompts = planner.get_visual_prompts(scene_plan)
            visual_results = await visual_engine.generate_all_scene_visuals(
                scenes=scene_prompts,
                video_id=job_id,
                parallel=3  # Limit concurrent API calls
            )
            
            # Collect successful visuals
            scene_images = [r.path for r in visual_results if r.success and r.path]
            providers_used = set(r.provider for r in visual_results if r.success)
            
            self._log(f"✅ Generated {len(scene_images)}/{len(scene_prompts)} scene visuals")
            self._log(f"🎯 Providers used: {', '.join(providers_used)}")
            
            if len(scene_images) < 5:
                self._log("⚠️ Too few scenes generated, falling back to elite builder")
                return await self._build_elite_video(audio_path, script, topic, "power_finance", job_id)
            
            # Step 3: Stitch scenes with motion and audio
            self._log("🎬 Stitching scenes with Ken Burns motion...")
            stitcher = SceneStitcher()
            
            stitch_result = await stitcher.stitch_scenes(
                scene_images=scene_images,
                audio_path=audio_path,
                output_path=str(output_path),
                video_id=job_id
            )
            
            if stitch_result.success:
                self._log(f"✅ Cinematic video created: {stitch_result.scene_count} scenes, {stitch_result.unique_visuals} unique visuals")
                
                # Log cinematic DNA for AAVE
                self._log_cinematic_dna(job_id, scene_plan, visual_results, providers_used)
                
                return stitch_result.video_path
            else:
                self._log(f"❌ Stitch failed: {stitch_result.error}")
                return await self._build_elite_video(audio_path, script, topic, "power_finance", job_id)
                
        except Exception as e:
            self._log(f"❌ Cinematic build failed: {e}")
            return await self._build_elite_video(audio_path, script, topic, "power_finance", job_id)
    
    async def _build_hollywood_video(
        self,
        audio_path: str,
        script: str,
        topic: str,
        archetype: str,
        job_id: str,
        retry_count: int = 0,
        force_mutation: bool = False
    ) -> Optional[str]:
        """
        Build video using HOLLYWOOD MULTI-PROVIDER system with auto-regeneration.
        
        This is the elite Hollywood method:
        1. Split script into beats (scenes)
        2. Rotate through ALL paid providers (Leonardo, Runway, Fal, Replicate, etc)
        3. Generate unique visual per scene with style rotation
        4. Add motion to each scene
        5. Assemble with GPU-accelerated NVENC encoding (AV1/H.264)
        6. AUTO-REGENERATE on quality fail with different styles
        
        Result: Every scene is different provider + different style = maximum entropy
        """
        
        MAX_RETRIES = 2
        
        if not HAS_HOLLYWOOD:
            self._log("⚠️ Hollywood mode not available, trying cinematic...")
            if HAS_CINEMATIC:
                return await self._build_cinematic_video(audio_path, script, topic, archetype, job_id)
            return await self._build_elite_video(audio_path, script, topic, "power_finance", job_id)
        
        # Use different job_id for retries to avoid file conflicts
        actual_job_id = f"{job_id}_r{retry_count}" if retry_count > 0 else job_id
        output_path = OUTPUT_DIR / f"{actual_job_id}_hollywood.mp4"
        
        try:
            # Step 1: Plan scenes with style/provider rotation
            self._log("🎬 Hollywood Scene Planning...")
            planner = HollywoodPlanner()
            
            # Force different styles on retry
            mutation_mode = "aggressive" if force_mutation or retry_count > 0 else "normal"
            
            # Auto mode selection based on performance data
            effective_visual_mode = self.visual_mode
            if self.auto_mode and HAS_VISUAL_GROUNDING:
                try:
                    mode_decision = select_visual_mode(
                        trust_score=0.5,  # Will be updated with real analytics
                        retention_curve=None,  # No historical data yet
                        avg_view_duration=0.5
                    )
                    effective_visual_mode = mode_decision.mode
                    self._log(f"🤖 Auto-selected visual mode: {effective_visual_mode} ({mode_decision.reasoning})")
                except Exception as e:
                    self._log(f"⚠️ Auto mode selection failed: {e}, using {self.visual_mode}")
            
            self._log(f"🎨 Visual grounding mode: {effective_visual_mode}")
            
            plan = planner.plan_from_script(
                script=script,
                title=topic,
                thesis=f"Elite content about {topic}",
                mode="shorts",
                visual_mode=effective_visual_mode
            )
            
            # Force style mutation on retry
            if mutation_mode == "aggressive":
                self._log("🔄 Mutation mode: Forcing different styles...")
                import random
                MUTATION_STYLES = ["cinematic", "anime", "abstract", "glitch", "motion", "documentary"]
                for scene in plan.scenes:
                    scene.style = random.choice([s for s in MUTATION_STYLES if s != scene.style])
            
            # Validate plan meets Hollywood standards
            is_valid, errors = planner.validate_plan(plan)
            if not is_valid:
                self._log(f"⚠️ Plan validation issues: {errors}")
            
            self._log(f"📋 Planned {len(plan.scenes)} scenes")
            self._log(f"🎨 Providers: {plan.provider_count} | Styles: {plan.style_count}")
            
            # Step 2: Generate visuals using ALL paid providers
            self._log("🎨 Generating multi-provider visuals...")
            factory = HollywoodVisualFactory()
            
            # Enable battle mode on retry for best quality
            use_battle = retry_count > 0
            
            results = await factory.generate_all_scenes(
                scenes=plan.scenes,
                video_id=actual_job_id,
                parallel=3,
                battle_mode=use_battle
            )
            
            # Count successes
            successful = [s for s in plan.scenes if s.generated]
            providers_used = set(s.provider for s in successful)
            
            self._log(f"✅ Generated {len(successful)}/{len(plan.scenes)} visuals")
            self._log(f"🎯 Providers: {', '.join(providers_used)}")
            
            if len(successful) < 5:
                self._log("⚠️ Too few scenes generated, falling back...")
                if HAS_CINEMATIC:
                    return await self._build_cinematic_video(audio_path, script, topic, archetype, job_id)
                return await self._build_elite_video(audio_path, script, topic, "power_finance", job_id)
            
            # Step 3: Assemble with GPU-accelerated Hollywood encoding
            self._log("🎬 Hollywood Assembly (GPU-accelerated)...")
            assembler = HollywoodAssembler(prefer_av1=True)
            
            # Log encoder info
            encoder_info = assembler._get_best_encoder()
            self._log(f"🖥️ Encoder: {encoder_info[0]}")
            
            result = await assembler.assemble(
                scenes=successful,
                audio_path=audio_path,
                output_path=str(output_path),
                video_id=actual_job_id
            )
            
            if result.success:
                self._log(f"✅ Hollywood video: {result.scene_count} scenes, {result.bitrate/1_000_000:.1f} Mbps")
                
                # QUALITY GATE - Auto-regenerate on failure
                if result.bitrate < 6_000_000:
                    self._log(f"⚠️ Quality gate: Bitrate {result.bitrate/1_000_000:.1f}M < 6M minimum")
                    
                    if retry_count < MAX_RETRIES:
                        self._log(f"🔄 Auto-regenerating (attempt {retry_count + 2}/{MAX_RETRIES + 1})...")
                        return await self._build_hollywood_video(
                            audio_path, script, topic, archetype, job_id,
                            retry_count=retry_count + 1,
                            force_mutation=True
                        )
                    else:
                        self._log("⚠️ Max retries reached, proceeding with current video")
                
                if len(providers_used) < 3 and retry_count < MAX_RETRIES:
                    self._log(f"⚠️ Quality gate: Only {len(providers_used)} providers (need 3+)")
                    
                    if retry_count < MAX_RETRIES:
                        self._log(f"🔄 Auto-regenerating for provider diversity...")
                        return await self._build_hollywood_video(
                            audio_path, script, topic, archetype, job_id,
                            retry_count=retry_count + 1,
                            force_mutation=True
                        )
                
                # Log Hollywood DNA
                self._log_hollywood_dna(job_id, plan, providers_used)
                
                return result.video_path
            else:
                self._log(f"❌ Assembly failed: {result.error}")
                
                # Try again with mutation
                if retry_count < MAX_RETRIES:
                    self._log(f"🔄 Assembly failed, retrying with mutation...")
                    return await self._build_hollywood_video(
                        audio_path, script, topic, archetype, job_id,
                        retry_count=retry_count + 1,
                        force_mutation=True
                    )
                
                return await self._build_elite_video(audio_path, script, topic, "power_finance", job_id)
                
        except Exception as e:
            self._log(f"❌ Hollywood build failed: {e}")
            if HAS_CINEMATIC:
                return await self._build_cinematic_video(audio_path, script, topic, archetype, job_id)
            return await self._build_elite_video(audio_path, script, topic, "power_finance", job_id)
    
    def _log_hollywood_dna(self, job_id: str, plan, providers_used):
        """Log Hollywood production DNA for AAVE learning."""
        try:
            dna = {
                "job_id": job_id,
                "type": "hollywood",
                "scene_count": len(plan.scenes),
                "provider_count": len(providers_used),
                "style_count": plan.style_count,
                "providers_used": list(providers_used),
                "styles": [s.style for s in plan.scenes],
                "intents": [s.visual_intent for s in plan.scenes],
                "emotional_arc": plan.emotional_arc,
                "quality_passed": plan.quality_passed,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            dna_file = DNA_DIR / "hollywood_dna.json"
            existing = json.loads(dna_file.read_text()) if dna_file.exists() else []
            if not isinstance(existing, list):
                existing = []
            existing.append(dna)
            existing = existing[-500:]
            dna_file.write_text(json.dumps(existing, indent=2))
        except:
            pass
    
    def _log_cinematic_dna(self, job_id: str, scene_plan, visual_results, providers_used):
        """Log cinematic production DNA for AAVE learning."""
        try:
            dna = {
                "job_id": job_id,
                "type": "cinematic",
                "scene_count": len(scene_plan.scenes),
                "unique_visuals": len([r for r in visual_results if r.success]),
                "providers_used": list(providers_used),
                "archetype": scene_plan.archetype,
                "intents": [s.intent for s in scene_plan.scenes],
                "styles": [s.style for s in scene_plan.scenes],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            dna_file = DNA_DIR / "cinematic_dna.json"
            existing = json.loads(dna_file.read_text()) if dna_file.exists() else []
            if not isinstance(existing, list):
                existing = []
            existing.append(dna)
            existing = existing[-500:]  # Keep last 500
            dna_file.write_text(json.dumps(existing, indent=2))
        except:
            pass

    def _quality_check(self, video_path: str, mode: str = "shorts") -> tuple:
        """Run quality gate checks."""
        import subprocess
        
        spec = self.QUALITY_SPEC[mode]
        
        try:
            cmd = f'ffprobe -v error -show_entries format=duration,bit_rate -of json "{video_path}"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            data = json.loads(result.stdout)
            fmt = data.get("format", {})
            
            duration = float(fmt.get("duration", 0))
            bitrate = int(fmt.get("bit_rate", 0))
            
            report = {
                "duration": duration,
                "bitrate": bitrate,
                "passed": True
            }
            
            # Check Hollywood standards
            if bitrate < spec["min_bitrate"]:
                report["passed"] = False
                report["fail_reason"] = f"Bitrate {bitrate/1e6:.1f} Mbps below {spec['min_bitrate']/1e6:.1f} Mbps"
            elif duration < spec["min_duration"]:
                report["passed"] = False
                report["fail_reason"] = f"Duration {duration:.1f}s under {spec['min_duration']}s"
            elif duration > spec["max_duration"]:
                report["passed"] = False
                report["fail_reason"] = f"Duration {duration:.1f}s over {spec['max_duration']}s"
            
            return report["passed"], report
            
        except Exception as e:
            return False, {"passed": False, "error": str(e)}
    
    def _generate_description(self, topic: str, script: str, visual_intent: str) -> str:
        """Generate YouTube description with spoken SEO and hashtags."""
        
        # Clean script excerpt
        script_excerpt = script[:400].strip()
        if len(script) > 400:
            script_excerpt += "..."
        
        # Get session end line if trust module available
        session_hook = ""
        if self.trust_module:
            session_hook = self.trust_module.get_session_end_line()
        
        description = f"""{script_excerpt}

{session_hook}

🔔 Subscribe for daily wealth insights
📈 Money Machine AI - Truth over motivation

#shorts #money #wealth #finance #investing #{visual_intent.replace('_', '')}"""
        
        return description
    
    def _generate_tags(self, topic: str, visual_intent: str, trust_data: dict = None) -> List[str]:
        """Generate optimized tags for YouTube."""
        
        base_tags = ["shorts", "money", "wealth", "finance", "investing", "rich", "success"]
        
        # Add topic-derived tags
        topic_words = [w.lower() for w in topic.split() if len(w) > 3]
        topic_tags = [w for w in topic_words if w not in ["the", "and", "for", "with", "that", "your"]][:5]
        
        # Add visual intent tag
        intent_tags = [visual_intent.replace("_", " ")]
        
        # Add viewer model tags if available
        viewer_tags = []
        if trust_data and trust_data.get("viewer_model", {}).get("recommended_tags"):
            viewer_tags = trust_data["viewer_model"]["recommended_tags"][:3]
        
        # Combine and dedupe
        all_tags = base_tags + topic_tags + intent_tags + viewer_tags
        return list(dict.fromkeys(all_tags))[:15]  # Max 15 tags, unique
    
    def _save_for_playback(
        self, 
        video_path: str, 
        topic: str, 
        job_id: str,
        subdir: str = "shorts"
    ) -> Path:
        """Save video to local playback folder."""
        
        playback_dir = LOCAL_PLAYBACK_DIR / subdir
        playback_dir.mkdir(parents=True, exist_ok=True)
        
        # Create clean filename from topic
        safe_topic = "".join(c for c in topic if c.isalnum() or c in " -_")[:50]
        filename = f"{job_id}_{safe_topic}.mp4"
        
        dest_path = playback_dir / filename
        shutil.copy2(video_path, dest_path)
        
        return dest_path
    
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
    
    async def _notify_telegram(self, message: str):
        """Send Telegram notification."""
        
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        if not bot_token or not chat_id:
            return
        
        try:
            import httpx
            
            async with httpx.AsyncClient(timeout=10) as client:
                await client.post(
                    f"https://api.telegram.org/bot{bot_token}/sendMessage",
                    json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
                )
        except:
            pass
    
    def _get_winners(self) -> List[Dict]:
        """Get winning topics from AAVE."""
        try:
            return self.aave.get_winners()[:5]
        except:
            return []
    
    def _log_dna(self, dna: Dict[str, Any]):
        """Log DNA to file."""
        
        dna_file = DNA_DIR / "pool.json"
        
        try:
            existing = json.loads(dna_file.read_text()) if dna_file.exists() else []
            # Handle if file contains a dict instead of array
            if isinstance(existing, dict):
                pool = [existing]
            elif isinstance(existing, list):
                pool = existing
            else:
                pool = []
        except:
            pool = []
        
        pool.append(dna)
        pool = pool[-1000:]  # Keep last 1000
        
        dna_file.write_text(json.dumps(pool, indent=2))
    
    def _log(self, message: str):
        """Log message."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{timestamp}] {message}"
        print(line)
        
        log_file = LOGS_DIR / f"sovereign_{datetime.now().strftime('%Y%m%d')}.log"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    
    def _check_ffmpeg(self) -> bool:
        """Check if FFmpeg is available."""
        import subprocess
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
# CLI
# ============================================================

async def main():
    parser = argparse.ArgumentParser(description="Money Machine AI - Sovereign Media Engine")
    parser.add_argument("--continuous", action="store_true", help="Run continuously (30 min shorts, 6 hr longform)")
    parser.add_argument("--shorts", action="store_true", help="Produce single short")
    parser.add_argument("--longform", action="store_true", help="Produce single longform documentary")
    parser.add_argument("--health", action="store_true", help="Check system health")
    parser.add_argument("--local-only", action="store_true", help="Save locally only, don't upload")
    parser.add_argument("--cinematic", action="store_true", help="Use CINEMATIC mode (AI-generated scene visuals)")
    parser.add_argument("--hollywood", action="store_true", help="Use HOLLYWOOD mode (multi-provider scene-based)")
    parser.add_argument("--topic", type=str, help="Override topic")
    parser.add_argument("--count", "-n", type=int, default=1, help="Number of videos to produce")
    parser.add_argument("--json-out", action="store_true", help="Output JSON only (for n8n integration)")
    parser.add_argument("--analytics", action="store_true", help="Run analytics scan")
    # Visual grounding & adaptive narration
    parser.add_argument("--visual-mode", choices=["word", "sentence", "hybrid"], default="hybrid",
                        help="Visual grounding mode: word (literal), sentence (balanced), hybrid (cinematic)")
    parser.add_argument("--auto", action="store_true", help="Auto-select visual mode based on performance data")
    parser.add_argument("--adaptive-narration", action="store_true", help="Enable self-healing script optimization")
    args = parser.parse_args()
    
    # Show mode status (suppress for json-out mode)
    if not args.json_out:
        if args.hollywood:
            if HAS_HOLLYWOOD:
                print("🎥 HOLLYWOOD MODE ENABLED - Multi-provider scene-based generation")
            else:
                print("⚠️ Hollywood modules not available, trying cinematic mode")
        elif args.cinematic:
            if HAS_CINEMATIC:
                print("🎬 CINEMATIC MODE ENABLED - Scene-based AI visual generation")
            else:
                print("⚠️ Cinematic modules not available, falling back to elite mode")
    
    # Analytics mode
    if args.analytics:
        try:
            from engines.analytics_engine import AnalyticsEngine
            analytics = AnalyticsEngine()
            report = await analytics.scan_performance()
            print(json.dumps(report.summary, indent=2))
        except ImportError:
            print(json.dumps({"error": "Analytics engine not available"}, indent=2))
        return
    
    engine = SovereignMediaEngine(
        local_only=args.local_only, 
        cinematic=args.cinematic,
        hollywood=args.hollywood,
        visual_mode=args.visual_mode,
        auto_mode=args.auto,
        adaptive_narration=args.adaptive_narration
    )
    
    if args.health:
        result = engine.check_health()
        result["cinematic_available"] = HAS_CINEMATIC
        result["hollywood_available"] = HAS_HOLLYWOOD
        result["visual_grounding_available"] = HAS_VISUAL_GROUNDING
        result["visual_mode"] = args.visual_mode
        result["auto_mode"] = args.auto
        result["adaptive_narration"] = args.adaptive_narration
        print(json.dumps(result, indent=2))
        return
    
    if args.shorts:
        results = []
        for i in range(args.count):
            if not args.json_out:
                print(f"\n{'='*60}")
            if engine.hollywood:
                mode_str = "HOLLYWOOD"
            elif engine.cinematic:
                mode_str = "CINEMATIC"
            else:
                mode_str = "ELITE"
            if not args.json_out:
                print(f"🎬 PRODUCING {mode_str} SHORT {i+1}/{args.count}")
                print(f"{'='*60}")
            result = await engine.produce_short(args.topic if i == 0 else None)
            results.append(result)
            if not args.json_out and result.get("status") == "SUCCESS":
                print(f"✅ Saved to: {result.get('local_path')}")
        
        # Log to analytics if available
        try:
            from engines.analytics_engine import AnalyticsEngine
            analytics = AnalyticsEngine()
            for result in results:
                if result.get("status") == "SUCCESS":
                    analytics.log_video_dna({
                        "title": result.get("title"),
                        "topic": result.get("topic"),
                        "archetype": result.get("archetype"),
                        "visual_intent": result.get("visual_intent"),
                        "providers_used": result.get("providers_used", []),
                        "styles_used": result.get("styles_used", []),
                        "word_count": result.get("word_count"),
                        "duration": result.get("duration")
                    })
        except ImportError:
            pass
        
        # Output results
        if args.json_out:
            # Clean output for n8n
            output = {
                "video_path": results[0].get("local_path") if results else None,
                "title": results[0].get("title") if results else None,
                "description": results[0].get("description") if results else None,
                "tags": results[0].get("tags", []) if results else [],
                "topic": results[0].get("topic") if results else None,
                "status": results[0].get("status") if results else "FAILED"
            }
            print(json.dumps(output))
        elif args.count == 1:
            print(json.dumps(results[0], indent=2))
        else:
            successes = sum(1 for r in results if r.get("status") == "SUCCESS")
            print(f"\n{'='*60}")
            print(f"📊 BATCH COMPLETE: {successes}/{args.count} succeeded")
            print(f"{'='*60}")
            print(json.dumps({"results": results, "success_rate": f"{successes}/{args.count}"}, indent=2))
        return
    
    if args.longform:
        result = await engine.produce_longform(args.topic)
        print(json.dumps(result, indent=2))
        return
    
    if args.continuous:
        await engine.run_continuous()
        return
    
    # Default: single short
    result = await engine.produce_short(args.topic)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
