"""
===============================================================================
CINEMATIC SCENE PLANNER - Script-to-Scene Intelligence
===============================================================================
Splits scripts into individual scenes with visual intent, style, and timing.
This is the "brain" that Hollywood uses for storytelling.

Each sentence = 1 scene (1.5-2.5 seconds)
Each scene = unique visual metaphor
===============================================================================
"""

import os
import json
import re
import random
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
import hashlib

# Try to import nltk for better sentence tokenization
try:
    import nltk
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt', quiet=True)
    HAS_NLTK = True
except ImportError:
    HAS_NLTK = False


@dataclass
class CinematicScene:
    """A single scene in the video."""
    index: int
    text: str
    intent: str
    style: str
    emotion: str
    duration: float
    start_time: float
    keywords: List[str] = field(default_factory=list)


@dataclass
class ScenePlan:
    """Complete scene plan for a video."""
    video_id: str
    topic: str
    archetype: str
    total_duration: float
    scenes: List[CinematicScene] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "video_id": self.video_id,
            "topic": self.topic,
            "archetype": self.archetype,
            "total_duration": self.total_duration,
            "scene_count": len(self.scenes),
            "scenes": [
                {
                    "index": s.index,
                    "text": s.text,
                    "intent": s.intent,
                    "style": s.style,
                    "emotion": s.emotion,
                    "duration": s.duration,
                    "start_time": s.start_time,
                    "keywords": s.keywords
                }
                for s in self.scenes
            ]
        }


# Emotional arc mapping for Hollywood pacing
EMOTIONAL_ARCS = {
    "threat": ["shock", "fear", "anger", "revelation", "urgency"],
    "system_reveal": ["curiosity", "suspicion", "anger", "clarity", "empowerment"],
    "authority_contradiction": ["confusion", "disbelief", "revelation", "understanding", "action"],
    "system_exploit": ["intrigue", "revelation", "anger", "strategy", "dominance"],
    "slow_burn_truth": ["unease", "growing_fear", "revelation", "acceptance", "urgency"],
    "mechanism": ["curiosity", "revelation", "understanding", "concern", "action"],
    "identity_trigger": ["recognition", "discomfort", "reflection", "revelation", "transformation"],
    "myth_destruction": ["belief", "doubt", "revelation", "understanding", "new_belief"],
    "contrarian_fear": ["comfort", "disruption", "fear", "understanding", "new_path"],
    "future_threat": ["present", "warning", "vision", "fear", "call_to_action"],
    "urgency": ["awareness", "alarm", "evidence", "urgency", "action"],
    "educational": ["question", "context", "mechanism", "implication", "understanding"],
    "hidden_change": ["normal", "suspicion", "revelation", "impact", "urgency"]
}

# Intent to visual style mapping
INTENT_TO_STYLE = {
    "oppression": "anime_dark",
    "power_finance": "power_finance",
    "system_control": "system_expose",
    "wealth_display": "luxury_wealth",
    "collapse": "collapse",
    "psychology": "psychology",
    "inequality": "class_divide",
    "revelation": "cinematic",
    "fear": "anime_dark",
    "mechanism": "system_expose",
    "trap": "anime_dark",
    "freedom": "cinematic",
    "surveillance": "system_expose",
    "decay": "collapse",
    "luxury": "luxury_wealth",
    "poverty": "class_divide"
}

