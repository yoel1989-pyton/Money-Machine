"""
===============================================================================
VISUAL GROUNDING ENGINE - Word-Locked Semantic Visuals
===============================================================================
Converts abstract script "intents" into concrete visual tokens.

Instead of:
  "Make a cinematic visual about control"
  
We now ask:
  "Show credit card statement, interest graph, man staring at red debt numbers"

This is the difference between vibes and explanation.
===============================================================================
"""

import re
import math
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class GroundedVisual:
    """A visual prompt grounded in script words."""
    visual_prompt: str
    mode: str  # word, sentence, cinematic
    keyword: Optional[str] = None
    duration: float = 1.5
    original_text: str = ""


# High-signal noun dictionary - expand over time based on performance
VISUAL_MAP = {
    # FINANCE / MONEY
    "debt": ["credit card statement closeup", "negative balance screen glowing red", "pile of bills and statements"],
    "interest": ["compound interest graph rising", "percentage numbers climbing", "calculator showing growing debt"],
    "bank": ["bank vault door closing", "financial institution marble lobby", "ATM screen declining transaction"],
    "credit": ["credit card being swiped", "credit score meter", "approved vs denied stamps"],
    "loan": ["loan application form", "handshake in bank office", "mortgage documents"],
    "mortgage": ["house with sold sign", "monthly payment breakdown", "family looking at bills"],
    "savings": ["piggy bank cracking", "savings account balance", "money jar half empty"],
    "investment": ["stock chart rising", "portfolio dashboard", "compound growth visualization"],
    "compound": ["exponential growth curve", "money doubling animation", "snowball effect visual"],
    "inflation": ["dollar bill shrinking", "grocery prices rising", "purchasing power graph declining"],
    
    # WEALTH / POWER
    "rich": ["private jet interior", "luxury penthouse view", "wealthy businessman in tailored suit"],
    "wealthy": ["mansion exterior at sunset", "luxury car collection", "champagne toast in boardroom"],
    "poor": ["empty wallet closeup", "declined card notification", "man checking bank app worried"],
    "broke": ["overdrawn account alert", "empty fridge", "counting coins on table"],
    "millionaire": ["portfolio showing millions", "business owner at desk", "multiple income streams diagram"],
    "billionaire": ["skyscraper ownership view", "private island aerial", "empire visualization"],
    
    # SYSTEM / CONTROL
    "system": ["financial flowchart diagram", "interconnected gears mechanism", "network grid visualization"],
    "control": ["puppet strings from above", "surveillance camera watching", "hands gripping control panel"],
    "trap": ["mouse trap with cheese", "cage closing", "quicksand visual"],
    "hidden": ["iceberg showing hidden mass", "behind curtain reveal", "locked door with key"],
    "secret": ["classified folder opening", "whispered conversation", "hidden mechanism exposed"],
    "exposed": ["spotlight on truth", "curtain being pulled back", "mask being removed"],
    "rigged": ["loaded dice", "fixed scale", "stacked deck of cards"],
    
    # TIME / URGENCY
    "time": ["clock spinning fast", "calendar pages flipping", "hourglass running out"],
    "years": ["timeline visualization", "age progression", "decades passing montage"],
    "future": ["crystal ball", "road stretching ahead", "sunrise on horizon"],
    "past": ["old photographs", "rearview mirror", "history book pages"],
    "now": ["present moment indicator", "today circled on calendar", "urgent red button"],
    
    # EMOTION / ACTION
    "escape": ["chains breaking apart", "door opening to bright light", "man walking toward freedom"],
    "freedom": ["bird flying from cage", "open road ahead", "breaking free gesture"],
    "fear": ["shadow looming", "worried face closeup", "storm clouds gathering"],
    "hope": ["light at end of tunnel", "sunrise breaking through", "plant growing from concrete"],
    "truth": ["scale of justice", "lie detector", "mirror reflection"],
    "lie": ["crossed fingers behind back", "fake smile closeup", "crumbling facade"],
    
    # EDUCATION / KNOWLEDGE
    "learn": ["lightbulb moment", "book opening", "mind expanding visualization"],
    "understand": ["puzzle pieces connecting", "aha moment", "clarity emerging from fog"],
    "knowledge": ["library of information", "brain with connections", "key to locked door"],
    "ignorance": ["blindfold on person", "fog covering path", "question marks floating"],
    
    # PEOPLE / SOCIETY
    "people": ["crowd in city", "diverse faces", "society overhead view"],
    "government": ["capitol building", "official documents", "legislation gavel"],
    "corporation": ["corporate tower", "boardroom meeting", "logo on building"],
    "elite": ["exclusive club entrance", "velvet rope", "private members only sign"],
    "middle class": ["suburban home", "9 to 5 commute", "average family budget"],
    "working": ["office cubicle", "factory floor", "tired worker at desk"],
}

