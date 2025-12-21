"""
============================================================
MONEY MACHINE - PROFIT ALLOCATOR ENGINE
Profit-First Capital Discipline
============================================================
Implements the 30/40/30 allocation strategy:
- 30% Tax Reserve
- 40% Reinvestment (Ads, Tools, Content)
- 30% Owner Profit

Money enters → is protected → reinvested → paid to you
No leaks. No freezes. No guesswork.
============================================================
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AllocationStatus(Enum):
    """Status of profit allocation"""
    PENDING = "pending"
    PROCESSED = "processed"
    TRANSFERRED = "transferred"
    FAILED = "failed"


class TransferDestination(Enum):
    """Where money should go"""
    TAX_VAULT = "tax_vault"
    REINVEST_ADS = "reinvest_ads"
    REINVEST_TOOLS = "reinvest_tools"
    REINVEST_CONTENT = "reinvest_content"
    OWNER_PROFIT = "owner_profit"


@dataclass
class AllocationConfig:
    """Configuration for profit allocation"""
    
    # Core allocation percentages (must sum to 100)
    tax_percent: float = 30.0
    reinvest_percent: float = 40.0
    owner_percent: float = 30.0
    
    # Reinvestment breakdown (must sum to 100)
    reinvest_ads_percent: float = 50.0      # 50% of reinvest = 20% total
    reinvest_tools_percent: float = 30.0    # 30% of reinvest = 12% total
    reinvest_content_percent: float = 20.0  # 20% of reinvest = 8% total
    
    # Thresholds
    min_balance_to_allocate: float = 100.0  # Don't allocate below $100
    sweep_threshold: float = 100.0          # PayPal sweep at $100
    scale_threshold: float = 500.0          # Start scaling at $500
    empire_threshold: float = 1000.0        # Full reinvestment at $1000
    
    # Transfer destinations (account IDs/emails)
    tax_account: str = ""
    owner_account: str = ""
    ads_account: str = ""
    
    def validate(self) -> bool:
        """Validate configuration sums to 100%"""
        core_sum = self.tax_percent + self.reinvest_percent + self.owner_percent
        reinvest_sum = (
            self.reinvest_ads_percent + 
            self.reinvest_tools_percent + 
            self.reinvest_content_percent
        )
        return abs(core_sum - 100.0) < 0.01 and abs(reinvest_sum - 100.0) < 0.01


@dataclass
class Allocation:
    """A single profit allocation"""
    
    allocation_id: str
    period_start: datetime
    period_end: datetime
    
    # Source amounts
    total_revenue: float
    total_expenses: float
    net_profit: float
    
    # Allocated amounts
    tax_reserve: float
    reinvest_fund: float
    owner_profit: float
    
    # Reinvest breakdown
    ads_budget: float
    tools_budget: float
    content_budget: float
    
    # Status
    status: AllocationStatus = AllocationStatus.PENDING
    processed_at: Optional[datetime] = None
    transfers: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "allocation_id": self.allocation_id,
            "period": f"{self.period_start.date()} to {self.period_end.date()}",
            "net_profit": f"${self.net_profit:.2f}",
            "allocations": {
                "tax_reserve": f"${self.tax_reserve:.2f} (30%)",
                "reinvest": f"${self.reinvest_fund:.2f} (40%)",
                "owner_profit": f"${self.owner_profit:.2f} (30%)",
            },
            "reinvest_breakdown": {
                "ads": f"${self.ads_budget:.2f}",
                "tools": f"${self.tools_budget:.2f}",
                "content": f"${self.content_budget:.2f}",
            },
            "status": self.status.value
        }


class ProfitAllocator:
    """
    Core profit allocation engine.
    Implements Profit-First methodology.
    """
    
    def __init__(self, config: Optional[AllocationConfig] = None):
        self.config = config or AllocationConfig()
        if not self.config.validate():
            raise ValueError("Allocation percentages must sum to 100%")
        
        self.allocations: List[Allocation] = []
        
    def allocate(self, balance: float) -> Dict[str, float]:
        """
        Simple allocation of a balance.
        Returns dict with amounts for each bucket.
        """
        if balance < self.config.min_balance_to_allocate:
            return {
                "tax": 0,
                "reinvest": 0,
                "owner": 0,
                "message": f"Balance ${balance:.2f} below minimum ${self.config.min_balance_to_allocate}"
            }
        
        tax = round(balance * (self.config.tax_percent / 100), 2)
        reinvest = round(balance * (self.config.reinvest_percent / 100), 2)
        owner = round(balance * (self.config.owner_percent / 100), 2)
        
        # Ensure no rounding errors lose money
        total = tax + reinvest + owner
        if total != balance:
            owner += (balance - total)
        
        return {
            "tax": tax,
            "reinvest": reinvest,
            "owner": owner,
        }
    
    def calculate_weekly_allocation(
        self, 
        revenue: float, 
        expenses: float,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None
    ) -> Allocation:
        """
        Calculate a full weekly allocation with breakdown.
        """
        import uuid
        
        if period_end is None:
            period_end = datetime.now()
        if period_start is None:
            period_start = period_end - timedelta(days=7)
        
        net_profit = revenue - expenses
        
        if net_profit <= 0:
            return Allocation(
                allocation_id=str(uuid.uuid4()),
                period_start=period_start,
                period_end=period_end,
                total_revenue=revenue,
                total_expenses=expenses,
                net_profit=net_profit,
                tax_reserve=0,
                reinvest_fund=0,
                owner_profit=0,
                ads_budget=0,
                tools_budget=0,
                content_budget=0,
                status=AllocationStatus.PENDING
            )
        
        # Core allocation
        tax_reserve = round(net_profit * (self.config.tax_percent / 100), 2)
        reinvest_fund = round(net_profit * (self.config.reinvest_percent / 100), 2)
        owner_profit = round(net_profit * (self.config.owner_percent / 100), 2)
        
        # Reinvest breakdown
        ads_budget = round(reinvest_fund * (self.config.reinvest_ads_percent / 100), 2)
        tools_budget = round(reinvest_fund * (self.config.reinvest_tools_percent / 100), 2)
        content_budget = round(reinvest_fund * (self.config.reinvest_content_percent / 100), 2)
        
        allocation = Allocation(
            allocation_id=str(uuid.uuid4()),
            period_start=period_start,
            period_end=period_end,
            total_revenue=revenue,
            total_expenses=expenses,
            net_profit=net_profit,
            tax_reserve=tax_reserve,
            reinvest_fund=reinvest_fund,
            owner_profit=owner_profit,
            ads_budget=ads_budget,
            tools_budget=tools_budget,
            content_budget=content_budget,
            status=AllocationStatus.PENDING
        )
        
        self.allocations.append(allocation)
        return allocation
    
    def should_sweep(self, paypal_balance: float) -> Tuple[bool, float]:
        """
        Determine if PayPal should be swept.
        Returns (should_sweep, amount_to_sweep)
        """
        reserve = 50.0  # Keep $50 buffer
        
        if paypal_balance <= self.config.sweep_threshold:
            return False, 0
        
        sweep_amount = paypal_balance - reserve
        return True, round(sweep_amount, 2)
    
    def should_scale(self, total_balance: float) -> Dict[str, bool]:
        """
        Determine which scaling actions should trigger.
        """
        return {
            "enable_ads": total_balance >= self.config.scale_threshold,
            "upgrade_tts": total_balance >= self.config.scale_threshold,
            "upgrade_stock": total_balance >= self.config.empire_threshold,
            "expand_niches": total_balance >= self.config.empire_threshold,
        }
    
    def get_mode(self, total_balance: float) -> str:
        """
        Determine current operational mode based on balance.
        """
        if total_balance < self.config.min_balance_to_allocate:
            return "bootstrap"
        elif total_balance < self.config.scale_threshold:
            return "growth"
        elif total_balance < self.config.empire_threshold:
            return "scale"
        else:
            return "empire"


class ReinvestmentEngine:
    """
    Decides how to reinvest allocated funds.
    Tracks ROI on reinvestment decisions.
    """
    
    def __init__(self):
        self.investments: List[Dict] = []
        self.roi_history: Dict[str, List[float]] = {
            "ads": [],
            "tools": [],
            "content": [],
        }
    
    def allocate_ads_budget(
        self, 
        budget: float, 
        content_performance: List[Dict]
    ) -> List[Dict]:
        """
        Allocate ads budget to winning content.
        """
        if not content_performance or budget <= 0:
            return []
        
        # Sort by RPM (revenue per mille)
        sorted_content = sorted(
            content_performance, 
            key=lambda x: x.get("rpm", 0), 
            reverse=True
        )
        
        # Take top 10%
        top_count = max(1, len(sorted_content) // 10)
        winners = sorted_content[:top_count]
        
        # Distribute budget proportionally to RPM
        total_rpm = sum(c.get("rpm", 0) for c in winners)
        if total_rpm == 0:
            # Equal distribution if no RPM data
            per_content = budget / len(winners)
            return [
                {
                    "content_id": w.get("content_id"),
                    "platform": w.get("platform", "youtube_ads"),
                    "budget": round(per_content, 2),
                    "reason": "winner_equal"
                }
                for w in winners
            ]
        
        allocations = []
        for w in winners:
            rpm = w.get("rpm", 0)
            proportion = rpm / total_rpm
            alloc_amount = round(budget * proportion, 2)
            
            allocations.append({
                "content_id": w.get("content_id"),
                "platform": w.get("platform", "youtube_ads"),
                "budget": alloc_amount,
                "rpm": rpm,
                "reason": "winner_proportional"
            })
        
        return allocations
    
    def recommend_tools(self, budget: float, current_stack: List[str]) -> List[Dict]:
        """
        Recommend tool upgrades based on budget.
        """
        recommendations = []
        
        # Priority order of upgrades
        upgrade_path = [
            {
                "name": "ElevenLabs",
                "current": "edge_tts",
                "cost": 5.0,
                "impact": "20-30% conversion lift from natural voice",
                "priority": 1
            },
            {
                "name": "Storyblocks",
                "current": "pexels",
                "cost": 15.0,
                "impact": "Higher authority, less spam overlap",
                "priority": 2
            },
            {
                "name": "Claude API",
                "current": "basic_prompts",
                "cost": 10.0,
                "impact": "Better scripts, more engagement",
                "priority": 3
            },
        ]
        
        remaining = budget
        for upgrade in upgrade_path:
            if upgrade["current"] in current_stack and remaining >= upgrade["cost"]:
                recommendations.append({
                    "upgrade": upgrade["name"],
                    "replaces": upgrade["current"],
                    "monthly_cost": upgrade["cost"],
                    "expected_impact": upgrade["impact"],
                    "approved": True
                })
                remaining -= upgrade["cost"]
        
        return recommendations
    
    def track_roi(self, category: str, spent: float, returned: float):
        """
        Track ROI for a category.
        """
        if spent > 0:
            roi = (returned - spent) / spent
            self.roi_history[category].append(roi)


class MasterProfitAllocator:
    """
    Master orchestrator for all profit allocation.
    """
    
    def __init__(self, config: Optional[AllocationConfig] = None):
        self.allocator = ProfitAllocator(config)
        self.reinvestor = ReinvestmentEngine()
        self.logger = logging.getLogger(__name__)
    
    async def process_weekly(
        self, 
        revenue: float, 
        expenses: float,
        paypal_balance: float,
        content_metrics: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Process weekly allocation and generate action items.
        """
        # Calculate allocation
        allocation = self.allocator.calculate_weekly_allocation(revenue, expenses)
        
        # Check sweep
        should_sweep, sweep_amount = self.allocator.should_sweep(paypal_balance)
        
        # Get mode
        mode = self.allocator.get_mode(allocation.net_profit)
        
        # Get scaling recommendations
        scaling = self.allocator.should_scale(allocation.net_profit)
        
        # Get ads allocation if in scale mode
        ads_allocation = []
        if scaling["enable_ads"] and content_metrics:
            ads_allocation = self.reinvestor.allocate_ads_budget(
                allocation.ads_budget,
                content_metrics
            )
        
        # Get tool recommendations
        tool_recommendations = self.reinvestor.recommend_tools(
            allocation.tools_budget,
            ["edge_tts", "pexels", "basic_prompts"]  # Current stack
        )
        
        return {
            "allocation": allocation.to_dict(),
            "mode": mode,
            "actions": {
                "sweep_paypal": {
                    "execute": should_sweep,
                    "amount": sweep_amount
                },
                "ads_boost": ads_allocation,
                "tool_upgrades": tool_recommendations,
                "scaling": scaling
            },
            "report_generated": datetime.now().isoformat()
        }
    
    async def get_summary(self) -> Dict:
        """
        Get summary of all allocations.
        """
        total_allocated = sum(a.net_profit for a in self.allocator.allocations)
        total_tax = sum(a.tax_reserve for a in self.allocator.allocations)
        total_reinvest = sum(a.reinvest_fund for a in self.allocator.allocations)
        total_owner = sum(a.owner_profit for a in self.allocator.allocations)
        
        return {
            "total_periods": len(self.allocator.allocations),
            "total_allocated": f"${total_allocated:.2f}",
            "total_tax_reserved": f"${total_tax:.2f}",
            "total_reinvested": f"${total_reinvest:.2f}",
            "total_owner_profit": f"${total_owner:.2f}",
            "avg_roi": {
                "ads": sum(self.reinvestor.roi_history["ads"]) / len(self.reinvestor.roi_history["ads"]) if self.reinvestor.roi_history["ads"] else 0,
                "tools": sum(self.reinvestor.roi_history["tools"]) / len(self.reinvestor.roi_history["tools"]) if self.reinvestor.roi_history["tools"] else 0,
            }
        }


# Quick test
if __name__ == "__main__":
    async def test():
        allocator = MasterProfitAllocator()
        
        result = await allocator.process_weekly(
            revenue=1500.00,
            expenses=200.00,
            paypal_balance=450.00,
            content_metrics=[
                {"content_id": "vid_001", "rpm": 12.5, "platform": "youtube"},
                {"content_id": "vid_002", "rpm": 8.3, "platform": "youtube"},
                {"content_id": "vid_003", "rpm": 15.2, "platform": "youtube"},
            ]
        )
        
        print("Weekly Allocation Result:")
        import json
        print(json.dumps(result, indent=2))
    
    asyncio.run(test())
