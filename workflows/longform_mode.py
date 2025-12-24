"""
LONG-FORM DOCUMENTARY MODE v2.0
Converts winning Shorts DNA into 10-20 minute documentaries.

Revenue Mathematics:
- Shorts RPM: $0.02 - $0.08
- Long-form RPM: $12 - $30+
- Watch time multiplier: 60 seconds → 17 minutes = 17x
- Combined: 170-850x revenue per view

This workflow:
1. Monitors AAVE engine for Golden Gate winners
2. Generates documentary outlines
3. Produces full scripts using GPT-4
4. Generates hardened async TTS narration
5. Assembles videos with 5-Act structure
6. Uploads to YouTube with SEO optimization

Run daily at 4 PM when ad rates peak.
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import argparse

# Add parent directory to path
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from engines.longform_builder import (
    LongformBuilder, 
    LongformAudioEngine, 
    DocumentaryDNA,
    TTSVoice
)
from engines.aave_engine import AAVEEngine, VisualDNA

# Try importing optional dependencies
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    import edge_tts
    HAS_EDGE_TTS = True
except ImportError:
    HAS_EDGE_TTS = False

try:
    from engines.dna_expander import DNAExpander, ShortDNA, DocumentaryOutline
    HAS_DNA_EXPANDER = True
except ImportError:
    HAS_DNA_EXPANDER = False

try:
    from engines.broll_engine import BRollEngine, resolve_visual_intent
    HAS_BROLL = True
except ImportError:
    HAS_BROLL = False


SCRIPTS_DIR = BASE_DIR / "data" / "scripts"
AUDIO_DIR = BASE_DIR / "data" / "audio" 
OUTPUT_DIR = BASE_DIR / "data" / "output"
DOCUMENTARIES_DIR = OUTPUT_DIR / "documentaries"


class LongformMode:
    """
    Autonomous documentary production workflow.
    
    Uses AAVE Engine's Golden Gate thresholds for winner detection:
    - AVD > 75%
    - RPM > $0.05
    - Replay Rate > 15%
    """
    
    def __init__(self):
        # Core engines
        self.aave_engine = AAVEEngine()
        self.longform_builder = LongformBuilder()
        self.audio_engine = LongformAudioEngine()
        
        # Optional DNA expander for backwards compatibility
        self.dna_expander = None
        if HAS_DNA_EXPANDER:
            try:
                self.dna_expander = DNAExpander()
            except:
                pass
        
        # Create directories
        SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
        AUDIO_DIR.mkdir(parents=True, exist_ok=True)
        DOCUMENTARIES_DIR.mkdir(parents=True, exist_ok=True)
        
        # OpenAI client
        self.openai_client = None
        if HAS_OPENAI and os.getenv("OPENAI_API_KEY"):
            self.openai_client = OpenAI()
        
        # Get winner stats
        winners = self.aave_engine.get_winners()
        
        print("[LONGFORM] Documentary Mode v2.0 initialized")
        print(f"[LONGFORM] AAVE DNA Pool: {len(self.aave_engine.dna_pool)} strains")
        print(f"[LONGFORM] Golden Gate Winners: {len(winners)} ready for expansion")
        print(f"[LONGFORM] Audio Engine: {'edge-tts' if HAS_EDGE_TTS else 'gTTS fallback'}")
    
    def generate_documentary_script(self, outline: DocumentaryOutline) -> str:
        """
        Generate a full 2000-2500 word documentary script from outline.
        Uses GPT-4 for expansion with specific voice preservation.
        """
        if not self.openai_client:
            print("[LONGFORM] ⚠️ No OpenAI API - using template expansion")
            return self._template_expansion(outline)
        
        prompt = f"""You are a documentary scriptwriter specializing in financial system exposés.

SOURCE TOPIC: {outline.source_dna.topic}
THESIS: {outline.thesis}
HOOK TYPE: {outline.source_dna.hook_type}
EMOTIONAL TRIGGER: {outline.source_dna.emotional_trigger}

Write a 17-minute documentary script (approximately 2500 words) following this 5-Act structure:

ACT 1 - HOOK (2 minutes, ~300 words):
{json.dumps(outline.acts[0], indent=2)}

ACT 2 - MECHANISM (4 minutes, ~600 words):
{json.dumps(outline.acts[1], indent=2)}

ACT 3 - PLAYERS (4 minutes, ~600 words):
{json.dumps(outline.acts[2], indent=2)}

ACT 4 - CONSEQUENCES (4 minutes, ~600 words):
{json.dumps(outline.acts[3], indent=2)}

ACT 5 - RESOLUTION (3 minutes, ~400 words):
{json.dumps(outline.acts[4], indent=2)}

