"""
REPLICATION ENGINE v2.0
Clones winning DNA across multiple channels.

The Replication Protocol:
1. Detect winner DNA (85%+ AVD, >$0.05 RPM)
2. Mutate for new niche (same structure, different topic)
3. Clone to new channel with inherited visual DNA
4. Monitor performance, feed back into DNA pool

Multi-Channel Architecture:
- money_machine_ai (finance) [ACTIVE]
- money_machine_tech (technology)
- money_machine_career (career/jobs)
- money_machine_economy (macro economics)

Each channel inherits:
- Visual DNA (pacing, cut frequency, color mood)
- Hook structure that worked
- Emotional triggers that converted
"""

import os
import sys
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent


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
    hook_type: str
    emotional_trigger: str
    visual_dna: VisualDNA
    script_hash: str
    is_winner: bool = False
    should_expand: bool = False
    times_mutated: int = 0
    rpm: float = 0.0


@dataclass
class ChannelConfig:
    """Configuration for a single channel."""
    name: str
    channel_id: str
    niche: str
    topic_seeds: List[str]
    visual_dna: Optional[VisualDNA] = None
    parent_channel: Optional[str] = None
    videos_per_day: int = 4
    active: bool = True
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


@dataclass 
class NicheMutation:
    """Defines how to mutate DNA for a specific niche."""
    niche: str
    topic_transforms: Dict[str, str]
    visual_overrides: Dict[str, str]
    emotional_preferences: List[str]


# Legacy compatibility
@dataclass
class ChannelInfo:
    channel_id: str
    channel_name: str
    niche: str
    is_primary: bool = False
    uploads_today: int = 0
    total_uploads: int = 0


