"""
===============================================================================
VISUAL ADAPTERS - Multi-Provider Hollywood Visual Generation
===============================================================================
Connects to ALL paid visual APIs for scene-based generation.
Each provider generates unique visuals. No reuse. No loops.

PROVIDERS:
- Leonardo AI (anime, stylized)
- Runway ML (gen4_image)
- Fal.ai (Flux dev)
- Replicate (SDXL, Flux)
- Kie AI (Flux Kontext)
- Stability AI (hyperreal)
- Local Fallback (gradient frames)
===============================================================================
"""

import os
import json
import asyncio
import httpx
import time
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from collections import defaultdict

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# ============================================================================
# RATE LIMITING & CONCURRENCY CONTROL
# ============================================================================

class RateLimiter:
    """Per-provider rate limiting to prevent API throttling."""
    
    # Rate limits per provider (requests per minute)
    RATE_LIMITS = {
        "stability": 10,
        "fal": 20,
        "replicate": 10,
        "runway": 10,
        "kie": 15,
        "leonardo": 10,
        "local": 100,  # No real limit for local
    }
    
    # Minimum delay between requests (seconds)
    MIN_DELAY = {
        "stability": 2.0,
        "fal": 1.5,
        "replicate": 3.0,  # Replicate is more sensitive
        "runway": 2.0,
        "kie": 2.0,
        "leonardo": 2.0,
        "local": 0.1,
    }
    
    def __init__(self):
        self._last_request: Dict[str, float] = defaultdict(float)
        self._request_counts: Dict[str, list] = defaultdict(list)
        self._locks: Dict[str, asyncio.Lock] = {}
    
    def _get_lock(self, provider: str) -> asyncio.Lock:
        if provider not in self._locks:
            self._locks[provider] = asyncio.Lock()
        return self._locks[provider]
    
    async def wait_if_needed(self, provider: str):
        """Wait if we're hitting rate limits."""
        async with self._get_lock(provider):
            now = time.time()
            
            # Enforce minimum delay
            min_delay = self.MIN_DELAY.get(provider, 1.0)
            time_since_last = now - self._last_request[provider]
            if time_since_last < min_delay:
                await asyncio.sleep(min_delay - time_since_last)
            
            # Clean old request timestamps (older than 1 minute)
            self._request_counts[provider] = [
                t for t in self._request_counts[provider]
                if now - t < 60
            ]
            
            # Check rate limit
            rate_limit = self.RATE_LIMITS.get(provider, 10)
            if len(self._request_counts[provider]) >= rate_limit:
                # Wait until oldest request expires
                oldest = self._request_counts[provider][0]
                wait_time = 60 - (now - oldest) + 0.5
                if wait_time > 0:
                    print(f"[RateLimit] {provider}: waiting {wait_time:.1f}s")
                    await asyncio.sleep(wait_time)
            
            # Record this request
            self._last_request[provider] = time.time()
            self._request_counts[provider].append(time.time())


# Global rate limiter instance
_rate_limiter = RateLimiter()


# ============================================================================
# PROVIDER PRIORITY WEIGHTS (Battle Mode Selection)
# ============================================================================
# Higher weight = more likely to be selected for battle mode
# This ensures visual diversity and quality optimization

PROVIDER_PRIORITY = {
    "leonardo": 1.3,   # Highest - anime/stylized diversity
    "runway": 1.2,     # High - cinematic quality
    "kie": 1.1,        # Medium-high - Flux Kontext quality
    "fal": 1.0,        # Baseline
    "stability": 0.9,  # Support role
    "replicate": 0.8,  # Backup/experimental
    "local": 0.1,      # Only fallback
}

# Style mutation tracking
STYLE_FAMILIES = {
    "dark": ["noir", "shadow", "gothic", "horror"],
    "cinematic": ["film_grain", "dramatic", "epic", "blockbuster"],
    "anime": ["anime_dark", "manga", "cel_shaded", "stylized"],
    "abstract": ["surreal", "dreamscape", "ethereal", "cosmic"],
    "hyperreal": ["photorealistic", "ultra_hd", "documentary", "raw"],
}


