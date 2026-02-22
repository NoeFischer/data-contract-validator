import datetime

import pytest

from data_contract_validator.checks.type_checks import check_types
from data_contract_validator.models.contract import DataContract
from data_contract_validator.models.report import ValidationReport


def make_contract(col_name: str, col_type: str, fmt: str | None = None) -> DataContract:
    col = {"name": col_name, "type": col_type}
    if fmt:
        col["format"] = fmt
    return DataContract.model_validate({
        "contract": {"name": "test", "version": "1.0"},
        "schema": {"columns": [col]},
    })


def make_report() -> ValidationReport:
    return ValidationReport(contract_name="test", contract_version="1.0", data_file="f.csv")


def run(col_type: str, values: list[str], fmt: str | None = None):
    contract = make_contract("x", col_type, fmt)
    rows = [{"x": v} for v in values]
    report = make_report()
    coerced = check_types(rows, contract, {"x"}, report)
    return coerced, report


# ── string ────────────────────────────────────────────────────────────────────

def test_string_passes_anything():
    coerced, report = run("string", ["hello", "123", ""])
    assert report.passed is True
    assert coerced[0]["x"] == "hello"
    assert coerced[1]["x"] == "123"
    assert coerced[2]["x"] is None  # empty string -> None


def test_string_whitespace_only_is_null():
    coerced, report = run("string", ["  ", "\t"])
    assert report.passed is True
    assert coerced[0]["x"] is None
    assert coerced[1]["x"] is None


# ── integer ───────────────────────────────────────────────────────────────────

def test_integer_valid():
    coerced, report = run("integer", ["42", "-7", "0"])
    assert report.passed is True
    assert coerced[0]["x"] == 42
    assert coerced[1]["x"] == -7


def test_integer_rejects_float_string():
    coerced, report = run("integer", ["3.7"])
    assert report.passed is False
    assert coerced[0]["x"] is None
    assert "float" in report.violations[0].message


def test_integer_rejects_text():
    coerced, report = run("integer", ["abc"])
    assert report.passed is False
    assert report.violations[0].rule == "type_check"
    assert report.violations[0].column == "x"
    assert report.violations[0].row == 2  # row_index 0 + 2


def test_integer_empty_becomes_none_no_violation():
    coerced, report = run("integer", [""])
    assert report.passed is True
    assert coerced[0]["x"] is None


def test_integer_whitespace_becomes_none():
    coerced, report = run("integer", ["  "])
    assert report.passed is True
    assert coerced[0]["x"] is None


# ── float ─────────────────────────────────────────────────────────────────────

def test_float_valid():
    coerced, report = run("float", ["3.14", "0", "-1.5", "1e3"])
    assert report.passed is True
    assert coerced[0]["x"] == pytest.approx(3.14)
    assert coerced[3]["x"] == pytest.approx(1000.0)


def test_float_rejects_text():
    coerced, report = run("float", ["abc"])
    assert report.passed is False


def test_float_rejects_nan():
    coerced, report = run("float", ["nan"])
    assert report.passed is False
    assert "finite" in report.violations[0].message


def test_float_rejects_inf():
    coerced, report = run("float", ["inf"])
    assert report.passed is False


def test_float_rejects_negative_inf():
    coerced, report = run("float", ["-inf"])
    assert report.passed is False


# ── boolean ───────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("val", ["true", "True", "TRUE", "1", "yes", "YES", "t"])
def test_boolean_truthy_values(val):
    coerced, report = run("boolean", [val])
    assert report.passed is True
    assert coerced[0]["x"] is True


@pytest.mark.parametrize("val", ["false", "False", "FALSE", "0", "no", "NO", "f"])
def test_boolean_falsy_values(val):
    coerced, report = run("boolean", [val])
    assert report.passed is True
    assert coerced[0]["x"] is False


def test_boolean_rejects_unknown():
    coerced, report = run("boolean", ["maybe"])
    assert report.passed is False
    assert "boolean" in report.violations[0].message


def test_boolean_with_whitespace():
    coerced, report = run("boolean", [" true ", " false "])
    assert report.passed is True
    assert coerced[0]["x"] is True
    assert coerced[1]["x"] is False


# ── date ──────────────────────────────────────────────────────────────────────

def test_date_valid_default_format():
    coerced, report = run("date", ["2024-01-15"])
    assert report.passed is True
    assert coerced[0]["x"] == datetime.date(2024, 1, 15)


def test_date_valid_custom_format():
    coerced, report = run("date", ["15/01/2024"], fmt="%d/%m/%Y")
    assert report.passed is True
    assert coerced[0]["x"] == datetime.date(2024, 1, 15)


def test_date_rejects_wrong_format():
    coerced, report = run("date", ["01/15/2024"])  # expects %Y-%m-%d
    assert report.passed is False


def test_date_rejects_text():
    coerced, report = run("date", ["not-a-date"])
    assert report.passed is False


# ── datetime ──────────────────────────────────────────────────────────────────

def test_datetime_valid_default_format():
    coerced, report = run("datetime", ["2024-01-15T10:30:00"])
    assert report.passed is True
    assert coerced[0]["x"] == datetime.datetime(2024, 1, 15, 10, 30, 0)


def test_datetime_valid_custom_format():
    coerced, report = run("datetime", ["2024-01-15 10:30"], fmt="%Y-%m-%d %H:%M")
    assert report.passed is True
    assert coerced[0]["x"] == datetime.datetime(2024, 1, 15, 10, 30)


def test_datetime_rejects_date_only():
    coerced, report = run("datetime", ["2024-01-15"])  # missing time component
    assert report.passed is False


# ── row numbers ───────────────────────────────────────────────────────────────

def test_row_numbers_are_correct():
    contract = make_contract("x", "integer")
    rows = [{"x": "1"}, {"x": "bad"}, {"x": "3"}]
    report = make_report()
    check_types(rows, contract, {"x"}, report)
    assert report.violations[0].row == 3  # row_index=1 -> row 3 (header + 1-based)


# ── columns not in present_columns are passed through ─────────────────────────

def test_non_present_columns_passthrough():
    contract = make_contract("x", "integer")
    rows = [{"x": "1", "y": "hello"}]
    report = make_report()
    coerced = check_types(rows, contract, {"x"}, report)  # "y" not in present
    assert coerced[0]["y"] == "hello"  # unchanged raw string
