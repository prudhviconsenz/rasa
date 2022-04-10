import logging
from logging import Formatter, StreamHandler, getLogger


def getlog():
    fmt = Formatter(
        fmt="[{module}:{lineno}:{levelname}]:{message} (time={asctime} {processName})",
        datefmt="%b-%d %H:%M",
        style="{",
    )
    log = getLogger()
    stream = StreamHandler()
    stream.setFormatter(fmt)
    log.handlers.clear()
    log.addHandler(stream)
    log.setLevel(logging.INFO)
    log.info(f"logging started from {__file__}")

    return log


log = getlog()
