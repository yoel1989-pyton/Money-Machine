"""
============================================================
MONEY MACHINE - CREATOR ENGINE
The Automated Content Factory
============================================================
Transforms opportunities into monetizable content assets.
Uses FREE APIs and tools only.
============================================================
ELITE MODE: Quality gates BLOCK all broken content.
============================================================
"""

import os
import json
import asyncio
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Optional
import httpx

# Import quality gates
from engines.quality_gates import (
    ScriptSanitizer,
    TTSProsody,
    QualityGate,
    VisualFallback,
    QualityConfig
)

# ============================================================
# CONFIGURATION
# ============================================================

class CreatorConfig:
    """Creator Engine Configuration"""
    
    # Base directory (project root)
    BASE_DIR = Path(__file__).parent.parent
    
    # Output directories (relative to project root)
    OUTPUT_DIR = BASE_DIR / "data" / "output"
    TEMP_DIR = BASE_DIR / "data" / "temp"
    ASSETS_DIR = BASE_DIR / "data" / "assets"
    
    # Video settings
    VIDEO_WIDTH = 1080
    VIDEO_HEIGHT = 1920  # Vertical for Shorts/TikTok
    VIDEO_FPS = 30
    VIDEO_BITRATE = "4M"
    
    # Audio settings
    AUDIO_BITRATE = "192k"
    TTS_VOICE = "en-US-ChristopherNeural"  # Edge TTS (free)
    
    # Content lengths
    SHORT_DURATION = 60  # seconds
    LONG_DURATION = 600  # seconds


# ============================================================
# TEXT-TO-SPEECH ENGINE (FREE - Edge TTS)
# ============================================================

class TTSEngine:
    """
    Text-to-Speech using Microsoft Edge TTS.
    100% FREE, no API key required, unlimited usage.
    ELITE MODE: Enforces prosody settings for human-like speech.
    """
    
    VOICES = {
        "male_us": "en-US-ChristopherNeural",
        "female_us": "en-US-JennyNeural",
        "male_uk": "en-GB-RyanNeural",
        "female_uk": "en-GB-SoniaNeural",
        "male_au": "en-AU-WilliamNeural",
        "female_au": "en-AU-NatashaNeural"
    }
    
    async def generate(
        self,
        text: str,
        output_path: str,
        voice: str = "male_us",
        rate: str = None,
        pitch: str = None,
        channel_id: str = None
    ) -> bool:
        """
        Generate speech from text using Edge TTS.
        ELITE: Auto-sanitizes text and applies proper prosody.
        Returns True if successful.
        """
        import edge_tts
        
        voice_id = self.VOICES.get(voice, self.VOICES["male_us"])
        
        # ELITE: Get prosody settings based on channel
        prosody = TTSProsody.get_settings(channel_id)
        rate = rate or prosody["rate"]
        pitch = pitch or prosody["pitch"]
        
        # ELITE: Sanitize text to prevent robotic pauses
        clean_text = ScriptSanitizer.prepare_for_tts(text)
        
        if not clean_text:
            print("[CREATOR] ❌ TTS failed: Empty text after sanitization")
            return False
        
        print(f"[CREATOR] TTS settings: rate={rate}, pitch={pitch}")
        print(f"[CREATOR] TTS text length: {len(clean_text)} chars")
        
        try:
            communicate = edge_tts.Communicate(clean_text, voice_id, rate=rate, pitch=pitch)
            await communicate.save(output_path)
            print(f"[CREATOR] ✅ TTS generated: {output_path}")
            return True
        except Exception as e:
            print(f"[CREATOR] ❌ TTS exception: {e}")
            return False
    
    async def generate_with_timestamps(
        self,
        text: str,
        output_audio: str,
        output_srt: str,
        voice: str = "male_us",
        channel_id: str = None
    ) -> bool:
        """Generate TTS with subtitle timestamps - ELITE: Auto-sanitized"""
        import edge_tts
        
        voice_id = self.VOICES.get(voice, self.VOICES["male_us"])
        
        # ELITE: Get prosody settings based on channel
        prosody = TTSProsody.get_settings(channel_id)
        
        # ELITE: Sanitize text to prevent robotic pauses
        clean_text = ScriptSanitizer.prepare_for_tts(text)
        
        if not clean_text:
            print("[CREATOR] ❌ TTS failed: Empty text after sanitization")
            return False
        
        try:
            communicate = edge_tts.Communicate(
                clean_text, 
                voice_id, 
                rate=prosody["rate"], 
                pitch=prosody["pitch"]
            )
            submaker = edge_tts.SubMaker()
            
            with open(output_audio, "wb") as audio_file:
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        audio_file.write(chunk["data"])
                    elif chunk["type"] == "WordBoundary":
                        submaker.feed(chunk)
            
            with open(output_srt, "w", encoding="utf-8") as srt_file:
                srt_file.write(submaker.get_srt())
            
            print(f"[CREATOR] ✅ TTS+SRT generated: {output_audio}")
            return True
            
        except Exception as e:
            print(f"[CREATOR] ❌ TTS+SRT exception: {e}")
            return False


