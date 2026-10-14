# logsum

Tiny stdlib-only Python CLI that summarizes plain-text log files.

## Why

Quick triage of a log without loading it into a tool: how many lines per level,
what time range it covers, and which errors repeat most. Variable parts of error
messages (numbers, hex values, UUIDs) are replaced with placeholders
(`<N>`, `<HEX>`, `<UUID>`) so similar errors group together.

## Install

```
pip install .        # provides the `logsum` command
# or run directly: python3 logsum.py FILE...
```

## Usage

```
logsum [--top N] [--json] [FILE...]     # reads stdin if no files
```

- Levels (DEBUG, INFO, WARN, WARNING, ERROR, CRITICAL, FATAL) are matched case-insensitively as whole tokens.
- Timestamps: ISO-8601 like `2026-10-07T12:00:00` or `2026-10-07 12:00:00`.
- Error messages come from ERROR/CRITICAL/FATAL lines (timestamp and level removed).

Sample (`example.log` in this repo):

```
$ logsum example.log
Lines: 6
Levels:
  DEBUG    1
  INFO     1
  WARN     1
  ERROR    2
  FATAL    1
First timestamp: 2026-10-07T12:00:00
Last timestamp:  2026-10-07 12:04:00
Top 5 error messages:
      2  failed to connect to db<N>:<N> id=<UUID>
      1  out of memory at <HEX>
```

JSON: `logsum --json --top 1 < example.log` prints `total_lines`, `levels`,
`first_timestamp`, `last_timestamp` and `top_errors` (list of `{message, count}`).

## Tests

```
python3 -m unittest discover -s tests
```

## Related tools

- [jsonlq](https://github.com/hal5000-openclaw/jsonlq) – query JSONL files
- [jsonldiff](https://github.com/hal5000-openclaw/jsonldiff) – diff JSONL files
- [envcheck](https://github.com/hal5000-openclaw/envcheck) – validate .env files

## License

MIT
