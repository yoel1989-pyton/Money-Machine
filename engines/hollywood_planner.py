"""
===============================================================================
HOLLYWOOD SCENE PLANNER - Elite Scene-Based Cinema Intelligence
===============================================================================
Converts scripts into multi-scene, multi-provider cinematic experiences.
Every sentence = 1 scene. Style rotates. Providers rotate. No repetition.

RULES:
- Scene change every 1.2–2.5 seconds
- Minimum 10–18 unique scenes per short
- At least 3 different visual generators per video
- No scene reused, looped, or extended
- Motion in every single frame
===============================================================================
"""

import os
import random
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Visual Grounding for semantic intelligence
try:
    from engines.visual_grounding import build_visual_plan, ground_single_sentence, VISUAL_MAP
    HAS_VISUAL_GROUNDING = True
except ImportError:
    HAS_VISUAL_GROUNDING = False
    VISUAL_MAP = {}


# ============================================================================
# STYLE DEFINITIONS - Hollywood Visual DNA
# ============================================================================

STYLE_PROVIDERS = [
    ("anime_dark", "leonardo"),
    ("cinematic_real", "runway"),
    ("abstract_metaphor", "fal"),
    ("glitch_data", "replicate"),
    ("motion_cinematic", "kie"),
    ("hyperreal", "stability"),
    ("anime_clean", "leonardo"),
    ("documentary", "shotstack"),
]

MOTION_TYPES = [
    "parallax_zoom",
    "pan_left", 
    "pan_right",
    "pan_up",
    "pan_down",
    "dolly_in",
    "dolly_out",
    "slow_zoom",
    "ken_burns",
    "push_in",
]

VISUAL_INTENTS = {
    "debt": ["oppression", "chains", "weight", "burden"],
    "banks": ["power_control", "mechanism", "system", "machine"],
    "control": ["puppet", "strings", "surveillance", "cage"],
    "wealth": ["luxury", "gold", "opulence", "throne"],
    "poverty": ["decay", "shadows", "emptiness", "fading"],
    "system": ["matrix", "gears", "labyrinth", "invisible_walls"],
    "escape": ["freedom", "light", "breaking", "ascending"],
    "truth": ["revelation", "exposure", "clarity", "awakening"],
    "power": ["dominance", "crown", "peak", "lightning"],
    "fear": ["darkness", "abyss", "storm", "shadow"],
}

EMOTIONAL_ARCS = {
    "revelation": ["shock", "anger", "clarity", "power"],
    "warning": ["fear", "tension", "realization", "urgency"],
    "empowerment": ["struggle", "awakening", "rise", "dominance"],
    "expose": ["discovery", "shock", "understanding", "action"],
}


@dataclass
class HollywoodScene:
    """A single scene in the Hollywood production."""
    beat: int
    text: str
    visual_intent: str
    style: str
    provider: str
    motion: str
    duration: float
    emotion: str = ""
    file_index: str = ""
    prompt: str = ""
    image_path: Optional[str] = None
    video_path: Optional[str] = None
    generated: bool = False
    

@dataclass
class HollywoodPlan:
    """Complete Hollywood production plan."""
    title: str
    thesis: str
    scenes: List[HollywoodScene]
    total_duration: float
    provider_count: int
    style_count: int
    emotional_arc: List[str]
    mode: str = "shorts"
    quality_passed: bool = False
    

