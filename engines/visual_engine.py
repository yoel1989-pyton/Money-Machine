"""
===============================================================================
VISUAL ENGINE - AI-Powered Scene-Based Image Generation
===============================================================================
Generates unique visuals for each scene using multiple AI providers.
Rotates providers to avoid fingerprinting.

Providers:
- Stability AI (Stable Diffusion Ultra)
- Replicate (Flux, SDXL)
- Leonardo AI (via webhook)
- Local fallback (B-roll)
===============================================================================
"""

import os
import json
import asyncio
import httpx
import random
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

# Load environment variables from .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Directories
TEMP_DIR = Path(__file__).parent.parent / "data" / "temp"
SCENE_VISUALS_DIR = Path(__file__).parent.parent / "data" / "temp" / "scene_visuals"
BROLL_DIR = Path(__file__).parent.parent / "data" / "assets" / "backgrounds"

TEMP_DIR.mkdir(parents=True, exist_ok=True)
SCENE_VISUALS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class VisualResult:
    """Result from visual generation."""
    path: str
    provider: str
    prompt: str
    success: bool
    error: Optional[str] = None
    metadata: Optional[Dict] = None


@dataclass 
class SceneVisual:
    """Visual for a single scene."""
    scene_index: int
    text: str
    intent: str
    style: str
    image_path: Optional[str] = None
    provider: Optional[str] = None
    generated: bool = False


# Visual style presets for different archetypes
STYLE_PRESETS = {
    "anime_dark": {
        "prefix": "Anime-style cinematic illustration, dark moody atmosphere, high contrast",
        "suffix": "dramatic shadows, sharp focus, vertical composition 9:16, no text, no watermark",
        "negative": "low quality, blurry, text, watermark, signature, bright colors, happy, cheerful"
    },
    "cinematic": {
        "prefix": "Cinematic film still, professional cinematography, dramatic lighting",
        "suffix": "film grain, 8k resolution, vertical composition 9:16, no text",
        "negative": "cartoon, anime, low quality, blurry, text, watermark"
    },
    "system_expose": {
        "prefix": "Dark documentary aesthetic, surveillance footage style, dystopian",
        "suffix": "high contrast, dramatic shadows, vertical 9:16, mysterious",
        "negative": "bright, happy, colorful, cartoon, low quality, text"
    },
    "power_finance": {
        "prefix": "Luxury wealth aesthetic, dark moody lighting, power imagery",
        "suffix": "gold accents, dramatic shadows, vertical 9:16, cinematic",
        "negative": "poor, cheap, low quality, bright, cartoon, text"
    },
    "collapse": {
        "prefix": "Dystopian collapse scene, ruins, decay, abandoned",
        "suffix": "atmospheric fog, dramatic lighting, vertical 9:16, cinematic",
        "negative": "happy, bright, colorful, cartoon, text"
    },
    "luxury_wealth": {
        "prefix": "Ultra luxury aesthetic, wealth and opulence, dark moody",
        "suffix": "gold and black, dramatic lighting, vertical 9:16",
        "negative": "poor, cheap, bright, cartoon, text"
    },
    "psychology": {
        "prefix": "Abstract psychological imagery, surreal mind visualization",
        "suffix": "dark moody, high contrast, vertical 9:16, artistic",
        "negative": "happy, bright, realistic, text, watermark"
    },
    "class_divide": {
        "prefix": "Visual metaphor for inequality, contrast between rich and poor",
        "suffix": "split composition, dramatic lighting, vertical 9:16",
        "negative": "happy, equal, bright, cartoon, text"
    }
}

# Visual intent to metaphor mapping
VISUAL_METAPHORS = {
    "debt": ["chains breaking", "prison bars", "sinking ship", "drowning person"],
    "banks": ["dark vault", "giant building crushing person", "chess pieces", "puppet strings"],
    "control": ["puppet on strings", "matrix code", "surveillance eyes", "locked cage"],
    "wealth": ["golden throne", "skyscraper penthouse", "private jet", "vault of gold"],
    "poverty": ["empty wallet", "crumbling house", "long shadows", "fading figure"],
    "system": ["giant machine gears", "maze labyrinth", "invisible walls", "matrix"],
    "inflation": ["melting money", "shrinking dollar", "rising flames", "eroding cliff"],
    "taxes": ["hands reaching from shadows", "pyramid scheme", "drain", "extraction"],
    "freedom": ["breaking chains", "open door light", "flying bird", "horizon"],
    "trap": ["bear trap", "spider web", "quicksand", "invisible walls"],
    "weapon": ["sword", "chess piece", "hidden dagger", "double-edged sword"],
    "power": ["throne", "crown", "mountain peak", "lightning"],
    "fear": ["shadows", "dark figure", "storm clouds", "abyss"],
    "truth": ["light piercing darkness", "revealed curtain", "cracked mirror", "exposed wires"]
}


