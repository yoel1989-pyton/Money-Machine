"""
============================================================
MONEY MACHINE - ENGINE ORCHESTRATOR
The Central Nervous System
============================================================
Coordinates all engines for seamless operation.
Includes self-healing, self-improving, self-fixing Omni Orchestrator.
============================================================
"""

from .hunter import MasterHunter, HunterConfig
from .creator import MasterCreator, CreatorConfig
from .gatherer import MasterGatherer, GathererConfig
from .businessman import MasterBusinessman, BusinessmanConfig
from .survivor import MasterSurvivor, SurvivorConfig
from .omni_orchestrator import (
    OmniOrchestrator,
    OmniConfig,
    PerformanceTracker,
    SelfHealer,
    SelfFixer,
    SelfImprover,
    ResourceScaler,
    SystemState,
    HealthStatus
)
from .affiliate import (
    MasterAffiliateEngine,
    AffiliateConfig,
    ClickBankHunter,
    Digistore24Hunter,
    OfferVault,
    AffiliateOffer
)
from .systeme_io import MasterSystemeManager, SystemeConfig
from .niche_manager import ChannelManager, Niche, NicheConfig, NICHE_STRATEGIES
from .auditor import MasterFinancialAuditor, AuditorConfig
from .elite_survivor import (
    MasterEliteSurvivor,
    SelfHealingEngine,
    SelfImprovementEngine,
    OmniAwarenessEngine
)
from .profit_allocator import (
    MasterProfitAllocator,
    ProfitAllocator,
    AllocationConfig,
    ReinvestmentEngine
)
from .ad_reinvestor import (
    MasterAdReinvestor,
    AdReinvestor,
    AdConfig,
    WinnerSelector,
    CampaignManager
)

__all__ = [
    # Core Engines
    "MasterHunter",
    "MasterCreator", 
    "MasterGatherer",
    "MasterBusinessman",
    "MasterSurvivor",
    # Configurations
    "HunterConfig",
    "CreatorConfig",
    "GathererConfig",
    "BusinessmanConfig",
    "SurvivorConfig",
    "OmniConfig",
    "AffiliateConfig",
    "SystemeConfig",
    "AuditorConfig",
    "NicheConfig",
    # Orchestrators
    "MoneyMachine",
    "OmniOrchestrator",
    # Self-Management Components
    "PerformanceTracker",
    "SelfHealer",
    "SelfFixer",
    "SelfImprover",
    "ResourceScaler",
    # States
    "SystemState",
    "HealthStatus",
    # Affiliate/Marketing
    "MasterAffiliateEngine",
    "ClickBankHunter",
    "Digistore24Hunter",
    "OfferVault",
    "AffiliateOffer",
    "MasterSystemeManager",
    # Niche Management
    "ChannelManager",
    "Niche",
    "NICHE_STRATEGIES",
    # Financial
    "MasterFinancialAuditor",
    # Elite Survivor (Self-Healing/Improving/Awareness)
    "MasterEliteSurvivor",
    "SelfHealingEngine",
    "SelfImprovementEngine",
    "OmniAwarenessEngine",
    # Profit Allocation
    "MasterProfitAllocator",
    "ProfitAllocator",
    "AllocationConfig",
    "ReinvestmentEngine",
    # Ad Reinvestment
    "MasterAdReinvestor",
    "AdReinvestor",
    "AdConfig",
    "WinnerSelector",
    "CampaignManager"
]


class MoneyMachine:
    """
    The Money Machine - Central Orchestrator
    Coordinates all 5 engines for autonomous operation.
    """
    
    def __init__(self):
        self.hunter = MasterHunter()
        self.creator = MasterCreator()
        self.gatherer = MasterGatherer()
        self.businessman = MasterBusinessman()
        self.survivor = MasterSurvivor()
        
    async def execute_full_cycle(self, niche: str = None) -> dict:
        """
        Execute a complete money-making cycle:
        1. Hunt for opportunities
        2. Create content
        3. Distribute to platforms
        4. Track financials
        5. Monitor health
        """
        results = {
            "cycle_id": None,
            "hunt": None,
            "create": None,
            "distribute": None,
            "financials": None,
            "health": None
        }
        
        try:
            # Step 1: Hunt
            hunt_results = await self.hunter.hunt(
                [niche] if niche else None
            )
            results["hunt"] = hunt_results
            
            if not hunt_results.get("top_opportunities"):
                return results
            
            # Get best opportunity
            best_opp = hunt_results["top_opportunities"][0]
            topic = best_opp.get("title", niche or "trending topic")
            
            # Step 2: Create
            create_results = await self.creator.create_multiplatform(topic)
            results["create"] = create_results
            
            if create_results.get("status") != "complete":
                await self.survivor.handle_error(
                    "creator",
                    create_results.get("error", "Creation failed"),
                    {"topic": topic}
                )
                return results
            
            # Step 3: Distribute
            video_path = create_results["assets"].get("final_video")
            script = create_results.get("script", {})
            
            distribute_results = await self.gatherer.distribute(
                video_path,
                script.get("title", topic),
                script.get("description", ""),
                script.get("hashtags", [])
            )
            results["distribute"] = distribute_results
            
            # Step 4: Financials
            results["financials"] = await self.businessman.get_roi_metrics()
            
            # Step 5: Health
            results["health"] = await self.survivor.run_health_check()
            
        except Exception as e:
            await self.survivor.handle_error(
                "money_machine",
                str(e),
                {"cycle": "full"}
            )
            results["error"] = str(e)
        
        return results
    
    async def get_dashboard(self) -> dict:
        """Get a complete dashboard view"""
        return {
            "financials": await self.businessman.get_financial_snapshot(),
            "distribution_stats": await self.gatherer.get_stats(),
            "system_health": await self.survivor.get_system_status()
        }