class HollywoodPlanner:
    """
    Elite Hollywood Scene Planner.
    Converts scripts into multi-scene, multi-provider cinematic plans.
    """
    
    def __init__(self):
        self.min_scenes = 10
        self.max_scenes = 20
        self.min_providers = 3
        self.min_duration = 1.2
        self.max_duration = 2.5
        
    def _extract_visual_intent(self, text: str) -> str:
        """Extract visual intent from scene text."""
        text_lower = text.lower()
        
        for keyword, intents in VISUAL_INTENTS.items():
            if keyword in text_lower:
                return random.choice(intents)
        
        # Default intents for generic text
        return random.choice(["revelation", "power", "system", "clarity"])
    
    def _get_emotion_for_beat(self, beat_index: int, total_beats: int, arc_name: str = "revelation") -> str:
        """Get emotion based on position in arc."""
        arc = EMOTIONAL_ARCS.get(arc_name, EMOTIONAL_ARCS["revelation"])
        position = beat_index / max(1, total_beats - 1)
        arc_index = int(position * (len(arc) - 1))
        return arc[arc_index]
    
    def _build_prompt(self, scene: HollywoodScene, visual_mode: str = "hybrid") -> str:
        """Build AI generation prompt for scene with optional visual grounding."""
        style_prompts = {
            "anime_dark": "Anime-style illustration, dark moody atmosphere, dramatic shadows, high contrast",
            "cinematic_real": "Cinematic film still, hyper-realistic, moody lighting, professional cinematography",
            "abstract_metaphor": "Abstract surreal metaphor, artistic interpretation, conceptual visual",
            "glitch_data": "Glitch art, data visualization, cyberpunk aesthetic, digital decay",
            "motion_cinematic": "Cinematic motion, dynamic camera movement, professional video quality",
            "hyperreal": "Hyperrealistic photography, ultra-detailed, dramatic lighting",
            "anime_clean": "Clean anime style, vibrant, professional animation quality",
            "documentary": "Documentary footage style, archival aesthetic, historical feel",
        }
        
        base_prompt = style_prompts.get(scene.style, style_prompts["cinematic_real"])
        
        # Use visual grounding for concrete object descriptions
        grounded_subject = None
        if HAS_VISUAL_GROUNDING and scene.text:
            grounded = ground_single_sentence(scene.text, mode=visual_mode)
            if grounded and grounded.visual_prompt:
                grounded_subject = grounded.visual_prompt
        
        if grounded_subject:
            # Use grounded concrete objects instead of abstract metaphors
            prompt = f"{base_prompt}, {grounded_subject}, {scene.emotion} mood, vertical 9:16, no text, no watermark, professional quality"
        else:
            # Fallback to abstract metaphor (original behavior)
            prompt = f"{base_prompt}, visual metaphor: {scene.visual_intent}, {scene.emotion} mood, vertical 9:16, no text, no watermark, professional quality"
        
        return prompt
    
    def plan_from_script(
        self, 
        script: str, 
        title: str = "Elite Video",
        thesis: str = "",
        arc_type: str = "revelation",
        mode: str = "shorts",
        visual_mode: str = "hybrid"
    ) -> HollywoodPlan:
        """
        Convert a script into a Hollywood scene plan.
        
        Args:
            script: Full script text
            title: Video title
            thesis: Core message
            arc_type: Emotional arc type
            mode: Production mode (shorts/anime/documentary)
            
        Returns:
            HollywoodPlan with all scenes configured
        """
        
        # Split script into beats (sentences)
        import re
        sentences = re.split(r'[.!?]+', script)
        beats = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 5]
        
        # Ensure minimum scenes
        if len(beats) < self.min_scenes:
            # Duplicate some beats to reach minimum
            while len(beats) < self.min_scenes:
                beats.append(random.choice(beats))
        
        # Cap at max scenes
        beats = beats[:self.max_scenes]
        
        # Prepare style rotation (shuffle to avoid patterns)
        style_cycle = list(STYLE_PROVIDERS) * 4
        random.shuffle(style_cycle)
        
        # Build scenes
        scenes = []
        providers_used = set()
        styles_used = set()
        total_duration = 0.0
        
        for i, text in enumerate(beats):
            style, provider = style_cycle[i % len(style_cycle)]
            
            # Ensure no consecutive duplicate styles
            if i > 0 and style == scenes[-1].style:
                alt_index = (i + 3) % len(style_cycle)
                style, provider = style_cycle[alt_index]
            
            duration = random.uniform(self.min_duration, self.max_duration)
            intent = self._extract_visual_intent(text)
            emotion = self._get_emotion_for_beat(i, len(beats), arc_type)
            
            scene = HollywoodScene(
                beat=i + 1,
                text=text,
                visual_intent=intent,
                style=style,
                provider=provider,
                motion=random.choice(MOTION_TYPES),
                duration=duration,
                emotion=emotion,
                file_index=f"{i + 1:02d}",
            )
            
            scene.prompt = self._build_prompt(scene, visual_mode=visual_mode)
            
            scenes.append(scene)
            providers_used.add(provider)
            styles_used.add(style)
            total_duration += duration
        
        # Quality check
        quality_passed = (
            len(scenes) >= self.min_scenes and
            len(providers_used) >= self.min_providers
        )
        
        # Get emotional arc
        emotional_arc = [s.emotion for s in scenes[:4]]  # First 4 for arc summary
        
        return HollywoodPlan(
            title=title,
            thesis=thesis or f"Elite content about {title}",
            scenes=scenes,
            total_duration=total_duration,
            provider_count=len(providers_used),
            style_count=len(styles_used),
            emotional_arc=emotional_arc,
            mode=mode,
            quality_passed=quality_passed,
        )
    
    def plan_from_beats(
        self,
        beats: List[str],
        intents: List[str],
        title: str = "Elite Video",
        thesis: str = "",
        mode: str = "shorts",
        visual_mode: str = "hybrid"
    ) -> HollywoodPlan:
        """
        Create plan from pre-defined beats and intents.
        
        Args:
            beats: List of script lines (one per scene)
            intents: List of visual intents
            title: Video title
            thesis: Core message
            mode: Production mode
            visual_mode: Grounding mode (word/sentence/hybrid)
            
        Returns:
            HollywoodPlan
        """
        
        # Prepare style rotation
        style_cycle = list(STYLE_PROVIDERS) * 4
        random.shuffle(style_cycle)
        
        scenes = []
        providers_used = set()
        styles_used = set()
        total_duration = 0.0
        
        for i, text in enumerate(beats):
            style, provider = style_cycle[i % len(style_cycle)]
            
            # Ensure no consecutive duplicate styles
            if i > 0 and style == scenes[-1].style:
                alt_index = (i + 3) % len(style_cycle)
                style, provider = style_cycle[alt_index]
            
            duration = random.uniform(self.min_duration, self.max_duration)
            intent = intents[i % len(intents)] if intents else self._extract_visual_intent(text)
            emotion = self._get_emotion_for_beat(i, len(beats))
            
            scene = HollywoodScene(
                beat=i + 1,
                text=text,
                visual_intent=intent,
                style=style,
                provider=provider,
                motion=random.choice(MOTION_TYPES),
                duration=duration,
                emotion=emotion,
                file_index=f"{i + 1:02d}",
            )
            
            scene.prompt = self._build_prompt(scene, visual_mode=visual_mode)
            
            scenes.append(scene)
            providers_used.add(provider)
            styles_used.add(style)
            total_duration += duration
        
        quality_passed = (
            len(scenes) >= self.min_scenes and
            len(providers_used) >= self.min_providers
        )
        
        emotional_arc = [s.emotion for s in scenes[:4]]
        
        return HollywoodPlan(
            title=title,
            thesis=thesis,
            scenes=scenes,
            total_duration=total_duration,
            provider_count=len(providers_used),
            style_count=len(styles_used),
            emotional_arc=emotional_arc,
            mode=mode,
            quality_passed=quality_passed,
        )
    
    def validate_plan(self, plan: HollywoodPlan) -> Tuple[bool, List[str]]:
        """Validate plan meets Hollywood quality standards."""
        errors = []
        
        if len(plan.scenes) < self.min_scenes:
            errors.append(f"Only {len(plan.scenes)} scenes (minimum {self.min_scenes})")
        
        if plan.provider_count < self.min_providers:
            errors.append(f"Only {plan.provider_count} providers (minimum {self.min_providers})")
        
        # Check for consecutive duplicate styles
        for i in range(1, len(plan.scenes)):
            if plan.scenes[i].style == plan.scenes[i-1].style:
                errors.append(f"Consecutive duplicate style at scenes {i} and {i+1}")
        
        return len(errors) == 0, errors


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_hollywood_plan(script: str, title: str = "Elite Video", mode: str = "shorts") -> HollywoodPlan:
    """Quick function to create a Hollywood plan from script."""
    planner = HollywoodPlanner()
    return planner.plan_from_script(script, title=title, mode=mode)


