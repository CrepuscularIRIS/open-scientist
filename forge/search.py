"""Small, independently implemented read-only corpus and arXiv adapters.

Retrieval records are discovery leads, not claim verification or novelty verdicts.
Uses Python's standard library; never builds an index or copies PDF files.
"""
from __future__ import annotations

import copy
from datetime import datetime, timezone
from http.client import HTTPException
import json
import math
import os
from pathlib import Path
import re
import sqlite3
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


DEFAULT_DB = "/data/paper_index/local_papers.db"
ARXIV_API = "https://export.arxiv.org/api/query"
NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom",
      "open": "http://a9.com/-/spec/opensearch/1.1/"}


def _tokens(query):
    words = list(dict.fromkeys(re.findall(r"[^\W_]+", query.lower(), re.UNICODE)))
    if not words or len(query) > 512 or len(words) > 32:
        raise ValueError("Each query needs 1–32 keyword tokens and at most 512 characters")
    return words


def _bounds(max_papers, start_year, end_year, timeout):
    if not isinstance(max_papers, int) or not 1 <= max_papers <= 100:
        raise ValueError("max_papers must be 1–100")
    for year in (start_year, end_year):
        if year is not None and (not isinstance(year, int) or not 1000 <= year <= 9999):
            raise ValueError("Years must be four-digit integers")
    if start_year and end_year and start_year > end_year:
        raise ValueError("start_year must not exceed end_year")
    if not math.isfinite(timeout) or not 0 < timeout <= 60:
        raise ValueError("timeout must be finite and in (0, 60] seconds")


def _doi(value):
    value = str(value or "").strip().lower()
    return re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", "", value)


def _arxiv(value):
    match = re.search(r"(?:arxiv\.org/(?:abs|pdf)/|arxiv:)([^?#\s]+)", str(value or ""), re.I)
    text = match.group(1) if match else str(value or "")
    text = re.sub(r"\.pdf$", "", text)
    text = re.sub(r"v\d+$", "", text)
    return text.lower() if re.fullmatch(r"(?:\d{4}\.\d{4,5}|[a-z-]+(?:\.[A-Z]{2})?/\d{7})", text, re.I) else ""


def _result(source, query, status, papers=None, detail="", truncated=False):
    return {"source": source, "query": query, "status": status,
            "papers": papers or [], "detail": detail, "truncated": truncated}


def search_local(query, *, db_path=None, max_papers=20, start_year=None,
                 end_year=None, timeout=10):
    """Read the installed papers/papers_fts schema through FTS5, with SQL LIMIT."""
    _bounds(max_papers, start_year, end_year, timeout)
    terms = _tokens(query)
    path = Path(db_path or os.environ.get("PAPER_SEARCH_LOCAL_DB", DEFAULT_DB)).expanduser().resolve()
    if not path.is_file():
        return _result("local", query, "missing_index", detail=f"Index not found: {path}")
    deadline = time.monotonic() + timeout
    conn = None
    try:
        conn = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=timeout)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA query_only = ON")
        conn.set_progress_handler(lambda: int(time.monotonic() >= deadline), 1000)
        where = ["papers_fts MATCH ?"]
        params = [' AND '.join('"' + term + '"' for term in terms)]
        if start_year is not None:
            where.append("p.year >= ?")
            params.append(start_year)
        if end_year is not None:
            where.append("p.year <= ?")
            params.append(end_year)
        params.append(max_papers + 1)
        rows = conn.execute(
            "SELECT p.id,p.title,p.abstract,p.authors,p.venue,p.year,p.url,p.pdf_path,"
            "p.corpus,p.title_source,p.abstract_source FROM papers_fts "
            "JOIN papers p ON p.id=papers_fts.rowid WHERE " + " AND ".join(where) +
            " ORDER BY bm25(papers_fts),p.id LIMIT ?", params).fetchall()
        papers = []
        for row in rows[:max_papers]:
            p = dict(row)
            record_id = str(p.pop("id"))
            if not isinstance(p["title"], str) or not p["title"].strip():
                return _result("local", query, "error", detail=f"Record {record_id} has no usable title")
            try:
                authors = json.loads(p["authors"] or "[]")
            except (ValueError, TypeError):
                authors = []
            p["authors"] = authors if isinstance(authors, list) else []
            p["arxiv_id"] = _arxiv(p["url"])
            p["doi"] = _doi(p["url"]) if re.match(r"https?://(?:dx\.)?doi\.org/", p["url"] or "", re.I) else ""
            p["provenance"] = [{"source": "local", "query": query, "record_id": record_id,
                                "url": p["url"], "index": str(path), "corpus": p["corpus"],
                                "pdf_path": p["pdf_path"]}]
            papers.append(p)
        return _result("local", query, "ok" if papers else "empty", papers,
                       truncated=len(rows) > max_papers)
    except (sqlite3.Error, OSError) as exc:
        return _result("local", query, "error", detail=str(exc))
    finally:
        if conn is not None:
            conn.close()


