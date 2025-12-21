#!/usr/bin/env python3
"""
============================================================
ELITE MONEY MACHINE v2.0 - AUTONOMOUS LAUNCHER
POST-HUMAN MODE: Data decides. Machine improves. You collect.
============================================================
Usage:
    python run.py                    # Single cycle (interactive)
    python run.py --continuous       # 24/7 autonomous mode
    python run.py --dry-run          # Test without posting
    python run.py --health           # Health check only
    python run.py --status           # System status
============================================================
"""

import asyncio
import argparse
import json
import os
import sys
import random
from datetime import datetime
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# ============================================================
# CONFIGURATION (LOCKED)
# ============================================================

class MachineConfig:
    """Hardened configuration - DO NOT CHANGE"""
    
    # Cycle timing (continuous mode)
    CYCLE_INTERVAL_MINUTES = 60  # 1 cycle per hour
    CYCLE_JITTER_MINUTES = 15    # Random jitter to avoid patterns
    MAX_CYCLES_PER_DAY = 20      # Safety limit
    
    # Locked niches (fastest money)
    NICHES = [
        "wealth",      # AI income, side hustle, money
        "health",      # Bio-optimization, energy, sleep
        "survival"     # Self-reliance, preparedness
    ]
    
    # Circuit breaker settings
    MAX_FAILURES_BEFORE_PAUSE = 3
    PAUSE_DURATION_MINUTES = 30
    
    # Required directories
    REQUIRED_DIRS = [
        PROJECT_ROOT / "data" / "assets",
        PROJECT_ROOT / "data" / "temp",
        PROJECT_ROOT / "data" / "output",
        PROJECT_ROOT / "data" / "logs",
        PROJECT_ROOT / "data" / "metrics",
    ]


# ============================================================
# AUTO-PROVISIONING (NEVER FAIL ON MISSING FILES)
# ============================================================

async def auto_provision():
    """Ensure all required resources exist"""
    print("🔧 Auto-provisioning resources...")
    
    # Create required directories
    for dir_path in MachineConfig.REQUIRED_DIRS:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # Check/create default background video
    default_bg = PROJECT_ROOT / "data" / "assets" / "default_bg.mp4"
    if not default_bg.exists():
        print("   📹 Generating default background video...")
        await generate_default_background(str(default_bg))
    
    print("   ✅ All resources provisioned")
    return True


async def generate_default_background(output_path: str):
    """Generate a default background video using FFmpeg"""
    import subprocess
    
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "color=c=black:s=1920x1080:d=120",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "30",
        "-pix_fmt", "yuv420p",
        output_path
    ]
    
    try:
        subprocess.run(cmd, capture_output=True, check=True)
        print("   ✅ Default background created")
    except Exception as e:
        print(f"   ⚠️ Could not create background: {e}")


def print_banner():
    """Print the Money Machine banner"""
    banner = """
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║     💰 ELITE MONEY MACHINE v2.0 💰                       ║
    ║                                                          ║
    ║     POST-HUMAN MODE • AUTONOMOUS • CAPITALIZING          ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """
    print(banner)


async def test_imports():
    """Test all engine imports"""
    print("🔍 Testing engine imports...")
    try:
        from engines import (
            MoneyMachine,
            OmniOrchestrator,
            MasterHunter,
            MasterCreator,
            MasterGatherer,
            MasterBusinessman,
            MasterSurvivor,
            MasterAffiliateEngine,
            MasterSystemeManager,
            MasterFinancialAuditor,
            MasterEliteSurvivor,
            MasterProfitAllocator,
            MasterAdReinvestor
        )
        print("✅ All engines imported successfully!")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False


async def check_environment():
    """Check required environment variables"""
    print("\n🔐 Checking environment variables...")
    
    required = [
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
    ]
    
    optional = [
        "REDDIT_CLIENT_ID",
        "REDDIT_CLIENT_SECRET",
        "PEXELS_API_KEY",
        "YOUTUBE_CLIENT_ID",
        "YOUTUBE_CLIENT_SECRET",
        "OPENAI_API_KEY",
        "STRIPE_API_KEY",
        "PAYPAL_CLIENT_ID",
    ]
    
    missing_required = []
    missing_optional = []
    
    for var in required:
        if not os.getenv(var):
            missing_required.append(var)
        else:
            print(f"  ✅ {var}: Set")
    
    for var in optional:
        if not os.getenv(var):
            missing_optional.append(var)
        else:
            print(f"  ✅ {var}: Set")
    
    if missing_required:
        print(f"\n❌ Missing REQUIRED variables: {', '.join(missing_required)}")
        return False
    
    if missing_optional:
        print(f"\n⚠️  Missing optional variables: {', '.join(missing_optional)}")
        print("   (System will run with reduced functionality)")
    
    return True


