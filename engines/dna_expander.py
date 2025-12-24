"""
DNA EXPANDER ENGINE v1.0
Extracts winning DNA from Shorts and expands into documentary outlines.

This is where billion-view systems are born:
- Shorts → Discovery
- Long-form → Compounding revenue + trust + RPM

The DNA includes:
- Topic
- Hook structure
- Emotional trigger
- Visual intent
- Retention pattern
- RPM performance
- Curiosity gaps (what was not answered)
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent
DNA_STORAGE = BASE_DIR / "data" / "dna"
METRICS_DIR = BASE_DIR / "data" / "metrics"


@dataclass
class VisualDNA:
    """The genetic code of a video's visual identity."""
    intent: str  # power_finance, systems_control, future_warning, etc.
    pacing: str  # aggressive, measured, contemplative
    motion_density: str  # high, medium, low
    color_mood: str  # dark, neutral, vibrant
    scene_duration: float  # average seconds per scene
    cut_frequency: float  # cuts per minute
    

@dataclass
class ShortDNA:
    """Complete DNA profile of a Short."""
    video_id: str
    topic: str
    hook_type: str  # curiosity_threat, revelation, challenge
    emotional_trigger: str  # injustice, revelation, urgency, curiosity
    visual_dna: VisualDNA
    script_hash: str
    
    # Performance metrics
    views_1hr: int = 0
    views_24hr: int = 0
    retention_rate: float = 0.0
    avg_view_duration: float = 0.0
    rpm: float = 0.0
    
    # Evolution flags
    is_winner: bool = False
    should_expand: bool = False
    times_mutated: int = 0
    
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


@dataclass 
class DocumentaryOutline:
    """Expanded outline for documentary production."""
    source_dna: ShortDNA
    title: str
    thesis: str
    acts: List[Dict[str, Any]]
    total_duration_minutes: int
    visual_requirements: List[Dict[str, str]]
    music_cues: List[Dict[str, Any]]


