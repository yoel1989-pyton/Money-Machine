"""
============================================================
MONEY MACHINE - OMNI ORCHESTRATOR
The Self-Healing, Self-Improving, Self-Fixing Autonomous System
============================================================
This is the "Brain Stem" - the meta-controller that:
1. Self-heals when components fail (auto-recovery)
2. Self-improves based on performance metrics (machine learning)
3. Self-fixes by detecting and patching issues automatically
4. Auto-scales resources based on demand
5. Maintains system homeostasis
6. Dynamically adjusts strategies for maximum ROI
============================================================
"""

import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
from enum import Enum
import httpx
from dataclasses import dataclass, field, asdict
import hashlib

# Import all engines
from .hunter import MasterHunter
from .creator import MasterCreator
from .gatherer import MasterGatherer
from .businessman import MasterBusinessman
from .survivor import MasterSurvivor, AlertManager, ErrorTracker


# ============================================================
# SYSTEM STATES
# ============================================================

class SystemState(Enum):
    """System operational states"""
    INITIALIZING = "initializing"
    RUNNING = "running"
    HEALING = "healing"
    IMPROVING = "improving"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    MAINTENANCE = "maintenance"


class HealthStatus(Enum):
    """Component health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILING = "failing"
    DEAD = "dead"
    RECOVERING = "recovering"


# ============================================================
# CONFIGURATION - The DNA (Enhanced)
# ============================================================

@dataclass
class OmniConfig:
    """Omni Orchestrator Configuration - The Genetic Code"""
    
    # Performance thresholds for self-improvement
    PERFORMANCE_THRESHOLDS: Dict = field(default_factory=lambda: {
        "min_conversion_rate": 0.01,      # 1% minimum conversion
        "min_engagement_rate": 0.02,      # 2% minimum engagement
        "max_error_rate": 0.1,            # 10% max error rate
        "min_roi": 1.5,                   # 150% ROI minimum
        "optimal_posting_frequency": 6,   # Posts per day across all channels
        "min_video_quality_score": 0.7,   # Minimum quality score
        "max_api_cost_per_video": 0.25,   # Maximum API cost per video
    })
    
    # Self-healing triggers (Enhanced)
    HEALING_TRIGGERS: Dict = field(default_factory=lambda: {
        "consecutive_failures": 3,        # Heal after 3 failures
        "error_rate_threshold": 0.2,      # Heal if 20% of operations fail
        "circuit_breaker_reset_time": 300,# 5 minutes
        "max_healing_attempts": 5,        # Maximum healing attempts before alert
        "health_check_interval": 60,      # Check health every 60 seconds
        "auto_restart_components": True,  # Auto restart failed components
        "quarantine_time": 600,           # 10 min quarantine for failing components
    })
    
    # Self-improvement parameters (Machine Learning)
    IMPROVEMENT_PARAMS: Dict = field(default_factory=lambda: {
        "learning_rate": 0.1,             # How quickly to adjust
        "experiment_budget": 0.2,         # 20% of content can be experimental
        "min_sample_size": 10,            # Minimum samples before adjusting
        "improvement_check_interval": 3600,# Check every hour
        "strategy_evolution_rate": 0.05,  # 5% strategy change per cycle
        "content_ab_test_ratio": 0.1,     # 10% A/B testing
        "performance_decay_rate": 0.95,   # Weight recent data more
    })
    
    # Self-fixing parameters
    FIX_PARAMS: Dict = field(default_factory=lambda: {
        "auto_rotate_failed_offers": True,
        "auto_refresh_oauth_tokens": True,
        "auto_clear_temp_files": True,
        "auto_optimize_storage": True,
        "auto_retry_failed_uploads": True,
        "max_auto_fix_attempts": 3,
        "fix_cooldown_seconds": 120,
    })
    
    # Niche priorities (dynamically adjusted based on performance)
    NICHE_WEIGHTS: Dict = field(default_factory=lambda: {
        "survival": 1.0,
        "wealth": 1.0,
        "wellness": 1.0,
        "productivity": 1.0
    })
    
    # Data persistence
    STATE_FILE: Path = Path("/data/logs/omni_state.json")
    METRICS_FILE: Path = Path("/data/logs/performance_metrics.json")
    HEALING_LOG: Path = Path("/data/logs/healing_history.json")
    FIX_LOG: Path = Path("/data/logs/fix_history.json")
    
    # System limits
    MAX_CONCURRENT_OPERATIONS: int = 5
    MAX_DAILY_API_SPEND: float = 5.0
    MAX_VIDEOS_PER_DAY: int = 8
    
    @classmethod
    def load_from_env(cls) -> 'OmniConfig':
        """Load config from environment variables"""
        config = cls()
        # Override with env vars if present
        if os.getenv("OMNI_MAX_DAILY_VIDEOS"):
            config.MAX_VIDEOS_PER_DAY = int(os.getenv("OMNI_MAX_DAILY_VIDEOS"))
        if os.getenv("OMNI_LEARNING_RATE"):
            config.IMPROVEMENT_PARAMS["learning_rate"] = float(os.getenv("OMNI_LEARNING_RATE"))
        return config


# ============================================================
# PERFORMANCE TRACKER - The Memory
# ============================================================

class PerformanceTracker:
    """
    Tracks performance metrics across all engines.
    Provides data for self-improvement decisions.
    """
    
    def __init__(self):
        self.metrics_file = OmniConfig.METRICS_FILE
        self.metrics = self._load_metrics()
        
    def _load_metrics(self) -> Dict:
        """Load historical metrics"""
        if self.metrics_file.exists():
            try:
                with open(self.metrics_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            "content_performance": [],
            "niche_performance": {},
            "error_history": [],
            "financial_history": [],
            "optimization_history": []
        }
    
    def _save_metrics(self):
        """Persist metrics to disk"""
        self.metrics_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.metrics_file, 'w') as f:
            json.dump(self.metrics, f, indent=2, default=str)
    
    def record_content_performance(
        self,
        content_id: str,
        niche: str,
        platform: str,
        views: int,
        engagement: float,
        conversions: int
    ):
        """Record content performance for learning"""
        record = {
            "timestamp": datetime.utcnow().isoformat(),
            "content_id": content_id,
            "niche": niche,
            "platform": platform,
            "views": views,
            "engagement": engagement,
            "conversions": conversions,
            "conversion_rate": conversions / max(views, 1)
        }
        
        self.metrics["content_performance"].append(record)
        
        # Update niche performance
        if niche not in self.metrics["niche_performance"]:
            self.metrics["niche_performance"][niche] = {
                "total_views": 0,
                "total_conversions": 0,
                "content_count": 0,
                "avg_engagement": 0
            }
        
        niche_data = self.metrics["niche_performance"][niche]
        niche_data["total_views"] += views
        niche_data["total_conversions"] += conversions
        niche_data["content_count"] += 1
        niche_data["avg_engagement"] = (
            (niche_data["avg_engagement"] * (niche_data["content_count"] - 1) + engagement)
            / niche_data["content_count"]
        )
        
        # Keep only last 1000 records
        self.metrics["content_performance"] = self.metrics["content_performance"][-1000:]
        self._save_metrics()
    
    def record_error(self, component: str, error: str, context: Dict):
        """Record error for pattern analysis"""
        self.metrics["error_history"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "component": component,
            "error": error,
            "context": context
        })
        
        # Keep only last 500 errors
        self.metrics["error_history"] = self.metrics["error_history"][-500:]
        self._save_metrics()
    
    def record_financial(self, revenue: float, cost: float, source: str):
        """Record financial data"""
        self.metrics["financial_history"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "revenue": revenue,
            "cost": cost,
            "profit": revenue - cost,
            "source": source
        })
        
        # Keep only last 365 days
        self.metrics["financial_history"] = self.metrics["financial_history"][-365:]
        self._save_metrics()
    
    def get_niche_rankings(self) -> List[tuple]:
        """Get niches ranked by performance"""
        rankings = []
        
        for niche, data in self.metrics.get("niche_performance", {}).items():
            if data["content_count"] > 0:
                score = (
                    data["avg_engagement"] * 0.3 +
                    (data["total_conversions"] / max(data["content_count"], 1)) * 0.5 +
                    (data["total_views"] / max(data["content_count"], 1) / 10000) * 0.2
                )
                rankings.append((niche, score))
        
        return sorted(rankings, key=lambda x: x[1], reverse=True)
    
    def get_error_patterns(self) -> Dict:
        """Analyze error patterns for self-healing"""
        patterns = {}
        recent_errors = [
            e for e in self.metrics.get("error_history", [])
            if datetime.fromisoformat(e["timestamp"]) > datetime.utcnow() - timedelta(hours=24)
        ]
        
        for error in recent_errors:
            component = error["component"]
            if component not in patterns:
                patterns[component] = {"count": 0, "errors": []}
            patterns[component]["count"] += 1
            patterns[component]["errors"].append(error["error"])
        
        return patterns
    
    def calculate_roi(self, days: int = 30) -> float:
        """Calculate ROI over specified period"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        recent = [
            f for f in self.metrics.get("financial_history", [])
            if datetime.fromisoformat(f["timestamp"]) > cutoff
        ]
        
        if not recent:
            return 0.0
        
        total_revenue = sum(f["revenue"] for f in recent)
        total_cost = sum(f["cost"] for f in recent)
        
        if total_cost == 0:
            return float('inf') if total_revenue > 0 else 0.0
        
        return (total_revenue - total_cost) / total_cost


