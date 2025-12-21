"""
============================================================
MONEY MACHINE - SYSTEME.IO INTEGRATION
The All-in-One Marketing Automation Hub
============================================================
Manages funnels, email sequences, lead tagging, and automation
using Systeme.io's FREE tier (2,000 contacts, unlimited emails).
============================================================
"""

import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from dataclasses import dataclass, field, asdict
import httpx

# ============================================================
# CONFIGURATION
# ============================================================

@dataclass
class SystemeConfig:
    """Systeme.io Integration Configuration"""
    
    # API Settings
    BASE_URL: str = "https://api.systeme.io/api"
    
    # Niche-specific funnels
    FUNNELS = {
        "survival": {
            "name": "Survival Funnel",
            "slug": "survival-checklist",
            "lead_magnet": "The 72-Hour Survival Checklist",
            "tag": "SURV_01",
            "email_sequence_id": ""
        },
        "wealth": {
            "name": "Wealth Funnel", 
            "slug": "wealth-blueprint",
            "lead_magnet": "The 2025 Digital Arbitrage Protocol",
            "tag": "WLT_01",
            "email_sequence_id": ""
        },
        "wellness": {
            "name": "Wellness Funnel",
            "slug": "wellness-reset",
            "lead_magnet": "The Biological Reset: 7 Days to High-Voltage Energy",
            "tag": "WELL_01",
            "email_sequence_id": ""
        },
        "productivity": {
            "name": "Productivity Funnel",
            "slug": "productivity-system",
            "lead_magnet": "The Frictionless Workflow: Automating Your 9-to-5",
            "tag": "PROD_01",
            "email_sequence_id": ""
        }
    }
    
    # Email sequence templates (7-day nurture)
    EMAIL_SEQUENCE = [
        {"day": 0, "type": "lead_magnet", "subject": "Your FREE {lead_magnet} is inside!"},
        {"day": 1, "type": "value", "subject": "The #1 {niche} mistake (and how to avoid it)"},
        {"day": 2, "type": "story", "subject": "How I discovered the {niche} secret..."},
        {"day": 3, "type": "soft_pitch", "subject": "The tool that changed everything for me"},
        {"day": 4, "type": "value", "subject": "3 quick {niche} wins you can do today"},
        {"day": 5, "type": "hard_pitch", "subject": "Last chance: The {niche} solution you've been looking for"},
        {"day": 7, "type": "scarcity", "subject": "⚠️ Closing in 24 hours..."}
    ]


@dataclass
class Contact:
    """Represents a Systeme.io contact"""
    
    id: str = ""
    email: str = ""
    first_name: str = ""
    tags: List[str] = field(default_factory=list)
    source: str = ""
    niche: str = ""
    created_at: str = ""
    
    # Engagement tracking
    emails_sent: int = 0
    emails_opened: int = 0
    emails_clicked: int = 0
    purchases: int = 0
    revenue: float = 0.0


# ============================================================
# SYSTEME.IO API CLIENT
# ============================================================

class SystemeClient:
    """
    Low-level Systeme.io API client.
    Handles authentication and API calls.
    """
    
    def __init__(self):
        self.api_key = os.getenv("SYSTEME_IO_API_KEY", "")
        self.base_url = SystemeConfig.BASE_URL
        
    def _get_headers(self) -> Dict:
        """Get API headers"""
        return {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    async def _request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict:
        """Make API request"""
        if not self.api_key:
            return {"error": "API key not configured"}
            
        url = f"{self.base_url}/{endpoint}"
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self._get_headers(),
                    json=data,
                    params=params
                )
                
                if response.status_code in [200, 201]:
                    return response.json()
                else:
                    return {
                        "error": f"API error: {response.status_code}",
                        "message": response.text
                    }
                    
        except Exception as e:
            return {"error": str(e)}
    
    async def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        return await self._request("GET", endpoint, params=params)
    
    async def post(self, endpoint: str, data: Dict) -> Dict:
        return await self._request("POST", endpoint, data=data)
    
    async def put(self, endpoint: str, data: Dict) -> Dict:
        return await self._request("PUT", endpoint, data=data)
    
    async def delete(self, endpoint: str) -> Dict:
        return await self._request("DELETE", endpoint)


# ============================================================
# CONTACT MANAGER
# ============================================================

