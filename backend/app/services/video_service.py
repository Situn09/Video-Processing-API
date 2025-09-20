# app/services/video_service.py
import json
import subprocess
import os
from typing import Dict, List, Tuple

from fastapi import HTTPException
from fastapi.responses import FileResponse
from app.log import logger
from app.db.session import SessionLocal
from app.db.models.video import  VideoVersion
from app.schemas.overlay import  OverlayParams, validate_overlay
from app.enums.overlay_kind import OverlayKind
from app.services.ffmpeg_utils import add_image_overlay, add_text_overlay, add_video_overlay

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

def get_video_aspect(video_path):
    """Return aspect ratio (width/height) of video using ffprobe"""
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "json",
        video_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    info = json.loads(result.stdout)
    width = info["streams"][0]["width"]
    height = info["streams"][0]["height"]
    return width / height



def add_image_watermark(video_path:str, watermark_path:str, position="top-right"):
    """
    Add a PNG watermark to a video with dynamic scaling and positioning.

    position: "top-left", "top-right", "bottom-left", "bottom-right"
    scale_ratio: proportion of video width (0.3 = 30%, 0.5 = 50%)
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video not found: {video_path}")
    if not os.path.exists(watermark_path):
        raise FileNotFoundError(f"Watermark not found: {watermark_path}")
    try:
        # Decide scale ratio dynamically
        logger.info(f"Calculating aspect ratio for {video_path}")
        aspect_ratio = get_video_aspect(video_path)
        if aspect_ratio >= 1:  # Landscape (width >= height)
            scale_ratio = 0.4
        else:  # Portrait / reel format
            scale_ratio = 0.6

        pos_map = {
            "top-left": "10:10",
            "top-right": "main_w-overlay_w-10:10",
            "bottom-left": "10:main_h-overlay_h-10",
            "bottom-right": "main_w-overlay_w-10:main_h-overlay_h-10"
        }

        if position not in pos_map:
            raise ValueError(f"Invalid position '{position}', choose from {list(pos_map.keys())}")

        temp_output = os.path.splitext(video_path)[0] + "_watermarked.mp4"
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", watermark_path,
            "-filter_complex",
            "[1:v]scale=-1:-1[wm_orig];"
            f"[wm_orig][0:v]scale2ref=w='min(iw,main_w*{scale_ratio})':h='min(ih,main_h*{scale_ratio})'[wm][base];"
            f"[base][wm]overlay={pos_map[position]}",
            "-c:a", "copy",
            temp_output
        ]

        subprocess.run(ffmpeg_cmd, check=True)
        os.replace(temp_output, video_path)  # Overwrite original
        print(f"✅ Watermarked video saved to {video_path}")
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ FFmpeg error: {e.stderr}",exc_info=True)
        raise
    except Exception as e:
        logger.error(f"❌ Error adding watermark: {e}",exc_info=True)
        raise


def apply_overlays(kind: OverlayKind, overlay_params: OverlayParams, input_video_path: str, overlay_asset_path: str):
    """
    Validate -> save OverlayConfig row -> schedule background ffmpeg processing (or run sync)
    """

    try:
        if kind == OverlayKind.TEXT:
            add_text_overlay(str(input_video_path), 
                                text=overlay_params.text or "Sample Text",
                                position=overlay_params.position,
                                start=overlay_params.start_time,
                                end=overlay_params.end_time,
                                )
        elif kind == OverlayKind.IMAGE:
            add_image_overlay(str(input_video_path), str(overlay_asset_path),
                                position=overlay_params.position,
                                start=overlay_params.start_time,
                                end=overlay_params.end_time)
        elif kind == OverlayKind.VIDEO:
            add_video_overlay(str(input_video_path), str(overlay_asset_path),
                                position=overlay_params.position,
                                start=overlay_params.start_time,
                                end=overlay_params.end_time,)
        # here you may want to create a VideoVersion entry that points to this output_path
        # or do something like move it to final storage / create DB row
        # e.g., create VideoVersion(...) and save
    except Exception as exc:
        # TODO: update overlay row with error or logging
        logger.error(f"Overlay job failed:{exc}", exc_info=True)