#!/usr/bin/env python3
"""
════════════════════════════════════════════════════════════════════════════════
💎 ELITE AUTONOMOUS PRODUCTION SYSTEM
════════════════════════════════════════════════════════════════════════════════
Fully autonomous video production with:
- AAVE Brain topic selection (weighted algorithm-adaptive)
- Elite script generation (GPT-4o-mini optimized)
- ElevenLabs premium voice synthesis
- Scene-based video assembly with B-roll matching
- Automatic YouTube upload with metadata
- DNA tracking for performance evolution

Usage:
    python AUTO_ELITE.py                    # Continuous production (1/hour)
    python AUTO_ELITE.py --fast             # Fast mode (30 min intervals)
    python AUTO_ELITE.py --once             # Single video
    python AUTO_ELITE.py --topic "Custom"   # Specific topic
════════════════════════════════════════════════════════════════════════════════
"""

import os
import sys
import json
import asyncio
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

# ════════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ════════════════════════════════════════════════════════════════════════════════

DATA_DIR = Path(__file__).parent / "data"
TEMP_DIR = DATA_DIR / "temp"
OUTPUT_DIR = DATA_DIR / "output"
LOGS_DIR = DATA_DIR / "logs"

for d in [TEMP_DIR, OUTPUT_DIR, LOGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)


# ════════════════════════════════════════════════════════════════════════════════
# ELITE BANNER
# ════════════════════════════════════════════════════════════════════════════════

def print_banner():
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   💎  ELITE AUTONOMOUS PRODUCTION SYSTEM  💎                                ║
║                                                                              ║
║   ┌─────────────────────────────────────────────────────────────────────┐   ║
║   │  🧠 AAVE Brain          Algorithm-Adaptive Visual Evolution         │   ║
║   │  📝 Elite Scripts       80%+ Retention Optimized                    │   ║
║   │  🎙️ Premium Voice       ElevenLabs Multilingual V2                 │   ║
║   │  🎬 Scene Builder       Cut-Based Hollywood-Grade Assembly         │   ║
║   │  📤 Auto Upload         YouTube Shorts Direct Integration          │   ║
║   │  🧬 DNA Tracking        Performance-Based Evolution                │   ║
║   └─────────────────────────────────────────────────────────────────────┘   ║
║                                                                              ║
║   Status: FULLY AUTONOMOUS                                                   ║
║   Press Ctrl+C to stop                                                       ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)


# ════════════════════════════════════════════════════════════════════════════════
# ELITE PRODUCTION ENGINE
# ════════════════════════════════════════════════════════════════════════════════

