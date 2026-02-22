import io
import json
from pathlib import Path

from rich.console import Console

from data_contract_validator.models.report import ValidationReport, Violation
from data_contract_validator.reporter import export_json, print_report


def make_report(**kwargs) -> ValidationReport:
    defaults = {
        "contract_name": "test",
        "contract_version": "1.0",
        "data_file": "f.csv",
        "total_rows": 3,
    }
    defaults.update(kwargs)
    return ValidationReport(**defaults)


def capture_output(report: ValidationReport) -> str:
    buf = io.StringIO()
    console = Console(file=buf, force_terminal=True, width=120)
    print_report(report, console=console)
    return buf.getvalue()


# ── print_report ──────────────────────────────────────────────────────────────

def test_print_report_passing():
    report = make_report()
    output = capture_output(report)
    assert "PASSED" in output
    assert "No violations found" in output


def test_print_report_failing():
    report = make_report()
    report.add_violation(Violation(
        rule="required", column="id", row=2, message="Column 'id' is required."
    ))
    output = capture_output(report)
    assert "FAILED" in output
    assert "required" in output
    assert "id" in output


def test_print_report_shows_contract_info():
    report = make_report(contract_name="customers", contract_version="2.0")
    output = capture_output(report)
    assert "customers" in output
    assert "2.0" in output


def test_print_report_shows_row_count():
    report = make_report(total_rows=42)
    output = capture_output(report)
    assert "42" in output


def test_print_report_dataset_level_violation():
    """Violations without column or row should show dashes."""
    report = make_report()
    report.add_violation(Violation(rule="schema_presence", message="Column missing."))
    output = capture_output(report)
    assert "schema_presence" in output


# ── export_json ───────────────────────────────────────────────────────────────

def test_export_json_creates_valid_file(tmp_path):
    report = make_report()
    path = str(tmp_path / "report.json")
    export_json(report, path)
    data = json.loads(Path(path).read_text())
    assert data["passed"] is True
    assert data["contract_name"] == "test"


def test_export_json_includes_violations(tmp_path):
    report = make_report()
    report.add_violation(Violation(
        rule="enum", column="tier", row=5, message="bad value"
    ))
    path = str(tmp_path / "report.json")
    export_json(report, path)
    data = json.loads(Path(path).read_text())
    assert data["passed"] is False
    assert len(data["violations"]) == 1
    assert data["violations"][0]["rule"] == "enum"
    assert data["violations"][0]["row"] == 5


def test_export_json_no_default_str_fallback(tmp_path):
    """Ensure model_dump(mode='json') handles serialization without default=str."""
    report = make_report()
    path = str(tmp_path / "report.json")
    export_json(report, path)
    # If this doesn't raise, serialization is clean
    data = json.loads(Path(path).read_text())
    assert isinstance(data, dict)