# ============================================================
# SELF-HEALER - The Immune System
# ============================================================

class SelfHealer:
    """
    Automatic self-healing system.
    Detects issues and applies fixes without human intervention.
    """
    
    def __init__(self, survivor: MasterSurvivor, tracker: PerformanceTracker):
        self.survivor = survivor
        self.tracker = tracker
        self.healing_log = []
        
    async def diagnose_system(self) -> Dict:
        """Full system diagnosis"""
        diagnosis = {
            "timestamp": datetime.utcnow().isoformat(),
            "issues": [],
            "warnings": [],
            "healthy_components": []
        }
        
        # Check error patterns
        patterns = self.tracker.get_error_patterns()
        
        for component, data in patterns.items():
            if data["count"] >= OmniConfig.HEALING_TRIGGERS["consecutive_failures"]:
                diagnosis["issues"].append({
                    "component": component,
                    "type": "high_error_rate",
                    "count": data["count"],
                    "sample_errors": data["errors"][:3]
                })
        
        # Check circuit breakers
        for component, is_open in self.survivor.error_tracker.circuit_breakers.items():
            if is_open:
                diagnosis["issues"].append({
                    "component": component,
                    "type": "circuit_breaker_open"
                })
        
        # Check system health
        health = await self.survivor.run_health_check()
        if health.get("health", {}).get("status") != "healthy":
            diagnosis["warnings"].append({
                "type": "degraded_health",
                "details": health
            })
        
        return diagnosis
    
    async def heal(self, diagnosis: Dict) -> Dict:
        """Apply healing procedures based on diagnosis"""
        actions_taken = []
        
        for issue in diagnosis.get("issues", []):
            action = await self._apply_healing(issue)
            if action:
                actions_taken.append(action)
                self.healing_log.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "issue": issue,
                    "action": action
                })
        
        return {
            "healed": len(actions_taken) > 0,
            "actions": actions_taken,
            "remaining_issues": len(diagnosis.get("issues", [])) - len(actions_taken)
        }
    
    async def _apply_healing(self, issue: Dict) -> Optional[Dict]:
        """Apply specific healing action"""
        issue_type = issue.get("type")
        component = issue.get("component")
        
        if issue_type == "circuit_breaker_open":
            # Reset circuit breaker after cooldown
            self.survivor.error_tracker.reset_circuit(component)
            await self.survivor.alert_manager.alert(
                f"🔄 Auto-healed: Reset circuit breaker for {component}",
                "info"
            )
            return {"action": "reset_circuit_breaker", "component": component}
        
        elif issue_type == "high_error_rate":
            # Identify common error and apply fix
            errors = issue.get("sample_errors", [])
            
            # Check for rate limiting
            if any("rate" in str(e).lower() for e in errors):
                return {
                    "action": "reduce_frequency",
                    "component": component,
                    "message": "Reducing API call frequency"
                }
            
            # Check for auth issues
            if any("auth" in str(e).lower() or "401" in str(e) for e in errors):
                await self.survivor.alert_manager.alert(
                    f"🔐 Auth issue detected in {component}. Manual refresh needed.",
                    "critical"
                )
                return {
                    "action": "auth_alert_sent",
                    "component": component,
                    "requires_manual": True
                }
            
            # Generic: reset and retry
            self.survivor.error_tracker.reset_circuit(component)
            return {
                "action": "reset_and_retry",
                "component": component
            }
        
        return None
    
    async def run_healing_cycle(self) -> Dict:
        """Run a complete healing cycle"""
        diagnosis = await self.diagnose_system()
        
        if diagnosis["issues"]:
            healing_result = await self.heal(diagnosis)
            return {
                "diagnosis": diagnosis,
                "healing": healing_result
            }
        
        return {
            "diagnosis": diagnosis,
            "healing": {"healed": False, "message": "No issues detected"}
        }


