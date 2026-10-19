"""OpenReview label collection: real parser/store, injected transport, never live HTTP.

Fixtures mirror the API v2 shapes observed on 2026-10-18 (ICLR 2025 group and
submission notes with details=replies). Each test names the failure it catches.
"""
from __future__ import annotations

import hashlib
import importlib
import json
from email.message import Message
import io
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlparse

import pytest

V = "ICLR.cc/2025/Conference"


def api(name="forge.vendor.openreview_labels"):
    try:
        return importlib.import_module(name)
    except ModuleNotFoundError as exc:
        if exc.name != name:
            raise
        pytest.fail(f"{name} has not been implemented yet")


def group(venue=V, **overrides):
    content = {
        "submission_id": f"{venue}/-/Submission",
        "submission_venue_id": f"{venue}/Submission",
        "rejected_venue_id": f"{venue}/Rejected_Submission",
        "withdrawn_venue_id": f"{venue}/Withdrawn_Submission",
        "desk_rejected_venue_id": f"{venue}/Desk_Rejected_Submission",
        "decision_name": "Decision", "review_name": "Official_Review",
        "meta_review_name": "Meta_Review", "review_rating": "rating",
        "review_confidence": "confidence", "decision_field_name": "decision",
    }
    content.update(overrides)
    return {"groups": [{"id": venue, "content": {k: {"value": v} for k, v in content.items() if v is not None}}]}


def rid(forum, name, signer):
    """Opaque like real OpenReview ids: the signer must not leak through the id."""
    return f"{forum}-{name}-" + hashlib.sha1(signer.encode()).hexdigest()[:8]


def reply(forum, number, name, signer, content, replyto=None):
    return {"id": rid(forum, name, signer), "forum": forum, "replyto": replyto or forum,
            "invitations": [f"{V}/Submission{number}/-/{name}", f"{V}/-/Edit"],
            "signatures": [signer], "cdate": 1730000000000, "mdate": 1730000000000,
            "content": {k: {"value": v} for k, v in content.items()}}


def submission(number, venueid, *, decision=None, title=None, area="robotics", ratings=(6, 3)):
    forum = f"F{number}"
    replies = []
    for i, rating in enumerate(ratings):
        replies.append(reply(forum, number, "Official_Review", f"{V}/Submission{number}/Reviewer_r{i}",
                             {"rating": rating, "confidence": 4, "soundness": 3,
                              "strengths": f"clear idea {i}", "weaknesses": f"missing baseline {i}"}))
    if decision is not None:
        replies.append(reply(forum, number, "Decision", f"{V}/Program_Chairs",
                             {"title": "Paper Decision", "decision": decision}))
        replies.append(reply(forum, number, "Meta_Review", f"{V}/Submission{number}/Area_Chair_a",
                             {"metareview": "Reviewers want stronger baselines."}))
    replies.append(reply(forum, number, "Public_Comment", "~Real_Person1", {"comment": "nice"}))
    replies.append(reply(forum, number, "Official_Comment", f"{V}/Submission{number}/Authors",
                         {"comment": "rebuttal text"}, replyto=rid(forum, "Official_Review", f"{V}/Submission{number}/Reviewer_r0")))
    return {"id": forum, "forum": forum, "number": number, "invitations": [f"{V}/-/Submission"],
            "odate": 1728000000000, "pdate": None, "mdate": 1737000000000, "version": 2,
            "signatures": [f"{V}/Submission{number}/Authors"],
            "content": {"title": {"value": title or f"Paper {number}"},
                        "abstract": {"value": f"We study policy learning {number}."},
                        "keywords": {"value": ["robot learning"]}, "primary_area": {"value": area},
                        "venueid": {"value": venueid}, "venue": {"value": "ICLR 2025"},
                        "authorids": {"value": ["~Author_One1"]}, "authors": {"value": ["Author One"]}},
            "details": {"replies": replies}}


SUBMISSIONS = [
    submission(1, V, decision="Accept (Oral)"),
    submission(2, f"{V}/Rejected_Submission", decision="Reject", area="optimization"),
    submission(3, f"{V}/Withdrawn_Submission"),
    submission(4, f"{V}/Desk_Rejected_Submission", ratings=()),
    submission(5, V, decision="Reject"),  # official status vs decision text conflict
]