def search_arxiv(query, *, max_papers=20, start_year=None, end_year=None, timeout=10):
    """One bounded keyword request to the public Atom API; no retries or PDFs."""
    _bounds(max_papers, start_year, end_year, timeout)
    expression = " AND ".join(f'all:"{term}"' for term in _tokens(query))
    if start_year or end_year:
        expression += f" AND submittedDate:[{start_year or 1000}01010000 TO {end_year or 9999}12312359]"
    url = ARXIV_API + "?" + urlencode({"search_query": expression, "start": 0,
        "max_results": max_papers, "sortBy": "relevance", "sortOrder": "descending"})
    request = Request(url, headers={"User-Agent": "OpenScientist-literature-adapter/0.1",
                                    "Accept": "application/atom+xml"})
    deadline = time.monotonic() + timeout
    try:
        with urlopen(request, timeout=timeout) as response:
            chunks, size = [], 0
            while True:
                if time.monotonic() >= deadline:
                    raise TimeoutError("Response exceeded request budget")
                chunk = response.read(65536)
                if not chunk:
                    break
                size += len(chunk)
                if size > 2 * 1024 * 1024:
                    return _result("arxiv", query, "unavailable", detail="Response exceeds 2 MiB limit")
                chunks.append(chunk)
        feed = ET.fromstring(b"".join(chunks))
        if feed.tag != "{" + NS["atom"] + "}feed":
            return _result("arxiv", query, "unavailable", detail="Response is not an Atom feed")
        papers = []
        for entry in feed.findall("atom:entry", NS):
            def text(key):
                return " ".join((entry.findtext(key, default="", namespaces=NS)).split())
            entry_url = text("atom:id")
            arxiv_id = _arxiv(entry_url)
            if not arxiv_id:
                return _result("arxiv", query, "unavailable", detail="API error or malformed entry: " + text("atom:title"))
            published = text("atom:published")
            year = int(published[:4]) if published[:4].isdigit() else None
            if not text("atom:title") or not text("atom:summary") or year is None:
                return _result("arxiv", query, "unavailable", detail="Incomplete entry metadata: " + entry_url)
            if (start_year and (year is None or year < start_year)) or (end_year and (year is None or year > end_year)):
                continue
            pdf_url = next((link.attrib.get("href", "") for link in entry.findall("atom:link", NS)
                            if link.attrib.get("type") == "application/pdf"), "")
            papers.append({"title": text("atom:title"), "abstract": text("atom:summary"),
                "authors": [a.findtext("atom:name", default="", namespaces=NS) for a in entry.findall("atom:author", NS)],
                "year": year, "venue": "arXiv", "url": entry_url, "pdf_url": pdf_url,
                "pdf_path": "", "arxiv_id": arxiv_id, "doi": _doi(text("arxiv:doi")),
                "provenance": [{"source": "arxiv", "query": query, "record_id": entry_url,
                                "url": entry_url, "request_url": url}]})
        count_text = feed.findtext("open:totalResults", default="", namespaces=NS)
        total = int(count_text) if count_text.isdigit() else None
        return _result("arxiv", query, "ok" if papers else "empty", papers[:max_papers],
                       truncated=(total > max_papers if total is not None else len(papers) >= max_papers))
    except HTTPError as exc:
        return _result("arxiv", query, "rate_limited" if exc.code == 429 else "unavailable", detail=f"HTTP {exc.code}")
    except TimeoutError as exc:
        return _result("arxiv", query, "timeout", detail=str(exc))
    except URLError as exc:
        return _result("arxiv", query, "timeout" if isinstance(exc.reason, TimeoutError) else "unavailable", detail=str(exc.reason))
    except (ET.ParseError, HTTPException, OSError, ValueError) as exc:
        return _result("arxiv", query, "unavailable", detail=str(exc))


