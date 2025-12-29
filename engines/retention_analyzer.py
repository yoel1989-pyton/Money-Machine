"""
===============================================================================
RETENTION ANALYZER - Viewer Drop-Off Detection
===============================================================================
Analyzes YouTube retention curves to find exact moments viewers leave.
Marks lines that need improvement in next generation.
===============================================================================
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class DropOffPoint:
    """A detected viewer drop-off point."""
    second: int
    severity: str  # mild, moderate, severe
    drop_percentage: float
    suggested_fix: str


def detect_drop_off(
    retention_curve: List[float],
    threshold_mild: float = 4.0,
    threshold_moderate: float = 6.0,
    threshold_severe: float = 10.0
) -> List[DropOffPoint]:
    """
    Detect moments where viewers leave.
    
    Args:
        retention_curve: List of retention percentages per second
                        e.g., [100, 98, 95, 92, 85, 80, ...]
        threshold_*: Drop thresholds for severity classification
    
    Returns:
        List of DropOffPoint objects
    """
    if not retention_curve or len(retention_curve) < 3:
        return []
    
    drops = []
    
    for i in range(2, len(retention_curve)):
        drop = retention_curve[i-1] - retention_curve[i]
        
        if drop >= threshold_severe:
            drops.append(DropOffPoint(
                second=i,
                severity="severe",
                drop_percentage=drop,
                suggested_fix="Major content issue - consider complete rewrite of this section"
            ))
        elif drop >= threshold_moderate:
            drops.append(DropOffPoint(
                second=i,
                severity="moderate",
                drop_percentage=drop,
                suggested_fix="Add retention hook before this point"
            ))
        elif drop >= threshold_mild:
            drops.append(DropOffPoint(
                second=i,
                severity="mild",
                drop_percentage=drop,
                suggested_fix="Consider pacing adjustment"
            ))
    
    return drops


def get_drop_off_indices(
    retention_curve: List[float],
    scene_durations: List[float]
) -> List[int]:
    """
    Map drop-off seconds to scene indices.
    
    Args:
        retention_curve: Retention % per second
        scene_durations: Duration of each scene in seconds
    
    Returns:
        List of scene indices where drops occurred
    """
    drops = detect_drop_off(retention_curve)
    if not drops:
        return []
    
    # Build cumulative timeline
    cumulative = []
    total = 0
    for duration in scene_durations:
        total += duration
        cumulative.append(total)
    
    # Map drop seconds to scenes
    drop_indices = []
    for drop in drops:
        for i, end_time in enumerate(cumulative):
            start_time = cumulative[i-1] if i > 0 else 0
            if start_time <= drop.second < end_time:
                if i not in drop_indices:
                    drop_indices.append(i)
                break
    
    return drop_indices


def analyze_retention_pattern(retention_curve: List[float]) -> Dict:
    """
    Comprehensive retention analysis.
    
    Returns:
        Dict with:
        - average_retention: Overall retention %
        - hook_strength: First 5 seconds performance
        - mid_engagement: Middle section performance
        - completion_rate: Final retention
        - problem_zones: List of problematic time ranges
    """
    if not retention_curve or len(retention_curve) < 10:
        return {
            "average_retention": 0,
            "hook_strength": 0,
            "mid_engagement": 0,
            "completion_rate": 0,
            "problem_zones": [],
            "status": "insufficient_data"
        }
    
    # Hook strength (first 5 seconds)
    hook_retention = sum(retention_curve[:5]) / 5 if len(retention_curve) >= 5 else retention_curve[0]
    
    # Mid engagement (25-75% of video)
    mid_start = len(retention_curve) // 4
    mid_end = (len(retention_curve) * 3) // 4
    mid_retention = sum(retention_curve[mid_start:mid_end]) / max(1, mid_end - mid_start)
    
    # Completion rate
    completion = retention_curve[-1] if retention_curve else 0
    
    # Problem zones (consecutive drops)
    drops = detect_drop_off(retention_curve)
    problem_zones = []
    if drops:
        current_zone_start = drops[0].second
        current_zone_end = drops[0].second
        
        for i, drop in enumerate(drops[1:], 1):
            if drop.second - current_zone_end <= 3:
                current_zone_end = drop.second
            else:
                if current_zone_end - current_zone_start >= 2:
                    problem_zones.append({
                        "start": current_zone_start,
                        "end": current_zone_end,
                        "severity": "high" if any(d.severity == "severe" for d in drops) else "moderate"
                    })
                current_zone_start = drop.second
                current_zone_end = drop.second
    
    return {
        "average_retention": sum(retention_curve) / len(retention_curve),
        "hook_strength": hook_retention,
        "mid_engagement": mid_retention,
        "completion_rate": completion,
        "problem_zones": problem_zones,
        "drop_count": len(drops),
        "status": "analyzed"
    }


def suggest_improvements(analysis: Dict) -> List[str]:
    """
    Generate actionable improvement suggestions.
    """
    suggestions = []
    
    if analysis.get("hook_strength", 100) < 85:
        suggestions.append("HOOK: Strengthen first 3 seconds with pattern interrupt")
    
    if analysis.get("mid_engagement", 100) < 70:
        suggestions.append("MIDDLE: Add retention hooks and open loops")
    
    if analysis.get("completion_rate", 100) < 50:
        suggestions.append("END: Add stronger payoff and session hook")
    
    for zone in analysis.get("problem_zones", []):
        suggestions.append(f"ZONE {zone['start']}-{zone['end']}s: {zone['severity'].upper()} drop - inject engagement")
    
    return suggestions


# =============================================================================
# STANDALONE TEST
# =============================================================================

if __name__ == "__main__":
    # Simulated retention curve (starts at 100%, drops over time)
    test_curve = [100, 98, 96, 94, 92, 85, 82, 80, 78, 76, 
                  74, 65, 63, 62, 61, 60, 59, 58, 57, 56,
                  55, 54, 53, 52, 51, 50, 49, 48, 47, 46]
    
    print("=" * 60)
    print("RETENTION ANALYZER TEST")
    print("=" * 60)
    
    # Detect drops
    drops = detect_drop_off(test_curve)
    print(f"\n📉 Detected {len(drops)} drop-off points:")
    for drop in drops:
        print(f"   Second {drop.second}: -{drop.drop_percentage:.1f}% ({drop.severity})")
    
    # Full analysis
    analysis = analyze_retention_pattern(test_curve)
    print(f"\n📊 Analysis:")
    print(f"   Hook Strength: {analysis['hook_strength']:.1f}%")
    print(f"   Mid Engagement: {analysis['mid_engagement']:.1f}%")
    print(f"   Completion Rate: {analysis['completion_rate']:.1f}%")
    
    # Suggestions
    suggestions = suggest_improvements(analysis)
    print(f"\n💡 Suggestions:")
    for s in suggestions:
        print(f"   • {s}")
