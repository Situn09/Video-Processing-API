import logging
import os

# Create a logger
logger = logging.getLogger("video_processing_api")
logger.setLevel(logging.DEBUG)

# Ensure logs directory exists
os.makedirs("./logs", exist_ok=True)

# File Handler (for storing logs)
file_handler = logging.FileHandler("./logs/app.log")
file_handler.setLevel(logging.DEBUG)


formatter = logging.Formatter(
    "[%(asctime)s] [%(levelname)s] %(name)s (%(filename)s:%(lineno)d) - %(message)s"
)
file_handler.setFormatter(formatter)

# Add handlers
logger.addHandler(file_handler)

# Test log message
logger.info("Application started.")