# Keyword to intent mapping
KEYWORD_INTENTS = {
    # Financial control
    "bank": "power_finance",
    "banks": "power_finance",
    "debt": "oppression",
    "loan": "trap",
    "credit": "trap",
    "interest": "mechanism",
    "compound": "mechanism",
    "federal reserve": "system_control",
    "fed": "system_control",
    "money supply": "mechanism",
    "inflation": "decay",
    "deflation": "collapse",
    "currency": "mechanism",
    
    # Wealth/Poverty
    "rich": "wealth_display",
    "wealthy": "wealth_display",
    "billionaire": "luxury",
    "millionaire": "luxury",
    "poor": "poverty",
    "poverty": "poverty",
    "middle class": "inequality",
    "working class": "oppression",
    
    # Control/System
    "control": "system_control",
    "system": "system_control",
    "designed": "mechanism",
    "trap": "trap",
    "weapon": "power_finance",
    "slave": "oppression",
    "chain": "oppression",
    "prison": "oppression",
    "cage": "trap",
    
    # Psychological
    "fear": "fear",
    "scared": "fear",
    "psychology": "psychology",
    "mindset": "psychology",
    "think": "psychology",
    "believe": "psychology",
    "brainwash": "system_control",
    
    # Action/Revelation
    "truth": "revelation",
    "secret": "revelation",
    "hidden": "revelation",
    "revealed": "revelation",
    "discover": "revelation",
    "freedom": "freedom",
    "escape": "freedom",
    "break": "freedom"
}


