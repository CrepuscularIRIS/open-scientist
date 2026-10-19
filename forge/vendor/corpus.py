"""Phase 0: bounded arXiv metadata collection, not scientific quality labeling.

Standard-library only. Raw responses, immutable metadata snapshots, query lanes
and resumable page cursors live separately from project research findings.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import date, datetime, timezone
from email.utils import parsedate_to_datetime
import fcntl
import hashlib
from http.client import HTTPException
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
import tempfile
import time
from urllib.error import HTTPError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen
import uuid
import xml.etree.ElementTree as ET

API = "https://export.arxiv.org/api/query"
NS = {"a": "http://www.w3.org/2005/Atom", "x": "http://arxiv.org/schemas/atom",
      "o": "http://a9.com/-/spec/opensearch/1.1/"}
MAX_BODY = 8 * 1024 * 1024
ID = re.compile(r"^(\d{4}\.\d{4,5}|[a-zA-Z-]+(?:\.[A-Za-z]{2})?/\d{7})(?:v([1-9]\d*))?$")


def now():
    return datetime.now(timezone.utc).isoformat()


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value):
    return hashlib.sha256(value).hexdigest()


def arxiv_identity(value):
    if not isinstance(value, str):
        raise ValueError("arXiv identifier must be a string")
    value = value.strip()
    if value.startswith(("https://", "http://")):
        parsed = urlparse(value)
        if parsed.hostname not in {"arxiv.org", "www.arxiv.org", "export.arxiv.org"}:
            raise ValueError("Not an arXiv identifier URL")
        value = re.sub(r"^/(abs|pdf)/", "", parsed.path)
    value = re.sub(r"^arxiv:", "", value, flags=re.I)
    value = re.sub(r"\.pdf$", "", value)
    match = ID.fullmatch(value)
    if not match:
        raise ValueError(f"Invalid arXiv ID: {value[:160]}")
    return match[1], int(match[2]) if match[2] else None


def parse_atom(data):
    if len(data) > MAX_BODY:
        raise ValueError("Atom response exceeds size limit")
    feed = ET.fromstring(data)
    if feed.tag != "{" + NS["a"] + "}feed":
        raise ValueError("Response is not an Atom feed")
    entries = []
    for entry in feed.findall("a:entry", NS):
        def text(key):
            return " ".join(entry.findtext(key, "", NS).split())
        identifier = text("a:id")
        if "api/errors" in identifier or text("a:title").lower() == "error":
            raise ValueError("arXiv error feed: " + text("a:summary"))
        aid, version = arxiv_identity(identifier)
        title, abstract = text("a:title"), text("a:summary")
        published, updated = text("a:published"), text("a:updated")
        if not title or not abstract or not published or not updated:
            raise ValueError(f"Incomplete metadata for {aid}")
        # Validate dates, preserving the original timestamp and arXiv version.
        datetime.fromisoformat(published.replace("Z", "+00:00"))
        datetime.fromisoformat(updated.replace("Z", "+00:00"))
        suffix = aid + (f"v{version}" if version else "")
        primary = entry.find("x:primary_category", NS)
        pdf = next((link.get("href") for link in entry.findall("a:link", NS)
                    if link.get("type") == "application/pdf"), None)
        entries.append({"arxiv_id": aid, "version": version, "title": title,
            "abstract": abstract, "authors": [" ".join(a.findtext("a:name", "", NS).split())
                for a in entry.findall("a:author", NS)],
            "published": published, "updated": updated,
            "categories": sorted({c.get("term") for c in entry.findall("a:category", NS) if c.get("term")}),
            "primary_category": primary.get("term") if primary is not None else None,
            "doi": text("x:doi") or None, "journal_ref": text("x:journal_ref") or None,
            "comment": text("x:comment") or None,
            "abs_url": "https://arxiv.org/abs/" + suffix,
            "pdf_url": pdf, "source_entry_id": identifier})
    def integer(key):
        value = feed.findtext(key, None, NS)
        if value is None or not value.strip().isdigit():
            raise ValueError(f"Missing/invalid feed count: {key}")
        return int(value)
    return {"total": integer("o:totalResults"), "start": integer("o:startIndex"), "entries": entries}


def normalize_config(config):
    allowed = {"name", "start_date", "end_date", "queries", "page_size"}
    if not isinstance(config, dict) or set(config) - allowed:
        raise ValueError("Invalid config fields")
    if not isinstance(config.get("name"), str) or not config["name"].strip():
        raise ValueError("name is required")
    start, end = config.get("start_date"), config.get("end_date")
    if not isinstance(start, str) or not isinstance(end, str):
        raise ValueError("Explicit start_date and end_date required")
    if not all(re.fullmatch(r"\d{4}-\d{2}-\d{2}", d) for d in (start, end)):
        raise ValueError("Dates must use YYYY-MM-DD")
    if date.fromisoformat(start) > date.fromisoformat(end):
        raise ValueError("start_date must not exceed end_date")
    size = config.get("page_size", 25)
    if type(size) is not int or not 1 <= size <= 100:
        raise ValueError("page_size must be 1..100")
    queries = config.get("queries")
    if not isinstance(queries, list) or not 1 <= len(queries) <= 100:
        raise ValueError("queries must contain 1..100 entries")
    ids, normalized = set(), []
    for q in queries:
        if not isinstance(q, dict) or set(q) - {"id", "lane", "domain", "search_query", "ids", "max_results"}:
            raise ValueError("Invalid query fields")
        qid = q.get("id")
        if not isinstance(qid, str) or not re.fullmatch(r"[a-zA-Z0-9_-]{1,80}", qid) or qid in ids:
            raise ValueError("Each query requires a unique safe id")
        ids.add(qid)
        if q.get("lane") not in {"in_domain", "cross_domain"}:
            raise ValueError("lane must be in_domain or cross_domain")
        if not isinstance(q.get("domain"), str) or not q["domain"].strip():
            raise ValueError("query domain is required")
        if ("ids" in q) == ("search_query" in q):
            raise ValueError("Choose exactly one of ids or search_query")
        item = dict(q)
        if "ids" in q:
            if not isinstance(q["ids"], list) or not 1 <= len(q["ids"]) <= 100:
                raise ValueError("ids must have 1..100 explicit arXiv identifiers")
            cleaned = []
            for identifier in q["ids"]:
                aid, version = arxiv_identity(identifier)
                cleaned.append(aid + (f"v{version}" if version else ""))
            item["ids"] = list(dict.fromkeys(cleaned))
        elif not isinstance(q["search_query"], str) or not 1 <= len(q["search_query"].strip()) <= 3000:
            raise ValueError("search_query must be a nonempty arXiv expression")
        cap = q.get("max_results", len(item["ids"]) if "ids" in item else 100)
        if type(cap) is not int or not 1 <= cap <= 1000:
            raise ValueError("max_results must be 1..1000; partition larger corpora")
        if "ids" in item and cap < len(item["ids"]):
            raise ValueError("max_results cannot silently discard requested IDs")
        item["max_results"] = cap
        normalized.append(item)
    return {"name": config["name"], "start_date": start, "end_date": end,
            "page_size": size, "queries": normalized}


class RemoteCooldown(ValueError):
    """The service requested a pause shared across this user's collectors."""


