"""Domain lifecycle: init a work tree, freeze it into an immutable version, revise from a stage, lessons."""
from __future__ import annotations

import hashlib
import shutil

from forge.schemas import reading_targets, safe_id, signatures
from forge.util import SIDECARS, Layout, append_jsonl, now, read_json, read_jsonl, remove_with_sidecars, sha256_file, write_json

# Pipeline stages in order; revising from a stage removes its outputs and everything after it.
STAGES = {
    "brief": ["brief.md", "queries.json"],
    "corpus": ["papers.jsonl"],
    "triage": ["triage.json"],
    "readings": ["readings"],
    "cards": ["clusters.suggested.json", "cards"],
    "profile": ["profile"],
    "stats": ["antipatterns.json"],
}
FROZEN_SKIP = {"corpus", "previous", "readings"}  # readings are copied selectively (targets only)
DEFAULT_READ_LIMIT = 25


def init(layout: Layout, topic, read_limit=DEFAULT_READ_LIMIT):
    if not isinstance(topic, str) or not topic.strip():
        raise ValueError("A non-empty --topic is required")
    if type(read_limit) is not int or not 1 <= read_limit <= 200:
        raise ValueError("--read-limit must be 1..200")
    marker = layout.file("topic.txt")
    if marker.exists():
        if marker.read_text(encoding="utf-8").strip() != topic.strip():
            raise ValueError("This domain already has a different topic; use a new domain slug or revise --from-stage brief")
        return {"domain": layout.domain, "work": str(layout.work), "created": False}
    layout.work.mkdir(parents=True, exist_ok=True)
    marker.write_text(topic.strip() + "\n", encoding="utf-8")
    write_json(layout.file("settings.json"), {"read_limit": read_limit})
    return {"domain": layout.domain, "work": str(layout.work), "created": True, "read_limit": read_limit}


def counts(layout):
    targets = reading_targets(layout)
    index = read_json(layout.cards_dir / "index.json") or {"cards": []}
    return {"papers": len(read_jsonl(layout.file("papers.jsonl"))), "reading_targets": len(targets),
            "signatures": len(signatures(layout, targets)), "cards": len(index["cards"]),
            "labels": len(read_jsonl(layout.file("labels.jsonl")))}


def freeze(layout: Layout):
    from forge.navigator import next_domain  # Freeze only what the navigator considers complete.
    step = next_domain(layout)
    if step["step"] != "freeze":
        raise ValueError(f"Domain is not ready to freeze; next step is {step['step']}")
    version = (max(layout.versions()) if layout.versions() else 0) + 1
    target = layout.version_dir(version)
    sources = []
    for path in sorted(layout.work.rglob("*")):
        rel = path.relative_to(layout.work)
        if path.is_dir() or rel.parts[0] in FROZEN_SKIP or rel.name.endswith(SIDECARS) or rel.name == "FROZEN_AS":
            continue
        sources.append((path, rel))
    for aid in reading_targets(layout):  # Only validated target readings become citable.
        path = layout.readings_dir / f"{safe_id(aid)}.json"
        sources.append((path, path.relative_to(layout.work)))
    files = {}
    for path, rel in sources:
        destination = target / rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
        files[str(rel)] = sha256_file(destination)
    manifest = {"domain": layout.domain, "version": version, "frozen_at": now(),
                "topic": layout.file("topic.txt").read_text(encoding="utf-8").strip(),
                "revision": read_json(layout.file("REVISION.json")), "counts": counts(layout),
                "lessons_absorbed": len(read_jsonl(layout.lessons)),
                "labels": "present" if layout.file("labels.jsonl").exists() else "no_outcome_labels",
                "files": files}
    write_json(target / "manifest.json", manifest)
    (layout.root / "CURRENT").write_text(f"v{version}\n")
    layout.file("FROZEN_AS").write_text(f"v{version}\n")
    return {"domain": layout.domain, "version": version, "path": str(target), "files": len(files)}


def verify_version(layout: Layout, version):
    """Files of a frozen version whose bytes no longer match its manifest (or that vanished)."""
    vdir = layout.version_dir(version)
    manifest = read_json(vdir / "manifest.json") or {}
    broken = []
    for rel, digest in (manifest.get("files") or {}).items():
        path = vdir / rel
        if not path.is_file() or sha256_file(path) != digest:
            broken.append(rel)
    return broken if manifest else ["manifest.json"]


def revise(layout: Layout, from_stage, reason):
    if from_stage not in STAGES:
        raise ValueError(f"--from-stage must be one of {list(STAGES)}")
    if not reason or not reason.strip():
        raise ValueError("A --reason is required; it is stored with the next version")
    current = layout.current_version()
    if current is None:
        raise ValueError("Nothing frozen yet; keep building the work tree instead")
    previous = layout.work / "previous"
    if previous.exists():
        shutil.rmtree(previous)
    source = layout.version_dir(current)
    previous.mkdir(parents=True)
    for name in ("triage.json", "cards", "profile"):  # The next build sees what it is revising.
        if (source / name).is_dir():
            shutil.copytree(source / name, previous / name)
        elif (source / name).exists():
            shutil.copy2(source / name, previous / name)
    removed, started = [], False
    for stage, names in STAGES.items():
        started = started or stage == from_stage
        if not started:
            continue
        for name in names:
            path = layout.file(name)
            if path.exists():
                removed.append(name)
            remove_with_sidecars(path)  # a stale acceptance stamp must not outlive its output
    layout.file("FROZEN_AS").unlink(missing_ok=True)
    write_json(layout.file("REVISION.json"), {"from_version": current, "from_stage": from_stage,
                                              "reason": reason.strip(), "at": now(),
                                              "refresh_corpus": from_stage in {"brief", "corpus"}})
    return {"domain": layout.domain, "from_version": current, "from_stage": from_stage, "removed": removed}


def add_lesson(layout: Layout, text, source, refs, version=None, key=None):
    """Append a lesson once. Every lesson has a key, so cards can cite it as `lesson:<key>`."""
    if not text or not source:
        raise ValueError("A lesson needs text and source")
    key = key or "L" + hashlib.sha256(f"{source}\0{' '.join(text.split())}".encode()).hexdigest()[:10]
    if any(row.get("key") == key for row in read_jsonl(layout.lessons)):
        return {"key": key, "duplicate": True}
    row = {"at": now(), "text": text.strip(), "source": source, "refs": refs or [],
           "domain_version": version if version is not None else layout.current_version(), "key": key}
    append_jsonl(layout.lessons, row)
    return row


def lessons_since_freeze(layout: Layout):
    """Lessons the current version did not absorb (by count at freeze, not by clock)."""
    current = layout.current_version()
    rows = read_jsonl(layout.lessons)
    if current is None:
        return rows
    absorbed = (read_json(layout.version_dir(current) / "manifest.json") or {}).get("lessons_absorbed", 0)
    return rows[absorbed:]
