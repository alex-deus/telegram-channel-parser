import logging

__all__ = ["get_logger", "KwargsFormatter"]

_RESERVED_KEYS = {"exc_info", "stack_info", "stacklevel", "extra"}


class KwargsFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        if not hasattr(record, "prefix"):
            record.prefix = ""

        if not hasattr(record, "message_id"):
            record.message_id = "\t"

        return super().format(record)


class KwargsLoggerAdapter(logging.LoggerAdapter):
    def log(self, level: int, msg: str, *args, **kwargs) -> None:
        extra = kwargs.pop("extra", {})

        user_kwargs = {k: v for k, v in kwargs.items() if k not in _RESERVED_KEYS}
        extra.update(user_kwargs)

        reserved_kwargs = {k: v for k, v in kwargs.items() if k in _RESERVED_KEYS}

        super().log(level, msg, *args, extra=extra, **reserved_kwargs)

    def process(self, msg: str, kwargs: dict) -> tuple:
        kwargs.setdefault("extra", {}).update(self.extra)
        return msg, kwargs


def get_logger(name: str, prefix: str = "", message_id: int | None = None) -> KwargsLoggerAdapter:
    logger = logging.getLogger(name)
    instance = KwargsLoggerAdapter(logger, {"prefix": prefix, "message_id": message_id or "\t"})

    return instance
