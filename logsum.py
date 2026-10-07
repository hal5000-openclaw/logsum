"""logsum - summarize plain-text log files (stdlib only)."""
import argparse
import json
import re
import sys
from collections import Counter

__version__ = "0.1.0"

LEVELS = ["DEBUG", "INFO", "WARN", "WARNING", "ERROR", "CRITICAL", "FATAL"]
ERROR_LEVELS = {"ERROR", "CRITICAL", "FATAL"}

LEVEL_RE = re.compile(r"(?<![A-Za-z0-9_])(" + "|".join(LEVELS) + r")(?![A-Za-z0-9_])", re.I)
TS_RE = re.compile(
    r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?(?:Z|[+-]\d{2}:?\d{2})?"
)
UUID_RE = re.compile(
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
)
HEX_RE = re.compile(r"\b0[xX][0-9a-fA-F]+\b|\b(?=[0-9a-fA-F]*\d)(?=[0-9a-fA-F]*[a-fA-F])[0-9a-fA-F]{8,}\b")
NUM_RE = re.compile(r"\d+")


def normalize(msg):
    """Replace UUIDs, hex values and digits with placeholders."""
    msg = UUID_RE.sub("<UUID>", msg)
    msg = HEX_RE.sub("<HEX>", msg)
    msg = NUM_RE.sub("<N>", msg)
    return " ".join(msg.split())


def summarize(lines):
    levels = Counter()
    errors = Counter()
    first = last = None
    total = 0
    for line in lines:
        line = line.rstrip("\r\n")
        total += 1
        ts = TS_RE.search(line)
        if ts:
            key = ts.group(0).replace(" ", "T")
            if first is None or key < first[0]:
                first = (key, ts.group(0))
            if last is None or key >= last[0]:
                last = (key, ts.group(0))
        m = LEVEL_RE.search(line)
        if not m:
            continue
        level = m.group(1).upper()
        levels[level] += 1
        if level in ERROR_LEVELS:
            rest = line[: m.start()] + " " + line[m.end():]
            if ts:
                rest = rest.replace(ts.group(0), " ", 1)
            rest = rest.strip(" \t-:[]|")
            errors[normalize(rest) or "(empty message)"] += 1
    return {
        "total_lines": total,
        "levels": {l: levels[l] for l in LEVELS if levels[l]},
        "first_timestamp": first[1] if first else None,
        "last_timestamp": last[1] if last else None,
        "errors": errors,
    }


def format_text(s, top):
    out = [f"Lines: {s['total_lines']}", "Levels:"]
    if s["levels"]:
        for l, c in s["levels"].items():
            out.append(f"  {l:<9}{c}")
    else:
        out.append("  (none)")
    out.append(f"First timestamp: {s['first_timestamp'] or '-'}")
    out.append(f"Last timestamp:  {s['last_timestamp'] or '-'}")
    out.append(f"Top {top} error messages:")
    common = s["errors"].most_common(top)
    if not common:
        out.append("  (none)")
    for msg, c in common:
        out.append(f"  {c:>5}  {msg}")
    return "\n".join(out)


def main(argv=None):
    p = argparse.ArgumentParser(prog="logsum", description="Summarize plain-text log files.")
    p.add_argument("files", nargs="*", help="log files (default: stdin)")
    p.add_argument("--top", type=int, default=5, metavar="N", help="top N error messages (default 5)")
    p.add_argument("--json", action="store_true", help="JSON output")
    p.add_argument("--version", action="version", version=__version__)
    args = p.parse_args(argv)
    if args.top < 0:
        p.error("--top must be >= 0")

    def gen():
        if not args.files or args.files == ["-"]:
            yield from sys.stdin
            return
        for name in args.files:
            with open(name, encoding="utf-8", errors="replace") as f:
                yield from f

    try:
        s = summarize(gen())
    except OSError as e:
        print(f"logsum: {e}", file=sys.stderr)
        return 2
    if args.json:
        s = dict(s)
        s["top_errors"] = [{"message": m, "count": c} for m, c in s.pop("errors").most_common(args.top)]
        print(json.dumps(s, indent=2))
    else:
        print(format_text(s, args.top))
    return 0


if __name__ == "__main__":
    sys.exit(main())
