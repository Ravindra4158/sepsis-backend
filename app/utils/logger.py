import sys
from loguru import logger
from app.config.settings import settings
logger.remove()
logger.add(sys.stdout, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level:<8}</level> | <cyan>{name}</cyan> - <level>{message}</level>", level="DEBUG" if settings.DEBUG else "INFO", colorize=True)
