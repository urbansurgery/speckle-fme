from fmeobjects import FME_WARN, FME_ERROR, FME_INFORM, FMELogFile

logger = FMELogFile()


def log(message: str, level: int = FME_INFORM) -> None:
    prefix: str = "Speckle:~ "
    logger.logMessageString(prefix + message, level)


def warn(message: str) -> None:
    log(message, FME_WARN)


def error(message: str) -> None:
    log(message, FME_ERROR)
