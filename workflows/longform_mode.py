"""
LONG-FORM DOCUMENTARY MODE v1.0
Converts winning Shorts DNA into 10-20 minute documentaries.

Revenue Mathematics:
- Shorts RPM: $0.02 - $0.08
- Long-form RPM: $12 - $30+
- Watch time multiplier: 60 seconds → 17 minutes = 17x
- Combined: 170-850x revenue per view

This workflow:
1. Monitors DNA pool for expansion candidates
2. Generates documentary outlines
3. Produces full scripts using GPT-4
4. Assembles videos with 5-Act structure
5. Uploads to YouTube with SEO optimization

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

from engines.dna_expander import DNAExpander, ShortDNA, DocumentaryOutline
from engines.longform_builder import LongformBuilder
from engines.broll_engine import get_clip_for_intent

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


SCRIPTS_DIR = BASE_DIR / "data" / "scripts"
AUDIO_DIR = BASE_DIR / "data" / "audio" 
OUTPUT_DIR = BASE_DIR / "data" / "output"
DOCUMENTARIES_DIR = OUTPUT_DIR / "documentaries"


class LongformMode:
    """
    Autonomous documentary production workflow.
    """
    
    def __init__(self):
        self.dna_expander = DNAExpander()
        self.longform_builder = LongformBuilder()
        
        # Create directories
        SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
        AUDIO_DIR.mkdir(parents=True, exist_ok=True)
        DOCUMENTARIES_DIR.mkdir(parents=True, exist_ok=True)
        
        # OpenAI client
        self.openai_client = None
        if HAS_OPENAI and os.getenv("OPENAI_API_KEY"):
            self.openai_client = OpenAI()
        
        print("[LONGFORM] Documentary mode initialized")
        print(f"[LONGFORM] DNA Pool: {len(self.dna_expander.dna_pool)} profiles")
        print(f"[LONGFORM] Expansion candidates: {len(self.dna_expander.get_expansion_candidates())}")
    
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
    
    async def generate_audio(self, script: str, output_path: Path) -> Optional[Path]:
        """
        Generate documentary narration using edge-tts.
        """
        if not HAS_EDGE_TTS:
            print("[LONGFORM] ⚠️ edge-tts not available")
            return None
        
        try:
            # Use a professional documentary voice
            voice = "en-US-GuyNeural"  # Deep, authoritative
            
            # Clean script - remove visual cues
            clean_script = script
            import re
            clean_script = re.sub(r'\[VISUAL:.*?\]', '', clean_script)
            clean_script = re.sub(r'\[ACT.*?\]', '', clean_script)
            
            communicate = edge_tts.Communicate(clean_script, voice)
            await communicate.save(str(output_path))
            
            print(f"[LONGFORM] Audio generated: {output_path}")
            return output_path
        except Exception as e:
            print(f"[LONGFORM] Audio error: {e}")
            return None
    
    def assemble_documentary(
        self, 
        outline: DocumentaryOutline,
        script: str,
        audio_path: Optional[Path] = None
    ) -> Optional[Path]:
        """
        Assemble the full documentary video.
        """
        # Get visual clips for each act
        visual_clips = []
        for act in outline.acts:
            intent = act.get("visual_intent", "power_finance")
            clip = get_clip_for_intent(intent)
            if clip:
                visual_clips.append({
                    "act": act["name"],
                    "clip": clip,
                    "duration": act["duration_minutes"] * 60
                })
        
        # Build the documentary
        output_path = self.longform_builder.build(
            outline=outline,
            script=script,
            audio_path=str(audio_path) if audio_path else None,
            visual_clips=visual_clips
        )
        
        if output_path:
            print(f"[LONGFORM] ✅ Documentary assembled: {output_path}")
        
        return output_path
    
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
        output_path = self.assemble_documentary(outline, script, audio_result)
        
        return output_path
    
    async def run_batch(self, max_videos: int = 1):
        """
        Process expansion candidates in batch.
        """
        candidates = self.dna_expander.get_expansion_candidates()
        
        if not candidates:
            print("[LONGFORM] No expansion candidates available")
            # For development: use winners if no explicit candidates
            candidates = self.dna_expander.get_winners()[:max_videos]
        
        if not candidates:
            print("[LONGFORM] No winners in DNA pool - waiting for Shorts data")
            return []
        
        print(f"[LONGFORM] Processing {min(len(candidates), max_videos)} candidates")
        
        results = []
        for dna in candidates[:max_videos]:
            try:
                result = await self.produce_documentary(dna)
                if result:
                    results.append(result)
            except Exception as e:
                print(f"[LONGFORM] Error processing {dna.video_id}: {e}")
        
        return results
    
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