# ============================================================
# SCRIPT GENERATOR (OpenAI or Local)
# ============================================================

class ScriptGenerator:
    """
    Generates video scripts from opportunities.
    Uses OpenAI API (free $5 credit) or local models.
    """
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = "https://api.openai.com/v1"
        
    async def generate_short_script(
        self,
        topic: str,
        angle: str = "educational",
        duration: int = 60
    ) -> dict:
        """
        Generate a YouTube Shorts / TikTok script.
        Optimized for engagement and retention.
        """
        
        words_target = duration * 2.5  # ~2.5 words per second
        
        prompt = f"""Create a viral YouTube Short script about: {topic}

REQUIREMENTS:
- Target duration: {duration} seconds (~{int(words_target)} words)
- Content angle: {angle}
- Structure:
  1. HOOK (0-3 sec): Pattern interrupt, shocking statement or question
  2. CONTEXT (3-10 sec): Why this matters, create curiosity gap
  3. VALUE (10-50 sec): Deliver the main content
  4. CTA (50-60 sec): Call to action (follow, comment, share)

OUTPUT FORMAT (JSON):
{{
    "hook": "The opening line",
    "script": "Full script with natural pauses marked as [PAUSE]",
    "cta": "The call to action",
    "title": "Catchy video title with emoji",
    "description": "SEO-optimized description",
    "hashtags": ["relevant", "hashtags", "list"],
    "estimated_duration": {duration}
}}

Make it conversational, engaging, and slightly controversial if appropriate.
"""

        if self.api_key:
            return await self._call_openai(prompt)
        else:
            return self._generate_template(topic, angle, duration)
    
    async def generate_long_script(
        self,
        topic: str,
        sources: list = None,
        duration: int = 600
    ) -> dict:
        """
        Generate a longer video script (5-15 minutes).
        """
        words_target = duration * 2.5
        
        sources_text = "\n".join(sources) if sources else "General knowledge"
        
        prompt = f"""Create a comprehensive YouTube video script about: {topic}

SOURCE MATERIAL:
{sources_text}

REQUIREMENTS:
- Target duration: {duration} seconds (~{int(words_target)} words)
- Structure:
  1. HOOK (0-15 sec): Attention-grabbing opening
  2. INTRO (15-60 sec): What they'll learn, why it matters
  3. MAIN CONTENT (1-8 min): Numbered points with examples
  4. SUMMARY (8-9 min): Key takeaways
  5. CTA (9-10 min): Subscribe, comment, related video

OUTPUT FORMAT (JSON):
{{
    "hook": "Opening hook",
    "intro": "Introduction paragraph",
    "sections": [
        {{"title": "Section 1", "content": "Content..."}},
        {{"title": "Section 2", "content": "Content..."}}
    ],
    "summary": "Summary paragraph",
    "cta": "Call to action",
    "title": "Video title",
    "description": "Full YouTube description with timestamps",
    "tags": ["tag1", "tag2"]
}}
"""
        
        if self.api_key:
            return await self._call_openai(prompt)
        else:
            return self._generate_template(topic, "educational", duration)
    
    async def _call_openai(self, prompt: str) -> dict:
        """Call OpenAI API"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-4o-mini",  # Cheapest model
                        "messages": [
                            {"role": "system", "content": "You are a viral content scriptwriter."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.8,
                        "response_format": {"type": "json_object"}
                    },
                    timeout=60
                )
                
                if response.status_code == 200:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    return json.loads(content)
                else:
                    print(f"[CREATOR] OpenAI error: {response.text}")
                    return {}
                    
        except Exception as e:
            print(f"[CREATOR] OpenAI exception: {e}")
            return {}
    
    def _generate_template(self, topic: str, angle: str, duration: int) -> dict:
        """Fallback template when no API key"""
        return {
            "hook": f"Did you know this about {topic}?",
            "script": f"Let's talk about {topic}. This is important because...",
            "cta": "Follow for more tips!",
            "title": f"🔥 {topic.title()} - What You Need to Know",
            "description": f"In this video, we cover everything about {topic}.",
            "hashtags": ["viral", topic.replace(" ", ""), "trending"],
            "estimated_duration": duration
        }


# ============================================================
# STOCK FOOTAGE ENGINE (FREE APIs)
# ============================================================

class StockEngine:
    """
    Fetches stock video/images from free APIs.
    Pexels: Unlimited free downloads
    Pixabay: Unlimited free downloads
    """
    
    def __init__(self):
        self.pexels_key = os.getenv("PEXELS_API_KEY")
        self.pixabay_key = os.getenv("PIXABAY_API_KEY")
        
    async def search_pexels_videos(
        self,
        query: str,
        orientation: str = "portrait",
        per_page: int = 5
    ) -> list:
        """Search Pexels for stock videos"""
        if not self.pexels_key:
            return []
            
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.pexels.com/videos/search",
                headers={"Authorization": self.pexels_key},
                params={
                    "query": query,
                    "orientation": orientation,
                    "per_page": per_page
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                videos = []
                
                for video in data.get("videos", []):
                    # Get best quality file
                    files = video.get("video_files", [])
                    hd_file = next(
                        (f for f in files if f.get("quality") == "hd"),
                        files[0] if files else None
                    )
                    
                    if hd_file:
                        videos.append({
                            "id": video["id"],
                            "url": hd_file["link"],
                            "width": hd_file.get("width"),
                            "height": hd_file.get("height"),
                            "duration": video.get("duration"),
                            "source": "pexels"
                        })
                
                return videos
        
        return []
    
    async def download_video(self, url: str, output_path: str) -> bool:
        """Download a video file"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, follow_redirects=True)
                
                if response.status_code == 200:
                    with open(output_path, "wb") as f:
                        f.write(response.content)
                    return True
                    
        except Exception as e:
            print(f"[CREATOR] Download error: {e}")
            
        return False


