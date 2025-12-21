"""
============================================================
MONEY MACHINE - ELITE AFFILIATE ENGINE
The Intelligent Offer Selection & Rotation System
============================================================
Automatically selects HIGH-CONVERTING offers from ClickBank
and Digistore24. Rotates underperformers. Maximizes EPC.
============================================================
"""

import os
import json
import asyncio
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from dataclasses import dataclass, field, asdict
import httpx

# ============================================================
# CONFIGURATION
# ============================================================

@dataclass
class AffiliateConfig:
    """Elite Affiliate Engine Configuration"""
    
    # Minimum quality thresholds (STRICT)
    MIN_GRAVITY: float = 50.0           # Only proven sellers
    MAX_REFUND_RATE: float = 0.10       # < 10% refunds only
    MIN_EPC: float = 0.50               # Minimum earnings per click
    MIN_COMMISSION: float = 30.0        # Minimum $ per sale
    
    # Niche mappings to affiliate categories
    NICHE_CATEGORIES = {
        "survival": ["survival", "self-defense", "outdoors", "prepping", "emergency"],
        "wealth": ["e-business", "investing", "forex", "crypto", "make-money"],
        "wellness": ["health", "fitness", "diet", "supplements", "beauty", "weight-loss"],
        "productivity": ["self-help", "education", "software", "business"]
    }
    
    # Network priorities (higher = preferred)
    NETWORK_PRIORITY = {
        "clickbank": 10,
        "digistore24": 9,
        "shareasale": 5,
        "amazon": 2
    }
    
    # Auto-rotation settings
    ROTATION_CHECK_HOURS: int = 168     # Check weekly
    GRAVITY_DROP_THRESHOLD: float = 0.20  # 20% drop triggers swap
    
    # Offer vault limits
    MAX_OFFERS_PER_NICHE: int = 5


@dataclass
class AffiliateOffer:
    """Represents a single affiliate offer"""
    
    offer_id: str
    network: str
    niche: str
    name: str
    gravity: float
    epc: float
    commission: float
    refund_rate: float
    hop_link: str
    category: str
    last_updated: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    is_active: bool = True
    performance_score: float = 0.0
    
    def calculate_score(self) -> float:
        """Calculate composite performance score"""
        # Weighted scoring: Gravity (40%), EPC (30%), Commission (20%), Low Refunds (10%)
        gravity_score = min(self.gravity / 100, 1.0) * 40
        epc_score = min(self.epc / 2.0, 1.0) * 30
        commission_score = min(self.commission / 100, 1.0) * 20
        refund_score = (1 - self.refund_rate) * 10
        
        self.performance_score = gravity_score + epc_score + commission_score + refund_score
        return self.performance_score


# ============================================================
# CLICKBANK HUNTER - The King of Digital Products
# ============================================================

class ClickBankHunter:
    """
    Hunts high-converting offers from ClickBank Marketplace.
    Uses the official ClickBank XML feed (FREE).
    """
    
    def __init__(self):
        self.affiliate_id = os.getenv("CLICKBANK_AFFILIATE_ID", "")
        self.dev_key = os.getenv("CLICKBANK_DEV_KEY", "")
        self.marketplace_url = "https://accounts.clickbank.com/marketplace.htm"
        self.feed_base = "https://www.clickbank.com/marketplace/search"
        
    async def fetch_top_offers(
        self, 
        category: str = "all",
        sort_by: str = "gravity",
        limit: int = 20
    ) -> List[Dict]:
        """
        Fetch top performing offers from ClickBank.
        Returns list of qualified offers.
        """
        offers = []
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # ClickBank marketplace search (public)
                params = {
                    "cid": self._get_category_id(category),
                    "sortField": sort_by,
                    "sortOrder": "DESC",
                    "resultsPerPage": limit
                }
                
                # Note: ClickBank's public marketplace API
                response = await client.get(
                    "https://www.clickbank.com/marketplace/search",
                    params=params,
                    headers={"User-Agent": "MoneyMachine/2.0"}
                )
                
                if response.status_code == 200:
                    # Parse response - actual implementation depends on CB API format
                    offers = self._parse_marketplace_response(response.text, category)
                    
        except Exception as e:
            print(f"[AFFILIATE] ClickBank fetch error: {e}")
            
        return offers
    
    def _get_category_id(self, category: str) -> int:
        """Map category name to ClickBank category ID"""
        category_map = {
            "health": 10,
            "e-business": 3,
            "self-help": 18,
            "survival": 15,
            "fitness": 8,
            "spirituality": 19,
            "software": 17
        }
        return category_map.get(category.lower(), 0)
    
    def _parse_marketplace_response(self, html: str, category: str) -> List[Dict]:
        """Parse ClickBank marketplace response"""
        # In production, this would parse the actual HTML/XML
        # For now, return structured placeholder data
        # The real implementation would scrape gravity, EPC, etc.
        return []
    
    def generate_hop_link(self, vendor_id: str, tracking_id: str = "") -> str:
        """Generate ClickBank affiliate hop link"""
        base_url = f"https://{self.affiliate_id}.{vendor_id}.hop.clickbank.net"
        if tracking_id:
            base_url += f"?tid={tracking_id}"
        return base_url
    
    async def get_gravity_history(self, vendor_id: str, days: int = 30) -> List[float]:
        """
        Track gravity trends over time.
        Detects declining offers for rotation.
        """
        # In production: Query historical data or maintain local DB
        return []


