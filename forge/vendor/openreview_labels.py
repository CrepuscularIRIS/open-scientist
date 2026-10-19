"""OpenReview submission outcomes and reviews, collected per venue-year on demand.

Standard-library only, API v2 conference venues. A decision labels one
submission event; it is not empirical success or mechanism quality. Raw
responses, note snapshots and normalized observations are kept separately, and
every view reads one pass over a venue so denominators never mix time points.
"""
from __future__ import annotations

from contextlib import suppress
from datetime import datetime, timezone
import fcntl
import hashlib
from http.client import HTTPException
import json
from pathlib import Path
import re
import sqlite3
import sys
from urllib.error import HTTPError
from urllib.parse import urlencode
import uuid

from forge.vendor.openreview_transport import API, RemoteCooldown, Transport, read_credentials

__all__ = ["Labels", "Transport", "RemoteCooldown", "read_credentials", "venue_config",
           "normalize_status", "note_role", "signer_role", "score", "NORMALIZER_VERSION"]

NORMALIZER_VERSION = "openreview-status-v1"
VENUE = re.compile(r"^[A-Za-z0-9._-]+(?:/[A-Za-z0-9._-]+)*$")
REQUIRED = ("submission_id", "submission_venue_id", "rejected_venue_id", "withdrawn_venue_id",
            "desk_rejected_venue_id", "decision_name", "review_name", "meta_review_name")
FIXED_ROLES = {"Submission": "submission", "Official_Comment": "official_comment",
               "Public_Comment": "public_comment", "Withdrawal": "withdrawal",
               "Desk_Rejection": "desk_rejection"}
PRIVATE_FIELDS = {"authorids"}
REFRESH_HINT = "rerun with --refresh to start a new pass"


def now():
    return datetime.now(timezone.utc).isoformat()


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value):
    return hashlib.sha256(value).hexdigest()


def value(field):
    return field.get("value") if isinstance(field, dict) and "value" in field else field


def flat(content):
    return {k: value(v) for k, v in (content or {}).items() if k not in PRIVATE_FIELDS}


def progress(record):
    with suppress(OSError):  # A closed stderr must never undo a committed page.
        print(encoded(record), file=sys.stderr, flush=True)


def venue_config(group_json):
    groups = group_json.get("groups") if isinstance(group_json, dict) else None
    if not isinstance(groups, list) or len(groups) != 1:
        raise ValueError("Venue group not found or ambiguous")
    group = groups[0]
    content = flat(group.get("content"))
    missing = [k for k in REQUIRED if not isinstance(content.get(k), str) or not content[k]]
    if missing:
        raise ValueError(f"Venue {group.get('id')} is not supported by the API v2 conference adapter "
                         f"(group lacks {', '.join(missing)})")
    config = {"venue_id": group["id"], **{k: content[k] for k in REQUIRED}}
    config.update(review_rating=content.get("review_rating") or "rating",
                  review_confidence=content.get("review_confidence") or "confidence",
                  decision_field_name=content.get("decision_field_name") or "decision",
                  rebuttal_name=content.get("rebuttal_name"))
    return config


def normalize_status(cfg, raw_venueid, decision):
    statuses = {cfg["venue_id"]: "accepted", cfg["rejected_venue_id"]: "rejected",
                cfg["withdrawn_venue_id"]: "withdrawn", cfg["desk_rejected_venue_id"]: "desk_rejected",
                cfg["submission_venue_id"]: "pending"}
    raw = raw_venueid if isinstance(raw_venueid, str) else None
    status = statuses.get(raw, "unknown")
    text = decision.lower() if isinstance(decision, str) else ""
    tier = None
    if status == "accepted":
        tier = next((t for t in ("oral", "spotlight", "poster") if t in text), "unknown")
    conflict = bool(text) and ((status == "accepted" and "reject" in text) or
                               (status in {"rejected", "withdrawn"} and "accept" in text) or
                               status == "pending")
    if status == "unknown":
        reason = f"venueid {raw_venueid!r} matches no status in the venue group"
    else:
        reason = "official venueid" + (f"; decision note says {decision!r}" if conflict else "")
    return {"status": status, "tier": tier, "conflict": conflict, "reason": reason,
            "normalizer_version": NORMALIZER_VERSION}


