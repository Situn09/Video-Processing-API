import os
from pathlib import Path
from app.core.config import settings
from app.log import logger

Path(settings.STORAGE_PATH).mkdir(parents=True, exist_ok=True)

def save_upload(file_bytes: bytes, filename: str) -> str:
    logger.info(f"Saving file to storage {settings.STORAGE_PATH}: {filename}")
    path = str((Path(settings.STORAGE_PATH) / filename).resolve())  # Path object
    logger.info(f"Saving file to {path}, size={len(file_bytes)} bytes")
    try:
        with open(path, "wb") as f:
            f.write(file_bytes)
        logger.info("File saved successfully.")
    except Exception as e:
        logger.error(f"Failed to save file: {e}",exc_info=True)
        raise
    return path

# async def save_upload(file_bytes: bytes, filename: str) -> str:
#     logger.info(f"Saving file to storage {settings.STORAGE_PATH}: {filename}")
#     path = os.path.join(settings.STORAGE_PATH, filename)
#     logger.info(f"Saving file to {path}, size={len(file_bytes)} bytes")
#     try:
#         async with aiofiles.open(path, "wb") as f:
#             await f.write(file_bytes)
#         logger.info("File saved successfully.")
#     except Exception as e:
#         logger.error(f"Failed to save file: {e}")
#         raise
#     return path
