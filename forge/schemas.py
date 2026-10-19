"""Validators for domain assets. Each returns a list of human-readable errors (empty = valid).

The navigator runs these before advancing, and hands any errors back to the
step that produced the file, so a malformed asset is repaired, never skipped.
"""
from __future__ import annotations

import re

from forge.util import read_json, read_jsonl, tolerant
from forge.vendor.corpus import normalize_config

RELEVANCE = {"core", "adjacent", "off_topic"}
LANES = {"in_domain", "cross_domain"}
ACCESS = {"arxiv_html", "arxiv_pdf", "local_pdf", "abstract_only", "other"}
EVIDENCE = {"author_claim", "reported_experiment", "theorem", "observed"}
CARD_STATUS = {"case", "candidate_pattern", "checked_for_scope", "needs_revision"}
EXPECTATION_KIND = {"baseline", "dataset", "metric", "ablation", "theory", "reproducibility", "scale", "other"}
EXPECTATION_EVIDENCE = {"paper_limitation", "paper_practice", "review"}
OUTCOMES = {"accepted", "rejected", "withdrawn", "desk_rejected", "pending", "unknown"}
STRENGTHS = ("single_source", "common_practice", "observed_in_reviews")  # weakest first
COMMON_PRACTICE_PAPERS = 3
ARXIV_SOURCES = {"arxiv_html", "arxiv_pdf"}
PATTERN_STATUS = {"candidate_pattern", "checked_for_scope"}
CARD_SECTIONS = ("## Operation", "## When it works", "## When it fails", "## Counterexamples", "## Sources")
CARD_ID = re.compile(r"^K\d{2,3}-[a-z0-9-]{1,48}$")


def safe_id(arxiv_id):
    return arxiv_id.replace("/", "_")


def _text(value):
    return isinstance(value, str) and value.strip() != ""


def _texts(value):
    return isinstance(value, list) and all(_text(v) for v in value)


@tolerant
def validate_queries(layout):
    config = read_json(layout.file("queries.json"))
    if config is None:
        return ["queries.json missing"]
    try:
        normalize_config(config)
    except ValueError as exc:
        return [f"queries.json: {exc}"]
    lanes = {q.get("lane") for q in config["queries"]}
    return [] if lanes == LANES else ["queries.json: include at least one in_domain and one cross_domain query"]


def papers(layout):
    return {p["arxiv_id"]: p for p in read_jsonl(layout.file("papers.jsonl"))}


@tolerant
def validate_triage(layout):
    data = read_json(layout.file("triage.json"))
    if not isinstance(data, dict) or not isinstance(data.get("papers"), list):
        return ["triage.json must be {\"papers\": [...]}"]
    known, seen, errors = papers(layout), set(), []
    for i, row in enumerate(data["papers"]):
        where = f"triage.papers[{i}]"
        aid = row.get("arxiv_id") if isinstance(row, dict) else None
        if aid not in known:
            errors.append(f"{where}: unknown arxiv_id {aid!r}")
            continue
        if aid in seen:
            errors.append(f"{where}: duplicate {aid}")
        seen.add(aid)
        if row.get("relevance") not in RELEVANCE:
            errors.append(f"{where}: relevance must be one of {sorted(RELEVANCE)}")
        if row.get("lane") not in LANES:
            errors.append(f"{where}: lane must be in_domain or cross_domain")
        if type(row.get("read_priority")) is not int or row["read_priority"] < 0:
            errors.append(f"{where}: read_priority must be an integer >= 0 (0 = do not read)")
        if row.get("relevance") == "off_topic" and row.get("read_priority"):
            errors.append(f"{where}: off_topic papers must have read_priority 0")
        if not _text(row.get("reason")):
            errors.append(f"{where}: reason required")
    missing = sorted(set(known) - seen)
    if missing:
        errors.append(f"triage.json does not cover {len(missing)} papers, e.g. {missing[:3]}")
    return errors


def read_limit(layout):
    return (read_json(layout.file("settings.json")) or {}).get("read_limit", 25)


def reading_targets(layout, limit=None):
    """Papers to read: highest read_priority first, ties by arxiv_id; never off_topic. Limit persists in settings.json."""
    limit = read_limit(layout) if limit is None else limit
    data = read_json(layout.file("triage.json")) or {"papers": []}
    rows = [r for r in data.get("papers", []) if isinstance(r, dict) and type(r.get("read_priority")) is int
            and r["read_priority"] > 0 and r.get("relevance") != "off_topic" and isinstance(r.get("arxiv_id"), str)]
    rows.sort(key=lambda r: (-r["read_priority"], r["arxiv_id"]))
    return [r["arxiv_id"] for r in rows[:limit]]


