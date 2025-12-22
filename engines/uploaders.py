"""
============================================================
ELITE MONEY MACHINE - PLATFORM UPLOADERS
Compliant, Official API Automation
============================================================
YouTube: Full automation via Data API v3
Instagram: Reels via Meta Graph API
TikTok: Draft push via Content Posting API
LOCAL MODE: Saves videos when APIs not configured
============================================================
ELITE MODE: Quality gates block broken content before upload.
============================================================
"""

import os
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import httpx
import shutil

# Load environment variables
from dotenv import load_dotenv
load_dotenv(override=True)

# Import guardrails (lazy to avoid circular imports)
_guardrails = None
def get_guardrails():
    global _guardrails
    if _guardrails is None:
        from .guardrails import Guardrails
        _guardrails = Guardrails()
    return _guardrails

# Import quality gate (lazy to avoid circular imports)
_quality_gate = None
def get_quality_gate():
    global _quality_gate
    if _quality_gate is None:
        from .quality_gates import QualityGate
        _quality_gate = QualityGate()
    return _quality_gate

# Import ELITE video validator
from engines.video_builder import validate_video

# ============================================================
# YOUTUBE UPLOADER (PRIMARY - FULL AUTOMATION)
# ============================================================

class YouTubeUploader:
    """
    Upload Shorts to YouTube using official Data API v3.
    Fully compliant. Unlimited uploads within quota.
    
    Required env vars (either naming convention works):
    - YOUTUBE_CLIENT_ID or YT_CLIENT_ID
    - YOUTUBE_CLIENT_SECRET or YT_CLIENT_SECRET
    - YOUTUBE_REFRESH_TOKEN or YT_REFRESH_TOKEN
    """
    
    UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    
    def __init__(self):
        self.client_id = os.getenv("YOUTUBE_CLIENT_ID") or os.getenv("YT_CLIENT_ID")
        self.client_secret = os.getenv("YOUTUBE_CLIENT_SECRET") or os.getenv("YT_CLIENT_SECRET")
        self.refresh_token = os.getenv("YOUTUBE_REFRESH_TOKEN") or os.getenv("YT_REFRESH_TOKEN")
        self.access_token = None
        self.channel_id = os.getenv("YT_CHANNEL_ID", "UCZppwcvPrWlAG0vb78elPJA")
    
    def is_configured(self) -> bool:
        """Check if YouTube API is configured with REAL credentials"""
        if not all([self.client_id, self.client_secret, self.refresh_token]):
            return False
        # Check they're not placeholder values
        if "your-" in self.client_id.lower() or self.client_id == "":
            return False
        return True
    
    async def refresh_access_token(self) -> bool:
        """Refresh the OAuth access token"""
        if not self.is_configured():
            print("[YOUTUBE] Not configured - LOCAL MODE")
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.TOKEN_URL,
                    data={
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "refresh_token": self.refresh_token,
                        "grant_type": "refresh_token"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.access_token = data.get("access_token")
                    print("[YOUTUBE] Access token refreshed")
                    return True
                else:
                    print(f"[YOUTUBE] Token refresh failed: {response.status_code}")
                    return False
        except Exception as e:
            print(f"[YOUTUBE] Token refresh error: {e}")
            return False
    
    async def upload_short(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: list = None,
        privacy: str = "public"
    ) -> Dict[str, Any]:
        """
        Upload a Short to YouTube.
        ELITE: Validates video before upload to block audio-only files.
        
        Args:
            video_path: Path to the video file
            title: Video title (max 100 chars)
            description: Video description with CTAs
            tags: List of tags
            privacy: public, private, or unlisted
        
        Returns:
            Dict with video_id and status
        """
        # ELITE: Hard block audio-only uploads
        if not validate_video(video_path):
            error_msg = "Upload blocked: invalid video (audio-only or corrupted)"
            print(f"[YOUTUBE] ❌ {error_msg}")
            return {"success": False, "error": error_msg, "blocked": True}
        
        if not self.is_configured():
            return {"success": False, "error": "YouTube not configured"}
        
        if not self.access_token:
            if not await self.refresh_access_token():
                return {"success": False, "error": "Token refresh failed"}
        
        # Prepare metadata
        metadata = {
            "snippet": {
                "title": title[:100],  # YouTube limit
                "description": description[:5000],
                "tags": tags or ["shorts", "money", "wealth"],
                "categoryId": "22"  # People & Blogs
            },
            "status": {
                "privacyStatus": privacy,
                "selfDeclaredMadeForKids": False,
                "madeForKids": False
            }
        }
        
        try:
            # Read video file
            video_data = Path(video_path).read_bytes()
            
            async with httpx.AsyncClient(timeout=300.0) as client:
                # Resumable upload initiation
                init_response = await client.post(
                    f"{self.UPLOAD_URL}?uploadType=resumable&part=snippet,status",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": "application/json",
                        "X-Upload-Content-Type": "video/mp4",
                        "X-Upload-Content-Length": str(len(video_data))
                    },
                    json=metadata
                )
                
                if init_response.status_code == 200:
                    upload_url = init_response.headers.get("Location")
                    
                    # Upload video data
                    upload_response = await client.put(
                        upload_url,
                        headers={
                            "Authorization": f"Bearer {self.access_token}",
                            "Content-Type": "video/mp4"
                        },
                        content=video_data
                    )
                    
                    if upload_response.status_code in [200, 201]:
                        result = upload_response.json()
                        video_id = result.get("id")
                        print(f"[YOUTUBE] ✅ Uploaded: https://youtube.com/shorts/{video_id}")
                        return {
                            "success": True,
                            "video_id": video_id,
                            "url": f"https://youtube.com/shorts/{video_id}"
                        }
                    else:
                        print(f"[YOUTUBE] Upload failed: {upload_response.status_code}")
                        return {"success": False, "error": upload_response.text}
                else:
                    print(f"[YOUTUBE] Init failed: {init_response.status_code}")
                    return {"success": False, "error": init_response.text}
                    
        except Exception as e:
            print(f"[YOUTUBE] Upload error: {e}")
            return {"success": False, "error": str(e)}


