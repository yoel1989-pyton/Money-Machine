#!/usr/bin/env python3
"""
============================================================
MONEY MACHINE - ALGORITHM-ADAPTIVE VISUAL EVOLUTION (AAVE)
============================================================
A closed feedback loop where YouTube's actual response 
(not opinion) decides:
- Pacing
- Visuals  
- Structure
- Topic weighting

Losing patterns are killed automatically.
Winning patterns replicate and mutate.

Think: Genetic algorithm applied to Shorts.
============================================================
"""

import os
import json
import random
import hashlib
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict, field
from enum import Enum


# ============================================================
# ENUMS & CONSTANTS
# ============================================================

class HookType(Enum):
    THREAT = "threat"
    CONTRARIAN_FEAR = "contrarian_fear"
    MYTH_DESTRUCTION = "myth_destruction"
    CONSPIRACY_ADJACENT = "conspiracy_adjacent"
    AUTHORITY_GAP = "authority_gap"
    SELF_ATTACK = "self_attack"
    IDENTITY_TRIGGER = "identity_trigger"
    VICTIM_AWAKENING = "victim_awakening"
    METAPHOR_SHOCK = "metaphor_shock"
    INTERNAL_CONFLICT = "internal_conflict"
    HARSH_TRUTH = "harsh_truth"
    CULTURAL_REVERSAL = "cultural_reversal"
    SYSTEM_EXPOSURE = "system_exposure"
    POWER_GAP = "power_gap"
    MORAL_SHOCK = "moral_shock"
    FUTURE_THREAT = "future_threat"
    URGENCY = "urgency"
    LOSS_FRAMING = "loss_framing"
    HIDDEN_CHANGE = "hidden_change"
    ENDGAME_CURIOSITY = "endgame_curiosity"


class CutStyle(Enum):
    HARD = "hard"
    SMOOTH = "smooth"
    JUMP = "jump"
    FADE = "fade"


class MotionType(Enum):
    ZOOMPAN_SINE = "zoompan_sine"
    ZOOMPAN_LINEAR = "zoompan_linear"
    SLOW_ZOOM_IN = "slow_zoom_in"
    SLOW_ZOOM_OUT = "slow_zoom_out"
    PAN_LEFT = "pan_left"
    PAN_RIGHT = "pan_right"
    SHAKE = "shake"
    STATIC = "static"


class CaptionIntensity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    AGGRESSIVE = "aggressive"


class ColorGrade(Enum):
    NEUTRAL = "neutral"
    HIGH_CONTRAST = "high_contrast"
    WARM = "warm"
    COLD = "cold"
    CINEMATIC = "cinematic"
    VINTAGE = "vintage"


# ============================================================
# VISUAL DNA DATACLASS
# ============================================================

