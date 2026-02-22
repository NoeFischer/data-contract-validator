import pytest
from pydantic import ValidationError

from data_contract_validator.models.contract import (
    ColumnConstraints,
    ColumnDefinition,
    ContractMetadata,
    DataContract,
    SchemaDefinition,
)
from data_contract_validator.models.report import ValidationReport, Violation


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_contract(**schema_kwargs):
    """Build a minimal valid DataContract."""
    columns = schema_kwargs.pop("columns", [
        {"name": "id", "type": "string"}
    ])
    return DataContract.model_validate({
        "contract": {"name": "test", "version": "1.0.0"},
        "schema": {"columns": columns},
    })


# ── ColumnConstraints ─────────────────────────────────────────────────────────

def test_column_constraints_defaults():
    c = ColumnConstraints()
    assert c.required is False
    assert c.unique is False
    assert c.enum is None


def test_column_constraints_enum():
    c = ColumnConstraints(enum=["a", "b"])
    assert c.enum == ["a", "b"]


# ── ColumnDefinition ──────────────────────────────────────────────────────────

def test_column_definition_valid_types():
    for t in ("string", "integer", "float", "boolean", "date", "datetime"):
        col = ColumnDefinition(name="x", type=t)
        assert col.type == t


def test_column_definition_invalid_type():
    with pytest.raises(ValidationError):
        ColumnDefinition(name="x", type="uuid")


def test_column_definition_format_allowed_on_date():
    col = ColumnDefinition(name="d", type="date", format="%Y-%m-%d")
    assert col.format == "%Y-%m-%d"


def test_column_definition_format_allowed_on_datetime():
    col = ColumnDefinition(name="d", type="datetime", format="%Y-%m-%dT%H:%M:%S")
    assert col.format == "%Y-%m-%dT%H:%M:%S"


def test_column_definition_format_rejected_on_string():
    with pytest.raises(ValidationError, match="'format' is only valid"):
        ColumnDefinition(name="x", type="string", format="%Y-%m-%d")


def test_column_definition_format_rejected_on_integer():
    with pytest.raises(ValidationError, match="'format' is only valid"):
        ColumnDefinition(name="x", type="integer", format="%d")


def test_column_definition_empty_name_rejected():
    with pytest.raises(ValidationError):
        ColumnDefinition(name="", type="string")


def test_column_definition_enum_only_on_string():
    col = ColumnDefinition(
        name="tier", type="string",
        constraints=ColumnConstraints(enum=["a", "b"]),
    )
    assert col.constraints.enum == ["a", "b"]


def test_column_definition_enum_rejected_on_integer():
    with pytest.raises(ValidationError, match="'enum' is only valid"):
        ColumnDefinition(
            name="x", type="integer",
            constraints=ColumnConstraints(enum=["1", "2"]),
        )


def test_column_definition_enum_rejected_on_boolean():
    with pytest.raises(ValidationError, match="'enum' is only valid"):
        ColumnDefinition(
            name="x", type="boolean",
            constraints=ColumnConstraints(enum=["true", "false"]),
        )


# ── SchemaDefinition ──────────────────────────────────────────────────────────

def test_schema_no_duplicate_names():
    with pytest.raises(ValidationError, match="Duplicate column names"):
        SchemaDefinition(columns=[
            ColumnDefinition(name="id", type="string"),
            ColumnDefinition(name="id", type="integer"),
        ])


def test_schema_empty_columns_rejected():
    with pytest.raises(ValidationError):
        SchemaDefinition(columns=[])


# ── ContractMetadata ──────────────────────────────────────────────────────────

def test_empty_version_rejected():
    with pytest.raises(ValidationError):
        ContractMetadata(name="test", version="")


# ── DataContract ──────────────────────────────────────────────────────────────

def test_data_contract_valid():
    contract = make_contract()
    assert contract.contract.name == "test"
    assert contract.contract.version == "1.0.0"
    assert len(contract.schema_.columns) == 1


def test_data_contract_column_map():
    contract = make_contract(columns=[
        {"name": "id", "type": "string"},
        {"name": "age", "type": "integer"},
    ])
    col_map = contract.column_map
    assert "id" in col_map
    assert "age" in col_map
    assert col_map["age"].type == "integer"


def test_data_contract_optional_metadata():
    contract = make_contract()
    assert contract.contract.description is None
    assert contract.contract.owner is None


def test_data_contract_full_metadata():
    contract = DataContract.model_validate({
        "contract": {
            "name": "customers",
            "version": "2.0.0",
            "description": "CRM export",
            "owner": "team@example.com",
        },
        "schema": {"columns": [{"name": "id", "type": "string"}]},
    })
    assert contract.contract.owner == "team@example.com"


# ── ValidationReport ─────────────────────────────────────────────────────────

def test_report_starts_passing():
    r = ValidationReport(
        contract_name="test", contract_version="1.0", data_file="f.csv"
    )
    assert r.passed is True
    assert r.violations == []


def test_report_add_violation_sets_failed():
    r = ValidationReport(
        contract_name="test", contract_version="1.0", data_file="f.csv"
    )
    r.add_violation(Violation(rule="required", column="id", row=2, message="missing"))
    assert r.passed is False
    assert len(r.violations) == 1


def test_violation_fields():
    v = Violation(rule="enum", column="tier", row=5, message="bad value")
    assert v.rule == "enum"
    assert v.column == "tier"
    assert v.row == 5


def test_violation_optional_fields():
    v = Violation(rule="schema", message="column missing")
    assert v.column is None
    assert v.row is None
