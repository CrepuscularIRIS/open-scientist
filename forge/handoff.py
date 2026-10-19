"""Web handoff packets and receipts, plus provenance records for every LLM step.

A packet is self-contained: the step prompt, the output contract, any FIX
errors and the inlined content of each input (the web cannot read local
paths). A receipt tracks the serial handoff; the reply is ingested locally into
the same files the step would have written, so modes stay comparable.

A handoff belongs to one step of one attempt and audit round
(`handoff/<step>-a<attempt>-r<round>/`) and records the fingerprint of the
run-local files it was built from. A reply to an older candidate is never
ingested for a newer one: when those files change, the packet is superseded and
a new request is prepared; the old one stays as history.
"""
from __future__ import annotations

from pathlib import Path
import uuid

from forge.util import accept, append_jsonl, fingerprint, now, read_json, read_jsonl, restamp_refusal, sha256_file, write_json

FILE_CAP = 60_000
TOTAL_CAP = 600_000
TEXT_SUFFIXES = {".json", ".jsonl", ".md", ".txt"}
RECEIPT_STATUS = {"prepared", "sent", "returned", "interrupted", "cancelled"}


def _base(scope):
    kind, project, name = scope
    root = Path(project).expanduser().resolve() / ".forge"
    return root / {"run": "runs", "study": "studies"}.get(kind, "domains") / name


def provenance_path(project):
    return Path(project).expanduser().resolve() / ".forge" / "provenance.jsonl"


def position(scope):
    """(attempt, audit round) of a run scope; (1, 1) for a domain."""
    if scope[0] == "study":  # one handoff per step per proposal
        root = _base(scope) / "proposals"
        numbers = [int(p.stem) for p in root.glob("[0-9][0-9][0-9].json")] if root.exists() else []
        return (max(numbers) if numbers else 0), 1
    if scope[0] != "run":
        return 1, 1
    base = _base(scope)
    attempts = base / "attempts"
    done = [p for p in attempts.glob("attempt_*") if (p / "audit.json").exists()] if attempts.exists() else []
    return len(done) + 1, 2 if (base / "audit_round1.json").exists() else 1


def handoff_key(scope, step_name):
    attempt, round_ = position(scope)
    return f"{step_name}-a{attempt}-r{round_}"


def handoff_dir(scope, step_name):
    return _base(scope) / "handoff" / handoff_key(scope, step_name)


def response_path(hdir):
    return Path(hdir) / "response.md"


def local_deps(scope, deps):
    """The deps that live in this scope's own directory (the domain version is pinned and hashed separately)."""
    base = _base(scope)
    return [d for d in deps if Path(d).resolve().is_relative_to(base)]


def deps_fingerprint(scope, deps):
    return fingerprint(local_deps(scope, deps))


def _files(path):
    path = Path(path)
    if path.is_file():
        return [path]
    if path.is_dir():
        return sorted(p for p in path.rglob("*") if p.is_file() and p.suffix in TEXT_SUFFIXES and "handoff" not in p.parts)
    return []


def build_packet(step, action, tier):
    contracts = Path(step["prompt"]).parent / "contracts.md" if step.get("prompt") else None
    parts = [f"# Research Forge handoff: {step['step']} ({action}, suggested {tier})", "",
             "You are filling one step of a research pipeline. Everything you need is below; you cannot see any other "
             "files. Answer with the output file(s) the prompt asks for, each in its own fenced block headed by its "
             "file name. Cite only material included here; mark anything else as your recollection to be checked.", ""]
    if step.get("errors"):
        parts += ["## Errors to fix in a previous answer", *[f"- {e}" for e in step["errors"]], ""]
    if step.get("notes"):
        parts += ["## Step notes", *[f"- {n}" for n in step["notes"]], ""]
    parts += ["## Step prompt", Path(step["prompt"]).read_text(encoding="utf-8"), ""]
    if contracts and contracts.exists():
        parts += ["## Output contract", contracts.read_text(encoding="utf-8"), ""]
    parts += ["## Expected output files", *[f"- `{Path(o).name}`" for o in step["outputs"]], "", "## Materials"]
    total, manifest, truncated = 0, [], []
    for path in step["inputs"]:
        for f in _files(path):
            text = f.read_text(encoding="utf-8", errors="replace")
            cut = text[:FILE_CAP]
            if total + len(cut) > TOTAL_CAP:
                truncated.append(str(f))
                continue
            if len(cut) < len(text):
                truncated.append(str(f))
            total += len(cut)
            manifest.append({"path": str(f), "sha256": sha256_file(f), "chars": len(cut), "truncated": len(cut) < len(text)})
            parts += [f"### {f.name}  ({f.parent.name})", "```", cut, "```", ""]
    if truncated:
        parts += ["## Not fully included", *[f"- {t}" for t in truncated], ""]
    return "\n".join(parts), manifest, truncated