@dataclass
class VisualDNA:
    """
    The genetic blueprint of a video's visual style.
    Each parameter can mutate based on performance.
    """
    # Scene composition
    scene_length: float = 1.4  # seconds per scene
    cut_style: str = "hard"
    motion_type: str = "zoompan_sine"
    broll_density: float = 0.42  # 0-1, how much b-roll vs talking head
    
    # Caption styling
    caption_intensity: str = "medium"
    caption_position: str = "center"  # top, center, bottom
    caption_font_weight: str = "bold"
    
    # Hook & structure
    hook_type: str = "threat"
    hook_duration: float = 3.0  # seconds for hook
    open_loops: int = 2  # number of open loops in script
    
    # Color & post
    color_grade: str = "high_contrast"
    saturation: float = 1.12
    contrast: float = 1.07
    brightness: float = 0.02
    sharpness: float = 0.9
    
    # Pacing
    words_per_second: float = 2.8
    pause_after_hook: float = 0.5  # seconds
    
    # Metadata
    generation: int = 1
    parent_id: Optional[str] = None
    mutations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VisualDNA":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
    
    def get_id(self) -> str:
        """Generate unique ID based on DNA values."""
        dna_str = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.md5(dna_str.encode()).hexdigest()[:12]
    
    def mutate(self, mutation_rate: float = 0.3) -> "VisualDNA":
        """
        Create a mutated offspring.
        mutation_rate: probability of each gene mutating
        """
        child_data = self.to_dict()
        child_data["parent_id"] = self.get_id()
        child_data["generation"] = self.generation + 1
        child_data["mutations"] = []
        
        # Possible mutations per gene
        mutations: Dict[str, Any] = {
            "scene_length": lambda x: max(0.8, min(3.0, float(x) + random.uniform(-0.3, 0.3))),
            "cut_style": lambda _: random.choice(["hard", "smooth", "jump"]),
            "motion_type": lambda _: random.choice(["zoompan_sine", "zoompan_linear", "slow_zoom_in"]),
            "broll_density": lambda x: max(0.2, min(0.8, float(x) + random.uniform(-0.1, 0.1))),
            "caption_intensity": lambda _: random.choice(["low", "medium", "high", "aggressive"]),
            "hook_duration": lambda x: max(2.0, min(5.0, float(x) + random.uniform(-0.5, 0.5))),
            "open_loops": lambda x: max(0, min(4, int(x) + random.randint(-1, 1))),
            "saturation": lambda x: max(1.0, min(1.3, float(x) + random.uniform(-0.05, 0.05))),
            "contrast": lambda x: max(1.0, min(1.2, float(x) + random.uniform(-0.03, 0.03))),
            "sharpness": lambda x: max(0.5, min(1.5, float(x) + random.uniform(-0.1, 0.1))),
            "words_per_second": lambda x: max(2.2, min(3.5, float(x) + random.uniform(-0.2, 0.2))),
        }
        
        for gene, mutator in mutations.items():
            if random.random() < mutation_rate:
                old_val = child_data[gene]
                child_data[gene] = mutator(old_val)
                if child_data[gene] != old_val:
                    child_data["mutations"].append(gene)
        
        return VisualDNA.from_dict(child_data)
    
    def crossover(self, other: "VisualDNA") -> "VisualDNA":
        """
        Combine DNA from two parents (sexual reproduction).
        """
        child_data: Dict[str, Any] = {}
        
        for field_name in self.__dataclass_fields__:
            if field_name in ["generation", "parent_id", "mutations"]:
                continue
            
            # 50% chance from each parent
            if random.random() < 0.5:
                child_data[field_name] = getattr(self, field_name)
            else:
                child_data[field_name] = getattr(other, field_name)
        
        child_data["generation"] = max(self.generation, other.generation) + 1
        child_data["parent_id"] = f"{self.get_id()}x{other.get_id()}"
        child_data["mutations"] = ["crossover"]
        
        return VisualDNA.from_dict(child_data)


# ============================================================
# METRICS TRACKING
# ============================================================

@dataclass
class VideoMetrics:
    """
    All the metrics that actually matter (not vanity).
    """
    video_id: str
    topic: str
    dna_id: str
    
    # Core metrics
    retention_0_3s: float = 0.0  # Scroll-stop signal
    retention_3_10s: float = 0.0  # Pattern interrupt quality
    avg_view_duration: float = 0.0  # Core ranking driver
    replays: int = 0  # Strong interest / confusion loop
    rpm: float = 0.0  # Revenue per mille (when available)
    velocity_views_per_min: float = 0.0  # Short-term algorithm boost
    
    # Secondary (for context only)
    views_1hr: int = 0
    views_24hr: int = 0
    views_total: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    
    # Timestamps
    uploaded_at: str = ""
    metrics_updated_at: str = ""
    
    def fitness_score(self) -> float:
        """
        Calculate fitness score for genetic selection.
        Formula: Retention × RPM × Velocity
        """
        # Normalize each component
        retention_score = (self.retention_0_3s * 0.4 + 
                         self.retention_3_10s * 0.3 + 
                         (self.avg_view_duration / 60) * 0.3)
        
        rpm_score = min(self.rpm / 10, 1.0) if self.rpm > 0 else 0.5
        velocity_score = min(self.velocity_views_per_min / 100, 1.0)
        
        # Replay bonus
        replay_bonus = 1.0 + (min(self.replays, 1000) / 5000)
        
        return retention_score * rpm_score * velocity_score * replay_bonus
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ============================================================
# ELITE TOPIC DEFINITIONS
# ============================================================

