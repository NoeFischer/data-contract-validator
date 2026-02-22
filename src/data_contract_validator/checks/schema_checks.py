from __future__ import annotations

from data_contract_validator.models.contract import DataContract
from data_contract_validator.models.report import ValidationReport, Violation


def check_schema_presence(
    fieldnames: list[str],
    contract: DataContract,
    report: ValidationReport,
) -> set[str]:
    """
    Check that all columns declared in the contract exist in the CSV.

    Returns the set of declared column names that are present in the data
    so downstream checks can skip missing columns gracefully.
    """
    csv_columns = set(fieldnames)
    contract_columns = set(contract.column_map.keys())

    missing = contract_columns - csv_columns
    for col in sorted(missing):
        report.add_violation(Violation(
            rule="schema_presence",
            column=col,
            message=f"Column '{col}' is declared in the contract but missing from the CSV.",
        ))

    return contract_columns & csv_columns