def prepare(scope, step, action, tier, supersede=False):
    hdir = handoff_dir(scope, step["step"])
    if (hdir / "receipt.json").exists():
        if not supersede:
            raise ValueError(f"A handoff for {step['step']} already exists at {hdir}; resume it instead of sending twice")
        n = 1
        while hdir.with_name(f"{hdir.name}.superseded-{n}").exists():
            n += 1
        hdir.rename(hdir.with_name(f"{hdir.name}.superseded-{n}"))
    text, manifest, truncated = build_packet(step, action, tier)
    hdir.mkdir(parents=True, exist_ok=True)
    (hdir / "packet.md").write_text(text, encoding="utf-8")
    attempt, round_ = position(scope)
    receipt = {"request_id": uuid.uuid4().hex, "scope": scope[0], "name": scope[2], "step": step["step"],
               "attempt": attempt, "round": round_, "deps": [str(d) for d in local_deps(scope, step.get("deps", []))],
               "deps_fingerprint": deps_fingerprint(scope, step.get("deps", [])),
               "action": action, "requested_route": tier, "observed_route": None, "conversation_url": None,
               "status": "prepared", "prepared_at": now(), "materials": manifest, "truncated": truncated,
               "usage": "unknown"}
    write_json(hdir / "receipt.json", receipt)
    return {"packet": str(hdir / "packet.md"), "chars": len(text), "truncated": len(truncated), "key": hdir.name}


def mark(scope, step_name, status, url=None, observed_route=None):
    if status not in RECEIPT_STATUS:
        raise ValueError(f"status must be one of {sorted(RECEIPT_STATUS)}")
    hdir = handoff_dir(scope, step_name)
    receipt = read_json(hdir / "receipt.json")
    if receipt is None:
        raise ValueError(f"No handoff prepared for {step_name} ({hdir.name})")
    receipt.update(status=status, **({"conversation_url": url} if url else {}),
                   **({"observed_route": observed_route} if observed_route else {}), **{f"{status}_at": now()})
    write_json(hdir / "receipt.json", receipt)
    return receipt


def record_provenance(scope, step_name, executor, mode, outputs, deps=(), failed=False):
    """Append who produced a step's outputs and stamp each output as accepted against its deps.

    `executor` is the route the host was asked to use (self-reported, not authenticated); a web receipt adds the
    route the person observed, when they recorded one. An output that is byte-identical to its accepted version
    is never re-accepted against changed deps: a stale output must be written again. `failed` marks a fill whose
    output still fails validation (it counts toward the repair cap).
    """
    paths = list(map(Path, outputs))
    refusals = [r for p in paths if p.is_file() and (r := restamp_refusal(p, deps))]
    if refusals:
        raise ValueError("; ".join(refusals))
    files = [{"path": str(p), "sha256": sha256_file(p)} for p in paths if p.is_file()]
    missing = [str(p) for p in paths if not p.exists()]
    receipt = read_json(handoff_dir(scope, step_name) / "receipt.json") if executor.startswith("web:") else None
    attempt, round_ = position(scope)
    row = {"at": now(), "scope": scope[0], "name": scope[2], "step": step_name, "attempt": attempt, "round": round_,
           "requested_executor": executor, "observed_route": (receipt or {}).get("observed_route") or "unknown",
           "mode": mode, "outputs": files, "missing_outputs": missing, "failed_validation": bool(failed),
           "handoff": receipt["request_id"] if receipt else None}
    append_jsonl(provenance_path(scope[1]), row)
    for p in paths:
        if p.is_file():
            accept(p, deps, executor=executor, mode=mode)
    if receipt and receipt["status"] != "returned":
        mark(scope, step_name, "returned")
    return row


def step_runs(scope, step_name):
    """How many fills of this step in the current attempt and round still failed validation (from provenance).

    Counted only when the host records provenance; a host that skips run_after gets `accept` steps instead.
    """
    attempt, round_ = position(scope)
    return sum(1 for r in read_jsonl(provenance_path(scope[1]))
               if r.get("scope") == scope[0] and r.get("name") == scope[2] and r.get("step") == step_name
               and r.get("attempt", 1) == attempt and r.get("round", 1) == round_ and r.get("failed_validation"))
