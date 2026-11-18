import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.cache_utils import get_run_path, load_cached_run, save_cached_run


class InstalledCachePathTests(unittest.TestCase):
    def test_saved_cache_uses_the_same_fallback_path_as_lookup(self):
        params = {"backend": "rust", "seed": 19}
        prefix_parts = ["backend-rust", "seed19"]
        payload = {"result": [0.25, 0.75]}

        with tempfile.TemporaryDirectory(prefix="gtiv-installed-cache-") as temp_dir:
            installed_core = Path(temp_dir) / "site-packages" / "core"
            installed_core.mkdir(parents=True)
            simulated_module = installed_core / "cache_utils.py"

            with patch("core.cache_utils.__file__", str(simulated_module)):
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
            self.assertEqual(data_path, expected_run_dir / "data.pkl")
            self.assertEqual(loaded, payload)
            self.assertEqual(metadata["params"], params)
            self.assertTrue((expected_run_dir / "metadata.json").is_file())


if __name__ == "__main__":
    unittest.main()
