import logging
import os

def setup_logger(name="automation_logger"):
    """
    Requirement: Logging & Evidence Collection.
    Configures a centralized logger that outputs to both the console and a persistent log file.
    """
    # Ensure the directory for log artifacts exists
    os.makedirs("outputs/logs", exist_ok=True)
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Singleton-like check: Prevent log duplication if the setup is invoked multiple times 
    # within the same execution context.
    if not logger.handlers:
        # Define a consistent format for timestamps and log levels
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

        # Console Handler: Provides real-time feedback during local test execution
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File Handler: Stores execution history for post-run analysis and CI/CD artifacts
        file_handler = logging.FileHandler("outputs/logs/test_run.log")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger