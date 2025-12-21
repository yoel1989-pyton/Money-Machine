"""
============================================================
MONEY MACHINE - GATHERER ENGINE
The Omni-Channel Distribution System
============================================================
Distributes content assets across all platforms.
Uses OFFICIAL APIs only - compliant and sustainable.
============================================================
"""

import os
import json
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import httpx

# ============================================================
# CONFIGURATION
# ============================================================

class GathererConfig:
    """Gatherer Engine Configuration"""
    
    # Optimal posting times (EST)
    OPTIMAL_TIMES = {
        "youtube": ["12:00", "15:00", "18:00"],
        "tiktok": ["07:00", "12:00", "19:00", "22:00"],
        "instagram": ["11:00", "14:00", "19:00"],
        "pinterest": ["20:00", "21:00"],
        "reddit": ["08:00", "12:00", "17:00"]
    }
    
    # Daily limits (to stay under rate limits)
    DAILY_LIMITS = {
        "youtube": 6,  # API quota
        "tiktok": 10,
        "instagram": 5,
        "pinterest": 25,
        "reddit": 10
    }


# ============================================================
# YOUTUBE GATHERER (Official Data API v3)
# ============================================================

class YouTubeGatherer:
    """
    Upload and manage YouTube content.
    FREE: 10,000 quota units/day
    Upload = 1600 units, so ~6 uploads/day
    """
    
    def __init__(self):
        self.client_id = os.getenv("YOUTUBE_CLIENT_ID")
        self.client_secret = os.getenv("YOUTUBE_CLIENT_SECRET")
        self.refresh_token = os.getenv("YOUTUBE_REFRESH_TOKEN")
        self.access_token = None
        
    async def authenticate(self) -> bool:
        """Refresh OAuth access token"""
        if not all([self.client_id, self.client_secret, self.refresh_token]):
            print("[GATHERER] YouTube credentials not configured")
            return False
            
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
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
                return True
                
        return False
    
    async def upload_video(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: list = None,
        category_id: str = "22",  # People & Blogs
        privacy: str = "private",  # Start private for Content ID check
        is_short: bool = True
    ) -> dict:
        """
        Upload video to YouTube via resumable upload.
        """
        if not self.access_token:
            await self.authenticate()
            
        if not self.access_token:
            return {"success": False, "error": "Authentication failed"}
        
        # Add #Shorts tag for Shorts
        if is_short and "#Shorts" not in (tags or []):
            tags = (tags or []) + ["#Shorts"]
        
        metadata = {
            "snippet": {
                "title": title[:100],  # Max 100 chars
                "description": description[:5000],
                "tags": tags[:500] if tags else [],
                "categoryId": category_id
            },
            "status": {
                "privacyStatus": privacy,
                "selfDeclaredMadeForKids": False
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                # Step 1: Initialize resumable upload
                init_response = await client.post(
                    "https://www.googleapis.com/upload/youtube/v3/videos",
                    params={
                        "uploadType": "resumable",
                        "part": "snippet,status"
                    },
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": "application/json",
                        "X-Upload-Content-Type": "video/*"
                    },
                    json=metadata
                )
                
                if init_response.status_code != 200:
                    return {
                        "success": False,
                        "error": f"Init failed: {init_response.text}"
                    }
                
                upload_url = init_response.headers.get("Location")
                
                # Step 2: Upload video file
                with open(video_path, "rb") as video_file:
                    video_data = video_file.read()
                    
                upload_response = await client.put(
                    upload_url,
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": "video/*"
                    },
                    content=video_data,
                    timeout=600  # 10 min timeout for large files
                )
                
                if upload_response.status_code == 200:
                    data = upload_response.json()
                    return {
                        "success": True,
                        "video_id": data.get("id"),
                        "url": f"https://youtube.com/watch?v={data.get('id')}",
                        "platform": "youtube"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Upload failed: {upload_response.text}"
                    }
                    
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def update_privacy(self, video_id: str, privacy: str) -> bool:
        """Update video privacy (after Content ID check passes)"""
        if not self.access_token:
            await self.authenticate()
            
        async with httpx.AsyncClient() as client:
            response = await client.put(
                "https://www.googleapis.com/youtube/v3/videos",
                params={"part": "status"},
                headers={"Authorization": f"Bearer {self.access_token}"},
                json={
                    "id": video_id,
                    "status": {"privacyStatus": privacy}
                }
            )
            
            return response.status_code == 200
    
    async def get_video_status(self, video_id: str) -> dict:
        """Check video status (for Content ID claims)"""
        if not self.access_token:
            await self.authenticate()
            
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/youtube/v3/videos",
                params={
                    "part": "status,contentDetails",
                    "id": video_id
                },
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                if items:
                    return items[0]
        
        return {}


# ============================================================
# TIKTOK GATHERER (Official Content Posting API)
# ============================================================

class TikTokGatherer:
    """
    Upload content to TikTok.
    Uses Official TikTok API for Creators.
    """
    
    def __init__(self):
        self.client_key = os.getenv("TIKTOK_CLIENT_KEY")
        self.client_secret = os.getenv("TIKTOK_CLIENT_SECRET")
        self.access_token = os.getenv("TIKTOK_ACCESS_TOKEN")
        
    async def upload_video(
        self,
        video_path: str,
        description: str,
        hashtags: list = None
    ) -> dict:
        """
        Upload video to TikTok via Official API.
        """
        if not self.access_token:
            return {"success": False, "error": "TikTok not authenticated"}
        
        # Add hashtags to description
        if hashtags:
            hashtag_str = " ".join([f"#{h}" for h in hashtags])
            description = f"{description} {hashtag_str}"
        
        try:
            async with httpx.AsyncClient() as client:
                # Step 1: Initialize upload
                init_response = await client.post(
                    "https://open.tiktokapis.com/v2/post/publish/inbox/video/init/",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "source_info": {
                            "source": "FILE_UPLOAD",
                            "video_size": os.path.getsize(video_path)
                        }
                    }
                )
                
                if init_response.status_code != 200:
                    return {
                        "success": False,
                        "error": f"TikTok init failed: {init_response.text}"
                    }
                
                data = init_response.json()
                upload_url = data.get("data", {}).get("upload_url")
                publish_id = data.get("data", {}).get("publish_id")
                
                # Step 2: Upload video
                with open(video_path, "rb") as f:
                    upload_response = await client.put(
                        upload_url,
                        headers={"Content-Type": "video/mp4"},
                        content=f.read()
                    )
                
                if upload_response.status_code == 200:
                    return {
                        "success": True,
                        "publish_id": publish_id,
                        "platform": "tiktok"
                    }
                else:
                    return {
                        "success": False,
                        "error": "Upload failed"
                    }
                    
        except Exception as e:
            return {"success": False, "error": str(e)}


# ============================================================
# INSTAGRAM GATHERER (Meta Content Publishing API)
# ============================================================

class InstagramGatherer:
    """
    Upload content to Instagram.
    Uses Meta Graph API (official).
    """
    
    def __init__(self):
        self.access_token = os.getenv("META_ACCESS_TOKEN")
        self.ig_user_id = os.getenv("INSTAGRAM_BUSINESS_ID")
        
    async def upload_reel(
        self,
        video_url: str,  # Must be publicly accessible URL
        caption: str,
        hashtags: list = None
    ) -> dict:
        """
        Upload a Reel to Instagram.
        Note: Video must be hosted at a public URL.
        """
        if not self.access_token or not self.ig_user_id:
            return {"success": False, "error": "Instagram not configured"}
        
        # Add hashtags
        if hashtags:
            hashtag_str = " ".join([f"#{h}" for h in hashtags])
            caption = f"{caption}\n\n{hashtag_str}"
        
        try:
            async with httpx.AsyncClient() as client:
                # Step 1: Create container
                container_response = await client.post(
                    f"https://graph.facebook.com/v18.0/{self.ig_user_id}/media",
                    params={
                        "access_token": self.access_token,
                        "media_type": "REELS",
                        "video_url": video_url,
                        "caption": caption
                    }
                )
                
                if container_response.status_code != 200:
                    return {
                        "success": False,
                        "error": f"Container failed: {container_response.text}"
                    }
                
                container_id = container_response.json().get("id")
                
                # Step 2: Wait for processing (poll status)
                for _ in range(30):  # Max 5 min wait
                    status_response = await client.get(
                        f"https://graph.facebook.com/v18.0/{container_id}",
                        params={
                            "access_token": self.access_token,
                            "fields": "status_code"
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
                    f"https://graph.facebook.com/v18.0/{self.ig_user_id}/media_publish",
                    params={
                        "access_token": self.access_token,
                        "creation_id": container_id
                    }
                )
                
                if publish_response.status_code == 200:
                    return {
                        "success": True,
                        "media_id": publish_response.json().get("id"),
                        "platform": "instagram"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Publish failed: {publish_response.text}"
                    }
                    
        except Exception as e:
            return {"success": False, "error": str(e)}


# ============================================================
# PINTEREST GATHERER (Official API)
# ============================================================

class PinterestGatherer:
    """
    Upload pins to Pinterest.
    Uses Official Pinterest API.
    """
    
    def __init__(self):
        self.access_token = os.getenv("PINTEREST_ACCESS_TOKEN")
        
    async def create_pin(
        self,
        image_url: str,
        title: str,
        description: str,
        link: str,
        board_id: str
    ) -> dict:
        """Create a pin on Pinterest"""
        if not self.access_token:
            return {"success": False, "error": "Pinterest not configured"}
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.pinterest.com/v5/pins",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "board_id": board_id,
                        "title": title[:100],
                        "description": description[:500],
                        "link": link,
                        "media_source": {
                            "source_type": "image_url",
                            "url": image_url
                        }
                    }
                )
                
                if response.status_code == 201:
                    data = response.json()
                    return {
                        "success": True,
                        "pin_id": data.get("id"),
                        "platform": "pinterest"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Pin failed: {response.text}"
                    }
                    
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def create_video_pin(
        self,
        video_url: str,
        title: str,
        description: str,
        board_id: str
    ) -> dict:
        """Create a video pin (Idea Pin)"""
        if not self.access_token:
            return {"success": False, "error": "Pinterest not configured"}
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.pinterest.com/v5/pins",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "board_id": board_id,
                        "title": title[:100],
                        "description": description[:500],
                        "media_source": {
                            "source_type": "video_id",
                            "cover_image_url": video_url.replace(".mp4", "_thumb.jpg"),
                            "media_id": video_url  # This needs video upload first
                        }
                    }
                )
                
                return {
                    "success": response.status_code == 201,
                    "platform": "pinterest"
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}


# ============================================================
# EMAIL LIST GATHERER (Beehiiv)
# ============================================================

class EmailGatherer:
    """
    Manage email list growth.
    Uses Beehiiv API (FREE up to 2,500 subscribers).
    """
    
    def __init__(self):
        self.api_key = os.getenv("BEEHIIV_API_KEY")
        self.publication_id = os.getenv("BEEHIIV_PUBLICATION_ID")
        
    async def add_subscriber(
        self,
        email: str,
        source: str = "money_machine"
    ) -> dict:
        """Add a subscriber to the email list"""
        if not self.api_key or not self.publication_id:
            return {"success": False, "error": "Beehiiv not configured"}
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://api.beehiiv.com/v2/publications/{self.publication_id}/subscriptions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "email": email,
                        "reactivate_existing": True,
                        "send_welcome_email": True,
                        "utm_source": source
                    }
                )
                
                return {
                    "success": response.status_code in [200, 201],
                    "platform": "email"
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_subscriber_count(self) -> int:
        """Get total subscriber count"""
        if not self.api_key or not self.publication_id:
            return 0
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.beehiiv.com/v2/publications/{self.publication_id}",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("data", {}).get("stats", {}).get("total_subscribers", 0)
                    
        except Exception:
            pass
            
        return 0


# ============================================================
# MASTER GATHERER - ORCHESTRATOR
# ============================================================

class MasterGatherer:
    """
    Master Gatherer that orchestrates all distribution.
    Omni-alignment: One asset → All platforms simultaneously.
    """
    
    def __init__(self):
        self.youtube = YouTubeGatherer()
        self.tiktok = TikTokGatherer()
        self.instagram = InstagramGatherer()
        self.pinterest = PinterestGatherer()
        self.email = EmailGatherer()
        
        # Track daily uploads
        self.daily_counts = {
            "youtube": 0,
            "tiktok": 0,
            "instagram": 0,
            "pinterest": 0
        }
        self.last_reset = datetime.utcnow().date()
        
    def _check_limits(self, platform: str) -> bool:
        """Check if we're under daily limits"""
        # Reset counts at midnight
        today = datetime.utcnow().date()
        if today != self.last_reset:
            self.daily_counts = {k: 0 for k in self.daily_counts}
            self.last_reset = today
            
        return self.daily_counts.get(platform, 0) < GathererConfig.DAILY_LIMITS.get(platform, 10)
    
    async def distribute(
        self,
        video_path: str,
        title: str,
        description: str,
        hashtags: list = None,
        platforms: list = None
    ) -> dict:
        """
        Distribute content to all specified platforms.
        """
        if platforms is None:
            platforms = ["youtube", "tiktok"]
        
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "video_path": video_path,
            "platforms": {}
        }
        
        # Distribute to each platform
        for platform in platforms:
            if not self._check_limits(platform):
                results["platforms"][platform] = {
                    "success": False,
                    "error": "Daily limit reached"
                }
                continue
                
            try:
                if platform == "youtube":
                    result = await self.youtube.upload_video(
                        video_path, title, description, hashtags
                    )
                elif platform == "tiktok":
                    result = await self.tiktok.upload_video(
                        video_path, description, hashtags
                    )
                else:
                    result = {"success": False, "error": f"Platform {platform} not implemented"}
                
                results["platforms"][platform] = result
                
                if result.get("success"):
                    self.daily_counts[platform] = self.daily_counts.get(platform, 0) + 1
                    
            except Exception as e:
                results["platforms"][platform] = {
                    "success": False,
                    "error": str(e)
                }
        
        # Calculate success rate
        successes = sum(1 for p in results["platforms"].values() if p.get("success"))
        results["success_rate"] = f"{successes}/{len(platforms)}"
        
        return results
    
    async def distribute_omni(
        self,
        assets: dict,
        metadata: dict
    ) -> dict:
        """
        Full omni-channel distribution.
        Takes pre-formatted assets for each platform.
        """
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "distributions": []
        }
        
        # YouTube Short
        if "youtube_short" in assets:
            yt_result = await self.youtube.upload_video(
                assets["youtube_short"],
                metadata.get("title", ""),
                metadata.get("description", ""),
                metadata.get("hashtags", []),
                is_short=True
            )
            results["distributions"].append({
                "platform": "youtube",
                "type": "short",
                **yt_result
            })
        
        # TikTok
        if "tiktok" in assets:
            tt_result = await self.tiktok.upload_video(
                assets["tiktok"],
                metadata.get("description", ""),
                metadata.get("hashtags", [])
            )
            results["distributions"].append({
                "platform": "tiktok",
                **tt_result
            })
        
        return results
    
    async def get_stats(self) -> dict:
        """Get distribution statistics"""
        return {
            "daily_uploads": self.daily_counts,
            "limits": GathererConfig.DAILY_LIMITS,
            "email_subscribers": await self.email.get_subscriber_count()
        }


# ============================================================
# CLI INTERFACE
# ============================================================

if __name__ == "__main__":
    import sys
    
    async def main():
        gatherer = MasterGatherer()
        
        if len(sys.argv) > 1:
            command = sys.argv[1]
            
            if command == "stats":
                result = await gatherer.get_stats()
            elif command == "distribute" and len(sys.argv) > 4:
                video_path = sys.argv[2]
                title = sys.argv[3]
                description = sys.argv[4]
                result = await gatherer.distribute(video_path, title, description)
            else:
                result = {"error": "Usage: gatherer.py [stats|distribute <path> <title> <desc>]"}
        else:
            result = await gatherer.get_stats()
        
        print(json.dumps(result, indent=2))
    
    asyncio.run(main())