# ============================================================================
# DIRECTORIES
# ============================================================================

BASE_DIR = Path(__file__).parent.parent
SCENES_DIR = BASE_DIR / "data" / "scenes"
TEMP_DIR = BASE_DIR / "data" / "temp"

SCENES_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# RESULT DATACLASS
# ============================================================================

@dataclass
class GenerationResult:
    """Result from visual generation."""
    success: bool
    provider: str
    path: Optional[str] = None
    error: Optional[str] = None
    duration: float = 0.0
    metadata: Optional[Dict] = None


# ============================================================================
# PROVIDER ADAPTERS
# ============================================================================

class LeonardoAdapter:
    """Leonardo AI - Anime and stylized visuals."""
    
    def __init__(self):
        self.api_key = os.getenv("LEONARDO_API_KEY") or os.getenv("LEONARDO_AI_API_KEY")
        self.base_url = "https://cloud.leonardo.ai/api/rest/v1"
        
    async def generate(self, prompt: str, output_path: str, style: str = "anime_dark") -> GenerationResult:
        if not self.api_key:
            return GenerationResult(success=False, provider="leonardo", error="No API key")
        
        # Rate limiting
        await _rate_limiter.wait_if_needed("leonardo")
        
        start = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                # Create generation
                # Use Leonardo Kino XL for cinematic results
                response = await client.post(
                    f"{self.base_url}/generations",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "prompt": prompt,
                        "negative_prompt": "text, words, letters, watermark, logo, blurry, low quality",
                        "modelId": "aa77f04e-3eec-4034-9c07-d0f619684628",  # Leonardo Kino XL
                        "width": 576,
                        "height": 1024,
                        "num_images": 1,
                        "guidance_scale": 7
                    }
                )
                
                if response.status_code != 200:
                    return GenerationResult(
                        success=False, provider="leonardo",
                        error=f"API error: {response.status_code} - {response.text[:200]}"
                    )
                
                data = response.json()
                generation_id = data.get("sdGenerationJob", {}).get("generationId")
                
                if not generation_id:
                    return GenerationResult(success=False, provider="leonardo", error="No generation ID")
                
                # Poll for completion
                for _ in range(60):
                    await asyncio.sleep(2)
                    
                    status_response = await client.get(
                        f"{self.base_url}/generations/{generation_id}",
                        headers={"Authorization": f"Bearer {self.api_key}"}
                    )
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        images = status_data.get("generations_by_pk", {}).get("generated_images", [])
                        
                        if images and images[0].get("url"):
                            image_url = images[0]["url"]
                            
                            # Download image
                            img_response = await client.get(image_url)
                            if img_response.status_code == 200:
                                Path(output_path).write_bytes(img_response.content)
                                return GenerationResult(
                                    success=True,
                                    provider="leonardo",
                                    path=output_path,
                                    duration=time.time() - start,
                                    metadata={"model": "dreamshaper", "style": style}
                                )
                
                return GenerationResult(success=False, provider="leonardo", error="Timeout waiting for generation")
                
        except Exception as e:
            return GenerationResult(success=False, provider="leonardo", error=str(e))