class ContactManager:
    """
    Manages contacts, tags, and segmentation.
    The core of lead nurturing.
    """
    
    def __init__(self, client: SystemeClient):
        self.client = client
        self.config = SystemeConfig()
        
    async def create_contact(
        self,
        email: str,
        first_name: str = "",
        niche: str = "survival",
        source: str = "youtube"
    ) -> Dict:
        """
        Create a new contact with proper tagging.
        Automatically assigns niche tag for segmentation.
        """
        funnel_config = self.config.FUNNELS.get(niche, self.config.FUNNELS["survival"])
        
        data = {
            "email": email,
            "fields": {
                "first_name": first_name
            },
            "tags": [
                funnel_config["tag"],
                f"source_{source}",
                f"niche_{niche}"
            ]
        }
        
        result = await self.client.post("contacts", data)
        
        if "error" not in result:
            print(f"[SYSTEME] Created contact: {email} with tag {funnel_config['tag']}")
            
        return result
    
    async def get_contact(self, email: str) -> Dict:
        """Get contact by email"""
        result = await self.client.get("contacts", params={"email": email})
        return result
    
    async def add_tag(self, contact_id: str, tag: str) -> Dict:
        """Add a tag to a contact"""
        return await self.client.post(f"contacts/{contact_id}/tags", {"tag": tag})
    
    async def remove_tag(self, contact_id: str, tag: str) -> Dict:
        """Remove a tag from a contact"""
        return await self.client.delete(f"contacts/{contact_id}/tags/{tag}")
    
    async def get_contacts_by_tag(self, tag: str, limit: int = 100) -> List[Dict]:
        """Get all contacts with a specific tag"""
        result = await self.client.get("contacts", params={"tag": tag, "limit": limit})
        return result.get("items", [])
    
    async def get_niche_stats(self) -> Dict:
        """Get contact counts per niche"""
        stats = {}
        
        for niche, config in self.config.FUNNELS.items():
            contacts = await self.get_contacts_by_tag(config["tag"])
            stats[niche] = {
                "tag": config["tag"],
                "count": len(contacts),
                "funnel": config["name"]
            }
            
        return stats


# ============================================================
# FUNNEL MANAGER
# ============================================================

class FunnelManager:
    """
    Manages sales funnels and landing pages.
    Optimizes for lead capture and conversion.
    """
    
    def __init__(self, client: SystemeClient):
        self.client = client
        self.config = SystemeConfig()
        
    async def get_funnels(self) -> List[Dict]:
        """Get all funnels"""
        result = await self.client.get("funnels")
        return result.get("items", [])
    
    async def get_funnel_stats(self, funnel_id: str) -> Dict:
        """Get funnel statistics"""
        result = await self.client.get(f"funnels/{funnel_id}/stats")
        return result
    
    async def get_all_funnel_stats(self) -> Dict:
        """Get stats for all niche funnels"""
        funnels = await self.get_funnels()
        stats = {}
        
        for funnel in funnels:
            funnel_stats = await self.get_funnel_stats(funnel["id"])
            stats[funnel["name"]] = {
                "id": funnel["id"],
                "views": funnel_stats.get("views", 0),
                "optins": funnel_stats.get("optins", 0),
                "conversion_rate": funnel_stats.get("conversion_rate", 0),
                "revenue": funnel_stats.get("revenue", 0)
            }
            
        return stats
    
    def get_funnel_url(self, niche: str) -> str:
        """Get the funnel URL for a specific niche"""
        funnel_config = self.config.FUNNELS.get(niche)
        if not funnel_config:
            return ""
        
        subdomain = os.getenv("SYSTEME_SUBDOMAIN", "your-subdomain")
        return f"https://{subdomain}.systeme.io/{funnel_config['slug']}"


# ============================================================
# EMAIL CAMPAIGN MANAGER
# ============================================================

