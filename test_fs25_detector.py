"""Tests for FS25 install detection."""
import tempfile
import unittest
from pathlib import Path

from core.fs25_detector import FS25Detector


def _make_fs25_data(root: Path) -> Path:
    """Create a directory that looks like FS25 user data."""
    root.mkdir(parents=True, exist_ok=True)
    (root / "mods").mkdir()
    return root


class TestDetectorScan(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def _patch_roots(self, steam_roots, common_paths=()):
        orig_steam = FS25Detector.STEAM_ROOTS
        orig_common = FS25Detector.COMMON_PATHS
        FS25Detector.STEAM_ROOTS = [str(p) for p in steam_roots]
        FS25Detector.COMMON_PATHS = [str(p) for p in common_paths]

        def restore():
            FS25Detector.STEAM_ROOTS = orig_steam
            FS25Detector.COMMON_PATHS = orig_common

        self.addCleanup(restore)

    def test_finds_data_inside_proton_prefix(self):
        steam = self.tmp / "steam"
        prefix = steam / "steamapps" / "compatdata" / "2300320"
        data = _make_fs25_data(prefix / FS25Detector.PREFIX_DATA_SUFFIX)
        self._patch_roots([steam])

        self.assertEqual(FS25Detector.search(), [str(data)])
        self.assertEqual(FS25Detector.find_user_data_path(), str(data))

    def test_follows_extra_library_from_libraryfolders_vdf(self):
        steam = self.tmp / "steam"
        (steam / "steamapps").mkdir(parents=True)
        other = self.tmp / "second_drive"
        (other / "steamapps" / "compatdata" / "2300320").mkdir(parents=True)
        data = _make_fs25_data(
            other / "steamapps" / "compatdata" / "2300320" / FS25Detector.PREFIX_DATA_SUFFIX
        )
        (steam / "steamapps" / "libraryfolders.vdf").write_text(
            '"libraryfolders"\n{\n\t"0"\n\t{\n\t\t"path"\t\t"%s"\n\t}\n}\n' % other,
            encoding="utf-8",
        )
        self._patch_roots([steam])

        self.assertEqual(FS25Detector.search(), [str(data)])

    def test_reports_progress_and_honours_cancel(self):
        steam = self.tmp / "steam"
        compatdata = steam / "steamapps" / "compatdata"
        for app_id in ("1", "2", "3"):
            _make_fs25_data(compatdata / app_id / FS25Detector.PREFIX_DATA_SUFFIX)
        self._patch_roots([steam])

        seen = []

        def progress(done, total, path):
            seen.append((done, total, path))
            return done < 2  # cancel partway through

        found = FS25Detector.search(progress=progress)
        self.assertEqual(len(seen), 2)
        self.assertEqual(seen[0][1], 3)
        self.assertEqual(len(found), 1)

    def test_finds_data_under_a_localised_documents_folder(self):
        steam = self.tmp / "steam"
        prefix = steam / "steamapps" / "compatdata" / "2300320"
        data = _make_fs25_data(
            prefix / "pfx/drive_c/users/steamuser/Dokumente/My Games/FarmingSimulator2025"
        )
        self._patch_roots([steam])

        self.assertEqual(FS25Detector.search(), [str(data)])

    def test_returns_nothing_when_no_install_exists(self):
        self._patch_roots([self.tmp / "absent"])
        self.assertEqual(FS25Detector.search(), [])
        self.assertIsNone(FS25Detector.find_user_data_path())

    def test_finds_game_install_from_app_manifest(self):
        steam = self.tmp / "steam"
        steamapps = steam / "steamapps"
        steamapps.mkdir(parents=True)
        install = steamapps / "common" / "Farming Simulator 25"
        install.mkdir(parents=True)
        (steamapps / "appmanifest_2300320.acf").write_text(
            '"AppState"\n{\n\t"appid"\t\t"2300320"\n\t"installdir"\t\t"Farming Simulator 25"\n}\n',
            encoding="utf-8",
        )
        self._patch_roots([steam])

        self.assertEqual(FS25Detector.find_game_install(), str(install))

    def test_game_install_is_none_when_not_installed(self):
        self._patch_roots([self.tmp / "absent"])
        self.assertIsNone(FS25Detector.find_game_install())

    def test_validate_path_requires_an_fs25_indicator(self):
        empty = self.tmp / "empty"
        empty.mkdir()
        self.assertFalse(FS25Detector.validate_path(str(empty)))
        self.assertFalse(FS25Detector.validate_path(""))
        self.assertTrue(FS25Detector.validate_path(str(_make_fs25_data(self.tmp / "real"))))


if __name__ == "__main__":
    unittest.main()
