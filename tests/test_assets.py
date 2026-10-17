"""Exercise the asset importer with real git repositories and byte mutations."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "import_assets.py"
RS_SKILL = "ResearchStudio-Idea/skills/idea_spark/SKILL.md"
RC_SKILL = "skills/research-companion/SKILL.md"


class AssetImportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.sources = self.root / "sources"
        self.dest = self.root / "plugin"
        fixtures = {
            "ResearchStudio": [RS_SKILL, "ResearchStudio-Idea/skills/idea_spark/references/system-prompts/generate.txt", "ResearchStudio-Idea/skills/paper_search/SKILL.md", "ResearchStudio-Idea/skills/scoop_check/SKILL.md", "ResearchStudio-Idea/evaluation/idea_quality/SKILL.md"],
            "research-companion": ["agents/brainstormer.md", "principles/research-strategy.md", RC_SKILL, "codex-skills/research-companion/SKILL.md"],
            "Co-Scientist": ["plugin/skills/evolving-hypotheses/SKILL.md", "plugin/skills/evolving-hypotheses/reference/combine.md", "config/prompts/evolution_combine.md"],
        }
        for repo, paths in fixtures.items():
            folder = self.sources / repo
            for rel in paths + ["LICENSE"]:
                path = folder / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(("Original paragraph for " + rel + "\r\n原始段落\r\n").encode())
            self.git(folder, "init", "-q")
            self.git(folder, "add", ".")
            self.git(folder, "-c", "user.name=Asset Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "fixture")
        self.dirty_bytes = b"Retain local edits verbatim.\r\n\x00\xff\n"
        (self.sources / "research-companion" / RC_SKILL).write_bytes(self.dirty_bytes)

    @staticmethod
    def git(folder, *args):
        return subprocess.run(["git", "-C", str(folder), *args], check=True, capture_output=True).stdout.decode().strip()

    def run_cli(self, action, *, sources=True):
        command = [sys.executable, str(SCRIPT), action, "--destination", str(self.dest)]
        if sources:
            command += ["--source-root", str(self.sources)]
        return subprocess.run(command, capture_output=True, text=True)

    def imported(self):
        result = self.run_cli("import")
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads((self.dest / "docs/source-manifest.json").read_text())

    def test_import_preserves_dirty_bytes_and_provenance(self):
        """Catches reading HEAD instead of worktree and newline/encoding conversion."""
        manifest = self.imported()
        entry = next(f for f in manifest["files"] if f["source_repo"] == "research-companion" and f["source_path"] == RC_SKILL)
        self.assertEqual((self.dest / entry["archive_path"]).read_bytes(), self.dirty_bytes)
        self.assertEqual(entry["sha256"], hashlib.sha256(self.dirty_bytes).hexdigest())
        self.assertTrue(entry["dirty"])
        self.assertEqual(entry["source_commit"], self.git(self.sources / "research-companion", "rev-parse", "HEAD"))
        clean = next(f for f in manifest["files"] if f["source_path"] == RS_SKILL)
        self.assertFalse(clean["dirty"])
        self.assertEqual(self.run_cli("check").returncode, 0)

    def test_import_is_deterministic_and_check_is_portable(self):
        """Catches timestamps in manifests and check depending on absent source repos."""
        self.imported()
        original = (self.dest / "docs/source-manifest.json").read_bytes()
        self.imported()
        self.assertEqual((self.dest / "docs/source-manifest.json").read_bytes(), original)
        self.assertEqual(self.run_cli("check", sources=False).returncode, 0)

    def test_check_detects_tampered_or_missing_archive(self):
        """Catches validators that only count names rather than checking bytes."""
        manifest = self.imported()
        target = self.dest / manifest["files"][0]["archive_path"]
        target.write_bytes(b"silently rewritten")
        result = self.run_cli("check", sources=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("sha256", result.stderr)
        target.unlink()
        self.assertNotEqual(self.run_cli("check", sources=False).returncode, 0)

    def test_check_detects_removed_manifest_entry(self):
        """Catches a manifest that silently drops an archived source file."""
        manifest = self.imported()
        manifest["files"].pop()
        (self.dest / "docs/source-manifest.json").write_text(json.dumps(manifest))
        self.assertNotEqual(self.run_cli("check", sources=False).returncode, 0)

    def test_check_sources_detects_missing_entry_and_archive_together(self):
        """Catches omission of an entire selected source asset from the archive."""
        manifest = self.imported()
        entry = next(f for f in manifest["files"] if f["source_path"] == RS_SKILL)
        manifest["files"].remove(entry)
        (self.dest / entry["archive_path"]).unlink()
        (self.dest / "docs/source-manifest.json").write_text(json.dumps(manifest))
        self.assertNotEqual(self.run_cli("check").returncode, 0)

    def test_check_detects_missing_license_copy_and_source_drift(self):
        """Catches incomplete attribution packaging and unnoticed source edits."""
        manifest = self.imported()
        entry = next(f for f in manifest["files"] if f["source_repo"] == "ResearchStudio" and f["source_path"] == "LICENSE")
        (self.dest / entry["license_copy_path"]).unlink()
        self.assertNotEqual(self.run_cli("check", sources=False).returncode, 0)
        self.imported()
        (self.sources / "ResearchStudio" / RS_SKILL).write_bytes(b"changed after snapshot")
        self.assertNotEqual(self.run_cli("check").returncode, 0)
        self.assertEqual(self.run_cli("check", sources=False).returncode, 0)

    def test_missing_required_source_fails_before_copy(self):
        """Catches a partial import presented as successful when a required skill is absent."""
        (self.sources / "ResearchStudio" / RS_SKILL).unlink()
        self.assertNotEqual(self.run_cli("import").returncode, 0)
        self.assertFalse((self.dest / "docs/source-manifest.json").exists())

    def test_check_rejects_manifest_path_escape(self):
        """Catches trusting manifest paths outside the package."""
        manifest = self.imported()
        outside = self.root / "outside.txt"
        outside.write_bytes(b"outside")
        manifest["files"][0]["archive_path"] = "../outside.txt"
        manifest["files"][0]["sha256"] = hashlib.sha256(b"outside").hexdigest()
        (self.dest / "docs/source-manifest.json").write_text(json.dumps(manifest))
        self.assertNotEqual(self.run_cli("check", sources=False).returncode, 0)


class ShippedAssetTests(unittest.TestCase):
    def test_taxonomy_index_resolves_all_46_original_cards(self):
        """Catches omitted taxonomy assets or broken retrieval links in the shipped index."""
        root = SCRIPT.parent.parent
        index = root / "references/patterns/INDEX.md"
        self.assertTrue(index.is_file(), "missing complete pattern retrieval index")
        links = dict(re.findall(r"^\[([^\]]+)\]: (\S+)$", index.read_text(), re.M))
        expected = {f"C{n:02d}" for n in range(31)} | {
            "assumption_audit_and_pivot", "architectural_operator_substitution",
            "generative_process_redesign", "controlled_diagnostic_design",
            "unify_into_shared_representation", "reframe_as_solvable_object",
            "self_supervised_signal_engineering", "structural_prior_encoding",
            "algebraic_equivalence_unification", "heterogeneous_decomposition",
            "decompose_and_delegate", "relax_discrete_search_to_continuous",
            "adapt_via_conditioning", "characterize_limit_then_surpass",
            "targeted_self_supervised_objective",
        }
        self.assertTrue(expected <= links.keys(), expected - links.keys())
        for name in expected:
            target = (index.parent / links[name]).resolve()
            self.assertTrue(target.is_file(), name)
            self.assertTrue(target.is_relative_to(root / "vendor"), name)
            self.assertEqual(target.stem, name)


if __name__ == "__main__":
    unittest.main()