class ReplicationEngine:
    """
    Manages multi-channel replication and DNA cloning.
    """
    
    NICHE_MUTATIONS = {
        "tech": NicheMutation(
            niche="tech",
            topic_transforms={
                "rich": "tech giants",
                "money": "data",
                "bank": "big tech",
                "wealth": "power",
                "finance": "technology",
                "economy": "tech industry",
            },
            visual_overrides={
                "intent": "systems_control",
                "color_mood": "tech_blue"
            },
            emotional_preferences=["revelation", "urgency"]
        ),
        "career": NicheMutation(
            niche="career",
            topic_transforms={
                "rich": "corporations",
                "money": "career",
                "bank": "HR",
                "wealth": "success",
                "finance": "workplace",
                "economy": "job market",
            },
            visual_overrides={
                "intent": "psychology",
                "color_mood": "neutral"
            },
            emotional_preferences=["injustice", "revelation"]
        ),
        "economy": NicheMutation(
            niche="economy",
            topic_transforms={
                "rich": "elites",
                "money": "economy",
                "bank": "central banks",
                "wealth": "capital",
                "finance": "macroeconomics",
            },
            visual_overrides={
                "intent": "future_warning",
                "color_mood": "dark"
            },
            emotional_preferences=["urgency", "revelation"]
        ),
    }
    
    def __init__(self):
        self.config_dir = BASE_DIR / "data" / "channels"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.channels: Dict[str, ChannelConfig] = {}
        self._load_channels()
        
        # Legacy compatibility
        self._legacy_channels: Dict[str, ChannelInfo] = {}
        
        # Initialize primary channel if not exists
        if not self.channels:
            self._init_primary_channel()
    
    def _load_channels(self):
        """Load existing channel configurations."""
        config_file = self.config_dir / "channels.json"
        if config_file.exists():
            try:
                with open(config_file, "r") as f:
                    data = json.load(f)
                    for name, config in data.items():
                        visual_dna = None
                        if config.get("visual_dna"):
                            visual_dna = VisualDNA(**config.pop("visual_dna"))
                        self.channels[name] = ChannelConfig(**config, visual_dna=visual_dna)
            except Exception as e:
                print(f"[REPLICATION] Error loading channels: {e}")
    
    def _save_channels(self):
        """Save channel configurations."""
        config_file = self.config_dir / "channels.json"
        try:
            data = {}
            for name, channel in self.channels.items():
                channel_dict = asdict(channel)
                data[name] = channel_dict
            with open(config_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[REPLICATION] Error saving channels: {e}")
    
    def _init_primary_channel(self):
        """Initialize the primary Money Machine channel."""
        primary = ChannelConfig(
            name="money_machine_ai",
            channel_id=os.getenv("YOUTUBE_CHANNEL_ID", "UCZppwcvPrWlAG0vb78elPJA"),
            niche="finance",
            topic_seeds=[
                "Why the rich don't work for money",
                "The hidden tax nobody talks about",
                "What banks don't want you to know",
                "Why your savings are disappearing",
                "The wealth transfer happening right now",
            ],
            visual_dna=VisualDNA(
                intent="power_finance",
                pacing="aggressive",
                motion_density="high",
                color_mood="dark",
                scene_duration=2.0,
                cut_frequency=25.0
            ),
            parent_channel=None,
            videos_per_day=4,
            active=True
        )
        self.channels["money_machine_ai"] = primary
        self._save_channels()
        print("[REPLICATION] Initialized primary channel: money_machine_ai")
    
    # Legacy compatibility methods
    def register_channel(self, channel_id: str, channel_name: str, niche: str, is_primary: bool = False) -> None:
        self._legacy_channels[channel_id] = ChannelInfo(
            channel_id=channel_id, 
            channel_name=channel_name, 
            niche=niche, 
            is_primary=is_primary
        )
    
    def record_upload(self, channel_id: str) -> None:
        if channel_id in self._legacy_channels:
            self._legacy_channels[channel_id].uploads_today += 1
            self._legacy_channels[channel_id].total_uploads += 1
    
    def get_replication_topic(self, channel_id: str = None) -> Optional[str]:
        return None
    
    def get_status(self) -> Dict:
        return {
            "total_channels": len(self.channels),
            "channels": {name: {"niche": ch.niche, "active": ch.active} for name, ch in self.channels.items()}
        }
    
    def clone_channel(
        self,
        source_name: str,
        target_name: str,
        target_niche: str,
        channel_id: str = None
    ) -> ChannelConfig:
        """Clone a channel with niche mutation."""
        if source_name not in self.channels:
            raise ValueError(f"Source channel not found: {source_name}")
        
        source = self.channels[source_name]
        mutation = self.NICHE_MUTATIONS.get(target_niche)
        
        if not mutation:
            mutation = NicheMutation(
                niche=target_niche,
                topic_transforms={},
                visual_overrides={},
                emotional_preferences=["curiosity"]
            )
        
        # Mutate topic seeds
        mutated_seeds = []
        for seed in source.topic_seeds:
            mutated_seed = seed
            for original, replacement in mutation.topic_transforms.items():
                mutated_seed = mutated_seed.lower().replace(original, replacement)
            mutated_seeds.append(mutated_seed)
        
        # Clone visual DNA with mutations
        new_visual = VisualDNA(
            intent=mutation.visual_overrides.get("intent", source.visual_dna.intent) if source.visual_dna else "power_finance",
            pacing=source.visual_dna.pacing if source.visual_dna else "aggressive",
            motion_density=source.visual_dna.motion_density if source.visual_dna else "high",
            color_mood=mutation.visual_overrides.get("color_mood", source.visual_dna.color_mood if source.visual_dna else "dark"),
            scene_duration=source.visual_dna.scene_duration if source.visual_dna else 2.0,
            cut_frequency=source.visual_dna.cut_frequency if source.visual_dna else 25.0
        )
        
        new_channel = ChannelConfig(
            name=target_name,
            channel_id=channel_id or f"pending_{target_name}",
            niche=target_niche,
            topic_seeds=mutated_seeds,
            visual_dna=new_visual,
            parent_channel=source_name,
            videos_per_day=source.videos_per_day,
            active=False
        )
        
        self.channels[target_name] = new_channel
        self._save_channels()
        
        print(f"[REPLICATION] 🔄 Cloned: {source_name} → {target_name}")
        return new_channel
    
    def mutate_dna_for_niche(self, dna: ShortDNA, target_niche: str) -> ShortDNA:
        """Mutate DNA for a different niche."""
        mutation = self.NICHE_MUTATIONS.get(target_niche)
        if not mutation:
            return dna
        
        new_topic = dna.topic
        for original, replacement in mutation.topic_transforms.items():
            new_topic = new_topic.lower().replace(original, replacement)
        
        new_visual = VisualDNA(
            intent=mutation.visual_overrides.get("intent", dna.visual_dna.intent),
            pacing=dna.visual_dna.pacing,
            motion_density=dna.visual_dna.motion_density,
            color_mood=mutation.visual_overrides.get("color_mood", dna.visual_dna.color_mood),
            scene_duration=dna.visual_dna.scene_duration,
            cut_frequency=dna.visual_dna.cut_frequency
        )
        
        return ShortDNA(
            video_id=f"{dna.video_id}_{target_niche}",
            topic=new_topic,
            hook_type=dna.hook_type,
            emotional_trigger=mutation.emotional_preferences[0] if mutation.emotional_preferences else dna.emotional_trigger,
            visual_dna=new_visual,
            script_hash=f"{dna.script_hash}_{target_niche}",
            times_mutated=dna.times_mutated + 1
        )
    
    def get_active_channels(self) -> List[ChannelConfig]:
        return [ch for ch in self.channels.values() if ch.active]
    
    def activate_channel(self, name: str, channel_id: str):
        if name not in self.channels:
            raise ValueError(f"Channel not found: {name}")
        self.channels[name].channel_id = channel_id
        self.channels[name].active = True
        self._save_channels()
        print(f"[REPLICATION] ✅ Activated: {name}")
