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
        self.stats = {
            "created": 0,
            "uploaded": 0,
            "failed": 0,
            "quarantined": 0
        }
    
    def get_next_topic(self) -> str:
        """Get next topic from self-rotating pool."""
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
        
        # Assemble (ELITE FIX: Forces video frames with MANDATORY bitrate floor)
        # noise filter prevents entropy collapse that causes FFmpeg to over-compress
        cmd = [
            "ffmpeg", "-y",
            # Loop background video infinitely
            "-stream_loop", "-1",
            "-i", bg_path,
            # Add audio
            "-i", audio_path,
            # FORCE stream mapping (prevents audio-only)
            "-map", "0:v:0",
            "-map", "1:a:0",
            # Force duration (cap at 58 seconds for Shorts)
            "-t", str(min(duration, 58.0)),
            # Video filter with motion, noise (anti-compression), format
            "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,eq=contrast=1.08:saturation=1.12,noise=alls=20:allf=t+u,format=yuv420p",
            # Video codec with YouTube Shorts compliance - ELITE ENCODING
            "-c:v", "libx264",
            "-profile:v", "high",
            "-level", "4.2",
            "-preset", "slow",
            "-pix_fmt", "yuv420p",
            # MANDATORY BITRATE CONTROLS (prevents 200kbps disaster)
            "-b:v", "8M",
            "-minrate", "6M",
            "-maxrate", "10M",
            "-bufsize", "16M",
            # GOP settings for Shorts
            "-g", "60",
            "-keyint_min", "60",
            "-sc_threshold", "0",
            # Audio codec
            "-c:a", "aac",
            "-b:a", "192k",
            "-ar", "48000",
            # Fast start for streaming
            "-movflags", "+faststart",
            # Output
            output_path
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()
        
        return output_path if os.path.exists(output_path) else None
    
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
    parser.add_argument("--interval", type=int, default=3600, help="Seconds between uploads (default: 3600)")
    args = parser.parse_args()
    
    mode = ContinuousMode()
    
    if args.loop:
        await mode.run_continuous(interval=args.interval)
    else:
        await mode.create_one()


if __name__ == "__main__":
    asyncio.run(main())
