#!/usr/bin/env python3
"""Check portable active Markdown references, excluding historical vendor data."""
import argparse
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit


def check_links(root: Path) -> list[str]:
    root = root.resolve()
    documents = list(root.glob("*.md"))
    for directory in ("skills", "references", "docs", "examples"):
        documents.extend((root / directory).rglob("*.md"))
    errors = []
    for doc in documents:
        text = re.sub(r"(?ms)^\s*(```|~~~).*?^\s*\1[^\n]*$", "", doc.read_text())
        for link in re.finditer(r"\[[^\]]*\]\((<[^>]+>|[^)\s]+)(?:\s+[^)]*)?\)", text):
            raw = link.group(1).strip("<>")
            parsed = urlsplit(raw)
            if parsed.scheme or not parsed.path:
                continue
            target = (doc.parent / unquote(parsed.path)).resolve()
            if not target.is_relative_to(root):
                errors.append(f"{doc.relative_to(root)}: outside package: {raw}")
            elif not target.exists():
                errors.append(f"{doc.relative_to(root)}: missing target: {raw}")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    errors = check_links(args.root)
    print(json.dumps({"ok": not errors, "errors": errors}, ensure_ascii=False, indent=2))
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
