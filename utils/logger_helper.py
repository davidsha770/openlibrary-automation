import logging
import os

def setup_logger(name="automation_logger"):
    """
    Requirement: Logging & Evidence.
    Configures a logger that outputs to both console and a file.
    """
    # Create logs directory if it doesn't exist
    os.makedirs("outputs/logs", exist_ok=True)
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Prevent duplicate logs if setup is called multiple times
    if not logger.handlers:
        # Create formatters
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

        # Console Handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File Handler
        file_handler = logging.FileHandler("outputs/logs/test_run.log")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger