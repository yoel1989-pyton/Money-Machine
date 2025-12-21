"""
============================================================
MONEY MACHINE - BUSINESSMAN ENGINE
The Automated Financial Sovereignty System
============================================================
Manages revenue, reinvestment, and financial optimization.
Uses FREE financial APIs.
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

class BusinessmanConfig:
    """Businessman Engine Configuration"""
    
    # Revenue allocation percentages
    ALLOCATION = {
        "tax_reserve": 0.30,      # 30% for taxes
        "reinvestment": 0.40,     # 40% back into the machine
        "profit": 0.30            # 30% owner payout
    }
    
    # Reinvestment priorities
    REINVESTMENT_PRIORITIES = [
        {"name": "api_credits", "threshold": 50, "amount": 20},
        {"name": "infrastructure", "threshold": 100, "amount": 50},
        {"name": "advertising", "threshold": 200, "amount": 100}
    ]
    
    # Thresholds for automated actions
    PAYOUT_THRESHOLD = 100  # Minimum balance for payout
    REINVEST_THRESHOLD = 50  # Minimum for reinvestment


# ============================================================
# STRIPE REVENUE TRACKER (FREE - only pay on transactions)
# ============================================================

class StripeManager:
    """
    Manage Stripe payments and revenue tracking.
    FREE: No monthly fee, only transaction fees.
    """
    
    def __init__(self):
        self.api_key = os.getenv("STRIPE_SECRET_KEY")
        self.base_url = "https://api.stripe.com/v1"
        
    async def get_balance(self) -> dict:
        """Get current Stripe balance"""
        if not self.api_key:
            return {"available": 0, "pending": 0, "currency": "usd"}
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/balance",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    available = data.get("available", [{}])[0]
                    pending = data.get("pending", [{}])[0]
                    
                    return {
                        "available": available.get("amount", 0) / 100,  # Convert cents
                        "pending": pending.get("amount", 0) / 100,
                        "currency": available.get("currency", "usd")
                    }
                    
        except Exception as e:
            print(f"[BUSINESSMAN] Stripe error: {e}")
            
        return {"available": 0, "pending": 0, "currency": "usd"}
    
    async def get_recent_revenue(self, days: int = 30) -> dict:
        """Get revenue for the last N days"""
        if not self.api_key:
            return {"total": 0, "count": 0}
            
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/charges",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    params={
                        "created[gte]": int(start_date.timestamp()),
                        "limit": 100
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    charges = data.get("data", [])
                    
                    total = sum(
                        c.get("amount", 0) for c in charges 
                        if c.get("paid") and not c.get("refunded")
                    )
                    
                    return {
                        "total": total / 100,
                        "count": len(charges),
                        "period_days": days
                    }
                    
        except Exception as e:
            print(f"[BUSINESSMAN] Revenue error: {e}")
            
        return {"total": 0, "count": 0, "period_days": days}
    
    async def create_payment_link(
        self,
        product_name: str,
        price_cents: int,
        description: str = ""
    ) -> dict:
        """Create a payment link for a product"""
        if not self.api_key:
            return {"success": False, "error": "Stripe not configured"}
            
        try:
            async with httpx.AsyncClient() as client:
                # Create product
                product_response = await client.post(
                    f"{self.base_url}/products",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    data={
                        "name": product_name,
                        "description": description
                    }
                )
                
                if product_response.status_code != 200:
                    return {"success": False, "error": "Product creation failed"}
                
                product_id = product_response.json().get("id")
                
                # Create price
                price_response = await client.post(
                    f"{self.base_url}/prices",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    data={
                        "unit_amount": price_cents,
                        "currency": "usd",
                        "product": product_id
                    }
                )
                
                if price_response.status_code != 200:
                    return {"success": False, "error": "Price creation failed"}
                
                price_id = price_response.json().get("id")
                
                # Create payment link
                link_response = await client.post(
                    f"{self.base_url}/payment_links",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    data={"line_items[0][price]": price_id, "line_items[0][quantity]": 1}
                )
                
                if link_response.status_code == 200:
                    return {
                        "success": True,
                        "url": link_response.json().get("url"),
                        "product_id": product_id,
                        "price_id": price_id
                    }
                    
        except Exception as e:
            print(f"[BUSINESSMAN] Payment link error: {e}")
            
        return {"success": False, "error": "Unknown error"}


# ============================================================
# PAYPAL MANAGER (FREE)
# ============================================================

class PayPalManager:
    """
    Manage PayPal payments.
    FREE: No monthly fee.
    """
    
    def __init__(self):
        self.client_id = os.getenv("PAYPAL_CLIENT_ID")
        self.client_secret = os.getenv("PAYPAL_CLIENT_SECRET")
        self.access_token = None
        self.base_url = "https://api-m.paypal.com"  # Use sandbox for testing
        
    async def authenticate(self) -> bool:
        """Get PayPal access token"""
        if not self.client_id or not self.client_secret:
            return False
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/v1/oauth2/token",
                    auth=(self.client_id, self.client_secret),
                    data={"grant_type": "client_credentials"}
                )
                
                if response.status_code == 200:
                    self.access_token = response.json().get("access_token")
                    return True
                    
        except Exception as e:
            print(f"[BUSINESSMAN] PayPal auth error: {e}")
            
        return False
    
    async def get_balance(self) -> dict:
        """Get PayPal balance"""
        if not self.access_token:
            await self.authenticate()
            
        if not self.access_token:
            return {"available": 0, "currency": "USD"}
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/v1/reporting/balances",
                    headers={"Authorization": f"Bearer {self.access_token}"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    balances = data.get("balances", [])
                    
                    if balances:
                        primary = balances[0]
                        available = primary.get("available_balance", {})
                        return {
                            "available": float(available.get("value", 0)),
                            "currency": available.get("currency_code", "USD")
                        }
                        
        except Exception as e:
            print(f"[BUSINESSMAN] PayPal balance error: {e}")
            
        return {"available": 0, "currency": "USD"}


# ============================================================
# MERCURY BANKING (FREE business banking)
# ============================================================

class MercuryManager:
    """
    Programmatic banking with Mercury.
    FREE: No monthly fees for business accounts.
    """
    
    def __init__(self):
        self.api_key = os.getenv("MERCURY_API_KEY")
        self.base_url = "https://api.mercury.com/api/v1"
        
    async def get_accounts(self) -> list:
        """Get all Mercury accounts"""
        if not self.api_key:
            return []
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/accounts",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return [
                        {
                            "id": acc.get("id"),
                            "name": acc.get("name"),
                            "balance": acc.get("currentBalance"),
                            "type": acc.get("kind")
                        }
                        for acc in data.get("accounts", [])
                    ]
                    
        except Exception as e:
            print(f"[BUSINESSMAN] Mercury error: {e}")
            
        return []
    
    async def get_total_balance(self) -> float:
        """Get total balance across all accounts"""
        accounts = await self.get_accounts()
        return sum(acc.get("balance", 0) for acc in accounts)
    
    async def get_recent_transactions(self, days: int = 30) -> list:
        """Get recent transactions"""
        if not self.api_key:
            return []
            
        accounts = await self.get_accounts()
        all_transactions = []
        
        for account in accounts:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{self.base_url}/account/{account['id']}/transactions",
                        headers={"Authorization": f"Bearer {self.api_key}"},
                        params={"limit": 50}
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        all_transactions.extend(data.get("transactions", []))
                        
            except Exception:
                pass
                
        return all_transactions


# ============================================================
# AFFILIATE TRACKER
# ============================================================

class AffiliateTracker:
    """
    Track affiliate earnings across networks.
    """
    
    def __init__(self):
        self.clickbank_api = os.getenv("CLICKBANK_API_KEY")
        self.clickbank_account = os.getenv("CLICKBANK_ACCOUNT_NAME")
        
    async def get_clickbank_earnings(self, days: int = 30) -> dict:
        """Get ClickBank earnings"""
        if not self.clickbank_api or not self.clickbank_account:
            return {"earnings": 0, "sales": 0}
            
        try:
            # ClickBank API endpoint
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.clickbank.com/rest/1.3/accounting/{self.clickbank_account}",
                    headers={
                        "Authorization": f"{self.clickbank_account}:{self.clickbank_api}",
                        "Accept": "application/json"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "earnings": data.get("totalAccountAmount", 0),
                        "sales": data.get("totalOrderCount", 0)
                    }
                    
        except Exception as e:
            print(f"[BUSINESSMAN] ClickBank error: {e}")
            
        return {"earnings": 0, "sales": 0}
    
    async def get_all_affiliate_earnings(self) -> dict:
        """Get earnings from all affiliate networks"""
        clickbank = await self.get_clickbank_earnings()
        
        return {
            "clickbank": clickbank,
            "total": clickbank.get("earnings", 0)
        }


# ============================================================
# REINVESTMENT ENGINE
# ============================================================

class ReinvestmentEngine:
    """
    Automated reinvestment logic.
    Decides when and how to reinvest profits.
    """
    
    def __init__(self):
        self.config = BusinessmanConfig
        
    def calculate_allocation(self, revenue: float) -> dict:
        """Calculate how to allocate revenue"""
        return {
            "tax_reserve": revenue * self.config.ALLOCATION["tax_reserve"],
            "reinvestment": revenue * self.config.ALLOCATION["reinvestment"],
            "profit": revenue * self.config.ALLOCATION["profit"]
        }
    
    def get_reinvestment_recommendations(self, available_funds: float) -> list:
        """Get prioritized reinvestment recommendations"""
        recommendations = []
        remaining = available_funds
        
        for priority in self.config.REINVESTMENT_PRIORITIES:
            if remaining >= priority["threshold"]:
                recommendations.append({
                    "action": priority["name"],
                    "amount": min(priority["amount"], remaining),
                    "reason": f"Invest in {priority['name']} for growth"
                })
                remaining -= priority["amount"]
                
            if remaining <= 0:
                break
                
        return recommendations
    
    def should_payout(self, balance: float) -> bool:
        """Determine if we should trigger a payout"""
        return balance >= self.config.PAYOUT_THRESHOLD
    
    def should_reinvest(self, balance: float) -> bool:
        """Determine if we should reinvest"""
        return balance >= self.config.REINVEST_THRESHOLD


# ============================================================
# MASTER BUSINESSMAN - ORCHESTRATOR
# ============================================================

class MasterBusinessman:
    """
    Master Businessman that orchestrates all financial operations.
    Tracks revenue, manages reinvestment, and optimizes cash flow.
    """
    
    def __init__(self):
        self.stripe = StripeManager()
        self.paypal = PayPalManager()
        self.mercury = MercuryManager()
        self.affiliate = AffiliateTracker()
        self.reinvestment = ReinvestmentEngine()
        
    async def get_financial_snapshot(self) -> dict:
        """
        Get a complete financial snapshot.
        Called by n8n to assess the machine's financial health.
        """
        # Gather all balances
        stripe_balance = await self.stripe.get_balance()
        paypal_balance = await self.paypal.get_balance()
        mercury_balance = await self.mercury.get_total_balance()
        
        # Get revenue data
        stripe_revenue = await self.stripe.get_recent_revenue(30)
        affiliate_revenue = await self.affiliate.get_all_affiliate_earnings()
        
        # Calculate totals
        total_available = (
            stripe_balance.get("available", 0) +
            paypal_balance.get("available", 0) +
            mercury_balance
        )
        
        total_revenue_30d = (
            stripe_revenue.get("total", 0) +
            affiliate_revenue.get("total", 0)
        )
        
        # Calculate allocation
        allocation = self.reinvestment.calculate_allocation(total_revenue_30d)
        
        # Get recommendations
        recommendations = self.reinvestment.get_reinvestment_recommendations(
            allocation["reinvestment"]
        )
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "balances": {
                "stripe": stripe_balance,
                "paypal": paypal_balance,
                "mercury": mercury_balance,
                "total": total_available
            },
            "revenue_30d": {
                "stripe": stripe_revenue,
                "affiliate": affiliate_revenue,
                "total": total_revenue_30d
            },
            "allocation": allocation,
            "recommendations": recommendations,
            "actions": {
                "should_payout": self.reinvestment.should_payout(allocation["profit"]),
                "should_reinvest": self.reinvestment.should_reinvest(allocation["reinvestment"])
            }
        }
    
    async def execute_daily_routine(self) -> dict:
        """
        Execute daily financial routine.
        Called by n8n cron job.
        """
        snapshot = await self.get_financial_snapshot()
        actions_taken = []
        
        # Check if payout is needed
        if snapshot["actions"]["should_payout"]:
            actions_taken.append({
                "type": "payout_notification",
                "amount": snapshot["allocation"]["profit"],
                "message": "Ready for owner payout"
            })
        
        # Check reinvestment opportunities
        if snapshot["actions"]["should_reinvest"]:
            for rec in snapshot["recommendations"]:
                actions_taken.append({
                    "type": "reinvestment_recommendation",
                    **rec
                })
        
        return {
            "snapshot": snapshot,
            "actions_taken": actions_taken,
            "status": "complete"
        }
    
    async def get_roi_metrics(self) -> dict:
        """Calculate ROI metrics for the machine"""
        revenue = await self.stripe.get_recent_revenue(30)
        
        # Estimate costs (would need to track actual costs)
        estimated_monthly_cost = 50  # $50 budget mentioned
        
        monthly_revenue = revenue.get("total", 0)
        roi = ((monthly_revenue - estimated_monthly_cost) / max(estimated_monthly_cost, 1)) * 100
        
        return {
            "monthly_revenue": monthly_revenue,
            "monthly_cost": estimated_monthly_cost,
            "net_profit": monthly_revenue - estimated_monthly_cost,
            "roi_percentage": roi,
            "breakeven_status": "profitable" if monthly_revenue > estimated_monthly_cost else "pre-revenue"
        }


# ============================================================
# CLI INTERFACE
# ============================================================

if __name__ == "__main__":
    import sys
    
    async def main():
        businessman = MasterBusinessman()
        
        if len(sys.argv) > 1:
            command = sys.argv[1]
            
            if command == "snapshot":
                result = await businessman.get_financial_snapshot()
            elif command == "daily":
                result = await businessman.execute_daily_routine()
            elif command == "roi":
                result = await businessman.get_roi_metrics()
            else:
                result = {"error": "Usage: businessman.py [snapshot|daily|roi]"}
        else:
            result = await businessman.get_financial_snapshot()
        
        print(json.dumps(result, indent=2))
    
    asyncio.run(main())
