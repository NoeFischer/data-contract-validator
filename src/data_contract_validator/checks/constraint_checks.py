"""Constraint checks: required, enum, and unique.

These checks run on coerced (typed) values after type checking has
completed.  Null values (``None``) are skipped by ``enum`` and
``unique`` — use ``required`` to disallow nulls.
"""

from __future__ import annotations

from typing import Any

from data_contract_validator.models.contract import DataContract
from data_contract_validator.models.report import ValidationReport, Violation


def check_constraints(
    coerced_rows: list[dict[str, Any]],
    contract: DataContract,
    present_columns: set[str],
    report: ValidationReport,
) -> None:
    """Apply constraint rules to all columns that are present in the CSV.

    Iterates over each column defined in the contract and runs whichever
    constraints are configured (``required``, ``enum``, ``unique``).

    Args:
        coerced_rows: Rows with values already coerced to their declared types.
        contract: The parsed data contract.
        present_columns: Column names confirmed present in the CSV.
        report: Report to append violations to.
    """
    for col_def in contract.schema_.columns:
        if col_def.name not in present_columns:
            continue

        c = col_def.constraints
        values = [row[col_def.name] for row in coerced_rows]

        if c.required:
            _check_required(col_def.name, values, report)

        if c.enum is not None:
            _check_enum(col_def.name, values, c.enum, report)

        if c.unique:
            _check_unique(col_def.name, values, report)


def _check_required(
    col: str,
    values: list[Any],
    report: ValidationReport,
) -> None:
    """Flag rows where a required column is null.

    Args:
        col: Column name.
        values: Coerced values for every row in this column.
        report: Report to append violations to.
    """
    for row_index, value in enumerate(values):
        row_num = row_index + 2
        if value is None:
            report.add_violation(Violation(
                rule="required",
                column=col,
                row=row_num,
                message=f"Column '{col}' is required but is empty at row {row_num}.",
            ))


def _check_enum(
    col: str,
    values: list[Any],
    allowed: list[str],
    report: ValidationReport,
) -> None:
    """Flag rows where a value is not in the allowed set.

    Null values are skipped — use ``required`` to catch those.

    Args:
        col: Column name.
        values: Coerced values for every row in this column.
        allowed: List of permitted string values.
        report: Report to append violations to.
    """
    allowed_set = set(allowed)
    for row_index, value in enumerate(values):
        if value is None:
            continue  # nulls are handled by required check
        row_num = row_index + 2
        if value not in allowed_set:
            report.add_violation(Violation(
                rule="enum",
                column=col,
                row=row_num,
                message=(
                    f"Column '{col}' row {row_num}: '{value}' is not in "
                    f"allowed values {allowed}."
                ),
            ))


def _check_unique(
    col: str,
    values: list[Any],
    report: ValidationReport,
) -> None:
    """Flag rows where a value duplicates an earlier row.

    Null values are not subject to uniqueness checks.

    Args:
        col: Column name.
        values: Coerced values for every row in this column.
        report: Report to append violations to.
    """
    seen: dict[Any, int] = {}  # value -> first row number it appeared
    for row_index, value in enumerate(values):
        if value is None:
            continue  # nulls are not subject to uniqueness
        row_num = row_index + 2
        if value in seen:
            report.add_violation(Violation(
                rule="unique",
                column=col,
                row=row_num,
                message=(
                    f"Column '{col}' row {row_num}: '{value}' is a duplicate "
                    f"(first seen at row {seen[value]})."
                ),
            ))
        else:
            seen[value] = row_num