# ============================================================
# DIGISTORE24 HUNTER - High Commission European Offers
# ============================================================

class Digistore24Hunter:
    """
    Hunts high-converting offers from Digistore24.
    Up to 90% commissions available!
    """
    
    def __init__(self):
        self.affiliate_id = os.getenv("DIGISTORE24_AFFILIATE_ID", "")
        self.api_key = os.getenv("DIGISTORE24_API_KEY", "")
        self.base_url = "https://www.digistore24.com/api"
        
    async def fetch_top_offers(
        self,
        category: str = "all",
        language: str = "en",
        limit: int = 20
    ) -> List[Dict]:
        """
        Fetch top performing offers from Digistore24.
        """
        offers = []
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # Digistore24 affiliate marketplace
                params = {
                    "category": self._get_category_id(category),
                    "language": language,
                    "sort": "bestseller",
                    "limit": limit
                }
                
                if self.api_key:
                    params["apikey"] = self.api_key
                
                response = await client.get(
                    f"{self.base_url}/marketplace/products",
                    params=params
                )
                
                if response.status_code == 200:
                    data = response.json()
                    offers = self._parse_offers(data, category)
                    
        except Exception as e:
            print(f"[AFFILIATE] Digistore24 fetch error: {e}")
            
        return offers
    
    def _get_category_id(self, category: str) -> str:
        """Map category name to Digistore24 category"""
        category_map = {
            "health": "health_fitness",
            "wealth": "business_investment",
            "survival": "living_lifestyle",
            "productivity": "self_improvement"
        }
        return category_map.get(category.lower(), "all")
    
    def _parse_offers(self, data: dict, category: str) -> List[Dict]:
        """Parse Digistore24 API response"""
        offers = []
        products = data.get("products", [])
        
        for product in products:
            offers.append({
                "offer_id": product.get("id"),
                "network": "digistore24",
                "niche": category,
                "name": product.get("name"),
                "gravity": product.get("popularity_score", 0),
                "epc": product.get("earnings_per_click", 0),
                "commission": product.get("commission_amount", 0),
                "refund_rate": product.get("refund_rate", 0),
                "hop_link": product.get("affiliate_link", ""),
                "category": product.get("category", category)
            })
            
        return offers
    
    def generate_promo_link(self, product_id: str, tracking_id: str = "") -> str:
        """Generate Digistore24 affiliate promo link"""
        base_url = f"https://www.digistore24.com/redir/{product_id}/{self.affiliate_id}/"
        if tracking_id:
            base_url += f"?tid={tracking_id}"
        return base_url


# ============================================================
# THE OFFER VAULT - Centralized Offer Management
# ============================================================