VOICE REQUIREMENTS:
- First person, revelatory tone
- "I" statements, not "you should"
- No motivation, no fluff
- Concrete examples and specifics
- Escalating stakes through each act
- End with intellectual conclusion, not call to action

FORMAT:
- Clear [ACT X: NAME] headers
- Natural paragraph breaks
- Include subtle [VISUAL: description] cues for B-roll

Begin the script:"""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a documentary scriptwriter with a dark, revelatory voice. You expose hidden systems with concrete specifics, not vague claims."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=4000
            )
            script = response.choices[0].message.content
            print(f"[LONGFORM] Generated {len(script.split())} word script")
            return script
        except Exception as e:
            print(f"[LONGFORM] OpenAI error: {e}")
            return self._template_expansion(outline)
    
    def _template_expansion(self, outline: DocumentaryOutline) -> str:
        """Fallback template expansion without API."""
        script_parts = []
        
        for act in outline.acts:
            script_parts.append(f"\n[ACT: {act['name'].upper()}]")
            script_parts.append(f"\n{act['description']}")
            script_parts.append("\n\n[This section explores the following points:]")
            for point in act.get('key_points', []):
                script_parts.append(f"\n- {point}")
            script_parts.append("\n")
        
        script = "\n".join(script_parts)
        print(f"[LONGFORM] Template expansion: {len(script.split())} words")
        return script
    
    async def generate_audio(self, script: str, output_path: Path, dna: DocumentaryDNA = None) -> Optional[Path]:
        """
        Generate documentary narration using hardened LongformAudioEngine.
        
        Uses:
        - edge-tts with voice fallbacks
        - Minimum script validation (100 words)
        - Proper async/await handling
        """
        import re
        
        # Clean script - remove visual cues and headers
        clean_script = script
        clean_script = re.sub(r'\[VISUAL:.*?\]', '', clean_script)
        clean_script = re.sub(r'\[ACT.*?\]', '', clean_script)
        clean_script = re.sub(r'\s+', ' ', clean_script).strip()
        
        # Use the hardened audio engine
        audio_path = await self.audio_engine.generate_from_script_with_validation(
            script=clean_script,
            dna=dna,
            voice=TTSVoice.ANDREW  # Documentary authority voice
        )
        
        if audio_path:
            print(f"[LONGFORM] ✅ Audio generated: {audio_path}")
            return Path(audio_path)
        else:
            print("[LONGFORM] ❌ Audio generation failed - check logs")
            return None
    
    async def assemble_documentary(
        self, 
        outline: DocumentaryOutline,
        script: str,
        audio_path: Optional[Path] = None
    ) -> Optional[Path]:
        """
        Assemble the full documentary video.
        """
        # Get visual clips for each act using BRollEngine
        visual_clips = []
        broll_engine = BRollEngine()
        
        for act in outline.acts:
            intent = act.get("visual_intent", "power_finance")
            clip = await broll_engine.get_clip_for_intent(intent)
            
            if clip:
                visual_clips.append({
                    "act": act["name"],
                    "clip": clip,
                    "duration": act["duration_minutes"] * 60
                })
        
        # Build the documentary using the longform_builder
        try:
            output_path = await self.longform_builder.expand_to_documentary(
                dna=self._convert_outline_to_dna(outline),
                audio_path=str(audio_path) if audio_path else None
            )
        except Exception as e:
            print(f"[LONGFORM] Assembly error: {e}")
            output_path = None
        
        if output_path:
            print(f"[LONGFORM] ✅ Documentary assembled: {output_path}")
        
        return output_path
    
    def _convert_outline_to_dna(self, outline: DocumentaryOutline):
        """Convert DocumentaryOutline to DocumentaryDNA for builder."""
        from engines.longform_builder import DocumentaryDNA
        return DocumentaryDNA(
            topic=outline.source_dna.topic,
            theme="hidden_truth",
            hook_structure=outline.source_dna.hook_type,
            emotional_trigger=outline.source_dna.emotional_trigger,
            visual_intent=outline.source_dna.visual_dna.intent,
            curiosity_gaps=["How does this work?", "Who benefits?", "What can you do?"],
            retention_pattern="front_loaded",
            rpm_score=outline.source_dna.rpm,
            source_short_id=outline.source_dna.video_id
        )
    
    async def produce_documentary(self, dna: ShortDNA) -> Optional[Path]:
        """
        Full documentary production pipeline from DNA.
        """
        print(f"\n{'='*60}")
        print(f"[LONGFORM] 🎬 PRODUCING DOCUMENTARY")
        print(f"[LONGFORM] Source: {dna.topic[:50]}...")
        print(f"[LONGFORM] Hook: {dna.hook_type}, Emotion: {dna.emotional_trigger}")
        print(f"{'='*60}\n")
        
        # Step 1: Expand to outline
        outline = self.dna_expander.expand_to_outline(dna)
        
        # Step 2: Generate script
        script = self.generate_documentary_script(outline)
        
        # Save script
        script_path = SCRIPTS_DIR / f"doc_{dna.video_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script)
        print(f"[LONGFORM] Script saved: {script_path}")
        
        # Step 3: Generate audio
        audio_path = AUDIO_DIR / f"doc_{dna.video_id}.mp3"
        audio_result = await self.generate_audio(script, audio_path)
        
        # Step 4: Assemble documentary
        output_path = await self.assemble_documentary(outline, script, audio_result)
        
        return output_path
    
    async def run_batch(self, max_videos: int = 1):
        """
        Process Golden Gate winners from AAVE engine in batch.
        
        Uses AAVE's get_expansion_candidates() for best winners.
        """
        # Get expansion candidates from AAVE engine (replaces old DNA expander)
        candidates = self.aave_engine.get_expansion_candidates(limit=max_videos)
        
        if not candidates:
            print("[LONGFORM] No Golden Gate winners found")
            print("[LONGFORM] Thresholds: AVD > 75%, RPM > $0.05, Replay > 15%")
            return []
        
        print(f"[LONGFORM] Processing {len(candidates)} expansion candidates")
        
        results = []
        for candidate in candidates:
            try:
                # Convert AAVE candidate to production format
                result = await self.produce_from_aave_winner(candidate)
                if result:
                    results.append(result)
            except Exception as e:
                print(f"[LONGFORM] Error processing {candidate.get('video_id', 'unknown')}: {e}")
        
        return results
    
    async def produce_from_aave_winner(self, winner: Dict[str, Any]) -> Optional[Path]:
        """
        Produce documentary from AAVE Golden Gate winner.
        
        This is the main n8n integration endpoint.
        """
        video_id = winner.get("video_id", "unknown")
        topic = winner.get("topic", "Unknown Topic")
        dna_data = winner.get("dna", {})
        doc_potential = winner.get("documentary_potential", {})
        
        print(f"\n{'='*60}")
        print(f"[LONGFORM] 🎬 PRODUCING FROM AAVE WINNER")
        print(f"[LONGFORM] Video: {video_id}")
        print(f"[LONGFORM] Topic: {topic[:50]}...")
        print(f"[LONGFORM] Theme: {doc_potential.get('theme', 'hidden_truth')}")
        print(f"[LONGFORM] Revenue Multiplier: {doc_potential.get('revenue_multiplier', '170x-850x')}")
        print(f"{'='*60}\n")
        
        # Create DocumentaryDNA from winner data
        documentary_dna = DocumentaryDNA(
            topic=topic,
            theme=doc_potential.get("theme", "hidden_truth"),
            hook_structure=dna_data.get("hook_type", "threat"),
            emotional_trigger=self._detect_emotion_from_topic(topic),
            visual_intent=dna_data.get("broll_density", 0.5),
            curiosity_gaps=self._generate_curiosity_gaps(topic),
            retention_pattern="front_loaded",
            rpm_score=winner.get("metrics", {}).get("rpm", 0.05),
            source_short_id=video_id
        )
        
        # Generate expanded script
        script = await self._expand_winner_to_script(winner, documentary_dna)
        
        # Save script
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        script_path = SCRIPTS_DIR / f"doc_{video_id}_{timestamp}.txt"
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script)
        print(f"[LONGFORM] Script saved: {script_path}")
        
        # Generate audio using hardened engine
        audio_path = AUDIO_DIR / f"doc_{video_id}.mp3"
        audio_result = await self.generate_audio(script, audio_path, documentary_dna)
        
        if not audio_result:
            print("[LONGFORM] ⚠️ Audio generation failed - cannot proceed")
            return None
        
        # Assemble documentary
        try:
            output_path = await self.longform_builder.expand_to_documentary(
                dna=documentary_dna,
                audio_path=str(audio_result)
            )
            if output_path:
                print(f"[LONGFORM] ✅ Documentary complete: {output_path}")
                return Path(output_path)
        except Exception as e:
            print(f"[LONGFORM] Assembly error: {e}")
        
        return None
    
    def _detect_emotion_from_topic(self, topic: str) -> str:
        """Detect emotional trigger from topic."""
        topic_lower = topic.lower()
        if any(w in topic_lower for w in ["unfair", "rigged", "designed"]):
            return "injustice"
        if any(w in topic_lower for w in ["secret", "hidden", "never told"]):
            return "revelation"
        if any(w in topic_lower for w in ["disappear", "collapse", "end"]):
            return "urgency"
        return "curiosity"
    
    def _generate_curiosity_gaps(self, topic: str) -> List[str]:
        """Generate curiosity gaps from topic."""
        return [
            f"How does this ({topic[:30]}...) actually work?",
            "Who designed this system and why?",
            "What happens if you don't understand this?",
            "What can you do about it?",
        ]
    
    async def _expand_winner_to_script(self, winner: Dict, dna: DocumentaryDNA) -> str:
        """Expand winner topic into full documentary script."""
        topic = winner.get("topic", "")
        doc_potential = winner.get("documentary_potential", {})
        target_minutes = doc_potential.get("estimated_length_minutes", 15)
        
        if self.openai_client:
            return await self._gpt4_script_expansion(topic, dna, target_minutes)
        else:
            return self._fallback_script_expansion(topic, dna, target_minutes)
    
    async def _gpt4_script_expansion(self, topic: str, dna: DocumentaryDNA, target_minutes: int = 15) -> str:
        """
        Expand topic into full documentary script using GPT-4o.
        
        5-Act Structure:
        1. Hook (2 min) - Shorts-level intensity
        2. Mechanism (4 min) - How the system works
        3. Players (4 min) - Who benefits, who loses
        4. Consequences (4 min) - Why this affects viewer
        5. Resolution (3 min) - Strategic understanding
        """
        target_words = target_minutes * 150  # ~150 words per minute
        
        prompt = f"""You are a documentary scriptwriter specializing in financial system exposés.

