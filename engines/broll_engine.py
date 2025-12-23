"""
B-ROLL ENGINE - Keyword-Matched Real Footage
Maps script keywords to visual categories.
"""

import os
import random
from pathlib import Path
from typing import Dict, List, Optional, Set
import re

DEFAULT_BROLL_DIR = Path(__file__).parent.parent / "data" / "assets" / "backgrounds"

KEYWORD_TO_VISUAL = {
    "money": "money", "wealth": "money", "rich": "money", "million": "money", "billion": "money",
    "dollar": "money", "cash": "money", "bank": "money", "invest": "money", "stocks": "money",
    "crypto": "money", "bitcoin": "money", "gold": "money", "profit": "money", "income": "money",
    "salary": "money", "debt": "money", "broke": "money", "poor": "money", "tax": "money",
    "city": "city", "urban": "city", "downtown": "city", "skyline": "city", "street": "city",
    "building": "city", "real estate": "city", "property": "city", "new york": "city",
    "technology": "tech", "tech": "tech", "computer": "tech", "laptop": "tech", "phone": "tech",
    "screen": "tech", "data": "tech", "ai": "tech", "automation": "tech", "digital": "tech",
    "luxury": "lifestyle", "car": "lifestyle", "house": "lifestyle", "travel": "lifestyle",
    "freedom": "lifestyle", "success": "lifestyle", "goal": "lifestyle", "dream": "lifestyle",
    "people": "people", "person": "people", "man": "people", "woman": "people", "family": "people",
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