def http_error(code, retry_after=None, body=b"{}"):
    headers = Message()
    if retry_after:
        headers["Retry-After"] = retry_after
    return HTTPError("https://api2.openreview.net/notes", code, "error", headers, io.BytesIO(body))


def replaced(sub, **content):
    out = json.loads(json.dumps(sub))
    out["content"].update({k: {"value": v} for k, v in content.items()})
    return out


class FakeTransport:
    """Network boundary only. Routes /groups and paged /notes to fixture data."""

    def __init__(self, submissions=SUBMISSIONS, *, groups=None, fail_at=None, count_shift_at=None,
                 before_page=None):
        self.submissions = list(submissions)
        self.before_page = before_page  # Mutates the listing between pages, as a live venue may.
        self.groups = groups or {V: group()}
        self.fail_at = dict(fail_at or {})
        self.count_shift_at = count_shift_at
        self.urls = []

    def get(self, url):
        self.urls.append(url)
        parsed = urlparse(url)
        q = {k: v[0] for k, v in parse_qs(parsed.query).items()}
        if parsed.path == "/groups":
            return json.dumps(self.groups[q["id"]]).encode()
        assert parsed.path == "/notes" and q["details"] == "replies" and q["sort"] == "number:asc"
        offset, limit = int(q["offset"]), int(q["limit"])
        if self.before_page:
            self.before_page(self, offset)
        if offset in self.fail_at:
            raise self.fail_at.pop(offset)
        count = len(self.submissions) + (1 if self.count_shift_at == offset else 0)
        return json.dumps({"count": count, "notes": self.submissions[offset:offset + limit]}).encode()


def harvest(tmp_path, transport, **kwargs):
    labels_api = api()
    with labels_api.Labels(tmp_path / "labels") as labels:
        return labels.harvest([V], transport=transport, page_size=kwargs.pop("page_size", 2), **kwargs)


# --- normalization -----------------------------------------------------------

@pytest.mark.parametrize("raw,decision,status,tier,conflict", [
    (V, "Accept (Oral)", "accepted", "oral", False),
    (V, "Accept (Poster)", "accepted", "poster", False),
    (f"{V}/Rejected_Submission", "Reject", "rejected", None, False),
    (f"{V}/Withdrawn_Submission", None, "withdrawn", None, False),
    (f"{V}/Desk_Rejected_Submission", None, "desk_rejected", None, False),
    (f"{V}/Submission", None, "pending", None, False),
    ("Something/Else", None, "unknown", None, False),
    (None, None, "unknown", None, False),
    (V, "Reject", "accepted", "unknown", True),
    (f"{V}/Rejected_Submission", "Accept (Poster)", "rejected", None, True),
])
def test_status_comes_from_official_venueid_and_conflicts_are_kept(raw, decision, status, tier, conflict):
    m = api()
    cfg = m.venue_config(group())
    result = m.normalize_status(cfg, raw, decision)
    assert (result["status"], result["tier"], result["conflict"]) == (status, tier, conflict)
    assert result["normalizer_version"] == m.NORMALIZER_VERSION
    assert result["status"] != "rejected" or raw == f"{V}/Rejected_Submission"


def test_unsupported_group_is_refused_instead_of_guessing_statuses():
    m = api()
    tmlr = {"groups": [{"id": "TMLR", "content": {"submission_id": {"value": "TMLR/-/Submission"}}}]}
    with pytest.raises(ValueError, match="not supported"):
        m.venue_config(tmlr)


def test_roles_come_from_invitations_and_profiles_are_not_kept():
    m = api()
    cfg = m.venue_config(group())
    sub = SUBMISSIONS[0]
    roles = {m.note_role(cfg, r) for r in sub["details"]["replies"]}
    assert roles == {"review", "decision", "meta_review", "public_comment", "official_comment"}
    assert m.signer_role("~Real_Person1") == "public_user"
    assert m.signer_role(f"{V}/Submission1/Reviewer_r0") == "Reviewer_r0"
    assert m.signer_role(f"{V}/Program_Chairs") == "Program_Chairs"


def test_rating_parses_numbers_and_legacy_text_scales():
    m = api()
    assert m.score(6) == 6
    assert m.score("8: accept, good paper") == 8
    assert m.score("") is None and m.score(None) is None


