"""
RHYTHM ENGINE - Beat Detection & Scene Timing
Analyzes audio to find optimal scene cut points.
"""

import json
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple

try:
    import librosa
    import numpy as np
    HAS_LIBROSA = True
except ImportError:
    HAS_LIBROSA = False


class RhythmEngine:
    def __init__(self):
        self._emphasis_cache: Dict[str, List[float]] = {}
    
    def analyze(self, audio_path: str) -> Dict:
        duration = self._get_duration(audio_path)
        beats = self._detect_beats_librosa(audio_path) if HAS_LIBROSA else self._detect_beats_ffmpeg(audio_path)
        emphasis = self._detect_emphasis_librosa(audio_path) if HAS_LIBROSA else []
        silences = self._detect_silences(audio_path)
        scene_cuts = self._compute_scene_cuts(duration, beats, emphasis, silences)
        return {"duration": duration, "beats": beats, "emphasis": emphasis, "silences": silences, "scene_cuts": scene_cuts}
    
    def _get_duration(self, audio_path: str) -> float:
        try:
            result = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", audio_path], capture_output=True, text=True)
            return float(json.loads(result.stdout)["format"]["duration"])
        except:
            return 60.0
    
    def _detect_beats_librosa(self, audio_path: str) -> List[float]:
        try:
            y, sr = librosa.load(audio_path, sr=22050)
            onset_env = librosa.onset.onset_strength(y=y, sr=sr)
            onset_frames = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr, units='time')
            return onset_frames.tolist()
        except:
            return []
    
    def _detect_emphasis_librosa(self, audio_path: str) -> List[float]:
        try:
            y, sr = librosa.load(audio_path, sr=22050)
            rms = librosa.feature.rms(y=y)[0]
            times = librosa.times_like(rms, sr=sr)
            threshold = np.percentile(rms, 75)
            peaks = [float(t) for i, (t, r) in enumerate(zip(times, rms)) if r > threshold and 0 < i < len(rms) - 1 and rms[i-1] < r > rms[i+1]]
            self._emphasis_cache[audio_path] = peaks
            return peaks
        except:
            return []
    
    def _detect_beats_ffmpeg(self, audio_path: str) -> List[float]:
        return [end for start, end in self._detect_silences(audio_path)]
    
    def _detect_silences(self, audio_path: str) -> List[Tuple[float, float]]:
        try:
            result = subprocess.run(["ffmpeg", "-i", audio_path, "-af", "silencedetect=noise=-30dB:d=0.3", "-f", "null", "-"], capture_output=True, text=True)
            silences = []
            current_start = None
            for line in result.stderr.split('\n'):
                if 'silence_start' in line:
                    try: current_start = float(line.split('silence_start:')[1].strip().split()[0])
                    except: pass
                elif 'silence_end' in line and current_start is not None:
                    try:
                        end = float(line.split('silence_end:')[1].strip().split()[0])
                        silences.append((current_start, end))
                        current_start = None
                    except: pass
            return silences
        except:
            return []
    
    def _compute_scene_cuts(self, duration: float, beats: List[float], emphasis: List[float], silences: List[Tuple]) -> List[float]:
        MIN_SCENE, MAX_SCENE = 1.2, 2.8
        candidates = {0.0}
        candidates.update(beats)
        candidates.update(e - 0.1 for e in emphasis if e > 0.1)
        candidates.update(end for _, end in silences)
        candidates = sorted(candidates)
        cuts = [0.0]
        for c in candidates[1:]:
            gap = c - cuts[-1]
            if gap >= MIN_SCENE:
                if gap <= MAX_SCENE:
                    cuts.append(c)
                elif gap > MAX_SCENE * 1.5:
                    num_splits = int(gap / ((MIN_SCENE + MAX_SCENE) / 2))
                    split_duration = gap / (num_splits + 1)
                    for i in range(1, num_splits + 1):
                        cuts.append(cuts[-1] + split_duration)
                    cuts.append(c)
        if cuts[-1] < duration - 0.5:
            cuts.append(duration)
        return cuts
    
    def get_emphasis_points(self, audio_path: str) -> List[float]:
        return self._emphasis_cache.get(audio_path) or (self._detect_emphasis_librosa(audio_path) if HAS_LIBROSA else [])


def detect_scene_beats(audio_path: str) -> List[float]:
    return RhythmEngine().analyze(audio_path)["scene_cuts"]


def merge_beats_and_keywords(beats: List[float], keywords: List[str], duration: float) -> List[float]:
    return beats