TOPIC: {topic}
THEME: {dna.theme}
EMOTIONAL TRIGGER: {dna.emotional_trigger}
CURIOSITY GAPS TO ADDRESS: {', '.join(dna.curiosity_gaps)}

Write a {target_minutes}-minute documentary script (approximately {target_words} words) following this 5-Act structure:

ACT 1 - THE HOOK (2 minutes, ~300 words):
- Open with the most provocative claim from the topic
- Create immediate tension
- Make viewer feel something is being hidden from them
- Shorts-level intensity and pacing

ACT 2 - THE MECHANISM (4 minutes, ~600 words):
- Explain HOW this system actually works
- Use concrete examples, specific numbers
- Build understanding before judgment
- Educational but not boring

ACT 3 - THE PLAYERS (4 minutes, ~600 words):
- Who designed this system and why
- Who benefits the most
- Historical examples of this pattern
- Name specific institutions/people when relevant

ACT 4 - THE CONSEQUENCES (4 minutes, ~600 words):
- Why this affects the viewer personally
- Future implications if trends continue
- Escalate the stakes dramatically
- Make it personal

ACT 5 - THE RESOLUTION (3 minutes, ~400 words):
- Strategic understanding (NOT motivational fluff)
- What the viewer now understands that others don't
- Intellectual closure, not hope
- Leave them thinking, not inspired

