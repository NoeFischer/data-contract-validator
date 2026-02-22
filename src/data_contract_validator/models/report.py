from __future__ import annotations

from pydantic import BaseModel, Field


class Violation(BaseModel):
    rule: str
    column: str | None = None
    row: int | None = None  # 1-based (accounts for header row)
    message: str


class ValidationReport(BaseModel):
    contract_name: str
    contract_version: str
    data_file: str
    passed: bool = True
    total_rows: int = 0
    violations: list[Violation] = Field(default_factory=list)

    def add_violation(self, violation: Violation) -> None:
        self.violations.append(violation)
        self.passed = False
