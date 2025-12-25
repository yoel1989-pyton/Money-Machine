#!/usr/bin/env python3
"""
════════════════════════════════════════════════════════════════════════════════
🎬 MONEY MACHINE WEBHOOK RECEIVER
Receives triggers from n8n Cloud to assemble videos locally with FFmpeg
════════════════════════════════════════════════════════════════════════════════
"""

import os
import json
import asyncio
import subprocess
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import requests
import threading

load_dotenv()

app = Flask(__name__)

# Configuration
DATA_DIR = Path("data")
TEMP_DIR = DATA_DIR / "temp"
OUTPUT_DIR = DATA_DIR / "output"
ASSETS_DIR = DATA_DIR / "assets" / "backgrounds"

# Ensure directories exist
TEMP_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def download_file(url: str, output_path: Path) -> bool:
    """Download a file from URL"""
    try:
        response = requests.get(url, stream=True, timeout=120)
        response.raise_for_status()
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"✅ Downloaded: {output_path}")
        return True
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return False

def get_random_background() -> Path:
    """Get a random background video from assets"""
    import random
    backgrounds = []
    
    # Search all subdirectories for mp4 files
    for category in ASSETS_DIR.iterdir():
        if category.is_dir():
            backgrounds.extend(list(category.glob("*.mp4")))
    
    if not backgrounds:
        # Fallback to any mp4 in the backgrounds folder
        backgrounds = list(ASSETS_DIR.glob("**/*.mp4"))
    
    if backgrounds:
        return random.choice(backgrounds)
    
    raise FileNotFoundError("No background videos found!")

def assemble_video(audio_path: Path, output_path: Path, topic: str = "") -> dict:
    """Assemble video using FFmpeg with Elite quality settings"""
    try:
        # Get background video
        background = get_random_background()
        print(f"🎬 Using background: {background.name}")
        
        # Elite FFmpeg command
        cmd = [
            "ffmpeg", "-y",
            "-stream_loop", "-1",
            "-i", str(background),
            "-i", str(audio_path),
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-shortest",
            "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,eq=contrast=1.08:saturation=1.12:brightness=0.02",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "18",
            "-b:v", "8M",
            "-minrate", "6M",
            "-maxrate", "10M",
            "-bufsize", "16M",
            "-c:a", "aac",
            "-b:a", "192k",
            str(output_path)
        ]
        
        print(f"🔧 Running FFmpeg...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0 and output_path.exists():
            # Get video info
            probe_cmd = [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration,bit_rate",
                "-of", "json",
                str(output_path)
            ]
            probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)
            probe_data = json.loads(probe_result.stdout) if probe_result.returncode == 0 else {}
            
            return {
                "success": True,
                "video_path": str(output_path),
                "duration": probe_data.get("format", {}).get("duration"),
                "bitrate": probe_data.get("format", {}).get("bit_rate"),
                "size_mb": round(output_path.stat().st_size / (1024 * 1024), 2),
                "background_used": background.name
            }
        else:
            return {
                "success": False,
                "error": result.stderr[-500:] if result.stderr else "Unknown FFmpeg error"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def upload_to_youtube(video_path: Path, title: str, description: str, tags: list) -> dict:
    """Upload video to YouTube using the existing uploader"""
    try:
        from engines.uploaders import YouTubeUploader
        
        uploader = YouTubeUploader()
        if not uploader.is_configured():
            return {"success": False, "error": "YouTube not configured"}
        
        result = uploader.upload_short(
            video_path=str(video_path),
            title=title,
            description=description,
            tags=tags
        )
        
        return result
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Money Machine Webhook Receiver"
    })

