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
