"""Tests for LogAnalyzer parsing and error-fallback behavior."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, mock_open

from core.log_analyzer import LogAnalyzer


class TestLogAnalyzerParseLog(unittest.TestCase):
    def _make_analyzer(self, tmpdir: str) -> LogAnalyzer:
        return LogAnalyzer(tmpdir)

    def test_parse_log_returns_fallback_on_os_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "log.txt"
            log_path.write_text("Error: something\n", encoding="utf-8")

            analyzer = self._make_analyzer(tmpdir)
            with patch("builtins.open", side_effect=OSError("permission denied")):
                entries = analyzer.parse_log()

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["type"], "ERROR")
        self.assertEqual(entries[0]["human_title"], "Analyzer Failure")

    def test_parse_log_translates_known_error_pattern(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "log.txt"
            log_path.write_text(
                "Error: Invalid mod name 'FS25 BadMod'!\n",
                encoding="utf-8",
            )

            analyzer = self._make_analyzer(tmpdir)
            entries = analyzer.parse_log()

        error_entries = [e for e in entries if e["type"] == "ERROR"]
        self.assertTrue(len(error_entries) >= 1)
        matched = next(
            (e for e in error_entries if e["human_title"] == "Invalid Mod File Name"),
            None,
        )
        self.assertIsNotNone(matched, "Expected 'Invalid Mod File Name' entry")
        self.assertIn("FS25 BadMod", matched["human_msg"])  # type: ignore[index]

    def test_parse_log_returns_info_for_plain_lines(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "log.txt"
            log_path.write_text(
                "Loading map assets...\nInitializing vehicles...\n",
                encoding="utf-8",
            )

            analyzer = self._make_analyzer(tmpdir)
            entries = analyzer.parse_log()

        self.assertTrue(all(e["type"] == "INFO" for e in entries))
        self.assertEqual(len(entries), 2)

    def test_translate_line_returns_unknown_for_unmatched_error(self) -> None:
        analyzer = LogAnalyzer("/tmp")
        result = analyzer._translate_line("Error: some completely unknown problem xyz")

        self.assertEqual(result["type"], "ERROR")
        self.assertEqual(result["human_title"], "Unrecognised Error")
        # The original game message must survive, not be replaced by a
        # generic sentence that tells the user nothing.
        self.assertIn("some completely unknown problem xyz", result["human_msg"])

    def test_parse_log_returns_empty_when_log_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            # Do NOT create log.txt
            analyzer = LogAnalyzer(tmpdir)
            # Also ensure the static fallback path doesn't exist
            analyzer.log_path = Path(tmpdir) / "log.txt"
            entries = analyzer.parse_log()

        self.assertEqual(entries, [])


if __name__ == "__main__":
    unittest.main()


class TestLogAnalyzerSummarize(unittest.TestCase):
    def _analyzer_with(self, tmpdir: str, lines: str) -> LogAnalyzer:
        with open(os.path.join(tmpdir, "log.txt"), "w", encoding="utf-8") as fh:
            fh.write(lines)
        return LogAnalyzer(tmpdir)

    def test_groups_repeated_issues_and_counts_severities(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            analyzer = self._analyzer_with(tmp, "\n".join([
                "Just an info line",
                "Error: Invalid mod name 'FS25 BadMod'!",
                "Error: Invalid mod name 'FS25 BadMod'!",
                "Error: Invalid mod name 'FS25 BadMod'!",
                "Warning: Duplicate lua script 'gps.lua'",
            ]) + "\n")

            report = analyzer.summarize()
            self.assertEqual(report["errors"], 3)
            self.assertEqual(report["warnings"], 1)
            # Three identical errors collapse into one grouped issue.
            self.assertEqual(len(report["issues"]), 2)
            self.assertEqual(report["issues"][0]["type"], "ERROR")
            self.assertEqual(report["issues"][0]["count"], 3)
            self.assertEqual(report["info_lines"], ["Just an info line"])

    def test_reports_nothing_when_log_is_clean(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = self._analyzer_with(tmp, "all good\nstill fine\n").summarize()
            self.assertEqual(report["issues"], [])
            self.assertEqual(report["errors"], 0)
            self.assertEqual(report["total_lines"], 2)

    def test_recognises_controller_mapping_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            analyzer = self._analyzer_with(
                tmp,
                "  Error: Failed to read button mapping in file "
                "C:/users/steamuser/Documents/inputDevices/HoriTruckControlWheel.xml\n",
            )
            issue = analyzer.summarize()["issues"][0]
            self.assertEqual(issue["human_title"], "Controller Mapping Skipped")
            self.assertIn("HoriTruckControlWheel.xml", issue["human_msg"])