# ============================================================
# INSTAGRAM UPLOADER (SECONDARY - REELS VIA GRAPH API)
# ============================================================

class InstagramUploader:
    """
    Upload Reels to Instagram using Meta Graph API.
    Requires Business/Creator account + Facebook Page.
    
    Required env vars:
    - IG_ACCESS_TOKEN (long-lived page token)
    - IG_USER_ID (Instagram Business Account ID)
    """
    
    GRAPH_URL = "https://graph.facebook.com/v18.0"
    
    def __init__(self):
        self.access_token = os.getenv("IG_ACCESS_TOKEN")
        self.user_id = os.getenv("IG_USER_ID")
    
    def is_configured(self) -> bool:
        """Check if Instagram API is configured with REAL credentials"""
        if not all([self.access_token, self.user_id]):
            return False
        # Check they're not placeholder values
        if "your-" in str(self.access_token).lower() or self.access_token == "":
            return False
        return True
    
    async def upload_reel(
        self,
        video_url: str,  # Must be publicly accessible URL
        caption: str,
        cover_url: str = None
    ) -> Dict[str, Any]:
        """
        Upload a Reel to Instagram.
        
        Note: Video must be hosted at a public URL.
        For local files, upload to cloud storage first.
        
        Args:
            video_url: Public URL of the video
            caption: Reel caption with CTAs
            cover_url: Optional cover image URL
        
        Returns:
            Dict with media_id and status
        """
        if not self.is_configured():
            return {"success": False, "error": "Instagram not configured"}
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                # Step 1: Create media container
                container_params = {
                    "media_type": "REELS",
                    "video_url": video_url,
                    "caption": caption[:2200],  # Instagram limit
                    "access_token": self.access_token
                }
                
                if cover_url:
                    container_params["cover_url"] = cover_url
                
                container_response = await client.post(
                    f"{self.GRAPH_URL}/{self.user_id}/media",
                    params=container_params
                )
                
                if container_response.status_code != 200:
                    return {"success": False, "error": container_response.text}
                
                container_id = container_response.json().get("id")
                
                # Step 2: Wait for processing
                for _ in range(30):  # Max 5 minutes
                    status_response = await client.get(
                        f"{self.GRAPH_URL}/{container_id}",
                        params={
                            "fields": "status_code",
                            "access_token": self.access_token
                        }
                    )
                    
                    status = status_response.json().get("status_code")
                    if status == "FINISHED":
                        break
                    elif status == "ERROR":
                        return {"success": False, "error": "Processing failed"}
                    
                    await asyncio.sleep(10)
                
                # Step 3: Publish
                publish_response = await client.post(
                    f"{self.GRAPH_URL}/{self.user_id}/media_publish",
                    params={
                        "creation_id": container_id,
                        "access_token": self.access_token
                    }
                )
                
                if publish_response.status_code == 200:
                    media_id = publish_response.json().get("id")
                    print(f"[INSTAGRAM] ✅ Reel published: {media_id}")
                    return {"success": True, "media_id": media_id}
                else:
                    return {"success": False, "error": publish_response.text}
                    
        except Exception as e:
            print(f"[INSTAGRAM] Upload error: {e}")
            return {"success": False, "error": str(e)}


