import subprocess
from pathlib import Path
from app.core.config import settings
import shlex

def run_cmd(cmd):
    print("FFMPEG CMD:", cmd)
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Command failed: {res.stderr}\n{res.stdout}")
    return res.stdout

def trim_video(input_path: str, output_path: str, start: float, end: float):
    duration = end - start
    # -ss before -i is fast seek, -t controls duration
    cmd = f'ffmpeg -y -ss {start} -i {shlex.quote(input_path)} -t {duration} -c:v libx264 -c:a aac {shlex.quote(output_path)}'
    run_cmd(cmd)
    return output_path

def add_watermark(input_path: str, watermark_path: str, position="10:10", output_path=None):
    if output_path is None:
        output_path = str(Path(input_path).with_name(Path(input_path).stem + "_wm.mp4"))
    # overlay at top-left with padding x:y handled by overlay filter (use overlay=X:Y)
    # position is "x:y"
    cmd = f'ffmpeg -y -i {shlex.quote(input_path)} -i {shlex.quote(watermark_path)} -filter_complex "overlay={position}" -c:a copy {shlex.quote(output_path)}'
    run_cmd(cmd)
    return output_path

def add_text_overlay(input_path: str, text: str, fontfile: str, x="(w-text_w)/2", y="(h-text_h)/2", start=0, end=None, fontsize=48, output_path=None):
    if output_path is None:
        output_path = str(Path(input_path).with_name(Path(input_path).stem + "_text.mp4"))
    drawtext = f"drawtext=fontfile={fontfile}:text='{text}':x={x}:y={y}:fontsize={fontsize}:enable='between(t,{start},{end if end is not None else 99999})'"
    cmd = f'ffmpeg -y -i {shlex.quote(input_path)} -vf "{drawtext}" -c:a copy {shlex.quote(output_path)}'
    run_cmd(cmd)
    return output_path

def transcode_quality(input_path: str, output_path: str, resolution: str, bitrate: str = None):
    # resolution examples: 1920x1080, 1280x720, 854x480
    br = f"-b:v {bitrate}" if bitrate else ""
    cmd = f'ffmpeg -y -i {shlex.quote(input_path)} -vf scale={resolution} -c:v libx264 {br} -preset veryfast -c:a aac -b:a 128k {shlex.quote(output_path)}'
    run_cmd(cmd)
    return output_path
