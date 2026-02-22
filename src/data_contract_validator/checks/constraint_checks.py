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
    """Apply required, enum, and unique constraints to coerced values."""
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
