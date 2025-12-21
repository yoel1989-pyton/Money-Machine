"""
============================================================
MONEY MACHINE - SURVIVOR ENGINE
The Anti-Fragility & Self-Healing System
============================================================
Monitors system health, handles errors, and ensures resilience.
The immune system of the Money Machine.
============================================================
"""

import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Callable
from pathlib import Path
import httpx

# ============================================================
# CONFIGURATION
# ============================================================

class SurvivorConfig:
    """Survivor Engine Configuration"""
    
    # Alert thresholds
    ERROR_THRESHOLD = 3  # Errors before alert
    RETRY_ATTEMPTS = 3
    RETRY_DELAY = 60  # seconds
    
    # Health check intervals
    HEALTH_CHECK_INTERVAL = 300  # 5 minutes
    
    # Account health thresholds
    SHADOWBAN_THRESHOLD = {
        "youtube": {"views": 10, "hours": 48},
        "tiktok": {"views": 50, "hours": 24},
        "instagram": {"engagement": 0.01, "hours": 48}
    }
    
    # Logging
    LOG_DIR = Path("/data/logs")


# ============================================================
# ALERT MANAGER (Telegram + Discord)
# ============================================================

class AlertManager:
    """
    Send alerts via Telegram and Discord.
    Both are FREE with unlimited messages.
    """
    
    def __init__(self):
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.telegram_chat = os.getenv("TELEGRAM_CHAT_ID")
        self.discord_webhook = os.getenv("DISCORD_WEBHOOK_URL")
        
    async def send_telegram(self, message: str, priority: str = "normal") -> bool:
        """Send Telegram alert"""
        if not self.telegram_token or not self.telegram_chat:
            return False
            
        emoji = {
            "critical": "🚨",
            "warning": "⚠️",
            "info": "ℹ️",
            "success": "✅"
        }.get(priority, "📢")
        
        formatted = f"{emoji} *MONEY MACHINE*\n\n{message}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://api.telegram.org/bot{self.telegram_token}/sendMessage",
                    json={
                        "chat_id": self.telegram_chat,
                        "text": formatted,
                        "parse_mode": "Markdown"
                    }
                )
                return response.status_code == 200
                
        except Exception as e:
            print(f"[SURVIVOR] Telegram error: {e}")
            return False
    
    async def send_discord(self, message: str, priority: str = "normal") -> bool:
        """Send Discord alert"""
        if not self.discord_webhook:
            return False
            
        color = {
            "critical": 0xFF0000,  # Red
            "warning": 0xFFA500,   # Orange
            "info": 0x0099FF,      # Blue
            "success": 0x00FF00    # Green
        }.get(priority, 0x808080)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.discord_webhook,
                    json={
                        "embeds": [{
                            "title": "🤖 Money Machine Alert",
                            "description": message,
                            "color": color,
                            "timestamp": datetime.utcnow().isoformat()
                        }]
                    }
                )
                return response.status_code in [200, 204]
                
        except Exception as e:
            print(f"[SURVIVOR] Discord error: {e}")
            return False
    
    async def alert(self, message: str, priority: str = "normal") -> dict:
        """Send alert to all channels"""
        results = {
            "telegram": await self.send_telegram(message, priority),
            "discord": await self.send_discord(message, priority)
        }
        return results


# ============================================================
# ERROR TRACKER & LOGGER
# ============================================================

