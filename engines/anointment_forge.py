"""
ANOINTMENT PROTOCOL - Railway Backend (The Forge)
==================================================
Handles the heavy computational tasks:
- Video transcoding
- Metadata stripping
- Cryptographic obfuscation ("Anointment")

Endpoints:
    POST /anoint - Process a video for cross-platform distribution
    POST /health - Health check
    GET /static/{file} - Serve anointed files

The "Anointment" breaks both:
- Cryptographic hashing (MD5/SHA) - exact file matches
- Perceptual hashing (pHash) - visual similarity detection
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import subprocess
import os
import requests
import uuid
import json
from datetime import datetime
from pathlib import Path

app = FastAPI(
    title="Anointment Forge",
    description="Video fingerprint obfuscation service",
    version="1.0.0"
)

# CORS for n8n access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure directories exist
Path("temp").mkdir(exist_ok=True)
Path("static").mkdir(exist_ok=True)

# Mount static files for serving anointed videos
app.mount("/static", StaticFiles(directory="static"), name="static")


# ============================================================
# PYDANTIC SCHEMAS (Fix for 422 errors)
# ============================================================
# These schemas MUST match exactly what n8n sends
# No double-serialization - arrays stay arrays, objects stay objects

class ProcessingRequest(BaseModel):
    """Input schema for /anoint endpoint"""
    video_url: str = Field(..., description="URL to the source video")
    publish_platform: str = Field(default="all", description="Target platform(s)")
    
    # Optional metadata - n8n can pass these as objects, not stringified JSON
    metadata: Optional[Dict[str, Any]] = Field(default=None)
    tags: Optional[List[str]] = Field(default=None)
    caption: Optional[str] = Field(default=None)

    class Config:
        # Allow extra fields without failing
        extra = "ignore"


class AnointmentResponse(BaseModel):
    """Output schema for /anoint endpoint"""
    status: str
    anointed_url: str
    task_id: str
    processing_time_ms: int
    fingerprint_changes: Dict[str, Any]


class HealthResponse(BaseModel):
    status: str
    ffmpeg_available: bool
    storage_mb_free: float
    timestamp: str


# ============================================================
# ANOINTMENT ENGINE (The Core)
# ============================================================

def check_ffmpeg() -> bool:
    """Verify FFmpeg is installed and accessible."""
    try:
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            timeout=10
        )
        return result.returncode == 0
    except Exception:
        return False


def anoint_video(input_path: str, output_path: str) -> Dict[str, Any]:
    """
    Applies imperceptible filters to alter video fingerprint.
    
    Obfuscation techniques:
    1. eq=brightness=0.01 - Changes every pixel's hex value
    2. noise=alls=1 - Disrupts edge-detection algorithms
    3. setpts=PTS/1.01 - Desynchronizes timeline
    4. -map_metadata -1 - Strips XMP/platform tags
    
    Returns:
        Dict with processing details and success status
    """
    try:
        command = [
            'ffmpeg',
            '-y',  # Overwrite output
            '-i', input_path,
            
            # VIDEO FILTER CHAIN (The Anointment)
            '-vf', ','.join([
                'eq=brightness=0.01',           # +1% brightness (imperceptible)
                'noise=alls=1:allf=t+u',        # Random noise injection
                'setpts=PTS/1.01',              # 1% time desync
            ]),
            
            # AUDIO PROCESSING
            '-af', 'aecho=0.8:0.88:6:0.1',     # Subtle audio fingerprint change
            
            # METADATA STRIPPING (Critical for avoiding flags)
            '-map_metadata', '-1',              # Remove all metadata
            '-fflags', '+bitexact',             # Deterministic output
            
            # ENCODING SETTINGS
            '-c:v', 'libx264',
            '-preset', 'veryfast',              # Balance speed/quality
            '-crf', '26',                       # Slight compression difference
            '-c:a', 'aac',
            '-b:a', '128k',
            
            # OUTPUT
            output_path
        ]
        
        start_time = datetime.now()
        process = subprocess.run(
            command,
            capture_output=True,
            timeout=300  # 5 minute timeout
        )
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        if process.returncode != 0:
            error_msg = process.stderr.decode()[:500]
            return {
                "success": False,
                "error": error_msg,
                "processing_time_ms": processing_time
            }
        
        return {
            "success": True,
            "processing_time_ms": processing_time,
            "fingerprint_changes": {
                "brightness_shift": 0.01,
                "noise_injection": True,
                "time_desync": 0.01,
                "metadata_stripped": True,
                "audio_modified": True
            }
        }
        
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Processing timeout (300s)"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================
# API ENDPOINTS
# ============================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for monitoring."""
    import shutil
    
    total, used, free = shutil.disk_usage("/")
    
    return HealthResponse(
        status="operational",
        ffmpeg_available=check_ffmpeg(),
        storage_mb_free=free / (1024 * 1024),
        timestamp=datetime.now().isoformat()
    )