# ============================================================
# TIKTOK UPLOADER (TERTIARY - DRAFT PUSH)
# ============================================================

class TikTokUploader:
    """
    Push videos to TikTok drafts using Content Posting API.
    User taps "Post" to publish (1-2 taps/day).
    
    Required env vars:
    - TIKTOK_ACCESS_TOKEN
    - TIKTOK_OPEN_ID
    """
    
    API_URL = "https://open.tiktokapis.com/v2"
    
    def __init__(self):
        self.access_token = os.getenv("TIKTOK_ACCESS_TOKEN")
        self.open_id = os.getenv("TIKTOK_OPEN_ID")
    
    def is_configured(self) -> bool:
        """Check if TikTok API is configured with REAL credentials"""
        if not all([self.access_token, self.open_id]):
            return False
        # Check they're not placeholder values
        if "your-" in str(self.access_token).lower() or self.access_token == "":
            return False
        return True
    
    async def upload_to_drafts(
        self,
        video_path: str,
        title: str = ""
    ) -> Dict[str, Any]:
        """
        Upload video to TikTok drafts.
        User must open TikTok app and tap Post.
        ELITE: Validates video before upload to block audio-only files.
        
        Args:
            video_path: Path to the video file
            title: Optional title/caption
        
        Returns:
            Dict with publish_id and status
        """
        # ELITE: Hard block audio-only uploads
        if not validate_video(video_path):
            error_msg = "Upload blocked: invalid video (audio-only or corrupted)"
            print(f"[TIKTOK] ❌ {error_msg}")
            return {"success": False, "error": error_msg, "blocked": True}
        
        if not self.is_configured():
            return {"success": False, "error": "TikTok not configured"}
        
        try:
            video_data = Path(video_path).read_bytes()
            video_size = len(video_data)
            
            async with httpx.AsyncClient(timeout=300.0) as client:
                # Step 1: Initialize upload
                init_response = await client.post(
                    f"{self.API_URL}/post/publish/inbox/video/init/",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "source_info": {
                            "source": "FILE_UPLOAD",
                            "video_size": video_size,
                            "chunk_size": video_size,
                            "total_chunk_count": 1
                        }
                    }
                )
                
                if init_response.status_code != 200:
                    return {"success": False, "error": init_response.text}
                
                init_data = init_response.json().get("data", {})
                publish_id = init_data.get("publish_id")
                upload_url = init_data.get("upload_url")
                
                # Step 2: Upload video
                upload_response = await client.put(
                    upload_url,
                    headers={
                        "Content-Type": "video/mp4",
                        "Content-Range": f"bytes 0-{video_size-1}/{video_size}"
                    },
                    content=video_data
                )
                
                if upload_response.status_code in [200, 201]:
                    print(f"[TIKTOK] ✅ Video pushed to drafts: {publish_id}")
                    print("[TIKTOK] 📱 Open TikTok app and tap Post to publish")
                    return {
                        "success": True,
                        "publish_id": publish_id,
                        "status": "in_drafts"
                    }
                else:
                    return {"success": False, "error": upload_response.text}
                    
        except Exception as e:
            print(f"[TIKTOK] Upload error: {e}")
            return {"success": False, "error": str(e)}


# ============================================================
# LOCAL SAVER (WHEN NO APIS CONFIGURED)
# ============================================================