@tolerant
def validate_reading(layout, arxiv_id):
    path = layout.readings_dir / f"{safe_id(arxiv_id)}.json"
    data = read_json(path)
    if not isinstance(data, dict):
        return [f"{path.name}: missing or not an object"]
    errors, where = [], path.name
    known = papers(layout).get(arxiv_id)
    if data.get("arxiv_id") != arxiv_id:
        errors.append(f"{where}: arxiv_id must be {arxiv_id}")
    if known and data.get("snapshot_id") != known.get("snapshot_id"):
        errors.append(f"{where}: snapshot_id must match papers.jsonl ({known.get('snapshot_id')})")
    access = data.get("access") or {}
    if access.get("source") not in ACCESS or not _text(access.get("locator")) or not _texts(access.get("sections_read")):
        errors.append(f"{where}: access needs source in {sorted(ACCESS)}, a locator and sections_read[]")
    if access.get("source") in ARXIV_SOURCES:
        version = access.get("version")
        if not isinstance(version, str) or not re.fullmatch(r"v\d+", version) or version not in str(access.get("locator")):
            errors.append(f"{where}: access.version must name the arXiv version read (e.g. v2) and the locator must be "
                          "that versioned URL; an unversioned URL does not pin what was read")
    if access.get("source") != "abstract_only" and not access.get("sections_read"):
        errors.append(f"{where}: a full-text reading lists the sections it read")
    if not _text(data.get("summary")):
        errors.append(f"{where}: summary required")
    sigs = data.get("signatures")
    if not isinstance(sigs, list) or not sigs:
        errors.append(f"{where}: at least one signature required")
        sigs = []
    abstract_only = access.get("source") == "abstract_only"
    for j, sig in enumerate(sigs):
        at = f"{where}.signatures[{j}]"
        if not isinstance(sig, dict):
            errors.append(f"{at}: must be an object")
            continue
        if not isinstance(sig.get("sig_id"), str) or not re.fullmatch(re.escape(arxiv_id) + r"#s\d+", sig["sig_id"]):
            errors.append(f"{at}: sig_id must look like {arxiv_id}#s1")
        for field in ("object", "information", "operation", "output", "claimed_effect", "failure_boundary"):
            if not _text(sig.get(field)):
                errors.append(f"{at}: {field} required")
        if not _texts(sig.get("conditions")):
            errors.append(f"{at}: conditions must be a list of strings")
        evidence = sig.get("evidence") or {}
        if evidence.get("kind") not in EVIDENCE or not _text(evidence.get("locator")):
            errors.append(f"{at}: evidence needs kind in {sorted(EVIDENCE)} and a locator")
        expected = "abstract_only" if abstract_only else "fulltext"
        if sig.get("verified") != expected:
            errors.append(f"{at}: verified must be {expected!r} for access source {access.get('source')!r}")
    ids = [s.get("sig_id") for s in sigs if isinstance(s, dict)]
    if len(set(ids)) != len(ids):
        errors.append(f"{where}: duplicate sig_id")
    for k, b in enumerate(data.get("baselines") or []):
        if not isinstance(b, dict) or not _text(b.get("name")) or b.get("kind") not in {"method", "dataset", "metric", "benchmark"}:
            errors.append(f"{where}.baselines[{k}]: needs name and kind method|dataset|metric|benchmark")
    if not isinstance(data.get("limitations", []), list):
        errors.append(f"{where}: limitations must be a list")
    return errors


def signatures(layout, ids):
    found = {}
    for aid in ids:
        data = read_json(layout.readings_dir / f"{safe_id(aid)}.json") or {}
        for sig in data.get("signatures") or []:
            if isinstance(sig, dict) and isinstance(sig.get("sig_id"), str):
                found[sig["sig_id"]] = {**sig, "arxiv_id": aid}
    return found


def _refs(items, known, where, errors):
    if not isinstance(items, list):
        errors.append(f"{where}: must be a list")
        return
    for k, item in enumerate(items):
        if not isinstance(item, dict) or not _text(item.get("text")) or not item.get("refs"):
            errors.append(f"{where}[{k}]: needs text and refs[]")
        elif any(r not in known for r in item["refs"]):
            errors.append(f"{where}[{k}]: refs must be known sig_ids or lesson:<key> from lessons.jsonl")


def lesson_refs(layout):
    return {f"lesson:{row['key']}" for row in read_jsonl(layout.lessons) if isinstance(row, dict) and row.get("key")}