class VisualEngine:
    """
    Multi-provider AI visual generation engine.
    Generates unique images for each scene using rotating providers.
    """
    
    def __init__(self):
        # Load API keys
        self.stability_key = os.getenv("STABILITY_API_KEY")
        self.replicate_key = os.getenv("REPLICATE_API_TOKEN")
        self.runway_key = os.getenv("RUNWAYML_API_KEY")
        
        # Provider health tracking
        self.provider_status = {
            "stability": {"available": bool(self.stability_key), "failures": 0, "last_success": None},
            "replicate": {"available": bool(self.replicate_key), "failures": 0, "last_success": None},
            "local": {"available": True, "failures": 0, "last_success": None}
        }
        
        # Usage tracking for rotation
        self.provider_usage = {"stability": 0, "replicate": 0, "local": 0}
        
    def _get_available_providers(self) -> List[str]:
        """Get list of available providers sorted by usage (least used first)."""
        available = [p for p, s in self.provider_status.items() 
                    if s["available"] and s["failures"] < 3]
        return sorted(available, key=lambda p: self.provider_usage.get(p, 0))
    
    def _rotate_provider(self) -> str:
        """Select provider using rotation to avoid fingerprinting."""
        available = self._get_available_providers()
        if not available:
            return "local"  # Always have local fallback
        
        # Weight towards least-used provider
        if len(available) > 1:
            # 70% chance of least used, 30% chance of random
            if random.random() < 0.7:
                return available[0]
            return random.choice(available)
        return available[0]
    
    def _build_prompt(self, scene_text: str, intent: str, style: str) -> str:
        """Build optimized image generation prompt."""
        
        preset = STYLE_PRESETS.get(style, STYLE_PRESETS["cinematic"])
        
        # Extract visual metaphor from intent
        metaphor = ""
        for keyword, metaphors in VISUAL_METAPHORS.items():
            if keyword in intent.lower() or keyword in scene_text.lower():
                metaphor = random.choice(metaphors)
                break
        
        if not metaphor:
            # Extract key concept from scene text
            words = scene_text.split()[:5]
            metaphor = " ".join(words)
        
        prompt = f"{preset['prefix']}, visual metaphor: {metaphor}, {preset['suffix']}"
        
        return prompt
    
    async def generate_scene_visual(
        self, 
        scene_text: str, 
        intent: str, 
        style: str,
        scene_index: int,
        video_id: str,
        preferred_provider: str = None
    ) -> VisualResult:
        """Generate visual for a single scene."""
        
        provider = preferred_provider or self._rotate_provider()
        prompt = self._build_prompt(scene_text, intent, style)
        
        output_path = SCENE_VISUALS_DIR / f"{video_id}_scene_{scene_index:03d}.png"
        
        self.provider_usage[provider] = self.provider_usage.get(provider, 0) + 1
        
        try:
            if provider == "stability":
                result = await self._generate_stability(prompt, str(output_path))
            elif provider == "replicate":
                result = await self._generate_replicate(prompt, str(output_path))
            else:
                result = await self._generate_local_fallback(intent, style, str(output_path))
            
            if result.success:
                self.provider_status[provider]["failures"] = 0
                self.provider_status[provider]["last_success"] = datetime.now().isoformat()
            
            return result
            
        except Exception as e:
            self.provider_status[provider]["failures"] += 1
            
            # Try fallback
            if provider != "local":
                return await self._generate_local_fallback(intent, style, str(output_path))
            
            return VisualResult(
                path="",
                provider=provider,
                prompt=prompt,
                success=False,
                error=str(e)
            )
    
    async def _generate_stability(self, prompt: str, output_path: str) -> VisualResult:
        """Generate image using Stability AI."""
        
        if not self.stability_key:
            return VisualResult(path="", provider="stability", prompt=prompt, 
                              success=False, error="No API key")
        
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                # Use Stable Image Ultra for highest quality
                response = await client.post(
                    "https://api.stability.ai/v2beta/stable-image/generate/ultra",
                    headers={
                        "Authorization": f"Bearer {self.stability_key}",
                        "Accept": "image/*"
                    },
                    files={"none": ("", "")},  # Required for multipart
                    data={
                        "prompt": prompt,
                        "negative_prompt": STYLE_PRESETS["cinematic"]["negative"],
                        "aspect_ratio": "9:16",
                        "output_format": "png"
                    }
                )
                
                if response.status_code == 200:
                    Path(output_path).write_bytes(response.content)
                    return VisualResult(
                        path=output_path,
                        provider="stability",
                        prompt=prompt,
                        success=True,
                        metadata={"model": "stable-image-ultra", "size": len(response.content)}
                    )
                else:
                    return VisualResult(
                        path="", provider="stability", prompt=prompt,
                        success=False, error=f"API error: {response.status_code}"
                    )
                    
        except Exception as e:
            return VisualResult(path="", provider="stability", prompt=prompt,
                              success=False, error=str(e))
    
    async def _generate_replicate(self, prompt: str, output_path: str) -> VisualResult:
        """Generate image using Replicate (Flux model)."""
        
        if not self.replicate_key:
            return VisualResult(path="", provider="replicate", prompt=prompt,
                              success=False, error="No API key")
        
        try:
            async with httpx.AsyncClient(timeout=180) as client:
                # Start prediction with Flux Schnell (fast, high quality)
                response = await client.post(
                    "https://api.replicate.com/v1/predictions",
                    headers={
                        "Authorization": f"Token {self.replicate_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "version": "5599ed30703defd1d160a25a63321b4dec97101d98b4674bcc56e41f62f35637",
                        "input": {
                            "prompt": prompt,
                            "aspect_ratio": "9:16",
                            "num_inference_steps": 4,
                            "output_format": "png",
                            "output_quality": 100
                        }
                    }
                )
                
                if response.status_code not in [200, 201]:
                    return VisualResult(path="", provider="replicate", prompt=prompt,
                                      success=False, error=f"API error: {response.status_code}")
                
                prediction = response.json()
                prediction_id = prediction.get("id")
                
                # Poll for completion
                for _ in range(60):  # Max 60 seconds
                    await asyncio.sleep(1)
                    
                    status_response = await client.get(
                        f"https://api.replicate.com/v1/predictions/{prediction_id}",
                        headers={"Authorization": f"Token {self.replicate_key}"}
                    )
                    
                    status_data = status_response.json()
                    status = status_data.get("status")
                    
                    if status == "succeeded":
                        output_url = status_data.get("output")
                        if isinstance(output_url, list):
                            output_url = output_url[0]
                        
                        # Download the image
                        img_response = await client.get(output_url)
                        if img_response.status_code == 200:
                            Path(output_path).write_bytes(img_response.content)
                            return VisualResult(
                                path=output_path,
                                provider="replicate",
                                prompt=prompt,
                                success=True,
                                metadata={"model": "flux-schnell", "prediction_id": prediction_id}
                            )
                    
                    elif status == "failed":
                        return VisualResult(path="", provider="replicate", prompt=prompt,
                                          success=False, error="Prediction failed")
                
                return VisualResult(path="", provider="replicate", prompt=prompt,
                                  success=False, error="Timeout waiting for prediction")
                
        except Exception as e:
            return VisualResult(path="", provider="replicate", prompt=prompt,
                              success=False, error=str(e))
    
    async def _generate_local_fallback(self, intent: str, style: str, output_path: str) -> VisualResult:
        """Fallback: Use local B-roll frame as visual."""
        
        try:
            # Find a matching B-roll video
            videos = []
            for root, dirs, files in os.walk(BROLL_DIR):
                if "_deprecated" in root:
                    continue
                for f in files:
                    if f.endswith(('.mp4', '.mov', '.webm')):
                        videos.append(os.path.join(root, f))
            
            if not videos:
                return VisualResult(path="", provider="local", prompt=intent,
                                  success=False, error="No B-roll available")
            
            # Pick random video based on intent hash (consistent per intent)
            intent_hash = int(hashlib.md5(intent.encode()).hexdigest()[:8], 16)
            video = videos[intent_hash % len(videos)]
            
            # Extract a frame at random position
            import subprocess
            offset = random.uniform(1, 5)
            
            cmd = [
                "ffmpeg", "-y", "-ss", str(offset), "-i", video,
                "-vframes", "1", "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
                output_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            
            if Path(output_path).exists():
                return VisualResult(
                    path=output_path,
                    provider="local",
                    prompt=intent,
                    success=True,
                    metadata={"source": video, "offset": offset}
                )
            
            return VisualResult(path="", provider="local", prompt=intent,
                              success=False, error="Frame extraction failed")
                              
        except Exception as e:
            return VisualResult(path="", provider="local", prompt=intent,
                              success=False, error=str(e))
    
    async def generate_all_scene_visuals(
        self,
        scenes: List[Dict],
        video_id: str,
        parallel: int = 3
    ) -> List[VisualResult]:
        """
        Generate visuals for all scenes with parallel execution.
        
        Args:
            scenes: List of scene dicts with text, intent, style
            video_id: Unique video identifier
            parallel: Max parallel requests
        
        Returns:
            List of VisualResult for each scene
        """
        
        results = []
        semaphore = asyncio.Semaphore(parallel)
        
        async def generate_with_limit(scene: Dict, index: int):
            async with semaphore:
                return await self.generate_scene_visual(
                    scene_text=scene.get("text", ""),
                    intent=scene.get("intent", "power_finance"),
                    style=scene.get("style", "cinematic"),
                    scene_index=index,
                    video_id=video_id
                )
        
        tasks = [generate_with_limit(scene, i) for i, scene in enumerate(scenes)]
        results = await asyncio.gather(*tasks)
        
        return list(results)
    
    def get_provider_stats(self) -> Dict:
        """Get provider usage and health statistics."""
        return {
            "status": self.provider_status,
            "usage": self.provider_usage,
            "available_providers": self._get_available_providers()
        }


# Convenience function
async def generate_scene_visuals(scenes: List[Dict], video_id: str) -> List[VisualResult]:
    """Generate visuals for all scenes."""
    engine = VisualEngine()
    return await engine.generate_all_scene_visuals(scenes, video_id)
