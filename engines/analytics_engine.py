"""
===============================================================================
ANALYTICS ENGINE - YouTube Performance Feedback Loop
===============================================================================
Pulls YouTube analytics, identifies winners, and feeds mutations back to content.

MUTATION RULES:
- AVD < 50% → STRENGTHEN_HOOK (pattern interrupt intensity)
- CTR < 3% → OPTIMIZE_THUMBNAIL (high contrast, expressions)
- Engagement < 3% → ADD_CONTROVERSY (provocative statements)
- RPM < $0.03 → SHIFT_NICHE (higher CPM topics)

WINNER THRESHOLDS:
- AVD > 75%
- RPM > $0.05
- Views > 1000
- Engagement > 5%
===============================================================================
"""

import os
import json
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
import httpx

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class VideoMetrics:
    """Performance metrics for a single video."""
    video_id: str
    title: str
    published_at: str
    
    # Core metrics
    views: int = 0
    watch_time_minutes: float = 0.0
    average_view_duration: float = 0.0  # Seconds
    average_view_percentage: float = 0.0  # AVD %
    
    # Engagement metrics
    likes: int = 0
    comments: int = 0
    shares: int = 0
    engagement_rate: float = 0.0  # (likes + comments + shares) / views
    
    # Revenue metrics
    estimated_revenue: float = 0.0
    rpm: float = 0.0  # Revenue per 1000 views
    cpm: float = 0.0  # Cost per 1000 impressions
    
    # Click metrics
    impressions: int = 0
    ctr: float = 0.0  # Click-through rate
    
    # Content DNA (from original generation)
    topic: str = ""
    archetype: str = ""
    visual_intent: str = ""
    providers_used: List[str] = field(default_factory=list)
    
    # Analysis
    is_winner: bool = False
    expansion_eligible: bool = False
    suggested_mutations: List[str] = field(default_factory=list)


@dataclass
class MutationRule:
    """A rule that triggers content mutations."""
    condition: str
    metric: str
    threshold: float
    comparison: str  # "lt" (less than) or "gt" (greater than)
    action: str
    adjustment: str
    priority: int = 1


@dataclass
class AnalyticsReport:
    """Aggregated analytics report."""
    scan_time: str
    total_videos: int
    winners: List[VideoMetrics]
    losers: List[VideoMetrics]
    mutations_triggered: List[Dict]
    summary: Dict


# ============================================================================
# CONFIGURATION
# ============================================================================

WINNER_THRESHOLDS = {
    "min_avd": 75.0,          # Average View Duration %
    "min_rpm": 0.05,          # Revenue per 1000 views
    "min_views": 1000,        # Minimum views to qualify
    "min_engagement": 5.0,    # Engagement rate %
    "min_ctr": 4.0,           # Click-through rate %
}

MUTATION_RULES = [
    MutationRule(
        condition="AVD < 50%",
        metric="average_view_percentage",
        threshold=50.0,
        comparison="lt",
        action="STRENGTHEN_HOOK",
        adjustment="Increase pattern interrupt intensity in first 3 seconds",
        priority=1
    ),
    MutationRule(
        condition="CTR < 3%",
        metric="ctr",
        threshold=3.0,
        comparison="lt",
        action="OPTIMIZE_THUMBNAIL",
        adjustment="Test high-contrast colors and facial expressions",
        priority=2
    ),
    MutationRule(
        condition="Engagement < 3%",
        metric="engagement_rate",
        threshold=3.0,
        comparison="lt",
        action="ADD_CONTROVERSY",
        adjustment="Increase provocative statements and open loops",
        priority=3
    ),
    MutationRule(
        condition="RPM < $0.03",
        metric="rpm",
        threshold=0.03,
        comparison="lt",
        action="SHIFT_NICHE",
        adjustment="Move toward higher CPM topics (investing > budgeting)",
        priority=4
    ),
    MutationRule(
        condition="Views < 100 in 24h",
        metric="views",
        threshold=100,
        comparison="lt",
        action="BOOST_DISTRIBUTION",
        adjustment="Cross-post to other platforms, use trending hashtags",
        priority=5
    ),
]

