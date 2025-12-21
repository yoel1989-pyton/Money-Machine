"""
============================================================
MONEY MACHINE - HUNTER ENGINE
The Aggressive Opportunity Identification System
============================================================
Scans multiple data sources to identify high-ROI content opportunities.
Uses FREE APIs only.
============================================================
"""

import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import Optional
import httpx

# ============================================================
# CONFIGURATION
# ============================================================

class HunterConfig:
    """Hunter Engine Configuration"""
    
    # Niches to monitor (customize based on your channels)
    NICHES = [
        "personal finance",
        "side hustle",
        "passive income",
        "wellness",
        "productivity",
        "self improvement",
        "technology",
        "ai tools"
    ]
    
    # Minimum engagement threshold
    MIN_ENGAGEMENT_SCORE = 50
    
    # Content velocity threshold (posts per hour)
    MIN_VELOCITY = 10
    
    # Sentiment filter (positive content performs better)
    SENTIMENT_BIAS = "positive"


# ============================================================
# REDDIT HUNTER - FREE API
# ============================================================

class RedditHunter:
    """
    Hunts trending topics on Reddit.
    FREE: 60 requests/minute, OAuth required.
    """
    
    def __init__(self):
        self.client_id = os.getenv("REDDIT_CLIENT_ID")
        self.client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        self.user_agent = os.getenv("REDDIT_USER_AGENT", "MoneyMachine/1.0")
        self.access_token = None
        
    async def authenticate(self) -> bool:
        """Get OAuth token from Reddit"""
        if not self.client_id or not self.client_secret:
            print("[HUNTER] Reddit credentials not configured")
            return False
            
        async with httpx.AsyncClient() as client:
            auth = httpx.BasicAuth(self.client_id, self.client_secret)
            response = await client.post(
                "https://www.reddit.com/api/v1/access_token",
                auth=auth,
                data={"grant_type": "client_credentials"},
                headers={"User-Agent": self.user_agent}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token")
                return True
            return False
    
    async def hunt_subreddit(self, subreddit: str, limit: int = 25) -> list:
        """
        Hunt trending posts in a subreddit.
        Returns list of opportunities with scores.
        """
        if not self.access_token:
            await self.authenticate()
            
        opportunities = []
        
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "User-Agent": self.user_agent
            }
            
            # Get hot posts
            response = await client.get(
                f"https://oauth.reddit.com/r/{subreddit}/hot",
                headers=headers,
                params={"limit": limit}
            )
            
            if response.status_code == 200:
                data = response.json()
                posts = data.get("data", {}).get("children", [])
                
                for post in posts:
                    post_data = post.get("data", {})
                    
                    # Calculate opportunity score
                    score = self._calculate_opportunity_score(post_data)
                    
                    if score >= HunterConfig.MIN_ENGAGEMENT_SCORE:
                        opportunities.append({
                            "source": "reddit",
                            "subreddit": subreddit,
                            "title": post_data.get("title"),
                            "score": post_data.get("score"),
                            "comments": post_data.get("num_comments"),
                            "url": f"https://reddit.com{post_data.get('permalink')}",
                            "opportunity_score": score,
                            "content_angle": self._extract_content_angle(post_data),
                            "timestamp": datetime.utcnow().isoformat()
                        })
        
        return sorted(opportunities, key=lambda x: x["opportunity_score"], reverse=True)
    
    def _calculate_opportunity_score(self, post: dict) -> float:
        """Calculate ROI potential score for a post"""
        upvotes = post.get("score", 0)
        comments = post.get("num_comments", 0)
        upvote_ratio = post.get("upvote_ratio", 0.5)
        
        # Engagement velocity (comments indicate active discussion)
        engagement = (upvotes * 0.3) + (comments * 0.7)
        
        # Controversy boost (slightly controversial = more engagement)
        controversy_boost = 1.0 + (0.5 - abs(0.5 - upvote_ratio))
        
        return engagement * controversy_boost
    
    def _extract_content_angle(self, post: dict) -> str:
        """Extract the hook/angle for content creation"""
        title = post.get("title", "")
        
        # Identify content type
        if "?" in title:
            return "answer_question"
        elif any(word in title.lower() for word in ["how", "guide", "tutorial"]):
            return "tutorial"
        elif any(word in title.lower() for word in ["best", "top", "worst"]):
            return "listicle"
        elif any(word in title.lower() for word in ["story", "happened", "experience"]):
            return "story"
        else:
            return "commentary"
    
    async def hunt_multiple(self, subreddits: list) -> list:
        """Hunt across multiple subreddits"""
        all_opportunities = []
        
        for subreddit in subreddits:
            try:
                opportunities = await self.hunt_subreddit(subreddit)
                all_opportunities.extend(opportunities)
            except Exception as e:
                print(f"[HUNTER] Error hunting r/{subreddit}: {e}")
                
        return sorted(all_opportunities, key=lambda x: x["opportunity_score"], reverse=True)