def cooldown_seconds(error):
    value = error.headers.get("Retry-After", "") if error.headers else ""
    try:
        seconds = float(value)
    except ValueError:
        try:
            seconds = parsedate_to_datetime(value).timestamp() - time.time()
        except (ValueError, TypeError, OverflowError):
            seconds = 60
    return max(3.1, seconds)


@contextmanager
def request_slot():
    """Serialize this collector's requests across local processes/corpus roots."""
    lock = Path(tempfile.gettempdir()) / f"open-scientist-arxiv-{os.getuid()}.lock"
    with lock.open("a+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        f.seek(0)
        previous = json.loads(f.read().strip() or "0")
        # Older collector locks stored just the last completion timestamp.
        state = previous if isinstance(previous, dict) else {"last_finished": previous}
        if state.get("cooldown_until", 0) > time.time():
            raise RemoteCooldown(f"arXiv cooldown active until {state['cooldown_until']}; resume later")
        delay = max(0, state.get("last_finished", 0) + 3.1 - time.time())
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
            f.write(encoded(state))
            f.flush()
            fcntl.flock(f, fcntl.LOCK_UN)


def fetch_arxiv(url):
    # No hidden retries: a failed page is visible and retried on explicit resume.
    with request_slot():
        request = Request(url, headers={"User-Agent": "OpenScientist-Corpus/0.1 (metadata research)",
                                       "Accept": "application/atom+xml"})
        with urlopen(request, timeout=30) as response:
            data = response.read(MAX_BODY + 1)
        if len(data) > MAX_BODY:
            raise ValueError("arXiv response exceeds size limit")
        return data


SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS corpus_meta(version INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS runs(
 run_id TEXT PRIMARY KEY, config_hash TEXT NOT NULL, config_json TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS tasks(
 run_id TEXT NOT NULL REFERENCES runs, query_id TEXT NOT NULL, next_start INTEGER NOT NULL DEFAULT 0,
 returned INTEGER NOT NULL DEFAULT 0, total INTEGER, status TEXT NOT NULL DEFAULT 'pending', error TEXT,
 PRIMARY KEY(run_id,query_id));
CREATE TABLE IF NOT EXISTS requests(
 request_id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs, query_id TEXT NOT NULL,
 page_start INTEGER NOT NULL, url TEXT NOT NULL, attempted_at TEXT NOT NULL, status TEXT NOT NULL,
 raw_path TEXT, sha256 TEXT, error TEXT);
CREATE TABLE IF NOT EXISTS papers(arxiv_id TEXT PRIMARY KEY);
CREATE TABLE IF NOT EXISTS snapshots(
 snapshot_id TEXT PRIMARY KEY, arxiv_id TEXT NOT NULL REFERENCES papers, version INTEGER,
 metadata_json TEXT NOT NULL, first_seen TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS memberships(
 run_id TEXT NOT NULL, query_id TEXT NOT NULL, snapshot_id TEXT NOT NULL REFERENCES snapshots,
 rank INTEGER NOT NULL, request_id TEXT NOT NULL REFERENCES requests,
 PRIMARY KEY(run_id,query_id,snapshot_id),
 FOREIGN KEY(run_id,query_id) REFERENCES tasks(run_id,query_id));
"""


class Corpus:
    def __init__(self, root):
        self.root = Path(root).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "raw").mkdir(exist_ok=True)
        self.db = sqlite3.connect(self.root / "corpus.sqlite3", timeout=30)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)
        versions = self.db.execute("SELECT version FROM corpus_meta").fetchall()
        if not versions:
            self.db.execute("INSERT INTO corpus_meta VALUES (1)")
            self.db.commit()
        elif len(versions) != 1 or versions[0][0] != 1:
            raise ValueError("Unsupported corpus schema version")

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.db.close()

    def _run(self, config, refresh):
        raw = encoded(config)
        key = digest(raw.encode())
        old = self.db.execute("SELECT run_id FROM runs WHERE config_hash=? ORDER BY created_at DESC LIMIT 1", (key,)).fetchone()
        if old and not refresh:
            return old[0]
        run_id = uuid.uuid4().hex
        with self.db:
            self.db.execute("INSERT INTO runs VALUES (?,?,?,?)", (run_id, key, raw, now()))
            for q in config["queries"]:
                self.db.execute("INSERT INTO tasks(run_id,query_id) VALUES (?,?)", (run_id, q["id"]))
        return run_id

    def harvest(self, config, refresh=False, fetcher=None):
        config = normalize_config(config)
        fetcher = fetcher or fetch_arxiv
        # One collector writer per corpus. Status/export still work during HTTP waits.
        with (self.root / "harvest.lock").open("a+") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise ValueError("Another collector is writing this corpus")
            run_id = self._run(config, refresh)
            with self.db:
                self.db.execute("UPDATE requests SET status='interrupted',error='Previous collector ended before committing page; cursor not advanced' WHERE run_id=? AND status='running'", (run_id,))
            for q in config["queries"]:
                if self._collect(run_id, config, q, fetcher):
                    break  # Global service cooldown; later queries remain pending.
            return self.report(run_id)

    def _collect(self, run_id, config, q, fetcher):
        while True:
            task = self.db.execute("SELECT * FROM tasks WHERE run_id=? AND query_id=?", (run_id, q["id"])).fetchone()
            if task["status"] in {"complete", "capped", "empty"}:
                return
            start = task["next_start"]
            size = min(config["page_size"], q["max_results"] - start)
            params = {"start": start, "max_results": size}
            if "ids" in q:
                params.update(id_list=",".join(q["ids"]), start=0, max_results=len(q["ids"]))
            else:
                window = f"submittedDate:[{config['start_date'].replace('-', '')}0000 TO {config['end_date'].replace('-', '')}2359]"
                params.update(search_query=f"({q['search_query']}) AND {window}",
                              sortBy="submittedDate", sortOrder="ascending")
            url = API + "?" + urlencode(params)
            request_id, attempted = uuid.uuid4().hex, now()
            raw_path, sha = None, None
            with self.db:
                self.db.execute("INSERT INTO requests VALUES (?,?,?,?,?,?,'running',NULL,NULL,NULL)",
                                (request_id, run_id, q["id"], start, url, attempted))
            try:
                data = fetcher(url)
                sha = digest(data)
                raw_path = f"raw/{sha}.xml"
                destination = self.root / raw_path
                if not destination.exists():
                    temporary = destination.with_suffix(".tmp")
                    temporary.write_bytes(data)
                    temporary.replace(destination)
                feed = parse_atom(data)
                entries = feed["entries"]
                if feed["start"] != params["start"] or len(entries) > params["max_results"]:
                    raise ValueError("Unexpected page start or size; cursor unchanged")
                if start + len(entries) > feed["total"]:
                    raise ValueError("Page entries exceed totalResults; cursor unchanged")
                identities = [(p["arxiv_id"], p["version"]) if "ids" in q else p["arxiv_id"] for p in entries]
                if len(set(identities)) != len(identities):
                    raise ValueError("Duplicate paper identity within page; cursor unchanged")
                if not entries and feed["total"] > start:
                    raise ValueError("Empty page before totalResults; cursor unchanged")
                missing = []
                if "ids" in q:
                    observed = {(p["arxiv_id"], p["version"]) for p in entries}
                    requested = {arxiv_identity(i) for i in q["ids"]}
                    missing = [i for i in q["ids"] if not any(a == arxiv_identity(i)[0] and
                               (arxiv_identity(i)[1] is None or v == arxiv_identity(i)[1]) for a, v in observed)]
                    if any(not any(a == p["arxiv_id"] and (v is None or v == p["version"]) for a, v in requested) for p in entries):
                        raise ValueError("Unexpected unrequested ID in id_list response")
                else:
                    if any(not config["start_date"] <= p["published"][:10] <= config["end_date"] for p in entries):
                        raise ValueError("Response outside requested submission date window")
                    if start and entries:
                        previous_ids = {r[0] for r in self.db.execute(
                            "SELECT s.arxiv_id FROM memberships m JOIN snapshots s USING(snapshot_id) WHERE m.run_id=? AND m.query_id=?", (run_id, q["id"]))}
                        if any(p["arxiv_id"] in previous_ids for p in entries):
                            raise ValueError("Repeated paper IDs across pages; pagination drift, cursor unchanged")
                count = start + len(entries)
                if missing:
                    status = "missing_ids"
                elif "ids" in q or count >= feed["total"]:
                    status = "complete" if count else "empty"
                elif count >= q["max_results"]:
                    status = "capped"
                else:
                    status = "pending"
                with self.db:
                    self.db.execute("UPDATE requests SET status='ok',raw_path=?,sha256=? WHERE request_id=?", (raw_path, sha, request_id))
                    for i, p in enumerate(entries):
                        metadata = encoded(p)
                        snapshot_id = digest(metadata.encode())
                        self.db.execute("INSERT OR IGNORE INTO papers VALUES (?)", (p["arxiv_id"],))
                        self.db.execute("INSERT OR IGNORE INTO snapshots VALUES (?,?,?,?,?)",
                                        (snapshot_id, p["arxiv_id"], p["version"], metadata, attempted))
                        self.db.execute("INSERT INTO memberships VALUES (?,?,?,?,?) ON CONFLICT(run_id,query_id,snapshot_id) DO UPDATE SET rank=excluded.rank,request_id=excluded.request_id",
                                        (run_id, q["id"], snapshot_id, start+i, request_id))
                    # Missing id_list entries are retried as a whole, with no cursor advance.
                    self.db.execute("UPDATE tasks SET next_start=?,returned=?,total=?,status=?,error=? WHERE run_id=? AND query_id=?",
                        (0 if missing else count, count, feed["total"], status,
                         "IDs not returned: " + ", ".join(missing) if missing else None, run_id, q["id"]))
                print(encoded({"query": q["id"], "page_start": start, "received": len(entries), "status": status}), file=sys.stderr, flush=True)
                if missing:
                    return
            except (OSError, ValueError, ET.ParseError, HTTPException) as exc:
                error = f"{type(exc).__name__}: {exc}"
                if isinstance(exc, HTTPError):
                    error += f"; Retry-After={exc.headers.get('Retry-After', 'unspecified') if exc.headers else 'unspecified'}"
                with self.db:
                    self.db.execute("UPDATE requests SET status='error',raw_path=?,sha256=?,error=? WHERE request_id=?", (raw_path, sha, error, request_id))
                    self.db.execute("UPDATE tasks SET status='error',error=? WHERE run_id=? AND query_id=?", (error, run_id, q["id"]))
                print(encoded({"query": q["id"], "status": "error", "error": error}), file=sys.stderr, flush=True)
                return isinstance(exc, RemoteCooldown) or (isinstance(exc, HTTPError) and
                    (exc.code == 429 or bool(exc.headers and exc.headers.get("Retry-After"))))

    def report(self, run_id=None):
        explicit = run_id is not None
        if run_id is None:
            row = self.db.execute("SELECT run_id FROM runs ORDER BY created_at DESC LIMIT 1").fetchone()
            run_id = row[0] if row else None
        run = self.db.execute("SELECT * FROM runs WHERE run_id=?", (run_id,)).fetchone()
        if not run:
            if explicit:
                raise ValueError("Unknown corpus run_id")
            return {"root": str(self.root), "run_id": None, "papers": 0, "tasks": []}
        config = json.loads(run["config_json"])
        tasks = [dict(r) for r in self.db.execute("SELECT * FROM tasks WHERE run_id=? ORDER BY query_id", (run_id,))]
        by_id = {q["id"]: q for q in config["queries"]}
        for task in tasks:
            task.update(lane=by_id[task["query_id"]]["lane"], domain=by_id[task["query_id"]]["domain"])
        papers = self.db.execute("SELECT COUNT(DISTINCT s.arxiv_id) FROM memberships m JOIN snapshots s USING(snapshot_id) WHERE m.run_id=?", (run_id,)).fetchone()[0]
        return {"root": str(self.root), "run_id": run_id, "name": config["name"], "config_hash": run["config_hash"],
            "papers": papers, "tasks": tasks,
            "collection_ok": all(t["status"] in {"complete", "empty", "capped"} for t in tasks),
            "query_exhausted": all(t["status"] in {"complete", "empty"} for t in tasks),
            "review_labels": "not_collected", "fulltext": "not_read",
            "notice": "Query-based sample; capped/exhausted is not field coverage or scientific quality."}

    def export(self, path, run_id=None):
        report = self.report(run_id)
        run_id = report["run_id"]
        config_row = self.db.execute("SELECT config_json FROM runs WHERE run_id=?", (run_id,)).fetchone()
        queries = {q["id"]: q for q in json.loads(config_row[0])["queries"]} if config_row else {}
        rows = self.db.execute("""SELECT s.*,m.query_id,m.rank,r.url,r.raw_path,r.sha256,r.attempted_at
            FROM memberships m JOIN snapshots s USING(snapshot_id) JOIN requests r USING(request_id)
            WHERE m.run_id=? ORDER BY s.arxiv_id,COALESCE(s.version,0) DESC,r.rowid DESC,m.query_id""", (run_id,))
        papers = {}
        for row in rows:
            aid = row["arxiv_id"]
            if aid not in papers:
                papers[aid] = {**json.loads(row["metadata_json"]), "snapshot_id": row["snapshot_id"],
                    "review_status": "not_collected", "decisions": [], "fulltext_status": "not_read",
                    "signature_status": "not_extracted", "memberships": [], "observed_snapshots": []}
            p = papers[aid]
            if row["snapshot_id"] not in p["observed_snapshots"]:
                p["observed_snapshots"].append(row["snapshot_id"])
            query = queries[row["query_id"]]
            p["memberships"].append({"query_id": row["query_id"], "lane": query["lane"], "domain": query["domain"],
                "snapshot_id": row["snapshot_id"], "rank": row["rank"], "request_url": row["url"],
                "raw_path": row["raw_path"], "sha256": row["sha256"], "retrieved_at": row["attempted_at"]})
        target = Path(path).expanduser().resolve()
        if target == self.root / "corpus.sqlite3" or self.root / "raw" in target.parents:
            raise ValueError("Export must not overwrite the database or raw responses")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("".join(encoded(p) + "\n" for p in papers.values()))
        target.with_suffix(target.suffix + ".manifest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        return {"path": str(target), "papers": len(papers), "run_id": run_id}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, help="Explicit corpus output directory, separate from installed plugin")
    subs = parser.add_subparsers(dest="command", required=True)
    harvest = subs.add_parser("harvest", help="Collect or resume the same config; no PDFs or model calls")
    harvest.add_argument("--config", required=True)
    harvest.add_argument("--refresh", action="store_true", help="Create a new sampling run; retain old snapshots")
    subs.add_parser("status")
    export = subs.add_parser("export")
    export.add_argument("--output", required=True)
    export.add_argument("--run-id")
    args = parser.parse_args(argv)
    try:
        with Corpus(args.root) as corpus:
            if args.command == "harvest":
                result = corpus.harvest(json.loads(Path(args.config).read_text()), refresh=args.refresh)
            elif args.command == "export":
                result = corpus.export(args.output, args.run_id)
            else:
                result = corpus.report()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2 if args.command == "harvest" and not result["collection_ok"] else 0
    except (OSError, ValueError, sqlite3.Error) as exc:
        print(f"corpus: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