# DNA log file
DNA_LOG_PATH = Path(__file__).parent.parent / "data" / "metrics" / "content_dna.json"
ANALYTICS_LOG_PATH = Path(__file__).parent.parent / "data" / "metrics" / "analytics_history.json"


# ============================================================================
# YOUTUBE ANALYTICS CLIENT
# ============================================================================

class YouTubeAnalyticsClient:
    """Client for YouTube Analytics API."""
    
    def __init__(self):
        self.api_key = os.getenv("YOUTUBE_API_KEY")
        self.channel_id = os.getenv("YOUTUBE_CHANNEL_ID")
        self.refresh_token = os.getenv("YOUTUBE_REFRESH_TOKEN")
        self.client_id = os.getenv("YOUTUBE_CLIENT_ID")
        self.client_secret = os.getenv("YOUTUBE_CLIENT_SECRET")
        self.access_token = None
        self.base_url = "https://www.googleapis.com/youtube/v3"
        self.analytics_url = "https://youtubeanalytics.googleapis.com/v2"
    
    async def _refresh_access_token(self) -> Optional[str]:
        """Refresh OAuth access token."""
        if not all([self.refresh_token, self.client_id, self.client_secret]):
            print("⚠️ Missing OAuth credentials for token refresh")
            return None
        
        try:
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
                    return self.access_token
                else:
                    print(f"❌ Token refresh failed: {response.status_code}")
                    return None
        except Exception as e:
            print(f"❌ Token refresh error: {e}")
            return None
    
    async def get_channel_videos(self, max_results: int = 50) -> List[Dict]:
        """Get recent videos from channel."""
        if not self.access_token:
            await self._refresh_access_token()
        
        if not self.access_token:
            return []
        
        try:
            async with httpx.AsyncClient() as client:
                # Get uploads playlist
                response = await client.get(
                    f"{self.base_url}/channels",
                    params={
                        "part": "contentDetails",
                        "id": self.channel_id,
                        "key": self.api_key
                    },
                    headers={"Authorization": f"Bearer {self.access_token}"}
                )
                
                if response.status_code != 200:
                    print(f"❌ Failed to get channel: {response.status_code}")
                    return []
                
                data = response.json()
                uploads_id = data["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
                
                # Get videos from uploads playlist
                response = await client.get(
                    f"{self.base_url}/playlistItems",
                    params={
                        "part": "snippet,contentDetails",
                        "playlistId": uploads_id,
                        "maxResults": max_results,
                        "key": self.api_key
                    },
                    headers={"Authorization": f"Bearer {self.access_token}"}
                )
                
                if response.status_code == 200:
                    return response.json().get("items", [])
                
                return []
                
        except Exception as e:
            print(f"❌ Error getting videos: {e}")
            return []
    
    async def get_video_stats(self, video_id: str) -> Dict:
        """Get statistics for a single video."""
        if not self.access_token:
            await self._refresh_access_token()
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/videos",
                    params={
                        "part": "statistics,contentDetails,snippet",
                        "id": video_id,
                        "key": self.api_key
                    },
                    headers={"Authorization": f"Bearer {self.access_token}"} if self.access_token else {}
                )
                
                if response.status_code == 200:
                    items = response.json().get("items", [])
                    return items[0] if items else {}
                
                return {}
                
        except Exception as e:
            print(f"❌ Error getting video stats: {e}")
            return {}
    
    async def get_video_analytics(self, video_id: str, start_date: str = None, end_date: str = None) -> Dict:
        """Get detailed analytics for a video (requires OAuth)."""
        if not self.access_token:
            await self._refresh_access_token()
        
        if not self.access_token:
            return {}
        
        if not start_date:
            start_date = (datetime.now() - timedelta(days=28)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.analytics_url}/reports",
                    params={
                        "ids": f"channel=={self.channel_id}",
                        "startDate": start_date,
                        "endDate": end_date,
                        "metrics": "views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,likes,comments,shares,estimatedRevenue,cpm",
                        "dimensions": "video",
                        "filters": f"video=={video_id}",
                        "sort": "-views"
                    },
                    headers={"Authorization": f"Bearer {self.access_token}"}
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"❌ Analytics API error: {response.status_code} - {response.text[:200]}")
                    return {}
                    
        except Exception as e:
            print(f"❌ Analytics error: {e}")
            return {}