class ErrorTracker:
    """
    Track and log errors across all engines.
    Implements circuit breaker pattern.
    """
    
    def __init__(self):
        self.errors = {}  # {component: [error_timestamps]}
        self.circuit_breakers = {}  # {component: is_open}
        self.log_dir = SurvivorConfig.LOG_DIR
        
        # Ensure log directory exists
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
    def record_error(self, component: str, error: str, context: dict = None) -> dict:
        """Record an error occurrence"""
        timestamp = datetime.utcnow().isoformat()
        
        if component not in self.errors:
            self.errors[component] = []
            
        error_record = {
            "timestamp": timestamp,
            "error": error,
            "context": context or {}
        }
        
        self.errors[component].append(error_record)
        
        # Keep only last 100 errors per component
        self.errors[component] = self.errors[component][-100:]
        
        # Log to file
        self._write_log(component, error_record)
        
        # Check if circuit breaker should open
        recent_errors = self._count_recent_errors(component, minutes=5)
        if recent_errors >= SurvivorConfig.ERROR_THRESHOLD:
            self.circuit_breakers[component] = True
            return {
                "recorded": True,
                "circuit_breaker": "OPEN",
                "recent_errors": recent_errors
            }
        
        return {
            "recorded": True,
            "circuit_breaker": "CLOSED",
            "recent_errors": recent_errors
        }
    
    def _count_recent_errors(self, component: str, minutes: int = 5) -> int:
        """Count errors in the last N minutes"""
        if component not in self.errors:
            return 0
            
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        
        return sum(
            1 for e in self.errors[component]
            if datetime.fromisoformat(e["timestamp"]) > cutoff
        )
    
    def _write_log(self, component: str, error_record: dict):
        """Write error to log file"""
        log_file = self.log_dir / f"{component}_{datetime.utcnow().strftime('%Y%m%d')}.log"
        
        try:
            with open(log_file, "a") as f:
                f.write(json.dumps(error_record) + "\n")
        except Exception:
            pass
    
    def is_circuit_open(self, component: str) -> bool:
        """Check if circuit breaker is open for a component"""
        return self.circuit_breakers.get(component, False)
    
    def reset_circuit(self, component: str):
        """Reset circuit breaker for a component"""
        self.circuit_breakers[component] = False
    
    def get_error_summary(self) -> dict:
        """Get summary of all errors"""
        summary = {}
        
        for component, errors in self.errors.items():
            recent_1h = self._count_recent_errors(component, minutes=60)
            recent_24h = sum(
                1 for e in errors
                if datetime.fromisoformat(e["timestamp"]) > datetime.utcnow() - timedelta(hours=24)
            )
            
            summary[component] = {
                "total": len(errors),
                "last_1h": recent_1h,
                "last_24h": recent_24h,
                "circuit_breaker": "OPEN" if self.is_circuit_open(component) else "CLOSED",
                "last_error": errors[-1] if errors else None
            }
        
        return summary


# ============================================================
# RETRY HANDLER
# ============================================================

class RetryHandler:
    """
    Handle retries with exponential backoff.
    """
    
    def __init__(self, error_tracker: ErrorTracker):
        self.error_tracker = error_tracker
        
    async def execute_with_retry(
        self,
        func: Callable,
        component: str,
        max_retries: int = None,
        *args,
        **kwargs
    ) -> dict:
        """
        Execute a function with retry logic.
        Returns result or error details.
        """
        max_retries = max_retries or SurvivorConfig.RETRY_ATTEMPTS
        
        # Check circuit breaker
        if self.error_tracker.is_circuit_open(component):
            return {
                "success": False,
                "error": "Circuit breaker is open",
                "retry_after": 300  # 5 minutes
            }
        
        last_error = None
        
        for attempt in range(max_retries):
            try:
                result = await func(*args, **kwargs)
                return {
                    "success": True,
                    "result": result,
                    "attempts": attempt + 1
                }
                
            except Exception as e:
                last_error = str(e)
                
                # Record error
                self.error_tracker.record_error(
                    component,
                    last_error,
                    {"attempt": attempt + 1, "args": str(args)}
                )
                
                # Exponential backoff
                if attempt < max_retries - 1:
                    delay = SurvivorConfig.RETRY_DELAY * (2 ** attempt)
                    await asyncio.sleep(delay)
        
        return {
            "success": False,
            "error": last_error,
            "attempts": max_retries
        }


# ============================================================
# HEALTH MONITOR
# ============================================================

