from loguru import logger
import sys

logger.remove()
logger.add(sys.stdout, level="INFO", backtrace=False, diagnose=False, enqueue=True,
	format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")

__all__ = ["logger"]