import logging
import sys

def setup_logging(level=logging.INFO, log_to_file=False, filename="app.log"):
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(name)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    logging.basicConfig(
        level=level,
        handlers=[handler]
    )

    if log_to_file:
        file_handler = logging.FileHandler(filename)
        file_handler.setFormatter(formatter)
        logging.getLogger().addHandler(file_handler)
