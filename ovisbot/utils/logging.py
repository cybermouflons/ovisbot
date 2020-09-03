import logging.config
import os

file_path = os.path.dirname(os.path.abspath(__file__))

logging.config.fileConfig(
    os.path.join(file_path, "..", "..", "logging.ini"), disable_existing_loggers=False
)
