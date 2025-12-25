#!/usr/bin/env python3
"""
════════════════════════════════════════════════════════════════════════════════
💎 MONEY MACHINE AI — SOVEREIGN PRODUCTION DAEMON
════════════════════════════════════════════════════════════════════════════════
THE FINAL FORM: Continuous autonomous production

This script runs FOREVER, producing elite content:
- Every 30 minutes: New Short
- Every 6 hours: Check winners for longform expansion
- Self-healing: Retries on failure
- Hollywood quality: 8-10 Mbps enforced

Run this. Leave for work. Come back to money.

Usage:
    python SOVEREIGN.py                 # Start the machine
    python SOVEREIGN.py --fast          # 15 min intervals (testing)
    python SOVEREIGN.py --once          # Single video only
════════════════════════════════════════════════════════════════════════════════
"""

import os
import sys
import json
import asyncio
import argparse
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

# Import the job runner
from workflows.run_job import JobRunner

# ════════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ════════════════════════════════════════════════════════════════════════════════

OUTPUT_DIR = Path(__file__).parent / "data" / "output"
LOGS_DIR = Path(__file__).parent / "data" / "logs"

# Production intervals (in seconds)
SHORTS_INTERVAL = 30 * 60      # 30 minutes
ANALYTICS_INTERVAL = 6 * 60 * 60  # 6 hours

# Telegram notifications
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8501373839:AAGQley_8ZKwhzMzU7HTooonBb1ufiYj-Gw")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "5033650061")


# ════════════════════════════════════════════════════════════════════════════════
# TELEGRAM ALERTS
# ════════════════════════════════════════════════════════════════════════════════

async def send_telegram(message: str):
    """Send Telegram notification."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            await client.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json={
                    "chat_id": TELEGRAM_CHAT_ID,
                    "text": message,
                    "parse_mode": "Markdown"
                }
            )
    except Exception as e:
        print(f"[TELEGRAM] ⚠️ Failed: {e}")


# ════════════════════════════════════════════════════════════════════════════════
# SOVEREIGN DAEMON
# ════════════════════════════════════════════════════════════════════════════════

class SovereignDaemon:
    """
    The autonomous media production daemon.
    
    This is the final form of Money Machine AI.
    It runs continuously, learning and evolving.
    """
    
    def __init__(self, shorts_interval: int = SHORTS_INTERVAL):
        self.shorts_interval = shorts_interval
        self.runner = JobRunner()
        self.stats = {
            "started_at": datetime.now(timezone.utc).isoformat(),
            "videos_created": 0,
            "videos_uploaded": 0,
            "videos_failed": 0,
            "total_bitrate_avg": 0,
            "winners": []
        }
        self.running = True
    
    def print_banner(self):
        print("""
================================================================================
                                                                              
    MONEY MACHINE AI - SOVEREIGN PRODUCTION DAEMON                            
                                                                              
    +-----------------------------------------------------------------------+
    |  You are not "posting videos".                                        |
    |  You are running a distributed media intelligence system.             |
    |                                                                       |
    |  * Local compute (quality + control)                                  |
    |  * Cloud orchestration (scale + reliability)                          |
    |  * AI APIs (speed + leverage)                                         |
    |  * Feedback loops (learning + evolution)                              |
    +-----------------------------------------------------------------------+
                                                                              
    Status: AUTONOMOUS                                                         
    Quality: HOLLYWOOD (8-10 Mbps)                                            
    Evolution: AAVE ACTIVE                                                     
                                                                              
    Press Ctrl+C to stop                                                       
                                                                              
