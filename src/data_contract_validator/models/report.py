"""Models for validation results.

A ``ValidationReport`` accumulates ``Violation`` instances as the
validator runs through schema, type, and constraint checks.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Violation(BaseModel):
    """A single validation violation.

    Attributes:
        rule: Name of the check that failed (e.g. ``"type_check"``).
        column: Column where the violation occurred, if applicable.
        row: 1-based row number (accounting for the header row),
            or ``None`` for column-level violations.
        message: Human-readable description of the problem.
    """

    rule: str
    column: str | None = None
    row: int | None = None  # 1-based (accounts for header row)
    message: str


class ValidationReport(BaseModel):
    """Aggregated result of validating a CSV file against a contract.

    Attributes:
        contract_name: Name from the contract metadata.
        contract_version: Version from the contract metadata.
        data_file: Path to the CSV file that was validated.
        passed: ``True`` if no violations were recorded.
        total_rows: Number of data rows in the CSV (excluding header).
        violations: List of all violations found during validation.
    """

    contract_name: str
    contract_version: str
    data_file: str
    passed: bool = True
    total_rows: int = 0
    violations: list[Violation] = Field(default_factory=list)

    def add_violation(self, violation: Violation) -> None:
        """Record a violation and mark the report as failed.

        Args:
            violation: The violation to append.
        """
        self.violations.append(violation)
        self.passed = False
