from data_contract_validator.models.contract import DataContract
from data_contract_validator.validator import validate


def make_contract(columns: list[dict]) -> DataContract:
    return DataContract.model_validate({
        "contract": {"name": "test", "version": "1.0"},
        "schema": {"columns": columns},
    })


# ── Happy path ────────────────────────────────────────────────────────────────

def test_valid_data_passes():
    contract = make_contract([
        {"name": "id", "type": "string", "constraints": {"required": True, "unique": True}},
        {"name": "age", "type": "integer"},
        {"name": "score", "type": "float"},
        {"name": "active", "type": "boolean"},
        {"name": "joined", "type": "date"},
        {"name": "updated", "type": "datetime"},
        {"name": "tier", "type": "string", "constraints": {"enum": ["free", "pro"]}},
    ])
    rows = [{
        "id": "abc",
        "age": "30",
        "score": "9.5",
        "active": "true",
        "joined": "2024-01-15",
        "updated": "2024-01-15T10:00:00",
        "tier": "free",
    }]
    report = validate(contract, rows, "data.csv")
    assert report.passed is True
    assert report.violations == []
    assert report.total_rows == 1


# ── Schema violations ─────────────────────────────────────────────────────────

def test_missing_column_fails():
    contract = make_contract([
        {"name": "id", "type": "string"},
        {"name": "missing", "type": "string"},
    ])
    rows = [{"id": "1"}]
    report = validate(contract, rows, "data.csv")
    assert report.passed is False
    rules = [v.rule for v in report.violations]
    assert "schema_presence" in rules


# ── Type violations ───────────────────────────────────────────────────────────

def test_bad_integer_fails():
    contract = make_contract([{"name": "count", "type": "integer"}])
    rows = [{"count": "not-a-number"}]
    report = validate(contract, rows, "data.csv")
    assert report.passed is False
    assert report.violations[0].rule == "type_check"
    assert report.violations[0].row == 2


def test_bad_date_fails():
    contract = make_contract([{"name": "dob", "type": "date"}])
    rows = [{"dob": "15-01-2024"}]  # wrong format
    report = validate(contract, rows, "data.csv")
    assert report.passed is False
    assert report.violations[0].rule == "type_check"


# ── Constraint violations ─────────────────────────────────────────────────────

def test_required_violation():
    contract = make_contract([
        {"name": "id", "type": "string", "constraints": {"required": True}},
    ])
    rows = [{"id": "1"}, {"id": ""}]
    report = validate(contract, rows, "data.csv")
    assert report.passed is False
    assert report.violations[0].rule == "required"
    assert report.violations[0].row == 3


def test_unique_violation():
    contract = make_contract([
        {"name": "id", "type": "string", "constraints": {"unique": True}},
    ])
    rows = [{"id": "abc"}, {"id": "abc"}]
    report = validate(contract, rows, "data.csv")
    assert report.passed is False
    assert report.violations[0].rule == "unique"


def test_enum_violation():
    contract = make_contract([
        {"name": "tier", "type": "string", "constraints": {"enum": ["free", "pro"]}},
    ])
    rows = [{"tier": "enterprise"}]
    report = validate(contract, rows, "data.csv")
    assert report.passed is False
    assert report.violations[0].rule == "enum"


# ── Multiple violations in one run ────────────────────────────────────────────

def test_multiple_violations_collected():
    contract = make_contract([
        {"name": "id", "type": "string", "constraints": {"required": True}},
        {"name": "age", "type": "integer"},
    ])
    rows = [
        {"id": "",    "age": "30"},   # required violation on id
        {"id": "2",   "age": "bad"},  # type violation on age
    ]
    report = validate(contract, rows, "data.csv")
    assert report.passed is False
    rules = {v.rule for v in report.violations}
    assert "required" in rules
    assert "type_check" in rules


# ── Edge cases ────────────────────────────────────────────────────────────────

def test_empty_rows_passes_with_no_required():
    contract = make_contract([{"name": "id", "type": "string"}])
    report = validate(contract, [], "data.csv")
    assert report.total_rows == 0
    # No rows → no type or constraint violations; but schema check fires
    # (empty rows means no columns detected → schema_presence violation)
    assert report.passed is False  # "id" column not detectable from empty rows


def test_null_values_skip_type_check():
    contract = make_contract([{"name": "age", "type": "integer"}])
    rows = [{"age": ""}]  # empty = null, not a type error
    report = validate(contract, rows, "data.csv")
    assert report.passed is True


def test_report_metadata():
    contract = make_contract([{"name": "id", "type": "string"}])
    rows = [{"id": "1"}, {"id": "2"}]
    report = validate(contract, rows, "my_data.csv")
    assert report.contract_name == "test"
    assert report.contract_version == "1.0"
    assert report.data_file == "my_data.csv"
    assert report.total_rows == 2
