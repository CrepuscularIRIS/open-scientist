"""Deterministic domain assets: baseline registry, timeline, outcome statistics.

These never call a model. When outcome labels are absent the statistics say
so instead of inventing rates; small strata are reported, never promoted.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date
from itertools import combinations

from forge.schemas import papers, signatures
from forge.util import read_json, read_jsonl

POSITIVE, NEGATIVE = {"accepted"}, {"rejected"}


def baselines(layout, reading_ids):
    used = defaultdict(set)
    for aid in reading_ids:
        data = read_json(layout.readings_dir / f"{aid.replace('/', '_')}.json") or {}
        for b in data.get("baselines") or []:
            if isinstance(b, dict) and b.get("name") and b.get("kind"):
                used[(" ".join(b["name"].split()), b["kind"])].add(aid)
    rows = [{"name": n, "kind": k, "used_by": sorted(v), "count": len(v)} for (n, k), v in used.items()]
    rows.sort(key=lambda r: (-r["count"], r["kind"], r["name"].lower()))
    return {"baselines": rows, "readings": len(reading_ids),
            "notice": "Names as written in readings; aliases of one baseline are not merged automatically."}


def _month(published):
    return published[:7] if isinstance(published, str) and len(published) >= 7 else None


def _months_between(a, b):
    ya, ma = map(int, a.split("-"))
    yb, mb = map(int, b.split("-"))
    return (yb - ya) * 12 + (mb - ma)


def timeline(layout, reading_ids):
    """Per-card growth from member papers' first-version dates, relative to the corpus end."""
    corpus = papers(layout)
    months = sorted(m for m in (_month(p.get("published")) for p in corpus.values()) if m)
    end = months[-1] if months else date.today().isoformat()[:7]
    index = read_json(layout.cards_dir / "index.json") or {"cards": []}
    sigs = signatures(layout, reading_ids)
    cards = {}
    for card in index["cards"]:
        member_papers = sorted({sigs[s]["arxiv_id"] for s in card.get("members", []) if s in sigs})
        dates = sorted(m for m in (_month(corpus.get(a, {}).get("published")) for a in member_papers) if m)
        recent = sum(1 for m in dates if _months_between(m, end) < 12)
        cards[card["card_id"]] = {"papers": len(member_papers), "first": dates[0] if dates else None,
                                  "last": dates[-1] if dates else None, "last_12_months": recent,
                                  "recent_share": round(recent / len(dates), 3) if dates else None,
                                  "by_year": dict(sorted(Counter(m[:4] for m in dates).items()))}
    by_year = dict(sorted(Counter(m[:4] for m in months).items()))
    return {"corpus_end": end, "corpus_papers": len(corpus), "corpus_by_year": by_year, "cards": cards,
            "notice": "Counts are over this domain's sampled corpus, not the whole field."}


def submission_events(layout):
    """One row per submission event (paper, venue, year, track); an exact repeat of an event replaces the earlier row."""
    events = {}
    for row in read_jsonl(layout.file("labels.jsonl")):
        if not str(row.get("paper_ref", "")).startswith("arxiv:"):
            continue
        key = (row["paper_ref"], row.get("venue"), row.get("year"), row.get("track"))
        events[key] = {**row, "arxiv_id": row["paper_ref"].split(":", 1)[1]}
    return list(events.values())


def _tally(events):
    c = Counter(e["outcome"] for e in events)
    decided = c["accepted"] + c["rejected"]
    return {"events": len(events), "papers": len({e["arxiv_id"] for e in events}), "counts": dict(c), "decided": decided,
            "positive_rate": round(c["accepted"] / decided, 4) if decided else None}


def _delta(t, base):
    if t["positive_rate"] is None or base["positive_rate"] is None:
        return None
    return round(100 * (t["positive_rate"] - base["positive_rate"]), 2)


def outcome_stats(layout, reading_ids, min_n=30, delta_pp=-12.0):
    """Outcome tallies over submission events. A paper rejected at one venue and accepted at another counts twice.

    A combination is flagged only inside one venue-year stratum (same venue, same year), where acceptance rates are
    comparable; pooled numbers are descriptive. Outcomes measure passing review, not whether a mechanism works.
    """
    index = read_json(layout.cards_dir / "index.json") or {"cards": []}
    qualitative = [{"card_id": c["card_id"], "text": f["text"], "refs": f.get("refs", [])}
                   for c in index["cards"] for f in c.get("failure_modes", [])]
    sigs = signatures(layout, reading_ids)
    paper_cards = defaultdict(set)
    for card in index["cards"]:
        for s in card.get("members", []):
            if s in sigs:
                paper_cards[sigs[s]["arxiv_id"]].add(card["card_id"])
    events = [e for e in submission_events(layout) if e["arxiv_id"] in paper_cards]
    if not events:
        return {"status": "no_outcome_labels", "qualitative_candidates": qualitative,
                "notice": "No outcome labels for read papers; failure modes are reading-derived candidates, not statistics."}

    def with_cards(evs, cards):
        return [e for e in evs if set(cards) <= paper_cards[e["arxiv_id"]]]

    strata = defaultdict(list)
    for e in events:
        strata[(e.get("venue"), e.get("year"))].append(e)
    base = _tally(events)
    single = {c["card_id"]: _tally(with_cards(events, [c["card_id"]])) for c in index["cards"]}
    pairs = sorted({pair for cs in paper_cards.values() for pair in combinations(sorted(cs), 2)})
    combos = []
    for pair in pairs:
        per_stratum = []
        for (venue, year), evs in sorted(strata.items(), key=str):
            t, b = _tally(with_cards(evs, pair)), _tally(evs)
            if not t["events"]:
                continue
            d = _delta(t, b)
            flag = ("anti_pattern_candidate" if t["decided"] >= min_n and d is not None and d <= delta_pp
                    else "insufficient_n" if t["decided"] < min_n else "no_signal")
            per_stratum.append({"venue": venue, "year": year, **t, "stratum_rate": b["positive_rate"], "delta_pp": d, "flag": flag})
        pooled = _tally(with_cards(events, pair))
        flagged = [r for r in per_stratum if r["flag"] == "anti_pattern_candidate"]
        combos.append({"cards": list(pair), "pooled": {**pooled, "delta_pp": _delta(pooled, base)}, "strata": per_stratum,
                       "flag": "anti_pattern_candidate" if flagged else
                       "insufficient_n" if all(r["flag"] == "insufficient_n" for r in per_stratum) else "no_signal"})
    return {"status": "labeled", "unit": "submission_event", "base": base, "cards": single, "combos": combos,
            "strata": [{"venue": v, "year": y, **_tally(evs)} for (v, y), evs in sorted(strata.items(), key=str)],
            "thresholds": {"min_n": min_n, "delta_pp": delta_pp, "flag_scope": "within one venue-year stratum"},
            "qualitative_candidates": qualitative,
            "notice": "Counts are submission events of read papers (a resubmission is a second event). Flags compare a "
                      "combination with its own venue-year stratum; pooled deltas mix venues and years and are "
                      "descriptive only. Accept/reject measures passing review, not whether a mechanism works; "
                      "papers from one research family are not independent instances."}
