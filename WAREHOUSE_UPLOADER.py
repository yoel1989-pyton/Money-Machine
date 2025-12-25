#!/usr/bin/env python3
"""
WAREHOUSE_UPLOADER.py - Flush Local Videos to YouTube
======================================================
Run this when your YouTube quota resets to upload all warehoused videos.

Usage:
    python WAREHOUSE_UPLOADER.py              # Upload all pending
    python WAREHOUSE_UPLOADER.py --test       # Dry run (no upload)
    python WAREHOUSE_UPLOADER.py --limit 5    # Upload max 5 videos
"""

import os
import sys
import asyncio
import argparse
import shutil
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from engines.error_handler import send_success_alert

load_dotenv()

# Directories
QUEUE_DIR = Path("data/output/queue")
PUBLISHED_DIR = Path("data/output/published")
FAILED_DIR = Path("data/output/failed")

PUBLISHED_DIR.mkdir(parents=True, exist_ok=True)
FAILED_DIR.mkdir(parents=True, exist_ok=True)


def log(msg: str, level: str = "INFO"):
    ts = datetime.now().strftime("%H:%M:%S")
    prefix = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "WARN": "⚠️"}.get(level, "•")
    print(f"[{ts}] {prefix} {msg}")


async def flush_warehouse(limit: int = None, dry_run: bool = False):
    """Upload all videos from warehouse to YouTube"""
    
    # Get all mp4 files
    videos = list(QUEUE_DIR.glob("*.mp4"))
    
    if not videos:
        log("No videos in warehouse queue", "WARN")
        return
    
    if limit:
        videos = videos[:limit]
    
    log(f"Found {len(videos)} videos to upload")
    
    if dry_run:
        log("DRY RUN - No uploads will be made", "WARN")
        for v in videos:
            size_mb = v.stat().st_size / (1024 * 1024)
            log(f"  Would upload: {v.name} ({size_mb:.1f} MB)")
        return
    
    # Initialize uploader
    try:
        from engines.uploaders import MasterUploader
        uploader = MasterUploader()
    except Exception as e:
        log(f"Failed to initialize uploader: {e}", "ERROR")
        return
    
    uploaded = 0
    failed = 0
    quota_hit = False
    
    for video in videos:
        if quota_hit:
            break
            
        name = video.stem
        size_mb = video.stat().st_size / (1024 * 1024)
        
        # Generate title from filename
        title_parts = name.replace("elite_", "").replace("_", " ").split()
        # Remove timestamp parts
        title_parts = [p for p in title_parts if not p.isdigit() and len(p) > 2]
        title = " ".join(title_parts[:8]) + " #shorts #money #finance"
        
        description = f"""🔥 {' '.join(title_parts[:8])}

💰 Subscribe for daily wealth wisdom!

#shorts #finance #money #investing #wealth #financialfreedom #millionaire"""

        log(f"Uploading: {video.name} ({size_mb:.1f} MB)")
        
        try:
            result = await uploader.upload_youtube_only(
                video_path=str(video),
                title=title[:100],
                description=description,
                tags=["shorts", "money", "finance", "investing", "wealth"]
            )
            
            if result and result.get("success"):
                # Move to published folder
                dest = PUBLISHED_DIR / video.name
                shutil.move(str(video), str(dest))
                uploaded += 1
                log(f"✅ Published: {video.name}", "SUCCESS")
                
            else:
                error = result.get("error", "") if result else "Unknown"
                
                # Check for quota limit
                if "uploadLimitExceeded" in str(error) or "quota" in str(error).lower():
                    log("🛑 YouTube quota limit reached - stopping uploads", "WARN")
                    quota_hit = True
                else:
                    # Move to failed folder
                    dest = FAILED_DIR / video.name
                    shutil.move(str(video), str(dest))
                    failed += 1
                    log(f"❌ Failed: {error[:50]}", "ERROR")
                    
        except Exception as e:
            if "quota" in str(e).lower() or "limit" in str(e).lower():
                log("🛑 YouTube quota limit - stopping", "WARN")
                quota_hit = True
            else:
                dest = FAILED_DIR / video.name
                shutil.move(str(video), str(dest))
                failed += 1
                log(f"❌ Error: {e}", "ERROR")
    
    # Summary
    remaining = len(list(QUEUE_DIR.glob("*.mp4")))
    
    print("\n" + "="*60)
    print(f"   📊 WAREHOUSE FLUSH COMPLETE")
    print(f"   ✅ Uploaded: {uploaded}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📦 Remaining: {remaining}")
    if quota_hit:
        print(f"   ⚠️ Quota limit hit - run again later")
    print("="*60 + "\n")
    
    # Telegram notification
    send_success_alert(
        f"Warehouse Flush Complete!\n\n"
        f"✅ Uploaded: {uploaded}\n"
        f"❌ Failed: {failed}\n"
        f"📦 Remaining: {remaining}"
    )


def main():
    parser = argparse.ArgumentParser(description="Upload warehoused videos to YouTube")
    parser.add_argument("--test", action="store_true", help="Dry run - don't upload")
    parser.add_argument("--limit", type=int, help="Max videos to upload")
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("   📦 WAREHOUSE UPLOADER")
    print("   Flushing local videos to YouTube")
    print("="*60 + "\n")
    
    asyncio.run(flush_warehouse(limit=args.limit, dry_run=args.test))


if __name__ == "__main__":
    main()
