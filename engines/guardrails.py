"""
============================================================
ELITE MONEY MACHINE - GUARDRAILS & RATE LIMITING
Final Hardening Layer
============================================================
Prevents bans, throttling, and cascading failures.
Self-healing with automatic platform pause/resume.
============================================================
"""

import os
import json
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import shutil


# ============================================================
# CONFIGURATION
# ============================================================

@dataclass
class PlatformLimits:
    """Rate limits per platform to prevent bans"""
    max_per_day: int
    min_spacing_hours: float
    max_retries: int
    pause_on_failures: int  # Consecutive failures before pause
    pause_duration_hours: float


PLATFORM_LIMITS = {
    "youtube": PlatformLimits(
        max_per_day=12,
        min_spacing_hours=2.0,
        max_retries=3,
        pause_on_failures=3,
        pause_duration_hours=6.0
    ),
    "instagram": PlatformLimits(
        max_per_day=10,
        min_spacing_hours=3.0,
        max_retries=3,
        pause_on_failures=3,
        pause_duration_hours=6.0
    ),
    "tiktok": PlatformLimits(
        max_per_day=15,
        min_spacing_hours=1.5,
        max_retries=3,
        pause_on_failures=3,
        pause_duration_hours=6.0
    )
}


# ============================================================
# UPLOAD RATE LIMITER
# ============================================================

class UploadRateLimiter:
    """
    Rate limiter for platform uploads.
    Enforces daily limits and minimum spacing.
    Prevents account bans from over-posting.
    """
    
    def __init__(self, data_dir: Path = None):
        self.data_dir = data_dir or Path(__file__).parent.parent / "data"
        self.state_file = self.data_dir / "rate_limiter_state.json"
        self.state = self._load_state()
    
    def _load_state(self) -> Dict:
        """Load rate limiter state from disk"""
        if self.state_file.exists():
            try:
                with open(self.state_file) as f:
                    return json.load(f)
            except:
                pass
        return {
            "uploads": {},  # {platform: [{timestamp, video_id}]}
            "failures": {},  # {platform: {count, last_failure}}
            "paused": {},  # {platform: resume_at}
            "quarantine": []  # [{job_id, reason, timestamp}]
        }
    
    def _save_state(self):
        """Persist state to disk"""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, "w") as f:
            json.dump(self.state, f, indent=2, default=str)
    
    def _cleanup_old_uploads(self, platform: str):
        """Remove uploads older than 24 hours"""
        if platform not in self.state["uploads"]:
            return
        
        cutoff = datetime.now() - timedelta(hours=24)
        self.state["uploads"][platform] = [
            u for u in self.state["uploads"][platform]
            if datetime.fromisoformat(u["timestamp"]) > cutoff
        ]
    
    def can_upload(self, platform: str) -> Dict[str, Any]:
        """
        Check if we can upload to a platform.
        Returns status and wait time if needed.
        """
        limits = PLATFORM_LIMITS.get(platform)
        if not limits:
            return {"allowed": True, "reason": "No limits configured"}
        
        # Check if platform is paused
        if platform in self.state["paused"]:
            resume_at = datetime.fromisoformat(self.state["paused"][platform])
            if datetime.now() < resume_at:
                wait_seconds = (resume_at - datetime.now()).total_seconds()
                return {
                    "allowed": False,
                    "reason": f"Platform paused due to failures",
                    "wait_seconds": wait_seconds,
                    "resume_at": resume_at.isoformat()
                }
            else:
                # Resume time passed, unblock
                del self.state["paused"][platform]
                self.state["failures"][platform] = {"count": 0}
                self._save_state()
        
        # Clean old uploads
        self._cleanup_old_uploads(platform)
        
        uploads = self.state["uploads"].get(platform, [])
        
        # Check daily limit
        if len(uploads) >= limits.max_per_day:
            oldest = datetime.fromisoformat(uploads[0]["timestamp"])
            reset_at = oldest + timedelta(hours=24)
            wait_seconds = (reset_at - datetime.now()).total_seconds()
            return {
                "allowed": False,
                "reason": f"Daily limit reached ({limits.max_per_day}/day)",
                "wait_seconds": max(0, wait_seconds),
                "reset_at": reset_at.isoformat()
            }
        
        # Check spacing
        if uploads:
            last = datetime.fromisoformat(uploads[-1]["timestamp"])
            min_next = last + timedelta(hours=limits.min_spacing_hours)
            if datetime.now() < min_next:
                wait_seconds = (min_next - datetime.now()).total_seconds()
                return {
                    "allowed": False,
                    "reason": f"Minimum spacing not met ({limits.min_spacing_hours}h)",
                    "wait_seconds": wait_seconds,
                    "next_allowed": min_next.isoformat()
                }
        
        return {
            "allowed": True,
            "uploads_today": len(uploads),
            "remaining": limits.max_per_day - len(uploads)
        }
    
    def record_upload(self, platform: str, video_id: str = None):
        """Record a successful upload"""
        if platform not in self.state["uploads"]:
            self.state["uploads"][platform] = []
        
        self.state["uploads"][platform].append({
            "timestamp": datetime.now().isoformat(),
            "video_id": video_id
        })
        
        # Reset failure count on success
        self.state["failures"][platform] = {"count": 0}
        
        self._save_state()
    
    def record_failure(self, platform: str, error: str, job_id: str = None) -> Dict:
        """
        Record an upload failure.
        Returns quarantine info if threshold reached.
        """
        limits = PLATFORM_LIMITS.get(platform)
        if not limits:
            return {"quarantined": False}
        
        if platform not in self.state["failures"]:
            self.state["failures"][platform] = {"count": 0}
        
        self.state["failures"][platform]["count"] += 1
        self.state["failures"][platform]["last_error"] = error
        self.state["failures"][platform]["last_failure"] = datetime.now().isoformat()
        
        count = self.state["failures"][platform]["count"]
        
        # Check if should pause platform
        if count >= limits.pause_on_failures:
            resume_at = datetime.now() + timedelta(hours=limits.pause_duration_hours)
            self.state["paused"][platform] = resume_at.isoformat()
            
            # Quarantine the job
            if job_id:
                self.state["quarantine"].append({
                    "job_id": job_id,
                    "platform": platform,
                    "reason": f"{count} consecutive failures",
                    "timestamp": datetime.now().isoformat()
                })
            
            self._save_state()
            
            return {
                "quarantined": True,
                "platform_paused": True,
                "resume_at": resume_at.isoformat(),
                "consecutive_failures": count
            }
        
        self._save_state()
        return {
            "quarantined": False,
            "consecutive_failures": count,
            "retries_remaining": limits.max_retries - count
        }
    
    def get_status(self) -> Dict:
        """Get current rate limiter status"""
        status = {}
        
        for platform, limits in PLATFORM_LIMITS.items():
            self._cleanup_old_uploads(platform)
            uploads = self.state["uploads"].get(platform, [])
            failures = self.state["failures"].get(platform, {})
            
            status[platform] = {
                "uploads_today": len(uploads),
                "limit": limits.max_per_day,
                "remaining": limits.max_per_day - len(uploads),
                "consecutive_failures": failures.get("count", 0),
                "paused": platform in self.state["paused"],
                "can_upload": self.can_upload(platform)["allowed"]
            }
            
            if platform in self.state["paused"]:
                status[platform]["resume_at"] = self.state["paused"][platform]
        
        status["quarantine_count"] = len(self.state["quarantine"])
        
        return status


