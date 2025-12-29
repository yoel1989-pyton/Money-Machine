"""
ANOINTMENT REMIX ENGINE - Railway Backend
==========================================
Handles video remixing for flood content:
- 1.05x speed
- Mirror/crop
- Header text overlay
- Suno music mixing (15-25%)

Endpoints:
    POST /remix - Remix a video for repurposing
    POST /health - Health check
    GET /static/{file} - Serve remixed files
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import subprocess
import os
import requests
import uuid
from datetime import datetime
from pathlib import Path

app = FastAPI(
    title="Anointment Remix Engine",
    description="Video remixing for flood content",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Path("temp").mkdir(exist_ok=True)
Path("static").mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")


class RemixOptions(BaseModel):
    speed: float = Field(default=1.05, ge=0.5, le=2.0)
    mirror: bool = Field(default=True)
    crop_percent: int = Field(default=5, ge=0, le=20)
    add_header: bool = Field(default=True)
    header_text: str = Field(default="🔥")
    music_volume: float = Field(default=0.20, ge=0, le=1.0)
    music_url: Optional[str] = None


class RemixRequest(BaseModel):
    video_url: str
    remix_options: RemixOptions = Field(default_factory=RemixOptions)


class RemixResponse(BaseModel):
    status: str
    remixed_url: str
    task_id: str
    processing_time_ms: int
    changes_applied: Dict[str, Any]


def download_file(url: str, path: str) -> bool:
    """Download a file from URL."""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, stream=True, timeout=60)
        response.raise_for_status()
        with open(path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"Download failed: {e}")
        return False


def remix_video(
    input_path: str,
    output_path: str,
    options: RemixOptions,
    music_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Apply remix transformations to video.
    
    Transformations:
    - Speed adjustment (1.05x = unique fingerprint)
    - Horizontal mirror
    - Crop edges (removes watermarks)
    - Header text overlay
    - Background music mixing
    """
    try:
        # Build filter chain
        filters = []
        
        # Speed adjustment
        if options.speed != 1.0:
            filters.append(f"setpts={1/options.speed}*PTS")
        
        # Mirror (horizontal flip)
        if options.mirror:
            filters.append("hflip")
        
        # Crop edges (removes potential watermarks)
        if options.crop_percent > 0:
            crop = options.crop_percent / 100
            filters.append(f"crop=iw*(1-{crop}):ih*(1-{crop})")
            filters.append("scale=1080:1920:force_original_aspect_ratio=decrease")
            filters.append("pad=1080:1920:(ow-iw)/2:(oh-ih)/2")
        
        # Header text
        if options.add_header and options.header_text:
            safe_text = options.header_text.replace("'", "\\'")
            filters.append(
                f"drawtext=text='{safe_text}':"
                f"fontsize=48:fontcolor=white:"
                f"x=(w-text_w)/2:y=50:"
                f"borderw=2:bordercolor=black"
            )
        
        # Fingerprint breaking (same as anointment)
        filters.extend([
            "eq=brightness=0.02",
            "noise=alls=2:allf=t+u"
        ])
        
        filter_chain = ",".join(filters)
        
        # Build command
        command = [
            'ffmpeg', '-y',
            '-i', input_path
        ]
        
        # Add music if provided
        if music_path and os.path.exists(music_path):
            command.extend(['-i', music_path])
            
            # Mix audio
            audio_filter = (
                f"[0:a]volume=1.0[main];"
                f"[1:a]volume={options.music_volume}[music];"
                f"[main][music]amix=inputs=2:duration=first"
            )
            command.extend(['-filter_complex', audio_filter])
        
        # Video filters
        command.extend(['-vf', filter_chain])
        
        # Speed adjustment for audio
        if options.speed != 1.0:
            command.extend(['-af', f"atempo={options.speed}"])
        
        # Output settings
        command.extend([
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-map_metadata', '-1',
            output_path
        ])
        
        start_time = datetime.now()
        process = subprocess.run(command, capture_output=True, timeout=300)
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        if process.returncode != 0:
            return {
                "success": False,
                "error": process.stderr.decode()[:500],
                "processing_time_ms": processing_time
            }
        
        return {
            "success": True,
            "processing_time_ms": processing_time,
            "changes_applied": {
                "speed": options.speed,
                "mirror": options.mirror,
                "crop_percent": options.crop_percent,
                "header_added": options.add_header,
                "music_mixed": music_path is not None,
                "music_volume": options.music_volume,
                "fingerprint_broken": True
            }
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=10)
        ffmpeg_ok = result.returncode == 0
    except:
        ffmpeg_ok = False
    
    return {
        "status": "operational",
        "ffmpeg_available": ffmpeg_ok,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/remix", response_model=RemixResponse)
async def remix_endpoint(request: RemixRequest):
    """
    Remix a video for flood content repurposing.
    
    Applies:
    - 1.05x speed (fingerprint breaking)
    - Horizontal mirror
    - Edge cropping
    - Header text overlay
    - Optional music mixing
    """
    task_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    input_file = f"temp/{task_id}_input.mp4"
    music_file = f"temp/{task_id}_music.mp3" if request.remix_options.music_url else None
    output_file = f"static/remixed_{timestamp}_{task_id}.mp4"
    
    # Download video
    if not download_file(request.video_url, input_file):
        raise HTTPException(status_code=400, detail="Failed to download video")
    
    # Download music if provided
    if request.remix_options.music_url:
        if not download_file(request.remix_options.music_url, music_file):
            music_file = None  # Continue without music
    
    # Remix
    result = remix_video(input_file, output_file, request.remix_options, music_file)
    
    # Cleanup
    try:
        os.remove(input_file)
        if music_file and os.path.exists(music_file):
            os.remove(music_file)
    except:
        pass
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=f"Remix failed: {result.get('error')}")
    
    railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "localhost:8000")
    protocol = "https" if "railway" in railway_domain else "http"
    
    return RemixResponse(
        status="success",
        remixed_url=f"{protocol}://{railway_domain}/{output_file}",
        task_id=task_id,
        processing_time_ms=int(result["processing_time_ms"]),
        changes_applied=result["changes_applied"]
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