# ============================================================
# VIDEO ASSEMBLY ENGINE (FFmpeg)
# ============================================================

class VideoAssembler:
    """
    Assembles final videos using FFmpeg.
    Combines TTS audio with stock footage.
    """
    
    async def create_vertical_video(
        self,
        audio_path: str,
        background_path: str,
        output_path: str,
        subtitles_path: str = None
    ) -> bool:
        """
        Create a vertical video (9:16) for Shorts/TikTok.
        """
        
        # Get audio duration
        duration = await self._get_duration(audio_path)
        
        # Build FFmpeg command
        cmd = [
            "ffmpeg", "-y",
            # Loop background video
            "-stream_loop", "-1",
            "-i", background_path,
            # Add audio
            "-i", audio_path,
            # Trim to audio length
            "-t", str(duration),
            # Scale and crop to vertical
            "-vf", f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
            # Video codec (SPEED MODE)
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "30",
            "-tune", "zerolatency",
            "-threads", "0",
            # Audio codec
            "-c:a", "aac",
            "-b:a", "128k",
            # Output
            "-shortest",
            output_path
        ]
        
        # Add subtitles if provided and non-empty
        if subtitles_path and os.path.exists(subtitles_path) and os.path.getsize(subtitles_path) > 0:
            # FFmpeg subtitles filter requires escaped paths (colons and backslashes)
            escaped_srt = subtitles_path.replace("\\", "/").replace(":", "\\:")
            cmd[cmd.index("-vf")] = "-vf"
            vf_index = cmd.index("-vf") + 1
            cmd[vf_index] = f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,subtitles='{escaped_srt}'"
        
        return await self._run_ffmpeg(cmd)
    
    async def create_horizontal_video(
        self,
        audio_path: str,
        background_path: str,
        output_path: str
    ) -> bool:
        """Create a horizontal video (16:9) for YouTube"""
        
        duration = await self._get_duration(audio_path)
        
        cmd = [
            "ffmpeg", "-y",
            "-stream_loop", "-1",
            "-i", background_path,
            "-i", audio_path,
            "-t", str(duration),
            "-vf", "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "30",
            "-tune", "zerolatency",
            "-threads", "0",
            "-c:a", "aac",
            "-shortest",
            output_path
        ]
        
        return await self._run_ffmpeg(cmd)
    
    async def add_unique_fingerprint(
        self,
        input_path: str,
        output_path: str
    ) -> bool:
        """
        Add unique modifications to avoid content ID.
        - Slight speed change
        - Color grading
        - Noise overlay
        """
        
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-vf", ",".join([
                # Slight speed change (1%)
                "setpts=0.99*PTS",
                # Color adjustment
                "eq=brightness=0.02:contrast=1.02:saturation=1.05",
                # Very subtle noise
                "noise=alls=3:allf=t"
            ]),
            "-af", "atempo=1.01",  # Match audio to video speed
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "30",
            "-threads", "0",
            "-c:a", "aac",
            output_path
        ]
        
        return await self._run_ffmpeg(cmd)
    
    async def resize_for_platform(
        self,
        input_path: str,
        output_path: str,
        platform: str
    ) -> bool:
        """Resize video for different platforms"""
        
        sizes = {
            "youtube_short": "1080:1920",
            "youtube_long": "1920:1080",
            "tiktok": "1080:1920",
            "instagram_reel": "1080:1920",
            "instagram_feed": "1080:1080",
            "pinterest": "1000:1500"
        }
        
        size = sizes.get(platform, "1080:1920")
        width, height = size.split(":")
        
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "30",
            "-threads", "0",
            "-c:a", "copy",
            output_path
        ]
        
        return await self._run_ffmpeg(cmd)
    
    async def _get_duration(self, audio_path: str) -> float:
        """Get audio duration in seconds"""
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "json",
            audio_path
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, _ = await process.communicate()
        
        try:
            data = json.loads(stdout.decode())
            return float(data["format"]["duration"])
        except:
            return 60.0  # Default
    
    async def _run_ffmpeg(self, cmd: list) -> bool:
        """Run FFmpeg command"""
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            _, stderr = await process.communicate()
            
            if process.returncode == 0:
                print(f"[CREATOR] FFmpeg success: {cmd[-1]}")
                return True
            else:
                print(f"[CREATOR] FFmpeg error: {stderr.decode()[-500:]}")
                return False
                
        except Exception as e:
            print(f"[CREATOR] FFmpeg exception: {e}")
            return False