# ============================================================
# LOG ROTATOR
# ============================================================

class LogRotator:
    """
    Manages log files with automatic rotation.
    Keeps last 14 days, auto-deletes older logs.
    """
    
    RETENTION_DAYS = 14
    
    def __init__(self, log_dir: Path = None):
        self.log_dir = log_dir or Path(__file__).parent.parent / "data" / "logs"
        self.metrics_dir = Path(__file__).parent.parent / "data" / "metrics"
        self.quarantine_dir = Path(__file__).parent.parent / "data" / "quarantine"
        
        # Ensure directories exist
        for d in [self.log_dir, self.metrics_dir, self.quarantine_dir]:
            d.mkdir(parents=True, exist_ok=True)
    
    def log(self, category: str, message: str, level: str = "INFO", data: Dict = None):
        """Write a log entry"""
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = self.log_dir / f"{category}_{today}.log"
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            "data": data or {}
        }
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    
    def log_metric(self, metric_name: str, value: Any, tags: Dict = None):
        """Log a metric value"""
        today = datetime.now().strftime("%Y-%m-%d")
        metrics_file = self.metrics_dir / f"metrics_{today}.jsonl"
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "metric": metric_name,
            "value": value,
            "tags": tags or {}
        }
        
        with open(metrics_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    
    def quarantine_job(self, job_id: str, reason: str, data: Dict = None):
        """Move a failed job to quarantine"""
        quarantine_file = self.quarantine_dir / f"{job_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        entry = {
            "job_id": job_id,
            "reason": reason,
            "timestamp": datetime.now().isoformat(),
            "data": data or {}
        }
        
        with open(quarantine_file, "w", encoding="utf-8") as f:
            json.dump(entry, f, indent=2)
        
        self.log("quarantine", f"Job quarantined: {job_id}", "WARNING", entry)
    
    def rotate(self) -> Dict:
        """
        Rotate logs - delete files older than retention period.
        Should be called daily or at startup.
        """
        cutoff = datetime.now() - timedelta(days=self.RETENTION_DAYS)
        deleted = {"logs": 0, "metrics": 0}
        
        for directory, key in [(self.log_dir, "logs"), (self.metrics_dir, "metrics")]:
            for file in directory.glob("*.log") if key == "logs" else directory.glob("*.jsonl"):
                try:
                    # Extract date from filename
                    name = file.stem
                    date_str = name.split("_")[-1] if "_" in name else name
                    file_date = datetime.strptime(date_str, "%Y-%m-%d")
                    
                    if file_date < cutoff:
                        file.unlink()
                        deleted[key] += 1
                except (ValueError, IndexError):
                    continue
        
        self.log("system", f"Log rotation complete", "INFO", deleted)
        return deleted
    
    def get_recent_logs(self, category: str = None, hours: int = 24, level: str = None) -> list:
        """Get recent log entries"""
        entries = []
        cutoff = datetime.now() - timedelta(hours=hours)
        
        pattern = f"{category}_*.log" if category else "*.log"
        
        for log_file in sorted(self.log_dir.glob(pattern), reverse=True):
            try:
                with open(log_file, encoding="utf-8") as f:
                    for line in f:
                        try:
                            entry = json.loads(line)
                            entry_time = datetime.fromisoformat(entry["timestamp"])
                            
                            if entry_time < cutoff:
                                continue
                            
                            if level and entry.get("level") != level:
                                continue
                            
                            entries.append(entry)
                        except:
                            continue
            except:
                continue
        
        return sorted(entries, key=lambda x: x["timestamp"], reverse=True)


