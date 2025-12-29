"""
ELITE OMNI PIPELINE - Complete Orchestrator
============================================

The unified entry point for the entire pipeline:

STAGE 1: OPAL (Clip Factory)
    → Generates elite 8-10s clips
    → Self-heals errors
    → Exports structured data

STAGE 2: ASSEMBLER (VS Code / Local)
    → Reads OPAL output
    → Decides stitch order
    → Applies transitions/music
    → Produces assembly-ready video

STAGE 3: RUNWAY/GRID (Cinematic Finish)
    → Scene extension
    → Motion enhancement
    → Color grading

STAGE 4: PUBLISH (Money Machine)
    → YouTube upload
    → Telegram notify
    → DNA logging

Usage:
    python ELITE_OMNI.py --prompts data/scripts/prompts.json
    python ELITE_OMNI.py --topic "Why the Rich Use Debt"
    python ELITE_OMNI.py --resume data/opal_output/2025-12-28_123456
"""

import os
import sys
import json
import asyncio
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any

# Add engines to path
sys.path.insert(0, str(Path(__file__).parent))

from engines.opal_factory import OpalClipFactory, OperatingMode
from engines.omni_assembler import OmniAssembler, AssemblyConfig


class EliteOmniPipeline:
    """
    THE ELITE OMNI PIPELINE
    
    One command to:
    1. Generate elite clips with OPAL
    2. Assemble with OMNI Assembler
    3. Optionally publish to YouTube
    """
    
    # Default prompts for finance/wealth content
    DEFAULT_PROMPTS = [
        "A sunrise casting golden light over a modern city skyline, cinematic",
        "Currency notes dissolving into digital particles, dark atmospheric",
        "A locked vault door slowly opening to reveal golden light, dramatic",
        "Chains breaking apart in slow motion, symbolic freedom",
        "A chess king piece dominating the board from above, power dynamics",
        "Dark storm clouds parting to reveal intense sunlight, revelation",
        "Streams of data flowing across transparent display screens, technology",
        "A professional at a workstation with multiple screens showing charts",
        "A person standing at a crossroads with dramatic lighting, decision",
        "An eye opening wide reflecting digital data streams, awareness",
        "Gold coins stacking in an endless tower, wealth accumulation",
        "A puppet on strings with the strings being cut, liberation"
    ]
    
    def __init__(
        self,
        output_base: str = "data/opal_output",
        mode: str = "SAFE"
    ):
        self.output_base = Path(output_base)
        self.mode = OperatingMode.SAFE if mode.upper() == "SAFE" else OperatingMode.ACCELERATED
        
        # Ensure output directory exists
        self.output_base.mkdir(parents=True, exist_ok=True)
        
    def generate_prompts_from_topic(self, topic: str) -> List[str]:
        """
        Generate visual prompts from a topic using GPT-4o style breakdown.
        
        For now, uses a template-based approach.
        In production, this would call OpenAI/Claude.
        """
        # Visual concepts that work for any finance topic
        concepts = [
            f"A dramatic title card with the words related to {topic}, dark cinematic",
            "A person in shadows looking up at towering buildings, oppression",
            "Money flowing from many hands into one, wealth concentration",
            "A maze seen from above with a person trapped inside, system",
            "Scales of justice tipping dramatically, imbalance",
            "A clock with hands spinning rapidly, time pressure",
            "A door marked 'EXIT' with light streaming through, escape",
            "Charts and graphs showing dramatic downward trend, decline",
            "A mirror reflection showing a different reality, deception",
            "Chains around a wallet or piggy bank, financial trap",
            "A lighthouse beam cutting through dark fog, guidance",
            "A person breaking through a wall, breakthrough moment"
        ]
        
        return concepts
    
    def load_prompts_from_file(self, path: str) -> List[str]:
        """Load prompts from a JSON file."""
        with open(path) as f:
            data = json.load(f)
            
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and "prompts" in data:
            return data["prompts"]
        elif isinstance(data, dict) and "beats" in data:
            # Support script format from GPT-4o
            return [beat.get("visual", beat) for beat in data["beats"]]
        else:
            raise ValueError(f"Unrecognized prompt file format: {path}")
    
    async def run_stage1_opal(self, prompts: List[str]) -> Path:
        """
        STAGE 1: Run OPAL Clip Factory
        
        Returns:
            Path to OPAL output directory
        """
        print("\n" + "="*70)
        print("🔮 STAGE 1: OPAL CLIP FACTORY")
        print("="*70)
        
        factory = OpalClipFactory(
            output_base=str(self.output_base),
            mode=self.mode,
            clips_per_run=len(prompts),
            duration_per_clip=8.0
        )
        
        result = await factory.run(prompts)
        return result.output_dir
    
    def run_stage2_assembly(
        self,
        opal_dir: Path,
        with_transitions: bool = True,
        music_path: Optional[str] = None
    ) -> Path:
        """
        STAGE 2: Run OMNI Assembler
        
        Returns:
            Path to assembled video
        """
        print("\n" + "="*70)
        print("🎬 STAGE 2: OMNI ASSEMBLER")
        print("="*70)
        
        assembler = OmniAssembler(str(opal_dir))
        
        # Analyze first
        analysis = assembler.analyze_clips()
        print(f"\n📊 Clip Analysis:")
        print(f"   Total clips: {analysis['total_clips']}")
        print(f"   Estimated duration: {analysis['estimated_duration']}s")
        for rec in analysis['recommendations']:
            print(f"   💡 {rec}")
        
        # Assemble
        config = AssemblyConfig(
            output_name="elite_video",
            transition_type="fade",
            transition_duration=0.3
        )
        
        if with_transitions:
            video_path = assembler.assemble_with_transitions(config=config)
        else:
            video_path = assembler.assemble_simple(config=config)
        
        # Add music if provided
        if music_path and Path(music_path).exists():
            video_path = assembler.add_audio_track(str(video_path), music_path)
        
        # Export report
        assembler.export_assembly_report()
        
        return video_path
    
    def run_stage3_finish(self, video_path: Path) -> Path:
        """
        STAGE 3: Cinematic Finishing (Runway/Grid)
        
        This is a placeholder - actual implementation would:
        - Upload to Runway for motion enhancement
        - Apply color grading
        - Add film grain
        
        For now, just returns the input path.
        """
        print("\n" + "="*70)
        print("🎥 STAGE 3: CINEMATIC FINISH (Placeholder)")
        print("="*70)
        print("   ℹ️ In production, this would:")
        print("      - Upload to Runway for scene extension")
        print("      - Apply camera motion enhancement")
        print("      - Add film grain and color grading")
        print("   ⏭️ Skipping for now - video is assembly-ready")
        
        return video_path
    
    def run_stage4_publish(
        self,
        video_path: Path,
        title: str,
        description: str,
        upload_to_youtube: bool = False
    ) -> Dict[str, Any]:
        """
        STAGE 4: Publish (Money Machine Integration)
        
        This connects to the Money Machine repo for:
        - YouTube upload
        - Telegram notification
        - DNA logging
        """
        print("\n" + "="*70)
        print("📤 STAGE 4: PUBLISH")
        print("="*70)
        
        result = {
            "video_path": str(video_path),
            "title": title,
            "description": description,
            "youtube_id": None,
            "telegram_sent": False
        }
        
        if upload_to_youtube:
            print("   ⚠️ YouTube upload requires OAuth2 credentials")
            print("   💡 Use the n8n workflow for automated uploads")
        else:
            print("   ℹ️ Video ready for manual upload")
            print(f"   📁 Path: {video_path}")
        
        return result
    
    async def run_full_pipeline(
        self,
        prompts: Optional[List[str]] = None,
        topic: Optional[str] = None,
        prompts_file: Optional[str] = None,
        with_transitions: bool = True,
        music_path: Optional[str] = None,
        upload: bool = False
    ) -> Dict[str, Any]:
        """
        Run the complete Elite Omni Pipeline.
        
        Args:
            prompts: List of visual prompts
            topic: Topic to generate prompts from
            prompts_file: Path to JSON file with prompts
            with_transitions: Use crossfade transitions
            music_path: Path to background music
            upload: Upload to YouTube when done
            
        Returns:
            Complete pipeline result with all paths and metadata
        """
        print("\n" + "🔥"*35)
        print("🔥 ELITE OMNI PIPELINE - FULL RUN")
        print("🔥"*35)
        print(f"⏰ Started: {datetime.now().isoformat()}")
        print(f"🔒 Mode: {self.mode.value}")
        
        # Determine prompts
        if prompts:
            final_prompts = prompts
        elif prompts_file:
            final_prompts = self.load_prompts_from_file(prompts_file)
        elif topic:
            final_prompts = self.generate_prompts_from_topic(topic)
        else:
            print("   ℹ️ No prompts specified, using defaults")
            final_prompts = self.DEFAULT_PROMPTS
        
        print(f"📝 Prompts: {len(final_prompts)}")
        
        # Stage 1: OPAL
        opal_dir = await self.run_stage1_opal(final_prompts)
        
        # Stage 2: Assembly
        video_path = self.run_stage2_assembly(
            opal_dir,
            with_transitions=with_transitions,
            music_path=music_path
        )
        
        # Stage 3: Cinematic Finish
        final_video = self.run_stage3_finish(video_path)
        
        # Stage 4: Publish
        publish_result = self.run_stage4_publish(
            final_video,
            title=topic or "Elite Money Machine Video",
            description="Generated by the Elite Omni Pipeline",
            upload_to_youtube=upload
        )
        
        # Final summary
        print("\n" + "="*70)
        print("✅ ELITE OMNI PIPELINE COMPLETE")
        print("="*70)
        print(f"📁 OPAL Output: {opal_dir}")
        print(f"🎬 Final Video: {final_video}")
        print(f"⏰ Finished: {datetime.now().isoformat()}")
        
        return {
            "opal_dir": str(opal_dir),
            "video_path": str(final_video),
            "prompts_used": len(final_prompts),
            "mode": self.mode.value,
            "publish_result": publish_result
        }
    
    def resume_from_opal(
        self,
        opal_dir: str,
        with_transitions: bool = True,
        music_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Resume pipeline from existing OPAL output.
        
        Useful when:
        - OPAL completed but assembly failed
        - You want to re-assemble with different settings
        - Testing assembly configurations
        """
        print("\n" + "="*70)
        print("🔄 RESUMING FROM EXISTING OPAL OUTPUT")
        print("="*70)
        print(f"📁 OPAL Dir: {opal_dir}")
        
        opal_path = Path(opal_dir)
        
        # Stage 2: Assembly
        video_path = self.run_stage2_assembly(
            opal_path,
            with_transitions=with_transitions,
            music_path=music_path
        )
        
        # Stage 3: Finish
        final_video = self.run_stage3_finish(video_path)
        
        print("\n" + "="*70)
        print("✅ RESUME COMPLETE")
        print("="*70)
        print(f"🎬 Final Video: {final_video}")
        
        return {
            "opal_dir": str(opal_path),
            "video_path": str(final_video)
        }


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Elite Omni Pipeline - Generate elite videos with self-healing AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python ELITE_OMNI.py --topic "Why the Rich Use Debt"
  python ELITE_OMNI.py --prompts data/scripts/my_prompts.json
  python ELITE_OMNI.py --resume data/opal_output/2025-12-28_123456
  python ELITE_OMNI.py --topic "Inflation Secrets" --music assets/bg_music.mp3
        """
    )
    
    # Input options (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument(
        "--topic",
        help="Topic to generate prompts from"
    )
    input_group.add_argument(
        "--prompts",
        help="Path to JSON file containing prompts"
    )
    input_group.add_argument(
        "--resume",
        help="Resume from existing OPAL output directory"
    )
    
    # Pipeline options
    parser.add_argument(
        "--mode",
        choices=["SAFE", "ACCELERATED"],
        default="SAFE",
        help="Operating mode (default: SAFE)"
    )
    parser.add_argument(
        "--no-transitions",
        action="store_true",
        help="Skip crossfade transitions (faster)"
    )
    parser.add_argument(
        "--music",
        help="Path to background music file"
    )
    parser.add_argument(
        "--upload",
        action="store_true",
        help="Upload to YouTube when done (requires OAuth)"
    )
    parser.add_argument(
        "--output-dir",
        default="data/opal_output",
        help="Base directory for OPAL output"
    )
    
    args = parser.parse_args()
    
    # Create pipeline
    pipeline = EliteOmniPipeline(
        output_base=args.output_dir,
        mode=args.mode
    )
    
    # Run appropriate mode
    if args.resume:
        result = pipeline.resume_from_opal(
            args.resume,
            with_transitions=not args.no_transitions,
            music_path=args.music
        )
    else:
        result = asyncio.run(pipeline.run_full_pipeline(
            topic=args.topic,
            prompts_file=args.prompts,
            with_transitions=not args.no_transitions,
            music_path=args.music,
            upload=args.upload
        ))
    
    print(f"\n📊 Result: {json.dumps(result, indent=2)}")


if __name__ == "__main__":
    main()
