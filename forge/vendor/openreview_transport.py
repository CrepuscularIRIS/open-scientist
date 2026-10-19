"""Authenticated, rate-limited OpenReview API v2 reads. Tokens never leave memory."""
from __future__ import annotations

from contextlib import contextmanager
from email.utils import parsedate_to_datetime
import fcntl
import json
import os
from pathlib import Path
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

API = "https://api2.openreview.net"
MAX_BODY = 128 * 1024 * 1024
MIN_INTERVAL = 7.3  # Authenticated /notes budget observed 2026-10-18: 500 per hour.
USER_AGENT = "OpenScientist-Labels/0.1 (research metadata)"


class RemoteCooldown(ValueError):
    """OpenReview asked for a pause shared across this user's collectors."""


def read_credentials(env_file=None, environ=None):
    values = dict(os.environ if environ is None else environ)
    if env_file:
        for line in Path(env_file).expanduser().read_text().splitlines():
            line = line.strip()
            if line.startswith("export "):
                line = line[len("export "):].lstrip()
            if line and not line.startswith("#") and "=" in line:
                key, raw = line.split("=", 1)
                raw = raw.strip()
                if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
                    raw = raw[1:-1]
                values[key.strip()] = raw
    user, password = values.get("OPENREVIEW_USERNAME"), values.get("OPENREVIEW_PASSWORD")
    if not user or not password:
        raise ValueError("OPENREVIEW_USERNAME and OPENREVIEW_PASSWORD are required (environment or --env-file)")
    return user, password


def cooldown_seconds(error):
    raw = error.headers.get("Retry-After", "") if error.headers else ""
    try:
        seconds = float(raw)
    except ValueError:
        try:
            seconds = parsedate_to_datetime(raw).timestamp() - time.time()
        except (ValueError, TypeError, OverflowError):
            seconds = 300
    return max(MIN_INTERVAL, seconds)


def lock_path():
    base = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache") / "open-scientist"
    base.mkdir(parents=True, exist_ok=True, mode=0o700)
    return base / "openreview-requests.lock"


@contextmanager
def request_slot():
    """Serialize OpenReview requests across this user's processes and label roots."""
    with lock_path().open("a+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        f.seek(0)
        try:
            state = json.loads(f.read().strip() or "{}")
        except ValueError:
            state = {}  # A torn write must not wedge every later harvest.
        state = state if isinstance(state, dict) else {}
        if state.get("cooldown_until", 0) > time.time():
            raise RemoteCooldown(f"OpenReview cooldown active until {state['cooldown_until']}; resume later")
        delay = max(0, state.get("last_finished", 0) + MIN_INTERVAL - time.time())
        if delay:
            time.sleep(delay)
        try:
            yield
        except HTTPError as exc:
            if exc.code == 429 or (exc.headers and exc.headers.get("Retry-After")):
                state["cooldown_until"] = time.time() + cooldown_seconds(exc)
            raise
        finally:
            f.seek(0)
            f.truncate()
            state["last_finished"] = time.time()
            f.write(json.dumps(state))
            f.flush()
            fcntl.flock(f, fcntl.LOCK_UN)


class Transport:
    """API v2 reader that logs in on first use and keeps the token in memory."""

    def __init__(self, username, password, base=API):
        self.base, self._credentials, self._token = base, (username, password), None

    def _send(self, request):
        with request_slot():
            with urlopen(request, timeout=60) as response:
                data = response.read(MAX_BODY + 1)
        if len(data) > MAX_BODY:
            raise ValueError("OpenReview response exceeds size limit")
        return data

    def _login(self):
        user, password = self._credentials
        body = json.dumps({"id": user, "password": password}).encode()
        request = Request(self.base + "/login", data=body, method="POST",
                          headers={"User-Agent": USER_AGENT, "Content-Type": "application/json"})
        token = json.loads(self._send(request)).get("token")
        if not isinstance(token, str) or not token:
            raise ValueError("OpenReview login returned no token")
        self._token = token

    def get(self, url):
        if self._token is None:
            self._login()
        return self._send(Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json",
                                                "Authorization": "Bearer " + self._token}))