# ============================================================================
# ANALYTICS ENGINE
# ============================================================================

class AnalyticsEngine:
    """Main analytics engine for performance feedback loop."""
    
    def __init__(self):
        self.youtube = YouTubeAnalyticsClient()
        self.dna_log = self._load_dna_log()
        self.analytics_history = self._load_analytics_history()
    
    def _load_dna_log(self) -> List[Dict]:
        """Load content DNA log."""
        DNA_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        if DNA_LOG_PATH.exists():
            try:
                return json.loads(DNA_LOG_PATH.read_text())
            except:
                return []
        return []
    
    def _save_dna_log(self):
        """Save content DNA log."""
        DNA_LOG_PATH.write_text(json.dumps(self.dna_log, indent=2))
    
    def _load_analytics_history(self) -> List[Dict]:
        """Load analytics scan history."""
        ANALYTICS_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        if ANALYTICS_LOG_PATH.exists():
            try:
                return json.loads(ANALYTICS_LOG_PATH.read_text())
            except:
                return []
        return []
    
    def _save_analytics_history(self):
        """Save analytics history."""
        ANALYTICS_LOG_PATH.write_text(json.dumps(self.analytics_history[-100:], indent=2))  # Keep last 100
    
    def log_video_dna(self, video_data: Dict):
        """Log a new video's content DNA for future analysis."""
        dna_record = {
            "video_id": video_data.get("video_id"),
            "title": video_data.get("title"),
            "topic": video_data.get("topic"),
            "archetype": video_data.get("archetype"),
            "visual_intent": video_data.get("visual_intent"),
            "providers_used": video_data.get("providers_used", []),
            "styles_used": video_data.get("styles_used", []),
            "word_count": video_data.get("word_count"),
            "duration": video_data.get("duration"),
            "published_at": datetime.now().isoformat(),
            "metrics_updated_at": None,
            "is_winner": False,
            "expansion_eligible": False
        }
        
        self.dna_log.append(dna_record)
        self._save_dna_log()
        print(f"📝 Logged DNA for: {video_data.get('title', 'Unknown')}")
    
    async def scan_performance(self, days_back: int = 7) -> AnalyticsReport:
        """Scan all recent videos for performance metrics."""
        print(f"\n📊 Scanning YouTube performance (last {days_back} days)...")
        
        videos = await self.youtube.get_channel_videos(max_results=50)
        
        if not videos:
            print("⚠️ No videos found or API access issue")
            return AnalyticsReport(
                scan_time=datetime.now().isoformat(),
                total_videos=0,
                winners=[],
                losers=[],
                mutations_triggered=[],
                summary={"error": "No videos found"}
            )
        
        all_metrics = []
        winners = []
        losers = []
        
        for video in videos:
            video_id = video["contentDetails"]["videoId"]
            snippet = video["snippet"]
            
            # Get detailed stats
            stats = await self.youtube.get_video_stats(video_id)
            analytics = await self.youtube.get_video_analytics(video_id)
            
            # Build metrics object
            metrics = VideoMetrics(
                video_id=video_id,
                title=snippet.get("title", ""),
                published_at=snippet.get("publishedAt", "")
            )
            
            # Populate from stats
            if stats and "statistics" in stats:
                s = stats["statistics"]
                metrics.views = int(s.get("viewCount", 0))
                metrics.likes = int(s.get("likeCount", 0))
                metrics.comments = int(s.get("commentCount", 0))
                
                if metrics.views > 0:
                    metrics.engagement_rate = ((metrics.likes + metrics.comments) / metrics.views) * 100
            
            # Populate from analytics
            if analytics and "rows" in analytics:
                row = analytics["rows"][0] if analytics["rows"] else []
                if len(row) >= 9:
                    metrics.watch_time_minutes = row[1]
                    metrics.average_view_duration = row[2]
                    metrics.average_view_percentage = row[3]
                    metrics.estimated_revenue = row[7] if len(row) > 7 else 0
                    metrics.cpm = row[8] if len(row) > 8 else 0
                    
                    if metrics.views > 0:
                        metrics.rpm = (metrics.estimated_revenue / metrics.views) * 1000
            
            # Match with DNA log
            for dna in self.dna_log:
                if dna.get("video_id") == video_id:
                    metrics.topic = dna.get("topic", "")
                    metrics.archetype = dna.get("archetype", "")
                    metrics.visual_intent = dna.get("visual_intent", "")
                    metrics.providers_used = dna.get("providers_used", [])
                    break
            
            # Check if winner
            metrics.is_winner = self._is_winner(metrics)
            metrics.expansion_eligible = metrics.is_winner and metrics.views >= 1000
            metrics.suggested_mutations = self._get_mutations(metrics)
            
            all_metrics.append(metrics)
            
            if metrics.is_winner:
                winners.append(metrics)
            elif metrics.views >= 100:  # Only consider losers with some views
                losers.append(metrics)
        
        # Build report
        report = AnalyticsReport(
            scan_time=datetime.now().isoformat(),
            total_videos=len(all_metrics),
            winners=winners,
            losers=losers[:10],  # Top 10 losers for mutation
            mutations_triggered=self._aggregate_mutations(all_metrics),
            summary=self._build_summary(all_metrics, winners)
        )
        
        # Save to history
        self.analytics_history.append({
            "scan_time": report.scan_time,
            "total_videos": report.total_videos,
            "winners_count": len(winners),
            "top_winner": winners[0].title if winners else None,
            "mutations": len(report.mutations_triggered)
        })
        self._save_analytics_history()
        
        return report
    
    def _is_winner(self, metrics: VideoMetrics) -> bool:
        """Check if video meets winner thresholds."""
        return (
            metrics.average_view_percentage >= WINNER_THRESHOLDS["min_avd"] and
            metrics.views >= WINNER_THRESHOLDS["min_views"] and
            (metrics.engagement_rate >= WINNER_THRESHOLDS["min_engagement"] or
             metrics.rpm >= WINNER_THRESHOLDS["min_rpm"])
        )
    
    def _get_mutations(self, metrics: VideoMetrics) -> List[str]:
        """Get suggested mutations based on metrics."""
        mutations = []
        
        for rule in MUTATION_RULES:
            value = getattr(metrics, rule.metric, None)
            if value is None:
                continue
            
            triggered = False
            if rule.comparison == "lt" and value < rule.threshold:
                triggered = True
            elif rule.comparison == "gt" and value > rule.threshold:
                triggered = True
            
            if triggered:
                mutations.append(f"{rule.action}: {rule.adjustment}")
        
        return mutations
    
    def _aggregate_mutations(self, all_metrics: List[VideoMetrics]) -> List[Dict]:
        """Aggregate mutation suggestions across all videos."""
        mutation_counts = {}
        
        for metrics in all_metrics:
            for mutation in metrics.suggested_mutations:
                action = mutation.split(":")[0]
                if action not in mutation_counts:
                    mutation_counts[action] = {"count": 0, "videos": [], "adjustment": mutation}
                mutation_counts[action]["count"] += 1
                mutation_counts[action]["videos"].append(metrics.title[:50])
        
        # Sort by frequency
        return sorted(
            [{"action": k, **v} for k, v in mutation_counts.items()],
            key=lambda x: x["count"],
            reverse=True
        )
    
    def _build_summary(self, all_metrics: List[VideoMetrics], winners: List[VideoMetrics]) -> Dict:
        """Build analytics summary."""
        if not all_metrics:
            return {"status": "no_data"}
        
        total_views = sum(m.views for m in all_metrics)
        total_revenue = sum(m.estimated_revenue for m in all_metrics)
        avg_avd = sum(m.average_view_percentage for m in all_metrics) / len(all_metrics)
        avg_engagement = sum(m.engagement_rate for m in all_metrics) / len(all_metrics)
        
        return {
            "total_videos_analyzed": len(all_metrics),
            "total_views": total_views,
            "total_revenue": f"${total_revenue:.2f}",
            "average_avd": f"{avg_avd:.1f}%",
            "average_engagement": f"{avg_engagement:.2f}%",
            "winners_count": len(winners),
            "winner_rate": f"{(len(winners) / len(all_metrics) * 100):.1f}%",
            "top_performer": winners[0].title if winners else "None",
            "expansion_candidates": len([w for w in winners if w.expansion_eligible])
        }
    
    async def get_winner_dna(self) -> List[Dict]:
        """Get DNA of winning videos for content mutation."""
        report = await self.scan_performance()
        
        winner_dna = []
        for winner in report.winners:
            winner_dna.append({
                "topic": winner.topic,
                "archetype": winner.archetype,
                "visual_intent": winner.visual_intent,
                "providers_used": winner.providers_used,
                "metrics": {
                    "views": winner.views,
                    "avd": winner.average_view_percentage,
                    "engagement": winner.engagement_rate,
                    "rpm": winner.rpm
                }
            })
        
        return winner_dna
    
    async def generate_mutation_prompt(self) -> str:
        """Generate a prompt for AI to mutate content based on analytics."""
        report = await self.scan_performance()
        
        if not report.winners:
            return "No winning patterns detected yet. Continue with current strategy."
        
        prompt = f"""Based on YouTube Analytics, here's what's working:

TOP PERFORMERS ({len(report.winners)} winners):
"""
        
        for winner in report.winners[:3]:
            prompt += f"""
- "{winner.title}"
  Views: {winner.views}, AVD: {winner.average_view_percentage:.1f}%, Engagement: {winner.engagement_rate:.2f}%
  Topic: {winner.topic}, Archetype: {winner.archetype}
"""
        
        prompt += f"""
MUTATIONS NEEDED (based on underperformers):
"""
        
        for mutation in report.mutations_triggered[:5]:
            prompt += f"- {mutation['action']}: {mutation['count']} videos need this\n"
        
        prompt += f"""
SUMMARY:
- Average AVD: {report.summary.get('average_avd', 'N/A')}
- Winner Rate: {report.summary.get('winner_rate', 'N/A')}
- Expansion Candidates: {report.summary.get('expansion_candidates', 0)}

Generate content that matches winning patterns while applying suggested mutations.
"""
        
        return prompt


