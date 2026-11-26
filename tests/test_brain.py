"""Regression tests for defensive search, writeup coverage and remediation data."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from brain_core import ROOT
from brain_core.advisories import format_advisory, get_advisory
from brain_core.audit import audit_writeups
from brain_core.catalog import check_notes, load_notes, normalize, rank_notes
from brain_core.markdown import relative_links


class CatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.notes = load_notes(ROOT)

    def test_reference_queries(self):
        cases = [
            ("mass assignment", None, "api-mass-assignment"),
            ("BOPLA", None, "api-mass-assignment"),
            ("CWE-915", "technique", "api-mass-assignment"),
            ("API5:2023", "technique", "api-function-authorization"),
            ("function level authorization", None, "api-function-authorization"),
            ("OpenAPI", "tool", "spectral"),
            ("shadow API", None, "api-inventory"),
            ("API9:2023", "technique", "api-inventory"),
            ("SSPP", None, "api-parameter-pollution"),
            ("CWE-235", None, "api-parameter-pollution"),
            ("CWE-434", "technique", "file-upload"),
            ("file upload", "playbook", "file-upload-review"),
            ("WINDOWS EVENT LOGS", "tool", "windows-event-logs"),
            ("PCAP", "tool", "wireshark"),
            ("Kerberos", "technique", "directory-access-review"),
            ("systemd", "technique", "host-privilege-review"),
            ("Docker", "technique", "container-isolation"),
            ("credential reuse", "technique", "secret-handling"),
            ("segméntation", "technique", "network-segmentation"),
            ("CISA KEV", "playbook", "vulnerability-remediation"),
        ]
        for query, kind, expected in cases:
            with self.subTest(query=query, kind=kind):
                hits = rank_notes(self.notes.values(), normalize(query), kind)
                self.assertIn(expected, [note.id for note in hits[:3]])

    def test_catalog_and_all_writeup_headers(self):
        self.assertEqual(check_notes(ROOT, self.notes), [])
        audit = audit_writeups(ROOT, self.notes)
        self.assertEqual(audit["errors"], [])
        self.assertEqual(audit["missing_reports"], [])
        self.assertEqual(audit["reports"], len(list((ROOT / "writeups").rglob("*.md"))))
        portswigger_count = len(list((ROOT / "writeups" / "PortSwigger").rglob("*.md")))
        self.assertEqual(
            audit["by_platform"]["PortSwigger"],
            {"writeups": portswigger_count, "reports": portswigger_count},
        )
        self.assertTrue(any("parameter-pollution" in path for path in audit["limited_sources"]))

    def test_duplicate_ids_fail_validation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for folder in ("tools", "techniques"):
                directory = root / "defense" / folder
                directory.mkdir(parents=True)
                (directory / "same-id.md").write_text(
                    "# Example\n\n<!-- tags: example -->\n\nOverview.\n", encoding="utf-8",
                )
            with self.assertRaisesRegex(ValueError, "duplicate note ID"):
                load_notes(root)

    def test_relative_links_skip_code_images_and_remote_links(self):
        lines = [
            "````md", "[Ignored](example.md)", "```", "[Also ignored](a.md)", "````",
            "[Real](<two%20words.md#section>)", "![Image](image.png)", "[Web](https://example.org)",
        ]
        self.assertEqual(list(relative_links("\n".join(lines))), [(6, "two words.md")])


class AdvisoryTests(unittest.TestCase):
    def test_source_details_and_offline_cache(self):
        cve = "CVE-2030-1234"
        nvd = {"vulnerabilities": [{"cve": {
            "id": cve, "lastModified": "2030-01-02", "cisaExploitAdd": "2030-01-03",
            "cisaRequiredAction": "Apply updates.", "references": [{"url": "https://example.invalid"}],
            "configurations": [{"nodes": [{"cpeMatch": [
                {"criteria": "cpe:2.3:a:vendor:example:*:*:*:*:*:*:*:*", "vulnerable": True,
                 "versionEndExcluding": "2.0"},
                {"criteria": "ignored-platform-condition", "vulnerable": False},
            ]}]}],
        }}]}
        github = [{
            "ghsa_id": "GHSA-abcd-1234-efgh", "cve_id": cve, "withdrawn_at": None,
            "vulnerabilities": [{"package": {"ecosystem": "pip", "name": "example"},
                                 "vulnerable_version_range": "< 2.0",
                                 "first_patched_version": {"identifier": "2.0"}}],
        }]
        with tempfile.TemporaryDirectory() as temp, patch.dict(os.environ, BRAIN_CACHE_DIR=temp):
            with patch("brain_core.advisories.fetch_json", side_effect=[nvd, github]) as fetch:
                online = get_advisory(cve, refresh=True)
                self.assertIn("cveId=" + cve, fetch.call_args_list[0].args[0])
                self.assertIn("cve_id=" + cve, fetch.call_args_list[1].args[0])
            with patch("brain_core.advisories.fetch_json") as fetch:
                offline = get_advisory(cve, refresh=False)
                fetch.assert_not_called()
            with patch("brain_core.advisories.fetch_json", side_effect=OSError("offline")):
                retry = get_advisory(cve, refresh=True)
                self.assertEqual(retry["data"], online["data"])
                self.assertEqual(len(retry["warnings"]), 2)
        self.assertEqual(offline["data"], online["data"])
        self.assertEqual(online["data"]["nvd"]["details"]["kev_added"], "2030-01-03")
        self.assertEqual(online["data"]["github"]["details"][0]["first_patched_version"], "2.0")
        text = format_advisory(offline)
        self.assertIn("versionEndExcluding=2.0", text)
        self.assertIn("first patched 2.0", text)
        self.assertNotIn("example.invalid", text)


class CommandTests(unittest.TestCase):
    def invoke(self, *args, expected=0):
        with tempfile.TemporaryDirectory() as temp:
            result = subprocess.run(
                [sys.executable, "-B", str(ROOT / "brain.py"), *args], cwd=temp,
                text=True, encoding="utf-8", capture_output=True, timeout=15,
                env={**os.environ, "BRAIN_CACHE_DIR": temp, "PYTHONIOENCODING": "utf-8"},
            )
        self.assertEqual(result.returncode, expected, result.stderr)
        return result.stdout

    def test_search_show_and_exit_codes(self):
        results = json.loads(self.invoke("defense", "search", "CWE-915", "--limit", "1", "--json"))
        self.assertEqual(results[0]["id"], "api-mass-assignment")
        self.assertIn("## Mitigation", self.invoke("defense", "show", "api-mass-assignment"))
        self.assertEqual(json.loads(self.invoke("defense", "search", "nomatch021", "--json", expected=1)), [])
        self.invoke("defense", "search", "--limit", "0", expected=2)
        self.invoke("defense", "show", "../README", expected=1)

    def test_default_advisory_and_legacy_dispatch(self):
        offline = json.loads(self.invoke("defense", "advisory", "cve-2021-44228", "--json"))
        self.assertEqual(offline["cve"], "CVE-2021-44228")
        self.assertEqual(offline["data"], {})
        self.invoke("defense", "advisory", "invalid", expected=2)
        self.assertIn("writeups", self.invoke("--color=never", "stats"))
