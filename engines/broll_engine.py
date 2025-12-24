"""
B-ROLL ENGINE - Visual Intent Matched Footage
Maps script keywords AND visual_intent to real footage categories.
ELITE MODE: Scene-aware, semantic matching, no random garbage.
"""

import os
import random
from pathlib import Path
from typing import Dict, List, Optional, Set
import re

DEFAULT_BROLL_DIR = Path(__file__).parent.parent / "data" / "assets" / "backgrounds"

# Keyword to category mapping
KEYWORD_TO_VISUAL = {
    "money": "money", "wealth": "money", "rich": "money", "million": "money", "billion": "money",
    "dollar": "money", "cash": "money", "bank": "money", "invest": "money", "stocks": "money",
    "crypto": "money", "bitcoin": "money", "gold": "money", "profit": "money", "income": "money",
    "salary": "money", "debt": "money", "broke": "money", "poor": "money", "tax": "money",
    "city": "city", "urban": "city", "downtown": "city", "skyline": "city", "street": "city",
    "building": "city", "real estate": "city", "property": "city", "new york": "city",
    "technology": "tech", "tech": "tech", "computer": "tech", "laptop": "tech", "phone": "tech",
    "screen": "tech", "data": "tech", "ai": "tech", "automation": "tech", "digital": "tech",
    "algorithm": "tech", "system": "tech", "machine": "tech",
    "luxury": "lifestyle", "car": "lifestyle", "house": "lifestyle", "travel": "lifestyle",
    "freedom": "lifestyle", "success": "lifestyle", "goal": "lifestyle", "dream": "lifestyle",
    "people": "people", "person": "people", "man": "people", "woman": "people", "family": "people",
    "brain": "people", "psychology": "people", "mind": "people", "think": "people",
}

# ELITE: Visual intent to B-roll category mapping (scene-aware)
# Gold Standard: Kiyosaki, Graham Stephan, Andrei Jikh, Minority Mindset
VISUAL_INTENT_TO_CATEGORY = {
    # ============================================================
    # GOLD STANDARD ARCHETYPES (from research)
    # ============================================================
    
    # Kiyosaki/Hidden Secrets: System reveals, power structures
    "power_finance": ["money", "city"],
    "systems_control": ["tech", "city", "money"],
    
    # Graham Stephan: Lifestyle arbitrage, wealth hacks
    "wealth_hacks": ["money", "lifestyle", "city"],
    "lifestyle_arbitrage": ["lifestyle", "money", "city"],
    
    # Andrei Jikh: Psychology, comparative narratives
    "psychology": ["people", "tech"],
    "comparative": ["people", "money", "tech"],
    
    # Minority Mindset: Hidden rules, tax logic
    "hidden_rules": ["money", "city", "tech"],
    "tax_logic": ["money", "city"],
    
    # ============================================================
    # ORIGINAL INTENTS (proven)
    # ============================================================
    
    # Finance/Power
    "wealth": ["money", "lifestyle"],
    "banking": ["money", "city"],
    "elite_finance": ["money", "city", "lifestyle"],
    
    # Systems/Control
    "surveillance": ["tech", "city"],
    "automation": ["tech"],
    "data_flows": ["tech"],
    
    # Future/Warning
    "future_warning": ["tech", "city"],
    "dystopian": ["city", "tech"],
    "collapse": ["city"],
    "urgency": ["city", "tech"],
    
    # Psychology/People
    "human": ["people", "lifestyle"],
    "emotion": ["people"],
    "decision": ["people", "tech"],
    
    # Documentary/History
    "documentary": ["city", "people"],
    "history": ["city", "people"],
    "narrative": ["city", "lifestyle"],
    
    # Default fallbacks
    "default": ["money", "tech", "city"],
}


def extract_visual_keywords(script: str) -> Dict[str, str]:
    """Extract visual keywords from script and map to categories."""
    script_lower = script.lower()
    found = {}
    for keyword, category in KEYWORD_TO_VISUAL.items():
        if re.search(rf'\b{re.escape(keyword)}\b', script_lower):
            found[keyword] = category
    return found


