#!/usr/bin/env python3
"""
🚀 MONEY MACHINE AI - LIVE PRODUCTION
=====================================
Autonomous Short Factory - No Human Intervention Required

This script runs continuously, creating and uploading Shorts
to your Money machine ai channel.

Usage:
    python LIVE.py              # Start production (1 Short/hour)
    python LIVE.py --fast       # 1 Short every 30 minutes
    python LIVE.py --test       # Run once, no upload
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path
from datetime import datetime, timezone

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()


def print_banner():
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   💰  MONEY MACHINE AI - LIVE PRODUCTION  💰                ║
║                                                              ║
║   Status: AUTONOMOUS                                         ║
║   Mode: CONTINUOUS                                           ║
║   Uploads: ENABLED                                           ║
║                                                              ║
║   Press Ctrl+C to stop                                       ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)


async def main():
    parser = argparse.ArgumentParser(description="Money Machine AI - LIVE Production")
    parser.add_argument("--fast", action="store_true", help="30 minute intervals")
    parser.add_argument("--test", action="store_true", help="Run once, no upload")
    parser.add_argument("--interval", type=int, default=3600, help="Custom interval in seconds")
    args = parser.parse_args()
    
    print_banner()
    
    # Import here to avoid circular imports
    from workflows.continuous_mode import ContinuousMode
    
    mode = ContinuousMode()
    
    # Determine interval
    if args.fast:
        interval = 1800  # 30 minutes
    else:
        interval = args.interval
    
    print(f"📡 Channel: Money machine ai (UCZppwcvPrWlAG0vb78elPJA)")
    print(f"⏱️  Interval: {interval // 60} minutes")
    print(f"🔒 Quality Gates: ENABLED")
    print(f"📤 Uploads: {'DISABLED (test mode)' if args.test else 'ENABLED'}")
    print(f"🕐 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n" + "="*60)
    
    if args.test:
        # Run once without upload
        await mode.create_one()
        print("\n✅ Test complete. Run without --test to enable uploads.")
    else:
        # Run continuously with uploads
        await mode.run_continuous(interval=interval)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n🛑 Production stopped by user")
        print("   Run 'python LIVE.py' to restart")