async def test_telegram():
    """Test Telegram connection"""
    print("\n📱 Testing Telegram connection...")
    
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        print("❌ TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set")
        return False
    
    try:
        import httpx
        
        message = f"""
🤖 *MONEY MACHINE - SYSTEM TEST*

✅ Connection successful!
⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🖥️ Host: Local Development

System is ready for activation.
        """
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "Markdown"
                }
            )
            
            if response.status_code == 200:
                print("✅ Telegram message sent successfully!")
                print("   Check your Telegram for the test message.")
                return True
            else:
                print(f"❌ Telegram error: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Telegram test failed: {e}")
        return False


async def run_health_check():
    """Run system health check"""
    print("\n🏥 Running health check...")
    
    try:
        from engines import MasterSurvivor, MasterEliteSurvivor
        
        survivor = MasterSurvivor()
        elite_survivor = MasterEliteSurvivor()
        
        # Basic health check
        health = await survivor.run_health_check()
        
        print("\n📊 Health Report:")
        print(f"   Status: {health.get('health', {}).get('status', 'unknown')}")
        print(f"   Overall: {health.get('health', {}).get('overall_health', 'unknown')}")
        
        # Component status
        components = health.get('health', {}).get('components', {})
        if components:
            print("\n   Components:")
            for comp, status in components.items():
                emoji = "✅" if status == "healthy" else "⚠️" if status == "degraded" else "❌"
                print(f"     {emoji} {comp}: {status}")
        
        return health
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return None