class RunwayAdapter:
    """Runway ML - Image generation using Gen4."""
    
    def __init__(self):
        self.api_key = os.getenv("RUNWAYML_API_KEY")
        self.base_url = "https://api.dev.runwayml.com/v1"  # CORRECT endpoint
        
    async def generate(self, prompt: str, output_path: str, style: str = "cinematic", duration: int = 4) -> GenerationResult:
        if not self.api_key:
            return GenerationResult(success=False, provider="runway", error="No API key")
        
        # Rate limiting
        await _rate_limiter.wait_if_needed("runway")
        
        start = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=300) as client:
                # Use text_to_image endpoint - gen4_image model
                response = await client.post(
                    f"{self.base_url}/text_to_image",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "X-Runway-Version": "2024-11-06",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gen4_image",
                        "promptText": prompt,
                        "ratio": "720:1280"  # Portrait 9:16
                    }
                )
                
                if response.status_code != 200:
                    error_msg = response.text[:200] if response.text else f"Status {response.status_code}"
                    return GenerationResult(
                        success=False, provider="runway",
                        error=f"API error: {error_msg}"
                    )
                
                data = response.json()
                task_id = data.get("id")
                
                if not task_id:
                    return GenerationResult(success=False, provider="runway", error="No task ID")
                
                # Poll for completion
                for _ in range(120):
                    await asyncio.sleep(3)
                    
                    status_response = await client.get(
                        f"{self.base_url}/tasks/{task_id}",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "X-Runway-Version": "2024-11-06"
                        }
                    )
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        status = status_data.get("status", "").upper()
                        
                        if status == "SUCCEEDED":
                            # Get image URL from output
                            output = status_data.get("output", [])
                            image_url = output[0] if output else None
                            
                            if image_url:
                                img_response = await client.get(image_url)
                                if img_response.status_code == 200:
                                    # Save as PNG
                                    output_png = output_path.replace(".mp4", ".png") if output_path.endswith(".mp4") else output_path
                                    Path(output_png).write_bytes(img_response.content)
                                    return GenerationResult(
                                        success=True,
                                        provider="runway",
                                        path=output_png,
                                        duration=time.time() - start,
                                        metadata={"model": "gen4_image"}
                                    )
                        
                        elif status == "FAILED":
                            error_detail = status_data.get("failure", status_data.get("error", "Generation failed"))
                            return GenerationResult(
                                success=False, provider="runway",
                                error=str(error_detail)
                            )
                
                return GenerationResult(success=False, provider="runway", error="Timeout")
                
        except Exception as e:
            return GenerationResult(success=False, provider="runway", error=str(e))


