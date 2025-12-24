"""
MONEY MACHINE ERROR HANDLER
============================
Self-healing error intelligence system with Telegram alerts.
Python equivalent of the n8n error workflow.

Features:
- Error classification (TIMEOUT, AUTH_FAILURE, RATE_LIMIT, API_DOWN)
- Automatic recovery actions
- Telegram alerts to phone
- Error logging with forensic details
- Retry logic with exponential backoff
"""

import os
import sys
import json
import time
import traceback
import functools
import requests
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable, Any
from dataclasses import dataclass, asdict
from enum import Enum

from dotenv import load_dotenv

load_dotenv()


class ErrorType(Enum):
    TIMEOUT = "TIMEOUT"
    AUTH_FAILURE = "AUTH_FAILURE"
    RATE_LIMIT = "RATE_LIMIT"
    API_DOWN = "API_DOWN"
    RENDER_FAILED = "RENDER_FAILED"
    UPLOAD_FAILED = "UPLOAD_FAILED"
    UNKNOWN = "UNKNOWN"


class Severity(Enum):
    INFO = "INFO"
    WARN = "WARN"
    CRITICAL = "CRITICAL"


class RecoveryAction(Enum):
    AUTO_RETRY_IMMEDIATE = "AUTO_RETRY_IMMEDIATE"
    AUTO_RETRY_DELAYED = "AUTO_RETRY_DELAYED"
    CHECK_CREDENTIALS = "CHECK_CREDENTIALS"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    SKIP_AND_CONTINUE = "SKIP_AND_CONTINUE"


@dataclass
class ErrorReport:
    """Structured error report for logging and alerts"""
    severity: str
    error_type: str
    node_failed: str
    message: str
    timestamp: str
    recovery_action: str
    stack: str = ""
    execution_id: str = ""
    workflow: str = "Money Machine"
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    def to_telegram_message(self) -> str:
        return f"""🚨 **MONEY MACHINE ALERT**

**Severity:** {self.severity}
**Node:** {self.node_failed}
**Type:** {self.error_type}
**Time:** {self.timestamp}

**Message:**
```{self.message[:500]}```

**Recovery:** {self.recovery_action}"""