# ============================================================
# HEALTH DOWNGRADE MANAGER
# ============================================================

class HealthDowngradeManager:
    """
    Manages health degradation and automatic recovery.
    Implements platform pausing, source switching, and fallbacks.
    """
    
    def __init__(self, log_rotator: LogRotator = None):
        self.logger = log_rotator or LogRotator()
        self.data_dir = Path(__file__).parent.parent / "data"
        self.state_file = self.data_dir / "health_state.json"
        self.state = self._load_state()
    
    def _load_state(self) -> Dict:
        if self.state_file.exists():
            try:
                with open(self.state_file) as f:
                    return json.load(f)
            except:
                pass
        return {
            "api_failures": {},  # {api_name: {count, last_failure, paused_until}}
            "source_failures": {},  # {source_name: {count, disabled}}
            "ffmpeg_fallback": False,
            "trend_sources": ["newsapi", "reddit", "google_trends"]  # Priority order
        }
    
    def _save_state(self):
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, "w") as f:
            json.dump(self.state, f, indent=2, default=str)
    
    def record_api_failure(self, api_name: str, error: str) -> Dict:
        """
        Record an API failure.
        3 consecutive failures = pause for 6 hours.
        """
        if api_name not in self.state["api_failures"]:
            self.state["api_failures"][api_name] = {"count": 0}
        
        state = self.state["api_failures"][api_name]
        state["count"] += 1
        state["last_failure"] = datetime.now().isoformat()
        state["last_error"] = error
        
        result = {"paused": False, "count": state["count"]}
        
        if state["count"] >= 3:
            resume_at = datetime.now() + timedelta(hours=6)
            state["paused_until"] = resume_at.isoformat()
            result["paused"] = True
            result["resume_at"] = resume_at.isoformat()
            
            self.logger.log("health", f"API {api_name} paused due to failures", "WARNING", {
                "api": api_name,
                "consecutive_failures": state["count"],
                "resume_at": resume_at.isoformat()
            })
        
        self._save_state()
        return result
    
    def record_api_success(self, api_name: str):
        """Record successful API call - resets failure count"""
        if api_name in self.state["api_failures"]:
            self.state["api_failures"][api_name] = {"count": 0}
            self._save_state()
    
    def is_api_available(self, api_name: str) -> bool:
        """Check if an API is available (not paused)"""
        state = self.state["api_failures"].get(api_name, {})
        
        if "paused_until" in state:
            resume_at = datetime.fromisoformat(state["paused_until"])
            if datetime.now() < resume_at:
                return False
            else:
                # Resume time passed
                state["count"] = 0
                del state["paused_until"]
                self._save_state()
        
        return True
    
    def record_source_failure(self, source_name: str) -> str:
        """
        Record trend source failure.
        Returns next source to try or None if all exhausted.
        """
        if source_name not in self.state["source_failures"]:
            self.state["source_failures"][source_name] = {"count": 0}
        
        self.state["source_failures"][source_name]["count"] += 1
        self.state["source_failures"][source_name]["last_failure"] = datetime.now().isoformat()
        
        # Get next available source
        for source in self.state["trend_sources"]:
            failures = self.state["source_failures"].get(source, {})
            if failures.get("count", 0) < 3:
                self._save_state()
                return source
        
        # All sources failed - reset and start over
        self.state["source_failures"] = {}
        self._save_state()
        
        self.logger.log("health", "All trend sources failed - resetting", "WARNING")
        return self.state["trend_sources"][0]
    
    def set_ffmpeg_fallback(self, enabled: bool):
        """Enable/disable FFmpeg fallback mode"""
        self.state["ffmpeg_fallback"] = enabled
        self._save_state()
        
        if enabled:
            self.logger.log("health", "FFmpeg fallback mode enabled", "WARNING")
    
    def get_health_status(self) -> Dict:
        """Get current health status"""
        status = {
            "apis": {},
            "sources": {},
            "ffmpeg_fallback": self.state["ffmpeg_fallback"]
        }
        
        for api, state in self.state["api_failures"].items():
            status["apis"][api] = {
                "failures": state.get("count", 0),
                "available": self.is_api_available(api),
                "paused_until": state.get("paused_until")
            }
        
        for source, state in self.state["source_failures"].items():
            status["sources"][source] = {
                "failures": state.get("count", 0),
                "available": state.get("count", 0) < 3
            }
        
        # Overall health
        api_issues = sum(1 for a in status["apis"].values() if not a["available"])
        source_issues = sum(1 for s in status["sources"].values() if not s["available"])
        
        if api_issues == 0 and source_issues == 0 and not self.state["ffmpeg_fallback"]:
            status["overall"] = "healthy"
        elif api_issues > 1 or source_issues > 1:
            status["overall"] = "degraded"
        else:
            status["overall"] = "warning"
        
        return status