def deduplicate(papers):
    """Union normalized DOI, arXiv version IDs and title matches; keep provenance.

    Title equality is a retrieval heuristic, not proof that two claims coincide.
    Alias keys survive merging so later records can link through earlier titles.
    """
    groups, owner = {}, {}
    for paper in papers:
        p = copy.deepcopy(paper)
        keys = set()
        doi, aid = _doi(p.get("doi")), _arxiv(p.get("arxiv_id") or p.get("url"))
        title = " ".join(re.findall(r"[^\W_]+", str(p.get("title") or "").lower()))
        for kind, value in (("doi", doi), ("arxiv", aid), ("title", title)):
            if value:
                keys.add((kind, value))
        matches = {owner[k] for k in keys if k in owner}
        if not matches:
            group_id = len(owner) + len(groups)
            while group_id in groups:
                group_id += 1
            groups[group_id] = p
        else:
            group_id = min(matches)
            target = groups[group_id]
            for other_id in sorted(matches - {group_id}):
                other = groups.pop(other_id)
                p.setdefault("provenance", []).extend(other.get("provenance", []))
                for key in list(owner):
                    if owner[key] == other_id:
                        owner[key] = group_id
            provenance = target.setdefault("provenance", [])
            for item in p.get("provenance", []):
                if item not in provenance:
                    provenance.append(item)
            for key, value in p.items():
                if not target.get(key) and value:
                    target[key] = value
        for key in keys:
            owner[key] = group_id
    return list(groups.values())


def search(queries, *, sources=("local", "arxiv"), max_papers=20, start_year=None,
           end_year=None, timeout=10, budget_seconds=25, db_path=None):
    """Search bounded batches; preserve every source/query outcome, including failures."""
    _bounds(max_papers, start_year, end_year, timeout)
    if not math.isfinite(budget_seconds) or not 0 < budget_seconds <= 300:
        raise ValueError("budget_seconds must be finite and in (0, 300]")
    queries = list(dict.fromkeys(q.strip() for q in queries if q.strip()))
    sources = list(dict.fromkeys(sources))
    if not queries or len(queries) > 8:
        raise ValueError("Provide 1–8 queries")
    if not sources or any(s not in ("local", "arxiv") for s in sources):
        raise ValueError("sources must contain only local and/or arxiv")
    for query in queries:
        _tokens(query)
    started = time.monotonic()
    deadline, last_arxiv = started + budget_seconds, None
    attempts = []
    for source in sources:
        for query in queries:
            if source == "arxiv" and last_arxiv is not None:
                delay = max(0, 3.1 - (time.monotonic() - last_arxiv))
                if time.monotonic() + delay < deadline:
                    time.sleep(delay)
                elif delay:
                    attempts.append(_result(source, query, "timeout", detail="budget_exhausted_before_rate_spacing"))
                    continue
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                attempts.append(_result(source, query, "timeout" if source == "arxiv" else "error", detail="budget_exhausted"))
                continue
            kwargs = dict(max_papers=max_papers, start_year=start_year, end_year=end_year,
                          timeout=min(timeout, remaining))
            if source == "local":
                result = search_local(query, db_path=db_path, **kwargs)
            else:
                result = search_arxiv(query, **kwargs)
                last_arxiv = time.monotonic()
            attempts.append(result)
    # Interleave attempts before deduplication so a single broad query cannot
    # monopolize the display cap. Retain all attempt summaries even after capping.
    interleaved = []
    for rank in range(max((len(a["papers"]) for a in attempts), default=0)):
        interleaved.extend(a["papers"][rank] for a in attempts if rank < len(a["papers"]))
    merged = deduplicate(interleaved)
    reports = {}
    for source in sources:
        own = [a for a in attempts if a["source"] == source]
        good = [a for a in own if a["status"] in ("ok", "empty")]
        status = "ok" if any(a["status"] == "ok" for a in good) else "empty" if good else own[0]["status"]
        reports[source] = {"status": status, "partial": len(good) != len(own),
            "attempts": [{k: v for k, v in a.items() if k not in ("papers", "source")} |
                         {"count": len(a["papers"])} for a in own]}
    failed = [s for s, value in reports.items() if value["partial"]]
    limited = len(merged) > max_papers or any(a["truncated"] for a in attempts)
    return {"schema_version": 1, "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "queries": queries, "year_range": {"start": start_year, "end": end_year},
        "sources": reports, "papers": merged[:max_papers], "evidence_status": "retrieval_only",
        "coverage": {"partial": bool(failed) or limited, "failed_sources": failed,
            "limited": limited, "unique_before_display_limit": len(merged),
            "note": "Bounded keyword retrieval only; an empty result does not establish novelty. Source identity and claim support require separate checks."},
        "elapsed_seconds": round(time.monotonic() - started, 3)}
