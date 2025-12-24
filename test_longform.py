#!/usr/bin/env python3
"""
Quick test script for longform documentary production.
Bypasses terminal timeout issues.
"""
import asyncio
import sys
import os
from pathlib import Path

# Fix Windows encoding
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent))

from workflows.longform_mode import LongformMode

async def main():
    topic = "Why the Middle Class is Disappearing by Design"
    print(f"\n[LONGFORM TEST] Topic: {topic}\n")
    
    longform = LongformMode()
    result = await longform.produce_elite_documentary(topic)
    
    if result:
        print(f"\n[SUCCESS] {result}")
    else:
        print("\n[FAILED]")

if __name__ == "__main__":
    asyncio.run(main())
