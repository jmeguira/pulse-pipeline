import os
import random
import subprocess

from moviepy import VideoFileClip, vfx, afx
from types.run_config import RunConfig


def transform_clip(clip: VideoFileClip = None) -> VideoFileClip:
    """
    Applies minimally runtime-intensive clip transformations
    """
    speed_factor = 1 + random.uniform(0.025, 0.05)
    tint_factor = 1 + random.uniform(-0.05, 0.1)

    effects = [vfx.MultiplySpeed(factor=speed_factor), vfx.MultiplyColor(factor=tint_factor)]

    try:
        if clip.audio and clip.audio.nchannels == 2:
            pan_factor = random.uniform(-0.1, 0.1)
            effects.append(afx.MultiplyStereoVolume(left=1 - pan_factor, right=1 + pan_factor))
    except Exception:
        pass

    return clip.with_effects(effects)


def normalize_clip_audio(run_config: RunConfig, path: str = None):
    base, ext = os.path.splitext(path)
    tmp = base + ".tmp" + ext

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        path,
        "-af",
        f"loudnorm=I={run_config.target_lufs}:TP=-2:LRA=11",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        tmp,
    ]

    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.replace(tmp, path)
