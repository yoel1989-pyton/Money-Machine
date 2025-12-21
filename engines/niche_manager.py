"""
============================================================
MONEY MACHINE - 4-NICHE CHANNEL MANAGER
The Revenue Subsidiary Orchestration System
============================================================
Manages 4 independent YouTube channels (Wealth, Wellness,
Survival, Productivity) as separate "Revenue Subsidiaries"
under one central brain.
============================================================
"""

import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from dataclasses import dataclass, field, asdict
from enum import Enum
import httpx

# ============================================================
# NICHE DEFINITIONS
# ============================================================

class Niche(Enum):
    """The 4 Revenue Subsidiaries"""
    SURVIVAL = "survival"
    WEALTH = "wealth"
    WELLNESS = "wellness"
    PRODUCTIVITY = "productivity"


@dataclass
class NicheConfig:
    """Configuration for a single niche channel"""
    
    niche: Niche
    channel_name: str
    channel_id: str = ""
    
    # Content settings
    video_frequency: int = 1  # Videos per day
    short_frequency: int = 1  # Shorts per day
    optimal_length: int = 60  # Seconds for shorts
    
    # Brand assets
    logo_path: str = ""
    intro_path: str = ""
    outro_path: str = ""
    brand_colors: List[str] = field(default_factory=list)
    
    # Funnel settings
    systeme_funnel_url: str = ""
    lead_magnet_name: str = ""
    lead_magnet_path: str = ""
    
    # Monetization
    primary_offer_id: str = ""
    backup_offer_id: str = ""
    own_product_url: str = ""  # For Solidarity Ointments etc.
    
    # Tracking
    total_videos: int = 0
    total_views: int = 0
    total_subscribers: int = 0
    total_leads: int = 0
    total_revenue: float = 0.0
    
    # API credentials (per-channel)
    youtube_client_id: str = ""
    youtube_client_secret: str = ""
    youtube_refresh_token: str = ""


# ============================================================
# NICHE-SPECIFIC CONTENT STRATEGIES
# ============================================================

NICHE_STRATEGIES = {
    Niche.SURVIVAL: {
        "name": "Survival",
        "brand_suffix": "Survival Secrets",
        "keywords": [
            "survival tips", "prepping", "emergency preparedness",
            "wilderness survival", "first aid", "self defense",
            "off grid", "shtf", "bug out bag", "survival gear"
        ],
        "content_frameworks": [
            "Problem-Agitation-Solution",
            "Before-After-Bridge",
            "Fear-Relief-Action"
        ],
        "video_hooks": [
            "🚨 CRITICAL: {topic} that could save your life",
            "Most preppers IGNORE this {topic} mistake",
            "The military secret for {topic}",
            "Why 90% of survival guides are WRONG about {topic}",
            "The $5 {topic} that beats $500 gear"
        ],
        "lead_magnet": {
            "title": "The 72-Hour Survival Checklist",
            "hook": "🚨 DOWNLOAD: Emergency Prep Guide (Free)",
            "cta": "Get your free survival checklist 👇"
        },
        "own_product_keywords": [
            "wound", "healing", "infection", "first aid",
            "burns", "cuts", "emergency medicine"
        ],
        "subreddits": [
            "preppers", "Survival", "bugout", "homestead",
            "OffGrid", "SelfSufficiency"
        ]
    },
    
    Niche.WEALTH: {
        "name": "Wealth",
        "brand_suffix": "Wealth Accelerator",
        "keywords": [
            "passive income", "side hustle", "investing",
            "financial freedom", "make money online", "crypto",
            "real estate", "stocks", "ai money", "automation income"
        ],
        "content_frameworks": [
            "Problem-Agitation-Solution",
            "Proof-Promise-Picture-Push",
            "Hook-Story-Offer"
        ],
        "video_hooks": [
            "💰 How I made ${amount} with {topic} (Step-by-Step)",
            "The {topic} strategy billionaires don't share",
            "Why the rich use {topic} to multiply money",
            "I tested {topic} for 30 days - Here's what happened",
            "{topic}: The 2025 wealth secret nobody talks about"
        ],
        "lead_magnet": {
            "title": "The 2025 Digital Arbitrage Protocol",
            "hook": "💰 SECURE: Financial Freedom Blueprint (Free)",
            "cta": "Get your free wealth blueprint 👇"
        },
        "own_product_keywords": [],  # Wealth typically promotes affiliate offers
        "subreddits": [
            "passive_income", "sidehustle", "Entrepreneur",
            "financialindependence", "investing", "CryptoCurrency"
        ]
    },
    
    Niche.WELLNESS: {
        "name": "Wellness",
        "brand_suffix": "Wellness Protocol",
        "keywords": [
            "health tips", "weight loss", "fitness",
            "supplements", "anti-aging", "sleep hacks",
            "biohacking", "natural remedies", "energy boost",
            "inflammation", "gut health", "mental clarity"
        ],
        "content_frameworks": [
            "Problem-Agitation-Solution",
            "Before-After-Bridge",
            "Scientific-Discovery"
        ],
        "video_hooks": [
            "🧬 The {topic} secret doctors won't tell you",
            "I tried {topic} for 7 days - SHOCKING results",
            "Why {topic} is destroying your health",
            "The ancient {topic} remedy that actually works",
            "Harvard study reveals the truth about {topic}"
        ],
        "lead_magnet": {
            "title": "The Biological Reset: 7 Days to High-Voltage Energy",
            "hook": "🧬 RESTORE: 7-Day Energy Reset Guide (Free)",
            "cta": "Get your free wellness guide 👇"
        },
        "own_product_keywords": [
            "skin", "healing", "natural", "remedy", "pain",
            "inflammation", "recovery", "ointment", "balm"
        ],
        "subreddits": [
            "health", "loseit", "fitness", "nutrition",
            "Supplements", "Biohackers", "longevity"
        ]
    },
    
    Niche.PRODUCTIVITY: {
        "name": "Productivity",
        "brand_suffix": "Productivity Engine",
        "keywords": [
            "productivity hacks", "time management", "ai tools",
            "automation", "focus", "second brain", "notion",
            "work smarter", "remote work", "efficiency"
        ],
        "content_frameworks": [
            "Problem-Agitation-Solution",
            "Tool-Tutorial-Transformation",
            "Before-After-Bridge"
        ],
        "video_hooks": [
            "⚡ The {topic} hack that saved me 10 hours/week",
            "5 {topic} tools the pros use (most are FREE)",
            "Why your {topic} system is broken",
            "I built a {topic} system that runs itself",
            "The CEO morning {topic} routine that 10x'd my output"
        ],
        "lead_magnet": {
            "title": "The Frictionless Workflow: Automating Your 9-to-5",
            "hook": "⚡ UNLOCK: Productivity System Blueprint (Free)",
            "cta": "Get your free workflow guide 👇"
        },
        "own_product_keywords": [],  # Productivity typically promotes SaaS/courses
        "subreddits": [
            "productivity", "getdisciplined", "Notion",
            "automation", "selfimprovement", "Entrepreneur"
        ]
    }
}


