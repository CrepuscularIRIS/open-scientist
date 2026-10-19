"""Behavior tests for bounded retrieval; fixtures never contact the network."""
import importlib.util
from contextlib import closing
from http.client import IncompleteRead
import io
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "forge/search.py"
ATOM = b'''<feed xmlns="http://www.w3.org/2005/Atom"
 xmlns:arxiv="http://arxiv.org/schemas/atom"
 xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/">
 <opensearch:totalResults>1</opensearch:totalResults>
 <entry><id>http://arxiv.org/abs/2501.12345v2</id>
 <title>Memory Selection for Agents</title><published>2025-01-20T00:00:00Z</published>
 <summary>A retrieval mechanism.</summary><author><name>A. Author</name></author>
 <arxiv:doi>10.1234/example</arxiv:doi>
 <link href="http://arxiv.org/pdf/2501.12345v2" type="application/pdf"/>
 </entry></feed>'''


def make_db(path):
    with closing(sqlite3.connect(path)) as conn:
        conn.executescript('''CREATE TABLE papers (
          id INTEGER PRIMARY KEY, title TEXT, abstract TEXT, authors TEXT,
          venue TEXT, year INTEGER, url TEXT, pdf_path TEXT, corpus TEXT,
          keywords TEXT, title_source TEXT, abstract_source TEXT);
          CREATE VIRTUAL TABLE papers_fts USING fts5(title, abstract, keywords,
            authors, content='papers', content_rowid='id');''')
        conn.executemany("INSERT INTO papers VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", [
            (1, "Memory Selection for Agents", "A retrieval mechanism.", '["A. Author"]',
             "ICLR", 2025, "https://arxiv.org/abs/2501.12345v1", "/data/example.pdf",
             "fixture", "memory", "metadata", "metadata"),
            (2, "Memory in 2020", "memory older", '[]', "ICML", 2020,
             "https://example.org/old", "", "fixture", "", "metadata", ""),
            (3, "Vision only", "unrelated", '[]', "CVPR", 2025,
             "https://example.org/vision", "", "fixture", "", "metadata", ""),
        ])
        conn.execute("INSERT INTO papers_fts(papers_fts) VALUES ('rebuild')")
        conn.commit()


class SearchTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(MODULE.exists(), "search adapter has not been implemented")
        spec = importlib.util.spec_from_file_location("search_adapter_under_test", MODULE)
        self.search = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.search)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / "papers.db"
        make_db(self.db)

    def test_missing_index_does_not_create_database_or_claim_empty(self):
        missing = Path(self.temp.name) / "missing.db"
        result = self.search.search_local("memory", db_path=missing)
        self.assertEqual(result["status"], "missing_index")
        self.assertFalse(missing.exists())

    def test_local_query_filters_year_caps_results_and_does_not_write(self):
        before = self.db.read_bytes()
        result = self.search.search_local("memory", db_path=self.db, start_year=2024,
                                          end_year=2026, max_papers=1)
        self.assertEqual(result["status"], "ok")
        self.assertEqual([p["title"] for p in result["papers"]], ["Memory Selection for Agents"])
        self.assertEqual(result["papers"][0]["pdf_path"], "/data/example.pdf")
        self.assertEqual(self.db.read_bytes(), before)

    def test_no_hits_is_distinct_from_bad_schema(self):
        self.assertEqual(self.search.search_local("nonexistentzq", db_path=self.db)["status"], "empty")
        broken = Path(self.temp.name) / "broken.db"
        sqlite3.connect(broken).close()
        self.assertEqual(self.search.search_local("memory", db_path=broken)["status"], "error")

    def test_keyword_quotes_cannot_inject_fts_or_sql(self):
        result = self.search.search_local('memory"; DROP TABLE papers; --', db_path=self.db)
        self.assertEqual(result["status"], "empty")
        with closing(sqlite3.connect(self.db)) as conn:
            self.assertEqual(conn.execute("SELECT count(*) FROM papers").fetchone()[0], 3)

    def test_arxiv_atom_parsing_and_query_bounds(self):
        with patch.object(self.search, "urlopen", return_value=io.BytesIO(ATOM)) as network:
            result = self.search.search_arxiv("memory selection", start_year=2024,
                                             end_year=2026, max_papers=3)
        self.assertEqual(result["status"], "ok")
        paper = result["papers"][0]
        self.assertEqual(paper["arxiv_id"], "2501.12345")
        self.assertEqual(paper["doi"], "10.1234/example")
        self.assertEqual(paper["authors"], ["A. Author"])
        from urllib.parse import parse_qs, urlparse
        params = parse_qs(urlparse(network.call_args.args[0].full_url).query)
        self.assertEqual(params["max_results"], ["3"])
        self.assertIn("submittedDate:[202401010000 TO 202612312359]", params["search_query"][0])

    def test_arxiv_empty_malformed_and_failures_stay_distinct(self):
        cases = [
            (io.BytesIO(b'<feed xmlns="http://www.w3.org/2005/Atom"/>'), None, "empty"),
            (io.BytesIO(b'<html>proxy login</html>'), None, "unavailable"),
            (None, TimeoutError("slow"), "timeout"),
            (None, URLError("offline"), "unavailable"),
            (None, HTTPError("https://export.arxiv.org", 429, "limit", {}, None), "rate_limited"),
        ]
        for response, error, expected in cases:
            with self.subTest(expected=expected), patch.object(
                    self.search, "urlopen", return_value=response, side_effect=error):
                self.assertEqual(self.search.search_arxiv("memory")["status"], expected)

    def test_atom_missing_required_metadata_is_not_success(self):
        incomplete = b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>https://arxiv.org/abs/2501.12345</id></entry></feed>'
        with patch.object(self.search, "urlopen", return_value=io.BytesIO(incomplete)):
            result = self.search.search(["memory"], sources=["arxiv"])
        self.assertEqual(result["sources"]["arxiv"]["status"], "unavailable")
        self.assertTrue(result["coverage"]["partial"])

    def test_null_title_cannot_crash_dedup_or_discard_other_results(self):
        result = self.search.deduplicate([
            {"title": None, "url": "https://example.org/paper", "provenance": []},
            {"title": "Known title", "provenance": []},
        ])
        self.assertEqual(len(result), 2)
        self.assertEqual(result[1]["title"], "Known title")

    def test_local_record_missing_title_reports_error_not_complete_metadata(self):
        with closing(sqlite3.connect(self.db)) as conn:
            conn.execute("UPDATE papers SET title=NULL WHERE id=1")
            conn.execute("INSERT INTO papers_fts(papers_fts) VALUES ('rebuild')")
            conn.commit()
        result = self.search.search_local("retrieval", db_path=self.db)
        self.assertEqual(result["status"], "error")

    def test_default_sources_deduplicate_versions_and_keep_provenance(self):
        with patch.object(self.search, "urlopen", return_value=io.BytesIO(ATOM)):
            result = self.search.search(["memory selection"], db_path=self.db)
        self.assertEqual(set(result["sources"]), {"local", "arxiv"})
        self.assertEqual(len(result["papers"]), 1)
        self.assertEqual({p["source"] for p in result["papers"][0]["provenance"]}, {"local", "arxiv"})
        self.assertFalse(result["coverage"]["partial"])

    def test_one_failed_source_preserves_local_results_and_partial_coverage(self):
        with patch.object(self.search, "urlopen", side_effect=TimeoutError("slow")):
            result = self.search.search(["memory"], db_path=self.db)
        self.assertEqual(result["sources"]["arxiv"]["status"], "timeout")
        self.assertEqual(result["sources"]["local"]["status"], "ok")
        self.assertEqual(len(result["papers"]), 2)
        self.assertTrue(result["coverage"]["partial"])
        self.assertEqual(result["coverage"]["failed_sources"], ["arxiv"])

    def test_incomplete_http_body_preserves_other_source_results(self):
        with patch.object(self.search, "urlopen", side_effect=IncompleteRead(b"<feed", 100)):
            result = self.search.search(["memory"], db_path=self.db)
        self.assertEqual(result["sources"]["arxiv"]["status"], "unavailable")
        self.assertEqual(len(result["papers"]), 2)

    def test_cli_cannot_overwrite_the_local_index_with_its_report(self):
        before = self.db.read_bytes()
        proc = subprocess.run([sys.executable, str(ROOT / "scripts/search_papers.py"),
                               "--queries", "memory", "--sources", "local", "--json", str(self.db)],
                              env=dict(os.environ, PAPER_SEARCH_LOCAL_DB=str(self.db)),
                              text=True, capture_output=True)
        self.assertNotEqual(proc.returncode, 0)
        self.assertEqual(self.db.read_bytes(), before)

    def test_dedup_doi_and_title_retains_each_source_reference(self):
        papers = [
            {"title": "Old title", "doi": "https://doi.org/10.1234/EXAMPLE", "provenance": [{"source": "local", "record_id": "1"}]},
            {"title": "Revised title", "doi": "10.1234/example", "provenance": [{"source": "arxiv", "record_id": "2"}]},
            {"title": "Revised-title!", "provenance": [{"source": "local", "record_id": "3"}]},
        ]
        result = self.search.deduplicate(papers)
        self.assertEqual(len(result), 1)
        self.assertEqual(len(result[0]["provenance"]), 3)

    def test_empty_is_not_a_novelty_claim(self):
        result = self.search.search(["nonexistentzq"], sources=["local"], db_path=self.db)
        self.assertEqual(result["sources"]["local"]["status"], "empty")
        self.assertEqual(result["papers"], [])
        self.assertEqual(result["evidence_status"], "retrieval_only")
        self.assertIn("does not establish novelty", result["coverage"]["note"])

    def test_b02_empty_local_and_arxiv_429_remain_unresolved_retrieval(self):
        limit = HTTPError("https://export.arxiv.org", 429, "rate limit", {}, None)
        with patch.object(self.search, "urlopen", side_effect=limit):
            result = self.search.search(["nonexistentzq"], db_path=self.db)
        self.assertEqual(result["sources"]["local"]["status"], "empty")
        self.assertEqual(result["sources"]["arxiv"]["status"], "rate_limited")
        self.assertEqual(result["papers"], [])
        self.assertEqual(result["evidence_status"], "retrieval_only")
        self.assertTrue(result["coverage"]["partial"])

    def test_invalid_bounds_are_rejected_before_search(self):
        for kwargs in ({"max_papers": 0}, {"start_year": 2026, "end_year": 2020},
                       {"sources": ["semantic_scholar"]}, {"budget_seconds": 0}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.search.search(["memory"], db_path=self.db, **kwargs)

    def test_cli_works_from_another_directory_and_saves_json(self):
        output = Path(self.temp.name) / "result.json"
        env = dict(os.environ, PAPER_SEARCH_LOCAL_DB=str(self.db))
        proc = subprocess.run([sys.executable, str(ROOT / "scripts/search_papers.py"),
                               "--queries", "memory selection|vision", "--sources", "local",
                               "--max-papers", "2", "--start-year", "2024", "--json", str(output)],
                              cwd=self.temp.name, env=env, text=True, capture_output=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertEqual(data, json.loads(output.read_text()))
        self.assertEqual(len(data["papers"]), 2)


if __name__ == "__main__":
    unittest.main()
