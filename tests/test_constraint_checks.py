from data_contract_validator.checks.constraint_checks import (
    _check_enum,
    _check_required,
    _check_unique,
    check_constraints,
)
from data_contract_validator.models.contract import DataContract
from data_contract_validator.models.report import ValidationReport


def make_report() -> ValidationReport:
    return ValidationReport(contract_name="test", contract_version="1.0", data_file="f.csv")


def make_contract(col_name: str, col_type: str = "string", **constraint_kwargs) -> DataContract:
    return DataContract.model_validate({
        "contract": {"name": "test", "version": "1.0"},
        "schema": {"columns": [{
            "name": col_name,
            "type": col_type,
            "constraints": constraint_kwargs,
        }]},
    })


# ── _check_required ───────────────────────────────────────────────────────────

def test_required_passes_when_all_present():
    report = make_report()
    _check_required("id", ["a", "b", "c"], report)
    assert report.passed is True


def test_required_violation_on_none():
    report = make_report()
    _check_required("id", ["a", None, "c"], report)
    assert report.passed is False
    assert report.violations[0].rule == "required"
    assert report.violations[0].column == "id"
    assert report.violations[0].row == 3  # index 1 -> row 3


def test_required_multiple_nones():
    report = make_report()
    _check_required("x", [None, None], report)
    assert len(report.violations) == 2
    assert report.violations[0].row == 2
    assert report.violations[1].row == 3


# ── _check_enum ───────────────────────────────────────────────────────────────

def test_enum_passes_valid_values():
    report = make_report()
    _check_enum("tier", ["free", "pro", "free"], ["free", "pro", "enterprise"], report)
    assert report.passed is True


def test_enum_violation_on_unknown_value():
    report = make_report()
    _check_enum("tier", ["free", "vip"], ["free", "pro"], report)
    assert report.passed is False
    assert report.violations[0].rule == "enum"
    assert report.violations[0].column == "tier"
    assert report.violations[0].row == 3  # index 1 -> row 3
    assert "'vip'" in report.violations[0].message


def test_enum_skips_none_values():
    report = make_report()
    _check_enum("tier", [None, "free"], ["free", "pro"], report)
    assert report.passed is True  # None skipped, "free" is valid


# ── _check_unique ─────────────────────────────────────────────────────────────

def test_unique_passes_all_distinct():
    report = make_report()
    _check_unique("id", ["a", "b", "c"], report)
    assert report.passed is True


def test_unique_violation_on_duplicate():
    report = make_report()
    _check_unique("id", ["a", "b", "a"], report)
    assert report.passed is False
    assert report.violations[0].rule == "unique"
    assert report.violations[0].column == "id"
    assert report.violations[0].row == 4  # index 2 -> row 4
    assert "row 2" in report.violations[0].message  # first seen at row 2


def test_unique_skips_none_values():
    report = make_report()
    _check_unique("id", [None, None, "a"], report)
    assert report.passed is True  # Nones skipped


def test_unique_multiple_duplicates():
    report = make_report()
    _check_unique("id", ["x", "x", "x"], report)
    assert len(report.violations) == 2  # rows 3 and 4 are duplicates of row 2


# ── check_constraints (orchestrator) ─────────────────────────────────────────

def test_check_constraints_required():
    contract = make_contract("id", required=True)
    coerced = [{"id": "1"}, {"id": None}]
    report = make_report()
    check_constraints(coerced, contract, {"id"}, report)
    assert report.passed is False
    assert report.violations[0].rule == "required"


def test_check_constraints_enum():
    contract = make_contract("status", enum=["active", "inactive"])
    coerced = [{"status": "active"}, {"status": "deleted"}]
    report = make_report()
    check_constraints(coerced, contract, {"status"}, report)
    assert report.passed is False
    assert report.violations[0].rule == "enum"


def test_check_constraints_unique():
    contract = make_contract("id", unique=True)
    coerced = [{"id": "1"}, {"id": "1"}]
    report = make_report()
    check_constraints(coerced, contract, {"id"}, report)
    assert report.passed is False
    assert report.violations[0].rule == "unique"


def test_check_constraints_skips_missing_columns():
    contract = make_contract("id", required=True)
    coerced = [{"id": None}]
    report = make_report()
    # "id" not in present_columns — should be skipped entirely
    check_constraints(coerced, contract, set(), report)
    assert report.passed is True


def test_check_constraints_all_pass():
    contract = make_contract("tier", enum=["free", "pro"], unique=False, required=True)
    coerced = [{"tier": "free"}, {"tier": "pro"}]
    report = make_report()
    check_constraints(coerced, contract, {"tier"}, report)
    assert report.passed is True
    assert report.violations == []