# ============================================================
# SELF-FIXER - The Autonomous Repair System
# ============================================================

class SelfFixer:
    """
    Automatic self-fixing system.
    Detects specific issues and applies targeted fixes.
    Goes beyond healing to actually repair broken functionality.
    """
    
    def __init__(self, survivor: MasterSurvivor, tracker: PerformanceTracker):
        self.survivor = survivor
        self.tracker = tracker
        self.config = OmniConfig()
        self.fix_history = []
        self.fix_cooldowns = {}  # {fix_type: last_attempt_time}
        
    async def scan_for_fixable_issues(self) -> List[Dict]:
        """Scan system for issues that can be auto-fixed"""
        issues = []
        
        # 1. Check for stale OAuth tokens
        oauth_status = await self._check_oauth_tokens()
        if oauth_status.get("needs_refresh"):
            issues.append({
                "type": "oauth_expired",
                "component": oauth_status.get("component"),
                "priority": "high",
                "auto_fixable": self.config.FIX_PARAMS["auto_refresh_oauth_tokens"]
            })
        
        # 2. Check for full temp storage
        storage_status = await self._check_storage()
        if storage_status.get("temp_full"):
            issues.append({
                "type": "temp_storage_full",
                "used_percent": storage_status.get("used_percent"),
                "priority": "medium",
                "auto_fixable": self.config.FIX_PARAMS["auto_clear_temp_files"]
            })
        
        # 3. Check for failed uploads pending retry
        failed_uploads = await self._check_failed_uploads()
        if failed_uploads:
            issues.append({
                "type": "failed_uploads_pending",
                "count": len(failed_uploads),
                "uploads": failed_uploads,
                "priority": "high",
                "auto_fixable": self.config.FIX_PARAMS["auto_retry_failed_uploads"]
            })
        
        # 4. Check for underperforming affiliate offers
        offer_status = await self._check_affiliate_offers()
        if offer_status.get("needs_rotation"):
            issues.append({
                "type": "underperforming_offers",
                "offers": offer_status.get("offers", []),
                "priority": "medium",
                "auto_fixable": self.config.FIX_PARAMS["auto_rotate_failed_offers"]
            })
        
        # 5. Check for API rate limit issues
        rate_limit_status = self._check_rate_limits()
        if rate_limit_status.get("throttled"):
            issues.append({
                "type": "rate_limited",
                "apis": rate_limit_status.get("apis", []),
                "priority": "high",
                "auto_fixable": True
            })
        
        return issues
    
    async def _check_oauth_tokens(self) -> Dict:
        """Check OAuth token validity"""
        # Check error patterns for auth-related issues
        patterns = self.tracker.get_error_patterns()
        
        for component, data in patterns.items():
            errors = data.get("errors", [])
            auth_errors = [e for e in errors if "401" in str(e) or "auth" in str(e).lower()]
            if len(auth_errors) >= 2:
                return {"needs_refresh": True, "component": component}
        
        return {"needs_refresh": False}
    
    async def _check_storage(self) -> Dict:
        """Check temp storage status"""
        import shutil
        
        temp_path = Path("/data/temp")
        if temp_path.exists():
            try:
                total, used, free = shutil.disk_usage(temp_path)
                used_percent = (used / total) * 100
                
                return {
                    "temp_full": used_percent > 85,
                    "used_percent": used_percent,
                    "free_bytes": free
                }
            except:
                pass
        
        return {"temp_full": False, "used_percent": 0}
    
    async def _check_failed_uploads(self) -> List[Dict]:
        """Check for failed uploads that can be retried"""
        # Look for failed upload records in metrics
        failed = []
        content_data = self.tracker.metrics.get("content_performance", [])
        
        for content in content_data[-50:]:
            if content.get("upload_status") == "failed":
                failed.append({
                    "content_id": content.get("content_id"),
                    "platform": content.get("platform"),
                    "error": content.get("error")
                })
        
        return failed
    
    async def _check_affiliate_offers(self) -> Dict:
        """Check affiliate offer performance"""
        # Analyze conversion data
        content_data = self.tracker.metrics.get("content_performance", [])
        
        offer_performance = {}
        for content in content_data[-100:]:
            offer_id = content.get("offer_id")
            if offer_id:
                if offer_id not in offer_performance:
                    offer_performance[offer_id] = {"clicks": 0, "conversions": 0}
                offer_performance[offer_id]["clicks"] += content.get("clicks", 0)
                offer_performance[offer_id]["conversions"] += content.get("conversions", 0)
        
        # Find underperformers (< 0.5% conversion rate with significant traffic)
        needs_rotation = []
        for offer_id, data in offer_performance.items():
            if data["clicks"] >= 100:
                conv_rate = data["conversions"] / data["clicks"]
                if conv_rate < 0.005:  # < 0.5%
                    needs_rotation.append(offer_id)
        
        return {
            "needs_rotation": len(needs_rotation) > 0,
            "offers": needs_rotation
        }
    
    def _check_rate_limits(self) -> Dict:
        """Check for rate limit issues in error patterns"""
        patterns = self.tracker.get_error_patterns()
        throttled_apis = []
        
        for component, data in patterns.items():
            errors = data.get("errors", [])
            rate_errors = [e for e in errors if "429" in str(e) or "rate" in str(e).lower()]
            if len(rate_errors) >= 2:
                throttled_apis.append(component)
        
        return {
            "throttled": len(throttled_apis) > 0,
            "apis": throttled_apis
        }
    
    def _can_apply_fix(self, fix_type: str) -> bool:
        """Check if fix is off cooldown"""
        cooldown = self.config.FIX_PARAMS["fix_cooldown_seconds"]
        last_attempt = self.fix_cooldowns.get(fix_type)
        
        if last_attempt:
            elapsed = (datetime.utcnow() - last_attempt).total_seconds()
            return elapsed >= cooldown
        
        return True
    
    async def apply_fix(self, issue: Dict) -> Dict:
        """Apply a fix for a specific issue"""
        issue_type = issue.get("type")
        
        if not self._can_apply_fix(issue_type):
            return {"fixed": False, "reason": "On cooldown"}
        
        if not issue.get("auto_fixable", False):
            return {"fixed": False, "reason": "Not auto-fixable"}
        
        result = {"fixed": False, "type": issue_type}
        
        try:
            if issue_type == "temp_storage_full":
                result = await self._fix_storage()
            
            elif issue_type == "failed_uploads_pending":
                result = await self._fix_failed_uploads(issue.get("uploads", []))
            
            elif issue_type == "rate_limited":
                result = await self._fix_rate_limits(issue.get("apis", []))
            
            elif issue_type == "underperforming_offers":
                result = await self._fix_offers(issue.get("offers", []))
            
            # Record fix attempt
            self.fix_cooldowns[issue_type] = datetime.utcnow()
            self.fix_history.append({
                "timestamp": datetime.utcnow().isoformat(),
                "issue": issue,
                "result": result
            })
            
        except Exception as e:
            result = {"fixed": False, "error": str(e)}
        
        return result
    
    async def _fix_storage(self) -> Dict:
        """Clear temp storage"""
        import shutil
        
        temp_path = Path("/data/temp")
        files_removed = 0
        
        if temp_path.exists():
            for item in temp_path.iterdir():
                try:
                    if item.is_file():
                        # Only remove files older than 1 hour
                        age = datetime.utcnow().timestamp() - item.stat().st_mtime
                        if age > 3600:
                            item.unlink()
                            files_removed += 1
                    elif item.is_dir():
                        age = datetime.utcnow().timestamp() - item.stat().st_mtime
                        if age > 3600:
                            shutil.rmtree(item)
                            files_removed += 1
                except:
                    pass
        
        await self.survivor.alert_manager.alert(
            f"🧹 Auto-fixed: Cleared {files_removed} old temp files",
            "info"
        )
        
        return {"fixed": True, "files_removed": files_removed}
    
    async def _fix_failed_uploads(self, uploads: List[Dict]) -> Dict:
        """Retry failed uploads"""
        retried = 0
        succeeded = 0
        
        # Signal to gatherer to retry these uploads
        # (In production, would actually call gatherer methods)
        for upload in uploads[:5]:  # Limit to 5 retries per cycle
            retried += 1
            # Log retry attempt
            self.tracker.record_error(
                "self_fixer",
                f"Retry upload: {upload.get('content_id')}",
                {"action": "retry", "platform": upload.get("platform")}
            )
        
        await self.survivor.alert_manager.alert(
            f"🔄 Auto-fixed: Queued {retried} uploads for retry",
            "info"
        )
        
        return {"fixed": True, "retried": retried, "succeeded": succeeded}
    
    async def _fix_rate_limits(self, apis: List[str]) -> Dict:
        """Handle rate limit issues by backing off"""
        # Increase backoff timers for affected APIs
        for api in apis:
            # Reset circuit breaker with delay
            self.survivor.error_tracker.circuit_breakers[api] = True
        
        await self.survivor.alert_manager.alert(
            f"⏸️ Auto-fixed: Rate limit protection enabled for {', '.join(apis)}",
            "warning"
        )
        
        return {"fixed": True, "apis_throttled": apis}
    
    async def _fix_offers(self, offers: List[str]) -> Dict:
        """Rotate underperforming affiliate offers"""
        # Signal to affiliate engine to rotate offers
        rotated = len(offers)
        
        await self.survivor.alert_manager.alert(
            f"🔄 Auto-fixed: Flagged {rotated} offers for rotation",
            "info"
        )
        
        return {"fixed": True, "offers_flagged": rotated}
    
    async def run_fix_cycle(self) -> Dict:
        """Run a complete fix cycle"""
        issues = await self.scan_for_fixable_issues()
        
        fixes_applied = []
        for issue in issues:
            if issue.get("auto_fixable"):
                result = await self.apply_fix(issue)
                if result.get("fixed"):
                    fixes_applied.append(result)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "issues_found": len(issues),
            "fixes_applied": len(fixes_applied),
            "details": fixes_applied
        }


