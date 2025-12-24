#!/usr/bin/env python3
"""
MONEY MACHINE AI - CONTINUOUS PRODUCTION MODE
==============================================
Creates and uploads Shorts automatically with all quality gates.

Usage:
    python workflows/continuous_mode.py              # Run once
    python workflows/continuous_mode.py --loop       # Run continuously
    python workflows/continuous_mode.py --loop --interval 3600  # Every hour
"""

import os
import sys
import json
import asyncio
import argparse
import random
from datetime import datetime, timezone
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from engines.quality_gates import (
    ScriptSanitizer,
    TTSProsody,
    VideoValidator,
    QualityGate,
    VisualFallback
)
from engines.creator import CreatorConfig
from engines.broll_engine import resolve_visual_intent


# DNA tracking for documentary expansion
try:
    from engines.dna_expander import get_expander
    HAS_DNA_TRACKING = True
except ImportError:
    HAS_DNA_TRACKING = False


# ============================================================
# TOPIC ROTATION
# ============================================================

# Import topic pool for self-rotating topics
from engines.topic_pool import TopicPool


class ContinuousMode:
    """Continuous production mode with quality gates."""
    
    def __init__(self):
        self.channel_id = os.getenv("YOUTUBE_CHANNEL_ID", "UCZppwcvPrWlAG0vb78elPJA")
        self.quality_gate = QualityGate()
        self.safe_mode = self.quality_gate.is_safe_mode_channel(self.channel_id)
        self.topic_pool = TopicPool()  # Self-rotating topic selection
        self.current_topic = None
        self.current_pool = None
        self.elite_mode = False  # Force elite topic selection
        self._forced_topic = None  # Override topic from CLI
        self._force_upload = False  # Upload even with quota warnings
        self.stats = {
            "created": 0,
            "uploaded": 0,
            "failed": 0,
            "quarantined": 0
        }
    
    def get_next_topic(self) -> str:
        """Get next topic from self-rotating pool."""
        # Check for forced topic first
        if self._forced_topic:
            self.current_topic = self._forced_topic
            self.current_pool = "forced"
            print(f"[FORCED] 🎯 Topic: {self.current_topic}")
            return self.current_topic
        
        if self.elite_mode:
            # Force elite topic from AAVE engine
            try:
                from engines.aave_engine import AAVEEngine, ELITE_TOPICS
                aave = AAVEEngine()
                topic_data, dna = aave.select_elite_topic()
                self.current_topic = topic_data["topic"]
                self.current_pool = "elite"
                print(f"[ELITE] 🎯 Topic: {self.current_topic}")
                print(f"[ELITE] 🧬 DNA ID: {dna.get_id()}")
                print(f"[ELITE] 🎣 Hook: {topic_data['hook'].value}")
                return self.current_topic
            except Exception as e:
                print(f"[ELITE] ⚠️ Fallback to regular pool: {e}")
        
        self.current_topic, self.current_pool = self.topic_pool.get_next_topic()
        return self.current_topic
    
    async def generate_script(self, topic: str) -> str:
        """Generate script using OpenAI."""
        import openai
        
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """Write a YouTube Short script.

Rules:
- One single paragraph
- Spoken naturally
- No line breaks
- No pauses
- No emojis
- No stage directions
- No capitalization gimmicks

Length: 90-120 words

Structure:
1. Pattern interrupt in first 10 words
2. Open loop
3. Clear explanation
4. One takeaway"""
                },
                {
                    "role": "user",
                    "content": f"Topic: {topic}"
                }
            ],
            temperature=0.6,
            max_tokens=180
        )
        
        script = response.choices[0].message.content
        return ScriptSanitizer.prepare_for_tts(script)
    
    async def generate_voice(self, script: str) -> str:
        """Generate voice with proper prosody."""
        import edge_tts
        
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        audio_path = str(CreatorConfig.TEMP_DIR / f"prod_{timestamp}_voice.mp3")
        
        prosody = TTSProsody.get_settings(self.channel_id)
        
        communicate = edge_tts.Communicate(
            script,
            "en-US-ChristopherNeural",
            rate=prosody["rate"],
            pitch=prosody["pitch"]
        )
        await communicate.save(audio_path)
        
        return audio_path
    
    async def assemble_video(self, audio_path: str, script: str = None) -> str:
        """Assemble video with guaranteed visuals matched to script."""
        import subprocess
        
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        output_path = str(CreatorConfig.OUTPUT_DIR / f"prod_{timestamp}_video.mp4")
        
        # Get background - ELITE: Pass script for visual intent matching
        bg_path = await VisualFallback.get_fallback_background(duration=60, script=script)
        
        # Get audio duration
        try:
            result = subprocess.run([
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "json", audio_path
            ], capture_output=True, text=True)
            duration = float(json.loads(result.stdout)["format"]["duration"])
        except:
            duration = 45.0
        
        # ════════════════════════════════════════════════════════════════
        # 🛡️ BLOCKING AUTHORITY FIX - Prevents asyncio cancellation
        # Uses subprocess.run instead of asyncio to ensure FFmpeg completes
        # ════════════════════════════════════════════════════════════════
        
        import subprocess as sp
        import shlex
        
        # Build FFmpeg command as string for blocking execution
        ffmpeg_cmd = (
            f'ffmpeg -y -stream_loop -1 -i "{bg_path}" -i "{audio_path}" '
            f'-map 0:v:0 -map 1:a:0 -t {min(duration, 58.0)} '
            f'-vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,'
            f'eq=contrast=1.08:saturation=1.12,noise=alls=20:allf=t+u,format=yuv420p" '
            f'-c:v libx264 -profile:v high -level 4.2 -preset slow -pix_fmt yuv420p '
            f'-b:v 8M -minrate 6M -maxrate 10M -bufsize 16M -g 60 -keyint_min 60 -sc_threshold 0 '
            f'-c:a aac -b:a 192k -ar 48000 -movflags +faststart "{output_path}"'
        )
        
        print(f"   🎬 [AUTHORITY] Starting Blocking Render...")
        print(f"   ⏳ This will take 60-120 seconds. DO NOT INTERRUPT.")
        
        try:
            # BLOCKING CALL - Python WAITS until FFmpeg exits
            result = sp.run(
                ffmpeg_cmd,
                shell=True,  # Use shell=True for Windows compatibility
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout max
            )
            
            if result.returncode != 0:
                print(f"   ❌ [CRITICAL] FFmpeg error: {result.stderr[-500:] if result.stderr else 'Unknown'}")
                return None
                
            print(f"   ✅ [COMPLETE] Render finished successfully.")
            
        except sp.TimeoutExpired:
            print(f"   ❌ [TIMEOUT] FFmpeg exceeded 5 minute limit")
            return None
        except Exception as e:
            print(f"   ❌ [ERROR] FFmpeg failed: {e}")
            return None
        
        # ════════════════════════════════════════════════════════════════
        # 💎 SIZE GUARD - Verify file integrity before returning
        # ════════════════════════════════════════════════════════════════
        
        if os.path.exists(output_path):
            file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
            
            # Elite 8Mbps Short of 40s should be ~40MB, never under 15MB
            if file_size_mb < 15:
                print(f"   🚫 [GATE] Integrity FAILED: {file_size_mb:.2f}MB is too small. Corrupted render.")
                return None
            
            print(f"   💎 [GATE] Integrity Verified: {file_size_mb:.2f}MB")
            return output_path
        
        return None
    
    async def generate_metadata(self, topic: str) -> dict:
        """Generate title, description, tags."""
        import openai
        
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": f"""Create YouTube Shorts metadata.