# ============================================================
# MASTER GUARDRAILS (UNIFIED INTERFACE)
# ============================================================

class Guardrails:
    """
    Unified interface for all guardrails.
    Use this class for all safety checks.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.rate_limiter = UploadRateLimiter()
        self.logger = LogRotator()
        self.health = HealthDowngradeManager(self.logger)
        self._initialized = True
        
        # Run log rotation on startup
        self.logger.rotate()
    
    def can_upload(self, platform: str) -> Dict:
        """Check if upload is allowed"""
        return self.rate_limiter.can_upload(platform)
    
    def record_upload(self, platform: str, video_id: str = None):
        """Record successful upload"""
        self.rate_limiter.record_upload(platform, video_id)
        self.logger.log_metric("upload_success", 1, {"platform": platform})
        self.logger.log("uploads", f"Upload successful: {platform}", "INFO", {"video_id": video_id})
    
    def record_failure(self, platform: str, error: str, job_id: str = None) -> Dict:
        """Record upload failure"""
        result = self.rate_limiter.record_failure(platform, error, job_id)
        self.health.record_api_failure(platform, error)
        self.logger.log_metric("upload_failure", 1, {"platform": platform})
        self.logger.log("uploads", f"Upload failed: {platform}", "ERROR", {"error": error})
        return result
    
    def get_status(self) -> Dict:
        """Get complete guardrails status"""
        return {
            "rate_limits": self.rate_limiter.get_status(),
            "health": self.health.get_health_status(),
            "timestamp": datetime.now().isoformat()
        }
    
    def log(self, category: str, message: str, level: str = "INFO", data: Dict = None):
        """Log a message"""
        self.logger.log(category, message, level, data)
    
    def metric(self, name: str, value: Any, tags: Dict = None):
        """Log a metric"""
        self.logger.log_metric(name, value, tags)


# ============================================================
# CLI INTERFACE
# ============================================================

if __name__ == "__main__":
    import sys
    
    guardrails = Guardrails()
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        
        if cmd == "status":
            import json
            print(json.dumps(guardrails.get_status(), indent=2, default=str))
        
        elif cmd == "rotate":
            result = guardrails.logger.rotate()
            print(f"Rotated logs: {result}")
        
        elif cmd == "can-upload" and len(sys.argv) > 2:
            platform = sys.argv[2]
            result = guardrails.can_upload(platform)
            print(f"{platform}: {'✅ Allowed' if result['allowed'] else '❌ Blocked'}")
            print(json.dumps(result, indent=2))
        
        else:
            print("Usage: guardrails.py [status|rotate|can-upload <platform>]")
    else:
        print("Guardrails Status:")
        print("-" * 40)
        status = guardrails.get_status()
        for platform, info in status["rate_limits"].items():
            if isinstance(info, dict) and "can_upload" in info:
                icon = "✅" if info["can_upload"] else "🚫"
                print(f"  {icon} {platform}: {info.get('uploads_today', 0)}/{info.get('limit', '?')} uploads")
        print(f"\n  Health: {status['health']['overall']}")
