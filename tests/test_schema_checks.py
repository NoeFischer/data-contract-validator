from data_contract_validator.checks.schema_checks import check_schema_presence
from data_contract_validator.models.contract import DataContract
from data_contract_validator.models.report import ValidationReport


def make_contract(column_names: list[str]) -> DataContract:
    return DataContract.model_validate({
        "contract": {"name": "test", "version": "1.0"},
        "schema": {"columns": [{"name": n, "type": "string"} for n in column_names]},
    })


def make_report() -> ValidationReport:
    return ValidationReport(contract_name="test", contract_version="1.0", data_file="f.csv")


def test_all_columns_present():
    contract = make_contract(["id", "name"])
    report = make_report()
    present = check_schema_presence(["id", "name"], contract, report)
    assert present == {"id", "name"}
    assert report.passed is True
    assert report.violations == []


def test_missing_column_adds_violation():
    contract = make_contract(["id", "name", "email"])
    report = make_report()
    present = check_schema_presence(["id", "name"], contract, report)
    assert present == {"id", "name"}
    assert report.passed is False
    assert len(report.violations) == 1
    assert report.violations[0].column == "email"
    assert report.violations[0].rule == "schema_presence"


def test_multiple_missing_columns():
    contract = make_contract(["id", "name", "email", "age"])
    report = make_report()
    present = check_schema_presence(["id"], contract, report)
    assert present == {"id"}
    assert len(report.violations) == 3


def test_extra_csv_columns_are_ignored():
    contract = make_contract(["id"])
    report = make_report()
    present = check_schema_presence(["id", "extra_col"], contract, report)
    assert present == {"id"}
    assert report.passed is True


def test_empty_fieldnames_all_columns_missing():
    contract = make_contract(["id", "name"])
    report = make_report()
    present = check_schema_presence([], contract, report)
    assert present == set()
    assert len(report.violations) == 2


def test_header_only_csv_columns_detected():
    """A CSV with headers but no data rows should still detect column presence."""
    contract = make_contract(["id", "name"])
    report = make_report()
    present = check_schema_presence(["id", "name"], contract, report)
    assert present == {"id", "name"}
    assert report.passed is True


def test_extra_and_missing_simultaneously():
    contract = make_contract(["id", "email"])
    report = make_report()
    present = check_schema_presence(["id", "extra"], contract, report)
    assert present == {"id"}
    assert report.passed is False
    assert len(report.violations) == 1
    assert report.violations[0].column == "email"