# --- harvest -------------------------------------------------------------------

def test_full_venue_harvest_stores_every_status_and_completes(tmp_path):
    transport = FakeTransport()
    report = harvest(tmp_path, transport)
    task = report["venues"][0]
    assert task["status"] == "complete" and task["returned"] == 5 and task["total"] == 5
    assert report["status_counts"][V] == {"accepted": 2, "rejected": 1, "withdrawn": 1, "desk_rejected": 1}
    assert report["collection_ok"] is True
    raws = list((tmp_path / "labels" / "raw").glob("*.json"))
    assert len(raws) == 4  # group + 3 pages


def test_failed_page_keeps_cursor_and_resume_finishes(tmp_path):
    transport = FakeTransport(fail_at={1: http_error(500)})
    first = harvest(tmp_path, transport)
    assert first["venues"][0]["status"] == "error" and first["venues"][0]["next_offset"] == 2
    assert first["collection_ok"] is False
    second = harvest(tmp_path, transport)
    assert second["venues"][0]["status"] == "complete" and second["venues"][0]["returned"] == 5
    assert sum(second["status_counts"][V].values()) == 5


def test_count_drift_between_pages_is_an_error_not_silent_loss(tmp_path):
    report = harvest(tmp_path, FakeTransport(count_shift_at=1))
    assert report["venues"][0]["status"] == "error"
    assert "count changed" in report["venues"][0]["error"]
    assert report["venues"][0]["next_offset"] == 2


def test_repeated_submission_across_pages_is_pagination_drift(tmp_path):
    subs = [SUBMISSIONS[0], SUBMISSIONS[1], SUBMISSIONS[1], SUBMISSIONS[2]]
    report = harvest(tmp_path, FakeTransport(subs))
    assert report["venues"][0]["status"] == "error" and "Repeated" in report["venues"][0]["error"]


def test_rate_limit_sets_cooldown_and_stops_later_venues(tmp_path):
    m = api()
    other = "ICLR.cc/2024/Conference"
    transport = FakeTransport(groups={V: group(), other: group(other)},
                              fail_at={0: http_error(429, retry_after="120")})
    with m.Labels(tmp_path / "labels") as labels:
        report = labels.harvest([V, other], transport=transport, page_size=2)
    states = {t["venue_id"]: t["status"] for t in report["venues"]}
    assert states == {V: "error", other: "pending"}
    assert "Retry-After=120" in report["venues"][0]["error"]


def test_challenge_403_is_reported_and_writes_no_submissions(tmp_path):
    body = json.dumps({"name": "ChallengeRequiredError", "message": "Challenge verification required"}).encode()
    report = harvest(tmp_path, FakeTransport(fail_at={0: http_error(403, body=body)}))
    assert report["venues"][0]["status"] == "error"
    assert "ChallengeRequiredError" in report["venues"][0]["error"]
    assert report["status_counts"].get(V, {}) == {}


def test_max_pages_marks_partial_not_complete(tmp_path):
    report = harvest(tmp_path, FakeTransport(), max_pages=1)
    task = report["venues"][0]
    assert task["status"] == "partial" and task["returned"] == 2
    assert report["collection_ok"] is False


# --- export and links -----------------------------------------------------------

def exported(tmp_path, **kwargs):
    harvest(tmp_path, FakeTransport())
    ex = api("forge.vendor.openreview_export")
    m = api()
    out = tmp_path / "project" / "openreview.jsonl"
    with m.Labels(tmp_path / "labels") as labels:
        result = ex.export(labels, out, **kwargs)
    rows = [json.loads(line) for line in out.read_text().splitlines()]
    manifest = json.loads(out.with_suffix(".jsonl.manifest.json").read_text())
    return result, rows, manifest


def test_export_rows_carry_reviews_decisions_and_sources(tmp_path):
    result, rows, manifest = exported(tmp_path)
    assert result["submissions"] == 5
    by_number = {r["number"]: r for r in rows}
    oral = by_number[1]
    assert oral["status"] == "accepted" and oral["tier"] == "oral" and oral["raw_decision"] == "Accept (Oral)"
    assert [r["rating"] for r in oral["reviews"]] == [6, 3]
    assert oral["reviews"][0]["text"]["weaknesses"] == "missing baseline 0"
    assert oral["meta_review"]["text"]["metareview"].startswith("Reviewers want")
    assert oral["source"]["raw_path"].startswith("raw/") and oral["source"]["forum"] == "F1"
    assert by_number[5]["conflict"] is True
    dumped = json.dumps(rows)
    assert "Real_Person1" not in dumped and "Author_One1" not in dumped
    assert manifest["denominators"]["all"][V]["accepted"] == 2
    assert "not a population acceptance rate" in manifest["notice"]