ELITE_TOPICS = [
    # CATEGORY: MONEY / POWER / SYSTEMS (HIGH RPM)
    {
        "topic": "The Quiet Way Banks Legally Take Your Money",
        "hook": HookType.THREAT,
        "category": "money_power",
        "rpm_expected": "high"
    },
    {
        "topic": "Why Cash Is Actually Becoming a Liability",
        "hook": HookType.CONTRARIAN_FEAR,
        "category": "money_power",
        "rpm_expected": "high"
    },
    {
        "topic": "The Fed Doesn't Print Money the Way You Think",
        "hook": HookType.MYTH_DESTRUCTION,
        "category": "money_power",
        "rpm_expected": "high"
    },
    {
        "topic": "Why the Middle Class Is Disappearing by Design",
        "hook": HookType.CONSPIRACY_ADJACENT,
        "category": "money_power",
        "rpm_expected": "very_high"
    },
    {
        "topic": "The One Rule Rich People Never Break",
        "hook": HookType.AUTHORITY_GAP,
        "category": "money_power",
        "rpm_expected": "high"
    },
    
    # CATEGORY: PSYCHOLOGY / CONTROL (VERY HIGH RETENTION)
    {
        "topic": "Why Your Brain Loves Debt",
        "hook": HookType.SELF_ATTACK,
        "category": "psychology",
        "rpm_expected": "medium"
    },
    {
        "topic": "The System Rewards Obedience, Not Intelligence",
        "hook": HookType.IDENTITY_TRIGGER,
        "category": "psychology",
        "rpm_expected": "high"
    },
    {
        "topic": "Why Most People Are Financially Trained to Lose",
        "hook": HookType.VICTIM_AWAKENING,
        "category": "psychology",
        "rpm_expected": "very_high"
    },
    {
        "topic": "Comfort Is the Most Expensive Drug",
        "hook": HookType.METAPHOR_SHOCK,
        "category": "psychology",
        "rpm_expected": "medium"
    },
    {
        "topic": "Why Thinking Too Small Feels Safe",
        "hook": HookType.INTERNAL_CONFLICT,
        "category": "psychology",
        "rpm_expected": "medium"
    },
    
    # CATEGORY: HIDDEN RULES / GAME THEORY (RPM GOLD)
    {
        "topic": "Money Moves Faster Than Hard Work",
        "hook": HookType.HARSH_TRUTH,
        "category": "game_theory",
        "rpm_expected": "very_high"
    },
    {
        "topic": "Why Being Busy Is a Trap",
        "hook": HookType.CULTURAL_REVERSAL,
        "category": "game_theory",
        "rpm_expected": "high"
    },
    {
        "topic": "The Game Isn't Fair — It's Optimized",
        "hook": HookType.SYSTEM_EXPOSURE,
        "category": "game_theory",
        "rpm_expected": "very_high"
    },
    {
        "topic": "Why Rules Apply Differently at the Top",
        "hook": HookType.POWER_GAP,
        "category": "game_theory",
        "rpm_expected": "very_high"
    },
    {
        "topic": "How Risk Is Outsourced to the Poor",
        "hook": HookType.MORAL_SHOCK,
        "category": "game_theory",
        "rpm_expected": "high"
    },
    
    # CATEGORY: FUTURE / SHIFTS (LONG-TERM AUTHORITY)
    {
        "topic": "Why AI Will Make Average Income Obsolete",
        "hook": HookType.FUTURE_THREAT,
        "category": "future",
        "rpm_expected": "high"
    },
    {
        "topic": "Skills Are Replacing Jobs Faster Than You Think",
        "hook": HookType.URGENCY,
        "category": "future",
        "rpm_expected": "medium"
    },
    {
        "topic": "Why Owning Nothing Is the New Default",
        "hook": HookType.LOSS_FRAMING,
        "category": "future",
        "rpm_expected": "very_high"
    },
    {
        "topic": "The Economy Is Quietly Being Rewritten",
        "hook": HookType.HIDDEN_CHANGE,
        "category": "future",
        "rpm_expected": "high"
    },
    {
        "topic": "This Is What Money Looks Like After Trust Collapses",
        "hook": HookType.ENDGAME_CURIOSITY,
        "category": "future",
        "rpm_expected": "very_high"
    },
]


# ============================================================
# AAVE ENGINE
# ============================================================

