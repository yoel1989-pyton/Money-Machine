#!/usr/bin/env python3
"""
UPLOAD_QUEUE.py - Upload Queue Manager
=======================================
Manages the upload queue for produced videos.

Usage:
    python UPLOAD_QUEUE.py --list          # List pending uploads
    python UPLOAD_QUEUE.py --upload 3      # Upload next 3 videos
    python UPLOAD_QUEUE.py --upload-all    # Upload all pending
    python UPLOAD_QUEUE.py --preview       # Preview next video
    python UPLOAD_QUEUE.py --clear         # Clear failed uploads
"""

import sys
import json
import argparse
import asyncio
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from engines.error_handler import send_success_alert

load_dotenv()

MANIFEST_PATH = Path("data/output/upload_queue.json")
QUEUE_DIR = Path("data/output/queue")


def log(msg: str, level: str = "INFO"):
    ts = datetime.now().strftime("%H:%M:%S")
    prefix = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "WARN": "⚠️"}.get(level, "•")
    print(f"[{ts}] {prefix} {msg}")


def load_manifest() -> dict:
    if MANIFEST_PATH.exists():
        return json.loads(MANIFEST_PATH.read_text())
    return {"pending": [], "uploaded": [], "failed": []}


def save_manifest(manifest: dict):
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2))


def list_queue():
    """List all videos in queue"""
    manifest = load_manifest()
    
    print("\n" + "="*70)
    print("   📋 UPLOAD QUEUE STATUS")
    print("="*70)
    
    print(f"\n📦 PENDING ({len(manifest['pending'])} videos):")
    for i, v in enumerate(manifest["pending"], 1):
        print(f"   {i}. {v['topic'][:45]}")
        print(f"      📁 {v['filename']} | {v['size_mb']} MB | {v['duration']:.0f}s")
    
    if manifest["uploaded"]:
        print(f"\n✅ UPLOADED ({len(manifest['uploaded'])} videos):")
        for v in manifest["uploaded"][-5:]:  # Show last 5
            print(f"   • {v['topic'][:45]}")
            print(f"     🔗 {v.get('url', 'No URL')}")
    
    if manifest["failed"]:
        print(f"\n❌ FAILED ({len(manifest['failed'])} videos):")
        for v in manifest["failed"]:
            print(f"   • {v['topic'][:45]}")
            print(f"     ⚠️ {v.get('error', 'Unknown error')[:50]}")
    
    print("\n" + "="*70 + "\n")


def preview_next():
    """Preview the next video to upload"""
    manifest = load_manifest()
    
    if not manifest["pending"]:
        log("No videos in queue", "WARN")
        return
    
    v = manifest["pending"][0]
    
    print("\n" + "="*60)
    print("   🎬 NEXT VIDEO PREVIEW")
    print("="*60)
    print(f"\n📹 Topic: {v['topic']}")
    print(f"🎯 Archetype: {v['archetype']}")
    print(f"📁 File: {v['filename']}")
    print(f"📊 Size: {v['size_mb']} MB | Duration: {v['duration']:.1f}s")
    print(f"📅 Created: {v['created']}")
    print(f"\n📝 Title: {v['title']}")
    print(f"\n📋 Description:\n{v['description']}")
    print(f"\n✍️ Script:\n{v['script'][:500]}...")
    print("\n" + "="*60 + "\n")


