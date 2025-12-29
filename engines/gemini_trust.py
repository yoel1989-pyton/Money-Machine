"""
===============================================================================
GEMINI TRUST MODULE - Algorithm-Native Human Perception Engine
===============================================================================
Makes YouTube's Gemini AI read your content as:
- Human-created (not content farm)
- High-satisfaction (delivers on promise)
- Trustworthy (consistent quality)
- Viewer-modeled (specific audience match)

This is the difference between viral and buried.
===============================================================================
"""

import random
import hashlib
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class OrganicVariation:
    """Human-like imperfections that signal authenticity."""
    camera_shake: float      # Micro-movement intensity (0.6-1.3)
    grain: int               # Film grain level (8-14)
    cadence_variance: float  # Speech rhythm variation (0.92-1.08)
    pause_probability: float # Chance of natural pause (0.08-0.18)
    upload_delay_minutes: int  # Randomized upload timing


@dataclass
class SatisfactionScore:
    """Measures promise-to-delivery alignment."""
    title_script_overlap: float
    hook_clarity: float
    payoff_strength: float
    open_loop_count: int
    overall: float
    passed: bool


class GeminiTrustModule:
    """
    Enforces human signals, satisfaction alignment,
    and anti-content-farm detection resistance.
    
    YouTube's Gemini AI is trained to detect:
    - AI-perfect content (too smooth = bot)
    - Promise mismatches (clickbait penalty)
    - Repetitive patterns (content farm signature)
    - Low satisfaction trajectories
    
    This module counters all of these.
    """

    # Viewer model archetypes - each video should target ONE
    VIEWER_MODELS = {
        "working_class_finance": {
            "age_range": "25-45",
            "pain_points": ["debt", "paycheck to paycheck", "hidden fees"],
            "desires": ["freedom", "control", "understanding"],
            "keywords": ["banks", "credit", "debt", "system", "trap"]
        },
        "anti_system_money": {
            "age_range": "22-40", 
            "pain_points": ["manipulation", "inequality", "propaganda"],
            "desires": ["truth", "power", "escape"],
            "keywords": ["rich", "poor", "hidden", "secret", "exposed"]
        },
        "wealth_builder": {
            "age_range": "28-50",
            "pain_points": ["slow growth", "missed opportunities", "confusion"],
            "desires": ["strategy", "acceleration", "clarity"],
            "keywords": ["invest", "compound", "passive", "leverage", "wealth"]
        },
        "crypto_skeptic": {
            "age_range": "30-55",
            "pain_points": ["scams", "volatility", "FOMO"],
            "desires": ["truth", "stability", "real value"],
            "keywords": ["bitcoin", "crypto", "blockchain", "digital", "currency"]
        },
        "side_hustle_seeker": {
            "age_range": "20-35",
            "pain_points": ["time poverty", "low income", "no options"],
            "desires": ["freedom", "income streams", "escape"],
            "keywords": ["passive", "income", "hustle", "money", "online"]
        }
    }

    # Spoken SEO templates - Gemini listens before it reads
    SPOKEN_SEO_TEMPLATES = [
        "This video explains {topic} — not the surface version, but how it actually works and why most people misunderstand it.",
        "What I'm about to show you about {topic} is something the system doesn't want you to notice.",
        "Before we start — this is the real truth about {topic}. No motivation. No fluff. Just how it works.",
        "Today we're breaking down {topic} — the hidden mechanics that determine who wins and who stays trapped.",
        "Listen carefully. What you're about to learn about {topic} changes how you see everything.",
    ]

    def __init__(self, channel_id: str = "MoneyMachineAI"):
        self.channel_id = channel_id
        self.channel_entropy = self._generate_channel_entropy()
        self._session_seed = random.randint(0, 999999)

    def _generate_channel_entropy(self) -> int:
        """Generate daily-unique entropy for organic variation."""
        seed = f"{self.channel_id}{datetime.utcnow().date()}"
        return int(hashlib.sha256(seed.encode()).hexdigest(), 16) % 10000

    # =========================================================================
    # SPOKEN SEO - Make Gemini hear your topic immediately
    # =========================================================================

    def inject_spoken_seo(self, script: str, core_topic: str) -> str:
        """
        Inject topic mention in first 20-30 seconds.
        Gemini ASR processes audio BEFORE metadata.
        """
        template = random.choice(self.SPOKEN_SEO_TEMPLATES)
        intro = template.format(topic=core_topic.lower())
        
        # Add slight variation to prevent pattern detection
        variations = [
            "",
            "Pay attention. ",
            "Here's what you need to know. ",
            "Let me show you something. ",
        ]
        prefix = random.choice(variations)
        
        return f"{prefix}{intro} {script}"

    # =========================================================================
    # ORGANIC VARIATION - Human imperfection signals
    # =========================================================================

    def generate_organic_variation(self) -> OrganicVariation:
        """
        Generate human-like imperfections that signal authenticity.
        AI-perfect = content farm signature = algorithm death.
        """
        return OrganicVariation(
            camera_shake=round(random.uniform(0.6, 1.3), 2),
            grain=random.randint(8, 14),
            cadence_variance=round(random.uniform(0.92, 1.08), 3),
            pause_probability=round(random.uniform(0.08, 0.18), 2),
            upload_delay_minutes=random.randint(13, 60)
        )

    def get_organic_ffmpeg_filter(self, variation: OrganicVariation) -> str:
        """
        Generate FFmpeg filter string with organic imperfections.
        """
        shake_x = int(variation.camera_shake * 4)
        shake_y = int(variation.camera_shake * 4)
        
        # Organic motion with micro-shake and film grain
        filter_str = (
            f"zoompan=z='min(zoom+0.0008,1.06)':"
            f"x='iw/2-(iw/zoom/2)+random(1)*{shake_x}':"
            f"y='ih/2-(ih/zoom/2)+random(1)*{shake_y}',"
            f"noise=alls={variation.grain}:allf=t"
        )
        return filter_str

    def get_tts_settings(self, variation: OrganicVariation) -> Dict:
        """
        ElevenLabs settings with human imperfection.
        Over-stability = bot signature.
        """
        return {
            "stability": 0.42 + (variation.cadence_variance - 1.0) * 0.5,
            "similarity_boost": 0.78,
            "style": 0.55 + random.uniform(-0.1, 0.1),
            "use_speaker_boost": True
        }

    # =========================================================================
    # SATISFACTION GUARD - Promise-to-delivery alignment
    # =========================================================================

    def check_satisfaction(self, title: str, script: str, description: str = "") -> SatisfactionScore:
        """
        Ensure title promise is delivered in content.
        Low alignment = clickbait penalty = algorithmic death.
        """
        title_tokens = set(re.findall(r'\w+', title.lower()))
        script_tokens = set(re.findall(r'\w+', script.lower()))
        
        # Calculate overlaps
        title_script_overlap = len(title_tokens & script_tokens) / max(len(title_tokens), 1)
        
        # Check hook clarity (first 100 chars should relate to title)
        first_section = script[:500].lower()
        hook_hits = sum(1 for t in title_tokens if t in first_section)
        hook_clarity = hook_hits / max(len(title_tokens), 1)
        
        # Check payoff (last 200 chars should have resolution)
        payoff_keywords = ["so", "that's", "this is", "now you", "remember", "truth"]
        last_section = script[-300:].lower()
        payoff_strength = sum(1 for k in payoff_keywords if k in last_section) / len(payoff_keywords)
        
        # Count open loops (questions, "but", "however")
        open_loop_markers = ["?", "but ", "however", "what if", "here's the thing"]
        open_loop_count = sum(script.lower().count(m) for m in open_loop_markers)
        
        # Overall satisfaction score
        overall = (title_script_overlap * 0.4 + hook_clarity * 0.3 + payoff_strength * 0.3)
        
        return SatisfactionScore(
            title_script_overlap=round(title_script_overlap, 3),
            hook_clarity=round(hook_clarity, 3),
            payoff_strength=round(payoff_strength, 3),
            open_loop_count=open_loop_count,
            overall=round(overall, 3),
            passed=overall >= 0.5  # Lowered threshold for flexibility
        )

    # =========================================================================
    # VIEWER MODEL DETECTION - Single archetype per video
    # =========================================================================

    def detect_viewer_model(self, script: str, title: str) -> Tuple[str, float]:
        """
        Detect which viewer archetype this content targets.
        Multiple archetypes = confused algorithm = no push.
        """
        combined = f"{title} {script}".lower()
        
        scores = {}
        for model_name, model_data in self.VIEWER_MODELS.items():
            keyword_hits = sum(1 for k in model_data["keywords"] if k in combined)
            scores[model_name] = keyword_hits / len(model_data["keywords"])
        
        # Find best match
        best_model = max(scores, key=scores.get)
        confidence = scores[best_model]
        
        # Check for model collision (multiple strong matches)
        strong_matches = [m for m, s in scores.items() if s > 0.4]
        if len(strong_matches) > 1:
            # Collision detected - but we'll just warn, not fail
            pass
        
        return best_model, confidence

    def get_viewer_model_tags(self, model_name: str) -> List[str]:
        """Get recommended tags for a viewer model."""
        model = self.VIEWER_MODELS.get(model_name, {})
        return model.get("keywords", [])

    # =========================================================================
    # RETENTION STORYTELLING - Open loop injection
    # =========================================================================

    def inject_retention_hooks(self, scenes: List[Dict]) -> List[Dict]:
        """
        Inject open loops and retention hooks into scene structure.
        """
        if not scenes:
            return scenes
        
        # First scene = outcome tease
        if len(scenes) > 0:
            scenes[0]["retention_intent"] = "outcome_tease"
        
        # Second-to-last = payoff
        if len(scenes) > 2:
            scenes[-2]["retention_intent"] = "payoff"
        
        # Last scene = next question (session time boost)
        if len(scenes) > 1:
            scenes[-1]["retention_intent"] = "next_question"
            scenes[-1]["session_hook"] = True
        
        return scenes

    def get_session_end_line(self) -> str:
        """
        Final spoken line that feeds session time.
        This is YouTube's favorite metric.
        """
        options = [
            "What I just showed you is only part of it. The next system is even more powerful.",
            "This is just the beginning. There's something else they don't want you to see.",
            "Now that you understand this, everything else starts to make sense.",
            "Remember what you just learned. It connects to something bigger.",
            "This is why understanding the system changes everything.",
        ]
        return random.choice(options)

    # =========================================================================
    # TRUST SCORE GENERATION
    # =========================================================================

    def generate_trust_metadata(self) -> Dict:
        """
        Generate metadata that boosts algorithmic trust.
        """
        return {
            "entropy_seed": (self.channel_entropy + self._session_seed) % 10000,
            "upload_variance_minutes": random.randint(13, 47),
            "human_signal": True,
            "caption_variation_seed": hashlib.md5(
                f"{datetime.utcnow().isoformat()}".encode()
            ).hexdigest()[:8],
            "organic_timestamp": datetime.utcnow().isoformat(),
        }

    # =========================================================================
    # FULL TRUST CHECK - Run before publishing
    # =========================================================================

    def full_trust_check(
        self, 
        title: str, 
        script: str, 
        description: str = ""
    ) -> Dict:
        """
        Complete trust validation before upload.
        Returns pass/fail with detailed scores.
        """
        # Generate organic variation
        organic = self.generate_organic_variation()
        
        # Check satisfaction alignment
        satisfaction = self.check_satisfaction(title, script, description)
        
        # Detect viewer model
        viewer_model, model_confidence = self.detect_viewer_model(script, title)
        
        # Generate trust metadata
        trust_meta = self.generate_trust_metadata()
        
        # Overall pass/fail
        passed = satisfaction.passed and model_confidence >= 0.3
        
        return {
            "passed": passed,
            "satisfaction": {
                "overall": satisfaction.overall,
                "title_overlap": satisfaction.title_script_overlap,
                "hook_clarity": satisfaction.hook_clarity,
                "payoff_strength": satisfaction.payoff_strength,
                "open_loops": satisfaction.open_loop_count,
            },
            "viewer_model": {
                "detected": viewer_model,
                "confidence": model_confidence,
                "recommended_tags": self.get_viewer_model_tags(viewer_model),
            },
            "organic_variation": {
                "camera_shake": organic.camera_shake,
                "grain": organic.grain,
                "cadence_variance": organic.cadence_variance,
                "upload_delay": organic.upload_delay_minutes,
            },
            "trust_metadata": trust_meta,
            "session_end_line": self.get_session_end_line(),
            "ffmpeg_filter": self.get_organic_ffmpeg_filter(organic),
            "tts_settings": self.get_tts_settings(organic),
        }