def validate_hollywood_plan(plan: HollywoodPlan) -> Tuple[bool, List[str]]:
    """Quick function to validate a plan."""
    planner = HollywoodPlanner()
    return planner.validate_plan(plan)


if __name__ == "__main__":
    # Test the planner
    test_script = """
    Debt was never meant to help you. It was designed to shape behavior.
    Banks don't fear debt. They weaponize it.
    The system keeps you paying forever. Interest compounds against you.
    While the rich use debt to build empires. They borrow to buy assets.
    Assets that pay them back. Creating wealth while you sleep.
    The escape is understanding leverage. Not avoiding debt, but mastering it.
    This is how the 1% think. This is the game they don't teach you.
    Break free. Learn the rules. Use the system against itself.
    """
    
    planner = HollywoodPlanner()
    plan = planner.plan_from_script(test_script, title="How the Rich Use Debt", thesis="Debt is control")
    
    print(f"\n🎬 HOLLYWOOD PLAN: {plan.title}")
    print(f"📊 Scenes: {len(plan.scenes)}")
    print(f"🎨 Providers: {plan.provider_count}")
    print(f"🎭 Styles: {plan.style_count}")
    print(f"⏱️ Duration: {plan.total_duration:.1f}s")
    print(f"✅ Quality: {'PASSED' if plan.quality_passed else 'FAILED'}")
    print(f"\n📋 Scenes:")
    for s in plan.scenes:
        print(f"  [{s.file_index}] {s.style} via {s.provider} | {s.text[:40]}...")
