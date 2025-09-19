
# from pathlib import Path

# import subprocess
# from app.tasks.celery_app import celery
# from app.db.session import async_session
# from app.services import video_service
# from app.core.config import settings
# from app.enums.task_type import TaskType
# from app.enums.job_status import JobStatus
# from app.repositories.video_repo import VideoRepository
# from app.repositories.job_repo import JobRepository
# import asyncio, os
# from app.log import logger


# @celery.task(bind=True, name="app.tasks.video.process_upload")
# def process_upload_task(self, filepath: str, filename: str, job_id: str):
#     """
#     Process uploaded video asynchronously.
#     """
#     async def run():
#         async with async_session() as db:
#             v_repo = VideoRepository(db)
#             j_repo = JobRepository(db)

#             try:
#                 # Extract metadata
#                 size = os.path.getsize(filepath)

#                 # Create video record
#                 video = await v_repo.create(filename=filename, filepath=filepath, size=size)

#                 # Update job as SUCCESS and link video
#                 await j_repo.update_status(
#                     job_id=job_id,
#                     status=JobStatus.SUCCESS.value,
#                     meta={"filepath": filepath, "video_id": video.id},
#                 )

#             except Exception as e:
#                 # Update job as FAILED
#                 logger.error(f"Error processing upload task: {e}", exc_info=True)
#                 await j_repo.update_status(
#                     job_id=job_id,
#                     status=JobStatus.FAILED.value,
#                     meta={"error": str(e)},
#                 )

#     asyncio.run(run())

# @celery.task(bind=True, name="app.tasks.video.trim_video")
# def trim_video_task(self, video_id: int, start: float, end: float, job_id: str):
#     """
#     Trim a video asynchronously using ffmpeg.
#     Creates a new Video record linked to the original video.
#     Updates the job status.
#     """

#     async def run():
#         async with async_session() as db:
#             v_repo = VideoRepository(db)
#             j_repo = JobRepository(db)

#             try:
#                 # 1. Fetch original video
#                 video = await v_repo.get_video(video_id)
#                 if not video:
#                     raise ValueError(f"Video {video_id} not found")

#                 # 2. Define trimmed file path
#                 base, ext = os.path.splitext(video.filepath)
#                 trimmed_filepath = f"{base}_trimmed{ext}"

#                 # 3. Use video_service to trim using ffmpeg
#                 await video_service.trim_video_ffmpeg(
#                     input_path=video.filepath,
#                     output_path=trimmed_filepath,
#                     start=start,
#                     end=end
#                 )

#                 # 4. Get size and duration of trimmed video
#                 size, duration = video_service.get_video_metadata(trimmed_filepath)

#                 # 5. Create new Video record linked to original
#                 trimmed_video = await v_repo.create(
#                     filename=f"{video.filename}_trimmed",
#                     filepath=trimmed_filepath,
#                     size=size,
#                     duration=duration,
#                     trim_of_id=video.id  # link to original
#                 )

#                 # 6. Update job status SUCCESS
#                 await j_repo.update_status(
#                     job_id=job_id,
#                     status=JobStatus.SUCCESS.value,
#                     meta={
#                         "trimmed_video_id": trimmed_video.id,
#                         "filepath": trimmed_filepath
#                     }
#                 )

#             except Exception as e:
#                 # Update job status FAILED
#                 await j_repo.update_status(
#                     job_id=job_id,
#                     status=JobStatus.FAILED.value,
#                     meta={"error": str(e)}
#                 )

#     asyncio.run(run())

# @celery.task(bind=True, name="app.tasks.video.overlay_video")
# def overlay_video_task(self, video_id: int, overlays: list, watermark: dict | None, job_id: str):
#     """
#     Add overlays and watermark asynchronously using FFmpeg.
#     Updates the job status in DB.
#     """

#     async def run():
#         async with async_session() as db:
#             v_repo = VideoRepository(db)
#             j_repo = JobRepository(db)

#             try:
#                 # 1. Fetch original video
#                 video = await v_repo.get_video(video_id)
#                 if not video:
#                     raise ValueError(f"Video {video_id} not found")

#                 # 2. Prepare output file path
#                 base, ext = os.path.splitext(video.filepath)
#                 output_path = f"{base}_overlayed{ext}"

#                 # 3. Use video_service to apply overlays + watermark
#                 await video_service.apply_overlays_and_watermark(
#                     input_path=video.filepath,
#                     output_path=output_path,
#                     overlays=overlays,
#                     watermark=watermark
#                 )

#                 # 4. Update job status SUCCESS
#                 await j_repo.update_status(
#                     job_id=job_id,
#                     status=JobStatus.SUCCESS.value,
#                     meta={"filepath": output_path}
#                 )

#             except Exception as e:
#                 # 5. Update job status FAILED
#                 await j_repo.update_status(
#                     job_id=job_id,
#                     status=JobStatus.FAILED.value,
#                     meta={"error": str(e)}
#                 )

#     asyncio.run(run())


# @celery.task(bind=True, name="app.tasks.video.generate_versions")
# def generate_versions_task(self, video_id: int, job_id: str):
#     """
#     Generate multiple video versions asynchronously.
#     """
#     async def run():
#         async with async_session() as db:
#             v_repo = VideoRepository(db)
#             j_repo = JobRepository(db)

#             try:
#                 video = await v_repo.get_video(video_id)
#                 if not video:
#                     raise ValueError(f"Video {video_id} not found")

#                 # Output directory for versions
#                 base_dir = os.path.dirname(video.filepath)
#                 output_dir = os.path.join(base_dir, "versions")

#                 # Generate multiple resolutions
#                 versions = await video_service.generate_multi_quality_videos(video.filepath, output_dir)

#                 # Save versions in DB
#                 for v in versions:
#                     await v_repo.create_video_version(
#                         video_id=video.id,
#                         quality=v["quality"],
#                         filepath=v["filepath"],
#                         size=v["size"]
#                     )

#                 # Update job as SUCCESS
#                 await j_repo.update_status(
#                     job_id=job_id,
#                     status=JobStatus.SUCCESS.value,
#                     meta={"versions": [v["quality"] for v in versions]}
#                 )

#             except Exception as e:
#                 await j_repo.update_status(
#                     job_id=job_id,
#                     status=JobStatus.FAILED.value,
#                     meta={"error": str(e)}
#                 )

#     asyncio.run(run())



# app/tasks/video.py

from pathlib import Path
import subprocess
import os
import uuid

from app.tasks.celery_app import celery
from app.db.session import SessionLocal
from app.services import video_service
from app.enums.task_type import TaskType
from app.enums.job_status import JobStatus
from app.repositories.video_repo import VideoRepository
from app.repositories.job_repo import JobRepository
from app.log import logger


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
def overlay_video_task(self, video_id: int, overlays: list, watermark: dict | None, job_id: str):
    db = SessionLocal()
    v_repo = VideoRepository(db)
    j_repo = JobRepository(db)

    try:
        video = v_repo.get_video(video_id)
        if not video:
            raise ValueError(f"Video {video_id} not found")

        base, ext = os.path.splitext(video.filepath)
        output_path = f"{base}_overlayed{ext}"

        video_service.apply_overlays_and_watermark(
            input_path=video.filepath,
            output_path=output_path,
            overlays=overlays,
            watermark=watermark
        )

        j_repo.update_status(
            job_id=job_id,
            status=JobStatus.SUCCESS.value,
            meta={"filepath": output_path}
        )
        db.commit()

    except Exception as e:
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