class EmailCampaignManager:
    """
    Manages email campaigns and sequences.
    Implements the 7-day nurture sequence.
    """
    
    def __init__(self, client: SystemeClient):
        self.client = client
        self.config = SystemeConfig()
        
    async def get_campaigns(self) -> List[Dict]:
        """Get all email campaigns"""
        result = await self.client.get("email-campaigns")
        return result.get("items", [])
    
    async def send_broadcast(
        self,
        subject: str,
        content: str,
        tag: str,
        sender_name: str = "Money Machine"
    ) -> Dict:
        """
        Send a broadcast email to a specific tag.
        Used for promotions and announcements.
        """
        data = {
            "subject": subject,
            "content": content,
            "sender_name": sender_name,
            "filter": {
                "tag": tag
            }
        }
        
        result = await self.client.post("email-campaigns/broadcasts", data)
        return result
    
    async def send_niche_promotion(
        self,
        niche: str,
        subject: str,
        content: str,
        affiliate_link: str
    ) -> Dict:
        """
        Send a promotional email to a specific niche segment.
        Used for affiliate promotions.
        """
        funnel_config = self.config.FUNNELS.get(niche)
        if not funnel_config:
            return {"error": f"Unknown niche: {niche}"}
        
        # Insert affiliate link into content
        final_content = content.replace("{affiliate_link}", affiliate_link)
        final_content = final_content.replace("{lead_magnet}", funnel_config["lead_magnet"])
        
        return await self.send_broadcast(
            subject=subject,
            content=final_content,
            tag=funnel_config["tag"]
        )
    
    async def get_email_stats(self) -> Dict:
        """Get overall email statistics"""
        campaigns = await self.get_campaigns()
        
        total_sent = 0
        total_opened = 0
        total_clicked = 0
        
        for campaign in campaigns:
            total_sent += campaign.get("sent", 0)
            total_opened += campaign.get("opened", 0)
            total_clicked += campaign.get("clicked", 0)
        
        return {
            "total_sent": total_sent,
            "total_opened": total_opened,
            "total_clicked": total_clicked,
            "open_rate": (total_opened / total_sent * 100) if total_sent > 0 else 0,
            "click_rate": (total_clicked / total_sent * 100) if total_sent > 0 else 0,
            "campaigns_count": len(campaigns)
        }


# ============================================================
# AUTOMATION RULES ENGINE
# ============================================================

class AutomationRulesEngine:
    """
    Implements smart automation rules for lead nurturing.
    The "Businessman" logic for email marketing.
    """
    
    def __init__(self, client: SystemeClient):
        self.client = client
        self.contact_manager = ContactManager(client)
        self.email_manager = EmailCampaignManager(client)
        self.config = SystemeConfig()
        
    async def process_new_lead(
        self,
        email: str,
        first_name: str,
        niche: str,
        source: str
    ) -> Dict:
        """
        Process a new lead through the automation funnel.
        1. Create contact with tags
        2. Trigger email sequence
        3. Log for analytics
        """
        result = {
            "email": email,
            "niche": niche,
            "actions_taken": []
        }
        
        # Create contact
        contact_result = await self.contact_manager.create_contact(
            email=email,
            first_name=first_name,
            niche=niche,
            source=source
        )
        
        if "error" not in contact_result:
            result["actions_taken"].append("contact_created")
            result["contact_id"] = contact_result.get("id")
        else:
            result["error"] = contact_result["error"]
            
        return result
    
    async def trigger_promotion_sequence(
        self,
        niche: str,
        offer_name: str,
        affiliate_link: str
    ) -> Dict:
        """
        Trigger a promotional email sequence for a niche.
        Used when a new high-converting offer is added.
        """
        funnel_config = self.config.FUNNELS.get(niche)
        if not funnel_config:
            return {"error": f"Unknown niche: {niche}"}
        
        # Promotional email template
        subject = f"🔥 The {niche.title()} breakthrough you've been waiting for"
        content = f"""
Hey {{{{first_name}}}},

I just discovered something that could change everything for you...

[Tell story about the offer]

After testing dozens of {niche} solutions, I finally found one that actually delivers:

👉 **{offer_name}**

[Benefits and features]

Click here to learn more:
{{affiliate_link}}

This isn't just another {niche} product. It's the real deal.

[Add urgency/scarcity if applicable]

To your success,
The {niche.title()} Team

P.S. - The link above is exclusive to our subscribers. Don't share it publicly.
"""
        
        result = await self.email_manager.send_niche_promotion(
            niche=niche,
            subject=subject,
            content=content,
            affiliate_link=affiliate_link
        )
        
        return result
    
    async def run_daily_engagement_check(self) -> Dict:
        """
        Check engagement and apply tags for segmentation.
        Run daily via n8n.
        """
        results = {
            "checked": 0,
            "engaged": 0,
            "cold": 0,
            "actions": []
        }
        
        # Get email stats to identify engaged vs cold
        stats = await self.email_manager.get_email_stats()
        
        # In production: Query individual contact engagement
        # and apply "engaged" or "cold" tags for re-engagement campaigns
        
        return results


# ============================================================
# MASTER SYSTEME.IO MANAGER
# ============================================================