class OfferVault:
    """
    The Offer Vault stores, ranks, and rotates affiliate offers.
    Ensures only ELITE performers are promoted.
    """
    
    def __init__(self, storage_path: str = "/data/offer_vault.json"):
        self.storage_path = storage_path
        self.offers: Dict[str, List[AffiliateOffer]] = {
            "survival": [],
            "wealth": [],
            "wellness": [],
            "productivity": []
        }
        self.config = AffiliateConfig()
        self.load_vault()
        
    def load_vault(self):
        """Load offers from persistent storage"""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    for niche, offers in data.items():
                        self.offers[niche] = [
                            AffiliateOffer(**offer) for offer in offers
                        ]
                print(f"[VAULT] Loaded {sum(len(o) for o in self.offers.values())} offers")
        except Exception as e:
            print(f"[VAULT] Load error: {e}")
            
    def save_vault(self):
        """Persist offers to storage"""
        try:
            data = {
                niche: [asdict(offer) for offer in offers]
                for niche, offers in self.offers.items()
            }
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"[VAULT] Saved {sum(len(o) for o in self.offers.values())} offers")
        except Exception as e:
            print(f"[VAULT] Save error: {e}")
            
    def add_offer(self, offer: AffiliateOffer) -> bool:
        """
        Add an offer to the vault if it meets quality thresholds.
        Returns True if added, False if rejected.
        """
        # Quality gate
        if offer.gravity < self.config.MIN_GRAVITY:
            print(f"[VAULT] Rejected {offer.name}: Gravity {offer.gravity} < {self.config.MIN_GRAVITY}")
            return False
            
        if offer.refund_rate > self.config.MAX_REFUND_RATE:
            print(f"[VAULT] Rejected {offer.name}: Refund rate {offer.refund_rate} > {self.config.MAX_REFUND_RATE}")
            return False
            
        if offer.epc < self.config.MIN_EPC:
            print(f"[VAULT] Rejected {offer.name}: EPC {offer.epc} < {self.config.MIN_EPC}")
            return False
        
        # Calculate performance score
        offer.calculate_score()
        
        # Add to appropriate niche
        niche_offers = self.offers.get(offer.niche, [])
        
        # Check if already exists
        for existing in niche_offers:
            if existing.offer_id == offer.offer_id:
                # Update existing
                existing.gravity = offer.gravity
                existing.epc = offer.epc
                existing.performance_score = offer.performance_score
                existing.last_updated = offer.last_updated
                return True
        
        # Add new offer
        niche_offers.append(offer)
        
        # Keep only top performers
        niche_offers.sort(key=lambda x: x.performance_score, reverse=True)
        self.offers[offer.niche] = niche_offers[:self.config.MAX_OFFERS_PER_NICHE]
        
        self.save_vault()
        return True
    
    def get_best_offer(self, niche: str) -> Optional[AffiliateOffer]:
        """Get the highest-scoring active offer for a niche"""
        niche_offers = self.offers.get(niche, [])
        active_offers = [o for o in niche_offers if o.is_active]
        
        if not active_offers:
            return None
            
        return max(active_offers, key=lambda x: x.performance_score)
    
    def get_offer_for_keywords(self, keywords: List[str]) -> Optional[AffiliateOffer]:
        """
        Smart offer matching based on content keywords.
        Routes to the most relevant high-converting offer.
        """
        # Score each niche based on keyword matches
        niche_scores = {niche: 0 for niche in self.offers.keys()}
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            for niche, categories in self.config.NICHE_CATEGORIES.items():
                if any(cat in keyword_lower for cat in categories):
                    niche_scores[niche] += 1
        
        # Get best matching niche
        best_niche = max(niche_scores, key=niche_scores.get)
        
        if niche_scores[best_niche] == 0:
            # No match, return overall best
            all_offers = []
            for offers in self.offers.values():
                all_offers.extend([o for o in offers if o.is_active])
            if all_offers:
                return max(all_offers, key=lambda x: x.performance_score)
            return None
            
        return self.get_best_offer(best_niche)
    
    def check_rotation_needed(self) -> List[Dict]:
        """
        Check for underperforming offers that need rotation.
        Returns list of offers to swap.
        """
        rotation_needed = []
        
        for niche, offers in self.offers.items():
            for offer in offers:
                # Check if gravity dropped significantly
                # In production: Compare to historical gravity
                if offer.gravity < self.config.MIN_GRAVITY * 0.8:
                    rotation_needed.append({
                        "offer": offer,
                        "reason": "gravity_drop",
                        "niche": niche
                    })
                    
        return rotation_needed