# Style modifiers for different modes
MODE_SUFFIXES = {
    "word": ", ultra-realistic, explanatory, documentary style, clear subject, no abstraction, professional lighting, 4k quality",
    "sentence": ", cinematic, professional, clear composition, documentary realism, no text, vertical 9:16",
    "cinematic": ", cinematic metaphor, artistic interpretation, dramatic lighting, film grain, emotional impact",
}


def extract_keywords(text: str) -> List[str]:
    """Extract all matching keywords from text."""
    text_lower = text.lower()
    found = []
    for keyword in VISUAL_MAP:
        if re.search(rf"\b{keyword}\b", text_lower):
            found.append(keyword)
    return found


def get_best_visual(keywords: List[str], used_visuals: set = None) -> tuple:
    """Get the best visual for given keywords, avoiding repeats."""
    used_visuals = used_visuals or set()
    
    for keyword in keywords:
        visuals = VISUAL_MAP.get(keyword, [])
        for visual in visuals:
            if visual not in used_visuals:
                return keyword, visual
    
    # Fallback: return first available even if used
    if keywords and keywords[0] in VISUAL_MAP:
        return keywords[0], VISUAL_MAP[keywords[0]][0]
    
    return None, None


def calculate_duration(text: str) -> float:
    """Calculate scene duration based on word count."""
    words = len(text.split())
    return max(1.2, round(words * 0.28, 2))