@tolerant
def validate_cards(layout, reading_ids):
    index = read_json(layout.cards_dir / "index.json")
    if not isinstance(index, dict) or not isinstance(index.get("cards"), list):
        return ["cards/index.json must be {\"cards\": [...], \"unassigned\": [...]}"]
    known = signatures(layout, reading_ids)
    citable = set(known) | lesson_refs(layout)  # observations from runs are cited as lessons, never as papers
    errors, placed, ids = [], {}, set()
    for i, card in enumerate(index["cards"]):
        where = f"cards[{i}]"
        cid = card.get("card_id") if isinstance(card, dict) else None
        if not isinstance(cid, str) or not CARD_ID.fullmatch(cid) or cid in ids:
            errors.append(f"{where}: card_id must be unique and look like K01-short-name")
            continue
        ids.add(cid)
        if card.get("status") not in CARD_STATUS:
            errors.append(f"{cid}: status must be one of {sorted(CARD_STATUS)}")
        for field in ("title", "operation", "transfer_notes"):
            if not _text(card.get(field)):
                errors.append(f"{cid}: {field} required")
        members = card.get("members")
        if not isinstance(members, list) or not members:
            errors.append(f"{cid}: members[] required")
            members = []
        for sig in members:
            if sig not in known:
                errors.append(f"{cid}: unknown member {sig!r}")
            elif sig in placed:
                errors.append(f"{cid}: {sig} already in {placed[sig]}")
            else:
                placed[sig] = cid
        read_papers = {known[s]["arxiv_id"] for s in members if s in known and known[s].get("verified") == "fulltext"}
        if card.get("status") in PATTERN_STATUS and len(read_papers) < 2:
            errors.append(f"{cid}: {card.get('status')} needs members from >= 2 papers read in full text "
                          f"(has {len(read_papers)}); abstract-only signatures are leads, so use status case")
        for field in ("success_conditions", "failure_modes", "counterexamples"):
            _refs(card.get(field, []), citable, f"{cid}.{field}", errors)
        path = layout.work / (card.get("file") or "")
        if not card.get("file") or not path.is_file():
            errors.append(f"{cid}: file {card.get('file')!r} missing")
        else:
            body = path.read_text(encoding="utf-8")
            errors += [f"{cid}: card file lacks {s}" for s in CARD_SECTIONS if s not in body]
    unassigned = index.get("unassigned")
    if not isinstance(unassigned, list):
        errors.append("cards/index.json: unassigned[] required (may be empty)")
        unassigned = []
    for sig in unassigned:
        if sig in placed:
            errors.append(f"unassigned {sig} is also in {placed[sig]}")
    missing = sorted(set(known) - set(placed) - set(unassigned))
    if missing:
        errors.append(f"{len(missing)} signatures neither in a card nor unassigned, e.g. {missing[:3]}")
    return errors


@tolerant
def validate_profile(layout, card_ids, reading_ids):
    errors, prof = [], layout.profile_dir
    sigs = signatures(layout, reading_ids)
    exp = read_json(prof / "expectations.json")
    if not isinstance(exp, dict) or not isinstance(exp.get("expectations"), list):
        errors.append("profile/expectations.json must be {\"expectations\": [...]}")
    else:
        corpus = {f"arxiv:{a}" for a in papers(layout)}
        reviews = {r["review_id"]: r for r in read_jsonl(layout.file("reviews.jsonl"))
                   if isinstance(r, dict) and r.get("review_id") and r.get("paper_ref") in corpus}  # reviews of domain papers only
        for i, e in enumerate(exp["expectations"]):
            errors += validate_expectation(e, f"expectations[{i}]", sigs, set(reading_ids), reviews)
    lex = read_json(prof / "lexicon.json")
    if not isinstance(lex, dict) or not isinstance(lex.get("cards"), dict):
        errors.append("profile/lexicon.json must have cards{card_id: {signature_terms, alias_terms}}")
    else:
        for cid in card_ids:
            terms = lex["cards"].get(cid)
            if not isinstance(terms, dict) or not _texts(terms.get("signature_terms")) or not terms.get("signature_terms") \
                    or not _texts(terms.get("alias_terms", [])):
                errors.append(f"lexicon: card {cid} needs signature_terms[] (and alias_terms[] list)")
        win = lex.get("collision_windows") or {}
        if any(type(win.get(k)) is not int or not 1 <= win[k] <= 120 for k in ("signature_months", "alias_months")) \
                or not _text(win.get("basis")):
            errors.append("lexicon.collision_windows needs signature_months, alias_months (1..120) and basis")
    cross = read_json(prof / "crossmap.json")
    if not isinstance(cross, dict) or not isinstance(cross.get("maps"), list):
        errors.append("profile/crossmap.json must be {\"maps\": [...]} (may be empty)")
    else:
        for i, m in enumerate(cross["maps"]):
            mapping = m.get("mapping") or {}
            if not _text(m.get("source_domain")) or not m.get("source_refs") or any(r not in sigs for r in m["source_refs"]) \
                    or not all(_text(mapping.get(k)) for k in ("object", "operation", "condition")) \
                    or not _text(m.get("breaks_if")) or m.get("status") not in {"proposed", "checked", "refuted"}:
                errors.append(f"crossmap[{i}]: needs source_domain, source_refs (sig_ids), mapping{{object,operation,condition}}, breaks_if, status")
    return errors


