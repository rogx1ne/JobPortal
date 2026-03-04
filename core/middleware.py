from __future__ import annotations

import uuid

from django.http import HttpRequest, HttpResponse

from .request_id import set_request_id


class RequestIdMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        request.request_id = request_id
        set_request_id(request_id)

        response = self.get_response(request)
        response.headers["X-Request-ID"] = request_id
        return response