# ============================================================
# NEWS API HUNTER - FREE TIER (100 requests/day)
# ============================================================

class NewsHunter:
    """
    Hunts trending news for content opportunities.
    Uses NewsAPI.org - FREE: 100 requests/day.
    """
    
    def __init__(self):
        self.api_key = os.getenv("NEWSAPI_KEY")
        self.base_url = "https://newsapi.org/v2"
        
    async def get_top_headlines(self, category: str = "business", country: str = "us") -> list:
        """Get top headlines for opportunity identification"""
        if not self.api_key:
            print("[HUNTER] NewsAPI key not configured")
            return []
            
        opportunities = []
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/top-headlines",
                params={
                    "apiKey": self.api_key,
                    "category": category,
                    "country": country,
                    "pageSize": 20
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                for article in data.get("articles", []):
                    # Calculate opportunity score based on engagement signals
                    score = 50  # Base score
                    title = article.get("title", "")
                    
                    # Boost for money-related keywords
                    money_keywords = ["money", "income", "wealth", "invest", "save", "earn", "profit"]
                    if any(kw in title.lower() for kw in money_keywords):
                        score += 20
                    
                    # Boost for trending topics
                    trend_keywords = ["ai", "crypto", "tech", "breakthrough", "new", "2025"]
                    if any(kw in title.lower() for kw in trend_keywords):
                        score += 15
                        
                    opportunities.append({
                        "source": "news",
                        "title": title,
                        "description": article.get("description", ""),
                        "url": article.get("url", ""),
                        "published": article.get("publishedAt", ""),
                        "source_name": article.get("source", {}).get("name", ""),
                        "opportunity_score": score,
                        "content_angle": f"News: {title[:50]}..."
                    })
            else:
                print(f"[HUNTER] NewsAPI error: {response.status_code}")
                
        return sorted(opportunities, key=lambda x: x["opportunity_score"], reverse=True)[:10]
    
    async def search_topic(self, query: str) -> list:
        """Search for news on a specific topic"""
        if not self.api_key:
            return []
            
        opportunities = []
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/everything",
                params={
                    "apiKey": self.api_key,
                    "q": query,
                    "sortBy": "popularity",
                    "pageSize": 10
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                for article in data.get("articles", []):
                    opportunities.append({
                        "source": "news",
                        "title": article.get("title", ""),
                        "description": article.get("description", ""),
                        "url": article.get("url", ""),
                        "opportunity_score": 60,
                        "content_angle": f"Topic: {query}"
                    })
                    
        return opportunities


# ============================================================
# GOOGLE TRENDS HUNTER - FREE (NO API KEY)
# ============================================================

class GoogleTrendsHunter:
    """
    Hunts rising search trends using Google Trends.
    FREE: No API key required, rate limited.
    """
    
    async def get_trending_searches(self, geo: str = "US") -> list:
        """Get daily trending searches"""
        # Using the public RSS feed (free, no auth)
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://trends.google.com/trending/rss?geo={geo}"
            )
            
            if response.status_code == 200:
                # Parse RSS (simplified)
                trends = self._parse_trends_rss(response.text)
                return trends
        
        return []
    
    def _parse_trends_rss(self, rss_content: str) -> list:
        """Parse Google Trends RSS feed"""
        import xml.etree.ElementTree as ET
        
        trends = []
        try:
            root = ET.fromstring(rss_content)
            items = root.findall(".//item")
            
            for item in items[:20]:  # Top 20 trends
                title = item.find("title")
                traffic = item.find("ht:approx_traffic", 
                    {"ht": "https://trends.google.com/trends/trendingsearches/daily"})
                
                if title is not None:
                    trends.append({
                        "source": "google_trends",
                        "keyword": title.text,
                        "traffic": traffic.text if traffic is not None else "Unknown",
                        "timestamp": datetime.utcnow().isoformat()
                    })
        except Exception as e:
            print(f"[HUNTER] Error parsing trends: {e}")
            
        return trends


# ============================================================
# YOUTUBE TRENDS HUNTER - FREE API
# ============================================================

class YouTubeHunter:
    """
    Hunts trending videos and gaps in YouTube.
    FREE: 10,000 quota units/day.
    """
    
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.base_url = "https://www.googleapis.com/youtube/v3"
        
    async def search_niche(self, query: str, max_results: int = 10) -> list:
        """Search for videos in a niche to find gaps"""
        if not self.api_key:
            print("[HUNTER] YouTube API key not configured")
            return []
            
        opportunities = []
        
        async with httpx.AsyncClient() as client:
            # Search for recent videos
            response = await client.get(
                f"{self.base_url}/search",
                params={
                    "key": self.api_key,
                    "q": query,
                    "part": "snippet",
                    "type": "video",
                    "order": "viewCount",
                    "publishedAfter": (datetime.utcnow() - timedelta(days=7)).isoformat() + "Z",
                    "maxResults": max_results
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                videos = data.get("items", [])
                
                # Get video statistics
                video_ids = [v["id"]["videoId"] for v in videos]
                stats = await self._get_video_stats(video_ids)
                
                for video in videos:
                    video_id = video["id"]["videoId"]
                    snippet = video.get("snippet", {})
                    video_stats = stats.get(video_id, {})
                    
                    opportunities.append({
                        "source": "youtube",
                        "title": snippet.get("title"),
                        "channel": snippet.get("channelTitle"),
                        "video_id": video_id,
                        "views": int(video_stats.get("viewCount", 0)),
                        "likes": int(video_stats.get("likeCount", 0)),
                        "comments": int(video_stats.get("commentCount", 0)),
                        "published": snippet.get("publishedAt"),
                        "opportunity_score": self._calculate_yt_score(video_stats),
                        "timestamp": datetime.utcnow().isoformat()
                    })
        
        return sorted(opportunities, key=lambda x: x["opportunity_score"], reverse=True)
    
    async def _get_video_stats(self, video_ids: list) -> dict:
        """Get statistics for multiple videos"""
        if not video_ids:
            return {}
            
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/videos",
                params={
                    "key": self.api_key,
                    "id": ",".join(video_ids),
                    "part": "statistics"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    item["id"]: item.get("statistics", {})
                    for item in data.get("items", [])
                }
        
        return {}
    
    def _calculate_yt_score(self, stats: dict) -> float:
        """Calculate opportunity score for YouTube video"""
        views = int(stats.get("viewCount", 0))
        likes = int(stats.get("likeCount", 0))
        comments = int(stats.get("commentCount", 0))
        
        # Engagement rate
        if views > 0:
            engagement_rate = ((likes + comments) / views) * 100
        else:
            engagement_rate = 0
            
        # Views velocity (recent views = hot topic)
        velocity_score = min(views / 1000, 100)
        
        return (engagement_rate * 10) + velocity_score


# ============================================================
# AFFILIATE OPPORTUNITY HUNTER
# ============================================================

class AffiliateHunter:
    """
    Hunts high-converting affiliate opportunities.
    Analyzes product demand vs content supply gaps.
    """
    
    # High-converting niches with affiliate programs
    AFFILIATE_NICHES = {
        "software": ["clickbank", "jvzoo", "warriorplus"],
        "finance": ["clickbank", "cj", "shareasale"],
        "health": ["clickbank", "digistore24"],
        "education": ["clickbank", "teachable", "skillshare"],
        "ecommerce": ["amazon", "shopify", "etsy"]
    }
    
    async def find_gaps(self, niche: str) -> list:
        """Find content gaps in affiliate niches"""
        opportunities = []
        
        # This would integrate with affiliate network APIs
        # For now, returns structured opportunity data
        
        high_demand_keywords = {
            "software": ["ai tools", "automation software", "productivity apps"],
            "finance": ["budgeting apps", "investing for beginners", "side hustle ideas"],
            "health": ["weight loss supplements", "fitness equipment", "wellness products"],
            "education": ["online courses", "skill development", "certification programs"]
        }
        
        for keyword in high_demand_keywords.get(niche, []):
            opportunities.append({
                "source": "affiliate",
                "niche": niche,
                "keyword": keyword,
                "estimated_commission": "$20-100/sale",
                "competition": "medium",
                "content_type": "review",
                "timestamp": datetime.utcnow().isoformat()
            })
            
        return opportunities


# ============================================================
# MASTER HUNTER - ORCHESTRATOR
# ============================================================

class MasterHunter:
    """
    Master Hunter that orchestrates all hunting engines.
    Called by n8n to get the best opportunities.
    """
    
    def __init__(self):
        self.reddit = RedditHunter()
        self.google = GoogleTrendsHunter()
        self.youtube = YouTubeHunter()
        self.affiliate = AffiliateHunter()
        self.news = NewsHunter()
        
    async def hunt(self, niches: list = None) -> dict:
        """
        Execute a full hunt across all sources.
        Returns prioritized opportunities.
        """
        if niches is None:
            niches = HunterConfig.NICHES
            
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "reddit": [],
            "google_trends": [],
            "youtube": [],
            "affiliate": [],
            "news": [],
            "top_opportunities": []
        }
        
        # Hunt Reddit
        subreddits = [
            "entrepreneur", "passive_income", "sidehustle",
            "financialindependence", "beermoney", "WorkOnline"
        ]
        results["reddit"] = await self.reddit.hunt_multiple(subreddits)
        
        # Hunt Google Trends
        results["google_trends"] = await self.google.get_trending_searches()
        
        # Hunt News (NewsAPI)
        news_categories = ["business", "technology"]
        for category in news_categories:
            news_results = await self.news.get_top_headlines(category)
            results["news"].extend(news_results)
        
        # Hunt YouTube (if API key configured)
        for niche in niches[:3]:  # Limit to conserve API quota
            yt_results = await self.youtube.search_niche(niche)
            results["youtube"].extend(yt_results)
        
        # Hunt Affiliate Opportunities
        for niche in ["software", "finance", "health"]:
            aff_results = await self.affiliate.find_gaps(niche)
            results["affiliate"].extend(aff_results)
        
        # Compile top opportunities
        all_opps = []
        for source in ["reddit", "youtube", "news"]:
            for opp in results[source][:5]:
                all_opps.append(opp)
        
        results["top_opportunities"] = sorted(
            all_opps,
            key=lambda x: x.get("opportunity_score", 0),
            reverse=True
        )[:10]
        
        return results
    
    async def quick_hunt(self, source: str, query: str = None) -> list:
        """Quick hunt on a single source"""
        if source == "reddit" and query:
            return await self.reddit.hunt_subreddit(query)
        elif source == "youtube" and query:
            return await self.youtube.search_niche(query)
        elif source == "trends":
            return await self.google.get_trending_searches()
        else:
            return []


# ============================================================
# CLI INTERFACE (for n8n Execute Command node)
# ============================================================

if __name__ == "__main__":
    import sys
    
    async def main():
        hunter = MasterHunter()
        
        if len(sys.argv) > 1:
            command = sys.argv[1]
            
            if command == "full":
                results = await hunter.hunt()
            elif command == "reddit" and len(sys.argv) > 2:
                results = await hunter.quick_hunt("reddit", sys.argv[2])
            elif command == "youtube" and len(sys.argv) > 2:
                results = await hunter.quick_hunt("youtube", sys.argv[2])
            elif command == "trends":
                results = await hunter.quick_hunt("trends")
            else:
                results = {"error": "Unknown command"}
        else:
            results = await hunter.hunt()
        
        print(json.dumps(results, indent=2))
    
    asyncio.run(main())
