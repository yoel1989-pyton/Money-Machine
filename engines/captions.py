"""
DYNAMIC CAPTIONS ENGINE - Word-Level Kinetic Captions
Generates ASS subtitle format with keyword emphasis.
"""

import os
import re
import httpx
from pathlib import Path
from typing import List, Dict, Optional

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

CAPTION_STYLE = {
    "font": "Montserrat", "font_size": 68, "font_bold": True,
    "primary_color": "&H00FFFFFF", "outline_color": "&H00000000",
    "back_color": "&H80000000", "outline": 3, "shadow": 2, "margin_v": 180, "alignment": 2,
}

EMPHASIS_KEYWORDS = {
    "money": {"color": "&H0000D7FF", "scale": 115}, "wealth": {"color": "&H0000D7FF", "scale": 115},
    "rich": {"color": "&H0000D7FF", "scale": 118}, "million": {"color": "&H0000D7FF", "scale": 120},
    "debt": {"color": "&H000000FF", "scale": 115}, "broke": {"color": "&H000000FF", "scale": 118},
    "success": {"color": "&H0000FF00", "scale": 118}, "invest": {"color": "&H0000FF00", "scale": 115},
    "secret": {"color": "&H00FFFF00", "scale": 120}, "never": {"color": "&H00FFFF00", "scale": 118},
}


def format_ass_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def get_word_style(word: str) -> Dict:
    word_lower = word.lower().strip(".,!?\"'")
    return EMPHASIS_KEYWORDS.get(word_lower, {"color": None, "scale": 100})


def generate_ass_captions(words: List[Dict], output_path: str, style: Dict = None) -> str:
    style = {**CAPTION_STYLE, **(style or {})}
    header = f"""[Script Info]
Title: Money Machine Captions
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{style['font']},{style['font_size']},{style['primary_color']},{style['primary_color']},{style['outline_color']},{style['back_color']},{1 if style['font_bold'] else 0},0,0,0,100,100,0,0,1,{style['outline']},{style['shadow']},{style['alignment']},50,50,{style['margin_v']},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    for w in words:
        word = w["word"]
        start, end = format_ass_time(w["start"]), format_ass_time(w["end"])
        ws = get_word_style(word)
        text = word
        if ws["scale"] != 100:
            text = f"{{\\fscx{ws['scale']}\\fscy{ws['scale']}}}{text}{{\\fscx100\\fscy100}}"
        if ws["color"]:
            text = f"{{\\c{ws['color']}}}{text}{{\\c{style['primary_color']}}}"
        text = f"{{\\fad(50,50)}}{text}"
        events.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}")
    Path(output_path).write_text(header + "\n".join(events), encoding="utf-8")
    return output_path


def generate_phrase_captions(words: List[Dict], output_path: str, words_per_phrase: int = 4) -> str:
    style = CAPTION_STYLE
    header = f"""[Script Info]
Title: Money Machine Phrase Captions
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{style['font']},{style['font_size']},{style['primary_color']},{style['primary_color']},{style['outline_color']},{style['back_color']},1,0,0,0,100,100,0,0,1,{style['outline']},{style['shadow']},{style['alignment']},50,50,{style['margin_v']},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    for i in range(0, len(words), words_per_phrase):
        phrase_words = words[i:i + words_per_phrase]
        if not phrase_words: continue
        for j, current_word in enumerate(phrase_words):
            phrase_parts = []
            for k, pw in enumerate(phrase_words):
                word_text = pw["word"]
                ws = get_word_style(word_text)
                if k == j:
                    if ws["scale"] != 100:
                        word_text = f"{{\\fscx{ws['scale']}\\fscy{ws['scale']}}}{word_text}{{\\fscx100\\fscy100}}"
                    if ws["color"]:
                        word_text = f"{{\\c{ws['color']}}}{word_text}{{\\c{style['primary_color']}}}"
                    else:
                        word_text = f"{{\\b1}}{word_text}{{\\b0}}"
                else:
                    word_text = f"{{\\alpha&H80&}}{word_text}{{\\alpha&H00&}}"
                phrase_parts.append(word_text)
            text = f"{{\\fad(30,30)}}" + " ".join(phrase_parts)
            events.append(f"Dialogue: 0,{format_ass_time(current_word['start'])},{format_ass_time(current_word['end'])},Default,,0,0,0,,{text}")
    Path(output_path).write_text(header + "\n".join(events), encoding="utf-8")
    return output_path


async def transcribe_with_whisper(audio_path: str) -> List[Dict]:
    if not OPENAI_API_KEY: return []
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            with open(audio_path, "rb") as f:
                response = await client.post("https://api.openai.com/v1/audio/transcriptions",
                    headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                    files={"file": (Path(audio_path).name, f, "audio/mpeg")},
                    data={"model": "whisper-1", "response_format": "verbose_json", "timestamp_granularity": "word"})
            if response.status_code == 200:
                return [{"word": w["word"], "start": w["start"], "end": w["end"]} for w in response.json().get("words", [])]
    except: pass
    return []


def estimate_word_timestamps(script: str, duration: float) -> List[Dict]:
    words = re.findall(r'\S+', script)
    if not words: return []
    word_duration = duration / len(words)
    return [{"word": word, "start": i * word_duration, "end": (i + 1) * word_duration - 0.05} for i, word in enumerate(words)]