class ErrorHandler:
    """
    Central error handling system for Money Machine.
    Mirrors the n8n error workflow functionality.
    """
    
    def __init__(self):
        self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", "5033650061")
        self.error_log_path = Path("data/logs/errors.jsonl")
        self.error_log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Retry configuration
        self.max_retries = 3
        self.base_delay = 5  # seconds
        self.max_delay = 60  # seconds
    
    def classify_error(self, error: Exception) -> tuple[ErrorType, Severity, RecoveryAction]:
        """Classify error and determine recovery action"""
        msg = str(error).lower()
        
        # Rate limiting
        if "rate limit" in msg or "429" in msg or "too many requests" in msg:
            return ErrorType.RATE_LIMIT, Severity.WARN, RecoveryAction.AUTO_RETRY_DELAYED
        
        # Timeout
        if "timeout" in msg or "timed out" in msg:
            return ErrorType.TIMEOUT, Severity.WARN, RecoveryAction.AUTO_RETRY_IMMEDIATE
        
        # Authentication
        if "401" in msg or "403" in msg or "unauthorized" in msg or "forbidden" in msg:
            return ErrorType.AUTH_FAILURE, Severity.CRITICAL, RecoveryAction.CHECK_CREDENTIALS
        
        # API down
        if "500" in msg or "502" in msg or "503" in msg or "service unavailable" in msg:
            return ErrorType.API_DOWN, Severity.CRITICAL, RecoveryAction.AUTO_RETRY_DELAYED
        
        # Render failures
        if "ffmpeg" in msg or "render" in msg or "encoding" in msg:
            return ErrorType.RENDER_FAILED, Severity.CRITICAL, RecoveryAction.MANUAL_REVIEW
        
        # Upload failures
        if "upload" in msg or "youtube" in msg or "tiktok" in msg:
            return ErrorType.UPLOAD_FAILED, Severity.CRITICAL, RecoveryAction.AUTO_RETRY_DELAYED
        
        return ErrorType.UNKNOWN, Severity.CRITICAL, RecoveryAction.MANUAL_REVIEW
    
    def create_report(self, error: Exception, node_name: str = "Unknown") -> ErrorReport:
        """Create structured error report"""
        error_type, severity, recovery = self.classify_error(error)
        
        return ErrorReport(
            severity=severity.value,
            error_type=error_type.value,
            node_failed=node_name,
            message=str(error)[:1000],
            timestamp=datetime.now().isoformat(),
            recovery_action=recovery.value,
            stack=traceback.format_exc()[:500],
            execution_id=f"local_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
    
    def log_error(self, report: ErrorReport):
        """Log error to JSONL file for analysis"""
        with open(self.error_log_path, "a") as f:
            f.write(json.dumps(report.to_dict()) + "\n")
    
    def send_telegram_alert(self, report: ErrorReport) -> bool:
        """Send error alert to Telegram"""
        if not self.telegram_bot_token:
            print(f"[ERROR HANDLER] No Telegram token configured - logging only")
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            payload = {
                "chat_id": self.telegram_chat_id,
                "text": report.to_telegram_message(),
                "parse_mode": "Markdown"
            }
            
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            print(f"[ERROR HANDLER] ✅ Telegram alert sent")
            return True
            
        except Exception as e:
            print(f"[ERROR HANDLER] ❌ Telegram send failed: {e}")
            return False
    
    def handle(self, error: Exception, node_name: str = "Unknown", 
               alert: bool = True) -> ErrorReport:
        """
        Central error handling method.
        Creates report, logs, and optionally sends alert.
        """
        report = self.create_report(error, node_name)
        
        # Always log
        self.log_error(report)
        
        # Print to console
        print(f"\n{'='*60}")
        print(f"🚨 ERROR: {report.error_type}")
        print(f"   Node: {report.node_failed}")
        print(f"   Message: {report.message[:200]}")
        print(f"   Recovery: {report.recovery_action}")
        print(f"{'='*60}\n")
        
        # Send Telegram alert for critical errors
        if alert and report.severity == Severity.CRITICAL.value:
            self.send_telegram_alert(report)
        
        return report
    
    def should_retry(self, report: ErrorReport) -> bool:
        """Determine if error is retryable"""
        return report.recovery_action in [
            RecoveryAction.AUTO_RETRY_IMMEDIATE.value,
            RecoveryAction.AUTO_RETRY_DELAYED.value
        ]
    
    def get_retry_delay(self, attempt: int, report: ErrorReport) -> float:
        """Calculate retry delay with exponential backoff"""
        if report.recovery_action == RecoveryAction.AUTO_RETRY_IMMEDIATE.value:
            return min(self.base_delay * (2 ** attempt), self.max_delay)
        elif report.recovery_action == RecoveryAction.AUTO_RETRY_DELAYED.value:
            return min(self.base_delay * 2 * (2 ** attempt), self.max_delay * 2)
        return 0


# Global error handler instance
_handler = ErrorHandler()


def with_error_handling(node_name: str = "Unknown", max_retries: int = 3, 
                        alert_on_failure: bool = True):
    """
    Decorator for automatic error handling with retries.
    
    Usage:
        @with_error_handling("ScriptGenerator", max_retries=3)
        def generate_script(topic: str) -> str:
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_error = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                    
                except KeyboardInterrupt:
                    raise  # Don't catch Ctrl+C
                    
                except Exception as e:
                    last_error = e
                    report = _handler.handle(e, node_name, alert=False)
                    
                    if attempt < max_retries and _handler.should_retry(report):
                        delay = _handler.get_retry_delay(attempt, report)
                        print(f"[RETRY] Attempt {attempt + 1}/{max_retries} - waiting {delay:.1f}s...")
                        time.sleep(delay)
                    else:
                        # Final failure - send alert
                        if alert_on_failure:
                            _handler.send_telegram_alert(report)
                        break
            
            raise last_error
        
        return wrapper
    return decorator


def handle_error(error: Exception, node_name: str = "Unknown", 
                 alert: bool = True) -> ErrorReport:
    """Convenience function for manual error handling"""
    return _handler.handle(error, node_name, alert)


def send_success_alert(message: str):
    """Send success notification to Telegram"""
    if not _handler.telegram_bot_token:
        return
    
    try:
        url = f"https://api.telegram.org/bot{_handler.telegram_bot_token}/sendMessage"
        payload = {
            "chat_id": _handler.telegram_chat_id,
            "text": f"✅ **MONEY MACHINE SUCCESS**\n\n{message}",
            "parse_mode": "Markdown"
        }
        requests.post(url, json=payload, timeout=10)
    except:
        pass  # Silent fail for success messages


def send_status_update(title: str, details: dict):
    """Send status update to Telegram"""
    if not _handler.telegram_bot_token:
        return
    
    try:
        lines = [f"📊 **{title}**\n"]
        for key, value in details.items():
            lines.append(f"• **{key}:** {value}")
        
        url = f"https://api.telegram.org/bot{_handler.telegram_bot_token}/sendMessage"
        payload = {
            "chat_id": _handler.telegram_chat_id,
            "text": "\n".join(lines),
            "parse_mode": "Markdown"
        }
        requests.post(url, json=payload, timeout=10)
    except:
        pass


# =============================================================================
# SELF-TEST
# =============================================================================
if __name__ == "__main__":
    print("Testing Error Handler...")
    
    # Test error classification
    handler = ErrorHandler()
    
    test_errors = [
        Exception("Rate limit exceeded - 429"),
        Exception("Request timeout after 30s"),
        Exception("401 Unauthorized"),
        Exception("500 Internal Server Error"),
        Exception("FFmpeg render failed"),
        Exception("Unknown random error"),
    ]
    
    for err in test_errors:
        error_type, severity, recovery = handler.classify_error(err)
        print(f"  {str(err)[:40]:40} → {error_type.value:15} | {recovery.value}")
    
    print("\n✅ Error Handler ready!")