def supported_strength(evidence, sigs, reading_ids, reviews):
    """The strongest strength the evidence supports: reviews need resolvable review text; practice needs >= 3 papers."""
    if any(x.get("kind") == "review" and x.get("ref") in reviews for x in evidence):
        return "observed_in_reviews"  # quote and paper checks are separate errors in validate_expectation
    papers_shown = {sigs[x["ref"]]["arxiv_id"] if x.get("ref") in sigs else x.get("ref")
                    for x in evidence if x.get("kind") in {"paper_practice", "paper_limitation"}}
    return "common_practice" if len(papers_shown & reading_ids) >= COMMON_PRACTICE_PAPERS else "single_source"


def validate_expectation(e, at, sigs, reading_ids, reviews):
    if not isinstance(e, dict):
        return [f"{at}: must be an object"]
    errors = []
    if not _text(e.get("id")) or not _text(e.get("text")) or e.get("kind") not in EXPECTATION_KIND:
        errors.append(f"{at}: needs id, text and kind in {sorted(EXPECTATION_KIND)}")
    if not _text(e.get("applies_when")):
        errors.append(f"{at}: applies_when required: the kind of claim or setting this expectation is about "
                      "(a check reviewers ask of every paper here is 'any empirical method claim')")
    ev = e.get("evidence")
    if not isinstance(ev, list) or not ev or not all(isinstance(x, dict) for x in ev):
        return errors + [f"{at}: evidence[] needs at least one {{kind, ref}} object"]
    for k, x in enumerate(ev):
        if x.get("kind") not in EXPECTATION_EVIDENCE:
            errors.append(f"{at}.evidence[{k}]: kind must be one of {sorted(EXPECTATION_EVIDENCE)}")
        elif x.get("kind") == "review":
            if x.get("ref") not in reviews or not _text(x.get("quote")):
                errors.append(f"{at}.evidence[{k}]: review evidence needs ref = a review_id in reviews.jsonl and the "
                              "quoted review sentence; without review text it is not review evidence")
            elif " ".join(x["quote"].split()).lower() not in " ".join(str(reviews[x["ref"]].get("text")).split()).lower():
                errors.append(f"{at}.evidence[{k}]: the quote is not in review {x['ref']}'s text; quote it verbatim")
        elif x.get("ref") not in sigs and x.get("ref") not in reading_ids:
            errors.append(f"{at}.evidence[{k}]: ref must be a read paper's arxiv_id or sig_id")
    strength = e.get("strength")
    if strength not in STRENGTHS:
        errors.append(f"{at}: strength must be one of {list(STRENGTHS)}")
    elif not errors and STRENGTHS.index(strength) > STRENGTHS.index(supported_strength(ev, sigs, reading_ids, reviews)):
        errors.append(f"{at}: strength {strength} exceeds what the evidence supports "
                      f"({supported_strength(ev, sigs, reading_ids, reviews)}): observed_in_reviews needs resolvable "
                      f"review evidence, common_practice needs {COMMON_PRACTICE_PAPERS} read papers")
    return errors


@tolerant
def validate_reviews(layout):
    """Optional reviews.jsonl: review text the expectations may cite. One row per review (or meta-review)."""
    errors, seen = [], set()
    for i, row in enumerate(read_jsonl(layout.file("reviews.jsonl"))):
        if not isinstance(row, dict) or not _text(row.get("review_id")) or not _text(row.get("paper_ref")) \
                or not _text(row.get("text")) or not _text(row.get("source")):
            errors.append(f"reviews.jsonl:{i + 1}: needs review_id, paper_ref, text (the review itself) and source")
        elif row["review_id"] in seen:
            errors.append(f"reviews.jsonl:{i + 1}: duplicate review_id {row['review_id']}")
        else:
            seen.add(row["review_id"])
    return errors


@tolerant
def validate_labels(layout):
    errors = []
    for i, row in enumerate(read_jsonl(layout.file("labels.jsonl"))):
        if not isinstance(row, dict) or not isinstance(row.get("paper_ref"), str) or ":" not in row["paper_ref"] \
                or row.get("outcome") not in OUTCOMES or not _text(row.get("source")) or not _text(row.get("venue")) \
                or type(row.get("year")) is not int:
            errors.append(f"labels.jsonl:{i + 1}: one submission event needs paper_ref 'arxiv:<id>', outcome in "
                          f"{sorted(OUTCOMES)}, venue, year (int) and source; a resubmission is its own row")
    return errors
