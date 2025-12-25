from enum import Enum


class LogLevel(str, Enum):
    QUIET = "quiet"
    NORMAL = "normal"
    DEBUG = "debug"
    TRACE = "trace"
