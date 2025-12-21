"""
============================================================
MONEY MACHINE - AD REINVESTOR ENGINE
Algorithmic Growth Amplification
============================================================
Winners get fuel. Losers get cut.

This engine automatically:
- Identifies top-performing content (top 10% by RPM)
- Allocates ad budget proportionally
- Tracks ROI on ad spend
- Stops ads when ROI drops below threshold
- Scales winners aggressively
============================================================
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class CampaignStatus(Enum):
    """Ad campaign status"""
    PENDING = "pending"
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPED = "stopped"
    COMPLETED = "completed"


class AdPlatform(Enum):
    """Supported ad platforms"""
    YOUTUBE_ADS = "youtube_ads"
    TIKTOK_ADS = "tiktok_ads"
    FACEBOOK_ADS = "facebook_ads"
    GOOGLE_ADS = "google_ads"


@dataclass
class AdConfig:
    """Configuration for ad reinvestment"""
    
    # Budget controls
    min_daily_budget: float = 5.0
    max_daily_budget: float = 50.0
    total_monthly_cap: float = 500.0
    
    # Performance thresholds
    min_rpm_to_boost: float = 5.0        # Only boost if RPM >= $5
    min_views_to_qualify: float = 100    # Need at least 100 views
    min_roi_threshold: float = 1.5       # Stop if ROI < 1.5x
    target_roi: float = 3.0              # Aim for 3x ROI
    
    # Campaign rules
    max_campaigns_active: int = 5
    campaign_duration_days: int = 7
    cooldown_days: int = 3               # Days before re-boosting same content
    
    # Winner selection
    top_percent: float = 10.0            # Top 10% are winners


@dataclass
class ContentMetrics:
    """Metrics for a piece of content"""
    content_id: str
    platform: str
    niche: str
    title: str
    
    # Performance
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    watch_time_hours: float = 0
    
    # Revenue
    clicks: int = 0
    conversions: int = 0
    revenue: float = 0
    
    # Calculated
    rpm: float = 0
    engagement_rate: float = 0
    ctr: float = 0
    
    # Status
    published_at: Optional[datetime] = None
    is_winner: bool = False
    last_boosted: Optional[datetime] = None
    
    def calculate_metrics(self):
        """Calculate derived metrics"""
        if self.views > 0:
            self.rpm = (self.revenue / self.views) * 1000
            self.engagement_rate = (self.likes + self.comments + self.shares) / self.views
            self.ctr = self.clicks / self.views
    
    def to_dict(self) -> Dict:
        return {
            "content_id": self.content_id,
            "platform": self.platform,
            "niche": self.niche,
            "views": self.views,
            "revenue": f"${self.revenue:.2f}",
            "rpm": f"${self.rpm:.2f}",
            "is_winner": self.is_winner
        }


@dataclass
class AdCampaign:
    """Represents an ad campaign"""
    campaign_id: str
    content_id: str
    platform: AdPlatform
    niche: str
    
    # Budget
    daily_budget: float
    total_budget: float
    spent: float = 0
    
    # Performance
    impressions: int = 0
    clicks: int = 0
    conversions: int = 0
    revenue_generated: float = 0
    
    # Calculated
    roi: float = 0
    cpc: float = 0
    cpa: float = 0
    
    # Status
    status: CampaignStatus = CampaignStatus.PENDING
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    stop_reason: Optional[str] = None
    
    def calculate_metrics(self):
        """Calculate campaign metrics"""
        if self.spent > 0:
            self.roi = self.revenue_generated / self.spent
        if self.clicks > 0:
            self.cpc = self.spent / self.clicks
        if self.conversions > 0:
            self.cpa = self.spent / self.conversions
    
    def to_dict(self) -> Dict:
        return {
            "campaign_id": self.campaign_id,
            "content_id": self.content_id,
            "platform": self.platform.value,
            "budget": f"${self.total_budget:.2f}",
            "spent": f"${self.spent:.2f}",
            "revenue": f"${self.revenue_generated:.2f}",
            "roi": f"{self.roi:.2f}x",
            "status": self.status.value
        }


class WinnerSelector:
    """Selects winning content for ad amplification"""
    
    def __init__(self, config: AdConfig):
        self.config = config
    
    def select_winners(
        self, 
        content: List[ContentMetrics],
        max_winners: int = 5
    ) -> List[ContentMetrics]:
        """
        Select top performers for ad boost.
        """
        # Filter qualified content
        qualified = [
            c for c in content
            if c.rpm >= self.config.min_rpm_to_boost
            and c.views >= self.config.min_views_to_qualify
            and self._can_boost(c)
        ]
        
        if not qualified:
            logger.info("No qualified content for boosting")
            return []
        
        # Sort by RPM descending
        sorted_content = sorted(qualified, key=lambda x: x.rpm, reverse=True)
        
        # Take top percent
        top_count = max(1, int(len(sorted_content) * (self.config.top_percent / 100)))
        winners = sorted_content[:min(top_count, max_winners)]
        
        # Mark as winners
        for w in winners:
            w.is_winner = True
        
        logger.info(f"Selected {len(winners)} winners from {len(content)} content pieces")
        return winners
    
    def _can_boost(self, content: ContentMetrics) -> bool:
        """Check if content can be boosted (not in cooldown)"""
        if content.last_boosted is None:
            return True
        
        cooldown_end = content.last_boosted + timedelta(days=self.config.cooldown_days)
        return datetime.now() >= cooldown_end


class BudgetAllocator:
    """Allocates ad budget to winners"""
    
    def __init__(self, config: AdConfig):
        self.config = config
        self.monthly_spent: float = 0
    
    def allocate(
        self, 
        total_budget: float, 
        winners: List[ContentMetrics]
    ) -> List[Dict]:
        """
        Allocate budget proportionally to winners based on RPM.
        """
        if not winners or total_budget <= 0:
            return []
        
        # Check monthly cap
        available = min(total_budget, self.config.total_monthly_cap - self.monthly_spent)
        if available <= 0:
            logger.warning("Monthly ad cap reached")
            return []
        
        # Calculate total RPM for proportional allocation
        total_rpm = sum(w.rpm for w in winners)
        
        allocations = []
        remaining = available
        
        for winner in winners:
            if remaining <= 0:
                break
            
            # Proportional allocation
            if total_rpm > 0:
                proportion = winner.rpm / total_rpm
                allocation = min(
                    available * proportion,
                    remaining,
                    self.config.max_daily_budget * self.config.campaign_duration_days
                )
            else:
                # Equal distribution if no RPM data
                allocation = min(
                    available / len(winners),
                    remaining,
                    self.config.max_daily_budget * self.config.campaign_duration_days
                )
            
            # Ensure minimum budget
            if allocation < self.config.min_daily_budget:
                continue
            
            allocations.append({
                "content_id": winner.content_id,
                "platform": winner.platform,
                "niche": winner.niche,
                "total_budget": round(allocation, 2),
                "daily_budget": round(allocation / self.config.campaign_duration_days, 2),
                "rpm": winner.rpm,
                "reason": "rpm_proportional"
            })
            
            remaining -= allocation
        
        return allocations
    
    def track_spend(self, amount: float):
        """Track monthly spend"""
        self.monthly_spent += amount
    
    def reset_monthly(self):
        """Reset monthly tracking"""
        self.monthly_spent = 0


class CampaignManager:
    """Manages ad campaigns lifecycle"""
    
    def __init__(self, config: AdConfig):
        self.config = config
        self.campaigns: Dict[str, AdCampaign] = {}
    
    def create_campaign(
        self, 
        content_id: str,
        platform: str,
        niche: str,
        total_budget: float,
        daily_budget: float
    ) -> AdCampaign:
        """Create a new ad campaign"""
        import uuid
        
        campaign = AdCampaign(
            campaign_id=str(uuid.uuid4())[:8],
            content_id=content_id,
            platform=AdPlatform(platform) if isinstance(platform, str) else platform,
            niche=niche,
            daily_budget=daily_budget,
            total_budget=total_budget,
            status=CampaignStatus.PENDING,
            started_at=datetime.now()
        )
        
        self.campaigns[campaign.campaign_id] = campaign
        logger.info(f"Created campaign {campaign.campaign_id} for {content_id}")
        return campaign
    
    def update_metrics(
        self, 
        campaign_id: str, 
        spent: float,
        impressions: int,
        clicks: int,
        conversions: int,
        revenue: float
    ):
        """Update campaign metrics"""
        if campaign_id not in self.campaigns:
            return
        
        campaign = self.campaigns[campaign_id]
        campaign.spent = spent
        campaign.impressions = impressions
        campaign.clicks = clicks
        campaign.conversions = conversions
        campaign.revenue_generated = revenue
        campaign.calculate_metrics()
        
        # Check if should stop
        if campaign.roi < self.config.min_roi_threshold and campaign.spent >= campaign.daily_budget:
            self._stop_campaign(campaign_id, "roi_below_threshold")
    
    def _stop_campaign(self, campaign_id: str, reason: str):
        """Stop a campaign"""
        if campaign_id not in self.campaigns:
            return
        
        campaign = self.campaigns[campaign_id]
        campaign.status = CampaignStatus.STOPPED
        campaign.ended_at = datetime.now()
        campaign.stop_reason = reason
        logger.info(f"Stopped campaign {campaign_id}: {reason}")
    
    def get_active_campaigns(self) -> List[AdCampaign]:
        """Get all active campaigns"""
        return [
            c for c in self.campaigns.values()
            if c.status == CampaignStatus.ACTIVE
        ]
    
    def get_campaign_summary(self) -> Dict:
        """Get summary of all campaigns"""
        total_spent = sum(c.spent for c in self.campaigns.values())
        total_revenue = sum(c.revenue_generated for c in self.campaigns.values())
        
        return {
            "total_campaigns": len(self.campaigns),
            "active": len([c for c in self.campaigns.values() if c.status == CampaignStatus.ACTIVE]),
            "completed": len([c for c in self.campaigns.values() if c.status == CampaignStatus.COMPLETED]),
            "stopped": len([c for c in self.campaigns.values() if c.status == CampaignStatus.STOPPED]),
            "total_spent": f"${total_spent:.2f}",
            "total_revenue": f"${total_revenue:.2f}",
            "overall_roi": f"{(total_revenue / total_spent):.2f}x" if total_spent > 0 else "N/A"
        }


class AdReinvestor:
    """
    Main ad reinvestment engine.
    Combines winner selection, budget allocation, and campaign management.
    """
    
    def __init__(self, config: Optional[AdConfig] = None):
        self.config = config or AdConfig()
        self.selector = WinnerSelector(self.config)
        self.allocator = BudgetAllocator(self.config)
        self.manager = CampaignManager(self.config)
        self.logger = logging.getLogger(__name__)
    
    def select_winner(self, metrics: List[Dict]) -> Optional[Dict]:
        """
        Quick method to select single best winner.
        """
        if not metrics:
            return None
        return max(metrics, key=lambda x: x.get("rpm", 0))
    
    def reinvest(self, video_id: str, amount: float) -> Dict:
        """
        Simple reinvest method for a single video.
        """
        return {
            "platform": "youtube_ads",
            "video_id": video_id,
            "budget": amount,
            "daily_budget": round(amount / 7, 2),
            "duration_days": 7
        }
    
    async def process_reinvestment(
        self, 
        budget: float,
        content_metrics: List[ContentMetrics]
    ) -> Dict:
        """
        Full reinvestment processing.
        """
        # Select winners
        winners = self.selector.select_winners(content_metrics)
        
        if not winners:
            return {
                "status": "no_winners",
                "message": "No content qualified for boosting",
                "campaigns_created": 0
            }
        
        # Allocate budget
        allocations = self.allocator.allocate(budget, winners)
        
        if not allocations:
            return {
                "status": "no_budget",
                "message": "Budget insufficient or cap reached",
                "campaigns_created": 0
            }
        
        # Create campaigns
        campaigns_created = []
        for alloc in allocations:
            campaign = self.manager.create_campaign(
                content_id=alloc["content_id"],
                platform=alloc["platform"],
                niche=alloc["niche"],
                total_budget=alloc["total_budget"],
                daily_budget=alloc["daily_budget"]
            )
            campaigns_created.append(campaign.to_dict())
        
        # Track spend
        total_allocated = sum(a["total_budget"] for a in allocations)
        self.allocator.track_spend(total_allocated)
        
        return {
            "status": "success",
            "winners_selected": len(winners),
            "campaigns_created": len(campaigns_created),
            "total_budget_allocated": f"${total_allocated:.2f}",
            "campaigns": campaigns_created
        }
    
    async def evaluate_campaigns(self) -> Dict:
        """
        Evaluate all active campaigns and take action.
        """
        active = self.manager.get_active_campaigns()
        actions_taken = []
        
        for campaign in active:
            if campaign.roi >= self.config.target_roi:
                # Winner! Increase budget
                actions_taken.append({
                    "campaign_id": campaign.campaign_id,
                    "action": "increase_budget",
                    "reason": f"ROI {campaign.roi:.2f}x exceeds target"
                })
            elif campaign.roi < self.config.min_roi_threshold:
                # Loser! Stop campaign
                actions_taken.append({
                    "campaign_id": campaign.campaign_id,
                    "action": "stop",
                    "reason": f"ROI {campaign.roi:.2f}x below minimum"
                })
        
        return {
            "campaigns_evaluated": len(active),
            "actions": actions_taken,
            "summary": self.manager.get_campaign_summary()
        }
    
    async def get_roi_report(self) -> Dict:
        """
        Get ROI report for all ad spend.
        """
        summary = self.manager.get_campaign_summary()
        
        # Group by niche
        niche_performance = {}
        for campaign in self.manager.campaigns.values():
            if campaign.niche not in niche_performance:
                niche_performance[campaign.niche] = {
                    "spent": 0,
                    "revenue": 0,
                    "campaigns": 0
                }
            niche_performance[campaign.niche]["spent"] += campaign.spent
            niche_performance[campaign.niche]["revenue"] += campaign.revenue_generated
            niche_performance[campaign.niche]["campaigns"] += 1
        
        # Calculate ROI per niche
        for niche in niche_performance:
            spent = niche_performance[niche]["spent"]
            revenue = niche_performance[niche]["revenue"]
            niche_performance[niche]["roi"] = f"{(revenue / spent):.2f}x" if spent > 0 else "N/A"
        
        return {
            "overall": summary,
            "by_niche": niche_performance,
            "recommendations": self._generate_recommendations(niche_performance)
        }
    
    def _generate_recommendations(self, niche_data: Dict) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        for niche, data in niche_data.items():
            spent = data["spent"]
            revenue = data["revenue"]
            
            if spent > 0:
                roi = revenue / spent
                if roi >= 3:
                    recommendations.append(f"🚀 SCALE: {niche} is crushing it ({roi:.1f}x ROI). Increase budget 50%.")
                elif roi >= 2:
                    recommendations.append(f"✅ MAINTAIN: {niche} is profitable ({roi:.1f}x ROI). Keep current budget.")
                elif roi >= 1:
                    recommendations.append(f"⚠️ OPTIMIZE: {niche} is breaking even ({roi:.1f}x ROI). Test new creatives.")
                else:
                    recommendations.append(f"🛑 PAUSE: {niche} is losing money ({roi:.1f}x ROI). Pause and analyze.")
        
        return recommendations


class MasterAdReinvestor:
    """
    Master orchestrator for ad reinvestment.
    """
    
    def __init__(self, config: Optional[AdConfig] = None):
        self.reinvestor = AdReinvestor(config)
        self.logger = logging.getLogger(__name__)
    
    async def run_daily(
        self, 
        available_budget: float,
        content_metrics: List[Dict]
    ) -> Dict:
        """
        Run daily ad reinvestment cycle.
        """
        # Convert dict metrics to ContentMetrics objects
        content = []
        for m in content_metrics:
            cm = ContentMetrics(
                content_id=m.get("content_id", ""),
                platform=m.get("platform", "youtube"),
                niche=m.get("niche", ""),
                title=m.get("title", ""),
                views=m.get("views", 0),
                revenue=m.get("revenue", 0),
                rpm=m.get("rpm", 0)
            )
            cm.calculate_metrics()
            content.append(cm)
        
        # Process reinvestment
        result = await self.reinvestor.process_reinvestment(available_budget, content)
        
        # Evaluate existing campaigns
        evaluation = await self.reinvestor.evaluate_campaigns()
        
        return {
            "new_campaigns": result,
            "campaign_evaluation": evaluation,
            "timestamp": datetime.now().isoformat()
        }


# Quick test
if __name__ == "__main__":
    async def test():
        reinvestor = MasterAdReinvestor()
        
        # Sample content metrics
        content_metrics = [
            {"content_id": "vid_001", "platform": "youtube", "niche": "wealth", "views": 5000, "revenue": 75.00, "rpm": 15.0},
            {"content_id": "vid_002", "platform": "youtube", "niche": "survival", "views": 3000, "revenue": 30.00, "rpm": 10.0},
            {"content_id": "vid_003", "platform": "youtube", "niche": "wellness", "views": 8000, "revenue": 96.00, "rpm": 12.0},
            {"content_id": "vid_004", "platform": "youtube", "niche": "productivity", "views": 2000, "revenue": 8.00, "rpm": 4.0},
        ]
        
        result = await reinvestor.run_daily(
            available_budget=100.00,
            content_metrics=content_metrics
        )
        
        print("Ad Reinvestment Result:")
        import json
        print(json.dumps(result, indent=2, default=str))
    
    asyncio.run(test())
