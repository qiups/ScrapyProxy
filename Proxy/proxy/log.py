# -*- coding: utf-8 -*-


import logging
import logging.config

_LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "%(asctime)s - %(filename)s:%(lineno)s - (%(levelname)s) - %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "simple",
            "stream": "ext://sys.stdout"
        },
        "info_file_handler": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "simple",
            "filename": "info.log",
            "maxBytes": 10485760,
            "backupCount": 20,
            "encoding": "utf-8"
        },
        "error_file_handler": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "ERROR",
            "formatter": "simple",
            "filename": "errors.log",
            "maxBytes": 10485760,
            "backupCount": 20,
            "encoding": "utf-8"
        }
    },
    "loggers": {
        "file_logger": {
            "level": "ERROR",
            "handlers": ["info_file_handler", "error_file_handler"],
            "propagate": 0
        },
        "console_logger": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": 0
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["info_file_handler", "error_file_handler"]
    }
}

logging.config.dictConfig(_LOGGING)
