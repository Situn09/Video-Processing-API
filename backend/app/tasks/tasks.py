import uuid
import os
from app.tasks.celery_app import celery
from app.services.ffmpeg_utils import trim_video, add_watermark, transcode_quality, add_text_overlay
from app.core.config import settings
from pathlib import Path

@celery.task(bind=True)
def trim_task(self, video_path, start, end, out_name=None):
    job_id = self.request.id
    try:
        if out_name is None:
            out_name = f"{Path(video_path).stem}_trim_{start}_{end}.mp4"
        out_path = os.path.join(settings.STORAGE_PATH, out_name)
        trim_video(video_path, out_path, start, end)
        return {"status": "SUCCESS", "result": out_path}
    except Exception as e:
        raise self.retry(exc=e, countdown=5, max_retries=2)

@celery.task(bind=True)
def overlay_task(self, video_path, overlays: list, watermark: dict = None):
    job_id = self.request.id
    # simplistic: apply overlays sequentially producing intermediate files
    cur = video_path
    idx = 0
    try:
        for ov in overlays:
            idx += 1
            kind = ov.get("kind")
            params = ov.get("params", {})
            out = os.path.join(settings.STORAGE_PATH, f"{Path(video_path).stem}_ov{idx}.mp4")
            if kind == "text":
                text = params.get("text")
                font = params.get("font", "/app/fonts/NotoSansDevanagari-Regular.ttf")
                x = params.get("x", "(w-text_w)/2")
                y = params.get("y", "(h-text_h)/2")
                start = params.get("start", 0)
                end = params.get("end", None)
                add_text_overlay(cur, text, font, x, y, start, end, output_path=out)
            elif kind == "image":
                # image overlay: use overlay filter
                pos = params.get("pos", "10:10")
                from app.services.ffmpeg_utils import run_cmd
                cmd = f'ffmpeg -y -i {cur} -i {params["image_path"]} -filter_complex "overlay={pos}" -c:a copy {out}'
                run_cmd(cmd)
            # for video overlays etc. add similarly
            cur = out
        # watermark last
        if watermark:
            out_w = os.path.join(settings.STORAGE_PATH, f"{Path(video_path).stem}_wm.mp4")
            add_watermark(cur, watermark["path"], watermark.get("position", "10:10"), output_path=out_w)
            cur = out_w
        return {"status": "SUCCESS", "result": cur}
    except Exception as e:
        raise self.retry(exc=e, countdown=5, max_retries=2)

@celery.task(bind=True)
def transcode_multi_task(self, video_path, out_basename):
    outputs = {}
    mapping = {
        "1080p": ("1920x1080", "6M"),
        "720p": ("1280x720", "3M"),
        "480p": ("854x480", "1M"),
    }
    for quality, (res, br) in mapping.items():
        out = os.path.join(settings.STORAGE_PATH, f"{out_basename}_{quality}.mp4")
        transcode_quality(video_path, out, res, bitrate=br)
        outputs[quality] = out
    return {"status": "SUCCESS", "result": outputs}