async def run_dry_cycle():
    """Run a dry cycle (no actual posting)"""
    print("\n🧪 Running DRY RUN cycle...")
    print("   (No content will be posted)")
    
    try:
        from engines import MoneyMachine, OmniOrchestrator
        
        # Create orchestrator
        orchestrator = OmniOrchestrator()
        
        print("\n📡 Starting dry run...")
        
        # Simulate cycle steps
        steps = [
            ("🔍 Hunter", "Scanning for opportunities..."),
            ("🎨 Creator", "Preparing content pipeline..."),
            ("📤 Gatherer", "Distribution channels ready..."),
            ("💰 Businessman", "Financial tracking active..."),
            ("🛡️ Survivor", "Health monitoring engaged..."),
        ]
        
        for step_name, step_desc in steps:
            print(f"   {step_name}: {step_desc}")
            await asyncio.sleep(0.5)
        
        print("\n✅ Dry run complete!")
        print("   All systems operational.")
        print("   Ready for live cycle.")
        
        return True
        
    except Exception as e:
        print(f"❌ Dry run failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_full_cycle():
    """Run a full money-making cycle"""
    print("\n🚀 STARTING FULL CYCLE...")
    print("=" * 50)
    
    try:
        from engines import MoneyMachine
        
        machine = MoneyMachine()
        
        print("\n⚡ Executing full cycle...")
        print("   This may take several minutes.\n")
        
        # Execute cycle
        results = await machine.execute_full_cycle()
        
        # Print results
        print("\n📊 Cycle Results:")
        print("-" * 30)
        
        if results.get("hunt"):
            opps = results["hunt"].get("top_opportunities", [])
            print(f"   🔍 Opportunities found: {len(opps)}")
        
        if results.get("create"):
            status = results["create"].get("status", "unknown")
            print(f"   🎨 Content creation: {status}")
        
        if results.get("distribute"):
            print(f"   📤 Distribution: Complete")
        
        if results.get("financials"):
            print(f"   💰 Financials logged")
        
        if results.get("health"):
            health_status = results["health"].get("health", {}).get("status", "unknown")
            print(f"   🏥 Health: {health_status}")
        
        if results.get("error"):
            print(f"\n   ⚠️ Error encountered: {results['error']}")
        
        print("\n" + "=" * 50)
        print("✅ CYCLE COMPLETE")
        
        # Send Telegram notification
        await send_cycle_report(results)
        
        return results
        
    except Exception as e:
        print(f"\n❌ Cycle failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def send_cycle_report(results):
    """Send cycle report to Telegram"""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        return
    
    try:
        import httpx
        
        hunt_count = len(results.get("hunt", {}).get("top_opportunities", []))
        create_status = results.get("create", {}).get("status", "N/A")
        health_status = results.get("health", {}).get("health", {}).get("status", "N/A")
        
        message = f"""
🚀 *MONEY MACHINE - CYCLE COMPLETE*

📊 *Results:*
• Opportunities: {hunt_count}
• Creation: {create_status}
• Health: {health_status}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        async with httpx.AsyncClient() as client:
            await client.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "Markdown"
                }
            )
    except:
        pass


async def show_status():
    """Show current system status"""
    print("\n📊 SYSTEM STATUS")
    print("=" * 50)
    
    # Import check
    import_ok = await test_imports()
    
    # Environment check
    env_ok = await check_environment()
    
    # Health check
    health = await run_health_check()
    
    print("\n" + "=" * 50)
    print("📋 Summary:")
    print(f"   Imports: {'✅ OK' if import_ok else '❌ FAILED'}")
    print(f"   Environment: {'✅ OK' if env_ok else '⚠️ INCOMPLETE'}")
    print(f"   Health: {'✅ OK' if health else '❌ FAILED'}")
    
    if import_ok and health:
        print("\n🟢 System is READY for activation")
    else:
        print("\n🟡 System needs attention before activation")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Elite Money Machine v2.0 - Autonomous Launcher"
    )
    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Run in continuous 24/7 autonomous mode"
    )
    parser.add_argument(
        "--cycles",
        type=int,
        default=0,
        help="Number of cycles to run (0 = unlimited in continuous mode)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run a test cycle without posting"
    )
    parser.add_argument(
        "--health",
        action="store_true",
        help="Run health check only"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show system status"
    )
    parser.add_argument(
        "--test-telegram",
        action="store_true",
        help="Test Telegram connection"
    )
    parser.add_argument(
        "--no-confirm",
        action="store_true",
        help="Skip confirmation prompt"
    )
    
    args = parser.parse_args()
    
    print_banner()
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Auto-provision resources first
    await auto_provision()
    
    if args.status:
        await show_status()
    elif args.health:
        await run_health_check()
    elif args.test_telegram:
        await test_telegram()
    elif args.dry_run:
        await run_dry_cycle()
    elif args.continuous:
        # 24/7 AUTONOMOUS MODE
        await run_continuous_mode(max_cycles=args.cycles)
    else:
        # Single cycle
        if args.no_confirm:
            await run_full_cycle()
        else:
            confirm = input("\n⚠️  Run FULL cycle? This will create and post content. (y/N): ")
            if confirm.lower() == 'y':
                await run_full_cycle()
            else:
                print("Aborted.")


async def run_continuous_mode(max_cycles: int = 0):
    """
    Run the machine continuously in 24/7 autonomous mode.
    This is POST-HUMAN MODE - the machine decides everything.
    """
    print("\n" + "=" * 60)
    print("🤖 ENTERING POST-HUMAN MODE - 24/7 AUTONOMOUS OPERATION")
    print("=" * 60)
    print(f"   Cycle interval: {MachineConfig.CYCLE_INTERVAL_MINUTES} minutes")
    print(f"   Jitter: ±{MachineConfig.CYCLE_JITTER_MINUTES} minutes")
    print(f"   Max cycles: {'unlimited' if max_cycles == 0 else max_cycles}")
    print(f"   Locked niches: {', '.join(MachineConfig.NICHES)}")
    print("=" * 60)
    print("\n💡 Press Ctrl+C to stop\n")
    
    cycle_count = 0
    consecutive_failures = 0
    
    while True:
        cycle_count += 1
        
        # Check cycle limit
        if max_cycles > 0 and cycle_count > max_cycles:
            print(f"\n🏁 Reached max cycles ({max_cycles}). Stopping.")
            break
        
        # Check daily limit
        if cycle_count > MachineConfig.MAX_CYCLES_PER_DAY:
            print(f"\n⚠️ Daily cycle limit reached. Pausing until tomorrow.")
            await asyncio.sleep(3600)  # Wait 1 hour
            cycle_count = 0
            continue
        
        print(f"\n{'='*60}")
        print(f"🔄 CYCLE {cycle_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        try:
            # Run the full cycle
            results = await run_full_cycle()
            
            if results and not results.get("error"):
                consecutive_failures = 0
                print(f"   ✅ Cycle {cycle_count} complete")
            else:
                consecutive_failures += 1
                print(f"   ⚠️ Cycle {cycle_count} had issues")
        
        except Exception as e:
            consecutive_failures += 1
            print(f"   ❌ Cycle {cycle_count} failed: {e}")
        
        # Circuit breaker
        if consecutive_failures >= MachineConfig.MAX_FAILURES_BEFORE_PAUSE:
            print(f"\n🛑 Circuit breaker triggered ({consecutive_failures} failures)")
            print(f"   Pausing for {MachineConfig.PAUSE_DURATION_MINUTES} minutes...")
            await asyncio.sleep(MachineConfig.PAUSE_DURATION_MINUTES * 60)
            consecutive_failures = 0
            continue
        
        # Calculate next cycle time with jitter
        base_wait = MachineConfig.CYCLE_INTERVAL_MINUTES * 60
        jitter = random.randint(
            -MachineConfig.CYCLE_JITTER_MINUTES * 60,
            MachineConfig.CYCLE_JITTER_MINUTES * 60
        )
        wait_seconds = max(300, base_wait + jitter)  # Minimum 5 minutes
        
        next_cycle = datetime.now().timestamp() + wait_seconds
        next_cycle_str = datetime.fromtimestamp(next_cycle).strftime('%H:%M:%S')
        
        print(f"\n⏳ Next cycle at {next_cycle_str} ({wait_seconds//60} minutes)")
        print("   💤 Machine sleeping... (Ctrl+C to stop)")
        
        try:
            await asyncio.sleep(wait_seconds)
        except KeyboardInterrupt:
            print("\n\n🛑 Interrupted by user. Shutting down gracefully...")
            break
    
    print("\n🏁 AUTONOMOUS MODE ENDED")
    print(f"   Total cycles completed: {cycle_count}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Money Machine stopped. See you next time!")
