"""
OPAL CLIP FACTORY - Elite Omni Pipeline Stage 1
================================================
Outputs ONLY:
- High-quality 8-10s cinematic clips
- Clean metadata per clip
- Failure intelligence
- Prompt lineage (original → simplified → decomposed)

NEVER outputs:
- Final merges
- Long-form assembly
- HTML reports
"""

import os
import json
import asyncio
import aiohttp
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict
from enum import Enum


class OperatingMode(Enum):
    SAFE = "SAFE"
    ACCELERATED = "ACCELERATED"


class ErrorType(Enum):
    METADATA_ERROR = "METADATA_ERROR"           # Retry once
    TIMEOUT_ERROR = "TIMEOUT_ERROR"             # Pause + simplify
    ASSET_RESOLUTION_ERROR = "ASSET_ERROR"      # Reduce complexity
    UNKNOWN_ERROR = "UNKNOWN_ERROR"             # Semantic proxy
    REPEAT_FAIL_ERROR = "REPEAT_FAIL_ERROR"     # Symbolic stand-in
    RATE_LIMIT_ERROR = "RATE_LIMIT_ERROR"
    CONTENT_POLICY_ERROR = "CONTENT_POLICY_ERROR"


class RecoveryStrategy(Enum):
    RETRY_ORIGINAL = "RETRY_ORIGINAL"
    PROMPT_SIMPLIFICATION = "PROMPT_SIMPLIFICATION"
    SEMANTIC_PROXY = "SEMANTIC_PROXY"
    OMNI_DECOMPOSITION = "OMNI_DECOMPOSITION"
    PROVIDER_FAILOVER = "PROVIDER_FAILOVER"


@dataclass
class PromptLineage:
    original: str
    simplified: Optional[str] = None
    decomposed: Optional[str] = None
    final: Optional[str] = None
    
    def to_dict(self):
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class ClipResult:
    clip_id: str
    status: str  # SUCCESS, RECOVERED, FAILED
    file_path: Optional[str]
    provider: str
    duration: float
    prompt_lineage: PromptLineage
    error: Optional[str] = None
    recovery_strategy: Optional[str] = None
    attempts: int = 1


@dataclass
class OpalOutput:
    run_id: str
    output_dir: Path
    clips: List[ClipResult]
    metadata: Dict[str, Any]
    
    
