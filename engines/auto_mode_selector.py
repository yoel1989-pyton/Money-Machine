"""
===============================================================================
AUTO MODE SELECTOR - Intelligent Visual Mode Switching
===============================================================================
Automatically selects the optimal visual grounding mode based on:
- Trust score history
- Retention patterns
- Average view duration
- Channel performance trends

Modes:
- word: Educational, literal visuals (trust recovery)
- sentence: Fast, shorts-optimized (engagement)
- hybrid: Authority building (scale)
===============================================================================
"""

from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class ModeDecision:
    """Result of auto mode selection."""
    mode: str
    confidence: float
    reasoning: str
    adjustments: Dict


def select_visual_mode(
    trust_score: float = 0.5,
    retention_curve: Optional[List[float]] = None,
    avg_view_duration: float = 0.5,
    recent_performance: Optional[Dict] = None
) -> ModeDecision:
    """
    Automatically select the optimal visual mode.
    
    Args:
        trust_score: Current Gemini trust score (0-1)
        retention_curve: Retention % per second
        avg_view_duration: Average view duration as % of total
        recent_performance: Dict with recent video metrics
    
    Returns:
        ModeDecision with selected mode and reasoning
    """
    retention_curve = retention_curve or []
    recent_performance = recent_performance or {}
    
    # Detect early drop (viewers leaving in first 5 seconds)
    early_drop = False
    if len(retention_curve) > 5:
        initial = retention_curve[0] if retention_curve else 100
        at_5s = retention_curve[5] if len(retention_curve) > 5 else initial
        if initial - at_5s > 8:
            early_drop = True
    
    # Detect mid-video collapse
    mid_collapse = False
    if len(retention_curve) > 15:
        mid_point = len(retention_curve) // 2
        if retention_curve[mid_point] < 50:
            mid_collapse = True
    
    # Decision logic
    
    # CASE 1: LOW TRUST or EARLY DROP → EDUCATIONAL (word mode)
    if trust_score < 0.45 or early_drop:
        return ModeDecision(
            mode="word",
            confidence=0.85,
            reasoning="Low trust or early viewer drop detected. Switching to educational mode to rebuild credibility.",
            adjustments={
                "pacing": "slow",
                "tone": "explanatory",
                "visuals": "literal",
                "hooks": "value-first"
            }
        )
    
    # CASE 2: GOOD TRUST BUT LOW COMPLETION → SHORTS MODE (sentence)
    if trust_score >= 0.5 and avg_view_duration < 0.55:
        return ModeDecision(
            mode="sentence",
            confidence=0.80,
            reasoning="Trust is adequate but completion is low. Optimizing for Shorts-style quick engagement.",
            adjustments={
                "pacing": "fast",
                "tone": "punchy",
                "visuals": "clear",
                "hooks": "pattern-interrupt"
            }
        )
    
    # CASE 3: MID-VIDEO COLLAPSE → HYBRID (rebuild then cinematic)
    if mid_collapse:
        return ModeDecision(
            mode="hybrid",
            confidence=0.75,
            reasoning="Mid-video retention collapse. Using hybrid mode: educate first, then go cinematic.",
            adjustments={
                "pacing": "variable",
                "tone": "progressive",
                "visuals": "grounded-to-abstract",
                "hooks": "retention-focused"
            }
        )
    
    # CASE 4: HIGH TRUST + GOOD RETENTION → SCALE MODE (hybrid)
    if trust_score >= 0.6 and avg_view_duration >= 0.6:
        return ModeDecision(
            mode="hybrid",
            confidence=0.90,
            reasoning="Strong trust and retention. Using hybrid mode for authority building at scale.",
            adjustments={
                "pacing": "confident",
                "tone": "authoritative",
                "visuals": "grounded-to-cinematic",
                "hooks": "session-chaining"
            }
        )
    
    # DEFAULT: Balanced approach (sentence mode)
    return ModeDecision(
        mode="sentence",
        confidence=0.70,
        reasoning="Metrics are balanced. Using sentence mode for general optimization.",
        adjustments={
            "pacing": "moderate",
            "tone": "engaging",
            "visuals": "clear",
            "hooks": "standard"
        }
    )


def get_mode_from_history(
    video_history: List[Dict],
    window_size: int = 5
) -> str:
    """
    Analyze recent video performance to determine optimal mode.
    
    Args:
        video_history: List of dicts with {mode, views, retention, trust}
        window_size: Number of recent videos to analyze
    
    Returns:
        Recommended mode based on what's working
    """
    if not video_history:
        return "sentence"  # Safe default
    
    # Get recent videos
    recent = video_history[-window_size:]
    
    # Group by mode
    mode_performance = {}
    for video in recent:
        mode = video.get("mode", "sentence")
        if mode not in mode_performance:
            mode_performance[mode] = {
                "count": 0,
                "total_views": 0,
                "total_retention": 0,
                "total_trust": 0
            }
        
        mode_performance[mode]["count"] += 1
        mode_performance[mode]["total_views"] += video.get("views", 0)
        mode_performance[mode]["total_retention"] += video.get("retention", 0.5)
        mode_performance[mode]["total_trust"] += video.get("trust", 0.5)
    
    # Calculate averages
    best_mode = "sentence"
    best_score = 0
    
    for mode, data in mode_performance.items():
        if data["count"] > 0:
            avg_views = data["total_views"] / data["count"]
            avg_retention = data["total_retention"] / data["count"]
            avg_trust = data["total_trust"] / data["count"]
            
            # Composite score
            score = (avg_views / 1000) + (avg_retention * 50) + (avg_trust * 30)
            
            if score > best_score:
                best_score = score
                best_mode = mode
    
    return best_mode


def should_switch_mode(
    current_mode: str,
    current_trust: float,
    current_retention: float,
    mode_history: List[str]
) -> bool:
    """
    Determine if mode should be switched for next video.
    Prevents excessive mode-switching while allowing adaptation.
    """
    # Don't switch if doing well
    if current_trust >= 0.65 and current_retention >= 0.60:
        return False
    
    # Don't switch if just switched
    if len(mode_history) >= 2 and mode_history[-1] != mode_history[-2]:
        return False
    
    # Switch if struggling
    if current_trust < 0.4 or current_retention < 0.45:
        return True
    
    # Occasional exploration (10% chance)
    import random
    return random.random() < 0.10


# =============================================================================
# STANDALONE TEST
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("AUTO MODE SELECTOR TEST")
    print("=" * 60)
    
    # Test scenarios
    scenarios = [
        {"trust": 0.3, "retention": [100, 95, 85, 70, 60], "avg_duration": 0.4, "name": "Low Trust + Early Drop"},
        {"trust": 0.6, "retention": [100, 98, 95, 92, 88], "avg_duration": 0.5, "name": "Good Trust, Low Completion"},
        {"trust": 0.75, "retention": [100, 98, 96, 94, 92], "avg_duration": 0.7, "name": "High Performance"},
        {"trust": 0.55, "retention": [100, 95, 90, 60, 50], "avg_duration": 0.55, "name": "Mid-Video Collapse"},
    ]
    
    for scenario in scenarios:
        decision = select_visual_mode(
            trust_score=scenario["trust"],
            retention_curve=scenario["retention"],
            avg_view_duration=scenario["avg_duration"]
        )
        
        print(f"\n📌 {scenario['name']}:")
        print(f"   Mode: {decision.mode.upper()}")
        print(f"   Confidence: {decision.confidence:.0%}")
        print(f"   Reasoning: {decision.reasoning}")