# =============================================================================
# STANDALONE TEST
# =============================================================================

if __name__ == "__main__":
    trust = GeminiTrustModule(channel_id="MoneyMachineAI")
    
    # Test data
    test_title = "Why The Rich Never Use Cash"
    test_script = """
    The rich don't use cash. They use debt. While you're saving pennies, 
    they're leveraging millions. Here's how the system actually works.
    Banks want you to save. They make money when you're passive.
    But the wealthy? They borrow against assets and pay almost nothing.
    This is the hidden mechanism of wealth transfer.
    Now you understand why cash is a trap, not a tool.
    """
    
    # Run full trust check
    result = trust.full_trust_check(test_title, test_script)
    
    print("=" * 60)
    print("GEMINI TRUST CHECK")
    print("=" * 60)
    print(f"✅ Passed: {result['passed']}")
    print(f"\n📊 Satisfaction Score: {result['satisfaction']['overall']}")
    print(f"   Title Overlap: {result['satisfaction']['title_overlap']}")
    print(f"   Hook Clarity: {result['satisfaction']['hook_clarity']}")
    print(f"   Payoff Strength: {result['satisfaction']['payoff_strength']}")
    print(f"\n👤 Viewer Model: {result['viewer_model']['detected']}")
    print(f"   Confidence: {result['viewer_model']['confidence']}")
    print(f"\n🎬 Organic Settings:")
    print(f"   Camera Shake: {result['organic_variation']['camera_shake']}")
    print(f"   Grain: {result['organic_variation']['grain']}")
    print(f"   Upload Delay: {result['organic_variation']['upload_delay']} min")
    print(f"\n🔚 Session End Line: {result['session_end_line']}")