VOICE REQUIREMENTS:
- First person, revelatory tone ("I discovered...", "Here's what I found...")
- No motivation, no "you can do it" energy
- Concrete examples, specific numbers, real names
- Dark, authoritative, documentary tone
- Each act should flow naturally into the next

FORMAT:
- Include [ACT X: NAME] headers
- Natural paragraph breaks for narration
- Include [VISUAL: description] cues for B-roll

Write the complete script:"""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a documentary scriptwriter with a dark, revelatory voice. You expose hidden systems with concrete specifics, not vague claims."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=4000
            )
            script = response.choices[0].message.content
            word_count = len(script.split())
            print(f"[LONGFORM] GPT-4 generated {word_count} word script")
            return script
        except Exception as e:
            print(f"[LONGFORM] OpenAI error: {e}")
            return self._fallback_script_expansion(topic, dna, target_minutes)
    
    def _fallback_script_expansion(self, topic: str, dna: DocumentaryDNA, target_minutes: int = 15) -> str:
        """
        Template-based script expansion without API.
        Used when OpenAI is unavailable.
        """
        return f"""[ACT 1: THE HOOK]

{topic}. 

That's what they want you to believe. But I spent weeks digging into the actual data, 
and what I found changes everything you think you know about how this works.

See, the official story sounds reasonable enough. It's designed to. But when you trace 
the money, when you look at who actually benefits from the current system, a very 
different picture emerges.

Let me show you what I discovered.

[VISUAL: Financial data visualizations, money flow diagrams]

[ACT 2: THE MECHANISM]

Here's how it actually works.

