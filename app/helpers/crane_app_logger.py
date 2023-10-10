import logging
import orjson

class GoogleCloudStructuredLogging(logging.Formatter):
    def format(self, record):
        log_entry = {
            "severity": record.levelname,
            "message": super().format(record),
        }

        return orjson.dumps(log_entry).decode("utf-8")


logger = logging.getLogger()
logger_handler = logging.StreamHandler()
logger.handlers = []
logger.addHandler(logger_handler)
logger_handler.setFormatter(
    GoogleCloudStructuredLogging(
        f"%(asctime)s %(levelname)s\t%(message)s [%(name)s:%(filename)s:%(lineno)d]",
        datefmt="%I:%M:%S%p",
    )
)