class BRollEngine:
    def __init__(self, broll_dir: str = None):
        self.broll_dir = Path(broll_dir or DEFAULT_BROLL_DIR)
        self.broll_dir.mkdir(parents=True, exist_ok=True)
        self._clip_cache: Dict[str, List[str]] = {}
        self._refresh_cache()
    
    def _refresh_cache(self):
        self._clip_cache = {}
        for category_dir in self.broll_dir.iterdir():
            if not category_dir.is_dir() or "_deprecated" in category_dir.name:
                continue
            clips = [str(f) for f in category_dir.iterdir() if f.suffix.lower() in [".mp4", ".mov", ".webm"]]
            if clips:
                self._clip_cache[category_dir.name] = clips
    
    async def get_clip(self, category: str = None, exclude: Set[str] = None) -> Optional[str]:
        exclude = exclude or set()
        if category and category in self._clip_cache:
            available = [c for c in self._clip_cache[category] if c not in exclude]
            if available:
                return random.choice(available)
        all_clips = [c for clips in self._clip_cache.values() for c in clips if c not in exclude]
        return random.choice(all_clips) if all_clips else None
    
    async def get_clip_for_intent(self, visual_intent: str, exclude: Set[str] = None) -> Optional[str]:
        """
        ELITE: Get B-roll matched to visual_intent (scene-aware).
        This is what separates elite videos from garbage.
        """
        exclude = exclude or set()
        
        # Get preferred categories for this intent
        categories = VISUAL_INTENT_TO_CATEGORY.get(visual_intent, VISUAL_INTENT_TO_CATEGORY["default"])
        
        # Try each category in priority order
        for category in categories:
            if category in self._clip_cache:
                available = [c for c in self._clip_cache[category] if c not in exclude]
                if available:
                    clip = random.choice(available)
                    print(f"[BROLL] Intent '{visual_intent}' → category '{category}' → {Path(clip).name}")
                    return clip
        
        # Fallback to any available clip
        all_clips = [c for clips in self._clip_cache.values() for c in clips if c not in exclude]
        if all_clips:
            clip = random.choice(all_clips)
            print(f"[BROLL] Intent '{visual_intent}' → fallback → {Path(clip).name}")
            return clip
        
        return None
    
    async def get_clips_for_script(self, script: str, num_scenes: int = 3) -> List[str]:
        """
        Analyze script and return matched B-roll clips for each logical scene.
        """
        keywords = extract_visual_keywords(script)
        
        # Determine primary visual intent from keywords
        category_counts = {}
        for keyword, category in keywords.items():
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Get most relevant categories
        sorted_categories = sorted(category_counts.items(), key=lambda x: -x[1])
        primary_categories = [cat for cat, count in sorted_categories[:3]] if sorted_categories else ["money", "tech"]
        
        clips = []
        used = set()
        
        for i in range(num_scenes):
            category = primary_categories[i % len(primary_categories)]
            clip = await self.get_clip(category, exclude=used)
            if clip:
                clips.append(clip)
                used.add(clip)
        
        return clips
    
    async def get_random_clip(self, exclude: Set[str] = None) -> Optional[str]:
        return await self.get_clip(category=None, exclude=exclude)
    
    def get_categories(self) -> List[str]:
        return list(self._clip_cache.keys())
    
    def get_clip_count(self, category: str = None) -> int:
        if category:
            return len(self._clip_cache.get(category, []))
        return sum(len(clips) for clips in self._clip_cache.values())
    
    def status(self) -> Dict:
        return {"total_clips": self.get_clip_count(), "categories": {cat: len(clips) for cat, clips in self._clip_cache.items()}}


def resolve_visual_intent(script: str) -> str:
    """
    Analyze script text and return the best visual_intent for it.
    """
    script_lower = script.lower()
    
    # Intent detection patterns
    intent_patterns = {
        "power_finance": ["bank", "fed", "reserve", "wealth", "billion", "rich"],
        "systems_control": ["system", "algorithm", "control", "design", "rules"],
        "future_warning": ["ai", "obsolete", "future", "collapse", "disappear"],
        "psychology": ["brain", "think", "feel", "psychology", "mind", "fear"],
        "wealth": ["money", "cash", "dollar", "income", "salary"],
    }
    
    scores = {}
    for intent, patterns in intent_patterns.items():
        scores[intent] = sum(1 for p in patterns if p in script_lower)
    
    best_intent = max(scores.items(), key=lambda x: x[1])
    return best_intent[0] if best_intent[1] > 0 else "default"


def resolve_broll(script: str, broll_dir: str = None) -> Dict[str, str]:
    engine = BRollEngine(broll_dir)
    keywords = extract_visual_keywords(script)
    result = {}
    used = set()
    for keyword, category in keywords.items():
        if category in engine._clip_cache:
            available = [c for c in engine._clip_cache[category] if c not in used]
            if available:
                clip = random.choice(available)
                result[keyword] = clip
                used.add(clip)
    return result
