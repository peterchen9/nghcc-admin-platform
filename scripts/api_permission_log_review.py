#!/usr/bin/env python3
"""Parse API permission report-only log lines into a safe review table."""

from __future__ import annotations

import argparse
import csv
import re
import shlex
import sys
from dataclasses import dataclass
from typing import Iterable, TextIO


LOG_MARKER = "api_permission_report"
REVIEW_FIELDS = ("time", "user_id", "endpoint", "method", "scope", "decision", "reason")
SENSITIVE_TOKENS = (
    "password",
    "token",
    "csrf",
    "cookie",
    "session",
    "authorization",
    "secret",
)
TIMESTAMP_RE = re.compile(
    r"^(?P<time>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)\s+"
)


@dataclass(frozen=True)
class ApiPermissionLogRecord:
    time: str
    user_id: str
    endpoint: str
    method: str
    scope: str
    decision: str
    reason: str

    def as_row(self) -> dict[str, str]:
        return {
            "time": self.time,
            "user_id": self.user_id,
            "endpoint": self.endpoint,
            "method": self.method,
            "scope": self.scope,
            "decision": self.decision,
            "reason": self.reason,
        }


def _extract_time(line: str) -> tuple[str, str]:
    match = TIMESTAMP_RE.match(line)
    if not match:
        return "", line
    return match.group("time"), line[match.end() :]


def _parse_key_values(message: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for token in shlex.split(message):
        if "=" not in token:
            continue
        key, value = token.split("=", 1)
        values[key] = value
    return values


def parse_api_permission_log_line(line: str) -> ApiPermissionLogRecord | None:
    if LOG_MARKER not in line:
        return None

    time, remainder = _extract_time(line.strip())
    marker_index = remainder.find(LOG_MARKER)
    if marker_index == -1:
        return None

    message = remainder[marker_index + len(LOG_MARKER) :].strip()
    values = _parse_key_values(message)
    if values.get("mode") != "report-only":
        return None

    return ApiPermissionLogRecord(
        time=time,
        user_id=values.get("user_id", ""),
        endpoint=values.get("endpoint", ""),
        method=values.get("method", ""),
        scope=values.get("scope", ""),
        decision=values.get("decision", ""),
        reason=values.get("reason", ""),
    )


def iter_api_permission_log_records(lines: Iterable[str]) -> Iterable[ApiPermissionLogRecord]:
    for line in lines:
        record = parse_api_permission_log_line(line)
        if record is not None:
            yield record


def _safe_cell(value: str) -> str:
    lower_value = value.lower()
    if any(token in lower_value for token in SENSITIVE_TOKENS):
        return "[redacted]"
    return value


def write_records(records: Iterable[ApiPermissionLogRecord], output: TextIO) -> int:
    writer = csv.DictWriter(output, fieldnames=REVIEW_FIELDS, extrasaction="ignore")
    writer.writeheader()

    count = 0
    for record in records:
        writer.writerow({key: _safe_cell(value) for key, value in record.as_row().items()})
        count += 1
    return count


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Review report-only API permission logs without exposing request payloads.",
    )
    parser.add_argument(
        "log_file",
        nargs="?",
        help="Optional local log file. Reads stdin when omitted or set to '-'.",
    )
    args = parser.parse_args(argv)

    if args.log_file and args.log_file != "-":
        with open(args.log_file, encoding="utf-8", errors="replace") as handle:
            write_records(iter_api_permission_log_records(handle), sys.stdout)
    else:
        write_records(iter_api_permission_log_records(sys.stdin), sys.stdout)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