# ============================================================
# LINK ROTATOR - Dynamic Link Swapping
# ============================================================

class LinkRotator:
    """
    Automatically swaps affiliate links across channels
    when performance drops or better offers emerge.
    """
    
    def __init__(self, vault: OfferVault):
        self.vault = vault
        self.link_mappings: Dict[str, str] = {}  # channel_id -> current_link
        self.systeme_io_api_key = os.getenv("SYSTEME_IO_API_KEY", "")
        
    async def update_channel_links(self, channel_id: str, niche: str) -> Dict:
        """
        Update all links for a specific channel to the best offer.
        """
        best_offer = self.vault.get_best_offer(niche)
        
        if not best_offer:
            return {"success": False, "error": "No offers available"}
            
        old_link = self.link_mappings.get(channel_id, "")
        new_link = best_offer.hop_link
        
        if old_link == new_link:
            return {"success": True, "action": "no_change"}
            
        # Update the link
        self.link_mappings[channel_id] = new_link
        
        # Update Systeme.io funnel if configured
        if self.systeme_io_api_key:
            await self._update_systeme_funnel(niche, new_link)
        
        return {
            "success": True,
            "action": "rotated",
            "old_offer": old_link,
            "new_offer": new_link,
            "offer_name": best_offer.name,
            "performance_score": best_offer.performance_score
        }
    
    async def _update_systeme_funnel(self, niche: str, new_link: str):
        """Update Systeme.io funnel with new offer link"""
        # Implementation depends on Systeme.io API
        pass
    
    def get_link_for_content(self, keywords: List[str], tracking_id: str = "") -> str:
        """
        Get the best affiliate link for specific content.
        Used by Creator Engine when generating videos.
        """
        offer = self.vault.get_offer_for_keywords(keywords)
        
        if not offer:
            return ""
            
        link = offer.hop_link
        if tracking_id and "?" not in link:
            link += f"?tid={tracking_id}"
        elif tracking_id:
            link += f"&tid={tracking_id}"
            
        return link


# ============================================================
# MASTER AFFILIATE ENGINE
# ============================================================