def note_role(cfg, note):
    roles = {**FIXED_ROLES, cfg["review_name"]: "review", cfg["meta_review_name"]: "meta_review",
             cfg["decision_name"]: "decision"}
    if cfg.get("rebuttal_name"):
        roles[cfg["rebuttal_name"]] = "rebuttal"
    for invitation in note.get("invitations") or []:
        role = roles.get(invitation.rsplit("/-/", 1)[-1]) if "/-/" in invitation else None
        if role:
            return role
    return "other"


def signer_role(signature):
    if not isinstance(signature, str) or signature.startswith("~") or "@" in signature:
        return "public_user"  # Real profile IDs are not research data here.
    return signature.rsplit("/", 1)[-1]


def score(raw):
    if isinstance(raw, bool):
        return None
    if isinstance(raw, (int, float)):
        return int(raw) if float(raw).is_integer() else raw
    match = re.match(r"\s*(-?\d+(?:\.\d+)?)", raw) if isinstance(raw, str) else None
    return score(float(match[1])) if match else None


SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS labels_meta(version INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS venue_configs(
 venue_id TEXT NOT NULL, sha256 TEXT NOT NULL, config_json TEXT NOT NULL, raw_path TEXT NOT NULL,
 fetched_at TEXT NOT NULL, PRIMARY KEY(venue_id,sha256));
CREATE TABLE IF NOT EXISTS passes(
 pass_id TEXT PRIMARY KEY, venue_id TEXT NOT NULL, config_sha TEXT, started_at TEXT NOT NULL, completed_at TEXT);
CREATE TABLE IF NOT EXISTS tasks(
 venue_id TEXT PRIMARY KEY, pass_id TEXT NOT NULL REFERENCES passes, next_offset INTEGER NOT NULL DEFAULT 0,
 returned INTEGER NOT NULL DEFAULT 0, total INTEGER, last_id TEXT, last_number INTEGER,
 status TEXT NOT NULL DEFAULT 'pending', error TEXT, complete_pass_id TEXT REFERENCES passes);
CREATE TABLE IF NOT EXISTS requests(
 request_id TEXT PRIMARY KEY, venue_id TEXT NOT NULL, page_offset INTEGER, url TEXT NOT NULL,
 attempted_at TEXT NOT NULL, status TEXT NOT NULL, raw_path TEXT, sha256 TEXT, error TEXT);
CREATE TABLE IF NOT EXISTS notes(
 note_id TEXT NOT NULL, sha256 TEXT NOT NULL, venue_id TEXT NOT NULL, forum TEXT NOT NULL, replyto TEXT,
 role TEXT NOT NULL, signer TEXT NOT NULL, cdate INTEGER, mdate INTEGER, content_json TEXT NOT NULL,
 first_request_id TEXT NOT NULL REFERENCES requests, PRIMARY KEY(note_id,sha256));
CREATE TABLE IF NOT EXISTS observations(
 submission_id TEXT NOT NULL, request_id TEXT NOT NULL REFERENCES requests, venue_id TEXT NOT NULL,
 pass_id TEXT NOT NULL REFERENCES passes, raw_venueid TEXT, decision_note_id TEXT, raw_decision TEXT,
 status TEXT NOT NULL, tier TEXT, conflict INTEGER NOT NULL, reason TEXT NOT NULL,
 normalizer_version TEXT NOT NULL, thread_json TEXT NOT NULL, observed_at TEXT NOT NULL,
 PRIMARY KEY(submission_id,request_id));
CREATE TABLE IF NOT EXISTS pass_members(
 pass_id TEXT NOT NULL REFERENCES passes, submission_id TEXT NOT NULL, request_id TEXT NOT NULL,
 number INTEGER, PRIMARY KEY(pass_id,submission_id),
 FOREIGN KEY(submission_id,request_id) REFERENCES observations(submission_id,request_id));
CREATE TABLE IF NOT EXISTS links(
 left_ref TEXT NOT NULL, right_ref TEXT NOT NULL, relation TEXT NOT NULL, status TEXT NOT NULL,
 evidence_json TEXT NOT NULL, method_version TEXT NOT NULL, created_at TEXT NOT NULL,
 PRIMARY KEY(left_ref,right_ref,relation));
"""


class Labels:
    def __init__(self, root):
        self.root = Path(root).expanduser().resolve()
        (self.root / "raw").mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.root / "labels.sqlite3", timeout=30)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")  # Exports read while a harvest commits pages.
        self.db.execute("PRAGMA synchronous=NORMAL")  # WAL stays consistent; a lost tail page is refetched.
        self.db.executescript(SCHEMA)
        versions = self.db.execute("SELECT version FROM labels_meta").fetchall()
        if not versions:
            self.db.execute("INSERT INTO labels_meta VALUES (1)")
            self.db.commit()
        elif [v[0] for v in versions] != [1]:
            raise ValueError("Unsupported labels schema version")

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.db.close()

    def _save_raw(self, data):
        sha = digest(data)
        raw_path = f"raw/{sha}.json"
        destination = self.root / raw_path
        if not destination.exists():
            temporary = destination.with_suffix(".tmp")
            temporary.write_bytes(data)
            temporary.replace(destination)
        return raw_path, sha

    def _new_pass(self, venue):
        pass_id = uuid.uuid4().hex
        self.db.execute("INSERT INTO passes VALUES (?,?,NULL,?,NULL)", (pass_id, venue, now()))
        return pass_id

    def harvest(self, venues, transport, page_size=100, max_pages=None, refresh=False):
        if not venues or any(not isinstance(v, str) or not VENUE.fullmatch(v) for v in venues):
            raise ValueError("Give one or more OpenReview venue ids, e.g. ICLR.cc/2025/Conference")
        if type(page_size) is not int or not 1 <= page_size <= 1000:
            raise ValueError("page_size must be 1..1000")
        if max_pages is not None and (type(max_pages) is not int or max_pages < 1):
            raise ValueError("max_pages must be a positive integer")
        with (self.root / "harvest.lock").open("a+") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise ValueError("Another collector is writing these labels")
            with self.db:
                self.db.execute("UPDATE requests SET status='interrupted',error='Collector ended before committing; cursor not advanced' WHERE status='running'")
                for venue in dict.fromkeys(venues):
                    exists = self.db.execute("SELECT 1 FROM tasks WHERE venue_id=?", (venue,)).fetchone()
                    if not exists:
                        self.db.execute("INSERT INTO tasks(venue_id,pass_id) VALUES (?,?)", (venue, self._new_pass(venue)))
                    elif refresh:  # New pass; older snapshots, observations and the last complete pass stay.
                        self.db.execute("UPDATE tasks SET pass_id=?,next_offset=0,returned=0,total=NULL,last_id=NULL,"
                                        "last_number=NULL,status='pending',error=NULL WHERE venue_id=?",
                                        (self._new_pass(venue), venue))
            for venue in dict.fromkeys(venues):
                if self._collect(venue, transport, page_size, max_pages):
                    break  # Service cooldown: later venues stay pending.
            return self.report(venues)

    def _request(self, venue, offset, url, transport):
        request_id, attempted = uuid.uuid4().hex, now()
        with self.db:
            self.db.execute("INSERT INTO requests VALUES (?,?,?,?,?,'running',NULL,NULL,NULL)",
                            (request_id, venue, offset, url, attempted))
        data = transport.get(url)
        raw_path, sha = self._save_raw(data)
        with self.db:
            self.db.execute("UPDATE requests SET raw_path=?,sha256=? WHERE request_id=?", (raw_path, sha, request_id))
        return request_id, attempted, raw_path, sha, json.loads(data)

    def config(self, pass_id):
        row = self.db.execute("""SELECT c.config_json FROM passes p JOIN venue_configs c
            ON c.venue_id=p.venue_id AND c.sha256=p.config_sha WHERE p.pass_id=?""", (pass_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def _config(self, venue, pass_id, transport):
        """Each pass reads the venue group once, so one pass never mixes status mappings."""
        cfg = self.config(pass_id)
        if cfg:
            return cfg
        request_id, attempted, raw_path, sha, body = self._request(
            venue, None, f"{API}/groups?" + urlencode({"id": venue}), transport)
        cfg = venue_config(body)
        if cfg["venue_id"] != venue:
            raise ValueError("Group response names a different venue")
        config_json = encoded(cfg)
        config_sha = digest(config_json.encode())
        with self.db:
            self.db.execute("INSERT OR IGNORE INTO venue_configs VALUES (?,?,?,?,?)",
                            (venue, config_sha, config_json, raw_path, attempted))
            self.db.execute("UPDATE passes SET config_sha=? WHERE pass_id=?", (config_sha, pass_id))
            self.db.execute("UPDATE requests SET status='ok' WHERE request_id=?", (request_id,))
        return cfg

    def _collect(self, venue, transport, page_size, max_pages):
        pages = 0
        while True:
            task = self.db.execute("SELECT * FROM tasks WHERE venue_id=?", (venue,)).fetchone()
            if task["status"] == "complete":
                return False
            if max_pages is not None and pages >= max_pages:
                with self.db:
                    self.db.execute("UPDATE tasks SET status='partial',error=NULL WHERE venue_id=?", (venue,))
                return False
            offset, request_id = task["next_offset"], None
            try:
                cfg = self._config(venue, task["pass_id"], transport)
                # Re-read the previous page's last submission to detect shifts that keep the count.
                fetch_from = offset - 1 if offset else 0
                url = f"{API}/notes?" + urlencode({"invitation": cfg["submission_id"], "details": "replies",
                                                    "sort": "number:asc", "limit": page_size + (1 if offset else 0),
                                                    "offset": fetch_from})
                request_id, attempted, _, _, body = self._request(venue, offset, url, transport)
                status = self._store_page(cfg, task, request_id, attempted, body, page_size)
            except (OSError, ValueError, KeyError, TypeError, HTTPException, sqlite3.Error) as exc:
                error = f"{type(exc).__name__}: {exc}"
                if isinstance(exc, HTTPError):
                    retry = exc.headers.get("Retry-After", "unspecified") if exc.headers else "unspecified"
                    try:
                        detail = exc.read()[:300].decode("utf-8", "replace")
                    except Exception:  # The error body is diagnostic only.
                        detail = ""
                    error += f"; Retry-After={retry}; body={detail}"
                with self.db:
                    if request_id is None:
                        self.db.execute("UPDATE requests SET status='error',error=? WHERE venue_id=? AND status='running'", (error, venue))
                    else:
                        self.db.execute("UPDATE requests SET status='error',error=? WHERE request_id=?", (error, request_id))
                    self.db.execute("UPDATE tasks SET status='error',error=? WHERE venue_id=?", (error, venue))
                progress({"venue": venue, "offset": offset, "status": "error", "error": error[:300]})
                return isinstance(exc, RemoteCooldown) or (isinstance(exc, HTTPError) and
                    (exc.code == 429 or bool(exc.headers and exc.headers.get("Retry-After"))))
            pages += 1
            progress({"venue": venue, "offset": offset, "status": status})

    def _check_page(self, cfg, task, body, page_size):
        notes, count, offset = body.get("notes"), body.get("count"), task["next_offset"]
        if not isinstance(notes, list) or type(count) is not int:
            raise ValueError("Response is not a notes listing with a count")
        if count == 0:
            raise ValueError("Venue lists zero submissions; refusing to mark it complete (check access and invitation)")
        if task["total"] is not None and count != task["total"]:
            raise ValueError(f"Submission count changed from {task['total']} to {count}; {REFRESH_HINT}")
        if len(notes) > page_size + (1 if offset else 0):
            raise ValueError("Unexpected page size; cursor unchanged")
        ids = [n.get("id") for n in notes]
        if len(set(ids)) != len(ids):
            raise ValueError("Repeated submission within page; cursor unchanged")
        if offset:
            if not notes or notes[0].get("id") != task["last_id"]:
                raise ValueError(f"Pagination shifted before offset {offset} (expected {task['last_id']}); {REFRESH_HINT}")
            notes = notes[1:]
        if not notes and offset < count:
            raise ValueError("Empty page before count; cursor unchanged")
        previous = task["last_number"]
        for n in notes:
            if n.get("forum") != n.get("id") or cfg["submission_id"] not in (n.get("invitations") or []):
                raise ValueError(f"Unexpected note {n.get('id')!r} in submission listing")
            if self.db.execute("SELECT 1 FROM pass_members WHERE pass_id=? AND submission_id=?",
                               (task["pass_id"], n["id"])).fetchone():
                raise ValueError(f"Repeated submission {n['id']} across pages; pagination drift, {REFRESH_HINT}")
            number = n.get("number")
            if type(number) is not int or (previous is not None and number <= previous):
                raise ValueError(f"Submission numbers not strictly increasing at {n['id']}; {REFRESH_HINT}")
            previous = number
        return notes, count

    def _store_page(self, cfg, task, request_id, attempted, body, page_size):
        notes, count = self._check_page(cfg, task, body, page_size)
        venue, pass_id, done = cfg["venue_id"], task["pass_id"], task["next_offset"] + len(notes)
        status = "complete" if done >= count else "pending"
        with self.db:
            for n in notes:
                thread, decision = [], None
                for note in [n, *((n.get("details") or {}).get("replies") or [])]:
                    role = "submission" if note is n else note_role(cfg, note)
                    content = flat(note.get("content"))
                    snapshot = encoded(content)
                    sha = digest(snapshot.encode())
                    self.db.execute("INSERT OR IGNORE INTO notes VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        (note["id"], sha, venue, note.get("forum") or n["id"], note.get("replyto"), role,
                         signer_role((note.get("signatures") or [None])[0]), note.get("cdate"), note.get("mdate"),
                         snapshot, request_id))
                    thread.append([note["id"], sha])
                    if role == "decision" and decision is None:
                        decision = (note["id"], content.get(cfg["decision_field_name"]))
                raw_venueid = flat(n.get("content")).get("venueid")
                raw_decision = decision[1] if decision and isinstance(decision[1], str) else None
                result = normalize_status(cfg, raw_venueid, raw_decision)
                self.db.execute("INSERT INTO observations VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (n["id"], request_id, venue, pass_id, raw_venueid if isinstance(raw_venueid, str) else encoded(raw_venueid),
                     decision[0] if decision else None, raw_decision, result["status"], result["tier"],
                     int(result["conflict"]), result["reason"], NORMALIZER_VERSION, encoded(thread), attempted))
                self.db.execute("INSERT INTO pass_members VALUES (?,?,?,?)", (pass_id, n["id"], request_id, n["number"]))
            self.db.execute("UPDATE requests SET status='ok' WHERE request_id=?", (request_id,))
            self.db.execute("UPDATE tasks SET next_offset=?,returned=?,total=?,last_id=?,last_number=?,status=?,error=? WHERE venue_id=?",
                            (done, done, count, notes[-1]["id"] if notes else task["last_id"],
                             notes[-1]["number"] if notes else task["last_number"], status, None, venue))
            if status == "complete":
                self.db.execute("UPDATE tasks SET complete_pass_id=pass_id WHERE venue_id=?", (venue,))
                self.db.execute("UPDATE passes SET completed_at=? WHERE pass_id=?", (now(), pass_id))
        return status

    def members(self, pass_id):
        return self.db.execute("""SELECT m.number,o.* FROM pass_members m JOIN observations o
            ON o.submission_id=m.submission_id AND o.request_id=m.request_id
            WHERE m.pass_id=? ORDER BY m.number""", (pass_id,)).fetchall()

    def pass_counts(self, pass_id):
        counts = {}
        for row in self.db.execute("""SELECT o.status,COUNT(*) n FROM pass_members m JOIN observations o
                ON o.submission_id=m.submission_id AND o.request_id=m.request_id WHERE m.pass_id=? GROUP BY o.status""", (pass_id,)):
            counts[row["status"]] = row["n"]
        return counts

    def tasks(self, venues=None):
        return [dict(r) for r in self.db.execute("SELECT * FROM tasks ORDER BY rowid")
                if venues is None or r["venue_id"] in venues]

    def report(self, venues=None):
        tasks = self.tasks(venues)
        shown = [{k: t[k] for k in ("venue_id", "next_offset", "returned", "total", "status", "error")}
                 | {"has_complete_pass": t["complete_pass_id"] is not None} for t in tasks]
        return {"root": str(self.root), "venues": shown,
                "status_counts": {t["venue_id"]: c for t in tasks if (c := self.pass_counts(t["pass_id"]))},
                "collection_ok": bool(tasks) and all(t["status"] == "complete" for t in tasks),
                "normalizer_version": NORMALIZER_VERSION,
                "notice": "Counts cover the current pass of the listed venues; decisions label submission events, "
                          "not empirical success or mechanism quality."}

    def links(self):
        return [{"left_ref": r["left_ref"], "right_ref": r["right_ref"], "relation": r["relation"],
                 "status": r["status"], "method_version": r["method_version"],
                 "evidence": json.loads(r["evidence_json"])}
                for r in self.db.execute("SELECT * FROM links ORDER BY rowid")]
