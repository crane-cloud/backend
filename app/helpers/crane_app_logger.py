# app_logger.py
import logging
import orjson
from flask import request

def configure_logger(app):
    LOG_LEVEL = app.config.get('LOG_LEVEL', logging.INFO)

    logger = logging.getLogger()
    logger_handler = logging.StreamHandler()
    logger.handlers = []
    logger.addHandler(logger_handler)

    class GoogleCloudStructuredLogging(logging.Formatter):
        def format(self, record):
            log_entry = {
                "severity": record.levelname,
                "message": super().format(record),
                "requestid": request.headers.get("x-request-id", ""),
                "traceid": request.headers.get("x-b3-traceid", ""),
            }
            return orjson.dumps(log_entry).decode("utf-8")

    logger_handler.setFormatter(
        GoogleCloudStructuredLogging(
            f"%(asctime)s %(levelname)s\t%(message)s [%(name)s:%(filename)s:%(lineno)d]",
            datefmt="%I:%M:%S%p",
        )
    )
    logger.setLevel(LOG_LEVEL)

    requests_logger = logging.getLogger("requests.packages.urllib3.connectionpool")
    requests_logger.setLevel(logging.WARNING)
