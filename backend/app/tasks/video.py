# app/tasks/video.py
import os
from app.tasks.celery_app import celery
from app.db.session import SessionLocal
from app.services import video_service
from app.enums.job_status import JobStatus
from app.repositories.video_repo import VideoRepository
from app.repositories.job_repo import JobRepository
from app.log import logger
from app.enums.overlay_kind import OverlayKind
from app.schemas.overlay import OverlayParams


@celery.task(bind=True, name="app.tasks.video.process_upload")
def process_upload_task(self, filepath: str, filename: str, job_id: str):
    db = SessionLocal()
    v_repo = VideoRepository(db)
    j_repo = JobRepository(db)

    try:
        # Extract metadata
        size = os.path.getsize(filepath)

        # Create video record
        video = v_repo.create(filename=filename, filepath=filepath, size=size)
        db.commit()

        # Update job as SUCCESS and link video
        j_repo.update_status(
            job_id=job_id,
            status=JobStatus.SUCCESS.value,
            meta={"filepath": filepath, "video_id": video.id},
        )
        db.commit()

    except Exception as e:
        logger.error(f"Error processing upload task: {e}", exc_info=True)
        j_repo.update_status(
            job_id=job_id,
            status=JobStatus.FAILED.value,
            meta={"error": str(e)},
        )
        db.commit()
    finally:
        db.close()


@celery.task(bind=True, name="app.tasks.video.trim_video")
def trim_video_task(self, video_id: int, start: float, end: float, job_id: str):
    db = SessionLocal()
    v_repo = VideoRepository(db)
    j_repo = JobRepository(db)

    try:
        # 1. Fetch original video
        video = v_repo.get_video(video_id)
        if not video:
            raise ValueError(f"Video {video_id} not found")

        # 2. Define trimmed file path
        base, ext = os.path.splitext(video.filepath)
        trimmed_filepath = f"{base}_trimmed{ext}"
        logger.info(f"Trimming video {video.filepath} from {start} to {end}, saving to {trimmed_filepath}")
        # 3. Trim video using ffmpeg
        video_service.trim_video_ffmpeg(
            input_path=video.filepath,
            output_path=trimmed_filepath,
            start=start,
            end=end
        )

        # 4. Get size and duration
        size, duration = video_service.get_video_metadata(trimmed_filepath)

        # 5. Create new Video record
        trimmed_video = v_repo.create(
            filename=f"{video.filename}_trimmed",
            filepath=trimmed_filepath,
            size=size,
            duration=duration,
            trimmed_from_id=video.id
        )
        db.commit()

        # 6. Update job status SUCCESS
        j_repo.update_status(
            job_id=job_id,
            status=JobStatus.SUCCESS.value,
            meta={"trimmed_video_id": trimmed_video.id, "filepath": trimmed_filepath}
        )
        db.commit()
        logger.info(f"Trim job {job_id} completed successfully.")
    except Exception as e:
        logger.error(f"Error trimming video: {e}", exc_info=True)
        j_repo.update_status(
            job_id=job_id,
            status=JobStatus.FAILED.value,
            meta={"error": str(e)}
        )
        db.commit()
    finally:
        db.close()


@celery.task(bind=True, name="app.tasks.video.overlay_video")
def overlay_video_task(self, video_id: int, overlay_asset_path: str,overlay_kind:OverlayKind ,overlays_params: OverlayParams, job_id: str):
    db = SessionLocal()
    v_repo = VideoRepository(db)
    j_repo = JobRepository(db)

    try:
        video = v_repo.get_video(video_id)
        if not video:
            raise ValueError(f"Video {video_id} not found")

        base, ext = os.path.splitext(video.filepath)
        output_path = f"{base}_overlayed{ext}"

        video_service.apply_overlays(
            overlay_kind,
            overlays_params,
            video.filepath,
            overlay_asset_path,
        )

        j_repo.update_status(
            job_id=job_id,
            status=JobStatus.SUCCESS.value,
            meta={"filepath": output_path}
        )
        db.commit()

    except Exception as e:
        logger.error(f"Error applying overlays: {e}", exc_info=True)
        j_repo.update_status(
            job_id=job_id,
            status=JobStatus.FAILED.value,
            meta={"error": str(e)}
        )
        db.commit()
    finally:
        db.close()


@celery.task(bind=True, name="app.tasks.video.generate_versions")
def generate_versions_task(self, video_id: int, job_id: str):
    db = SessionLocal()
    v_repo = VideoRepository(db)
    j_repo = JobRepository(db)
    logger.info(f"Starting version generation task for video_id: {video_id}, job_id: {job_id}")
    try:
        video = v_repo.get_video(video_id)
        if not video:
            raise ValueError(f"Video {video_id} not found")

        base_dir = os.path.dirname(video.filepath)
        output_dir = os.path.join(base_dir, "versions")

        versions = video_service.generate_multi_quality_videos(video.filepath, output_dir)

        for v in versions:
            v_repo.create_video_version(
                video_id=video.id,
                quality=v["quality"],
                filepath=v["filepath"],
                size=v["size"]
            )
        db.commit()

        j_repo.update_status(
            job_id=job_id,
            status=JobStatus.SUCCESS.value,
            meta={"versions": [v["quality"] for v in versions]}
        )
        db.commit()
        logger.info(f"Version generation job {job_id} completed successfully.")
    except Exception as e:
        logger.error(f"Error generating video versions: {e}", exc_info=True)
        j_repo.update_status(
            job_id=job_id,
            status=JobStatus.FAILED.value,
            meta={"error": str(e)}
        )
        db.commit()
    finally:
        db.close()

@celery.task(bind=True, name="app.tasks.video.add_watermark")
def add_watermark_task(self, video_id: int, watermark_path: str,job_id: str):
    db = SessionLocal()
    v_repo = VideoRepository(db)
    j_repo = JobRepository(db)

    try:
        # 1. Fetch original video
        video = v_repo.get_video(video_id)
        if not video:
            raise ValueError(f"Video {video_id} not found")

        # 2. Define trimmed file path
        input_path = video.filepath
        logger.info(f"Adding watermark to video {input_path}, ")
        # 3. Trim video using ffmpeg
        video_service.add_image_watermark(
            input_path,
            watermark_path
        )

        # # 4. Get size and duration
        # size, duration = video_service.get_video_metadata(trimmed_filepath)

        # # 5. Create new Video record
        # trimmed_video = v_repo.create(
        #     filename=f"{video.filename}_trimmed",
        #     filepath=trimmed_filepath,
        #     size=size,
        #     duration=duration,
        #     trimmed_from_id=video.id
        # )
        # db.commit()

        # 6. Update job status SUCCESS
        j_repo.update_status(
            job_id=job_id,
            status=JobStatus.SUCCESS.value,
            meta={"video_id": video_id, "filepath": input_path}
        )
        db.commit()
        logger.info(f"Trim job {job_id} completed successfully.")
    except Exception as e:
        logger.error(f"Error trimming video: {e}", exc_info=True)
        j_repo.update_status(
            job_id=job_id,
            status=JobStatus.FAILED.value,
            meta={"error": str(e)}
        )
        db.commit()
    finally:
        db.close()
