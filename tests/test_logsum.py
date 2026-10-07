import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import logsum

SAMPLE = """\
2026-10-07T12:00:00 INFO started
2026-10-07 12:00:05 debug cache warm
2026-10-07 12:01:00 WARN slow query 120ms
2026-10-07 12:02:00 ERROR failed to connect to db1:5432 id=550e8400-e29b-41d4-a716-446655440000
2026-10-07 12:03:00 ERROR failed to connect to db2:5433 id=123e4567-e89b-12d3-a456-426614174000
2026-10-07 12:04:00 FATAL out of memory at 0xdeadbeef
no level here
"""


def run(args, stdin=None):
    buf = io.StringIO()
    old = sys.stdin
    if stdin is not None:
        sys.stdin = io.StringIO(stdin)
    try:
        with redirect_stdout(buf):
            rc = logsum.main(args)
    finally:
        sys.stdin = old
    return rc, buf.getvalue()


class Tests(unittest.TestCase):
    def test_level_counts_case_insensitive(self):
        s = logsum.summarize(SAMPLE.splitlines())
        self.assertEqual(s["levels"], {"DEBUG": 1, "INFO": 1, "WARN": 1, "ERROR": 2, "FATAL": 1})
        self.assertEqual(s["total_lines"], 7)

    def test_level_is_token_not_substring(self):
        s = logsum.summarize(["information about errors", "INFO: ok"])
        self.assertEqual(s["levels"], {"INFO": 1})

    def test_timestamps(self):
        s = logsum.summarize(SAMPLE.splitlines())
        self.assertEqual(s["first_timestamp"], "2026-10-07T12:00:00")
        self.assertEqual(s["last_timestamp"], "2026-10-07 12:04:00")

    def test_no_timestamps(self):
        s = logsum.summarize(["ERROR x"])
        self.assertIsNone(s["first_timestamp"])

    def test_normalize(self):
        self.assertEqual(
            logsum.normalize("id 550e8400-e29b-41d4-a716-446655440000 at 0xdeadbeef port 80"),
            "id <UUID> at <HEX> port <N>",
        )

    def test_errors_grouped(self):
        s = logsum.summarize(SAMPLE.splitlines())
        top = s["errors"].most_common(1)[0]
        self.assertEqual(top[1], 2)
        self.assertEqual(top[0], "failed to connect to db<N>:<N> id=<UUID>")

    def test_json_and_top_via_stdin(self):
        rc, out = run(["--json", "--top", "1"], stdin=SAMPLE)
        self.assertEqual(rc, 0)
        d = json.loads(out)
        self.assertEqual(len(d["top_errors"]), 1)
        self.assertEqual(d["top_errors"][0]["count"], 2)

    def test_file_and_missing_file(self):
        with tempfile.NamedTemporaryFile("w", suffix=".log", delete=False) as f:
            f.write(SAMPLE)
        try:
            rc, out = run([f.name])
            self.assertEqual(rc, 0)
            self.assertIn("ERROR", out)
        finally:
            os.unlink(f.name)
        self.assertEqual(run(["/nonexistent/x.log"])[0], 2)


if __name__ == "__main__":
    unittest.main()