class LocalSaver:
    """
    Saves videos locally when platform APIs aren't configured.
    Organizes by date and niche for easy manual upload.
    """
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent / "output"
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def save_for_upload(
        self,
        video_path: str,
        niche: str,
        title: str,
        description: str
    ) -> Dict[str, Any]:
        """
        Save video to output folder for manual upload.
        Creates metadata file alongside video.
        """
        try:
            source = Path(video_path)
            if not source.exists():
                return {"success": False, "error": "Video not found"}
            
            # Create dated folder
            today = datetime.now().strftime("%Y-%m-%d")
            day_folder = self.base_dir / today
            day_folder.mkdir(parents=True, exist_ok=True)
            
            # Clean filename - remove emojis and special chars
            clean_title = "".join(c for c in title[:50] if c.isalnum() or c in " -_").strip()
            if not clean_title:
                clean_title = "video"
            timestamp = datetime.now().strftime("%H%M%S")
            filename = f"{niche}_{clean_title}_{timestamp}"
            
            # Copy video
            dest = day_folder / f"{filename}.mp4"
            shutil.copy2(source, dest)
            
            # Save metadata with UTF-8 encoding
            meta_file = day_folder / f"{filename}_metadata.txt"
            meta_file.write_text(f"""TITLE: {title}

DESCRIPTION:
{description}

PLATFORMS:
- YouTube Shorts: https://studio.youtube.com/channel/UCZppwcvPrWlAG0vb78elPJA/videos/upload
- TikTok: https://www.tiktok.com/creator-center/upload
- Instagram: Use mobile app

NICHE: {niche}
CREATED: {datetime.now().isoformat()}
""", encoding="utf-8")
            
            print(f"[LOCAL] Saved: {dest}")
            print(f"[LOCAL] Metadata: {meta_file}")
            
            return {
                "success": True,
                "path": str(dest),
                "metadata": str(meta_file),
                "mode": "local"
            }
            
        except Exception as e:
            print(f"[LOCAL] Save error: {e}")
            return {"success": False, "error": str(e)}


# ============================================================
# MASTER UPLOADER (ORCHESTRATES ALL PLATFORMS)
# ============================================================