def build_visual_plan(
    script_lines: List[str],
    mode: str = "sentence",
    topic: str = ""
) -> List[GroundedVisual]:
    """
    Build a complete visual plan from script lines.
    
    Modes:
        - word: Every keyword gets its own visual (educational)
        - sentence: One visual per sentence (shorts-optimized)
        - hybrid: Word-level first 40%, cinematic rest (authority)
    """
    scenes = []
    used_visuals = set()
    
    # Clean script lines
    script_lines = [line.strip() for line in script_lines if line.strip()]
    
    if mode == "word":
        # WORD-LEVEL: Every keyword gets a visual
        for line in script_lines:
            keywords = extract_keywords(line)
            if keywords:
                for keyword in keywords[:2]:  # Max 2 visuals per line
                    _, visual = get_best_visual([keyword], used_visuals)
                    if visual:
                        used_visuals.add(visual)
                        scenes.append(GroundedVisual(
                            visual_prompt=visual + MODE_SUFFIXES["word"],
                            mode="word",
                            keyword=keyword,
                            duration=calculate_duration(line) / max(1, len(keywords)),
                            original_text=line
                        ))
            else:
                # No keywords - use line as abstract prompt
                scenes.append(GroundedVisual(
                    visual_prompt=f"visual representation of: {line[:100]}" + MODE_SUFFIXES["word"],
                    mode="word",
                    duration=calculate_duration(line),
                    original_text=line
                ))
    
    elif mode == "sentence":
        # SENTENCE-LEVEL: One best visual per sentence
        for line in script_lines:
            keywords = extract_keywords(line)
            keyword, visual = get_best_visual(keywords, used_visuals)
            
            if visual:
                used_visuals.add(visual)
                scenes.append(GroundedVisual(
                    visual_prompt=visual + MODE_SUFFIXES["sentence"],
                    mode="sentence",
                    keyword=keyword,
                    duration=calculate_duration(line),
                    original_text=line
                ))
            else:
                # Fallback to abstract
                scenes.append(GroundedVisual(
                    visual_prompt=f"cinematic scene about: {line[:80]}" + MODE_SUFFIXES["sentence"],
                    mode="sentence",
                    duration=calculate_duration(line),
                    original_text=line
                ))
    
    elif mode == "hybrid":
        # HYBRID: Word-level first 40%, cinematic rest
        cutoff = math.ceil(len(script_lines) * 0.4)
        
        for i, line in enumerate(script_lines):
            keywords = extract_keywords(line)
            
            if i < cutoff:
                # First 40%: Word-level grounding (build trust)
                keyword, visual = get_best_visual(keywords, used_visuals)
                if visual:
                    used_visuals.add(visual)
                    scenes.append(GroundedVisual(
                        visual_prompt=visual + MODE_SUFFIXES["word"],
                        mode="word",
                        keyword=keyword,
                        duration=calculate_duration(line),
                        original_text=line
                    ))
                else:
                    scenes.append(GroundedVisual(
                        visual_prompt=f"documentary scene: {line[:80]}" + MODE_SUFFIXES["word"],
                        mode="word",
                        duration=calculate_duration(line),
                        original_text=line
                    ))
            else:
                # Remaining 60%: Cinematic (build emotion)
                if keywords:
                    keyword = keywords[0]
                    scenes.append(GroundedVisual(
                        visual_prompt=f"cinematic metaphor of {keyword}: {line[:60]}" + MODE_SUFFIXES["cinematic"],
                        mode="cinematic",
                        keyword=keyword,
                        duration=calculate_duration(line),
                        original_text=line
                    ))
                else:
                    scenes.append(GroundedVisual(
                        visual_prompt=f"dramatic visualization: {line[:80]}" + MODE_SUFFIXES["cinematic"],
                        mode="cinematic",
                        duration=calculate_duration(line),
                        original_text=line
                    ))
    
    return scenes


def validate_visual_prompt(scene: GroundedVisual) -> GroundedVisual:
    """
    Self-healing: Ensure word-mode visuals don't contain abstract terms.
    """
    if scene.mode == "word":
        abstract_terms = ["abstract", "metaphor", "symbolic", "ethereal", "conceptual"]
        if any(term in scene.visual_prompt.lower() for term in abstract_terms):
            # Force literal interpretation
            if scene.keyword and scene.keyword in VISUAL_MAP:
                scene.visual_prompt = VISUAL_MAP[scene.keyword][0] + MODE_SUFFIXES["word"]
    
    return scene


# =============================================================================
# STANDALONE TEST
# =============================================================================

if __name__ == "__main__":
    test_script = """
    Banks don't want you to understand how interest really works.
    They profit when you stay in debt.
    The rich use this system completely differently.
    They leverage debt as a wealth-building tool.
    While you pay interest, they collect it.
    This is the hidden mechanism of wealth transfer.
    Once you understand this, everything changes.
    """
    
    lines = [l.strip() for l in test_script.strip().split(".") if l.strip()]
    
    print("=" * 60)
    print("VISUAL GROUNDING TEST")
    print("=" * 60)
    
    for mode in ["word", "sentence", "hybrid"]:
        print(f"\n📌 MODE: {mode.upper()}")
        print("-" * 40)
        plan = build_visual_plan(lines, mode=mode)
        for i, scene in enumerate(plan[:5]):  # Show first 5
            print(f"  [{i+1}] {scene.mode}: {scene.visual_prompt[:60]}...")
            print(f"       Duration: {scene.duration}s | Keyword: {scene.keyword}")