# ============================================================
# CHANNEL MANAGER
# ============================================================

class ChannelManager:
    """
    Manages a single YouTube channel for a specific niche.
    Handles uploads, analytics, and optimization.
    """
    
    def __init__(self, config: NicheConfig):
        self.config = config
        self.strategy = NICHE_STRATEGIES[config.niche]
        self.youtube_api_key = os.getenv("YOUTUBE_API_KEY", "")
        
    async def upload_video(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: List[str],
        is_short: bool = True
    ) -> Dict:
        """
        Upload a video to this channel.
        Returns video ID and status.
        """
        # Build optimized metadata
        full_description = self._build_description(description)
        full_tags = self._build_tags(tags)
        
        # Upload via YouTube API
        # In production: Use OAuth2 with channel-specific credentials
        
        result = {
            "success": False,
            "video_id": "",
            "channel": self.config.channel_name,
            "niche": self.config.niche.value,
            "title": title,
            "is_short": is_short
        }
        
        try:
            # Placeholder for actual YouTube upload
            # Would use google-api-python-client
            result["success"] = True
            result["video_id"] = "PLACEHOLDER_VIDEO_ID"
            
            # Update stats
            self.config.total_videos += 1
            
        except Exception as e:
            result["error"] = str(e)
            
        return result
    
    def _build_description(self, base_description: str) -> str:
        """Build SEO-optimized description with funnel link"""
        lead_magnet = self.strategy["lead_magnet"]
        
        description = f"""{lead_magnet['hook']}
{self.config.systeme_funnel_url}

---

{base_description}

---

🔔 Subscribe for more {self.strategy['name']} content!
👍 Like this video if it helped you.
💬 Comment your biggest {self.strategy['name'].lower()} challenge.

---

#{''.join(['#' + kw.replace(' ', '') + ' ' for kw in self.strategy['keywords'][:5]])}
"""
        return description
    
    def _build_tags(self, base_tags: List[str]) -> List[str]:
        """Build comprehensive tag list"""
        all_tags = base_tags.copy()
        all_tags.extend(self.strategy["keywords"][:10])
        return list(set(all_tags))[:30]  # YouTube max 500 chars
    
    def get_video_hook(self, topic: str) -> str:
        """Get a compelling hook for the video title"""
        import random
        hook_template = random.choice(self.strategy["video_hooks"])
        return hook_template.format(topic=topic, amount=random.randint(500, 5000))
    
    def get_content_framework(self) -> str:
        """Get the recommended content framework"""
        import random
        return random.choice(self.strategy["content_frameworks"])
    
    async def get_analytics(self, days: int = 30) -> Dict:
        """Get channel analytics for the last N days"""
        # In production: Query YouTube Analytics API
        return {
            "channel": self.config.channel_name,
            "niche": self.config.niche.value,
            "period_days": days,
            "views": self.config.total_views,
            "subscribers": self.config.total_subscribers,
            "videos": self.config.total_videos,
            "leads_captured": self.config.total_leads,
            "revenue": self.config.total_revenue
        }
    
    def should_route_to_own_product(self, keywords: List[str]) -> bool:
        """
        Check if content should promote own product instead of affiliate.
        Used for Solidarity Ointments routing.
        """
        own_keywords = self.strategy.get("own_product_keywords", [])
        if not own_keywords or not self.config.own_product_url:
            return False
            
        for keyword in keywords:
            if any(own_kw in keyword.lower() for own_kw in own_keywords):
                return True
        return False