def test_export_filter_keeps_full_denominators_for_comparison(tmp_path):
    _, rows, manifest = exported(tmp_path, primary_area="optimization")
    assert [r["number"] for r in rows] == [2]
    assert manifest["denominators"]["selected"][V] == {"rejected": 1}
    assert sum(manifest["denominators"]["all"][V].values()) == 5
    assert manifest["denominators"]["by_area"][V]["robotics"]["accepted"] == 2


def test_export_query_matches_title_abstract_keywords_and_can_drop_text(tmp_path):
    _, rows, _ = exported(tmp_path, query="policy learning 3", review_text=False)
    assert [r["number"] for r in rows] == [3]
    _, rows, _ = exported(tmp_path, query="robot", review_text=False)
    assert all("text" not in rev for r in rows for rev in r["reviews"])


def test_link_only_proposes_same_work_and_never_moves_labels(tmp_path):
    harvest(tmp_path, FakeTransport())
    ex, m = api("forge.vendor.openreview_export"), api()
    papers = tmp_path / "papers.jsonl"
    papers.write_text(json.dumps({"arxiv_id": "2501.00001", "title": "  paper   2 "}) + "\n"
                      + json.dumps({"arxiv_id": "2501.00002", "title": "Unrelated"}) + "\n")
    with m.Labels(tmp_path / "labels") as labels:
        result = ex.link(labels, papers)
        again = ex.link(labels, papers)
        links = labels.links()
    assert result["proposed"] == 1 and again["proposed"] == 0
    assert links == [{"left_ref": "openreview:F2", "right_ref": "arxiv:2501.00001", "relation": "same_work",
                      "status": "proposed", "method_version": ex.LINK_METHOD,
                      "evidence": {"normalized_title": "paper 2"}}]
    assert json.loads(papers.read_text().splitlines()[0]) == {"arxiv_id": "2501.00001", "title": "  paper   2 "}


def test_export_refuses_to_overwrite_database_or_raw(tmp_path):
    harvest(tmp_path, FakeTransport())
    ex, m = api("forge.vendor.openreview_export"), api()
    with m.Labels(tmp_path / "labels") as labels:
        with pytest.raises(ValueError):
            ex.export(labels, tmp_path / "labels" / "labels.sqlite3")
        with pytest.raises(ValueError):
            ex.export(labels, tmp_path / "labels" / "raw" / "x.jsonl")


def test_credentials_are_read_from_env_file_without_printing(tmp_path, capsys):
    m = api()
    env = tmp_path / ".env"
    env.write_text('# comment\nOPENREVIEW_USERNAME="me@example.org"\nOPENREVIEW_PASSWORD=secret\n')
    assert m.read_credentials(env, environ={}) == ("me@example.org", "secret")
    assert m.read_credentials(None, environ={"OPENREVIEW_USERNAME": "a", "OPENREVIEW_PASSWORD": "b"}) == ("a", "b")
    with pytest.raises(ValueError, match="OPENREVIEW_USERNAME"):
        m.read_credentials(None, environ={})
    assert "secret" not in capsys.readouterr().err


# --- review findings: drift, empty venues, passes, partial exports ---------------

def test_delete_plus_append_keeps_count_but_is_caught_as_shift(tmp_path):
    def shift(t, offset):
        if offset == 1 and t.submissions[0]["id"] == "F1":
            t.submissions = t.submissions[1:] + [submission(6, V, decision="Reject")]
    report = harvest(tmp_path, FakeTransport(before_page=shift))
    task = report["venues"][0]
    assert task["status"] == "error" and "Pagination shifted" in task["error"] and "--refresh" in task["error"]
    assert task["next_offset"] == 2 and report["collection_ok"] is False


def test_zero_submission_venue_is_an_error_not_complete(tmp_path):
    report = harvest(tmp_path, FakeTransport([]))
    assert report["venues"][0]["status"] == "error" and "zero submissions" in report["venues"][0]["error"]


