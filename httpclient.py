"""Small JSON client with a per-host pause, retries, and a short cache.

Public chain APIs rate-limit aggressively. A failed read can still return the
last good body so the picture does not go blank.
"""

from __future__ import annotations

import json
import threading
import time
import urllib.error
import urllib.request
from typing import Any, Callable

USER_AGENT = "Flowlight/1.1 (Hermes plugin; read-only)"


class HttpError(Exception):
    def __init__(self, message: str, status: int = 0):
        super().__init__(message)
        self.status = status


Transport = Callable[[str, str, bytes | None, dict[str, str], float], tuple[int, bytes]]


def urllib_transport(method: str, url: str, body: bytes | None, headers: dict[str, str], timeout: float) -> tuple[int, bytes]:
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return int(response.status), response.read()
    except urllib.error.HTTPError as exc:
        payload = exc.read() if exc.fp is not None else b""
        return int(exc.code), payload
    except urllib.error.URLError as exc:
        raise HttpError(f"network error: {exc.reason}") from exc
    except TimeoutError as exc:
        raise HttpError("timed out") from exc


class HttpClient:
    def __init__(self, transport: Transport | None = None, *, pause: float = 0.15, sleeper: Callable[[float], None] | None = None):
        self._transport = transport or urllib_transport
        self._pause = pause
        self._sleep = sleeper or time.sleep
        self._lock = threading.Lock()
        self._next_ok: dict[str, float] = {}
        self._down_until: dict[str, float] = {}
        self._cache: dict[str, tuple[float, Any]] = {}

    def _host(self, url: str) -> str:
        try:
            return url.split("/", 3)[2].lower()
        except IndexError:
            return url

    def mark_down(self, url: str, seconds: float = 600) -> None:
        with self._lock:
            self._down_until[self._host(url)] = time.monotonic() + seconds

    def is_down(self, url: str) -> bool:
        with self._lock:
            return self._down_until.get(self._host(url), 0) > time.monotonic()

    def _wait(self, host: str) -> None:
        with self._lock:
            delay = self._next_ok.get(host, 0) - time.monotonic()
            self._next_ok[host] = max(self._next_ok.get(host, 0), time.monotonic()) + self._pause
        if delay > 0:
            self._sleep(min(delay, 2))

    def _store(self, key: str, value: Any) -> None:
        with self._lock:
            self._cache[key] = (time.monotonic(), value)

    def _fresh(self, key: str, ttl: float) -> Any | None:
        with self._lock:
            row = self._cache.get(key)
        if not row:
            return None
        stored, value = row
        if time.monotonic() - stored <= ttl:
            return value
        return None

    def _stale(self, key: str) -> Any | None:
        with self._lock:
            row = self._cache.get(key)
        return None if row is None else row[1]

    def request_json(
        self,
        method: str,
        url: str,
        *,
        body: Any = None,
        ttl: float = 0,
        timeout: float = 12,
        accept_status: tuple[int, ...] = (200,),
    ) -> Any:
        key = method + " " + url + " " + (json.dumps(body, sort_keys=True, default=str) if body is not None else "")
        if ttl > 0:
            cached = self._fresh(key, ttl)
            if cached is not None:
                return cached
        if self.is_down(url):
            stale = self._stale(key) if ttl > 0 else None
            if stale is not None:
                return stale
            raise HttpError(f"{self._host(url)} is cooling down after a rate limit or block", status=429)
        raw = json.dumps(body).encode("utf-8") if body is not None else None
        headers = {"Accept": "application/json", "User-Agent": USER_AGENT}
        if raw is not None:
            headers["Content-Type"] = "application/json"
        last_error: Exception | None = None
        for attempt in range(3):
            self._wait(self._host(url))
            try:
                status, payload = self._transport(method, url, raw, headers, timeout)
            except HttpError as exc:
                last_error = exc
                if attempt < 2:
                    self._sleep(0.25 * (attempt + 1))
                    continue
                break
            if status in (429, 503):
                self.mark_down(url, 20 * (attempt + 1))
                last_error = HttpError(f"HTTP {status}", status=status)
                if attempt < 2:
                    self._sleep(0.35 * (attempt + 1))
                    continue
                break
            if status in (401, 403):
                self.mark_down(url, 600)
                last_error = HttpError(f"HTTP {status}", status=status)
                break
            if status not in accept_status:
                last_error = HttpError(f"HTTP {status}", status=status)
                break
            try:
                parsed = json.loads(payload.decode("utf-8") or "null")
            except json.JSONDecodeError as exc:
                last_error = HttpError("response was not JSON")
                last_error.__cause__ = exc
                break
            if ttl > 0:
                self._store(key, parsed)
            return parsed
        stale = self._stale(key) if ttl > 0 else None
        if stale is not None:
            return stale
        if last_error is None:
            last_error = HttpError("request failed")
        raise last_error

    def get_json(self, url: str, **kwargs: Any) -> Any:
        return self.request_json("GET", url, **kwargs)

    def get_json_once(self, url: str, *, timeout: float = 4) -> Any:
        """Single GET with no retry and no host cooldown. Used for 1-Click status."""
        headers = {"Accept": "application/json", "User-Agent": USER_AGENT}
        status, payload = self._transport("GET", url, None, headers, timeout)
        if status != 200:
            raise HttpError(f"HTTP {status}", status=status)
        try:
            return json.loads(payload.decode("utf-8") or "null")
        except json.JSONDecodeError as exc:
            raise HttpError("response was not JSON") from exc

    def post_json(self, url: str, body: Any, **kwargs: Any) -> Any:
        return self.request_json("POST", url, body=body, **kwargs)