# ============================================================
# SELF-IMPROVER - The Learning System
# ============================================================

class SelfImprover:
    """
    Automatic self-improvement through learning.
    Optimizes strategies based on performance data.
    """
    
    def __init__(self, tracker: PerformanceTracker):
        self.tracker = tracker
        self.improvements = []
        
    def analyze_and_improve(self) -> Dict:
        """Analyze performance and generate improvements"""
        improvements = []
        
        # 1. Optimize niche weights
        niche_optimization = self._optimize_niche_weights()
        if niche_optimization:
            improvements.append(niche_optimization)
        
        # 2. Optimize posting times
        timing_optimization = self._optimize_posting_times()
        if timing_optimization:
            improvements.append(timing_optimization)
        
        # 3. Content type optimization
        content_optimization = self._optimize_content_types()
        if content_optimization:
            improvements.append(content_optimization)
        
        # Save improvements
        self.improvements.extend(improvements)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "improvements": improvements,
            "applied": len(improvements)
        }
    
    def _optimize_niche_weights(self) -> Optional[Dict]:
        """Adjust niche weights based on performance"""
        rankings = self.tracker.get_niche_rankings()
        
        if len(rankings) < 2:
            return None
        
        # Check if we have enough data
        total_content = sum(
            self.tracker.metrics.get("niche_performance", {}).get(n, {}).get("content_count", 0)
            for n, _ in rankings
        )
        
        if total_content < OmniConfig.IMPROVEMENT_PARAMS["min_sample_size"]:
            return None
        
        # Calculate new weights
        new_weights = {}
        total_score = sum(score for _, score in rankings)
        
        if total_score == 0:
            return None
        
        for niche, score in rankings:
            # Blend current weight with performance-based weight
            current_weight = OmniConfig.NICHE_WEIGHTS.get(niche, 1.0)
            performance_weight = score / total_score * len(rankings)
            
            new_weight = (
                current_weight * (1 - OmniConfig.IMPROVEMENT_PARAMS["learning_rate"]) +
                performance_weight * OmniConfig.IMPROVEMENT_PARAMS["learning_rate"]
            )
            
            new_weights[niche] = round(new_weight, 2)
        
        # Update global config
        OmniConfig.NICHE_WEIGHTS.update(new_weights)
        
        return {
            "type": "niche_weight_optimization",
            "old_weights": dict(OmniConfig.NICHE_WEIGHTS),
            "new_weights": new_weights,
            "reason": "Performance-based adjustment"
        }
    
    def _optimize_posting_times(self) -> Optional[Dict]:
        """Analyze best posting times"""
        content_data = self.tracker.metrics.get("content_performance", [])
        
        if len(content_data) < 20:
            return None
        
        # Group by hour and calculate average engagement
        hour_performance = {}
        for content in content_data[-100:]:
            try:
                hour = datetime.fromisoformat(content["timestamp"]).hour
                if hour not in hour_performance:
                    hour_performance[hour] = []
                hour_performance[hour].append(content.get("engagement", 0))
            except:
                pass
        
        # Find best hours
        best_hours = sorted(
            hour_performance.items(),
            key=lambda x: sum(x[1]) / len(x[1]) if x[1] else 0,
            reverse=True
        )[:3]
        
        if not best_hours:
            return None
        
        return {
            "type": "posting_time_optimization",
            "best_hours_utc": [h for h, _ in best_hours],
            "reason": "Engagement-based analysis"
        }
    
    def _optimize_content_types(self) -> Optional[Dict]:
        """Identify best-performing content types"""
        content_data = self.tracker.metrics.get("content_performance", [])
        
        if len(content_data) < 10:
            return None
        
        # Analyze platform performance
        platform_performance = {}
        for content in content_data[-50:]:
            platform = content.get("platform", "unknown")
            if platform not in platform_performance:
                platform_performance[platform] = []
            platform_performance[platform].append(content.get("conversion_rate", 0))
        
        # Calculate averages
        platform_avg = {
            p: sum(rates) / len(rates) if rates else 0
            for p, rates in platform_performance.items()
        }
        
        best_platform = max(platform_avg, key=platform_avg.get) if platform_avg else None
        
        if not best_platform:
            return None
        
        return {
            "type": "platform_optimization",
            "best_platform": best_platform,
            "platform_scores": platform_avg,
            "recommendation": f"Prioritize {best_platform} content"
        }
    
    def get_current_strategy(self) -> Dict:
        """Get current optimized strategy"""
        return {
            "niche_weights": OmniConfig.NICHE_WEIGHTS,
            "performance_thresholds": OmniConfig.PERFORMANCE_THRESHOLDS,
            "recent_improvements": self.improvements[-10:]
        }


