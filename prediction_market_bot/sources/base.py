"""Shared HTTP helper used by all source adapters."""

import requests

from .. import config


class SourceError(RuntimeError):
    """Raised when a platform's API returns something we can't parse."""


def get_json(url, params=None, headers=None, timeout=None):
    all_headers = {"User-Agent": config.USER_AGENT}
    if headers:
        all_headers.update(headers)
    resp = requests.get(url, params=params, headers=all_headers, timeout=timeout or config.REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def to_float(value):
    """Best-effort float conversion; returns None for missing/unparseable values."""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
