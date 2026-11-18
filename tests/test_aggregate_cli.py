import io
import json
import unittest
from contextlib import redirect_stdout

from cli.aggregate_cli import main


class AggregateCliTests(unittest.TestCase):
    def test_aggregate_cli_emits_json_with_backend_metadata(self):
        output = io.StringIO()
        with redirect_stdout(output):
            main(
                [
                    "--ballot",
                    "0,1",
                    "--ballot",
                    "0,1",
                    "--ballot",
                    "1,0",
                    "--backend",
                    "auto",
                ]
            )

        result = json.loads(output.getvalue())
        self.assertEqual(result["candidates"], [0, 1])
        self.assertEqual(result["metadata"]["backend_requested"], "auto")
        self.assertEqual(result["metadata"]["backend_used"], "python")


if __name__ == "__main__":
    unittest.main()
