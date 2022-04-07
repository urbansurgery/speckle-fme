import traceback
from types import TracebackType
from typing import Union
from fmeobjects import FME_WARN, FME_ERROR, FME_INFORM, FMELogFile

logger = FMELogFile()
logger.allowDuplicateMessages(True)


def log(message: str, level: int = FME_INFORM) -> None:
    """Logs to the FME log file with the specified level."""
    prefix: str = "Speckle:~ "
    logger.logMessageString(prefix + str(message), level)


def warn(message: str) -> None:
    """Logs a warning message."""
    log(str(message), FME_WARN)


def error(message: str) -> None:
    """Logs an error message."""
    log(str(message), FME_ERROR)


def trace(tb: Union[TracebackType, None]) -> None:
    """Logs each line of an exceptions traceback as an error."""
    if tb is not None:
        for t in traceback.extract_tb(tb).format():
            error(t)
