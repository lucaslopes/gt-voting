import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.cache_utils import get_command_cache_dir, get_run_path, load_cached_run, save_cached_run


class InstalledCachePathTests(unittest.TestCase):
    def test_saved_cache_uses_the_same_fallback_path_as_lookup(self):
        params = {"backend": "rust", "seed": 19}
        prefix_parts = ["backend-rust", "seed19"]
        payload = {"result": [0.25, 0.75]}

        with tempfile.TemporaryDirectory(prefix="gtiv-installed-cache-") as temp_dir:
            foreign_checkout = Path(temp_dir) / "foreign-checkout"
            installed_core = foreign_checkout / ".venv" / "site-packages" / "core"
            installed_core.mkdir(parents=True)
            (foreign_checkout / "pyproject.toml").touch()
            simulated_module = installed_core / "cache_utils.py"
            user_cache = Path(temp_dir) / "user-cache"

            with (
                patch("core.cache_utils.__file__", str(simulated_module)),
                patch("core.cache_utils._user_cache_dir", return_value=user_cache),
                patch.dict(os.environ, {"GTIV_CACHE_DIR": ""}),
            ):
                expected_run_dir = get_run_path(
                    command="strategic_reports",
                    params=params,
                    prefix_parts=prefix_parts,
                )
                saved_run_dir, data_path = save_cached_run(
                    command="strategic_reports",
                    params=params,
                    prefix_parts=prefix_parts,
                    schema_version=1,
                    data=payload,
                )
                loaded, metadata = load_cached_run(
                    command="strategic_reports",
                    params=params,
                    prefix_parts=prefix_parts,
                    schema_version=1,
                )

            self.assertEqual(saved_run_dir, expected_run_dir)
            self.assertEqual(saved_run_dir.parent, user_cache / "strategic_reports_runs")
            self.assertEqual(data_path, expected_run_dir / "data.pkl")
            self.assertEqual(loaded, payload)
            self.assertEqual(metadata["params"], params)
            self.assertTrue((expected_run_dir / "metadata.json").is_file())
            self.assertFalse((installed_core / "data").exists())
            self.assertFalse((foreign_checkout / "data").exists())

    def test_source_checkout_and_cache_override(self):
        with tempfile.TemporaryDirectory(prefix="gtiv-source-cache-") as temp_dir:
            checkout = Path(temp_dir).resolve() / "checkout"
            (checkout / "core").mkdir(parents=True)
            (checkout / "pyproject.toml").touch()
            original = checkout / "data" / "rankings_runs"
            override = Path(temp_dir) / "override"

            with patch("core.cache_utils.__file__", str(checkout / "core" / "cache_utils.py")):
                with patch.dict(os.environ, {"GTIV_CACHE_DIR": ""}):
                    self.assertEqual(get_command_cache_dir("rankings"), original)
                with patch.dict(os.environ, {"GTIV_CACHE_DIR": str(override)}):
                    self.assertEqual(
                        get_command_cache_dir("rankings"), override.resolve() / "rankings_runs"
                    )
                    self.assertEqual(get_command_cache_dir("rankings", root=checkout), original)


if __name__ == "__main__":
    unittest.main()