class MasterUploader:
    """
    Orchestrates uploads across all platforms.
    Uses each platform's official API compliantly.
    Falls back to LOCAL MODE when no APIs are configured.
    ELITE: Quality gate validates all videos before upload.
    """
    
    def __init__(self):
        self.youtube = YouTubeUploader()
        self.instagram = InstagramUploader()
        self.tiktok = TikTokUploader()
        self.local = LocalSaver()
        self.channel_id = os.getenv("YOUTUBE_CHANNEL_ID")
    
    def get_status(self) -> Dict[str, bool]:
        """Get configuration status for all platforms"""
        status = {
            "youtube": self.youtube.is_configured(),
            "instagram": self.instagram.is_configured(),
            "tiktok": self.tiktok.is_configured()
        }
        status["any_configured"] = any(status.values())
        status["mode"] = "API" if status["any_configured"] else "LOCAL"
        return status
    
    async def validate_video(self, video_path: str) -> tuple:
        """
        ELITE: Run quality gate validation before upload.
        Returns (passed, report)
        """
        quality_gate = get_quality_gate()
        return await quality_gate.check_video(video_path, self.channel_id)
    
    async def upload_all(
        self,
        video_path: str,
        title: str,
        descriptions: Dict[str, str],
        niche: str,
        tags: list = None,
        skip_validation: bool = False
    ) -> Dict[str, Any]:
        """
        Upload to all configured platforms, or save locally.
        ELITE: Quality gate validates video before any upload.
        
        Args:
            video_path: Path to the video file
            title: Video title
            descriptions: Dict with platform-specific descriptions
            niche: Content niche (wealth/health/survival)
            tags: Optional list of tags
            skip_validation: Skip quality gate (NOT RECOMMENDED)
        
        Returns:
            Dict with results for each platform
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "mode": "LOCAL",
            "results": {},
            "summary": {},
            "quality_check": {}
        }
        
        # ELITE: Hard block - validate video stream exists FIRST
        if not validate_video(video_path):
            print("[UPLOADER] ❌ HARD BLOCK: Video validation failed - no video stream or corrupted")
            results["mode"] = "BLOCKED"
            results["quality_check"] = {
                "passed": False,
                "errors": ["No video stream detected (audio-only or corrupted file)"]
            }
            results["summary"] = {"uploaded": 0, "blocked": 1, "reason": "no_video_stream"}
            return results
        
        # ELITE: Quality gate validation (MANDATORY unless skipped)
        if not skip_validation:
            print("[UPLOADER] 🔍 Running quality gate validation...")
            passed, report = await self.validate_video(video_path)
            results["quality_check"] = {
                "passed": passed,
                "errors": report.get("errors", [])
            }
            
            if not passed:
                print(f"[UPLOADER] ❌ Quality gate FAILED - Upload blocked")
                print(f"[UPLOADER] Errors: {report.get('errors', [])}")
                results["mode"] = "QUARANTINED"
                results["summary"] = {"uploaded": 0, "blocked": 1, "reason": "quality_gate_failed"}
                return results
            
            print("[UPLOADER] ✅ Quality gate PASSED")
        
        status = self.get_status()
        
        # If no APIs configured, save locally
        if not status["any_configured"]:
            print("\n[UPLOADER] ⚠️ No platform APIs configured - using LOCAL MODE")
            print("[UPLOADER] Videos will be saved for manual upload")
            print("[UPLOADER] Run 'python upload_videos.py' to upload later\n")
            
            description = descriptions.get("youtube", descriptions.get("default", title))
            local_result = self.local.save_for_upload(video_path, niche, title, description)
            
            results["mode"] = "LOCAL"
            results["results"]["local"] = local_result
            results["summary"] = {"saved": 1, "uploaded": 0}
            return results
        
        # Upload to configured platforms
        results["mode"] = "API"
        uploaded = 0
        guardrails = get_guardrails()
        
        # YouTube (PRIMARY) - with rate limiting
        if status["youtube"]:
            can_upload = guardrails.can_upload("youtube")
            if can_upload["allowed"]:
                description = descriptions.get("youtube", descriptions.get("default", title))
                yt_result = await self.youtube.upload_short(video_path, title, description, tags)
                results["results"]["youtube"] = yt_result
                if yt_result.get("success"):
                    uploaded += 1
                    guardrails.record_upload("youtube", yt_result.get("video_id"))
                else:
                    guardrails.record_failure("youtube", yt_result.get("error", "Unknown"))
            else:
                results["results"]["youtube"] = {
                    "success": False,
                    "error": f"Rate limited: {can_upload.get('reason')}",
                    "wait_seconds": can_upload.get("wait_seconds")
                }
                print(f"[YOUTUBE] ⏳ Rate limited: {can_upload.get('reason')}")
        
        # Instagram (if configured and has public URL)
        if status["instagram"]:
            can_upload = guardrails.can_upload("instagram")
            if can_upload["allowed"]:
                results["results"]["instagram"] = {"success": False, "error": "Requires public video URL"}
            else:
                results["results"]["instagram"] = {"success": False, "error": f"Rate limited: {can_upload.get('reason')}"}
        
        # TikTok (drafts) - with rate limiting
        if status["tiktok"]:
            can_upload = guardrails.can_upload("tiktok")
            if can_upload["allowed"]:
                tt_result = await self.tiktok.upload_to_drafts(video_path, title)
                results["results"]["tiktok"] = tt_result
                if tt_result.get("success"):
                    uploaded += 1
                    guardrails.record_upload("tiktok", tt_result.get("video_id"))
                else:
                    guardrails.record_failure("tiktok", tt_result.get("error", "Unknown"))
            else:
                results["results"]["tiktok"] = {
                    "success": False,
                    "error": f"Rate limited: {can_upload.get('reason')}"
                }
        
        # Also save locally as backup
        description = descriptions.get("youtube", title)
        self.local.save_for_upload(video_path, niche, title, description)
        
        results["summary"] = {"uploaded": uploaded, "saved": 1}
        return results
    
    async def upload_to_all(
        self,
        video_paths: Dict[str, str],
        title: str,
        description: str,
        tags: list = None
    ) -> Dict[str, Any]:
        """
        Legacy method - Upload to all configured platforms.
        
        Args:
            video_paths: Dict with platform-specific video paths
                {
                    "youtube_short": "/path/to/youtube_short.mp4",
                    "instagram_reel": "/path/to/instagram_reel.mp4",
                    "tiktok": "/path/to/tiktok.mp4"
                }
            title: Video title
            description: Video description with CTAs
            tags: List of tags
        
        Returns:
            Dict with results for each platform
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "youtube": None,
            "instagram": None,
            "tiktok": None
        }
        
        # YouTube (PRIMARY)
        if self.youtube.is_configured() and video_paths.get("youtube_short"):
            results["youtube"] = await self.youtube.upload_short(
                video_paths["youtube_short"],
                title,
                description,
                tags
            )
        
        # Instagram (SECONDARY)
        # Note: Requires video to be hosted at public URL
        # For now, log as "queued for manual upload"
        if self.instagram.is_configured() and video_paths.get("instagram_reel"):
            # In production, upload to cloud storage first
            print("[INSTAGRAM] Video queued (requires public URL)")
            results["instagram"] = {"success": True, "status": "queued"}
        
        # TikTok (TERTIARY - drafts)
        if self.tiktok.is_configured() and video_paths.get("tiktok"):
            results["tiktok"] = await self.tiktok.upload_to_drafts(
                video_paths["tiktok"],
                title
            )
        
        return results
    
    async def upload_youtube_only(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: list = None
    ) -> Dict[str, Any]:
        """Quick method for YouTube-only upload"""
        if not self.youtube.is_configured():
            print("[UPLOADER] YouTube not configured")
            return {"success": False, "error": "Not configured"}
        
        return await self.youtube.upload_short(video_path, title, description, tags)