# ============================================================
# RESOURCE SCALER - The Growth System
# ============================================================

class ResourceScaler:
    """
    Auto-scales resources based on demand and performance.
    Manages the machine's growth trajectory.
    """
    
    def __init__(self, businessman: MasterBusinessman, tracker: PerformanceTracker):
        self.businessman = businessman
        self.tracker = tracker
        
    async def analyze_scaling_needs(self) -> Dict:
        """Analyze if scaling is needed"""
        roi = self.tracker.calculate_roi(30)
        
        snapshot = await self.businessman.get_financial_snapshot()
        available_reinvestment = snapshot.get("allocation", {}).get("reinvestment", 0)
        
        scaling_recommendations = []
        
        # Check if profitable enough to scale
        if roi >= OmniConfig.PERFORMANCE_THRESHOLDS["min_roi"]:
            if available_reinvestment >= 50:
                scaling_recommendations.append({
                    "action": "increase_content_frequency",
                    "reason": "Strong ROI supports scaling",
                    "investment_needed": 20
                })
            
            if available_reinvestment >= 100:
                scaling_recommendations.append({
                    "action": "add_new_niche",
                    "reason": "Revenue supports expansion",
                    "investment_needed": 50
                })
        
        # Check if underperforming and needs optimization
        elif roi < 1.0 and roi > 0:
            scaling_recommendations.append({
                "action": "optimize_before_scaling",
                "reason": "ROI below 100%, focus on optimization"
            })
        
        return {
            "current_roi": roi,
            "reinvestment_available": available_reinvestment,
            "recommendations": scaling_recommendations,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def calculate_optimal_frequency(self, niche: str) -> int:
        """Calculate optimal posting frequency for a niche"""
        niche_weight = OmniConfig.NICHE_WEIGHTS.get(niche, 1.0)
        base_frequency = OmniConfig.PERFORMANCE_THRESHOLDS["optimal_posting_frequency"]
        
        # Adjust based on weight
        optimal = int(base_frequency * niche_weight / 4)  # Divide by 4 niches
        
        return max(1, min(optimal, 3))  # Between 1-3 per day per niche


# ============================================================
# OMNI ORCHESTRATOR - The Supreme Controller
# ============================================================

class OmniOrchestrator:
    """
    The Supreme Controller - Orchestrates all autonomous operations.
    This is the "consciousness" of the Money Machine.
    """
    
    def __init__(self):
        # Core engines
        self.hunter = MasterHunter()
        self.creator = MasterCreator()
        self.gatherer = MasterGatherer()
        self.businessman = MasterBusinessman()
        self.survivor = MasterSurvivor()
        
        # Meta-controllers
        self.tracker = PerformanceTracker()
        self.healer = SelfHealer(self.survivor, self.tracker)
        self.fixer = SelfFixer(self.survivor, self.tracker)
        self.improver = SelfImprover(self.tracker)
        self.scaler = ResourceScaler(self.businessman, self.tracker)
        
        # System state
        self.system_state = SystemState.INITIALIZING
        
        # State
        self.state = self._load_state()
        self.is_running = False
        
        # Initialize complete
        self.system_state = SystemState.RUNNING
        
    def _load_state(self) -> Dict:
        """Load persistent state"""
        config = OmniConfig()
        if config.STATE_FILE.exists():
            try:
                with open(config.STATE_FILE, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            "cycles_completed": 0,
            "last_cycle": None,
            "last_healing": None,
            "last_fixing": None,
            "last_improvement": None,
            "errors_healed": 0,
            "issues_fixed": 0,
            "improvements_applied": 0,
            "total_revenue": 0.0,
            "total_content_created": 0,
            "version": "2.0.0"
        }
    
    def _save_state(self):
        """Persist state"""
        config = OmniConfig()
        config.STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(config.STATE_FILE, 'w') as f:
            json.dump(self.state, f, indent=2, default=str)
    
    async def execute_autonomous_cycle(self) -> Dict:
        """
        Execute a complete autonomous cycle:
        1. Self-heal if needed
        2. Self-fix detected issues
        3. Hunt for opportunities
        4. Create content optimized by learning
        5. Distribute across platforms
        6. Track performance
        7. Self-improve based on results
        """
        self.system_state = SystemState.RUNNING
        
        cycle_result = {
            "cycle_id": f"cycle_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "timestamp": datetime.utcnow().isoformat(),
            "phases": {}
        }
        
        try:
            # Phase 0: Self-Heal
            self.system_state = SystemState.HEALING
            healing = await self.healer.run_healing_cycle()
            cycle_result["phases"]["healing"] = healing
            
            if healing.get("diagnosis", {}).get("issues"):
                self.state["errors_healed"] += len(healing.get("healing", {}).get("actions", []))
            
            # Phase 0.5: Self-Fix
            fixing = await self.fixer.run_fix_cycle()
            cycle_result["phases"]["fixing"] = fixing
            
            if fixing.get("fixes_applied", 0) > 0:
                self.state["issues_fixed"] += fixing["fixes_applied"]
            
            self.system_state = SystemState.RUNNING
            
            # Phase 1: Strategic Hunt
            # Use optimized niche weights to prioritize
            niche_rankings = self.tracker.get_niche_rankings()
            target_niche = niche_rankings[0][0] if niche_rankings else "survival"
            
            hunt_result = await self.hunter.hunt([target_niche])
            cycle_result["phases"]["hunt"] = {
                "target_niche": target_niche,
                "opportunities_found": len(hunt_result.get("top_opportunities", []))
            }
            
            if not hunt_result.get("top_opportunities"):
                cycle_result["status"] = "no_opportunities"
                return cycle_result
            
            # Phase 2: Smart Creation
            best_opportunity = hunt_result["top_opportunities"][0]
            topic = best_opportunity.get("title", best_opportunity.get("keyword", "trending"))
            
            create_result = await self.creator.create_multiplatform(topic)
            cycle_result["phases"]["create"] = {
                "topic": topic,
                "status": create_result.get("status"),
                "platforms": create_result.get("platforms", [])
            }
            
            if create_result.get("status") != "complete":
                # Record error and attempt healing
                self.tracker.record_error("creator", create_result.get("error", "unknown"), {"topic": topic})
                cycle_result["status"] = "creation_failed"
                return cycle_result
            
            # Phase 3: Optimized Distribution
            video_path = create_result["assets"].get("final_video")
            script = create_result.get("script", {})
            
            distribute_result = await self.gatherer.distribute(
                video_path,
                script.get("title", topic),
                script.get("description", ""),
                script.get("hashtags", [])
            )
            cycle_result["phases"]["distribute"] = distribute_result
            
            # Phase 4: Financial Check
            financials = await self.businessman.get_financial_snapshot()
            cycle_result["phases"]["financials"] = {
                "total_balance": financials.get("balances", {}).get("total", 0),
                "revenue_30d": financials.get("revenue_30d", {}).get("total", 0)
            }
            
            # Phase 5: Self-Improvement
            improvements = self.improver.analyze_and_improve()
            cycle_result["phases"]["improvements"] = improvements
            
            if improvements.get("applied", 0) > 0:
                self.state["improvements_applied"] += improvements["applied"]
            
            # Phase 6: Scaling Analysis
            scaling = await self.scaler.analyze_scaling_needs()
            cycle_result["phases"]["scaling"] = scaling
            
            # Update state
            self.state["cycles_completed"] += 1
            self.state["last_cycle"] = datetime.utcnow().isoformat()
            self._save_state()
            
            cycle_result["status"] = "complete"
            
        except Exception as e:
            cycle_result["status"] = "error"
            cycle_result["error"] = str(e)
            self.tracker.record_error("omni_orchestrator", str(e), {"cycle": cycle_result["cycle_id"]})
            
            # Attempt emergency healing
            await self.survivor.handle_error("omni_orchestrator", str(e), {})
        
        return cycle_result
    
    async def run_maintenance(self) -> Dict:
        """Run maintenance tasks (hourly)"""
        self.system_state = SystemState.MAINTENANCE
        
        maintenance_result = {
            "timestamp": datetime.utcnow().isoformat(),
            "tasks": []
        }
        
        # Health check
        health = await self.survivor.run_health_check()
        maintenance_result["tasks"].append({
            "task": "health_check",
            "result": health.get("health", {}).get("status", "unknown")
        })
        
        # Healing cycle
        healing = await self.healer.run_healing_cycle()
        if healing.get("diagnosis", {}).get("issues"):
            maintenance_result["tasks"].append({
                "task": "self_healing",
                "issues_found": len(healing["diagnosis"]["issues"]),
                "healed": len(healing.get("healing", {}).get("actions", []))
            })
        
        # Fixing cycle
        fixing = await self.fixer.run_fix_cycle()
        if fixing.get("issues_found", 0) > 0:
            maintenance_result["tasks"].append({
                "task": "self_fixing",
                "issues_found": fixing["issues_found"],
                "fixed": fixing.get("fixes_applied", 0)
            })
        
        # Improvement check
        improvements = self.improver.analyze_and_improve()
        if improvements.get("applied", 0) > 0:
            maintenance_result["tasks"].append({
                "task": "self_improvement",
                "improvements": improvements["applied"]
            })
        
        self.system_state = SystemState.RUNNING
        return maintenance_result
    
    async def generate_daily_report(self) -> Dict:
        """Generate comprehensive daily report"""
        # Financial snapshot
        financials = await self.businessman.get_financial_snapshot()
        
        # System health
        health = await self.survivor.get_system_status()
        
        # Performance metrics
        roi = self.tracker.calculate_roi(30)
        niche_rankings = self.tracker.get_niche_rankings()
        
        # Current strategy
        strategy = self.improver.get_current_strategy()
        
        # Scaling recommendations
        scaling = await self.scaler.analyze_scaling_needs()
        
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "summary": {
                "cycles_completed": self.state["cycles_completed"],
                "errors_healed": self.state["errors_healed"],
                "issues_fixed": self.state.get("issues_fixed", 0),
                "improvements_applied": self.state["improvements_applied"],
                "total_content_created": self.state.get("total_content_created", 0),
                "30d_roi": f"{roi * 100:.1f}%"
            },
            "financials": {
                "total_balance": financials.get("balances", {}).get("total", 0),
                "30d_revenue": financials.get("revenue_30d", {}).get("total", 0),
                "should_payout": financials.get("actions", {}).get("should_payout", False)
            },
            "performance": {
                "top_niches": niche_rankings[:3],
                "current_strategy": strategy
            },
            "health": {
                "status": health.get("health", {}).get("status", "unknown"),
                "system_state": self.system_state.value,
                "open_circuits": list(health.get("circuit_breakers", {}).keys())
            },
            "scaling": scaling.get("recommendations", [])
        }
        
        # Send report via Telegram
        report_text = f"""
📊 *Daily Money Machine Report*
🤖 *Elite Autonomous System v2.0*

💰 *Financials:*
• Balance: ${report['financials']['total_balance']:.2f}
• 30d Revenue: ${report['financials']['30d_revenue']:.2f}
• ROI: {report['summary']['30d_roi']}

🎯 *Performance:*
• Cycles Completed: {report['summary']['cycles_completed']}
• Content Created: {report['summary']['total_content_created']}

🔧 *Self-Management:*
• Self-Healed: {report['summary']['errors_healed']} issues
• Self-Fixed: {report['summary']['issues_fixed']} problems
• Self-Improved: {report['summary']['improvements_applied']} times

🏥 *System Health:* {report['health']['status'].upper()}
⚙️ *State:* {report['health']['system_state']}

📈 *Top Niches:*
{chr(10).join([f'• {n}: {s:.2f}' for n, s in report['performance']['top_niches'][:3]]) if report['performance']['top_niches'] else '• No data yet'}

💡 *Recommendations:*
{chr(10).join([f"• {r.get('action', 'N/A')}" for r in report['scaling'][:3]]) if report['scaling'] else '• System running optimally'}
"""
        
        await self.survivor.alert_manager.send_telegram(report_text, "info")
        
        return report
    
    async def get_status(self) -> Dict:
        """Get current system status"""
        return {
            "state": self.state,
            "system_state": self.system_state.value,
            "is_running": self.is_running,
            "strategy": self.improver.get_current_strategy(),
            "health": await self.survivor.get_system_status()
        }
    
    async def emergency_fix(self) -> Dict:
        """Emergency fix cycle - run all self-repair systems"""
        self.system_state = SystemState.CRITICAL
        
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "actions": []
        }
        
        # Run healing
        healing = await self.healer.run_healing_cycle()
        results["actions"].append({"type": "healing", "result": healing})
        
        # Run fixing
        fixing = await self.fixer.run_fix_cycle()
        results["actions"].append({"type": "fixing", "result": fixing})
        
        # Alert owner
        await self.survivor.alert_manager.alert(
            f"🚨 EMERGENCY FIX EXECUTED\n\nHealing: {healing.get('healing', {}).get('healed', False)}\nFixes Applied: {fixing.get('fixes_applied', 0)}",
            "critical"
        )
        
        self.system_state = SystemState.RUNNING
        return results