class HealthMonitor:
    """
    Monitor the health of all system components.
    """
    
    def __init__(self):
        self.last_checks = {}
        self.health_status = {}
        
    async def check_api_health(self, name: str, url: str, headers: dict = None) -> dict:
        """Check if an API endpoint is healthy"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=headers,
                    timeout=10
                )
                
                healthy = response.status_code in [200, 201, 204]
                
                self.health_status[name] = {
                    "healthy": healthy,
                    "status_code": response.status_code,
                    "latency_ms": response.elapsed.total_seconds() * 1000,
                    "last_check": datetime.utcnow().isoformat()
                }
                
                return self.health_status[name]
                
        except Exception as e:
            self.health_status[name] = {
                "healthy": False,
                "error": str(e),
                "last_check": datetime.utcnow().isoformat()
            }
            return self.health_status[name]
    
    async def check_all_services(self) -> dict:
        """Check health of all critical services"""
        checks = {
            "n8n": "http://localhost:5678/healthz",
        }
        
        results = {}
        for name, url in checks.items():
            results[name] = await self.check_api_health(name, url)
        
        # Calculate overall health
        healthy_count = sum(1 for r in results.values() if r.get("healthy"))
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "services": results,
            "overall_health": f"{healthy_count}/{len(checks)}",
            "status": "healthy" if healthy_count == len(checks) else "degraded"
        }
    
    def get_health_history(self) -> dict:
        """Get health check history"""
        return self.health_status


# ============================================================
# ACCOUNT HEALTH MONITOR
# ============================================================

class AccountHealthMonitor:
    """
    Monitor the health of social media accounts.
    Detect shadowbans and performance issues.
    """
    
    def __init__(self):
        self.account_metrics = {}
        
    def record_metrics(
        self,
        platform: str,
        account_id: str,
        views: int,
        engagement: float
    ):
        """Record account performance metrics"""
        key = f"{platform}:{account_id}"
        
        if key not in self.account_metrics:
            self.account_metrics[key] = []
            
        self.account_metrics[key].append({
            "timestamp": datetime.utcnow().isoformat(),
            "views": views,
            "engagement": engagement
        })
        
        # Keep only last 100 data points
        self.account_metrics[key] = self.account_metrics[key][-100:]
    
    def check_shadowban(self, platform: str, account_id: str) -> dict:
        """Check if an account appears to be shadowbanned"""
        key = f"{platform}:{account_id}"
        metrics = self.account_metrics.get(key, [])
        
        if not metrics:
            return {"status": "unknown", "reason": "No metrics recorded"}
        
        threshold = SurvivorConfig.SHADOWBAN_THRESHOLD.get(platform, {})
        hours = threshold.get("hours", 24)
        
        # Get recent metrics
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        recent = [
            m for m in metrics
            if datetime.fromisoformat(m["timestamp"]) > cutoff
        ]
        
        if not recent:
            return {"status": "unknown", "reason": "No recent data"}
        
        avg_views = sum(m["views"] for m in recent) / len(recent)
        
        view_threshold = threshold.get("views", 10)
        
        if avg_views < view_threshold:
            return {
                "status": "suspected_shadowban",
                "avg_views": avg_views,
                "threshold": view_threshold,
                "recommendation": "Consider rotating to new account"
            }
        
        return {
            "status": "healthy",
            "avg_views": avg_views
        }


# ============================================================
# SELF-HEALING ENGINE
# ============================================================

class SelfHealingEngine:
    """
    Automated self-healing for common issues.
    """
    
    def __init__(self, error_tracker: ErrorTracker, alert_manager: AlertManager):
        self.error_tracker = error_tracker
        self.alert_manager = alert_manager
        self.healing_actions = []
        
    async def diagnose_and_heal(self, component: str, error: str) -> dict:
        """Diagnose an error and attempt to heal"""
        
        healing_strategies = {
            "rate_limit": self._heal_rate_limit,
            "auth_failed": self._heal_auth,
            "network_error": self._heal_network,
            "quota_exceeded": self._heal_quota
        }
        
        # Identify error type
        error_type = self._classify_error(error)
        
        # Get healing strategy
        strategy = healing_strategies.get(error_type, self._heal_generic)
        
        # Execute healing
        result = await strategy(component, error)
        
        # Log healing action
        self.healing_actions.append({
            "timestamp": datetime.utcnow().isoformat(),
            "component": component,
            "error_type": error_type,
            "action": result.get("action"),
            "success": result.get("success")
        })
        
        return result
    
    def _classify_error(self, error: str) -> str:
        """Classify error type from error message"""
        error_lower = error.lower()
        
        if "rate limit" in error_lower or "429" in error_lower:
            return "rate_limit"
        elif "auth" in error_lower or "401" in error_lower or "403" in error_lower:
            return "auth_failed"
        elif "network" in error_lower or "connection" in error_lower:
            return "network_error"
        elif "quota" in error_lower or "limit exceeded" in error_lower:
            return "quota_exceeded"
        else:
            return "unknown"
    
    async def _heal_rate_limit(self, component: str, error: str) -> dict:
        """Heal rate limit errors by waiting"""
        wait_time = 60 * 15  # 15 minutes
        
        await self.alert_manager.send_telegram(
            f"⏸️ Rate limit hit on {component}\nWaiting {wait_time}s before retry",
            "warning"
        )
        
        return {
            "success": True,
            "action": "wait",
            "wait_seconds": wait_time
        }
    
    async def _heal_auth(self, component: str, error: str) -> dict:
        """Heal auth errors"""
        await self.alert_manager.send_telegram(
            f"🔐 Auth failed on {component}\nManual token refresh may be needed",
            "critical"
        )
        
        return {
            "success": False,
            "action": "alert_sent",
            "requires_manual": True
        }
    
    async def _heal_network(self, component: str, error: str) -> dict:
        """Heal network errors by retrying"""
        return {
            "success": True,
            "action": "retry",
            "delay_seconds": 30
        }
    
    async def _heal_quota(self, component: str, error: str) -> dict:
        """Heal quota exceeded errors"""
        # Calculate time until quota reset (usually midnight UTC)
        now = datetime.utcnow()
        tomorrow = now.replace(hour=0, minute=0, second=0) + timedelta(days=1)
        wait_seconds = (tomorrow - now).total_seconds()
        
        await self.alert_manager.send_telegram(
            f"📊 Quota exceeded on {component}\nWill resume at midnight UTC",
            "warning"
        )
        
        return {
            "success": True,
            "action": "wait_for_reset",
            "wait_seconds": wait_seconds
        }
    
    async def _heal_generic(self, component: str, error: str) -> dict:
        """Generic healing strategy"""
        self.error_tracker.record_error(component, error, {"healing": "generic"})
        
        return {
            "success": False,
            "action": "logged",
            "requires_review": True
        }


# ============================================================
# MASTER SURVIVOR - ORCHESTRATOR
# ============================================================

class MasterSurvivor:
    """
    Master Survivor that orchestrates all resilience operations.
    The immune system of the Money Machine.
    """
    
    def __init__(self):
        self.alert_manager = AlertManager()
        self.error_tracker = ErrorTracker()
        self.retry_handler = RetryHandler(self.error_tracker)
        self.health_monitor = HealthMonitor()
        self.account_monitor = AccountHealthMonitor()
        self.healer = SelfHealingEngine(self.error_tracker, self.alert_manager)
        
    async def handle_error(self, component: str, error: str, context: dict = None) -> dict:
        """
        Central error handling for all engines.
        """
        # Record the error
        record_result = self.error_tracker.record_error(component, error, context)
        
        # Attempt self-healing
        healing_result = await self.healer.diagnose_and_heal(component, error)
        
        # Alert if circuit breaker opened
        if record_result.get("circuit_breaker") == "OPEN":
            await self.alert_manager.alert(
                f"🚨 Circuit breaker OPEN for {component}\n"
                f"Errors: {record_result['recent_errors']} in 5 min\n"
                f"Last error: {error[:100]}",
                "critical"
            )
        
        return {
            "error_recorded": record_result,
            "healing": healing_result
        }
    
    async def run_health_check(self) -> dict:
        """Run comprehensive health check"""
        health = await self.health_monitor.check_all_services()
        errors = self.error_tracker.get_error_summary()
        
        # Alert if unhealthy
        if health["status"] != "healthy":
            await self.alert_manager.alert(
                f"⚠️ System health degraded\n"
                f"Status: {health['overall_health']} services healthy",
                "warning"
            )
        
        return {
            "health": health,
            "errors": errors,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def get_system_status(self) -> dict:
        """Get complete system status"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "health": await self.health_monitor.check_all_services(),
            "errors": self.error_tracker.get_error_summary(),
            "circuit_breakers": self.error_tracker.circuit_breakers,
            "healing_actions": self.healer.healing_actions[-10:]  # Last 10 actions
        }
    
    async def daily_report(self) -> dict:
        """Generate daily status report"""
        status = await self.get_system_status()
        
        # Send daily report
        report = f"""
📊 *Daily Money Machine Report*

🏥 *Health:* {status['health']['status']}
🔌 *Services:* {status['health']['overall_health']}

📈 *Errors (24h):*
"""
        
        for component, data in status.get("errors", {}).items():
            report += f"  • {component}: {data.get('last_24h', 0)} errors\n"
        
        await self.alert_manager.alert(report, "info")
        
        return status


# ============================================================
# CLI INTERFACE
# ============================================================

if __name__ == "__main__":
    import sys
    
    async def main():
        survivor = MasterSurvivor()
        
        if len(sys.argv) > 1:
            command = sys.argv[1]
            
            if command == "health":
                result = await survivor.run_health_check()
            elif command == "status":
                result = await survivor.get_system_status()
            elif command == "report":
                result = await survivor.daily_report()
            elif command == "test-alert":
                result = await survivor.alert_manager.alert(
                    "🧪 Test alert from Money Machine",
                    "info"
                )
            else:
                result = {"error": "Usage: survivor.py [health|status|report|test-alert]"}
        else:
            result = await survivor.get_system_status()
        
        print(json.dumps(result, indent=2, default=str))
    
    asyncio.run(main())
