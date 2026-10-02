import logging
import sys

def setup_logger(name="rrtrackerito"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Format de log professionnel
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Sortie dans la console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Sortie dans un fichier bot.log (mode 'a' pour ajouter a la suite)
    file_handler = logging.FileHandler("bot.log", encoding="utf-8", mode="a")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

log = setup_logger()