class MasterAffiliateEngine:
    """
    The Master Affiliate Engine coordinates all affiliate operations:
    - Discovers new high-converting offers
    - Maintains the Offer Vault
    - Rotates underperformers
    - Provides optimal links for content
    """
    
    def __init__(self):
        self.config = AffiliateConfig()
        self.clickbank = ClickBankHunter()
        self.digistore24 = Digistore24Hunter()
        self.vault = OfferVault()
        self.rotator = LinkRotator(self.vault)
        
    async def hunt_new_offers(self) -> Dict:
        """
        Hunt for new high-converting offers across all networks.
        Should run weekly via n8n cron.
        """
        results = {
            "discovered": 0,
            "added": 0,
            "rejected": 0,
            "by_niche": {}
        }
        
        for niche in self.vault.offers.keys():
            niche_results = {"discovered": 0, "added": 0}
            
            # Hunt ClickBank
            cb_categories = self.config.NICHE_CATEGORIES.get(niche, [niche])
            for category in cb_categories[:2]:  # Limit API calls
                offers = await self.clickbank.fetch_top_offers(
                    category=category,
                    limit=10
                )
                
                for offer_data in offers:
                    niche_results["discovered"] += 1
                    offer = AffiliateOffer(
                        offer_id=offer_data.get("offer_id", ""),
                        network="clickbank",
                        niche=niche,
                        name=offer_data.get("name", ""),
                        gravity=offer_data.get("gravity", 0),
                        epc=offer_data.get("epc", 0),
                        commission=offer_data.get("commission", 0),
                        refund_rate=offer_data.get("refund_rate", 0),
                        hop_link=offer_data.get("hop_link", ""),
                        category=category
                    )
                    
                    if self.vault.add_offer(offer):
                        niche_results["added"] += 1
            
            # Hunt Digistore24
            ds_offers = await self.digistore24.fetch_top_offers(
                category=niche,
                limit=10
            )
            
            for offer_data in ds_offers:
                niche_results["discovered"] += 1
                offer = AffiliateOffer(
                    offer_id=str(offer_data.get("offer_id", "")),
                    network="digistore24",
                    niche=niche,
                    name=offer_data.get("name", ""),
                    gravity=offer_data.get("gravity", 0),
                    epc=offer_data.get("epc", 0),
                    commission=offer_data.get("commission", 0),
                    refund_rate=offer_data.get("refund_rate", 0),
                    hop_link=offer_data.get("hop_link", ""),
                    category=niche
                )
                
                if self.vault.add_offer(offer):
                    niche_results["added"] += 1
            
            results["by_niche"][niche] = niche_results
            results["discovered"] += niche_results["discovered"]
            results["added"] += niche_results["added"]
        
        results["rejected"] = results["discovered"] - results["added"]
        
        return results
    
    async def perform_rotation_check(self) -> Dict:
        """
        Check all offers and rotate underperformers.
        Should run weekly after hunting.
        """
        rotation_results = {
            "checked": 0,
            "rotated": 0,
            "details": []
        }
        
        # Check for rotation needs
        needs_rotation = self.vault.check_rotation_needed()
        
        for item in needs_rotation:
            offer = item["offer"]
            niche = item["niche"]
            
            # Deactivate underperformer
            offer.is_active = False
            
            # Log rotation
            rotation_results["rotated"] += 1
            rotation_results["details"].append({
                "offer": offer.name,
                "niche": niche,
                "reason": item["reason"],
                "old_score": offer.performance_score
            })
        
        self.vault.save_vault()
        
        return rotation_results
    
    def get_best_link(self, niche: str, tracking_id: str = "") -> str:
        """Get the current best affiliate link for a niche"""
        offer = self.vault.get_best_offer(niche)
        if not offer:
            return ""
        
        link = offer.hop_link
        if tracking_id:
            separator = "&" if "?" in link else "?"
            link += f"{separator}tid={tracking_id}"
        return link
    
    def get_link_for_keywords(self, keywords: List[str], tracking_id: str = "") -> str:
        """Get best link based on content keywords"""
        return self.rotator.get_link_for_content(keywords, tracking_id)
    
    def get_vault_summary(self) -> Dict:
        """Get current vault status"""
        summary = {
            "total_offers": 0,
            "active_offers": 0,
            "by_niche": {},
            "top_performers": []
        }
        
        all_offers = []
        for niche, offers in self.vault.offers.items():
            active = [o for o in offers if o.is_active]
            summary["by_niche"][niche] = {
                "total": len(offers),
                "active": len(active),
                "best": offers[0].name if offers else None,
                "best_score": offers[0].performance_score if offers else 0
            }
            summary["total_offers"] += len(offers)
            summary["active_offers"] += len(active)
            all_offers.extend(offers)
        
        # Top 5 overall
        all_offers.sort(key=lambda x: x.performance_score, reverse=True)
        summary["top_performers"] = [
            {
                "name": o.name,
                "niche": o.niche,
                "network": o.network,
                "score": o.performance_score,
                "gravity": o.gravity,
                "epc": o.epc
            }
            for o in all_offers[:5]
        ]
        
        return summary


# ============================================================
# CLI INTERFACE
# ============================================================

if __name__ == "__main__":
    import sys
    
    async def main():
        engine = MasterAffiliateEngine()
        
        if len(sys.argv) > 1:
            command = sys.argv[1]
            
            if command == "hunt":
                print("[AFFILIATE] Hunting new offers...")
                results = await engine.hunt_new_offers()
                print(json.dumps(results, indent=2))
                
            elif command == "rotate":
                print("[AFFILIATE] Checking rotation...")
                results = await engine.perform_rotation_check()
                print(json.dumps(results, indent=2))
                
            elif command == "status":
                summary = engine.get_vault_summary()
                print(json.dumps(summary, indent=2))
                
            elif command == "link":
                niche = sys.argv[2] if len(sys.argv) > 2 else "survival"
                link = engine.get_best_link(niche, tracking_id="n8n")
                print(f"Best link for {niche}: {link}")
                
        else:
            print("Usage: python affiliate.py [hunt|rotate|status|link <niche>]")
    
    asyncio.run(main())