class DNAExpander:
    """
    Extracts DNA from Shorts and expands winners into documentary outlines.
    """
    
    def __init__(self):
        DNA_STORAGE.mkdir(parents=True, exist_ok=True)
        METRICS_DIR.mkdir(parents=True, exist_ok=True)
        self.dna_pool: Dict[str, ShortDNA] = {}
        self._load_dna_pool()
    
    def _load_dna_pool(self):
        """Load existing DNA profiles."""
        dna_file = DNA_STORAGE / "pool.json"
        if dna_file.exists():
            try:
                with open(dna_file, "r") as f:
                    data = json.load(f)
                    for vid_id, dna_dict in data.items():
                        visual_dna = VisualDNA(**dna_dict.pop("visual_dna"))
                        self.dna_pool[vid_id] = ShortDNA(**dna_dict, visual_dna=visual_dna)
            except Exception as e:
                print(f"[DNA] Error loading pool: {e}")
    
    def _save_dna_pool(self):
        """Persist DNA pool to disk."""
        dna_file = DNA_STORAGE / "pool.json"
        try:
            data = {}
            for vid_id, dna in self.dna_pool.items():
                dna_dict = asdict(dna)
                data[vid_id] = dna_dict
            with open(dna_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[DNA] Error saving pool: {e}")
    
    def extract_dna(
        self,
        video_id: str,
        topic: str,
        script: str,
        visual_intent: str,
        metrics: Dict[str, Any] = None
    ) -> ShortDNA:
        """
        Extract DNA from a Short video.
        This is called after every upload.
        """
        metrics = metrics or {}
        
        # Detect hook type from script
        hook_type = self._detect_hook_type(script)
        
        # Detect emotional trigger
        emotional_trigger = self._detect_emotion(script)
        
        # Create visual DNA
        visual_dna = VisualDNA(
            intent=visual_intent,
            pacing=self._detect_pacing(script),
            motion_density="high",  # Default for Shorts
            color_mood="dark",  # Default for finance niche
            scene_duration=2.0,  # Default
            cut_frequency=25.0  # Default for Shorts
        )
        
        # Create Short DNA
        dna = ShortDNA(
            video_id=video_id,
            topic=topic,
            hook_type=hook_type,
            emotional_trigger=emotional_trigger,
            visual_dna=visual_dna,
            script_hash=str(hash(script)),
            views_1hr=metrics.get("views_1hr", 0),
            views_24hr=metrics.get("views_24hr", 0),
            retention_rate=metrics.get("retention_rate", 0.0),
            avg_view_duration=metrics.get("avg_view_duration", 0.0),
            rpm=metrics.get("rpm", 0.0)
        )
        
        # Store in pool
        self.dna_pool[video_id] = dna
        self._save_dna_pool()
        
        print(f"[DNA] Extracted: {topic[:50]}...")
        print(f"[DNA] Hook: {hook_type}, Emotion: {emotional_trigger}, Intent: {visual_intent}")
        
        return dna
    
    def _detect_hook_type(self, script: str) -> str:
        """Detect the hook archetype from script."""
        script_lower = script.lower()
        if any(w in script_lower for w in ["nobody told", "they don't want", "hidden"]):
            return "revelation"
        if any(w in script_lower for w in ["why", "disappearing", "dying", "ending"]):
            return "curiosity_threat"
        if any(w in script_lower for w in ["most people", "you're wrong", "think you know"]):
            return "challenge"
        if any(w in script_lower for w in ["secret", "only", "few people"]):
            return "exclusivity"
        return "curiosity_threat"
    
    def _detect_emotion(self, script: str) -> str:
        """Detect primary emotional trigger."""
        script_lower = script.lower()
        if any(w in script_lower for w in ["unfair", "rigged", "designed against"]):
            return "injustice"
        if any(w in script_lower for w in ["secret", "hidden", "never told"]):
            return "revelation"
        if any(w in script_lower for w in ["disappear", "collapse", "end", "die"]):
            return "urgency"
        if any(w in script_lower for w in ["why", "how", "what if"]):
            return "curiosity"
        return "curiosity"
    
    def _detect_pacing(self, script: str) -> str:
        """Detect pacing from script density."""
        words = len(script.split())
        if words > 120:
            return "aggressive"
        if words > 80:
            return "measured"
        return "contemplative"
    
    def update_metrics(self, video_id: str, metrics: Dict[str, Any]):
        """
        Update DNA with performance metrics.
        Called periodically to track video performance.
        """
        if video_id not in self.dna_pool:
            return
        
        dna = self.dna_pool[video_id]
        dna.views_1hr = metrics.get("views_1hr", dna.views_1hr)
        dna.views_24hr = metrics.get("views_24hr", dna.views_24hr)
        dna.retention_rate = metrics.get("retention_rate", dna.retention_rate)
        dna.avg_view_duration = metrics.get("avg_view_duration", dna.avg_view_duration)
        dna.rpm = metrics.get("rpm", dna.rpm)
        
        # Check if this is a winner
        dna.is_winner = self._is_winner(dna)
        dna.should_expand = dna.is_winner and dna.avg_view_duration > 0.85
        
        self._save_dna_pool()
        
        if dna.is_winner:
            print(f"[DNA] 🏆 WINNER DETECTED: {dna.topic[:40]}...")
    
    def _is_winner(self, dna: ShortDNA) -> bool:
        """Determine if this DNA is a winner worth expanding."""
        # Winner criteria:
        # - AVD > 85% OR
        # - Views in first hour > 500 OR
        # - RPM > $0.05
        if dna.avg_view_duration > 0.85:
            return True
        if dna.views_1hr > 500:
            return True
        if dna.rpm > 0.05:
            return True
        return False
    
    def get_winners(self) -> List[ShortDNA]:
        """Get all winning DNA profiles."""
        return [dna for dna in self.dna_pool.values() if dna.is_winner]
    
    def get_expansion_candidates(self) -> List[ShortDNA]:
        """Get DNA profiles ready for documentary expansion."""
        return [dna for dna in self.dna_pool.values() if dna.should_expand]
    
    def expand_to_outline(self, dna: ShortDNA) -> DocumentaryOutline:
        """
        Expand winning Short DNA into documentary outline.
        This is the bridge from Shorts to long-form.
        """
        # 5-Act structure
        acts = [
            {
                "name": "hook",
                "duration_minutes": 2,
                "description": f"Open with the core claim from '{dna.topic}'",
                "visual_intent": dna.visual_dna.intent,
                "intensity": "extreme",
                "key_points": [
                    "Most provocative claim first",
                    "Create immediate tension",
                    "Make viewer feel something is hidden"
                ]
            },
            {
                "name": "mechanism", 
                "duration_minutes": 4,
                "description": "Explain HOW this system actually works",
                "visual_intent": "systems_control",
                "intensity": "educational",
                "key_points": [
                    "Concrete examples",
                    "Step-by-step breakdown",
                    "Build understanding"
                ]
            },
            {
                "name": "players",
                "duration_minutes": 4,
                "description": "Who designed this and who benefits",
                "visual_intent": "power_finance",
                "intensity": "narrative",
                "key_points": [
                    "Historical context",
                    "Key players named",
                    "Pattern recognition"
                ]
            },
            {
                "name": "consequences",
                "duration_minutes": 4,
                "description": "Why this affects the viewer personally",
                "visual_intent": "future_warning",
                "intensity": "escalating",
                "key_points": [
                    "Personal relevance",
                    "Future implications",
                    "Escalate stakes"
                ]
            },
            {
                "name": "resolution",
                "duration_minutes": 3,
                "description": "Strategic understanding (not motivation)",
                "visual_intent": dna.visual_dna.intent,
                "intensity": "conclusive",
                "key_points": [
                    "Intellectual closure",
                    "No false hope",
                    "Leave them thinking"
                ]
            }
        ]
        
        # Visual requirements per act
        visual_requirements = [
            {"act": "hook", "type": "real_broll", "categories": ["money", "city"]},
            {"act": "mechanism", "type": "diagrams", "categories": ["tech", "data"]},
            {"act": "players", "type": "real_broll", "categories": ["people", "city"]},
            {"act": "consequences", "type": "real_broll", "categories": ["tech", "city"]},
            {"act": "resolution", "type": "real_broll", "categories": ["money", "lifestyle"]},
        ]
        
        # Music cues
        music_cues = [
            {"act": "hook", "mood": "tension", "intensity": 0.8},
            {"act": "mechanism", "mood": "educational", "intensity": 0.4},
            {"act": "players", "mood": "dramatic", "intensity": 0.6},
            {"act": "consequences", "mood": "urgency", "intensity": 0.9},
            {"act": "resolution", "mood": "contemplative", "intensity": 0.3},
        ]
        
        outline = DocumentaryOutline(
            source_dna=dna,
            title=f"The Truth About {dna.topic}",
            thesis=f"Exposing the hidden mechanics of {dna.topic.lower()}",
            acts=acts,
            total_duration_minutes=17,
            visual_requirements=visual_requirements,
            music_cues=music_cues
        )
        
        print(f"[DNA] 📜 Outline created: {outline.title}")
        return outline
    
    def get_dominant_dna(self) -> Optional[VisualDNA]:
        """
        Get the most successful visual DNA profile.
        This is what gets cloned to new channels.
        """
        winners = self.get_winners()
        if not winners:
            return None
        
        # Sort by RPM (most important metric)
        winners.sort(key=lambda x: x.rpm, reverse=True)
        return winners[0].visual_dna
    
    def mutate_dna(self, dna: ShortDNA) -> ShortDNA:
        """
        Create a mutated version of DNA for A/B testing.
        Winners get subtle mutations, losers get aggressive mutations.
        """
        import random
        
        # Clone the visual DNA
        new_visual = VisualDNA(
            intent=dna.visual_dna.intent,
            pacing=dna.visual_dna.pacing,
            motion_density=dna.visual_dna.motion_density,
            color_mood=dna.visual_dna.color_mood,
            scene_duration=dna.visual_dna.scene_duration,
            cut_frequency=dna.visual_dna.cut_frequency
        )
        
        # Mutation strength based on performance
        if dna.is_winner:
            # Subtle mutation for winners
            mutation_strength = 0.1
        else:
            # Aggressive mutation for losers
            mutation_strength = 0.3
        
        # Mutate scene duration
        new_visual.scene_duration *= (1 + random.uniform(-mutation_strength, mutation_strength))
        new_visual.scene_duration = max(0.8, min(3.0, new_visual.scene_duration))
        
        # Mutate cut frequency
        new_visual.cut_frequency *= (1 + random.uniform(-mutation_strength, mutation_strength))
        new_visual.cut_frequency = max(10, min(40, new_visual.cut_frequency))
        
        # Occasionally mutate pacing
        if random.random() < mutation_strength:
            pacings = ["aggressive", "measured", "contemplative"]
            new_visual.pacing = random.choice(pacings)
        
        # Create mutated DNA
        mutated = ShortDNA(
            video_id=f"{dna.video_id}_mutant_{dna.times_mutated + 1}",
            topic=dna.topic,
            hook_type=dna.hook_type,
            emotional_trigger=dna.emotional_trigger,
            visual_dna=new_visual,
            script_hash=dna.script_hash,
            times_mutated=dna.times_mutated + 1
        )
        
        return mutated


# Singleton instance
_expander = None

def get_expander() -> DNAExpander:
    """Get or create the DNA expander singleton."""
    global _expander
    if _expander is None:
        _expander = DNAExpander()
    return _expander


if __name__ == "__main__":
    expander = DNAExpander()
    print("DNA Expander v1.0")
    print(f"DNA Pool: {len(expander.dna_pool)} profiles")
    print(f"Winners: {len(expander.get_winners())}")
    print(f"Expansion Candidates: {len(expander.get_expansion_candidates())}")