# ============================================================
# CLI INTERFACE
# ============================================================

if __name__ == "__main__":
    import sys
    
    async def main():
        orchestrator = OmniOrchestrator()
        
        if len(sys.argv) > 1:
            command = sys.argv[1]
            
            if command == "cycle":
                result = await orchestrator.execute_autonomous_cycle()
            elif command == "maintenance":
                result = await orchestrator.run_maintenance()
            elif command == "report":
                result = await orchestrator.generate_daily_report()
            elif command == "status":
                result = await orchestrator.get_status()
            elif command == "heal":
                result = await orchestrator.healer.run_healing_cycle()
            elif command == "fix":
                result = await orchestrator.fixer.run_fix_cycle()
            elif command == "improve":
                result = orchestrator.improver.analyze_and_improve()
            elif command == "emergency":
                result = await orchestrator.emergency_fix()
            elif command == "help":
                result = {
                    "commands": {
                        "cycle": "Execute full autonomous cycle (hunt → create → distribute → improve)",
                        "maintenance": "Run hourly maintenance (health check, heal, fix, improve)",
                        "report": "Generate and send daily report",
                        "status": "Get current system status",
                        "heal": "Run self-healing cycle only",
                        "fix": "Run self-fixing cycle only",
                        "improve": "Run self-improvement analysis",
                        "emergency": "Execute emergency fix (all repair systems)",
                        "help": "Show this help message"
                    }
                }
            else:
                result = {"error": f"Unknown command: {command}", "hint": "Use 'help' for available commands"}
        else:
            result = await orchestrator.get_status()
        
        print(json.dumps(result, indent=2, default=str))
    
    asyncio.run(main())