# ============================================================
# MASTER CREATOR - ORCHESTRATOR
# ============================================================

class MasterCreator:
    """
    Master Creator that orchestrates all creation engines.
    Takes an opportunity and produces a ready-to-upload asset.
    ELITE MODE: Quality gates block all broken content.
    """
    
    def __init__(self, channel_id: str = None):
        self.tts = TTSEngine()
        self.script = ScriptGenerator()
        self.stock = StockEngine()
        self.video = VideoAssembler()
        self.quality_gate = QualityGate()
        
        # Get channel from env if not provided
        self.channel_id = channel_id or os.getenv("YOUTUBE_CHANNEL_ID")
        
        # Ensure directories exist
        for dir_path in [CreatorConfig.OUTPUT_DIR, CreatorConfig.TEMP_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    async def create_short(
        self,
        topic: str,
        angle: str = "educational",
        voice: str = "male_us",
        validate: bool = True
    ) -> dict:
        """
        Create a complete YouTube Short / TikTok video.
        ELITE: Quality gate validates before allowing upload.
        Returns paths to all generated assets.
        """
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        job_id = f"short_{timestamp}"
        
        result = {
            "job_id": job_id,
            "topic": topic,
            "channel_id": self.channel_id,
            "status": "processing",
            "quality_passed": False,
            "assets": {}
        }
        
        try:
            # Step 1: Generate script
            print(f"[CREATOR] 📝 Generating script for: {topic}")
            script_data = await self.script.generate_short_script(topic, angle)
            result["script"] = script_data
            
            # ELITE: Validate and sanitize script
            full_script = script_data.get("script", topic)
            valid, sanitized_script = self.quality_gate.check_script(full_script)
            
            if not valid:
                result["status"] = "failed"
                result["error"] = "Script validation failed - too short or invalid"
                return result
            
            # Step 2: Generate TTS with proper prosody
            audio_path = str(CreatorConfig.TEMP_DIR / f"{job_id}_audio.mp3")
            srt_path = str(CreatorConfig.TEMP_DIR / f"{job_id}.srt")
            
            print(f"[CREATOR] 🎙️ Generating TTS...")
            
            tts_success = await self.tts.generate_with_timestamps(
                sanitized_script,  # Use sanitized script
                audio_path, 
                srt_path, 
                voice,
                channel_id=self.channel_id
            )
            
            if not tts_success:
                result["status"] = "failed"
                result["error"] = "TTS generation failed"
                return result
            
            result["assets"]["audio"] = audio_path
            result["assets"]["subtitles"] = srt_path
            
            # Step 3: Get stock footage with FALLBACK
            print(f"[CREATOR] 🎬 Fetching stock footage...")
            videos = await self.stock.search_pexels_videos(topic)
            
            bg_path = str(CreatorConfig.TEMP_DIR / f"{job_id}_bg.mp4")
            
            if videos:
                download_success = await self.stock.download_video(videos[0]["url"], bg_path)
                if not download_success:
                    videos = []  # Trigger fallback
            
            # ELITE: Visual fallback - NEVER allow blank video
            if not videos or not os.path.exists(bg_path):
                print(f"[CREATOR] ⚠️ Stock footage failed, using fallback...")
                bg_path = await VisualFallback.get_fallback_background(duration=60)
            
            result["assets"]["background"] = bg_path
            
            # Step 4: Assemble video
            output_path = str(CreatorConfig.OUTPUT_DIR / f"{job_id}_vertical.mp4")
            print(f"[CREATOR] 🎥 Assembling video...")
            
            success = await self.video.create_vertical_video(
                audio_path,
                result["assets"]["background"],
                output_path,
                srt_path
            )
            
            if success:
                result["assets"]["video"] = output_path
                
                # Step 5: Add fingerprint
                final_path = str(CreatorConfig.OUTPUT_DIR / f"{job_id}_final.mp4")
                await self.video.add_unique_fingerprint(output_path, final_path)
                result["assets"]["final_video"] = final_path
                
                # ELITE: Quality gate validation
                if validate:
                    print(f"[CREATOR] 🔍 Running quality gate...")
                    passed, report = await self.quality_gate.check_video(
                        final_path, 
                        self.channel_id
                    )
                    
                    result["quality_passed"] = passed
                    result["quality_report"] = report
                    
                    if passed:
                        result["status"] = "complete"
                        print(f"[CREATOR] ✅ Quality gate PASSED - Ready for upload")
                    else:
                        result["status"] = "quarantined"
                        result["error"] = f"Quality gate failed: {report['errors']}"
                        print(f"[CREATOR] ❌ Quality gate FAILED - Quarantined")
                else:
                    result["status"] = "complete"
                    result["quality_passed"] = True
            else:
                result["status"] = "failed"
                result["error"] = "Video assembly failed"
                
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            print(f"[CREATOR] ❌ Error: {e}")
        
        return result
    
    async def create_multiplatform(
        self,
        topic: str,
        platforms: list = None,
        validate: bool = True
    ) -> dict:
        """
        Create content for multiple platforms from one source.
        Omni-alignment: One asset → All platforms
        ELITE: Quality gate validates before export.
        """
        
        if platforms is None:
            platforms = ["youtube_short", "tiktok", "instagram_reel"]
        
        # First, create the master asset
        master = await self.create_short(topic, validate=validate)
        
        if master["status"] != "complete":
            return master
        
        # Resize for each platform
        master_video = master["assets"].get("final_video")
        
        for platform in platforms:
            platform_path = master_video.replace("_final.mp4", f"_{platform}.mp4")
            await self.video.resize_for_platform(master_video, platform_path, platform)
            master["assets"][platform] = platform_path
        
        master["platforms"] = platforms
        return master
    
    def is_safe_mode(self) -> bool:
        """Check if current channel is in safe mode."""
        return self.quality_gate.is_safe_mode_channel(self.channel_id)


# ============================================================
# CLI INTERFACE (for n8n Execute Command node)
# ============================================================

if __name__ == "__main__":
    import sys
    
    async def main():
        # Get channel ID from env
        channel_id = os.getenv("YOUTUBE_CHANNEL_ID")
        creator = MasterCreator(channel_id=channel_id)
        
        # Check safe mode
        if creator.is_safe_mode():
            print(f"[CREATOR] 🔒 SAFE MODE ACTIVE for channel: {channel_id}")
        
        if len(sys.argv) > 1:
            command = sys.argv[1]
            
            # Check for --no-validate flag
            validate = "--no-validate" not in sys.argv
            
            # Remove flags from args
            args = [a for a in sys.argv[2:] if not a.startswith("--")]
            
            if command == "short" and args:
                topic = " ".join(args)
                result = await creator.create_short(topic, validate=validate)
            elif command == "multi" and args:
                topic = " ".join(args)
                result = await creator.create_multiplatform(topic, validate=validate)
            elif command == "test":
                # Quick test mode
                result = await creator.create_short(
                    "Money tips for beginners", 
                    validate=True
                )
            else:
                result = {"error": "Usage: creator.py [short|multi|test] <topic> [--no-validate]"}
        else:
            result = {"error": "No command provided. Usage: creator.py [short|multi|test] <topic>"}
        
        print(json.dumps(result, indent=2, default=str))
    
    asyncio.run(main())
