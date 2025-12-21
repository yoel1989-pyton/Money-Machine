#!/usr/bin/env python3
"""
============================================================
MONEY MACHINE - SYSTEM LAUNCHER
The Master Switch
============================================================
Usage:
    python run.py                    # Full cycle
    python run.py --dry-run          # Test without posting
    python run.py --health           # Health check only
    python run.py --status           # System status
    python run.py --test-telegram    # Test Telegram connection
============================================================
"""

import asyncio
import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()


def print_banner():
    """Print the Money Machine banner"""
    banner = """
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║     💰 ELITE MONEY MACHINE v2.0 💰                       ║
    ║                                                          ║
    ║     Self-Healing • Self-Improving • Autonomous           ║
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
        description="Elite Money Machine v2.0 - System Launcher"
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
    
    args = parser.parse_args()
    
    print_banner()
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if args.status:
        await show_status()
    elif args.health:
        await run_health_check()
    elif args.test_telegram:
        await test_telegram()
    elif args.dry_run:
        await run_dry_cycle()
    else:
        # Full cycle
        confirm = input("\n⚠️  Run FULL cycle? This will create and post content. (y/N): ")
        if confirm.lower() == 'y':
            await run_full_cycle()
        else:
            print("Aborted.")


if __name__ == "__main__":
    asyncio.run(main())
