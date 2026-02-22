"""Orchestrate the three-stage validation pipeline.

The ``validate`` function runs schema presence checks, type coercion,
and constraint checks in sequence, collecting all violations into a
single ``ValidationReport``.
"""

from __future__ import annotations

from data_contract_validator.checks.constraint_checks import check_constraints
from data_contract_validator.checks.schema_checks import check_schema_presence
from data_contract_validator.checks.type_checks import check_types
from data_contract_validator.models.contract import DataContract
from data_contract_validator.models.report import ValidationReport


def validate(
    contract: DataContract,
    fieldnames: list[str],
    rows: list[dict[str, str]],
    data_file: str,
) -> ValidationReport:
    """Validate CSV data against a data contract.

    Runs three stages in order:

    1. **Schema presence** — every column declared in the contract must
       exist in the CSV headers.
    2. **Type coercion** — every cell is coerced from its raw string to
       the declared type.
    3. **Constraint checks** — ``required``, ``enum``, and ``unique``
       rules are applied to coerced values.

    Args:
        contract: The parsed data contract.
        fieldnames: Column headers from the CSV file.
        rows: List of row dicts (column name to raw string value).
        data_file: Path string for display in the report.

    Returns:
        A ``ValidationReport`` with all violations collected.
    """
    report = ValidationReport(
        contract_name=contract.contract.name,
        contract_version=contract.contract.version,
        data_file=data_file,
        total_rows=len(rows),
    )

    # 1. Check all declared columns are present
    present_columns = check_schema_presence(fieldnames, contract, report)

    # 2. Coerce raw strings to declared types
    coerced_rows = check_types(rows, contract, present_columns, report)

    # 3. Apply constraints on coerced values
    check_constraints(coerced_rows, contract, present_columns, report)

    return report