class MasterSystemeManager:
    """
    The Master Manager coordinates all Systeme.io operations:
    - Contact management
    - Funnel analytics
    - Email campaigns
    - Automation rules
    """
    
    def __init__(self):
        self.client = SystemeClient()
        self.contacts = ContactManager(self.client)
        self.funnels = FunnelManager(self.client)
        self.emails = EmailCampaignManager(self.client)
        self.automation = AutomationRulesEngine(self.client)
        self.config = SystemeConfig()
        
    async def process_youtube_lead(
        self,
        email: str,
        first_name: str,
        video_niche: str,
        video_id: str
    ) -> Dict:
        """
        Process a lead that came from YouTube.
        Called by n8n webhook when someone opts in.
        """
        return await self.automation.process_new_lead(
            email=email,
            first_name=first_name,
            niche=video_niche,
            source=f"youtube_{video_id}"
        )
    
    async def get_dashboard(self) -> Dict:
        """
        Get comprehensive Systeme.io dashboard data.
        """
        # Gather all stats in parallel
        niche_stats, funnel_stats, email_stats = await asyncio.gather(
            self.contacts.get_niche_stats(),
            self.funnels.get_all_funnel_stats(),
            self.emails.get_email_stats()
        )
        
        # Calculate totals
        total_contacts = sum(n["count"] for n in niche_stats.values())
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "total_contacts": total_contacts,
            "contacts_by_niche": niche_stats,
            "funnels": funnel_stats,
            "email_performance": email_stats,
            "funnel_urls": {
                niche: self.funnels.get_funnel_url(niche)
                for niche in self.config.FUNNELS.keys()
            }
        }
    
    async def run_weekly_promotion(self, affiliate_engine) -> Dict:
        """
        Run weekly promotion for each niche.
        Promotes the best converting offer.
        """
        results = {"niches_promoted": 0, "details": []}
        
        for niche in self.config.FUNNELS.keys():
            # Get best offer for niche
            best_link = affiliate_engine.get_best_link(niche, tracking_id="email")
            
            if best_link:
                offer_name = f"Top {niche.title()} Solution"  # Would come from affiliate engine
                
                promo_result = await self.automation.trigger_promotion_sequence(
                    niche=niche,
                    offer_name=offer_name,
                    affiliate_link=best_link
                )
                
                results["details"].append({
                    "niche": niche,
                    "offer": offer_name,
                    "result": "sent" if "error" not in promo_result else "failed"
                })
                
                if "error" not in promo_result:
                    results["niches_promoted"] += 1
        
        return results
    
    def format_telegram_dashboard(self, dashboard: Dict) -> str:
        """Format dashboard for Telegram message"""
        message = f"""
📧 **SYSTEME.IO DASHBOARD**

📊 **Contacts Overview**
Total Leads: {dashboard['total_contacts']:,}
"""
        
        for niche, stats in dashboard.get("contacts_by_niche", {}).items():
            message += f"  • {niche.title()}: {stats['count']:,} ({stats['tag']})\n"
        
        message += f"""
📈 **Email Performance**
Sent: {dashboard['email_performance']['total_sent']:,}
Opens: {dashboard['email_performance']['open_rate']:.1f}%
Clicks: {dashboard['email_performance']['click_rate']:.1f}%

🔗 **Active Funnels**
"""
        
        for niche, url in dashboard.get("funnel_urls", {}).items():
            message += f"  • {niche.title()}: {url}\n"
        
        message += f"\n⏰ Updated: {dashboard['timestamp'][:16]}"
        
        return message


# ============================================================
# CLI INTERFACE
# ============================================================

if __name__ == "__main__":
    import sys
    
    async def main():
        manager = MasterSystemeManager()
        
        if len(sys.argv) > 1:
            command = sys.argv[1]
            
            if command == "dashboard":
                print("[SYSTEME] Fetching dashboard...")
                dashboard = await manager.get_dashboard()
                print(manager.format_telegram_dashboard(dashboard))
                
            elif command == "add":
                if len(sys.argv) >= 4:
                    email = sys.argv[2]
                    niche = sys.argv[3]
                    result = await manager.process_youtube_lead(
                        email=email,
                        first_name="",
                        video_niche=niche,
                        video_id="cli_test"
                    )
                    print(json.dumps(result, indent=2))
                else:
                    print("Usage: python systeme_io.py add <email> <niche>")
                    
            elif command == "stats":
                stats = await manager.contacts.get_niche_stats()
                print(json.dumps(stats, indent=2))
                
            elif command == "funnels":
                for niche in manager.config.FUNNELS.keys():
                    url = manager.funnels.get_funnel_url(niche)
                    print(f"{niche.title()}: {url}")
                    
        else:
            print("Usage: python systeme_io.py [dashboard|add|stats|funnels]")
    
    asyncio.run(main())
