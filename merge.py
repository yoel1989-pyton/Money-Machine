"""
FINVID OMNI MERGE - Universal Merge Script (FINAL)
===================================================
Merges all OPAL clips into a single MP4.

Usage:
    python merge.py
    python merge.py --input opal_output/2025-12-28_143052
    python merge.py --output my_video.mp4
"""

import os
import subprocess
import argparse
import json
from pathlib import Path


def find_latest_opal_output():
    """Find the most recent OPAL output folder."""
    opal_base = Path("data/opal_output")
    if not opal_base.exists():
        return None
    
    folders = sorted(opal_base.iterdir(), reverse=True)
    for folder in folders:
        if (folder / "clips").exists() and (folder / "manifest.json").exists():
            return folder
    
    # Fallback: just look for clips folder
    for folder in folders:
        if (folder / "clips").exists():
            return folder
    
    return None


def merge_clips(clips_dir: Path, output_file: str = "final_video.mp4"):
    """Merge all clips in directory using FFmpeg concat."""
    
    # Get sorted list of clips
    clips = sorted([
        f for f in os.listdir(clips_dir)
        if f.endswith(".mp4")
    ])
    
    if not clips:
        print("❌ No clips found in:", clips_dir)
        return False
    
    print(f"📹 Found {len(clips)} clips")
    
    # Create concat file
    concat_file = "clips.txt"
    with open(concat_file, "w") as f:
        for clip in clips:
            clip_path = clips_dir / clip
            f.write(f"file '{clip_path}'\n")
    
    print(f"📝 Created {concat_file}")
    
    # Run FFmpeg
    cmd = [
        "ffmpeg",
        "-y",  # Overwrite output
        "-f", "concat",
        "-safe", "0",
        "-i", concat_file,
        "-c", "copy",
        output_file
    ]
    
    print(f"🔧 Running FFmpeg...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"\n✅ FINAL VIDEO CREATED: {output_file}")
        # Clean up
        os.remove(concat_file)
        return True
    else:
        print(f"❌ FFmpeg failed:")
        print(result.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="Merge OPAL clips into final video")
    parser.add_argument(
        "--input", "-i",
        help="Path to OPAL output folder (default: latest)"
    )
    parser.add_argument(
        "--output", "-o",
        default="final_video.mp4",
        help="Output filename (default: final_video.mp4)"
    )
    args = parser.parse_args()
    
    # Find clips directory
    if args.input:
        opal_dir = Path(args.input)
        clips_dir = opal_dir / "clips" if (opal_dir / "clips").exists() else opal_dir
    else:
        opal_dir = find_latest_opal_output()
        if not opal_dir:
            print("❌ No OPAL output found. Run OPAL first or specify --input")
            return
        clips_dir = opal_dir / "clips"
    
    print(f"\n{'='*60}")
    print(f"🎬 FINVID OMNI MERGE")
    print(f"{'='*60}")
    print(f"📁 Input:  {clips_dir}")
    print(f"📤 Output: {args.output}")
    print()
    
    # Show manifest info if available
    manifest_file = opal_dir / "manifest.json"
    if manifest_file.exists():
        with open(manifest_file) as f:
            manifest = json.load(f)
        print(f"📊 Manifest: {len(manifest.get('clip_order', []))} clips, {manifest.get('total_duration', 0):.1f}s total")
        if not manifest.get("assembly_ready", True):
            print(f"⚠️  Warning: Some clips may be missing")
        print()
    
    # Merge
    success = merge_clips(clips_dir, args.output)
    
    if success:
        print(f"\n🎯 Your video is ready: {args.output}")
        print("   → Upload to Runway for cinematic polish (optional)")
        print("   → Or publish directly to YouTube")


if __name__ == "__main__":
    main()
