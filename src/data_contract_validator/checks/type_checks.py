"""Type coercion checks.

Every cell in the CSV is read as a raw string.  This module attempts to
coerce each value to the type declared in the contract (integer, float,
boolean, date, datetime).  String columns pass through without coercion.

Cells that cannot be coerced are recorded as violations and replaced
with ``None`` so that downstream constraint checks can still run.
"""

from __future__ import annotations

import datetime
import math
from typing import Any

from data_contract_validator.models.contract import ColumnDefinition, DataContract
from data_contract_validator.models.report import ValidationReport, Violation

BOOLEAN_TRUE = {"true", "1", "yes", "t"}
"""Accepted truthy string representations (case-insensitive)."""

BOOLEAN_FALSE = {"false", "0", "no", "f"}
"""Accepted falsy string representations (case-insensitive)."""


def _coerce(value: str, col_def: ColumnDefinition) -> tuple[Any, str | None]:
    """Attempt to coerce a raw string value to the declared column type.

    Args:
        value: The raw cell value from the CSV.
        col_def: Column definition with the target type and optional format.

    Returns:
        A ``(coerced_value, error_message)`` tuple.  On success the error
        is ``None``; on failure the coerced value is ``None``.  Empty or
        whitespace-only strings are treated as null — ``(None, None)``.
    """
    if value == "" or value.strip() == "":
        return None, None

    col_type = col_def.type
    value = value.strip()

    try:
        if col_type == "string":
            return value, None

        if col_type == "integer":
            if "." in value:
                raise ValueError(f"'{value}' looks like a float, not an integer")
            return int(value), None

        if col_type == "float":
            result = float(value)
            if math.isnan(result) or math.isinf(result):
                raise ValueError(f"'{value}' is not a finite number")
            return result, None

        if col_type == "boolean":
            lower = value.lower()
            if lower in BOOLEAN_TRUE:
                return True, None
            if lower in BOOLEAN_FALSE:
                return False, None
            raise ValueError(
                f"'{value}' is not a recognised boolean "
                f"(accepted: true/false, 1/0, yes/no, t/f)"
            )

        if col_type == "date":
            fmt = col_def.format or "%Y-%m-%d"
            return datetime.datetime.strptime(value, fmt).date(), None

        if col_type == "datetime":
            fmt = col_def.format or "%Y-%m-%dT%H:%M:%S"
            return datetime.datetime.strptime(value, fmt), None

    except (ValueError, TypeError) as exc:
        return None, str(exc)

    return None, f"Unsupported type '{col_type}'"  # unreachable, but safe


def check_types(
    rows: list[dict[str, str]],
    contract: DataContract,
    present_columns: set[str],
    report: ValidationReport,
) -> list[dict[str, Any]]:
    """Coerce every cell to its declared type.

    Args:
        rows: Raw CSV rows (column name to string value).
        contract: The parsed data contract.
        present_columns: Column names confirmed present in the CSV.
        report: Report to append violations to.

    Returns:
        A parallel list of dicts with typed values.  Cells that fail
        coercion become ``None`` and a violation is recorded.
    """
    coerced_rows: list[dict[str, Any]] = []

    for row_index, raw_row in enumerate(rows):
        row_num = row_index + 2  # 1-based + header row
        coerced: dict[str, Any] = {}

        for col_name, raw_value in raw_row.items():
            if col_name not in present_columns:
                coerced[col_name] = raw_value
                continue

            col_def = contract.column_map[col_name]

            # string columns need no coercion — skip to avoid noise
            if col_def.type == "string":
                coerced[col_name] = raw_value if raw_value.strip() != "" else None
                continue

            typed_value, error = _coerce(raw_value, col_def)
            if error is not None:
                report.add_violation(Violation(
                    rule="type_check",
                    column=col_name,
                    row=row_num,
                    message=(
                        f"Column '{col_name}' row {row_num}: "
                        f"cannot coerce '{raw_value}' to {col_def.type}. {error}"
                    ),
                ))
                coerced[col_name] = None
            else:
                coerced[col_name] = typed_value

        coerced_rows.append(coerced)

    return coerced_rows