Every time you interact with the financial system, whether that's using your bank, 
investing in the market, or simply holding cash, there are mechanisms in place that 
most people never see.

These aren't accidents. They're features, designed by people who understand that the 
best way to extract value is to make the extraction invisible.

The system operates on what insiders call "{dna.theme}". It sounds technical because 
that's the point. Complexity is a feature, not a bug.

When you break it down to its core components, you find the same pattern repeating:
- Rules that sound fair but aren't
- Complexity that benefits those who create it
- Small extractions that compound over time

[VISUAL: System diagrams, institutional buildings, trading floors]

[ACT 3: THE PLAYERS]

Now let's talk about who designed this.

The same institutions keep appearing whenever you follow these patterns. The same 
names, the same strategies, refined over decades.

This isn't conspiracy. It's documented history. The same playbook has been used 
for generations, just with updated terminology.

Think about who writes the rules. Think about who benefits when those rules are 
followed. It's never random who ends up on top.

[VISUAL: Historical footage, institution logos, congressional hearings]

[ACT 4: THE CONSEQUENCES]

So what does this mean for you?

Every day this continues, the gap widens. The extraction compounds. And most people 
never notice because it happens slowly, invisibly.

By the time the effects become obvious, years of wealth have already transferred. 
By the time you understand the mechanism, you've already paid the price.

This is why "{topic}" matters more than most people realize. It's not just abstract 
economics. It's your actual purchasing power. Your actual options. Your actual future.

The question isn't whether this affects you. It's whether you'll understand it in 
time to adapt.

[VISUAL: Economic charts, generational wealth gaps, future projections]

[ACT 5: THE RESOLUTION]

Here's what you need to understand.

The system isn't broken. It's working exactly as designed. Once you see that, 
everything clicks into place.

This isn't about being angry. It's about being accurate. The people who designed 
these systems understood incentives better than those who operate within them.

Understanding doesn't change the system. But it changes what you do with the 
information. And that's the only part you can actually control.

Most people will never watch this all the way through. Most people will keep 
operating with incomplete information. That's also by design.

You now know something most people don't about {topic.lower()}.

What you do with that knowledge is up to you.

[VISUAL: Slow fade to black, contemplative imagery]
"""
    
    async def run_demo(self, topic: str = None):
        """
        Run a demo documentary production.
        """
        # Create synthetic DNA for demo
        from engines.dna_expander import VisualDNA
        
        topic = topic or "The Hidden Tax That Steals 7% Of Your Wealth Every Year"
        
        demo_visual = VisualDNA(
            intent="power_finance",
            pacing="aggressive",
            motion_density="high",
            color_mood="dark",
            scene_duration=2.0,
            cut_frequency=25.0
        )
        
        demo_dna = ShortDNA(
            video_id="demo_001",
            topic=topic,
            hook_type="revelation",
            emotional_trigger="injustice",
            visual_dna=demo_visual,
            script_hash="demo",
            is_winner=True,
            should_expand=True,
            retention_rate=0.92,
            rpm=0.08
        )
        
        print(f"\n[LONGFORM] 🎬 DEMO MODE")
        print(f"[LONGFORM] Topic: {topic}")
        
        result = await self.produce_documentary(demo_dna)
        return result


async def main():
    parser = argparse.ArgumentParser(description="Long-form Documentary Mode")
    parser.add_argument("--demo", action="store_true", help="Run demo production")
    parser.add_argument("--topic", type=str, help="Custom topic for demo")
    parser.add_argument("--batch", type=int, default=1, help="Number of documentaries to produce")
    parser.add_argument("--loop", action="store_true", help="Run continuously")
    parser.add_argument("--interval", type=int, default=86400, help="Loop interval in seconds (default: 24 hours)")
    
    args = parser.parse_args()
    
    longform = LongformMode()
    
    if args.demo:
        result = await longform.run_demo(args.topic)
        if result:
            print(f"\n✅ Demo documentary: {result}")
    elif args.loop:
        print(f"[LONGFORM] Starting continuous mode (every {args.interval}s)")
        while True:
            try:
                results = await longform.run_batch(args.batch)
                print(f"[LONGFORM] Batch complete: {len(results)} documentaries")
                print(f"[LONGFORM] Next run in {args.interval}s...")
                await asyncio.sleep(args.interval)
            except KeyboardInterrupt:
                print("\n[LONGFORM] Stopped by user")
                break
            except Exception as e:
                print(f"[LONGFORM] Error: {e}")
                await asyncio.sleep(300)  # Wait 5 min on error
    else:
        results = await longform.run_batch(args.batch)
        print(f"\n✅ Produced {len(results)} documentaries")


if __name__ == "__main__":
    asyncio.run(main())
