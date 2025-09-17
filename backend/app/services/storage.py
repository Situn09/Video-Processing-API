import os
from pathlib import Path
from app.core.config import settings

Path(settings.STORAGE_PATH).mkdir(parents=True, exist_ok=True)

def save_upload(file_bytes: bytes, filename: str) -> str:
    path = os.path.join(settings.STORAGE_PATH, filename)
    with open(path, "wb") as f:
        f.write(file_bytes)
    return path
