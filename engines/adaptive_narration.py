"""
===============================================================================
ADAPTIVE NARRATION ENGINE - Self-Healing Script Optimization
===============================================================================
Mutates scripts based on:
- Viewer drop-off points
- Trust score calibration
- Gemini feedback signals

The system learns to speak like a human creator who improves over time.
===============================================================================
"""

import random
from typing import List, Dict, Optional


# Drop-off recovery phrases - injected before problem points
DROP_OFF_REPLACEMENTS = {
    "weak_hook": [
        "Here's the part they never explain.",
        "Most people miss this completely.",
        "This is where the system flips.",
        "Pay attention to what comes next.",
        "Here's what actually matters.",
    ],
    "slow_explanation": [
        "Stay with me — this part matters.",
        "This sounds simple, but it changes everything.",
        "Watch what happens next.",
        "This is the key insight.",
        "Here's where it gets interesting.",
    ],
    "confusing": [
        "Let me make this clear.",
        "Here's the simple version.",
        "Think of it like this.",
        "In plain terms:",
        "Simply put:",
    ],
    "low_energy": [
        "And here's the real kicker.",
        "But wait — it gets better.",
        "Now here's the twist.",
        "This is what they hide.",
        "But that's not even the worst part.",
    ],
}

# Trust calibration phrases
TRUST_DOWNGRADES = {
    "they don't want you to know": "most people aren't told",
    "this will change your life": "this explains why it works",
    "the secret they're hiding": "what's often overlooked",
    "you're being manipulated": "systems influence behavior",
    "they control you": "external forces shape choices",
    "wake up": "consider this",
    "exposed": "explained",
    "shocking truth": "important reality",
    "conspiracy": "pattern",
}

TRUST_UPGRADES = {
    "explained": "revealed",
    "important": "critical",
    "consider": "understand",
    "pattern": "hidden mechanism",
    "influences": "shapes",
    "often": "deliberately",
}


def detect_weak_sections(script_lines: List[str]) -> Dict[int, str]:
    """
    Analyze script for potential weak points.
    Returns dict of {line_index: weakness_type}
    """
    weak_points = {}
    
    for i, line in enumerate(script_lines):
        line_lower = line.lower()
        
        # First line weak hook detection
        if i == 0:
            if len(line.split()) < 5:
                weak_points[i] = "weak_hook"
            elif not any(w in line_lower for w in ["?", "!", "you", "why", "how", "what"]):
                weak_points[i] = "weak_hook"
        
        # Long explanatory sections
        if len(line.split()) > 20:
            weak_points[i] = "slow_explanation"
        
        # Jargon detection
        jargon = ["leverage", "compound", "arbitrage", "yield", "liquidity"]
        if sum(1 for j in jargon if j in line_lower) >= 2:
            weak_points[i] = "confusing"
        
        # Energy dips (multiple mid-script)
        if i > 2 and i < len(script_lines) - 2:
            if not any(p in line for p in [".", "!", "?"]):
                weak_points[i] = "low_energy"
    
    return weak_points


def mutate_script(
    script_lines: List[str],
    drop_off_points: Optional[List[int]] = None,
    trust_score: float = 0.5,
    weak_sections: Optional[Dict[int, str]] = None
) -> List[str]:
    """
    Mutate script based on performance feedback.
    
    Args:
        script_lines: List of script sentences
        drop_off_points: Indices where viewers dropped off
        trust_score: Current Gemini trust score (0-1)
        weak_sections: Pre-detected weak sections
    
    Returns:
        Mutated script lines
    """
    drop_off_points = drop_off_points or []
    weak_sections = weak_sections or detect_weak_sections(script_lines)
    
    mutated = []
    
    for i, line in enumerate(script_lines):
        # Inject reinforcement BEFORE drop-off points
        if i in drop_off_points:
            weakness_type = weak_sections.get(i, "slow_explanation")
            reinforcement = random.choice(DROP_OFF_REPLACEMENTS.get(weakness_type, DROP_OFF_REPLACEMENTS["slow_explanation"]))
            mutated.append(reinforcement)
        
        # Apply trust calibration
        if trust_score < 0.45:
            # Reduce aggressive language for low trust
            for old, new in TRUST_DOWNGRADES.items():
                line = line.replace(old, new)
                line = line.replace(old.capitalize(), new.capitalize())
        elif trust_score > 0.7:
            # Increase authority for high trust
            for old, new in TRUST_UPGRADES.items():
                line = line.replace(old, new)
        
        mutated.append(line)
    
    return mutated


def inject_retention_hooks(script_lines: List[str]) -> List[str]:
    """
    Add retention hooks at strategic points.
    """
    if len(script_lines) < 3:
        return script_lines
    
    result = []
    
    for i, line in enumerate(script_lines):
        result.append(line)
        
        # After first quarter: tease what's coming
        if i == len(script_lines) // 4:
            result.append("But here's where it gets interesting.")
        
        # Midpoint: reinforce value
        if i == len(script_lines) // 2:
            result.append("Stay with me on this.")
        
        # Before final payoff
        if i == len(script_lines) - 2:
            result.append("And this is the key insight:")
    
    return result


def add_session_hooks(script_lines: List[str]) -> List[str]:
    """
    Add end hooks that boost session time.
    """
    session_hooks = [
        "What I just showed you is only part of it. The next system is even more powerful.",
        "This is just the beginning. There's something else they don't want you to see.",
        "Now that you understand this, everything else starts to make sense.",
        "Remember what you just learned. It connects to something bigger.",
        "This is why understanding the system changes everything.",
    ]
    
    if script_lines:
        script_lines.append(random.choice(session_hooks))
    
    return script_lines


def full_script_mutation(
    script: str,
    drop_off_points: Optional[List[int]] = None,
    trust_score: float = 0.5,
    add_hooks: bool = True
) -> str:
    """
    Complete script mutation pipeline.
    """
    # Split into lines
    lines = [l.strip() for l in script.replace("\n", " ").split(".") if l.strip()]
    
    # Detect weak sections
    weak_sections = detect_weak_sections(lines)
    
    # Apply mutations
    lines = mutate_script(lines, drop_off_points, trust_score, weak_sections)
    
    # Add retention hooks
    if add_hooks:
        lines = inject_retention_hooks(lines)
        lines = add_session_hooks(lines)
    
    # Rejoin
    return ". ".join(lines)


# =============================================================================
# STANDALONE TEST
# =============================================================================

if __name__ == "__main__":
    test_script = """
    Banks profit from your ignorance.
    They don't want you to know how interest compounds.
    The rich use debt as a weapon.
    While you save, they leverage.
    This is the hidden mechanism of wealth transfer.
    Once you understand this, everything changes.
    """
    
    print("=" * 60)
    print("ADAPTIVE NARRATION TEST")
    print("=" * 60)
    
    # Test with low trust
    print("\n📉 LOW TRUST (0.3):")
    result_low = full_script_mutation(test_script, trust_score=0.3)
    print(result_low[:300] + "...")
    
    # Test with high trust
    print("\n📈 HIGH TRUST (0.8):")
    result_high = full_script_mutation(test_script, trust_score=0.8)
    print(result_high[:300] + "...")
    
    # Test with drop-off points
    print("\n⚠️ WITH DROP-OFF AT LINE 2:")
    result_drop = full_script_mutation(test_script, drop_off_points=[2], trust_score=0.5)
    print(result_drop[:400] + "...")