@app.post("/anoint", response_model=AnointmentResponse)
async def anoint_endpoint(request: ProcessingRequest):
    """
    Main anointment endpoint.
    
    Accepts a video URL, downloads it, applies fingerprint obfuscation,
    and returns a public URL to the anointed file.
    
    This endpoint is designed to work with n8n HTTP Request nodes.
    
    Example n8n expression (CORRECT - no double serialization):
        {
            "video_url": "{{ $json.download_url }}",
            "tags": {{ $json.hashtags }},  // Array, not stringified
            "metadata": {{ $json.meta }}   // Object, not stringified
        }
    """
    # Generate unique IDs for isolation
    task_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    input_file = f"temp/{task_id}_raw.mp4"
    output_file = f"static/anointed_{timestamp}_{task_id}.mp4"
    
    # ============================================================
    # STEP 1: Download Content
    # ============================================================
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(
            request.video_url,
            headers=headers,
            stream=True,
            timeout=60
        )
        response.raise_for_status()
        
        with open(input_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
    except requests.RequestException as e:
        raise HTTPException(
            status_code=400,
            detail=f"Download failed: {str(e)}"
        )
    
    # ============================================================
    # STEP 2: Execute Anointment (FFmpeg)
    # ============================================================
    result = anoint_video(input_file, output_file)
    
    # Clean up raw file regardless of success
    try:
        os.remove(input_file)
    except:
        pass
    
    if not result.get("success"):
        raise HTTPException(
            status_code=500,
            detail=f"Anointment failed: {result.get('error')}"
        )
    
    # ============================================================
    # STEP 3: Return Public URL
    # ============================================================
    railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "localhost:8000")
    protocol = "https" if "railway" in railway_domain else "http"
    
    return AnointmentResponse(
        status="success",
        anointed_url=f"{protocol}://{railway_domain}/{output_file}",
        task_id=task_id,
        processing_time_ms=int(result["processing_time_ms"]),
        fingerprint_changes=result["fingerprint_changes"]
    )


@app.post("/batch-anoint")
async def batch_anoint(videos: List[Dict[str, str]]):
    """
    Batch process multiple videos.
    
    Input: [{"video_url": "...", "id": "clip_01"}, ...]
    Output: [{"id": "clip_01", "anointed_url": "...", "status": "success"}, ...]
    """
    results = []
    
    for video in videos:
        try:
            request = ProcessingRequest(video_url=video.get("video_url", ""))
            response = await anoint_endpoint(request)
            results.append({
                "id": video.get("id", "unknown"),
                "anointed_url": response.anointed_url,
                "status": "success"
            })
        except HTTPException as e:
            results.append({
                "id": video.get("id", "unknown"),
                "error": e.detail,
                "status": "failed"
            })
    
    return {"results": results, "processed": len(results)}


# ============================================================
# CLEANUP TASK
# ============================================================

@app.on_event("startup")
async def startup_cleanup():
    """Clean up old files on startup."""
    import glob
    from datetime import timedelta
    
    # Remove files older than 24 hours
    cutoff = datetime.now() - timedelta(hours=24)
    
    for pattern in ["temp/*", "static/anointed_*"]:
        for filepath in glob.glob(pattern):
            try:
                file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                if file_time < cutoff:
                    os.remove(filepath)
            except:
                pass


# ============================================================
# LOCAL TESTING
# ============================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
