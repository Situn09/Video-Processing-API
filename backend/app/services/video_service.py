# app/services/video_service.py
import subprocess
import os
from typing import Dict, List, Tuple

from fastapi import HTTPException
from fastapi.responses import FileResponse
from app.log import logger
from app.db.session import SessionLocal
from app.db.models.video import VideoVersion

def trim_video_ffmpeg(input_path: str, output_path: str, start: float, end: float):
    """
    Trim video using ffmpeg and log output.
    """
    cmd = [
        "ffmpeg",  # or full path to ffmpeg.exe
        "-y",
        "-i", input_path,
        "-ss", str(start),
        "-to", str(end),
        "-c", "copy",
        output_path
    ]
    
    logger.info(f"Running ffmpeg command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.info(f"FFmpeg stdout: {result.stdout}")
        if result.stderr:
            logger.warning(f"FFmpeg stderr: {result.stderr}")
        logger.info(f"Video trimmed successfully: {output_path}")
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg failed with return code {e.returncode}")
        logger.error(f"FFmpeg stdout: {e.stdout}")
        logger.error(f"FFmpeg stderr: {e.stderr}")
        raise
    except FileNotFoundError:
        logger.error("FFmpeg executable not found. Make sure ffmpeg is installed and in PATH.")
        raise

def get_video_metadata(filepath: str) -> Tuple[int, float]:
    """
    Return file size in bytes and duration in seconds using ffprobe
    """
    import subprocess, json
    size = os.path.getsize(filepath)

    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json",
        filepath
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)
    duration = float(data["format"]["duration"])
    return size, duration



async def apply_overlays_and_watermark(
    input_path: str,
    output_path: str,
    overlays: List[Dict],
    watermark: Dict | None
):
    """
    Apply text/image/video overlays and optional watermark using FFmpeg.
    """
    # Build filter_complex commands
    filters = []

    for idx, ov in enumerate(overlays):
        kind = ov.get("kind")
        params = ov.get("params", {})
        start = params.get("start", 0)
        end = params.get("end", 10)
        pos = params.get("position", "10:10")

        if kind == "text":
            text = params.get("text", "")
            fontfile = params.get("fontfile", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
            filters.append(
                f"drawtext=text='{text}':x={pos.split(':')[0]}:y={pos.split(':')[1]}:enable='between(t,{start},{end})':fontfile={fontfile}:fontsize=24:fontcolor=white"
            )
        elif kind == "image":
            img_path = params.get("path")
            filters.append(f"overlay={pos}:enable='between(t,{start},{end})':shortest=1")
        elif kind == "video":
            # assuming overlay video input added separately
            overlay_vid = params.get("path")
            filters.append(f"[1:v] overlay={pos}:enable='between(t,{start},{end})'")

    # Add watermark
    if watermark:
        wm_path = watermark.get("filepath")
        wm_pos = watermark.get("position", "10:10")
        filters.append(f"movie={wm_path}[wm];[0:v][wm] overlay={wm_pos}")

    filter_complex = ",".join(filters) if filters else None

    # Build ffmpeg command
    cmd = ["ffmpeg", "-y", "-i", input_path]

    # For overlay videos, add additional inputs
    for ov in overlays:
        if ov.get("kind") == "video":
            cmd.extend(["-i", ov.get("params", {}).get("path")])

    cmd.extend(["-filter_complex", filter_complex] if filter_complex else [])
    cmd.append(output_path)

    # Run FFmpeg asynchronously
    await asyncio.to_thread(subprocess.run, cmd, check=True)

# app/services/video_service.py
import asyncio
import subprocess
import os
from typing import List, Tuple, Dict

RESOLUTIONS = {
    "1080p": "1920x1080",
    "720p": "1280x720",
    "480p": "854x480",
}

def generate_multi_quality_videos(input_path: str, output_dir: str) -> List[Dict]:
    """
    Generate multiple resolutions of the input video using FFmpeg.
    Returns a list of dicts with filepath and resolution.
    """
    os.makedirs(output_dir, exist_ok=True)
    tasks = []

    for quality, res in RESOLUTIONS.items():
        filename = os.path.splitext(os.path.basename(input_path))[0]
        output_path = os.path.join(output_dir, f"{filename}_{quality}.mp4")
        cmd = [
            "ffmpeg",
            "-y",
            "-i", input_path,
            "-vf", f"scale={res}",
            "-c:a", "aac",
            "-c:v", "libx264",
            "-preset", "fast",
            output_path
        ]
        # Run asynchronously in thread
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"FFmpeg stdout: {result.stdout}")
            if result.stderr:
                logger.warning(f"FFmpeg stderr: {result.stderr}")
            logger.info(f"Video trimmed successfully: {output_path}")
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg failed with return code {e.returncode}")
            logger.error(f"FFmpeg stdout: {e.stdout}")
            logger.error(f"FFmpeg stderr: {e.stderr}")
            raise
        except FileNotFoundError:
            logger.error("FFmpeg executable not found. Make sure ffmpeg is installed and in PATH.")
            raise
        # tasks.append(asyncio.to_thread(subprocess.run, cmd, check=True))
    
    # Wait for all tasks
    # await asyncio.gather(*tasks)

    # Collect results
    results = []
    for quality in RESOLUTIONS.keys():
        output_path = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(input_path))[0]}_{quality}.mp4")
        size = os.path.getsize(output_path)
        results.append({"quality": quality, "filepath": output_path, "size": size})
    return results


def get_version_file(video_id: int, quality: str) -> FileResponse:
    """
    Return the requested video version file if it exists.
    """
    db = SessionLocal()
    version = (
        db.query(VideoVersion)
        .filter(VideoVersion.video_id == video_id, VideoVersion.quality == quality)
        .first()
    )

    if not version:
        raise HTTPException(status_code=404, detail="Video version not found")

    return FileResponse(
        path=version.filepath,
        filename=f"{quality}_{video_id}.mp4",
        media_type="video/mp4"
    )