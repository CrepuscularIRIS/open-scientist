"""Suggested signature groups and near-duplicates. Standard-library TF-IDF + average linkage.

Ported idea from Co-Scientist's proximity agent (average-linkage cosine
clustering, 0.92 near-duplicate threshold), without embeddings or API calls.
Output is a *suggestion* for the card-merge step: similarity of wording is not
sameness of mechanism, so every group must be checked against the readings.
"""
from __future__ import annotations

from collections import Counter
import math
import re

WEIGHTS = {"operation": 3, "information": 2, "object": 2, "output": 1, "claimed_effect": 1, "conditions": 1}
STOP = set("""a an and are as at be by for from has have in into is it its of on or that the their this to
using via with we our which can more than not without based each both also these those such over under""".split())
TOKEN = re.compile(r"[a-z0-9]+|[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uac00-\ud7af]+")
CJK = re.compile(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uac00-\ud7af]")
METHOD = "tfidf-smooth-average-linkage-v2"


def tokens(text):
    """Latin words longer than two letters (minus stop words); CJK runs as character bigrams."""
    out = []
    for t in TOKEN.findall(text.lower()):
        if CJK.match(t):
            out += [t[i:i + 2] for i in range(len(t) - 1)] if len(t) > 1 else [t]
        elif len(t) > 2 and t not in STOP:
            out.append(t)
    return out


def document(sig):
    counts = Counter()
    for field, weight in WEIGHTS.items():
        value = sig.get(field)
        text = " ".join(value) if isinstance(value, list) else (value or "")
        for t in tokens(text):
            counts[t] += weight
    return counts


def vectors(docs):
    df = Counter(t for d in docs.values() for t in d)
    n = len(docs)
    out = {}
    for key, d in docs.items():
        # Smoothed IDF (+1): a term every signature shares still counts, so a small or uniform sample does not
        # collapse to empty vectors and identical signatures stay identical.
        vec = {t: (1 + math.log(c)) * (math.log((1 + n) / (1 + df[t])) + 1.0) for t, c in d.items()}
        vec = {t: w for t, w in vec.items() if w > 0}
        norm = math.sqrt(sum(w * w for w in vec.values())) or 1.0
        out[key] = {t: w / norm for t, w in vec.items()}
    return out


def cosine(a, b):
    if len(a) > len(b):
        a, b = b, a
    return sum(w * b.get(t, 0.0) for t, w in a.items())


def suggest(sigs, min_similarity=0.2, duplicate_similarity=0.92):
    """sigs: {sig_id: signature dict with arxiv_id}. Deterministic for a given input."""
    keys = sorted(sigs)
    vecs = vectors({k: document(sigs[k]) for k in keys})
    sim = {(a, b): cosine(vecs[a], vecs[b]) for i, a in enumerate(keys) for b in keys[i + 1:]}

    def pair(a, b):
        return sim[(a, b)] if a < b else sim[(b, a)]

    groups = [[k] for k in keys]
    while len(groups) > 1:
        best, where = -1.0, None
        for i in range(len(groups)):
            for j in range(i + 1, len(groups)):
                avg = sum(pair(a, b) for a in groups[i] for b in groups[j]) / (len(groups[i]) * len(groups[j]))
                if avg > best + 1e-12:
                    best, where = avg, (i, j)
        if best < min_similarity:
            break
        i, j = where
        groups[i] = sorted(groups[i] + groups[j])
        del groups[j]
    groups.sort(key=lambda g: (-len(g), g[0]))
    result = []
    for n, members in enumerate(groups, 1):
        weight = Counter()
        for m in members:
            weight.update(vecs[m])
        cohesion = (sum(pair(a, b) for i, a in enumerate(members) for b in members[i + 1:]) /
                    (len(members) * (len(members) - 1) / 2)) if len(members) > 1 else None
        result.append({"group": f"G{n:02d}", "members": members,
                       "papers": sorted({sigs[m]["arxiv_id"] for m in members}),
                       "top_terms": [t for t, _ in sorted(weight.items(), key=lambda x: (-x[1], x[0]))[:8]],
                       "cohesion": round(cohesion, 4) if cohesion is not None else None})
    duplicates = [{"a": a, "b": b, "similarity": round(s, 4)} for (a, b), s in sorted(sim.items())
                  if s >= duplicate_similarity and sigs[a]["arxiv_id"] != sigs[b]["arxiv_id"]]
    return {"method": METHOD, "min_similarity": min_similarity, "duplicate_similarity": duplicate_similarity,
            "signatures": len(keys), "groups": result, "near_duplicates": duplicates,
            "notice": "Suggested by wording only; confirm shared operation, information and conditions before merging."}