class AAVEEngine:
    """
    Algorithm-Adaptive Visual Evolution Engine.
    
    The Core Loop:
    UPLOAD → Early Metrics (0–60 min) → Score → Promote/Mutate/Kill → Next Video
    
    This is not A/B testing. This is survival of the fittest content.
    """
    
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    DNA_FILE = DATA_DIR / "visual_dna_pool.json"
    METRICS_FILE = DATA_DIR / "video_metrics.json"
    EVOLUTION_LOG = DATA_DIR / "evolution_log.json"
    
    # Evolution thresholds
    PROMOTE_THRESHOLD = 0.7  # fitness score to promote
    KILL_THRESHOLD = 0.3  # fitness score to kill
    MUTATION_RATE = 0.25
    ELITE_PRESERVE = 3  # Always keep top N DNA strains
    
    # Golden Gate Winner Thresholds (for longform expansion)
    WINNER_AVD_THRESHOLD = 75.0  # Avg View Duration % (0-100)
    WINNER_RPM_THRESHOLD = 0.05  # Revenue per mille
    WINNER_REPLAY_THRESHOLD = 15.0  # Replay rate %
    
    def __init__(self):
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.dna_pool = self._load_dna_pool()
        self.metrics = self._load_metrics()
        self.evolution_log = self._load_evolution_log()
    
    def _load_dna_pool(self) -> Dict[str, VisualDNA]:
        """Load DNA pool from disk."""
        if self.DNA_FILE.exists():
            with open(self.DNA_FILE, "r") as f:
                data = json.load(f)
                return {k: VisualDNA.from_dict(v) for k, v in data.get("dna_strains", {}).items()}
        return self._initialize_dna_pool()
    
    def _initialize_dna_pool(self) -> Dict[str, VisualDNA]:
        """Initialize with diverse starting DNA."""
        pool: Dict[str, VisualDNA] = {}
        
        # Create diverse starting strains
        base_configs = [
            {"scene_length": 1.2, "motion_type": "zoompan_sine", "hook_type": "threat"},
            {"scene_length": 1.5, "motion_type": "zoompan_linear", "hook_type": "harsh_truth"},
            {"scene_length": 1.0, "motion_type": "slow_zoom_in", "hook_type": "myth_destruction"},
            {"scene_length": 1.8, "motion_type": "zoompan_sine", "hook_type": "system_exposure"},
            {"scene_length": 1.4, "motion_type": "zoompan_sine", "hook_type": "threat", 
             "caption_intensity": "aggressive"},
        ]
        
        for config in base_configs:
            dna = VisualDNA(**config)
            pool[dna.get_id()] = dna
        
        return pool
    
    def _save_dna_pool(self):
        """Save DNA pool to disk."""
        data = {
            "dna_strains": {k: v.to_dict() for k, v in self.dna_pool.items()},
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        with open(self.DNA_FILE, "w") as f:
            json.dump(data, f, indent=2)
    
    def _load_metrics(self) -> Dict[str, VideoMetrics]:
        """Load video metrics from disk."""
        if self.METRICS_FILE.exists():
            with open(self.METRICS_FILE, "r") as f:
                data = json.load(f)
                metrics: Dict[str, VideoMetrics] = {}
                for vid, m in data.get("videos", {}).items():
                    metrics[vid] = VideoMetrics(**{k: v for k, v in m.items() 
                                                   if k in VideoMetrics.__dataclass_fields__})
                return metrics
        return {}
    
    def _save_metrics(self):
        """Save metrics to disk."""
        data = {
            "videos": {k: v.to_dict() for k, v in self.metrics.items()},
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        with open(self.METRICS_FILE, "w") as f:
            json.dump(data, f, indent=2)
    
    def _load_evolution_log(self) -> List[Dict[str, Any]]:
        """Load evolution history."""
        if self.EVOLUTION_LOG.exists():
            with open(self.EVOLUTION_LOG, "r") as f:
                return json.load(f).get("log", [])
        return []
    
    def _save_evolution_log(self):
        """Save evolution history."""
        data = {
            "log": self.evolution_log[-500:],  # Keep last 500 entries
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        with open(self.EVOLUTION_LOG, "w") as f:
            json.dump(data, f, indent=2)
    
    # ============================================================
    # CORE EVOLUTION METHODS
    # ============================================================
    
    def select_dna_for_video(self) -> VisualDNA:
        """
        Select DNA for the next video using tournament selection.
        Prefers high-fitness DNA but maintains exploration.
        """
        if not self.dna_pool:
            self.dna_pool = self._initialize_dna_pool()
            self._save_dna_pool()
        
        # Get fitness scores for all DNA
        dna_fitness: List[Tuple[VisualDNA, float]] = []
        for dna_id, dna in self.dna_pool.items():
            # Calculate average fitness from videos using this DNA
            fitness = self._calculate_dna_fitness(dna_id)
            dna_fitness.append((dna, fitness))
        
        # Tournament selection (pick best of random 3)
        tournament_size = min(3, len(dna_fitness))
        candidates = random.sample(dna_fitness, tournament_size)
        winner = max(candidates, key=lambda x: x[1])[0]
        
        # 20% chance to mutate the winner
        if random.random() < 0.2:
            mutated = winner.mutate(self.MUTATION_RATE)
            self.dna_pool[mutated.get_id()] = mutated
            self._save_dna_pool()
            
            self._log_evolution("MUTATION", {
                "parent_id": winner.get_id(),
                "child_id": mutated.get_id(),
                "mutations": mutated.mutations
            })
            
            return mutated
        
        return winner
    
    def _calculate_dna_fitness(self, dna_id: str) -> float:
        """Calculate average fitness for a DNA strain."""
        relevant_metrics = [m for m in self.metrics.values() if m.dna_id == dna_id]
        
        if not relevant_metrics:
            return 0.5  # Neutral fitness for unexplored DNA
        
        scores = [m.fitness_score() for m in relevant_metrics]
        return sum(scores) / len(scores)
    
    def record_video_upload(self, video_id: str, topic: str, dna: VisualDNA):
        """Record that a video was uploaded with specific DNA."""
        self.metrics[video_id] = VideoMetrics(
            video_id=video_id,
            topic=topic,
            dna_id=dna.get_id(),
            uploaded_at=datetime.now(timezone.utc).isoformat()
        )
        self._save_metrics()
        
        self._log_evolution("UPLOAD", {
            "video_id": video_id,
            "topic": topic,
            "dna_id": dna.get_id()
        })
    
    def update_metrics(self, video_id: str, 
                       retention_0_3s: float = None,
                       retention_3_10s: float = None,
                       avg_view_duration: float = None,
                       replays: int = None,
                       rpm: float = None,
                       velocity: float = None,
                       views_1hr: int = None,
                       views_24hr: int = None,
                       views_total: int = None,
                       likes: int = None,
                       comments: int = None,
                       shares: int = None):
        """
        Update metrics for a video.
        Call after 1 hour, 24 hours, and periodically.
        """
        if video_id not in self.metrics:
            return
        
        m = self.metrics[video_id]
        
        if retention_0_3s is not None:
            m.retention_0_3s = retention_0_3s
        if retention_3_10s is not None:
            m.retention_3_10s = retention_3_10s
        if avg_view_duration is not None:
            m.avg_view_duration = avg_view_duration
        if replays is not None:
            m.replays = replays
        if rpm is not None:
            m.rpm = rpm
        if velocity is not None:
            m.velocity_views_per_min = velocity
        if views_1hr is not None:
            m.views_1hr = views_1hr
        if views_24hr is not None:
            m.views_24hr = views_24hr
        if views_total is not None:
            m.views_total = views_total
        if likes is not None:
            m.likes = likes
        if comments is not None:
            m.comments = comments
        if shares is not None:
            m.shares = shares
        
        m.metrics_updated_at = datetime.now(timezone.utc).isoformat()
        self._save_metrics()
        
        # Trigger evolution check
        self._check_evolution(video_id)
    
    def _check_evolution(self, video_id: str):
        """
        Check if this video's performance should trigger evolution.
        """
        m = self.metrics[video_id]
        fitness = m.fitness_score()
        dna_id = m.dna_id
        
        if dna_id not in self.dna_pool:
            return
        
        dna = self.dna_pool[dna_id]
        
        # Promote: Clone and mutate winning DNA
        if fitness >= self.PROMOTE_THRESHOLD:
            offspring = dna.mutate(self.MUTATION_RATE)
            self.dna_pool[offspring.get_id()] = offspring
            
            self._log_evolution("PROMOTE", {
                "video_id": video_id,
                "fitness": round(fitness, 3),
                "parent_dna": dna_id,
                "offspring_dna": offspring.get_id()
            })
            print(f"[AAVE] 🧬 PROMOTED DNA {dna_id[:8]} (fitness={fitness:.2f}) → offspring {offspring.get_id()[:8]}")
        
        # Kill: Remove underperforming DNA (but keep elite)
        elif fitness <= self.KILL_THRESHOLD:
            elite_dnas = self._get_elite_dnas()
            
            if dna_id not in elite_dnas and len(self.dna_pool) > self.ELITE_PRESERVE:
                del self.dna_pool[dna_id]
                
                self._log_evolution("KILL", {
                    "video_id": video_id,
                    "fitness": round(fitness, 3),
                    "killed_dna": dna_id
                })
                print(f"[AAVE] ☠️ KILLED DNA {dna_id[:8]} (fitness={fitness:.2f})")
        
        self._save_dna_pool()
    
    def _get_elite_dnas(self) -> List[str]:
        """Get top N DNA strains by fitness."""
        dna_fitness = [(dna_id, self._calculate_dna_fitness(dna_id)) 
                       for dna_id in self.dna_pool]
        dna_fitness.sort(key=lambda x: x[1], reverse=True)
        return [x[0] for x in dna_fitness[:self.ELITE_PRESERVE]]
    
    def evolve_population(self):
        """
        Run a full evolution cycle.
        Call periodically (e.g., after every 10-20 videos).
        """
        # 1. Calculate fitness for all DNA
        dna_fitness = [(dna_id, self._calculate_dna_fitness(dna_id)) 
                       for dna_id in self.dna_pool]
        dna_fitness.sort(key=lambda x: x[1], reverse=True)
        
        # 2. Keep elite
        elite = dna_fitness[:self.ELITE_PRESERVE]
        
        # 3. Kill bottom performers (if pool is large enough)
        if len(self.dna_pool) > self.ELITE_PRESERVE * 2:
            bottom_count = len(dna_fitness) // 4  # Kill bottom 25%
            to_kill = [x[0] for x in dna_fitness[-bottom_count:] 
                       if x[0] not in [e[0] for e in elite]]
            
            for dna_id in to_kill:
                del self.dna_pool[dna_id]
                self._log_evolution("CULL", {"dna_id": dna_id})
        
        # 4. Crossover top performers
        if len(elite) >= 2:
            parent1 = self.dna_pool[elite[0][0]]
            parent2 = self.dna_pool[elite[1][0]]
            child = parent1.crossover(parent2)
            self.dna_pool[child.get_id()] = child
            
            self._log_evolution("CROSSOVER", {
                "parent1": elite[0][0],
                "parent2": elite[1][0],
                "child": child.get_id()
            })
        
        # 5. Inject fresh DNA occasionally
        if random.random() < 0.1:  # 10% chance
            fresh = VisualDNA(
                scene_length=random.uniform(0.8, 2.0),
                motion_type=random.choice(["zoompan_sine", "zoompan_linear", "slow_zoom_in"]),
                hook_type=random.choice(list(HookType)).value,
                generation=1
            )
            self.dna_pool[fresh.get_id()] = fresh
            self._log_evolution("INJECT", {"dna_id": fresh.get_id()})
        
        self._save_dna_pool()
        print(f"[AAVE] 🧬 Evolution complete. Pool size: {len(self.dna_pool)}")
    
    def _log_evolution(self, event_type: str, data: Dict[str, Any]):
        """Log evolution event."""
        self.evolution_log.append({
            "event": event_type,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        self._save_evolution_log()
    
    # ============================================================
    # TOPIC SELECTION (INTEGRATED WITH VISUAL DNA)
    # ============================================================
    
    def select_elite_topic(self) -> Tuple[Dict[str, Any], VisualDNA]:
        """
        Select an elite topic with matching DNA.
        Returns (topic_data, dna).
        """
        # Get topic performance data
        topic_scores = self._calculate_topic_scores()
        
        # Weighted random selection (favor high performers)
        weights: List[float] = []
        for topic_data in ELITE_TOPICS:
            topic = topic_data["topic"]
            score = topic_scores.get(topic, 0.5)  # Default neutral
            rpm_weight = {"low": 0.5, "medium": 1.0, "high": 1.5, "very_high": 2.0}.get(
                topic_data.get("rpm_expected", "medium"), 1.0
            )
            weights.append(score * rpm_weight)
        
        # Normalize weights
        total = sum(weights)
        weights = [w/total for w in weights]
        
        # Select topic
        selected = random.choices(ELITE_TOPICS, weights=weights, k=1)[0]
        
        # Match DNA to hook type
        dna = self._select_dna_for_hook(selected["hook"])
        
        return selected, dna
    
    def _calculate_topic_scores(self) -> Dict[str, float]:
        """Calculate performance scores for topics."""
        scores: Dict[str, List[float]] = {}
        
        for vid, m in self.metrics.items():
            topic = m.topic
            if topic not in scores:
                scores[topic] = []
            scores[topic].append(m.fitness_score())
        
        # Average scores
        return {t: sum(s)/len(s) for t, s in scores.items() if s}
    
    def _select_dna_for_hook(self, hook_type: HookType) -> VisualDNA:
        """Select DNA that works well with a specific hook type."""
        matching = [dna for dna in self.dna_pool.values() 
                    if dna.hook_type == hook_type.value]
        
        if matching:
            # Return best performing match
            fitness_scores = [(dna, self._calculate_dna_fitness(dna.get_id())) 
                             for dna in matching]
            return max(fitness_scores, key=lambda x: x[1])[0]
        
        # No match - create new DNA for this hook
        new_dna = VisualDNA(hook_type=hook_type.value)
        self.dna_pool[new_dna.get_id()] = new_dna
        self._save_dna_pool()
        return new_dna
    
    # ============================================================
    # ANALYTICS & REPORTING
    # ============================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get evolution statistics."""
        if not self.dna_pool:
            return {"status": "uninitialized"}
        
        dna_fitness = [(dna_id, self._calculate_dna_fitness(dna_id)) 
                       for dna_id in self.dna_pool]
        dna_fitness.sort(key=lambda x: x[1], reverse=True)
        
        # Top performing topics
        topic_scores = self._calculate_topic_scores()
        top_topics = sorted(topic_scores.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Recent evolution events
        recent_events = self.evolution_log[-10:]
        
        return {
            "dna_pool_size": len(self.dna_pool),
            "total_videos_tracked": len(self.metrics),
            "top_dna_strains": [
                {"id": dna_id[:8], "fitness": round(fitness, 3)}
                for dna_id, fitness in dna_fitness[:5]
            ],
            "top_topics": [
                {"topic": t[:40], "score": round(s, 3)}
                for t, s in top_topics
            ],
            "recent_evolution_events": len(recent_events),
            "generations_evolved": max((dna.generation for dna in self.dna_pool.values()), default=1)
        }
    
    def get_ffmpeg_params(self, dna: VisualDNA) -> Dict[str, Any]:
        """
        Convert Visual DNA to FFmpeg parameters.
        Returns dict of filter values.
        """
        return {
            "contrast": dna.contrast,
            "saturation": dna.saturation,
            "brightness": dna.brightness,
            "sharpness": dna.sharpness,
            "zoom_rate": 0.0009,  # Base rate
            "zoom_max": 1.08,
        }
    
    def get_script_params(self, dna: VisualDNA) -> Dict[str, Any]:
        """
        Convert Visual DNA to script generation parameters.
        """
        return {
            "hook_type": dna.hook_type,
            "hook_duration_seconds": dna.hook_duration,
            "words_per_second": dna.words_per_second,
            "open_loops": dna.open_loops,
            "pause_after_hook": dna.pause_after_hook
        }


# ============================================================
# CLI
# ============================================================

def main():
    import sys
    
    engine = AAVEEngine()
    
    if len(sys.argv) < 2:
        print("Usage: python aave_engine.py <command>")
        print("Commands: stats, select, evolve, topics, init")
        return
    
    cmd = sys.argv[1].lower()
    
    if cmd == "stats":
        stats = engine.get_stats()
        print("\n=== AAVE ENGINE STATS ===")
        for k, v in stats.items():
            print(f"{k}: {v}")
    
    elif cmd == "select":
        topic, dna = engine.select_elite_topic()
        print(f"\n=== SELECTED FOR NEXT VIDEO ===")
        print(f"Topic: {topic['topic']}")
        print(f"Hook: {topic['hook'].value}")
        print(f"DNA ID: {dna.get_id()}")
        print(f"DNA Generation: {dna.generation}")
    
    elif cmd == "evolve":
        print("Running evolution cycle...")
        engine.evolve_population()
    
    elif cmd == "topics":
        print("\n=== ELITE TOPICS ===")
        for i, t in enumerate(ELITE_TOPICS, 1):
            print(f"{i}. [{t['hook'].value}] {t['topic']}")
    
    elif cmd == "init":
        engine.dna_pool = engine._initialize_dna_pool()
        engine._save_dna_pool()
        print("DNA pool initialized with diverse strains")


if __name__ == "__main__":
    main()