@app.route('/webhook/assemble-video', methods=['POST'])
def webhook_assemble_video():
    """
    Webhook endpoint to receive video assembly requests from n8n
    
    Expected payload:
    {
        "audio_url": "https://drive.google.com/...",
        "topic": "Why the Rich Use Debt",
        "archetype": "system_reveal",
        "title": "Video Title",
        "description": "Video description",
        "tags": ["money", "wealth"],
        "upload_to_youtube": true
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "error": "No JSON payload"}), 400
        
        audio_url = data.get("audio_url")
        topic = data.get("topic", "Money Machine Video")
        upload_to_yt = data.get("upload_to_youtube", False)
        
        if not audio_url:
            return jsonify({"success": False, "error": "audio_url required"}), 400
        
        # Generate filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        audio_filename = f"n8n_{timestamp}_voice.mp3"
        video_filename = f"n8n_{timestamp}_video.mp4"
        
        audio_path = TEMP_DIR / audio_filename
        video_path = OUTPUT_DIR / video_filename
        
        # Download audio
        print(f"📥 Downloading audio from: {audio_url[:50]}...")
        if not download_file(audio_url, audio_path):
            return jsonify({"success": False, "error": "Failed to download audio"}), 500
        
        # Assemble video
        print(f"🎬 Assembling video for: {topic}")
        result = assemble_video(audio_path, video_path, topic)
        
        if not result["success"]:
            return jsonify(result), 500
        
        # Optionally upload to YouTube
        if upload_to_yt:
            print(f"📤 Uploading to YouTube...")
            yt_result = upload_to_youtube(
                video_path=video_path,
                title=data.get("title", topic),
                description=data.get("description", ""),
                tags=data.get("tags", [])
            )
            result["youtube"] = yt_result
        
        # Cleanup audio file
        try:
            audio_path.unlink()
        except:
            pass
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/webhook/full-pipeline', methods=['POST'])
def webhook_full_pipeline():
    """
    Full pipeline: Generate script → TTS → Video → Upload
    
    Expected payload:
    {
        "topic": "Why the Rich Use Debt",
        "archetype": "system_reveal",
        "upload": true
    }
    """
    try:
        data = request.get_json() or {}
        topic = data.get("topic")
        
        if not topic:
            return jsonify({"success": False, "error": "topic required"}), 400
        
        # Import and run the continuous mode
        from workflows.continuous_mode import ContinuousMode
        
        mode = ContinuousMode()
        result = mode.run_single(
            topic=topic,
            archetype=data.get("archetype"),
            force_upload=data.get("upload", False)
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ════════════════════════════════════════════════════════════════════════════════
# 🎬 SHOTSTACK CLOUD VIDEO ASSEMBLY
# ════════════════════════════════════════════════════════════════════════════════

SHOTSTACK_API_KEY = os.getenv('SHOTSTACK_API_KEY', '')
SHOTSTACK_BASE_URL = 'https://api.shotstack.io/edit/v1'

@app.route('/webhook/shotstack-render', methods=['POST'])
def webhook_shotstack_render():
    """
    Render video using Shotstack cloud API - no local FFmpeg required
    
    Expected payload:
    {
        "audio_url": "https://drive.google.com/...",
        "topic": "Why the Rich Use Debt",
        "upload_to_youtube": true
    }
    """
    try:
        if not SHOTSTACK_API_KEY:
            return jsonify({
                "success": False, 
                "error": "SHOTSTACK_API_KEY not configured in .env"
            }), 500
        
        data = request.get_json() or {}
        audio_url = data.get("audio_url")
        topic = data.get("topic", "Money Machine")
        
        if not audio_url:
            return jsonify({"success": False, "error": "audio_url required"}), 400
        
        # Shotstack render payload for YouTube Shorts (9:16)
        payload = {
            "timeline": {
                "background": "#000000",
                "tracks": [
                    {
                        "clips": [
                            {
                                "asset": {
                                    "type": "audio",
                                    "src": audio_url
                                },
                                "start": 0,
                                "length": "auto"
                            }
                        ]
                    },
                    {
                        "clips": [
                            {
                                "asset": {
                                    "type": "video",
                                    "src": "https://shotstack-assets.s3.amazonaws.com/footage/abstract-dark-blue.mp4",
                                    "volume": 0
                                },
                                "start": 0,
                                "length": "auto",
                                "fit": "cover"
                            }
                        ]
                    },
                    {
                        "clips": [
                            {
                                "asset": {
                                    "type": "title",
                                    "text": topic,
                                    "style": "future",
                                    "size": "medium",
                                    "position": "bottom"
                                },
                                "start": 0,
                                "length": 3,
                                "transition": {
                                    "in": "fade",
                                    "out": "fade"
                                }
                            }
                        ]
                    }
                ]
            },
            "output": {
                "format": "mp4",
                "resolution": "1080",
                "aspectRatio": "9:16",
                "fps": 30,
                "quality": "high"
            }
        }
        
        # Submit render job
        headers = {
            'x-api-key': SHOTSTACK_API_KEY,
            'Content-Type': 'application/json'
        }
        
        print(f"🎬 Submitting to Shotstack...")
        response = requests.post(
            f"{SHOTSTACK_BASE_URL}/render",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code not in [200, 201]:
            return jsonify({
                "success": False, 
                "error": f"Shotstack error: {response.text}"
            }), 500
        
        render_data = response.json()
        render_id = render_data.get('response', {}).get('id')
        
        if not render_id:
            return jsonify({
                "success": False,
                "error": "No render_id received"
            }), 500
        
        print(f"✅ Render submitted: {render_id}")
        
        # Poll for completion (with timeout)
        video_url = poll_shotstack_render(render_id, timeout=300)
        
        if not video_url:
            return jsonify({
                "success": True,
                "status": "processing",
                "render_id": render_id,
                "message": f"Render still processing. Check status at /webhook/shotstack-status/{render_id}"
            })
        
        result = {
            "success": True,
            "render_id": render_id,
            "video_url": video_url
        }
        
        # Optionally upload to YouTube
        if data.get("upload_to_youtube") and video_url:
            print(f"📤 Uploading to YouTube...")
            yt_result = upload_shotstack_to_youtube(
                video_url,
                title=data.get("title", topic),
                description=data.get("description", ""),
                tags=data.get("tags", [])
            )
            result["youtube"] = yt_result
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/webhook/shotstack-status/<render_id>', methods=['GET'])
def webhook_shotstack_status(render_id):
    """Check status of a Shotstack render"""
    try:
        if not SHOTSTACK_API_KEY:
            return jsonify({"success": False, "error": "SHOTSTACK_API_KEY not configured"}), 500
        
        headers = {'x-api-key': SHOTSTACK_API_KEY}
        response = requests.get(
            f"{SHOTSTACK_BASE_URL}/render/{render_id}", 
            headers=headers,
            timeout=30
        )
        
        if response.status_code != 200:
            return jsonify({"success": False, "error": f"Shotstack error: {response.text}"}), 500
        
        data = response.json().get('response', {})
        
        return jsonify({
            "success": True,
            "render_id": render_id,
            "status": data.get('status'),
            "video_url": data.get('url'),
            "progress": data.get('progress', 0)
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def poll_shotstack_render(render_id: str, timeout: int = 300, interval: int = 5):
    """Poll Shotstack until render is complete"""
    import time
    
    headers = {'x-api-key': SHOTSTACK_API_KEY}
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(
                f"{SHOTSTACK_BASE_URL}/render/{render_id}", 
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json().get('response', {})
                status = data.get('status')
                
                if status == 'done':
                    print(f"✅ Render complete: {render_id}")
                    return data.get('url')
                elif status == 'failed':
                    print(f"❌ Render failed: {data.get('error')}")
                    return None
                else:
                    print(f"⏳ Render {status}: {data.get('progress', 0)}%")
            
            time.sleep(interval)
            
        except Exception as e:
            print(f"⚠️ Poll error: {e}")
            time.sleep(interval)
    
    print(f"⏰ Render timeout after {timeout}s")
    return None


def upload_shotstack_to_youtube(video_url: str, title: str, description: str, tags: list) -> dict:
    """Download video from Shotstack and upload to YouTube"""
    try:
        import tempfile
        
        # Download to temp file
        print(f"📥 Downloading from Shotstack...")
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
            response = requests.get(video_url, stream=True, timeout=120)
            for chunk in response.iter_content(chunk_size=8192):
                tmp.write(chunk)
            tmp_path = Path(tmp.name)
        
        # Upload to YouTube
        result = upload_to_youtube(tmp_path, title, description, tags)
        
        # Cleanup
        try:
            tmp_path.unlink()
        except:
            pass
        
        return result
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def run_server(host='0.0.0.0', port=5678):
    """Run the webhook server"""
    shotstack_status = "✅ Configured" if SHOTSTACK_API_KEY else "⚠️ Not configured (add SHOTSTACK_API_KEY to .env)"
    
    print(f"""
╔════════════════════════════════════════════════════════════════╗
║        💰 MONEY MACHINE WEBHOOK RECEIVER 💰                    ║
╠════════════════════════════════════════════════════════════════╣
║  Endpoints:                                                     ║
║    GET  /health                     - Health check              ║
║    POST /webhook/assemble-video     - Local FFmpeg assembly     ║
║    POST /webhook/shotstack-render   - Cloud Shotstack render    ║
║    GET  /webhook/shotstack-status/  - Check render status       ║
║    POST /webhook/full-pipeline      - Run full content pipeline ║
╠════════════════════════════════════════════════════════════════╣
║  Shotstack: {shotstack_status:47}║
║  Server: http://{host}:{port}                                  ║
╠════════════════════════════════════════════════════════════════╣
║  💡 To expose to internet: ngrok http {port}                    ║
╚════════════════════════════════════════════════════════════════╝
    """)
    app.run(host=host, port=port, debug=False, threaded=True)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Money Machine Webhook Receiver")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5678, help="Port to listen on")
    
    args = parser.parse_args()
    run_server(host=args.host, port=args.port)
