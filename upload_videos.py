"""
============================================================
MONEY MACHINE - MANUAL VIDEO UPLOADER
============================================================
Run this when you have videos ready to upload.
Opens each platform's upload page with your video ready.
============================================================
"""

import os
import sys
import webbrowser
from pathlib import Path
from datetime import datetime

def get_pending_videos():
    """Get all videos that haven't been uploaded yet."""
    output_dir = Path(__file__).parent / "output"
    uploaded_log = output_dir / ".uploaded.txt"
    
    # Get already uploaded
    uploaded = set()
    if uploaded_log.exists():
        uploaded = set(uploaded_log.read_text().strip().split("\n"))
    
    # Find all mp4 files
    videos = []
    if output_dir.exists():
        for f in output_dir.glob("**/*.mp4"):
            if str(f) not in uploaded:
                videos.append(f)
    
    return videos, uploaded_log

def mark_uploaded(video_path, log_file):
    """Mark a video as uploaded."""
    with open(log_file, "a") as f:
        f.write(f"{video_path}\n")

def main():
    print("""
╔══════════════════════════════════════════════════════════╗
║         MONEY MACHINE - VIDEO UPLOADER                   ║
║         Quick Upload to All Platforms                    ║
╚══════════════════════════════════════════════════════════╝
""")
    
    videos, log_file = get_pending_videos()
    
    if not videos:
        print("✅ No pending videos to upload!")
        print("\nRun 'python run.py' to generate more videos.")
        return
    
    print(f"📹 Found {len(videos)} videos ready to upload:\n")
    for i, v in enumerate(videos, 1):
        print(f"  {i}. {v.name}")
    
    print(f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Your channels:
  🎬 YouTube:   https://www.youtube.com/channel/UCZppwcvPrWlAG0vb78elPJA
  📸 Instagram: @valenvox1
  🎵 TikTok:    @itzzz.emoji

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")
    
    for video in videos:
        print(f"\n📹 Uploading: {video.name}")
        print(f"   Path: {video}")
        
        # Extract metadata from filename if possible
        # Format: niche_topic_timestamp.mp4
        parts = video.stem.split("_")
        niche = parts[0] if len(parts) > 0 else "wealth"
        topic = " ".join(parts[1:-1]) if len(parts) > 2 else video.stem
        
        # Generate description
        descriptions = {
            "wealth": f"💰 {topic}\n\n🔥 Follow for daily wealth tips!\n\n#money #wealth #finance #investing #rich #success #millionaire #entrepreneur",
            "health": f"💪 {topic}\n\n🔥 Follow for daily health tips!\n\n#health #fitness #wellness #nutrition #workout #lifestyle #motivation #healthy",
            "survival": f"🏕️ {topic}\n\n🔥 Follow for survival tips!\n\n#survival #prepper #outdoors #camping #emergency #bushcraft #tactical #prepared"
        }
        
        desc = descriptions.get(niche.lower(), descriptions["wealth"])
        
        print(f"\n   Suggested description:\n   {desc[:100]}...")
        
        # Open upload pages
        input("\n   Press Enter to open upload pages...")
        
        # YouTube Studio upload
        webbrowser.open("https://studio.youtube.com/channel/UCZppwcvPrWlAG0vb78elPJA/videos/upload")
        
        # TikTok upload (desktop)
        webbrowser.open("https://www.tiktok.com/creator-center/upload")
        
        # Instagram (mobile only - show instructions)
        print("""
   📱 Instagram (mobile only):
      1. Open Instagram app
      2. Tap + → Reel
      3. Select video from gallery
      4. Add caption and post
""")
        
        # Copy description to clipboard
        try:
            import pyperclip
            pyperclip.copy(desc)
            print("   ✅ Description copied to clipboard!")
        except:
            print(f"\n   Copy this description:\n   {desc}")
        
        done = input("\n   Done uploading this video? (Y/n): ").strip().lower()
        if done != "n":
            mark_uploaded(str(video), log_file)
            print(f"   ✅ Marked as uploaded!")
    
    print(f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ All videos processed!

The machine keeps generating.
Run this script again when you have more videos.

💰 Money incoming...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")

if __name__ == "__main__":
    main()