def test_count_drift_message_says_refresh_and_refresh_recovers(tmp_path):
    m = api()
    transport = FakeTransport(count_shift_at=1)
    assert "--refresh" in harvest(tmp_path, transport)["venues"][0]["error"]
    transport.count_shift_at = None
    with m.Labels(tmp_path / "labels") as labels:
        report = labels.harvest([V], transport=transport, page_size=2, refresh=True)
    assert report["venues"][0]["status"] == "complete"


def test_export_reads_one_complete_pass_after_refresh_drops_a_submission(tmp_path):
    m, ex = api(), api("forge.vendor.openreview_export")
    harvest(tmp_path, FakeTransport())
    with m.Labels(tmp_path / "labels") as labels:
        labels.harvest([V], transport=FakeTransport(SUBMISSIONS[1:]), page_size=2, refresh=True)
        result = ex.export(labels, tmp_path / "out.jsonl")
    manifest = json.loads((tmp_path / "out.jsonl.manifest.json").read_text())
    assert result["submissions"] == 4
    assert manifest["denominators"]["all"][V] == {"accepted": 1, "rejected": 1, "withdrawn": 1, "desk_rejected": 1}
    assert manifest["passes"][V]["complete"] is True


def test_failed_refresh_keeps_exporting_the_previous_complete_pass(tmp_path):
    m, ex = api(), api("forge.vendor.openreview_export")
    harvest(tmp_path, FakeTransport())
    changed = [replaced(SUBMISSIONS[0], venueid=f"{V}/Rejected_Submission")] + SUBMISSIONS[1:]
    with m.Labels(tmp_path / "labels") as labels:
        report = labels.harvest([V], transport=FakeTransport(changed, fail_at={1: http_error(500)}),
                                page_size=2, refresh=True)
        assert report["venues"][0]["status"] == "error" and report["venues"][0]["has_complete_pass"] is True
        ex.export(labels, tmp_path / "out.jsonl")
    manifest = json.loads((tmp_path / "out.jsonl.manifest.json").read_text())
    assert manifest["denominators"]["all"][V]["accepted"] == 2  # old pass only, not mixed


def test_partial_harvest_cannot_export_unless_explicitly_allowed(tmp_path):
    m, ex = api(), api("forge.vendor.openreview_export")
    harvest(tmp_path, FakeTransport(), max_pages=1)
    with m.Labels(tmp_path / "labels") as labels:
        with pytest.raises(ValueError, match="no completed pass"):
            ex.export(labels, tmp_path / "out.jsonl")
        result = ex.export(labels, tmp_path / "out.jsonl", allow_partial=True)
    assert result["submissions"] == 2 and result["passes"][V]["complete"] is False


def test_non_string_venueid_is_unknown_and_harvest_still_completes(tmp_path):
    odd = [replaced(SUBMISSIONS[0], venueid=["weird"])] + SUBMISSIONS[1:]
    report = harvest(tmp_path, FakeTransport(odd))
    assert report["venues"][0]["status"] == "complete"
    assert report["status_counts"][V]["unknown"] == 1
    m = api()
    assert m.normalize_status(m.venue_config(group()), None, "Reject")["status"] == "unknown"


def test_invalid_reply_rolls_back_the_whole_page(tmp_path):
    broken = json.loads(json.dumps(SUBMISSIONS[1]))
    del broken["details"]["replies"][0]["id"]
    report = harvest(tmp_path, FakeTransport([SUBMISSIONS[0], broken, *SUBMISSIONS[2:]]))
    assert report["venues"][0]["status"] == "error" and report["venues"][0]["next_offset"] == 0
    m = api()
    with m.Labels(tmp_path / "labels") as labels:
        assert labels.db.execute("SELECT COUNT(*) FROM notes").fetchone()[0] == 0
        assert labels.db.execute("SELECT COUNT(*) FROM observations").fetchone()[0] == 0


def test_running_request_from_a_crash_is_marked_interrupted(tmp_path):
    m = api()
    with m.Labels(tmp_path / "labels") as labels:
        labels.db.execute("INSERT INTO requests VALUES ('r1',?,0,'u','t','running',NULL,NULL,NULL)", (V,))
        labels.db.commit()
    harvest(tmp_path, FakeTransport())
    with m.Labels(tmp_path / "labels") as labels:
        assert labels.db.execute("SELECT status FROM requests WHERE request_id='r1'").fetchone()[0] == "interrupted"


