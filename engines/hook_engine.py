"""
HOOK ENGINE - Cinematic Opening Hooks
Creates Hollywood-style hook overlays for first 0-3 seconds.
"""

import os
import random
import httpx
from pathlib import Path
from typing import Dict, List

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

HOOK_STYLES = {
    "lower_third": {"y_position": "h-h/5", "font_size": 56, "box": True, "box_opacity": 0.7},
    "center_punch": {"y_position": "h/2", "font_size": 72, "box": False},
}


async def generate_hook_text(topic: str) -> str:
    prompt = f"""Generate a SINGLE compelling video hook for: "{topic}"
The hook should be 3-6 words MAX, create curiosity, sound like expert authority.
Examples: "The math doesn't lie", "Banks hate this truth", "Nobody talks about this"
Return ONLY the hook text."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post("https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
                json={"model": "llama-3.1-70b-versatile", "messages": [{"role": "user", "content": prompt}], "max_tokens": 30, "temperature": 0.9})
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"].strip().strip('"\'')
    except: pass
    return random.choice(["The truth about money", "What they won't tell you", "This changes everything"])


def generate_hook_filter(hook_text: str, style_name: str = "lower_third", duration: float = 2.5, start_time: float = 0.3) -> str:
    style = HOOK_STYLES.get(style_name, HOOK_STYLES["lower_third"])
    escaped = hook_text.replace("'", "\\'").replace(":", "\\:")
    end_time = start_time + duration
    filter_parts = [f"drawtext=text='{escaped}'", f"fontsize={style['font_size']}", "fontfile=/Windows/Fonts/arial.ttf",
        "fontcolor=white", "x=(w-text_w)/2", f"y={style['y_position']}"]
    if style.get("box"):
        filter_parts.extend([f"box=1", f"boxcolor=black@{style.get('box_opacity', 0.7)}", "boxborderw=15"])
    filter_parts.append(f"enable='between(t,{start_time},{end_time})'")
    return ":".join(filter_parts)


def generate_hook_ass_overlay(hook_text: str, output_path: str, start_time: float = 0.3, duration: float = 2.5) -> str:
    end_time = start_time + duration
    def ass_time(t):
        h, m, s = int(t // 3600), int((t % 3600) // 60), t % 60
        return f"{h}:{m:02d}:{s:05.2f}"
    content = f"""[Script Info]
Title: Hook Overlay
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Hook,Montserrat,60,&H00FFFFFF,&H00FFFFFF,&H00000000,&HC0000000,1,0,0,0,100,100,2,0,3,4,0,2,50,50,350,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,{ass_time(start_time)},{ass_time(end_time)},Hook,,0,0,0,,{{\\fad(100,200)\\move(540,1650,540,1550,0,150)}}{hook_text}
"""
    Path(output_path).write_text(content, encoding="utf-8")
    return output_path


class HookEngine:
    def __init__(self, output_dir: str = "data/temp"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def create_hook_overlay(self, topic: str, video_id: str, style: str = "lower_third") -> Dict:
        hook_text = await generate_hook_text(topic)
        ass_path = self.output_dir / f"{video_id}_hook.ass"
        generate_hook_ass_overlay(hook_text, str(ass_path))
        return {"hook_text": hook_text, "ass_path": str(ass_path), "filter": generate_hook_filter(hook_text, style), "duration": 2.5, "start": 0.3}