class CinematicScenePlanner:
    """
    Transforms scripts into scene-by-scene visual plans.
    Hollywood-grade scene intelligence for AI video production.
    """
    
    def __init__(self, min_scene_duration: float = 1.5, max_scene_duration: float = 3.0):
        self.min_scene_duration = min_scene_duration
        self.max_scene_duration = max_scene_duration
        self.default_duration = 2.0
    
    def _tokenize_sentences(self, script: str) -> List[str]:
        """Split script into sentences."""
        
        # Clean up the script
        script = script.strip()
        
        # Remove stage directions if any
        script = re.sub(r'\[.*?\]', '', script)
        script = re.sub(r'\(.*?\)', '', script)
        
        if HAS_NLTK:
            try:
                sentences = nltk.sent_tokenize(script)
            except:
                sentences = self._fallback_tokenize(script)
        else:
            sentences = self._fallback_tokenize(script)
        
        # Filter and clean
        cleaned = []
        for s in sentences:
            s = s.strip()
            if len(s) > 10:  # Minimum sentence length
                cleaned.append(s)
        
        return cleaned
    
    def _fallback_tokenize(self, script: str) -> List[str]:
        """Fallback sentence tokenization."""
        # Split on sentence-ending punctuation
        sentences = re.split(r'(?<=[.!?])\s+', script)
        return [s.strip() for s in sentences if s.strip()]
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords from text."""
        text_lower = text.lower()
        found = []
        
        for keyword in KEYWORD_INTENTS.keys():
            if keyword in text_lower:
                found.append(keyword)
        
        return found
    
    def _detect_intent(self, text: str, keywords: List[str]) -> str:
        """Detect visual intent from text and keywords."""
        
        # Check keywords first
        for keyword in keywords:
            if keyword in KEYWORD_INTENTS:
                return KEYWORD_INTENTS[keyword]
        
        # Fallback detection
        text_lower = text.lower()
        
        if any(w in text_lower for w in ["bank", "debt", "credit", "loan"]):
            return "power_finance"
        elif any(w in text_lower for w in ["rich", "wealth", "money"]):
            return "wealth_display"
        elif any(w in text_lower for w in ["poor", "struggle", "afford"]):
            return "poverty"
        elif any(w in text_lower for w in ["control", "system", "designed"]):
            return "system_control"
        elif any(w in text_lower for w in ["truth", "secret", "hidden"]):
            return "revelation"
        else:
            return "power_finance"  # Default
    
    def _get_style_for_intent(self, intent: str) -> str:
        """Map intent to visual style."""
        return INTENT_TO_STYLE.get(intent, "cinematic")
    
    def _get_emotion_for_position(self, position: float, archetype: str) -> str:
        """Get emotional beat based on position in video."""
        
        arc = EMOTIONAL_ARCS.get(archetype, EMOTIONAL_ARCS["threat"])
        
        # Map position (0-1) to emotional arc
        arc_index = int(position * (len(arc) - 1))
        arc_index = min(arc_index, len(arc) - 1)
        
        return arc[arc_index]
    
    def _estimate_scene_duration(self, text: str) -> float:
        """Estimate how long to show this scene based on text."""
        
        # Word count based estimation
        words = len(text.split())
        
        # Roughly 2.5 words per second for narration
        estimated = words / 2.5
        
        # Clamp to min/max
        return max(self.min_scene_duration, min(self.max_scene_duration, estimated))
    
    def plan_scenes(
        self,
        script: str,
        topic: str = "",
        archetype: str = "threat",
        total_duration: float = None,
        video_id: str = None,
        max_scenes: int = 25
    ) -> ScenePlan:
        """
        Plan scenes from a script.
        
        Args:
            script: The narration script
            topic: Video topic for context
            archetype: Emotional archetype (threat, system_reveal, etc.)
            total_duration: Target video duration (from audio)
            video_id: Unique identifier
            max_scenes: Maximum number of scenes
        
        Returns:
            ScenePlan with all scenes defined
        """
        
        if not video_id:
            video_id = hashlib.md5(script[:100].encode()).hexdigest()[:8]
        
        # Tokenize script into sentences
        sentences = self._tokenize_sentences(script)
        
        # Limit to max scenes
        if len(sentences) > max_scenes:
            # Take evenly distributed sentences
            step = len(sentences) / max_scenes
            sentences = [sentences[int(i * step)] for i in range(max_scenes)]
        
        # Calculate timing
        if total_duration:
            # Distribute duration across scenes
            base_duration = total_duration / len(sentences) if sentences else self.default_duration
            base_duration = max(self.min_scene_duration, min(self.max_scene_duration, base_duration))
        else:
            base_duration = self.default_duration
        
        # Build scenes
        scenes = []
        current_time = 0.0
        
        for i, sentence in enumerate(sentences):
            # Position in video (0-1)
            position = i / max(len(sentences) - 1, 1)
            
            # Extract keywords and intent
            keywords = self._extract_keywords(sentence)
            intent = self._detect_intent(sentence, keywords)
            style = self._get_style_for_intent(intent)
            emotion = self._get_emotion_for_position(position, archetype)
            
            # Estimate duration
            duration = self._estimate_scene_duration(sentence)
            
            # Adjust if we have total duration constraint
            if total_duration:
                remaining_time = total_duration - current_time
                remaining_scenes = len(sentences) - i
                if remaining_scenes > 0:
                    avg_remaining = remaining_time / remaining_scenes
                    duration = max(self.min_scene_duration, min(self.max_scene_duration, avg_remaining))
            
            scenes.append(CinematicScene(
                index=i,
                text=sentence,
                intent=intent,
                style=style,
                emotion=emotion,
                duration=duration,
                start_time=current_time,
                keywords=keywords
            ))
            
            current_time += duration
        
        return ScenePlan(
            video_id=video_id,
            topic=topic,
            archetype=archetype,
            total_duration=current_time,
            scenes=scenes
        )
    
    def get_visual_prompts(self, scene_plan: ScenePlan) -> List[Dict]:
        """
        Convert scene plan to visual generation prompts.
        
        Returns list of dicts with text, intent, style for visual engine.
        """
        
        prompts = []
        for scene in scene_plan.scenes:
            prompts.append({
                "index": scene.index,
                "text": scene.text,
                "intent": scene.intent,
                "style": scene.style,
                "emotion": scene.emotion,
                "duration": scene.duration
            })
        
        return prompts


# Convenience functions
def plan_video_scenes(
    script: str,
    topic: str = "",
    archetype: str = "threat",
    audio_duration: float = None
) -> ScenePlan:
    """Plan scenes for a video."""
    planner = CinematicScenePlanner()
    return planner.plan_scenes(
        script=script,
        topic=topic,
        archetype=archetype,
        total_duration=audio_duration
    )


def script_to_scene_prompts(
    script: str,
    topic: str = "",
    archetype: str = "threat",
    audio_duration: float = None
) -> List[Dict]:
    """Convert script directly to visual prompts."""
    planner = CinematicScenePlanner()
    plan = planner.plan_scenes(
        script=script,
        topic=topic,
        archetype=archetype,
        total_duration=audio_duration
    )
    return planner.get_visual_prompts(plan)