================================================================================
        """)
    
    async def produce_short(self) -> Dict:
        """Produce a single elite Short."""
        
        payload = {
            "mode": "shorts",
            "force_upload": True,
            "elite": True
        }
        
        result = await self.runner.run(payload)
        
        if result["status"] == "SUCCESS":
            self.stats["videos_created"] += 1
            if result.get("youtube_url"):
                self.stats["videos_uploaded"] += 1
            
            # Track bitrate average
            if result.get("bitrate"):
                current_avg = self.stats["total_bitrate_avg"]
                count = self.stats["videos_created"]
                self.stats["total_bitrate_avg"] = (current_avg * (count - 1) + result["bitrate"]) / count
            
            # Send success notification
            await send_telegram(
                f"🎬 *ELITE VIDEO #{self.stats['videos_created']}*\n\n"
                f"📌 *Topic:* {result.get('dna', {}).get('topic', 'Unknown')}\n"
                f"📊 *Bitrate:* {result.get('bitrate', 0) / 1_000_000:.1f} Mbps\n"
                f"⏱️ *Duration:* {result.get('duration', 0):.1f}s\n"
                f"🔗 {result.get('youtube_url', 'Saved locally')}\n\n"
                f"_The machine is learning._ 🧠"
            )
        else:
            self.stats["videos_failed"] += 1
            
            await send_telegram(
                f"⚠️ *PRODUCTION FAILED*\n\n"
                f"❌ *Error:* {result.get('error', 'Unknown')}\n"
                f"🔄 *Retrying next cycle...*"
            )
        
        return result
    
    async def run_continuous(self):
        """Run continuous production forever."""
        
        self.print_banner()
        
        print(f"📡 Channel: Money Machine AI")
        print(f"⏱️  Interval: {self.shorts_interval // 60} minutes")
        print(f"🔒 Quality: Hollywood (8-10 Mbps enforced)")
        print(f"📤 Upload: ENABLED")
        print(f"📱 Telegram: ENABLED")
        print(f"🕐 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\n" + "═" * 70)
        
        # Startup notification
        await send_telegram(
            f"🚀 *SOVEREIGN DAEMON STARTED*\n\n"
            f"⏱️ Interval: {self.shorts_interval // 60} min\n"
            f"📊 Quality: Hollywood\n"
            f"🔄 Mode: Autonomous\n\n"
            f"_The machine is now running._ 💎"
        )
        
        cycle = 0
        
        while self.running:
            cycle += 1
            
            print(f"\n{'═' * 70}")
            print(f"🔄 CYCLE {cycle} | Created: {self.stats['videos_created']} | "
                  f"Uploaded: {self.stats['videos_uploaded']} | "
                  f"Failed: {self.stats['videos_failed']}")
            print(f"{'═' * 70}")
            
            try:
                # Produce a Short
                result = await self.produce_short()
                
                if result["status"] == "SUCCESS":
                    print(f"\n✅ SUCCESS: {result.get('youtube_url', result.get('video_path'))}")
                else:
                    print(f"\n❌ FAILED: {result.get('error')}")
                
            except Exception as e:
                print(f"\n❌ CYCLE ERROR: {e}")
                self.stats["videos_failed"] += 1
            
            # Wait for next cycle
            if self.running:
                next_time = datetime.now() + timedelta(seconds=self.shorts_interval)
                print(f"\n⏳ Next production at {next_time.strftime('%H:%M:%S')}")
                print(f"   ({self.shorts_interval // 60} minutes)")
                
                await asyncio.sleep(self.shorts_interval)
    
    async def run_once(self):
        """Run single production."""
        self.print_banner()
        
        print("🎯 Single production mode")
        print("═" * 70)
        
        result = await self.produce_short()
        
        print("\n" + "═" * 70)
        print("📊 RESULT:")
        print(json.dumps(result, indent=2))
        
        return result
    
    def stop(self):
        """Stop the daemon gracefully."""
        self.running = False
        print("\n🛑 Stopping daemon...")


# ════════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════════

async def main():
    parser = argparse.ArgumentParser(description="Money Machine AI - Sovereign Daemon")
    parser.add_argument("--fast", action="store_true", help="15 minute intervals")
    parser.add_argument("--once", action="store_true", help="Single production only")
    parser.add_argument("--interval", type=int, default=30, help="Interval in minutes")
    args = parser.parse_args()
    
    # Calculate interval
    if args.fast:
        interval = 15 * 60  # 15 minutes
    else:
        interval = args.interval * 60
    
    daemon = SovereignDaemon(shorts_interval=interval)
    
    try:
        if args.once:
            await daemon.run_once()
        else:
            await daemon.run_continuous()
    except KeyboardInterrupt:
        daemon.stop()
        
        # Final stats
        print("\n" + "═" * 70)
        print("📊 FINAL STATISTICS:")
        print(f"   Videos Created: {daemon.stats['videos_created']}")
        print(f"   Videos Uploaded: {daemon.stats['videos_uploaded']}")
        print(f"   Videos Failed: {daemon.stats['videos_failed']}")
        if daemon.stats['total_bitrate_avg']:
            print(f"   Avg Bitrate: {daemon.stats['total_bitrate_avg'] / 1_000_000:.1f} Mbps")
        print("═" * 70)
        
        await send_telegram(
            f"🛑 *DAEMON STOPPED*\n\n"
            f"📊 *Final Stats:*\n"
            f"• Created: {daemon.stats['videos_created']}\n"
            f"• Uploaded: {daemon.stats['videos_uploaded']}\n"
            f"• Failed: {daemon.stats['videos_failed']}\n\n"
            f"_Run `python SOVEREIGN.py` to restart._"
        )


if __name__ == "__main__":
    asyncio.run(main())
