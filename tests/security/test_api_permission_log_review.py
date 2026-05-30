import csv
import importlib.util
import io
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
PARSER_PATH = ROOT_DIR / "scripts" / "api_permission_log_review.py"
SPEC = importlib.util.spec_from_file_location("api_permission_log_review", PARSER_PATH)
api_permission_log_review = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = api_permission_log_review
SPEC.loader.exec_module(api_permission_log_review)


def test_parse_report_only_log_line_extracts_review_fields():
    line = (
        "2026-05-30T08:12:44.123Z web-1 | api_permission_report "
        "mode=report-only endpoint=/api/hymns/ method=POST scope=api:hymns:write "
        "user_id=123 user_authenticated=True user_is_superuser=False "
        "decision=deny reason=missing_scope"
    )

    record = api_permission_log_review.parse_api_permission_log_line(line)

    assert record.as_row() == {
        "time": "2026-05-30T08:12:44.123Z",
        "user_id": "123",
        "endpoint": "/api/hymns/",
        "method": "POST",
        "scope": "api:hymns:write",
        "decision": "deny",
        "reason": "missing_scope",
    }


def test_parse_ignores_non_report_only_and_unrelated_lines():
    lines = [
        "api_permission_report mode=enforce endpoint=/api/hymns/ method=POST "
        "scope=api:hymns:write user_id=123 decision=deny reason=missing_scope",
        "ordinary application log line",
        "api_permission_report mode=report-only endpoint=/api/humnos/download/ "
        "method=POST scope=api:humnos:write user_id=456 decision=allow reason=explicit_scope",
    ]

    records = list(api_permission_log_review.iter_api_permission_log_records(lines))

    assert len(records) == 1
    assert records[0].endpoint == "/api/humnos/download/"
    assert records[0].decision == "allow"
    assert records[0].reason == "explicit_scope"


def test_write_records_outputs_only_safe_review_columns():
    lines = [
        "api_permission_report mode=report-only endpoint=/api/hymns/ method=POST "
        "scope=api:hymns:write user_id=123 user_authenticated=True "
        "user_is_superuser=False decision=deny reason=missing_scope "
        "password=secret token=secret csrfmiddlewaretoken=secret"
    ]
    output = io.StringIO()

    count = api_permission_log_review.write_records(
        api_permission_log_review.iter_api_permission_log_records(lines),
        output,
    )

    assert count == 1
    rows = list(csv.DictReader(io.StringIO(output.getvalue())))
    assert list(rows[0].keys()) == [
        "time",
        "user_id",
        "endpoint",
        "method",
        "scope",
        "decision",
        "reason",
    ]
    assert rows[0] == {
        "time": "",
        "user_id": "123",
        "endpoint": "/api/hymns/",
        "method": "POST",
        "scope": "api:hymns:write",
        "decision": "deny",
        "reason": "missing_scope",
    }
    assert "secret" not in output.getvalue()
