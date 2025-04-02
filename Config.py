import os
import logging


class Config:
    logging_level = logging.DEBUG
    logs_dir = "logs"
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__)))