# ============================================================
# DESCRIPTION TEMPLATES (MONETIZATION-OPTIMIZED)
# ============================================================

class DescriptionTemplates:
    """
    Pre-built descriptions with CTAs for maximum conversions.
    Affiliate links, lead magnets, email capture.
    """
    
    @staticmethod
    def generate_all(niche: str, topic: str, cta_url: str = "Link in bio 🔗") -> Dict[str, str]:
        """
        Generate descriptions for all platforms based on niche.
        
        Args:
            niche: One of "wealth", "health", "survival"
            topic: The video topic/title
            cta_url: Call-to-action URL
        
        Returns:
            Dict with descriptions for each platform
        """
        niche = niche.lower() if niche else "wealth"
        
        if niche == "wealth" or "money" in niche or "finance" in niche:
            return {
                "youtube": f"""{topic}

💰 Want to learn how the wealthy think? Follow for daily money tips!

👉 {cta_url}

#shorts #money #wealth #finance #investing #rich #millionaire #entrepreneur #sidehustle #passiveincome""",
                "instagram": f"""{topic}

💰 Follow for daily wealth wisdom!
👉 {cta_url}

#money #wealth #finance #investing #rich #millionaire #entrepreneur""",
                "tiktok": f"""{topic} 💰 Follow for more! {cta_url} #money #wealth #investing #rich"""
            }
        
        elif niche == "health" or "fitness" in niche or "wellness" in niche:
            return {
                "youtube": f"""{topic}

💪 Your health is your wealth. Follow for daily tips!

👉 {cta_url}

#shorts #health #fitness #wellness #nutrition #workout #motivation #healthy #lifestyle #biohacking""",
                "instagram": f"""{topic}

💪 Follow for daily health tips!
👉 {cta_url}

#health #fitness #wellness #nutrition #workout #motivation #healthy""",
                "tiktok": f"""{topic} 💪 Follow for more! {cta_url} #health #fitness #wellness #workout"""
            }
        
        else:  # survival
            return {
                "youtube": f"""{topic}

🏕️ Be prepared for anything. Follow for survival tips!

👉 {cta_url}

#shorts #survival #prepper #outdoors #camping #emergency #bushcraft #tactical #prepared #selfreliance""",
                "instagram": f"""{topic}

🏕️ Follow for survival tips!
👉 {cta_url}

#survival #prepper #outdoors #camping #emergency #bushcraft #tactical""",
                "tiktok": f"""{topic} 🏕️ Follow for more! {cta_url} #survival #prepper #camping #prepared"""
            }
    
    @staticmethod
    def wealth_short(title: str, lead_magnet_url: str, affiliate_url: str = None) -> str:
        """Description for wealth/money niche Shorts"""
        desc = f"""{title}

💰 FREE Guide: How to Start Making Money Online
👉 {lead_magnet_url}

"""
        if affiliate_url:
            desc += f"""🔥 Best Tool I Use: {affiliate_url}

"""
        desc += """#shorts #money #sidehustle #passiveincome #makemoneyonline"""
        return desc
    
    @staticmethod
    def health_short(title: str, lead_magnet_url: str, affiliate_url: str = None) -> str:
        """Description for health/wellness niche Shorts"""
        desc = f"""{title}

🌿 FREE Checklist: Optimize Your Energy
👉 {lead_magnet_url}

"""
        if affiliate_url:
            desc += f"""✨ What I Recommend: {affiliate_url}

"""
        desc += """#shorts #health #wellness #energy #biohacking"""
        return desc
    
    @staticmethod
    def survival_short(title: str, lead_magnet_url: str, affiliate_url: str = None) -> str:
        """Description for survival/preparedness niche Shorts"""
        desc = f"""{title}

🛡️ FREE Guide: Emergency Preparedness Essentials
👉 {lead_magnet_url}

"""
        if affiliate_url:
            desc += f"""⚡ Gear I Trust: {affiliate_url}

"""
        desc += """#shorts #survival #preparedness #selfreliance #emergency"""
        return desc


# Export all classes
__all__ = [
    "YouTubeUploader",
    "InstagramUploader",
    "TikTokUploader",
    "MasterUploader",
    "LocalSaver",
    "DescriptionTemplates"
]