# ============================================================================
# CLI INTERFACE
# ============================================================================

async def main():
    """Run analytics scan."""
    import argparse
    
    parser = argparse.ArgumentParser(description="YouTube Analytics Engine")
    parser.add_argument("--scan", action="store_true", help="Scan YouTube for performance")
    parser.add_argument("--winners", action="store_true", help="Get winner DNA")
    parser.add_argument("--mutations", action="store_true", help="Get mutation prompt")
    parser.add_argument("--log", type=str, help="Log video DNA (JSON string)")
    
    args = parser.parse_args()
    
    engine = AnalyticsEngine()
    
    if args.scan:
        report = await engine.scan_performance()
        print(f"\n{'='*60}")
        print("📊 ANALYTICS REPORT")
        print(f"{'='*60}")
        print(json.dumps(report.summary, indent=2))
        print(f"\n🏆 Winners: {len(report.winners)}")
        for w in report.winners[:5]:
            print(f"  - {w.title[:50]} | Views: {w.views} | AVD: {w.average_view_percentage:.1f}%")
        print(f"\n🔧 Mutations Needed:")
        for m in report.mutations_triggered[:5]:
            print(f"  - {m['action']}: {m['count']} videos")
    
    elif args.winners:
        dna = await engine.get_winner_dna()
        print(json.dumps(dna, indent=2))
    
    elif args.mutations:
        prompt = await engine.generate_mutation_prompt()
        print(prompt)
    
    elif args.log:
        try:
            data = json.loads(args.log)
            engine.log_video_dna(data)
        except json.JSONDecodeError:
            print("Invalid JSON")
    
    else:
        # Default: full scan
        report = await engine.scan_performance()
        print(json.dumps(report.summary, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
