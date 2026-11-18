import json
import os
import pickle
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


class CachePublicationTests(unittest.TestCase):
    def setUp(self):
        cache_root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        (cache_root / "pyproject.toml").touch()
        self.entry = {
            "command": "strategic_reports",
            "params": {"seed": 19},
            "prefix_parts": ["seed19"],
            "schema_version": 1,
            "root": cache_root,
        }
        run_dir, self.data_path = save_cached_run(data={"rounds": 2}, **self.entry)
        self.metadata_path = run_dir / "metadata.json"

    def test_failure_during_staging_preserves_the_previous_run(self):
        previous = load_cached_run(**self.entry)
        with patch("core.cache_utils.json.dump", side_effect=OSError("disk full")):
            with self.assertRaisesRegex(OSError, "disk full"):
                save_cached_run(data={"rounds": 3}, **self.entry)
        self.assertEqual(load_cached_run(**self.entry), previous)
        self.assertEqual(
            sorted(file.name for file in self.data_path.parent.iterdir()),
            ["data.pkl", "metadata.json"],
        )

    def test_replacement_failure_does_not_return_stale_data_with_new_metadata(self):
        replace = Path.replace

        def fail_data_replacement(staged, target):
            if target == self.data_path:
                raise OSError("replacement failed")
            return replace(staged, target)

        with patch.object(Path, "replace", fail_data_replacement):
            with self.assertRaisesRegex(OSError, "replacement failed"):
                save_cached_run(data={"rounds": 3}, **self.entry)
        self.assertEqual(load_cached_run(**self.entry), (None, None))
        self.assertEqual(pickle.loads(self.data_path.read_bytes()), {"rounds": 2})

    def test_loads_legacy_entries_until_a_writer_replaces_the_metadata(self):
        legacy = json.loads(self.metadata_path.read_bytes())
        del legacy["data_sha256"]
        self.metadata_path.write_text(json.dumps(legacy), encoding="utf-8")
        self.assertEqual(load_cached_run(**self.entry), ({"rounds": 2}, legacy))
        original_open = Path.open

        def save_before_opening_data(cache_file, *args, **kwargs):
            if cache_file == self.data_path:
                save_cached_run(data={"rounds": 3}, **self.entry)
            return original_open(cache_file, *args, **kwargs)

        with patch.object(Path, "open", save_before_opening_data):
            self.assertEqual(load_cached_run(**self.entry), (None, None))
        data, metadata = load_cached_run(**self.entry)
        self.assertEqual(data, {"rounds": 3})
        self.assertEqual(len(metadata["data_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