# ============================================================
# MASTER NICHE ORCHESTRATOR
# ============================================================

class MasterNicheOrchestrator:
    """
    The Master Orchestrator manages all 4 niche channels.
    Coordinates content distribution, offer routing, and analytics.
    """
    
    def __init__(self, config_path: str = "/data/niche_config.json"):
        self.config_path = config_path
        self.channels: Dict[Niche, ChannelManager] = {}
        self.load_config()
        
    def load_config(self):
        """Load channel configurations"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                    for niche_str, config_data in data.items():
                        niche = Niche(niche_str)
                        config = NicheConfig(
                            niche=niche,
                            channel_name=config_data.get("channel_name", f"{niche.value.title()} Channel"),
                            **{k: v for k, v in config_data.items() if k not in ["niche", "channel_name"]}
                        )
                        self.channels[niche] = ChannelManager(config)
            else:
                # Initialize with defaults
                self._initialize_default_channels()
                
        except Exception as e:
            print(f"[ORCHESTRATOR] Config load error: {e}")
            self._initialize_default_channels()
    
    def _initialize_default_channels(self):
        """Initialize default channel configurations"""
        for niche in Niche:
            strategy = NICHE_STRATEGIES[niche]
            config = NicheConfig(
                niche=niche,
                channel_name=f"Elite {strategy['name']} {strategy['brand_suffix']}",
                lead_magnet_name=strategy["lead_magnet"]["title"],
                systeme_funnel_url=f"https://your-subdomain.systeme.io/{niche.value}-checklist"
            )
            
            # Set own product URL for relevant niches
            if niche in [Niche.WELLNESS, Niche.SURVIVAL]:
                config.own_product_url = os.getenv("OWN_PRODUCT_URL", "https://solidarityointments.com")
            
            self.channels[niche] = ChannelManager(config)
        
        self.save_config()
    
    def save_config(self):
        """Persist channel configurations"""
        try:
            data = {}
            for niche, manager in self.channels.items():
                config = manager.config
                data[niche.value] = {
                    "channel_name": config.channel_name,
                    "channel_id": config.channel_id,
                    "video_frequency": config.video_frequency,
                    "short_frequency": config.short_frequency,
                    "systeme_funnel_url": config.systeme_funnel_url,
                    "lead_magnet_name": config.lead_magnet_name,
                    "own_product_url": config.own_product_url,
                    "total_videos": config.total_videos,
                    "total_views": config.total_views,
                    "total_subscribers": config.total_subscribers,
                    "total_leads": config.total_leads,
                    "total_revenue": config.total_revenue
                }
            
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"[ORCHESTRATOR] Config save error: {e}")
    
    def get_channel(self, niche: Niche) -> ChannelManager:
        """Get channel manager for a specific niche"""
        return self.channels.get(niche)
    
    def identify_niche(self, keywords: List[str], topic: str = "") -> Niche:
        """
        Identify the best niche for given content keywords.
        Used for smart routing of generated content.
        """
        scores = {niche: 0 for niche in Niche}
        
        combined_text = " ".join(keywords) + " " + topic
        combined_lower = combined_text.lower()
        
        for niche in Niche:
            strategy = NICHE_STRATEGIES[niche]
            for keyword in strategy["keywords"]:
                if keyword.lower() in combined_lower:
                    scores[niche] += 1
        
        # Return highest scoring niche
        best_niche = max(scores, key=scores.get)
        
        # Default to survival if no matches
        if scores[best_niche] == 0:
            return Niche.SURVIVAL
            
        return best_niche
    
    def get_routing_decision(self, keywords: List[str], topic: str = "") -> Dict:
        """
        Make intelligent routing decision for content.
        Determines niche, channel, and whether to use own product.
        """
        niche = self.identify_niche(keywords, topic)
        manager = self.channels[niche]
        
        # Check if should route to own product
        use_own_product = manager.should_route_to_own_product(keywords)
        
        strategy = NICHE_STRATEGIES[niche]
        
        return {
            "niche": niche.value,
            "channel": manager.config.channel_name,
            "channel_id": manager.config.channel_id,
            "use_own_product": use_own_product,
            "product_url": manager.config.own_product_url if use_own_product else "",
            "funnel_url": manager.config.systeme_funnel_url,
            "lead_magnet_hook": strategy["lead_magnet"]["hook"],
            "lead_magnet_cta": strategy["lead_magnet"]["cta"],
            "video_hook": manager.get_video_hook(topic or keywords[0] if keywords else "this"),
            "content_framework": manager.get_content_framework()
        }
    
    async def distribute_content(
        self,
        video_path: str,
        title: str,
        description: str,
        keywords: List[str],
        tags: List[str]
    ) -> Dict:
        """
        Distribute content to the appropriate channel.
        Automatically routes based on content keywords.
        """
        routing = self.get_routing_decision(keywords)
        niche = Niche(routing["niche"])
        manager = self.channels[niche]
        
        # Enhance description with routing info
        enhanced_description = f"""{routing['lead_magnet_hook']}
{routing['funnel_url']}

