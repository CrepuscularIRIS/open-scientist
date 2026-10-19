"""Shared helpers: project layout, JSON I/O, hashing. Standard library only."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")
SIDECARS = (".tmp", ".inputs", ".accepted")  # bookkeeping files, never content


def now():
    return datetime.now(timezone.utc).isoformat()


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


class BadJSON(ValueError):
    """A file an agent wrote is not valid JSON; the step that wrote it must repair it."""


def read_json(path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise BadJSON(f"{path.name}: invalid JSON ({exc})") from exc


def fingerprint(paths):
    """Content hash over files (directories expanded), for deterministic outputs' staleness."""
    h = hashlib.sha256()
    for root in paths:
        root = Path(root)
        files = sorted(p for p in root.rglob("*") if p.is_file()) if root.is_dir() else ([root] if root.exists() else [])
        for f in files:
            if f.name.endswith(SIDECARS):
                continue
            h.update(str(f.relative_to(root.parent)).encode() + b"\0" + sha256_file(f).encode() + b"\n")
    return h.hexdigest()


def stamp(output, inputs):
    Path(str(output) + ".inputs").write_text(fingerprint(inputs) + "\n")


def fresh(output, inputs):
    marker = Path(str(output) + ".inputs")
    return Path(output).exists() and marker.exists() and marker.read_text().strip() == fingerprint(inputs)


def dep_key(path):
    """A dep's identity: its path from the project's `.forge/` down, so moving the project keeps stamps valid."""
    parts = Path(path).resolve().parts
    return "/".join(parts[parts.index(".forge"):]) if ".forge" in parts else str(Path(path).resolve())


def _dep_hashes(deps):
    return {dep_key(d): fingerprint([d]) for d in deps}


def read_stamp(output):
    stamp_path = Path(str(output) + ".accepted")
    try:
        data = json.loads(stamp_path.read_text(encoding="utf-8")) if stamp_path.exists() else None
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


def accept(output, deps, **record):
    """Stamp an agent-written output as accepted against the content of what it was built from."""
    output = Path(output)
    write_json(Path(str(output) + ".accepted"),
               {"output_sha256": sha256_file(output), "deps": _dep_hashes(deps), "at": now(), **record})


def acceptance(output, deps):
    """State of an agent-written output and the deps that changed:

    'missing'; 'unaccepted' (never stamped); 'stale' (a dep changed since the stamp; checked first, so editing a
    stale output does not hide it); 'edited' (the output changed after it was accepted); 'ok'.
    """
    output = Path(output)
    if not output.exists():
        return "missing", []
    stamp_data = read_stamp(output)
    if stamp_data is None:
        return "unaccepted", []
    recorded = stamp_data.get("deps") or {}
    changed = [d for d, h in _dep_hashes(deps).items() if recorded.get(d) != h]
    if changed:
        return "stale", changed
    return ("edited", []) if stamp_data.get("output_sha256") != sha256_file(output) else ("ok", [])


def restamp_refusal(output, deps):
    """Why an output may not be (re-)accepted now, or None: an unchanged output never re-accepts against changed deps."""
    stamp_data = read_stamp(output)
    if stamp_data and stamp_data.get("output_sha256") == sha256_file(output) and \
            (stamp_data.get("deps") or {}) != _dep_hashes(deps):
        return (f"{Path(output).name} is unchanged since it was accepted, but what it was built from changed; "
                "rerun the step and write it again")
    return None


def tolerant(fn):
    """A validator never crashes on malformed agent output; it says what is malformed."""
    import functools

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except (AttributeError, TypeError, KeyError, IndexError, ValueError) as exc:
            if isinstance(exc, BadJSON):
                return [str(exc)]
            return [f"{fn.__name__.removeprefix('validate_')}: malformed structure ({type(exc).__name__}: {exc}); "
                    "follow the contract's shapes"]
    return wrapper


def move_with_sidecars(source, target):
    """Move a file or directory and its bookkeeping sidecars together."""
    import shutil
    source, target = Path(source), Path(target)
    shutil.move(str(source), str(target))
    for suffix in SIDECARS[1:]:
        side = Path(str(source) + suffix)
        if side.exists():
            shutil.move(str(side), str(target) + suffix)


def remove_with_sidecars(path):
    import shutil
    path = Path(path)
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()
    for suffix in SIDECARS[1:]:
        Path(str(path) + suffix).unlink(missing_ok=True)


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def read_jsonl(path):
    path = Path(path)
    if not path.exists():
        return []
    rows = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            try:
                rows.append(json.loads(line))
            except ValueError as exc:
                raise BadJSON(f"{path.name}:{number}: invalid JSON ({exc})") from exc
    return rows


def append_jsonl(path, row):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(encoded(row) + "\n")


class Layout:
    """Where a project's Forge state lives: <project>/.forge/domains/<slug>/{work,v<N>,lessons.jsonl}."""

    def __init__(self, project, domain):
        if not SLUG.fullmatch(domain or ""):
            raise ValueError("Domain slug must be lowercase letters, digits and hyphens (max 63)")
        self.project = Path(project).expanduser().resolve()
        self.domain = domain
        self.root = self.project / ".forge" / "domains" / domain
        self.work = self.root / "work"
        self.lessons = self.root / "lessons.jsonl"

    def version_dir(self, version):
        return self.root / f"v{version}"

    def current_version(self):
        marker = self.root / "CURRENT"
        if not marker.exists():
            return None
        text = marker.read_text().strip()
        return int(text[1:]) if re.fullmatch(r"v\d+", text) else None

    def versions(self):
        found = []
        for child in self.root.glob("v*"):
            if child.is_dir() and re.fullmatch(r"v\d+", child.name) and (child / "manifest.json").exists():
                found.append(int(child.name[1:]))
        return sorted(found)

    # Work-tree files the domain pipeline produces, in pipeline order.
    def file(self, name):
        return self.work / name

    @property
    def readings_dir(self):
        return self.work / "readings"

    @property
    def cards_dir(self):
        return self.work / "cards"

    @property
    def profile_dir(self):
        return self.work / "profile"