Topic: {topic}

Rules:
- Title: 50-70 characters, no emojis, no clickbait spam
- Description: 100-200 characters, readable, one CTA
- Tags: 5-6 relevant tags

Output as JSON:
{{"title": "...", "description": "...", "tags": ["..."]}}"""
                }
            ],
            temperature=0.5,
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    
    async def upload_to_youtube(self, video_path: str, metadata: dict) -> bool:
        """Upload to YouTube using YouTubeUploader."""
        from engines.uploaders import YouTubeUploader
        
        uploader = YouTubeUploader()
        
        # Validate before upload
        passed, report = await self.quality_gate.check_video(video_path, self.channel_id)
        if not passed:
            print(f"❌ Quality gate failed: {report.get('errors', [])}")
            self.stats["quarantined"] += 1
            return False
        
        try:
            result = await uploader.upload_short(
                video_path=video_path,
                title=metadata["title"],
                description=metadata["description"],
                tags=metadata.get("tags", []),
                privacy="public"
            )
            
            if result and result.get("success"):
                video_id = result.get("video_id", result.get("id", ""))
                print(f"✅ Uploaded: https://youtube.com/shorts/{video_id}")
                self.stats["uploaded"] += 1
                return True
            else:
                print(f"❌ Upload failed: {result}")
                self.stats["failed"] += 1
                return False
                
        except Exception as e:
            print(f"❌ Upload error: {e}")
            self.stats["failed"] += 1
            return False
    
    async def create_one(self) -> bool:
        """Create and upload one Short."""
        print("\n" + "="*60)
        print(f"🎬 CREATING SHORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        try:
            # 1. Get topic from self-rotating pool
            topic = self.get_next_topic()
            pool_indicator = {
                "core": "📦",
                "high_performing": "🔥",
                "experimental": "🧪",
                "cooldown": "❄️",
                "fallback": "⚠️"
            }.get(self.current_pool, "📦")
            print(f"📝 Topic: {topic}")
            print(f"   {pool_indicator} Pool: {self.current_pool}")
            
            # 2. Generate script
            print("🖊️ Generating script...")
            script = await self.generate_script(topic)
            word_count = len(script.split())
            print(f"   ✓ {word_count} words")
            
            # 3. Generate voice
            print("🎙️ Generating voice...")
            audio_path = await self.generate_voice(script)
            print(f"   ✓ {os.path.getsize(audio_path) / 1024:.1f} KB")
            
            # 4. Assemble video - ELITE: Pass script for visual intent matching
            print("🎥 Assembling video...")
            video_path = await self.assemble_video(audio_path, script=script)
            if not video_path:
                print("   ❌ Video assembly failed")
                self.stats["failed"] += 1
                return False
            print(f"   ✓ {os.path.getsize(video_path) / 1024:.1f} KB")
            
            # 5. Validate with quality gate
            print("🔍 Running quality gates...")
            passed, report = await self.quality_gate.check_video(video_path, self.channel_id)
            if not passed:
                print(f"   ❌ Failed: {report.get('errors', [])}")
                self.stats["quarantined"] += 1
                return False
            print("   ✓ All gates passed")
            
            # 6. Generate metadata
            print("📋 Generating metadata...")
            metadata = await self.generate_metadata(topic)
            print(f"   ✓ Title: {metadata['title'][:50]}...")
            
            # 7. Upload
            print("📤 Uploading to YouTube...")
            success = await self.upload_to_youtube(video_path, metadata)
            
            if success:
                self.stats["created"] += 1
                print("\n✅ SHORT CREATED AND UPLOADED SUCCESSFULLY")
                
                # 8. Extract DNA for documentary expansion
                if HAS_DNA_TRACKING:
                    try:
                        visual_intent = resolve_visual_intent(script)
                        expander = get_expander()
                        expander.extract_dna(
                            video_id=metadata.get("title", "").replace(" ", "_")[:30],
                            topic=topic,
                            script=script,
                            visual_intent=visual_intent
                        )
                        print("🧬 DNA extracted for documentary expansion")
                    except Exception as e:
                        print(f"⚠️ DNA extraction skipped: {e}")
            
            return success
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            self.stats["failed"] += 1
            return False
    
    async def run_continuous(self, interval: int = 3600):
        """Run continuously with interval between uploads."""
        print("\n" + "="*60)
        print("🚀 MONEY MACHINE AI - CONTINUOUS MODE STARTED")
        print("="*60)
        print(f"Channel: {self.channel_id}")
        print(f"Safe Mode: {self.safe_mode}")
        print(f"Interval: {interval} seconds ({interval/60:.0f} minutes)")
        print("="*60)
        print("\nPress Ctrl+C to stop\n")
        
        while True:
            try:
                await self.create_one()
                
                # Print stats
                print(f"\n📊 Stats: Created={self.stats['created']} "
                      f"Uploaded={self.stats['uploaded']} "
                      f"Failed={self.stats['failed']} "
                      f"Quarantined={self.stats['quarantined']}")
                
                # Wait for next interval
                print(f"\n⏳ Next upload in {interval/60:.0f} minutes...")
                await asyncio.sleep(interval)
                
            except KeyboardInterrupt:
                print("\n\n🛑 Stopping continuous mode...")
                break
            except Exception as e:
                print(f"\n❌ Loop error: {e}")
                await asyncio.sleep(60)  # Wait 1 min on error
        
        print("\n" + "="*60)
        print("📊 FINAL STATS")
        print("="*60)
        print(f"Created: {self.stats['created']}")
        print(f"Uploaded: {self.stats['uploaded']}")
        print(f"Failed: {self.stats['failed']}")
        print(f"Quarantined: {self.stats['quarantined']}")
        print("="*60)


async def main():
    parser = argparse.ArgumentParser(description="Money Machine AI - Continuous Mode")
    parser.add_argument("--loop", action="store_true", help="Run continuously")
    parser.add_argument("--once", action="store_true", help="Run once (default)")
    parser.add_argument("--elite", action="store_true", help="Force elite topic selection")
    parser.add_argument("--topic", type=str, help="Force specific topic (overrides pool)")
    parser.add_argument("--force-upload", action="store_true", help="Upload even if quota warnings")
    parser.add_argument("--interval", type=int, default=3600, help="Seconds between uploads (default: 3600)")
    args = parser.parse_args()
    
    mode = ContinuousMode()
    
    # Elite mode: force elite topic
    if args.elite:
        print("\n🔥 ELITE MODE ACTIVATED")
        mode.elite_mode = True
    
    # Force specific topic
    if args.topic:
        print(f"\n🎯 FORCED TOPIC: {args.topic}")
        mode.current_topic = args.topic
        mode.current_pool = "forced"
        # Override get_next_topic to return forced topic
        mode._forced_topic = args.topic
    
    # Force upload flag
    if args.force_upload:
        print("📤 FORCE UPLOAD: Ignoring quota warnings")
        mode._force_upload = True
    
    if args.loop:
        await mode.run_continuous(interval=args.interval)
    else:
        await mode.create_one()


if __name__ == "__main__":
    asyncio.run(main())
