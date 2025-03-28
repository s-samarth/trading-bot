import logging

from Config import Config

# Set the logging level and the log file
logging.basicConfig(level=Config.logging_level, filename=f"{Config.logs_dir}/app.log", filemode="w", 
                    encoding="utf-8", format='%(levelname)s (%(asctime)s): %(message)s (Line: %(lineno)d [%(filename)s])', 
                    datefmt='%d/%m/%Y %I:%M:%S %p')

# Import the other modules after setting the logging configuration so that they can use the same configuration

from TelegramBot import App
from TelegramBot import Commands


if __name__ == "__main__":
    logging.debug("Debug message")
    logging.info("Info message")
    logging.warning("Warning message")
    logging.error("Error message")
    logging.critical("Critical message")
    logging.log(logging.DEBUG, "Log message")

    app = App()
    app.run()