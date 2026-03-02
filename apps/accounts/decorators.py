from __future__ import annotations

from functools import wraps

from django.core.exceptions import PermissionDenied
from django.shortcuts import resolve_url
from django.contrib.auth.views import redirect_to_login

from .models import Role


def _role_required(required_role: str):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(
                    request.get_full_path(), login_url=resolve_url("accounts:login")
                )
            if request.user.role != required_role:
                raise PermissionDenied
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator


def employer_required(view_func):
    return _role_required(Role.EMPLOYER)(view_func)


def job_seeker_required(view_func):
    return _role_required(Role.JOB_SEEKER)(view_func)
