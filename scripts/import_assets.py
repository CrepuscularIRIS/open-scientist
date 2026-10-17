#!/usr/bin/env python3
"""Archive selected source documents byte-for-byte; verify without executing them.

Only import writes files. Check works offline; --source-root additionally checks
scope completeness and equality against the current local source checkouts.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys


SOURCES = {
    "ResearchStudio": {
        "slug": "research-studio", "license": "MIT",
        "paths": [
            "ResearchStudio-Idea/skills/idea_spark/references",
            "ResearchStudio-Idea/skills/idea_spark/SKILL.md",
            "ResearchStudio-Idea/skills/paper_search/SKILL.md",
            "ResearchStudio-Idea/skills/scoop_check/SKILL.md",
            "ResearchStudio-Idea/evaluation/idea_quality/SKILL.md",
        ],
    },
    "research-companion": {
        "slug": "research-companion", "license": "MIT",
        "paths": ["agents", "principles", "skills/research-companion/SKILL.md",
                  "codex-skills/research-companion/SKILL.md"],
    },
    "Co-Scientist": {
        "slug": "co-scientist", "license": "Apache-2.0",
        "paths": ["plugin/skills", "config/prompts"],
    },
}


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True,
                          capture_output=True).stdout.decode().strip()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def safe_path(root, relative):
    rel = PurePosixPath(relative)
    if rel.is_absolute() or ".." in rel.parts or not rel.parts:
        raise ValueError(f"invalid relative path: {relative}")
    target = root.joinpath(*rel.parts)
    if not target.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"path escapes package: {relative}")
    return target


def collect(source_root):
    """Validate the complete required source scope before any archive writes."""
    entries, repositories, content = [], [], {}
    for name, spec in SOURCES.items():
        repo = source_root / name
        commit = git(repo, "rev-parse", "HEAD")
        paths = set()
        notices = sorted(p.name for p in repo.iterdir()
                         if p.is_file() and (p.name == "NOTICE" or p.name.startswith("NOTICE.")))
        scope = [*spec["paths"], "LICENSE", *notices]
        for relative in scope:
            path = safe_path(repo, relative)
            if path.is_symlink() or not path.exists():
                raise ValueError(f"missing or linked required source: {name}/{relative}")
            found = sorted(p for p in path.rglob("*") if p.is_file()) if path.is_dir() else [path]
            if not found:
                raise ValueError(f"empty required source directory: {name}/{relative}")
            for member in found:
                if member.is_symlink() or not member.resolve().is_relative_to(repo.resolve()):
                    raise ValueError(f"linked source is not archivable: {member}")
                paths.add(member.relative_to(repo).as_posix())
        repositories.append({"source_repo": name, "source_commit": commit,
                             "dirty": bool(git(repo, "status", "--porcelain")),
                             "license": spec["license"], "source_scope": scope})
        for relative in sorted(paths):
            data = (repo / relative).read_bytes()
            archive = f"vendor/{spec['slug']}/{relative}"
            entry = {"source_repo": name, "source_commit": commit,
                     "source_path": relative,
                     "dirty": bool(git(repo, "status", "--porcelain", "--", relative)),
                     "sha256": sha(data), "bytes": len(data), "archive_path": archive}
            if relative == "LICENSE" or relative in notices:
                entry["license_copy_path"] = f"licenses/{spec['slug']}/{relative}"
                content[entry["license_copy_path"]] = data
            content[archive] = data
            entries.append(entry)
    manifest = {"schema_version": 1, "archive_mode": "verbatim-working-tree",
                "repositories": repositories, "files": entries}
    return manifest, content


def import_assets(source_root, destination):
    manifest, content = collect(source_root)
    # Resolve every output path before writing, including existing symlinks.
    targets = [(safe_path(destination, rel), data) for rel, data in content.items()]
    manifest_path = safe_path(destination, "docs/source-manifest.json")
    for target, data in targets:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def check_assets(destination, source_root=None):
    manifest = json.loads((destination / "docs/source-manifest.json").read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1 or manifest.get("archive_mode") != "verbatim-working-tree":
        raise ValueError("unsupported manifest schema or archive mode")
    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        raise ValueError("manifest has no source files")
    expected_paths, keys, license_repos = set(), set(), set()
    for entry in files:
        name, relative = entry["source_repo"], entry["source_path"]
        if name not in SOURCES:
            raise ValueError(f"unknown source repository: {name}")
        safe_path(destination, relative)
        key = (name, relative)
        if key in keys:
            raise ValueError(f"duplicate source entry: {key}")
        keys.add(key)
        required_archive = f"vendor/{SOURCES[name]['slug']}/{relative}"
        if entry["archive_path"] != required_archive:
            raise ValueError(f"invalid archive mapping: {entry['archive_path']}")
        paths = [entry["archive_path"]]
        if relative == "LICENSE" or relative == "NOTICE" or relative.startswith("NOTICE."):
            required_copy = f"licenses/{SOURCES[name]['slug']}/{relative}"
            if entry.get("license_copy_path") != required_copy:
                raise ValueError(f"missing license copy mapping: {name}/{relative}")
            paths.append(required_copy)
            if relative == "LICENSE":
                license_repos.add(name)
        for relative_output in paths:
            path = safe_path(destination, relative_output)
            if not path.is_file():
                raise ValueError(f"missing archived file: {relative_output}")
            data = path.read_bytes()
            if sha(data) != entry["sha256"] or len(data) != entry["bytes"]:
                raise ValueError(f"sha256/size mismatch: {relative_output}")
            expected_paths.add(relative_output)
    if license_repos != set(SOURCES):
        raise ValueError("manifest must retain a source LICENSE for all three repositories")
    actual_paths = set()
    for spec in SOURCES.values():
        for prefix in [f"vendor/{spec['slug']}", f"licenses/{spec['slug']}"]:
            root = safe_path(destination, prefix)
            actual_paths.update(p.relative_to(destination).as_posix()
                                for p in root.rglob("*") if p.is_file())
    if actual_paths != expected_paths:
        raise ValueError(f"unlisted or missing archive files: {sorted(actual_paths ^ expected_paths)}")
    if source_root is not None:
        current, _ = collect(source_root)
        current_files = {(f["source_repo"], f["source_path"]): f for f in current["files"]}
        if set(current_files) != keys:
            raise ValueError("source scope differs from manifest (missing or extra source entries)")
        for entry in files:
            current_entry = current_files[(entry["source_repo"], entry["source_path"])]
            if entry != current_entry:
                raise ValueError(f"source bytes or provenance changed: {entry['source_repo']}/{entry['source_path']}")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["import", "check"])
    parser.add_argument("--source-root", type=Path,
                        help="directory containing ResearchStudio, research-companion and Co-Scientist")
    parser.add_argument("--destination", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        if args.action == "import":
            if args.source_root is None:
                parser.error("import requires --source-root")
            result = import_assets(args.source_root, args.destination)
        else:
            result = check_assets(args.destination, args.source_root)
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as exc:
        print(f"asset {args.action} failed: {exc}", file=sys.stderr)
        return 1
    print(f"{args.action}: {len(result['files'])} source files; "
          f"{sum(f['bytes'] for f in result['files'])} bytes verified/preserved")
    return 0


if __name__ == "__main__":
    sys.exit(main())
