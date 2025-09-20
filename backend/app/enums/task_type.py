from enum import Enum

class TaskType(str, Enum):
    UPLOAD = "UPLOAD"
    TRIM = "TRIM"
    TRANSCODE = "TRANSCODE" # Task to change video format or resolution
    TEXT_OVERLAY = "TEXT_OVERLAY"
    IMAGE_OVERLAY = "IMAGE_OVERLAY"
    VIDEO_OVERLAY = "VIDEO_OVERLAY"
    WATERMARK = "WATERMARK"