async def upload_videos(count: int = 1):
    """Upload videos from queue to YouTube"""
    manifest = load_manifest()
    
    if not manifest["pending"]:
        log("No videos in queue", "WARN")
        return
    
    try:
        from engines.uploaders import MasterUploader
        uploader = MasterUploader()
    except Exception as e:
        log(f"Failed to init uploader: {e}", "ERROR")
        return
    
    uploaded = 0
    to_upload = manifest["pending"][:count]
    
    for v in to_upload:
        log(f"Uploading: {v['topic'][:40]}...")
        
        try:
            video_path = Path(v["path"])
            if not video_path.exists():
                # Try queue dir
                video_path = QUEUE_DIR / v["filename"]
            
            if not video_path.exists():
                log(f"Video file not found: {v['filename']}", "ERROR")
                v["error"] = "File not found"
                manifest["failed"].append(v)
                manifest["pending"].remove(v)
                continue
            
            result = await uploader.upload_youtube_only(
                video_path=str(video_path),
                title=v["title"][:100],
                description=v["description"],
                tags=["shorts", "money", "finance", "investing"]
            )
            
            if result and result.get("success"):
                v["url"] = result.get("url", "Uploaded")
                v["uploaded_at"] = datetime.now().isoformat()
                v["status"] = "uploaded"
                manifest["uploaded"].append(v)
                manifest["pending"].remove(v)
                uploaded += 1
                log(f"✅ Uploaded: {v['topic'][:40]}", "SUCCESS")
            else:
                error = result.get("error", "Unknown") if result else "No result"
                
                # Check for rate limit
                if "uploadLimitExceeded" in str(error):
                    log("YouTube upload limit reached - stopping", "WARN")
                    break
                
                v["error"] = str(error)[:200]
                v["status"] = "failed"
                manifest["failed"].append(v)
                manifest["pending"].remove(v)
                log(f"❌ Failed: {error[:50]}", "ERROR")
                
        except Exception as e:
            v["error"] = str(e)[:200]
            manifest["failed"].append(v)
            manifest["pending"].remove(v)
            log(f"❌ Error: {e}", "ERROR")
    
    save_manifest(manifest)
    log(f"Uploaded {uploaded}/{len(to_upload)} videos")
    
    if uploaded > 0:
        send_success_alert(
            f"Upload Complete!\n\n"
            f"✅ Uploaded: {uploaded} videos\n"
            f"📋 Remaining: {len(manifest['pending'])} pending"
        )


def clear_failed():
    """Clear failed uploads (move back to pending or delete)"""
    manifest = load_manifest()
    
    if not manifest["failed"]:
        log("No failed uploads to clear", "INFO")
        return
    
    count = len(manifest["failed"])
    
    # Move back to pending for retry
    for v in manifest["failed"]:
        v.pop("error", None)
        v["status"] = "pending"
        manifest["pending"].append(v)
    
    manifest["failed"] = []
    save_manifest(manifest)
    
    log(f"Cleared {count} failed uploads - moved back to pending", "SUCCESS")


def open_queue_folder():
    """Open the queue folder in file explorer"""
    import subprocess
    subprocess.run(["explorer", str(QUEUE_DIR.absolute())])
    log(f"Opened: {QUEUE_DIR.absolute()}")


def main():
    parser = argparse.ArgumentParser(description="Upload Queue Manager")
    parser.add_argument("--list", action="store_true", help="List pending uploads")
    parser.add_argument("--upload", type=int, metavar="N", help="Upload next N videos")
    parser.add_argument("--upload-all", action="store_true", help="Upload all pending")
    parser.add_argument("--preview", action="store_true", help="Preview next video")
    parser.add_argument("--clear", action="store_true", help="Clear failed uploads")
    parser.add_argument("--open", action="store_true", help="Open queue folder")
    args = parser.parse_args()
    
    if args.list:
        list_queue()
    elif args.upload:
        asyncio.run(upload_videos(args.upload))
    elif args.upload_all:
        manifest = load_manifest()
        asyncio.run(upload_videos(len(manifest["pending"])))
    elif args.preview:
        preview_next()
    elif args.clear:
        clear_failed()
    elif args.open:
        open_queue_folder()
    else:
        # Default: show list
        list_queue()
        print("Commands:")
        print("  python UPLOAD_QUEUE.py --list          # List queue")
        print("  python UPLOAD_QUEUE.py --upload 3      # Upload 3 videos")
        print("  python UPLOAD_QUEUE.py --upload-all    # Upload all")
        print("  python UPLOAD_QUEUE.py --preview       # Preview next")
        print("  python UPLOAD_QUEUE.py --open          # Open folder")


if __name__ == "__main__":
    main()