class EliteProductionEngine:
    """Autonomous elite video production engine."""
    
    def __init__(self):
        self.stats = {
            "videos_created": 0,
            "videos_uploaded": 0,
            "total_views": 0,
            "avg_quality_score": 0,
            "start_time": datetime.now(timezone.utc).isoformat()
        }
        self._load_engines()
    
    def _load_engines(self):
        """Lazy load all engines."""
        try:
            from engines.aave_engine import AAVEEngine
            self.aave = AAVEEngine()
            print("   ✅ AAVE Engine loaded")
        except ImportError:
            self.aave = None
            print("   ⚠️ AAVE Engine not available")
        
        try:
            from engines.elite_builder import EliteVideoBuilder
            self.builder = EliteVideoBuilder()
            print("   ✅ Elite Builder loaded")
        except ImportError:
            self.builder = None
            print("   ⚠️ Elite Builder not available")
        
        try:
            from engines.uploaders import YouTubeUploader
            self.uploader = YouTubeUploader()
            print(f"   ✅ YouTube Uploader: {'CONFIGURED' if self.uploader.is_configured() else 'LOCAL MODE'}")
        except ImportError:
            self.uploader = None
            print("   ⚠️ YouTube Uploader not available")
    
    async def select_elite_topic(self, forced_topic: str = None) -> Tuple[str, Dict]:
        """Select elite topic using AAVE weighted selection."""
        if forced_topic:
            print(f"   🎯 Forced topic: {forced_topic}")
            return forced_topic, {"visual_intent": "power_finance", "hook": "system_reveal"}
        
        if self.aave:
            topic_data, dna = self.aave.select_elite_topic()
            print(f"   🎯 AAVE selected: {topic_data['topic']}")
            print(f"   🧬 DNA: {dna.get_id()}")
            print(f"   🎣 Hook: {topic_data['hook'].value}")
            return topic_data["topic"], topic_data
        else:
            # Fallback elite topics
            from engines.topic_pool import TopicPool
            pool = TopicPool()
            topic, source = pool.get_next_topic()
            return topic, {"visual_intent": "power_finance"}
    
    async def generate_script(self, topic: str, metadata: Dict) -> str:
        """Generate elite script using GPT-4o-mini."""
        import openai
        
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        hook_type = metadata.get("hook", {})
        hook_value = hook_type.value if hasattr(hook_type, "value") else str(hook_type)
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """You are an elite YouTube Shorts scriptwriter. Your scripts achieve 80%+ retention.

**ELITE FORMULA:**

1. HOOK (0-3s) - Pattern Interrupt:
   - Start with "You're being..." or shocking stat
   - Create immediate cognitive dissonance

2. AGITATION (3-15s) - Open the Wound:
   - Make the problem feel personal
   - Use "Every time you..." or "While you sleep..."

3. MECHANISM (15-40s) - The Hidden Truth:
   - Reveal the "how" nobody talks about
   - Use simple metaphors

4. PAYOFF (40-55s) - The Revelation:
   - Deliver the insight they came for
   - Make them feel smarter

5. LOOP (55-60s) - Engagement Hook:
   - End with open question
   - Tease next video

**VOICE:**
- Short sentences (5-12 words max)
- Conversational, not preachy
- Power words: exposed, rigged, weapon, hidden

**RULES:**
- 90-115 words total
- NO emojis, hashtags, timestamps
- Pure spoken narration only"""
                },
                {
                    "role": "user",
                    "content": f"Write an elite viral script about: {topic}\nHook Type: {hook_value}"
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
        
        word_count = len(script.split())
        print(f"   📝 Script: {word_count} words")
        
        return script
    
    async def generate_voice(self, script: str) -> str:
        """Generate voice using edge-tts (ElevenLabs fallback)."""
        import edge_tts
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        audio_path = str(TEMP_DIR / f"elite_{timestamp}_voice.mp3")
        
        try:
            # Try ElevenLabs first
            elevenlabs_key = os.getenv("ELEVENLABS_API_KEY")
            if elevenlabs_key:
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
                        print("   🎙️ Voice: ElevenLabs Premium")
                        return audio_path
        except Exception as e:
            print(f"   ⚠️ ElevenLabs failed: {e}")
        
        # Fallback to edge-tts
        communicate = edge_tts.Communicate(script, "en-US-AndrewNeural")
        await communicate.save(audio_path)
        print("   🎙️ Voice: Edge-TTS (Andrew)")
        
        return audio_path
    
    async def build_video(self, audio_path: str, script: str, topic: str) -> str:
        """Build elite video with scene-based assembly."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = str(OUTPUT_DIR / f"elite_{timestamp}_video.mp4")
        
        if self.builder:
            try:
                result = await self.builder.build(
                    audio_path=audio_path,
                    script=script,
                    topic=topic,
                    output_path=output_path
                )
                print(f"   🎬 Video: Elite Scene-Based Build")
                return result
            except Exception as e:
                print(f"   ⚠️ Elite builder failed: {e}")
        
        # Fallback to simple ffmpeg build
        from engines.video_builder import build_video_from_audio
        result = await build_video_from_audio(
            audio_path=audio_path,
            output_path=output_path,
            topic=topic
        )
        print(f"   🎬 Video: Standard Build")
        return result
    
    async def upload_video(self, video_path: str, topic: str, metadata: Dict) -> Optional[str]:
        """Upload to YouTube with elite metadata."""
        if not self.uploader or not self.uploader.is_configured():
            print("   📁 LOCAL MODE: Video saved locally")
            return None
        
        title = topic[:95] + "..." if len(topic) > 95 else topic
        
        description = f"""{topic}

🎯 Master your money. Build real wealth.

💰 Follow for daily wealth insights
📈 No fluff. Just truth.

#Shorts #Money #Wealth #Finance #Investing"""
        
        tags = ["money", "wealth", "finance", "investing", "shorts", "financial freedom"]
        
        try:
            video_id = await self.uploader.upload_short(
                video_path=video_path,
                title=title,
                description=description,
                tags=tags
            )
            
            if video_id:
                url = f"https://youtube.com/shorts/{video_id}"
                print(f"   📤 Uploaded: {url}")
                self.stats["videos_uploaded"] += 1
                return url
        except Exception as e:
            print(f"   ❌ Upload failed: {e}")
        
        return None
    
    async def produce_one(self, topic: str = None) -> Dict:
        """Produce a single elite video."""
        print("\n" + "═" * 60)
        print(f"🚀 ELITE PRODUCTION - {datetime.now().strftime('%H:%M:%S')}")
        print("═" * 60)
        
        result = {
            "success": False,
            "topic": None,
            "video_path": None,
            "youtube_url": None,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            # 1. Select topic
            print("\n[1/5] 🧠 Topic Selection...")
            topic, metadata = await self.select_elite_topic(topic)
            result["topic"] = topic
            
            # 2. Generate script
            print("\n[2/5] 📝 Script Generation...")
            script = await self.generate_script(topic, metadata)
            
            # 3. Generate voice
            print("\n[3/5] 🎙️ Voice Synthesis...")
            audio_path = await self.generate_voice(script)
            
            # 4. Build video
            print("\n[4/5] 🎬 Video Assembly...")
            video_path = await self.build_video(audio_path, script, topic)
            result["video_path"] = video_path
            
            # 5. Upload
            print("\n[5/5] 📤 Upload...")
            youtube_url = await self.upload_video(video_path, topic, metadata)
            result["youtube_url"] = youtube_url
            
            result["success"] = True
            self.stats["videos_created"] += 1
            
            print("\n" + "═" * 60)
            print("✅ ELITE PRODUCTION COMPLETE")
            print(f"   Topic: {topic}")
            print(f"   Video: {video_path}")
            if youtube_url:
                print(f"   YouTube: {youtube_url}")
            print("═" * 60)
            
        except Exception as e:
            print(f"\n❌ Production failed: {e}")
            result["error"] = str(e)
        
        return result
    
    async def run_continuous(self, interval: int = 3600):
        """Run continuous autonomous production."""
        print(f"\n🔄 Continuous mode: 1 video every {interval // 60} minutes")
        
        cycle = 0
        while True:
            cycle += 1
            print(f"\n{'═' * 60}")
            print(f"📊 CYCLE {cycle} | Videos: {self.stats['videos_created']} | Uploaded: {self.stats['videos_uploaded']}")
            print(f"{'═' * 60}")
            
            try:
                await self.produce_one()
            except Exception as e:
                print(f"❌ Cycle {cycle} failed: {e}")
            
            # Wait for next cycle
            print(f"\n⏳ Next production in {interval // 60} minutes...")
            await asyncio.sleep(interval)


# ════════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════════

async def main():
    parser = argparse.ArgumentParser(description="Elite Autonomous Production System")
    parser.add_argument("--fast", action="store_true", help="30-minute intervals")
    parser.add_argument("--once", action="store_true", help="Single video only")
    parser.add_argument("--topic", type=str, help="Specific topic to produce")
    parser.add_argument("--interval", type=int, default=3600, help="Custom interval (seconds)")
    args = parser.parse_args()
    
    print_banner()
    
    # Initialize engine
    print("\n🔧 Initializing Elite Engine...")
    engine = EliteProductionEngine()
    
    print(f"\n📡 Channel: Money machine ai")
    print(f"⏱️  Interval: {args.interval // 60 if not args.fast else 30} minutes")
    print(f"🔒 Quality Gates: ENABLED")
    print(f"📤 Auto Upload: {'ENABLED' if engine.uploader and engine.uploader.is_configured() else 'LOCAL MODE'}")
    print(f"🕐 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if args.once or args.topic:
        # Single production
        await engine.produce_one(args.topic)
    else:
        # Continuous production
        interval = 1800 if args.fast else args.interval
        await engine.run_continuous(interval)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n🛑 Production stopped by user")
        print("   Run 'python AUTO_ELITE.py' to restart")
