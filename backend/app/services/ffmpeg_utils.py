# app/services/ffmpeg_utils.py
import shlex
import subprocess
from pathlib import Path
from typing import Optional
import tempfile
import os

def _pos_to_xy(position: str, overlay_w: int = 0, overlay_h: int = 0):
    """
    Convert simple position keywords to x,y expressions for ffmpeg overlay/drawtext.
    overlay_w/h used for offsets when calculating right/bottom.
    """
    pos = position.lower() if position else "bottom-right"
    if ":" in pos:
        # assume "x:y" raw expressions
        x, y = pos.split(":", 1)
        return x, y
    if pos in ("top-left", "tl"):
        return "10", "10"
    if pos in ("top-right", "tr"):
        return f"main_w - {overlay_w} - 10", "10"
    if pos in ("bottom-left", "bl"):
        return "10", f"main_h - {overlay_h} - 10"
    if pos in ("bottom-right", "br"):
        return f"main_w - {overlay_w} - 10", f"main_h - {overlay_h} - 10"
    if pos in ("center", "c"):
        return f"(main_w - {overlay_w})/2", f"(main_h - {overlay_h})/2"
    # default
    return "10", f"main_h - {overlay_h} - 10"

def run_ffmpeg(args: list):
    """
    Run FFmpeg command (list form). Raise CalledProcessError on failure.
    """
    completed = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if completed.returncode != 0:
        raise subprocess.CalledProcessError(
            returncode=completed.returncode,
            cmd=args,
            output=completed.stdout,
            stderr=completed.stderr
        )
    return completed

def add_text_overlay(input_path: str,  text: str,
                     position: str = "bottom-right",
                     start: Optional[float] = 0.0,
                     end: Optional[float] = None):
    """
    Add drawtext overlay between start and end seconds.
    """
    # prepare drawtext options
    # ensure proper escaping of text
    safe_text = text.replace(":", r"\:").replace("'", r"\'")
    x_expr, y_expr = _pos_to_xy(position, overlay_w=0, overlay_h=0)
    enable = f"between(t,{start},{end})" if end is not None else f"gte(t,{start})"

    drawtext_parts = [
        f"text='{safe_text}'",
        # f"fontsize={fontsize}",
        # f"fontcolor={fontcolor}",
        f"x={x_expr}",
        f"y={y_expr}",
        f"enable='{enable}'"
    ]
    drawtext = ",".join([p for p in drawtext_parts if p])
    temp_path = input_path + "_text_overlay_temp.mp4"
    args = [
        "ffmpeg", "-y", "-i", str(input_path),
        "-vf", drawtext,
        "-c:a", "copy",
        str(temp_path)
    ]
    result = run_ffmpeg(args)

    # Replace original file with new file
    os.replace(temp_path, input_path)

    return 

def add_image_overlay(input_path: str, overlay_asset_path: str,
                      position: str = "top-right",
                      start: Optional[float] = 0.0,
                      end: Optional[float] = None,):
    """
    Overlay an image on video for time range [start,end). If end is None, overlay till end.
    Supports optional scaling and opacity.
    """
    enable = f"between(t,{start},{end})" if end is not None else f"gte(t,{start})"

    # Build filter_complex
    #  - load overlay, apply scale (if given) and optionally alpha with colorchannelmixer
    ov_filters = []
    # ensure overlay has alpha channel for opacity manipulation
    # we will use format=rgba and then colorchannelmixer
    ov_filters.append("format=rgba")

    ov_filter_str = ",".join(ov_filters)
    x_expr, y_expr = _pos_to_xy(position, overlay_w=0, overlay_h=0)

    # filter_complex: [1]... [ov]; [0][ov]overlay=...
    filter_complex = f"[1]{ov_filter_str}[ov];[0][ov]overlay=x={x_expr}:y={y_expr}:enable='{enable}'"
    temp_path = input_path + "_text_overlay_temp.mp4"
    args = [
        "ffmpeg", "-y", "-i", str(input_path), "-i", str(overlay_asset_path),
        "-filter_complex", filter_complex,
        "-c:a", "copy",
        str(temp_path)
    ]
    result = run_ffmpeg(args)
    # Replace original file with new file
    os.replace(temp_path, input_path)
    return 

def add_video_overlay(input_path: str, overlay_asset_path: str,
                      position: str = "center",
                      start: Optional[float] = 0.0,
                      end: Optional[float] = None,):
    """
    Overlay a video (overlay_video) on top of input video between start and end.
    overlay_video will loop or be cut depending on shortest settings — we set shortest=1 to stop when overlay ends
    """
    enable = f"between(t,{start},{end})" if end is not None else f"gte(t,{start})"
    ov_filters = []
    ov_filters.append("format=rgba")
    ov_filter_str = ",".join(ov_filters)
    x_expr, y_expr = _pos_to_xy(position, overlay_w=0, overlay_h=0)

    # map inputs: 0 = main video, 1 = overlay video
    # Use setpts to align overlay timing, use enable in overlay filter
    # We will use -stream_loop -1 for overlay looping if shorter than main (optional)
    filter_complex = f"[1]{ov_filter_str}[ov];[0][ov]overlay=x={x_expr}:y={y_expr}:enable='{enable}':shortest=1"
    temp_path = input_path + "_text_overlay_temp.mp4"
    args = [
        "ffmpeg", "-y", "-i", str(input_path), "-i", str(overlay_asset_path),
        "-filter_complex", filter_complex,
        "-c:v", "libx264", "-c:a", "copy",
        str(temp_path)
    ]
    result = run_ffmpeg(args)
    # Replace original file with new file
    os.replace(temp_path, input_path)
    return 
