from enum import Enum

class TaskType(str, Enum):
    UPLOAD = "UPLOAD"
    TRIM = "TRIM"
    TRANSCODE = "TRANSCODE" # Task to change video format or resolution
    OVERLAY = "OVERLAY"
    WATERMARK = "WATERMARK"