class FalAdapter:
    """Fal.ai - Flux and abstract visuals."""
    
    def __init__(self):
        self.api_key = os.getenv("FAL_API_KEY")
        self.base_url = "https://queue.fal.run"
        
    async def generate(self, prompt: str, output_path: str, style: str = "abstract") -> GenerationResult:
        if not self.api_key:
            return GenerationResult(success=False, provider="fal", error="No API key")
        
        # Rate limiting
        await _rate_limiter.wait_if_needed("fal")
        
        start = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=180) as client:
                # Submit to queue - use fal-ai/flux/dev for dev model
                response = await client.post(
                    f"{self.base_url}/fal-ai/flux/dev",
                    headers={
                        "Authorization": f"Key {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "prompt": prompt,
                        "image_size": "portrait_16_9",
                        "num_inference_steps": 28,
                        "guidance_scale": 3.5,
                        "num_images": 1,
                        "enable_safety_checker": False
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Direct response with image (synchronous completion)
                    images = data.get("images", [])
                    if images and images[0].get("url"):
                        img_response = await client.get(images[0]["url"])
                        if img_response.status_code == 200:
                            Path(output_path).write_bytes(img_response.content)
                            return GenerationResult(
                                success=True,
                                provider="fal",
                                path=output_path,
                                duration=time.time() - start,
                                metadata={"model": "flux-dev"}
                            )
                    
                    # Queue response - use response_url directly (correct path)
                    request_id = data.get("request_id")
                    response_url = data.get("response_url")  # Use the URL from response
                    
                    if request_id and response_url:
                        for _ in range(60):
                            await asyncio.sleep(3)
                            
                            # Get result directly using the provided response_url
                            result_response = await client.get(
                                response_url,
                                headers={"Authorization": f"Key {self.api_key}"}
                            )
                            
                            if result_response.status_code == 200:
                                result_data = result_response.json()
                                images = result_data.get("images", [])
                                if images and images[0].get("url"):
                                    img_response = await client.get(images[0]["url"])
                                    if img_response.status_code == 200:
                                        Path(output_path).write_bytes(img_response.content)
                                        return GenerationResult(
                                            success=True,
                                            provider="fal",
                                            path=output_path,
                                            duration=time.time() - start,
                                            metadata={"model": "flux-dev"}
                                        )
                            elif result_response.status_code == 202:
                                # Still processing, continue polling
                                continue
                            elif result_response.status_code == 400:
                                # Request not completed yet, continue
                                continue
                            else:
                                # Error
                                return GenerationResult(
                                    success=False, provider="fal",
                                    error=f"Poll error: {result_response.status_code}"
                                )
                        
                        return GenerationResult(success=False, provider="fal", error="Timeout")
                
                return GenerationResult(
                    success=False, provider="fal",
                    error=f"API error: {response.status_code}" if response.status_code != 200 else "No images in response"
                )
                
        except Exception as e:
            return GenerationResult(success=False, provider="fal", error=str(e))


class ReplicateAdapter:
    """Replicate - SDXL and experimental models."""
    
    def __init__(self):
        self.api_key = os.getenv("REPLICATE_API_TOKEN")
        self.base_url = "https://api.replicate.com/v1"
        
    async def generate(self, prompt: str, output_path: str, style: str = "cinematic") -> GenerationResult:
        if not self.api_key:
            return GenerationResult(success=False, provider="replicate", error="No API key")
        
        # Rate limiting - Replicate is sensitive to rate limits
        await _rate_limiter.wait_if_needed("replicate")
        
        start = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                # Use Flux Schnell for fast generation
                response = await client.post(
                    f"{self.base_url}/predictions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "version": "39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
                        "input": {
                            "prompt": prompt,
                            "negative_prompt": "text, words, watermark, blurry, low quality",
                            "width": 576,
                            "height": 1024,
                            "num_outputs": 1,
                            "guidance_scale": 7.5
                        }
                    }
                )
                
                if response.status_code not in [200, 201]:
                    return GenerationResult(
                        success=False, provider="replicate",
                        error=f"API error: {response.status_code}"
                    )
                
                data = response.json()
                prediction_url = data.get("urls", {}).get("get")
                
                if not prediction_url:
                    return GenerationResult(success=False, provider="replicate", error="No prediction URL")
                
                # Poll for completion
                for _ in range(60):
                    await asyncio.sleep(2)
                    
                    status_response = await client.get(
                        prediction_url,
                        headers={"Authorization": f"Bearer {self.api_key}"}
                    )
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        
                        if status_data.get("status") == "succeeded":
                            output = status_data.get("output", [])
                            if output:
                                img_url = output[0] if isinstance(output, list) else output
                                img_response = await client.get(img_url)
                                if img_response.status_code == 200:
                                    Path(output_path).write_bytes(img_response.content)
                                    return GenerationResult(
                                        success=True,
                                        provider="replicate",
                                        path=output_path,
                                        duration=time.time() - start,
                                        metadata={"model": "flux-schnell"}
                                    )
                        
                        elif status_data.get("status") == "failed":
                            return GenerationResult(
                                success=False, provider="replicate",
                                error=status_data.get("error", "Failed")
                            )
                
                return GenerationResult(success=False, provider="replicate", error="Timeout")
                
        except Exception as e:
            return GenerationResult(success=False, provider="replicate", error=str(e))


class StabilityAdapter:
    """Stability AI - Hyperrealistic visuals."""
    
    def __init__(self):
        self.api_key = os.getenv("STABILITY_API_KEY")
        self.base_url = "https://api.stability.ai/v2beta"
        
    async def generate(self, prompt: str, output_path: str, style: str = "hyperreal") -> GenerationResult:
        if not self.api_key:
            return GenerationResult(success=False, provider="stability", error="No API key")
        
        # Rate limiting
        await _rate_limiter.wait_if_needed("stability")
        
        start = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(
                    f"{self.base_url}/stable-image/generate/core",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Accept": "image/*"
                    },
                    files={"none": ("", "")},
                    data={
                        "prompt": prompt,
                        "negative_prompt": "text, words, watermark, blurry",
                        "aspect_ratio": "9:16",
                        "output_format": "png"
                    }
                )
                
                if response.status_code == 200:
                    Path(output_path).write_bytes(response.content)
                    return GenerationResult(
                        success=True,
                        provider="stability",
                        path=output_path,
                        duration=time.time() - start,
                        metadata={"model": "stable-image-core"}
                    )
                
                return GenerationResult(
                    success=False, provider="stability",
                    error=f"API error: {response.status_code}"
                )
                
        except Exception as e:
            return GenerationResult(success=False, provider="stability", error=str(e))


class KieAdapter:
    """Kie AI - Flux Kontext image generation."""
    
    def __init__(self):
        self.api_key = os.getenv("KIE_API_KEY") or os.getenv("KIE_AI_API_KEY")
        self.base_url = "https://api.kie.ai/api/v1/flux/kontext"  # Correct Flux Kontext endpoint
        
    async def generate(self, prompt: str, output_path: str, style: str = "cinematic") -> GenerationResult:
        if not self.api_key:
            return GenerationResult(success=False, provider="kie", error="No API key")
        
        # Rate limiting
        await _rate_limiter.wait_if_needed("kie")
        
        start = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=180) as client:
                # Generate image using Flux Kontext
                response = await client.post(
                    f"{self.base_url}/generate",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "prompt": prompt,
                        "aspectRatio": "9:16",  # Portrait for shorts
                        "model": "flux-kontext-pro",
                        "outputFormat": "png",
                        "enableTranslation": False,  # Prompts already in English
                        "promptUpsampling": True  # AI enhancement
                    }
                )
                
                if response.status_code != 200:
                    error_text = response.text[:200] if response.text else f"Status {response.status_code}"
                    return GenerationResult(
                        success=False, provider="kie",
                        error=f"API error: {error_text}"
                    )
                
                data = response.json()
                
                if data.get("code") != 200:
                    return GenerationResult(
                        success=False, provider="kie",
                        error=f"API error: {data.get('msg', 'Unknown error')}"
                    )
                
                task_id = data.get("data", {}).get("taskId")
                
                if not task_id:
                    return GenerationResult(success=False, provider="kie", error="No task ID")
                
                # Poll for completion
                for _ in range(60):
                    await asyncio.sleep(3)
                    
                    status_response = await client.get(
                        f"{self.base_url}/record-info?taskId={task_id}",
                        headers={"Authorization": f"Bearer {self.api_key}"}
                    )
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        
                        if status_data.get("code") == 200:
                            info = status_data.get("data", {})
                            success_flag = info.get("successFlag")
                            
                            if success_flag == 1:  # SUCCESS
                                response_data = info.get("response", {})
                                image_url = response_data.get("resultImageUrl")
                                
                                if image_url:
                                    img_response = await client.get(image_url)
                                    if img_response.status_code == 200:
                                        output_png = output_path.replace(".mp4", ".png") if output_path.endswith(".mp4") else output_path
                                        Path(output_png).write_bytes(img_response.content)
                                        return GenerationResult(
                                            success=True,
                                            provider="kie",
                                            path=output_png,
                                            duration=time.time() - start,
                                            metadata={"model": "flux-kontext-pro"}
                                        )
                            
                            elif success_flag in [2, 3]:  # FAILED
                                error_msg = info.get("errorMessage", "Generation failed")
                                return GenerationResult(
                                    success=False, provider="kie",
                                    error=error_msg
                                )
                            # else: still generating (0), continue polling
                
                return GenerationResult(success=False, provider="kie", error="Timeout")
                
        except Exception as e:
            return GenerationResult(success=False, provider="kie", error=str(e))


class LocalFallbackAdapter:
    """Local fallback - Generates high-entropy gradient frames with noise."""
    
    # Style-specific gradient colors
    STYLE_PALETTES = {
        "cinematic": [("0x0f0f23", "0x1a1a3e"), ("0x1e1e2e", "0x2a2a4e"), ("0x0d0d1a", "0x1f1f3d")],
        "anime": [("0x1a1a2e", "0x4a0080"), ("0x0d0d2e", "0x660066"), ("0x1a0033", "0x330066")],
        "abstract": [("0x2a0a3a", "0x0a2a3a"), ("0x3a1a0a", "0x0a1a3a"), ("0x1a3a1a", "0x1a1a3a")],
        "motion": [("0x0a0a1a", "0x2a2a4a"), ("0x1a0a0a", "0x1a2a2a"), ("0x0a1a0a", "0x2a2a3a")],
        "glitch": [("0x00ff00", "0x000000"), ("0xff0000", "0x000000"), ("0x0000ff", "0x000000")],
        "documentary": [("0x1a1a1a", "0x3a3a3a"), ("0x0f0f0f", "0x2f2f2f"), ("0x1a1a2a", "0x3a3a4a")],
        "default": [("0x0f0f1f", "0x2f1f3f"), ("0x1f0f1f", "0x1f2f3f"), ("0x1f1f0f", "0x3f2f1f")],
    }
    
    def __init__(self):
        self.broll_dir = BASE_DIR / "data" / "assets" / "backgrounds"
        
    def _get_gradient_colors(self, style: str) -> tuple:
        """Get gradient colors based on style."""
        import random
        style_key = style.lower() if style.lower() in self.STYLE_PALETTES else "default"
        return random.choice(self.STYLE_PALETTES[style_key])
        
    async def generate(self, prompt: str, output_path: str, style: str = "") -> GenerationResult:
        """Generate from local B-roll assets or create high-entropy gradient frames."""
        
        start = time.time()
        
        try:
            # Find available backgrounds
            backgrounds = []
            if self.broll_dir.exists():
                backgrounds = list(self.broll_dir.glob("*.mp4")) + list(self.broll_dir.glob("*.png")) + list(self.broll_dir.glob("*.jpg"))
            
            if backgrounds:
                # Use random background - prefer existing high-quality assets
                import random
                import shutil
                
                bg = random.choice(backgrounds)
                shutil.copy(bg, output_path)
                
                return GenerationResult(
                    success=True,
                    provider="local",
                    path=output_path,
                    duration=time.time() - start,
                    metadata={"source": str(bg)}
                )
            
            # No backgrounds available - generate high-entropy gradient with noise
            # This creates visually complex frames that maintain bitrate
            import random
            
            color1, color2 = self._get_gradient_colors(style)
            output_png = output_path.replace(".mp4", ".png") if output_path.endswith(".mp4") else output_path
            
            # Add grain/noise for visual complexity (high entropy = better bitrate)
            # Also add subtle vignette for cinematic look
            noise_level = random.uniform(0.015, 0.03)  # Subtle film grain
            
            # Complex filter with gradient + noise + vignette
            filter_complex = (
                f"gradients=size=1080x1920:c0={color1}:c1={color2}:duration=1,"
                f"noise=alls={int(noise_level * 100)}:allf=t,"
                f"vignette=PI/4,"
                f"format=yuv420p"
            )
            
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi",
                "-i", filter_complex,
                "-frames:v", "1",
                "-q:v", "1",  # Highest quality JPEG
                output_png
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            _, stderr = await process.communicate()
            
            # Fallback if gradients filter not available (older FFmpeg)
            if not Path(output_png).exists():
                # Use simpler color + noise approach
                cmd_fallback = [
                    "ffmpeg", "-y",
                    "-f", "lavfi",
                    "-i", f"color=c={color1}:s=1080x1920:d=1",
                    "-vf", (
                        f"noise=alls={int(noise_level * 100)}:allf=t,"
                        f"vignette=PI/4,"
                        f"format=yuv420p"
                    ),
                    "-frames:v", "1",
                    "-q:v", "1",
                    output_png
                ]
                
                process = await asyncio.create_subprocess_exec(
                    *cmd_fallback, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )
                await process.communicate()
            
            if Path(output_png).exists():
                return GenerationResult(
                    success=True,
                    provider="local",
                    path=output_png,
                    duration=time.time() - start,
                    metadata={"type": "gradient_noise", "style": style}
                )
            
            return GenerationResult(success=False, provider="local", error="Failed to generate frame")
            
        except Exception as e:
            return GenerationResult(success=False, provider="local", error=str(e))


# ============================================================================
# UNIFIED GENERATOR
# ============================================================================

class HollywoodVisualFactory:
    """
    Unified factory for Hollywood visual generation.
    Routes to appropriate provider and handles fallbacks.
    """
    
    def __init__(self):
        self.adapters = {
            "leonardo": LeonardoAdapter(),
            "runway": RunwayAdapter(),
            "fal": FalAdapter(),
            "replicate": ReplicateAdapter(),
            "stability": StabilityAdapter(),
            "kie": KieAdapter(),
            "local": LocalFallbackAdapter(),
            "shotstack": LocalFallbackAdapter(),  # Shotstack is for video assembly, not generation
        }
        
        # Track provider status
        self.provider_status = {}
        for name in self.adapters:
            self.provider_status[name] = {"failures": 0, "successes": 0}
    
    async def generate_scene(
        self,
        scene,  # HollywoodScene from planner
        video_id: str
    ) -> GenerationResult:
        """Generate visual for a single scene."""
        
        provider = scene.provider
        output_ext = ".mp4" if provider in ["runway", "kie"] else ".png"
        output_path = str(SCENES_DIR / f"{video_id}_scene_{scene.file_index}{output_ext}")
        
        adapter = self.adapters.get(provider)
        
        if not adapter:
            adapter = self.adapters["local"]
            provider = "local"
        
        # Try primary provider
        result = await adapter.generate(scene.prompt, output_path)
        
        if result.success:
            self.provider_status[provider]["successes"] += 1
            scene.image_path = result.path
            scene.generated = True
            return result
        
        # Fallback to local
        self.provider_status[provider]["failures"] += 1
        print(f"⚠️ {provider} failed for scene {scene.file_index}: {result.error}")
        
        local_result = await self.adapters["local"].generate(scene.prompt, output_path, scene.style)
        if local_result.success:
            scene.image_path = local_result.path
            scene.generated = True
        
        return local_result
    
    async def battle_generate_scene(
        self,
        scene,  # HollywoodScene from planner
        video_id: str,
        competitors: int = 3  # Increased to 3 for better quality selection
    ) -> GenerationResult:
        """
        PROVIDER BATTLE MODE - Generate from multiple providers, pick the best.
        
        This is Hollywood logic: always pit providers against each other.
        Uses weighted selection based on PROVIDER_PRIORITY for diversity.
        """
        
        import random
        
        # Select competing providers
        available_providers = [
            name for name, adapter in self.adapters.items()
            if name not in ["local", "shotstack"] and 
            hasattr(adapter, 'api_key') and adapter.api_key
        ]
        
        if len(available_providers) < competitors:
            # Not enough providers, fall back to normal generation
            return await self.generate_scene(scene, video_id)
        
        # WEIGHTED SELECTION - Use PROVIDER_PRIORITY for smarter selection
        def weighted_choice(providers: list) -> str:
            weights = [PROVIDER_PRIORITY.get(p, 1.0) for p in providers]
            total = sum(weights)
            r = random.random() * total
            cumulative = 0
            for p, w in zip(providers, weights):
                cumulative += w
                if r <= cumulative:
                    return p
            return providers[-1]
        
        # Pick weighted competitors including the assigned provider
        battle_providers = [scene.provider] if scene.provider in available_providers else []
        
        while len(battle_providers) < competitors:
            remaining = [p for p in available_providers if p not in battle_providers]
            if not remaining:
                break
            battle_providers.append(weighted_choice(remaining))
        
        print(f"🎬 Battle Mode: {battle_providers} competing for scene {scene.file_index}")
        
        # Generate from all competitors in parallel
        async def try_provider(provider_name: str):
            output_ext = ".mp4" if provider_name in ["runway", "kie"] else ".png"
            output_path = str(SCENES_DIR / f"{video_id}_scene_{scene.file_index}_{provider_name}{output_ext}")
            
            adapter = self.adapters.get(provider_name)
            if not adapter:
                return None
            
            try:
                result = await adapter.generate(scene.prompt, output_path, scene.style)
                if result.success:
                    # Score the result
                    result.metadata = result.metadata or {}
                    result.metadata["score"] = await self._score_visual(result.path)
                    return result
            except Exception as e:
                print(f"⚠️ Battle: {provider_name} crashed: {e}")
            
            return None
        
        # Run battle
        tasks = [try_provider(p) for p in battle_providers]
        results = await asyncio.gather(*tasks)
        
        # Pick winner (highest score)
        valid_results = [r for r in results if r and r.success]
        
        if not valid_results:
            # All failed, use local fallback
            return await self.generate_scene(scene, video_id)
        
        # Select best result
        winner = max(valid_results, key=lambda r: r.metadata.get("score", 0))
        
        # Update scene
        scene.image_path = winner.path
        scene.generated = True
        scene.provider = winner.provider  # Record actual winning provider
        
        self.provider_status[winner.provider]["successes"] += 1
        
        # Clean up losers
        for r in valid_results:
            if r.path != winner.path and Path(r.path).exists():
                try:
                    Path(r.path).unlink()
                except Exception:
                    pass
        
        return winner
    
    async def _score_visual(self, path: str) -> float:
        """
        Score a visual based on quality metrics.
        Higher score = better visual for selection.
        """
        import subprocess
        
        if not path or not Path(path).exists():
            return 0.0
        
        try:
            # Use FFmpeg to analyze visual complexity
            result = subprocess.run([
                "ffprobe", "-v", "error",
                "-show_entries", "stream=width,height,codec_name,pix_fmt",
                "-show_entries", "format=size,bit_rate",
                "-of", "json",
                path
            ], capture_output=True, text=True, timeout=10)
            
            data = json.loads(result.stdout)
            
            score = 50.0  # Base score
            
            # Prefer larger file sizes (more detail)
            size = int(data.get("format", {}).get("size", 0))
            if size > 500000:  # > 500KB
                score += 20
            elif size > 200000:  # > 200KB
                score += 10
            
            # Prefer video over image (more motion)
            codec = data.get("streams", [{}])[0].get("codec_name", "")
            if codec in ["h264", "hevc", "av1", "vp9"]:
                score += 20  # Video has motion
            
            # Resolution bonus
            width = int(data.get("streams", [{}])[0].get("width", 0))
            height = int(data.get("streams", [{}])[0].get("height", 0))
            if width >= 1080 and height >= 1920:
                score += 10
            
            return score
            
        except Exception:
            return 50.0  # Default neutral score

    async def generate_all_scenes(
        self,
        scenes: list,  # List of HollywoodScene
        video_id: str,
        parallel: int = 3,
        battle_mode: bool = False
    ) -> list:
        """Generate all scene visuals with parallelism."""
        
        semaphore = asyncio.Semaphore(parallel)
        
        async def generate_with_semaphore(scene):
            async with semaphore:
                if battle_mode:
                    return await self.battle_generate_scene(scene, video_id)
                return await self.generate_scene(scene, video_id)
        
        tasks = [generate_with_semaphore(s) for s in scenes]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to failed results
        final_results = []
        for i, r in enumerate(results):
            if isinstance(r, Exception):
                final_results.append(GenerationResult(
                    success=False,
                    provider="unknown",
                    error=str(r)
                ))
            else:
                final_results.append(r)
        
        return final_results
    
    def get_status_report(self) -> dict:
        """Get provider status report."""
        return {
            name: {
                "available": hasattr(self.adapters[name], 'api_key') and bool(getattr(self.adapters[name], 'api_key', True)),
                **status
            }
            for name, status in self.provider_status.items()
        }


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================

async def generate_scene_visual(scene, video_id: str) -> GenerationResult:
    """Quick function to generate a single scene visual."""
    factory = HollywoodVisualFactory()
    return await factory.generate_scene(scene, video_id)


if __name__ == "__main__":
    # Test adapters
    print("🎨 Visual Adapters Status:")
    
    factory = HollywoodVisualFactory()
    for name, adapter in factory.adapters.items():
        has_key = hasattr(adapter, 'api_key') and bool(getattr(adapter, 'api_key', None))
        status = "✅" if has_key or name == "local" else "❌ No API key"
        print(f"  {name}: {status}")