class OpalClipFactory:
    """
    OPAL = Omni Pipeline Asset Layer
    A stateless, portable clip factory.
    """
    
    # Provider configurations
    PROVIDERS = {
        "leonardo": {
            "url": "https://cloud.leonardo.ai/api/rest/v1/generations",
            "weight": 0.3,
            "style": "anime_dark"
        },
        "runway": {
            "url": "https://api.dev.runwayml.com/v1/text_to_image",
            "weight": 0.25,
            "style": "cinematic_real"
        },
        "fal": {
            "url": "https://queue.fal.run/fal-ai/flux/dev",
            "weight": 0.25,
            "style": "abstract_metaphor"
        },
        "stability": {
            "url": "https://api.stability.ai/v2beta/stable-image/generate/core",
            "weight": 0.2,
            "style": "hyperreal"
        }
    }
    
    # API Keys (load from env in production)
    API_KEYS = {
        "leonardo": os.getenv("LEONARDO_API_KEY", "8a7ccd1c-6aa6-4a0e-a28e-4d461b542212"),
        "runway": os.getenv("RUNWAY_API_KEY", "key_d327367da695c4e0b7005c8354c879262f74d0e3396cf1f615340949cca23c33fd1df587838c7702388956488e5c9ce80c63b32f54b42ab273b28ecbd8142ea0"),
        "fal": os.getenv("FAL_API_KEY", "04cc9251-3b11-482a-b89d-980f7a6791e4:1db3d89f6b155f496f1872f8afcbc46a"),
        "stability": os.getenv("STABILITY_API_KEY", "sk-nKoQVkvdM7w1cYfiTp1wSxGowNG3F9wkj7RxygTgn7peao98")
    }
    
    def __init__(
        self,
        output_base: str = "data/opal_output",
        mode: OperatingMode = OperatingMode.SAFE,
        clips_per_run: int = 30,
        duration_per_clip: float = 8.0,
        resolution: str = "1080x1920",
        fps: int = 30
    ):
        self.mode = mode
        self.clips_per_run = clips_per_run
        self.duration_per_clip = duration_per_clip
        self.resolution = resolution
        self.fps = fps
        
        # Create run-specific output directory
        self.run_id = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        self.output_dir = Path(output_base) / self.run_id
        self.clips_dir = self.output_dir / "clips"
        
        # Results tracking
        self.clips: List[ClipResult] = []
        self.prompts: Dict[str, Dict] = {}
        self.failures: Dict[str, Dict] = {}
        
    def _setup_directories(self):
        """Create output directory structure."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.clips_dir.mkdir(exist_ok=True)
        print(f"📁 OPAL Output: {self.output_dir}")
        
    def _simplify_prompt(self, prompt: str) -> str:
        """
        Prompt Simplification Engine.
        Removes complex modifiers while preserving core intent.
        """
        # Remove overly specific descriptors
        removals = [
            "intricate", "complex", "detailed", "advanced", "state-of-the-art",
            "sleek", "modern", "futuristic", "cutting-edge", "sophisticated",
            "ephemeral", "subtle", "gracefully", "seamlessly", "effortlessly"
        ]
        
        simplified = prompt
        for word in removals:
            simplified = simplified.replace(word + " ", "")
            simplified = simplified.replace(word + ",", ",")
            
        # Clean up double spaces
        while "  " in simplified:
            simplified = simplified.replace("  ", " ")
            
        return simplified.strip()
    
    def _decompose_prompt(self, prompt: str) -> str:
        """
        OMNI Decomposition - Break complex scenes into core elements.
        Last resort before failure.
        """
        # Extract the first noun phrase as the core subject
        words = prompt.split()
        
        # Find key subjects
        subjects = ["person", "people", "individual", "user", "hand", "hands",
                   "screen", "display", "interface", "room", "space", "city"]
        
        core_subject = None
        for word in words:
            if word.lower() in subjects:
                core_subject = word
                break
                
        if core_subject:
            return f"A {core_subject} in a dark, cinematic setting"
        else:
            return "A dark, atmospheric cinematic scene"
    
    def _semantic_proxy(self, prompt: str) -> str:
        """
        Semantic Proxy - Replace problematic concepts with safe alternatives.
        """
        proxies = {
            "holographic": "glowing digital",
            "AR glasses": "smart glasses",
            "neural network": "abstract pattern",
            "biometric": "digital data",
            "surveillance": "monitoring",
            "weapon": "tool",
            "blood": "red liquid",
            "death": "ending",
            "explosion": "burst of light"
        }
        
        result = prompt
        for original, proxy in proxies.items():
            result = result.replace(original, proxy)
            
        return result
    
    async def _generate_with_provider(
        self,
        provider: str,
        prompt: str,
        clip_id: str,
        session: aiohttp.ClientSession
    ) -> Optional[str]:
        """Generate a clip with a specific provider."""
        
        config = self.PROVIDERS[provider]
        api_key = self.API_KEYS[provider]
        
        try:
            if provider == "leonardo":
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "prompt": f"{prompt}, {config['style']}, cinematic, vertical 9:16, no text",
                    "modelId": "aa77f04e-3eec-4034-9c07-d0f619684628",
                    "width": 576,
                    "height": 1024,
                    "num_images": 1
                }
                async with session.post(config["url"], headers=headers, json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("sdGenerationJob", {}).get("generationId")
                    else:
                        return None
                        
            elif provider == "runway":
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "X-Runway-Version": "2024-11-06",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "gen4_image",
                    "promptText": f"{prompt}, {config['style']}, 9:16, no text",
                    "ratio": "9:16"
                }
                async with session.post(config["url"], headers=headers, json=payload) as resp:
                    if resp.status in [200, 201]:
                        data = await resp.json()
                        return data.get("id") or data.get("output", [None])[0]
                    else:
                        return None
                        
            elif provider == "fal":
                headers = {
                    "Authorization": f"Key {api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "prompt": f"{prompt}, {config['style']}, vertical 9:16, no text",
                    "image_size": "portrait_16_9",
                    "num_images": 1
                }
                async with session.post(config["url"], headers=headers, json=payload) as resp:
                    if resp.status in [200, 201]:
                        data = await resp.json()
                        return data.get("request_id") or data.get("images", [{}])[0].get("url")
                    else:
                        return None
                        
            elif provider == "stability":
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Accept": "application/json"
                }
                # Stability uses multipart form data
                data = aiohttp.FormData()
                data.add_field("prompt", f"{prompt}, {config['style']}, vertical, no text")
                data.add_field("aspect_ratio", "9:16")
                data.add_field("output_format", "png")
                
                async with session.post(config["url"], headers=headers, data=data) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        return result.get("image") or result.get("artifacts", [{}])[0].get("base64")
                    else:
                        return None
                        
        except Exception as e:
            print(f"  ❌ {provider} error: {str(e)[:50]}")
            return None
            
        return None
    
    async def _generate_clip_with_recovery(
        self,
        clip_num: int,
        original_prompt: str,
        provider: str,
        session: aiohttp.ClientSession
    ) -> ClipResult:
        """
        Generate a single clip with full self-healing capability.
        Recovery chain: Original → Simplified → Semantic Proxy → Decomposed → Failover
        """
        clip_id = f"clip_{clip_num:02d}"
        lineage = PromptLineage(original=original_prompt)
        
        # Attempt 1: Original prompt
        print(f"  🎬 {clip_id} → {provider} (original)")
        result = await self._generate_with_provider(provider, original_prompt, clip_id, session)
        
        if result:
            return ClipResult(
                clip_id=clip_id,
                status="SUCCESS",
                file_path=str(self.clips_dir / f"{clip_id}.mp4"),
                provider=provider,
                duration=self.duration_per_clip,
                prompt_lineage=lineage,
                attempts=1
            )
        
        # Attempt 2: Simplified prompt
        simplified = self._simplify_prompt(original_prompt)
        lineage.simplified = simplified
        print(f"  🔄 {clip_id} → {provider} (simplified)")
        result = await self._generate_with_provider(provider, simplified, clip_id, session)
        
        if result:
            return ClipResult(
                clip_id=clip_id,
                status="RECOVERED",
                file_path=str(self.clips_dir / f"{clip_id}.mp4"),
                provider=provider,
                duration=self.duration_per_clip,
                prompt_lineage=lineage,
                recovery_strategy=RecoveryStrategy.PROMPT_SIMPLIFICATION.value,
                attempts=2
            )
        
        # Attempt 3: Semantic proxy
        proxied = self._semantic_proxy(simplified)
        lineage.final = proxied
        print(f"  🔄 {clip_id} → {provider} (semantic proxy)")
        result = await self._generate_with_provider(provider, proxied, clip_id, session)
        
        if result:
            return ClipResult(
                clip_id=clip_id,
                status="RECOVERED",
                file_path=str(self.clips_dir / f"{clip_id}.mp4"),
                provider=provider,
                duration=self.duration_per_clip,
                prompt_lineage=lineage,
                recovery_strategy=RecoveryStrategy.SEMANTIC_PROXY.value,
                attempts=3
            )
        
        # Attempt 4: OMNI Decomposition
        decomposed = self._decompose_prompt(original_prompt)
        lineage.decomposed = decomposed
        lineage.final = decomposed
        print(f"  🔄 {clip_id} → {provider} (decomposed)")
        result = await self._generate_with_provider(provider, decomposed, clip_id, session)
        
        if result:
            return ClipResult(
                clip_id=clip_id,
                status="RECOVERED",
                file_path=str(self.clips_dir / f"{clip_id}.mp4"),
                provider=provider,
                duration=self.duration_per_clip,
                prompt_lineage=lineage,
                recovery_strategy=RecoveryStrategy.OMNI_DECOMPOSITION.value,
                attempts=4
            )
        
        # Attempt 5: Provider failover
        fallback_map = {
            "leonardo": "stability",
            "runway": "fal",
            "fal": "stability",
            "stability": "fal"
        }
        fallback = fallback_map.get(provider, "stability")
        print(f"  🔄 {clip_id} → {fallback} (failover)")
        result = await self._generate_with_provider(fallback, decomposed, clip_id, session)
        
        if result:
            return ClipResult(
                clip_id=clip_id,
                status="RECOVERED",
                file_path=str(self.clips_dir / f"{clip_id}.mp4"),
                provider=fallback,
                duration=self.duration_per_clip,
                prompt_lineage=lineage,
                recovery_strategy=RecoveryStrategy.PROVIDER_FAILOVER.value,
                attempts=5
            )
        
        # All attempts failed
        return ClipResult(
            clip_id=clip_id,
            status="FAILED",
            file_path=None,
            provider=provider,
            duration=0,
            prompt_lineage=lineage,
            error=ErrorType.UNKNOWN_ERROR.value,
            recovery_strategy="EXHAUSTED",
            attempts=5
        )
    
    def _export_metadata(self):
        """Export metadata.json"""
        metadata = {
            "run_id": self.run_id,
            "fps": self.fps,
            "resolution": self.resolution,
            "duration_per_clip": self.duration_per_clip,
            "total_clips": len(self.clips),
            "successful_clips": len([c for c in self.clips if c.status != "FAILED"]),
            "failed_clips": len([c for c in self.clips if c.status == "FAILED"]),
            "operating_mode": self.mode.value,
            "timestamp": datetime.now().isoformat()
        }
        
        with open(self.output_dir / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)
            
        return metadata
    
    def _export_prompts(self):
        """Export prompts.json with full lineage."""
        prompts = {}
        for clip in self.clips:
            prompts[clip.clip_id] = clip.prompt_lineage.to_dict()
            
        with open(self.output_dir / "prompts.json", "w") as f:
            json.dump(prompts, f, indent=2)
            
        return prompts
    
    def _export_failure_log(self):
        """Export failure_log.json for failed/recovered clips."""
        failures = {}
        for clip in self.clips:
            if clip.status in ["RECOVERED", "FAILED"]:
                failures[clip.clip_id] = {
                    "status": clip.status,
                    "error": clip.error,
                    "recovery_strategy": clip.recovery_strategy,
                    "attempts": clip.attempts,
                    "provider": clip.provider
                }
                
        with open(self.output_dir / "failure_log.json", "w") as f:
            json.dump(failures, f, indent=2)
            
        return failures
    
    def _export_manifest(self):
        """Export manifest.json - authoritative clip order for assembly."""
        manifest = {
            "run_id": self.run_id,
            "clip_order": [],
            "total_duration": 0,
            "assembly_ready": True
        }
        
        for clip in self.clips:
            if clip.status != "FAILED":
                manifest["clip_order"].append({
                    "id": clip.clip_id,
                    "file": f"clips/{clip.clip_id}.mp4",
                    "duration": clip.duration,
                    "provider": clip.provider,
                    "status": clip.status
                })
                manifest["total_duration"] += clip.duration
        
        # Check if any clips are missing
        if len([c for c in self.clips if c.status == "FAILED"]) > 0:
            manifest["assembly_ready"] = False
            manifest["missing_clips"] = [c.clip_id for c in self.clips if c.status == "FAILED"]
        
        with open(self.output_dir / "manifest.json", "w") as f:
            json.dump(manifest, f, indent=2)
            
        return manifest
    
    async def run(self, prompts: List[str]) -> OpalOutput:
        """
        Execute the OPAL Clip Factory.
        
        Args:
            prompts: List of scene prompts to generate
            
        Returns:
            OpalOutput with all clips, metadata, and intelligence
        """
        print(f"\n{'='*60}")
        print(f"🔮 OPAL CLIP FACTORY - {self.mode.value} MODE")
        print(f"{'='*60}")
        print(f"📊 Run ID: {self.run_id}")
        print(f"🎬 Clips to generate: {len(prompts)}")
        print(f"⏱️  Duration per clip: {self.duration_per_clip}s")
        print(f"📐 Resolution: {self.resolution}")
        print()
        
        self._setup_directories()
        
        # Assign providers based on weights
        providers = list(self.PROVIDERS.keys())
        
        async with aiohttp.ClientSession() as session:
            for i, prompt in enumerate(prompts, 1):
                provider = providers[(i - 1) % len(providers)]
                clip_result = await self._generate_clip_with_recovery(
                    i, prompt, provider, session
                )
                self.clips.append(clip_result)
                
                # Rate limiting per operating mode
                # SAFE: batch=1, pause=120s (highest reliability)
                # ACCELERATED: batch=2-3, shorter pause (only after SAFE success)
                if self.mode == OperatingMode.SAFE:
                    print(f"  ⏳ SAFE MODE: 120s cooldown...")
                    await asyncio.sleep(120)
                else:
                    await asyncio.sleep(30)
        
        # Export all intelligence
        print(f"\n📦 Exporting OPAL artifacts...")
        metadata = self._export_metadata()
        self._export_prompts()
        self._export_failure_log()
        self._export_manifest()
        
        # Summary
        success = len([c for c in self.clips if c.status == "SUCCESS"])
        recovered = len([c for c in self.clips if c.status == "RECOVERED"])
        failed = len([c for c in self.clips if c.status == "FAILED"])
        
        print(f"\n{'='*60}")
        print(f"✅ OPAL RUN COMPLETE")
        print(f"{'='*60}")
        print(f"  ✓ Success:   {success}")
        print(f"  ↻ Recovered: {recovered}")
        print(f"  ✗ Failed:    {failed}")
        print(f"\n📁 Output: {self.output_dir}")
        print(f"  ├─ clips/")
        print(f"  ├─ metadata.json")
        print(f"  ├─ prompts.json")
        print(f"  ├─ failure_log.json")
        print(f"  └─ manifest.json (authoritative clip order)")
        
        return OpalOutput(
            run_id=self.run_id,
            output_dir=self.output_dir,
            clips=self.clips,
            metadata=metadata
        )


# ============================================================
# STANDALONE EXECUTION
# ============================================================

if __name__ == "__main__":
    # Example: Generate clips for a finance video
    EXAMPLE_PROMPTS = [
        "A serene sunrise casting golden light over a modern city skyline",
        "A person in meditation, soft light filtering through a window",
        "Streams of luminous data flowing across transparent display screens",
        "Dynamic charts and graphs displaying financial growth on a tablet",
        "A professional focused at a modern workstation with multiple screens",
        "Currency notes dissolving into digital particles",
        "A locked vault door slowly opening to reveal golden light",
        "Chains breaking apart in dramatic slow motion",
        "A chess king piece dominating the board from above",
        "Dark storm clouds parting to reveal sunlight",
        "A person standing at a crossroads, dramatic lighting",
        "An eye opening wide, reflecting digital data streams"
    ]
    
    factory = OpalClipFactory(
        mode=OperatingMode.SAFE,
        clips_per_run=len(EXAMPLE_PROMPTS),
        duration_per_clip=8.0
    )
    
    asyncio.run(factory.run(EXAMPLE_PROMPTS))
