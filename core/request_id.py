from __future__ import annotations

import threading
from logging import Filter, LogRecord


_state = threading.local()


def set_request_id(request_id: str) -> None:
    _state.request_id = request_id


def get_request_id() -> str:
    return getattr(_state, "request_id", "-")


class RequestIdFilter(Filter):
    def filter(self, record: LogRecord) -> bool:
        record.request_id = get_request_id()
        return True