---

{description}
"""
        
        result = await manager.upload_video(
            video_path=video_path,
            title=title,
            description=enhanced_description,
            tags=tags,
            is_short=True
        )
        
        result["routing"] = routing
        self.save_config()
        
        return result
    
    async def get_all_analytics(self, days: int = 30) -> Dict:
        """Get combined analytics across all channels"""
        combined = {
            "period_days": days,
            "total_views": 0,
            "total_subscribers": 0,
            "total_videos": 0,
            "total_leads": 0,
            "total_revenue": 0.0,
            "by_niche": {}
        }
        
        for niche, manager in self.channels.items():
            analytics = await manager.get_analytics(days)
            combined["by_niche"][niche.value] = analytics
            combined["total_views"] += analytics["views"]
            combined["total_subscribers"] += analytics["subscribers"]
            combined["total_videos"] += analytics["videos"]
            combined["total_leads"] += analytics["leads_captured"]
            combined["total_revenue"] += analytics["revenue"]
        
        return combined
    
    def get_daily_content_plan(self) -> Dict:
        """
        Generate daily content plan for all channels.
        Used by n8n scheduler.
        """
        plan = {
            "date": datetime.utcnow().isoformat(),
            "channels": []
        }
        
        for niche, manager in self.channels.items():
            config = manager.config
            strategy = NICHE_STRATEGIES[niche]
            
            channel_plan = {
                "niche": niche.value,
                "channel": config.channel_name,
                "shorts_to_create": config.short_frequency,
                "videos_to_create": config.video_frequency,
                "recommended_topics": strategy["keywords"][:3],
                "funnel_url": config.systeme_funnel_url,
                "subreddits_to_monitor": strategy["subreddits"][:3]
            }
            
            plan["channels"].append(channel_plan)
        
        return plan


# ============================================================
# CLI INTERFACE
# ============================================================

if __name__ == "__main__":
    import sys
    
    async def main():
        orchestrator = MasterNicheOrchestrator()
        
        if len(sys.argv) > 1:
            command = sys.argv[1]
            
            if command == "plan":
                plan = orchestrator.get_daily_content_plan()
                print(json.dumps(plan, indent=2))
                
            elif command == "route":
                keywords = sys.argv[2:] if len(sys.argv) > 2 else ["survival", "emergency"]
                routing = orchestrator.get_routing_decision(keywords)
                print(json.dumps(routing, indent=2))
                
            elif command == "analytics":
                days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
                analytics = await orchestrator.get_all_analytics(days)
                print(json.dumps(analytics, indent=2))
                
            elif command == "channels":
                for niche, manager in orchestrator.channels.items():
                    print(f"\n=== {niche.value.upper()} ===")
                    print(f"Channel: {manager.config.channel_name}")
                    print(f"Funnel: {manager.config.systeme_funnel_url}")
                    print(f"Videos: {manager.config.total_videos}")
                    print(f"Leads: {manager.config.total_leads}")
                    
        else:
            print("Usage: python niche_manager.py [plan|route <keywords>|analytics|channels]")
    
    asyncio.run(main())