def test_normalized_tables_hold_no_profile_ids(tmp_path):
    harvest(tmp_path, FakeTransport())
    m = api()
    with m.Labels(tmp_path / "labels") as labels:
        dump = "\n".join(" ".join(map(str, row)) for table in ("notes", "observations", "pass_members")
                          for row in labels.db.execute(f"SELECT * FROM {table}"))
    assert "~Real_Person1" not in dump and "Author_One1" not in dump and "public_user" in dump


def test_broken_stderr_does_not_undo_a_committed_page(tmp_path, monkeypatch):
    m = api()

    class Closed:
        def write(self, _):
            raise BrokenPipeError

        def flush(self):
            raise BrokenPipeError

    monkeypatch.setattr(m.sys, "stderr", Closed())
    report = harvest(tmp_path, FakeTransport())
    assert report["venues"][0]["status"] == "complete"


# --- transport: login, token handling, cooldown -------------------------------

class FakeResponse:
    def __init__(self, body):
        self.body = body

    def read(self, _=None):
        return self.body

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


def test_transport_logs_in_once_and_never_writes_the_token(tmp_path, monkeypatch):
    t = api("forge.vendor.openreview_transport")
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setattr(t, "MIN_INTERVAL", 0)
    sent = []

    def fake_urlopen(request, timeout):
        sent.append((request.full_url, request.get_header("Authorization")))
        if request.full_url.endswith("/login"):
            return FakeResponse(json.dumps({"token": "SECRET-TOKEN"}).encode())
        if "/groups" in request.full_url:
            return FakeResponse(json.dumps(group()).encode())
        q = {k: v[0] for k, v in parse_qs(urlparse(request.full_url).query).items()}
        offset, limit = int(q["offset"]), int(q["limit"])
        return FakeResponse(json.dumps({"count": 5, "notes": SUBMISSIONS[offset:offset + limit]}).encode())

    monkeypatch.setattr(t, "urlopen", fake_urlopen)
    report = harvest(tmp_path, t.Transport("me", "pw"))
    assert report["venues"][0]["status"] == "complete"
    assert [u for u, _ in sent].count("https://api2.openreview.net/login") == 1
    assert all(auth == "Bearer SECRET-TOKEN" for u, auth in sent if not u.endswith("/login"))
    stored = b"".join(p.read_bytes() for root in ("labels", "cache") for p in (tmp_path / root).rglob("*") if p.is_file())
    assert b"SECRET-TOKEN" not in stored and b"pw" not in stored


def test_429_writes_shared_cooldown_and_next_call_sends_nothing(tmp_path, monkeypatch):
    t = api("forge.vendor.openreview_transport")
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setattr(t, "MIN_INTERVAL", 0)
    calls = []

    def limited(request, timeout):
        calls.append(request.full_url)
        if request.full_url.endswith("/login"):
            return FakeResponse(b'{"token":"x"}')
        raise http_error(429, retry_after="Wed, 21 Oct 2099 07:28:00 GMT")

    monkeypatch.setattr(t, "urlopen", limited)
    transport = t.Transport("me", "pw")
    with pytest.raises(HTTPError):
        transport.get("https://api2.openreview.net/groups?id=x")
    sent = len(calls)
    with pytest.raises(t.RemoteCooldown):
        transport.get("https://api2.openreview.net/groups?id=x")
    assert len(calls) == sent


def test_torn_lock_file_does_not_wedge_harvests(tmp_path, monkeypatch):
    t = api("forge.vendor.openreview_transport")
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setattr(t, "MIN_INTERVAL", 0)
    t.lock_path().write_text('{"last_fin')
    with t.request_slot():
        pass
    assert "last_finished" in json.loads(t.lock_path().read_text())


def test_env_file_keeps_inner_quotes_and_accepts_export(tmp_path):
    m = api()
    env = tmp_path / ".env"
    env.write_text("export OPENREVIEW_USERNAME=me\nOPENREVIEW_PASSWORD='pa\"ss'\n")
    assert m.read_credentials(env, environ={}) == ("me", 'pa"ss')
