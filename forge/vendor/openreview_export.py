"""Project exports of OpenReview outcomes and proposed cross-source identity links.

An export is the topic-relevant subset plus the full venue denominators it was
drawn from, read from one completed pass per venue, so contrastive labeling
compares like with like. Links are candidates only: no status, score or review
ever moves onto an arXiv record.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import unicodedata

from forge.vendor.openreview_labels import encoded, now, score

LINK_METHOD = "title-exact-v1"
SCORE_FIELDS = ("soundness", "presentation", "contribution")
NOTICE = ("Visible OpenReview submissions only; counts are not a population acceptance rate. "
          "A decision labels one submission event, not empirical success or mechanism quality.")


def normalized_title(title):
    text = unicodedata.normalize("NFKC", title if isinstance(title, str) else "").lower()
    return " ".join(re.sub(r"[^\w]+", " ", text).split())


def _note(labels, note_id, sha):
    row = labels.db.execute("SELECT * FROM notes WHERE note_id=? AND sha256=?", (note_id, sha)).fetchone()
    return row, json.loads(row["content_json"])


def _texts(content, skip=()):
    return {k: v for k, v in content.items() if k not in skip and isinstance(v, str)}


def _row(labels, obs, cfg, review_text):
    request = labels.db.execute("SELECT * FROM requests WHERE request_id=?", (obs["request_id"],)).fetchone()
    thread = json.loads(obs["thread_json"])
    head, content = _note(labels, *thread[0])
    numeric = {cfg["review_rating"]: "rating", cfg["review_confidence"]: "confidence", **{f: f for f in SCORE_FIELDS}}
    reviews, meta, comments = [], None, {"official_comment": 0, "public_comment": 0, "rebuttal": 0}
    for note_id, sha in thread[1:]:
        row, body = _note(labels, note_id, sha)
        if row["role"] == "review":
            review = {"note_id": note_id, "signer": row["signer"], "cdate": row["cdate"],
                      **{name: score(body.get(field)) for field, name in numeric.items()}}
            reviews.append(review | ({"text": _texts(body, numeric)} if review_text else {}))
        elif row["role"] == "meta_review" and meta is None:
            meta = {"note_id": note_id} | ({"text": _texts(body)} if review_text else {})
        elif row["role"] in comments:
            comments[row["role"]] += 1
    keywords = content.get("keywords")
    return {"venue_id": obs["venue_id"], "number": obs["number"], "submission_id": obs["submission_id"],
            "title": content.get("title"), "abstract": content.get("abstract"),
            "keywords": keywords if isinstance(keywords, list) else [], "primary_area": content.get("primary_area"),
            "status": obs["status"], "tier": obs["tier"], "conflict": bool(obs["conflict"]),
            "status_reason": obs["reason"], "raw_venueid": obs["raw_venueid"], "raw_decision": obs["raw_decision"],
            "decision_note_id": obs["decision_note_id"], "normalizer_version": obs["normalizer_version"],
            "reviews": reviews, "meta_review": meta, "comment_counts": comments,
            "source_dates": {"openreview_cdate": head["cdate"], "openreview_mdate": head["mdate"]},
            "label_kind": "submission_decision", "review_status": "collected",
            "source": {"forum": obs["submission_id"], "pass_id": obs["pass_id"], "snapshot_sha256": thread[0][1],
                       "request_url": request["url"], "raw_path": request["raw_path"],
                       "raw_sha256": request["sha256"], "retrieved_at": obs["observed_at"]}}


def _matches(row, query, primary_area):
    if primary_area and row["primary_area"] != primary_area:
        return False
    if query:
        haystack = " ".join([row["title"] or "", row["abstract"] or "", " ".join(map(str, row["keywords"]))]).lower()
        return all(term in haystack for term in query.lower().split())
    return True


def _count(table, *keys):
    for key in keys[:-1]:
        table = table.setdefault(key, {})
    table[keys[-1]] = table.get(keys[-1], 0) + 1


def _passes(labels, venue, allow_partial):
    tasks = labels.tasks([venue] if venue else None)
    if venue and not tasks:
        raise ValueError(f"No harvest for {venue}")
    chosen = {}
    for task in tasks:
        if task["complete_pass_id"]:
            chosen[task["venue_id"]] = (task["complete_pass_id"], True)
        elif allow_partial:
            chosen[task["venue_id"]] = (task["pass_id"], False)
        else:
            raise ValueError(f"{task['venue_id']} has no completed pass ({task['returned']}/{task['total']} "
                             "submissions); finish the harvest or pass allow_partial")
    return chosen


def _write(target, lines):
    temporary = target.with_name(target.name + ".tmp")
    with temporary.open("w") as f:
        for line in lines:
            f.write(line)
    temporary.replace(target)


def export(labels, path, venue=None, query=None, primary_area=None, review_text=True, allow_partial=False):
    target = Path(path).expanduser().resolve()
    if labels.root / "raw" in target.parents or (target.parent == labels.root and
            (target.name.startswith("labels.sqlite3") or target.name == "harvest.lock")):
        raise ValueError("Export must not overwrite the database, lock or raw responses")
    chosen = _passes(labels, venue, allow_partial)
    target.parent.mkdir(parents=True, exist_ok=True)
    denominators = {"all": {}, "selected": {}, "by_area": {}}
    passes = {v: {"pass_id": p, "complete": done} for v, (p, done) in chosen.items()}
    selected = 0

    def rows():
        nonlocal selected
        for venue_id, (pass_id, _) in chosen.items():
            cfg = labels.config(pass_id)
            for obs in labels.members(pass_id):
                row = _row(labels, obs, cfg, review_text)
                _count(denominators["all"], venue_id, row["status"])
                _count(denominators["by_area"], venue_id, row["primary_area"] or "unknown", row["status"])
                if _matches(row, query, primary_area):
                    _count(denominators["selected"], venue_id, row["status"])
                    selected += 1
                    yield encoded(row) + "\n"

    _write(target, rows())
    manifest = {"collection": labels.report(list(chosen) or None), "passes": passes, "exported_at": now(),
                "filters": {"venue": venue, "query": query, "primary_area": primary_area,
                            "review_text": review_text, "allow_partial": allow_partial},
                "denominators": denominators, "notice": NOTICE}
    manifest_path = target.with_suffix(target.suffix + ".manifest.json")
    _write(manifest_path, [json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"])
    return {"path": str(target), "submissions": selected, "passes": passes}


def link(labels, corpus_export):
    """Propose same_work links by exact normalized title; never confirm or copy labels."""
    titles = {}
    latest = labels.db.execute("""SELECT o.submission_id,o.thread_json FROM observations o
        WHERE o.observed_at=(SELECT MAX(observed_at) FROM observations x WHERE x.submission_id=o.submission_id)""").fetchall()
    for obs in latest:
        _, content = _note(labels, *json.loads(obs["thread_json"])[0])
        key = normalized_title(content.get("title"))
        if key and obs["submission_id"] not in titles.setdefault(key, []):
            titles[key].append(obs["submission_id"])
    proposed = 0
    with labels.db:
        for line in Path(corpus_export).expanduser().read_text().splitlines():
            if not line.strip():
                continue
            paper = json.loads(line)
            key = normalized_title(paper.get("title"))
            for submission_id in titles.get(key, []) if key and paper.get("arxiv_id") else []:
                cursor = labels.db.execute("INSERT OR IGNORE INTO links VALUES (?,?,?,?,?,?,?)",
                    (f"openreview:{submission_id}", f"arxiv:{paper['arxiv_id']}", "same_work", "proposed",
                     encoded({"normalized_title": key}), LINK_METHOD, now()))
                proposed += cursor.rowcount
    return {"proposed": proposed, "method_version": LINK_METHOD,
            "notice": "Candidate links only; confirm with explicit cross-references before relying on them."}
