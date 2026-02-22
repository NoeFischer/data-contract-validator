"""Load data contracts (YAML) and CSV data files.

This module provides two loaders:

- ``load_contract`` — parse and validate a YAML contract into a
  ``DataContract`` model.
- ``load_csv`` — read a CSV file as raw strings, returning fieldnames
  and rows separately.
"""

from __future__ import annotations

import csv
from pathlib import Path

import yaml
from pydantic import ValidationError

from data_contract_validator.models.contract import DataContract


class ContractLoadError(Exception):
    """Raised when a contract file cannot be loaded or fails validation."""


class DataLoadError(Exception):
    """Raised when a CSV file cannot be read."""


def load_contract(contract_path: str | Path) -> DataContract:
    """Parse a YAML contract file and return a validated ``DataContract``.

    Args:
        contract_path: Path to the YAML contract file.

    Returns:
        A validated ``DataContract`` instance.

    Raises:
        ContractLoadError: If the file is missing, is not valid YAML,
            or does not conform to the contract schema.
    """
    path = Path(contract_path)
    if not path.exists():
        raise ContractLoadError(f"Contract file not found: {path}")

    try:
        with path.open("r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        raise ContractLoadError(f"YAML parse error in {path}: {exc}") from exc

    if not isinstance(raw, dict):
        raise ContractLoadError(f"Contract must be a YAML mapping, got: {type(raw).__name__}")

    try:
        return DataContract.model_validate(raw)
    except ValidationError as exc:
        raise ContractLoadError(f"Contract schema invalid:\n{exc}") from exc


def load_csv(data_path: str | Path) -> tuple[list[str], list[dict[str, str]]]:
    """Load a CSV file and return ``(fieldnames, rows)``.

    Uses ``utf-8-sig`` encoding to transparently handle the optional
    BOM (byte order mark) inserted by Excel exports.  All cell values
    are returned as raw strings; empty trailing cells become ``""``.

    Args:
        data_path: Path to the CSV file.

    Returns:
        A tuple of ``(fieldnames, rows)`` where *fieldnames* is the
        list of column headers and *rows* is a list of dicts mapping
        column name to raw string value.

    Raises:
        DataLoadError: If the file is missing or cannot be read.
    """
    path = Path(data_path)
    if not path.exists():
        raise DataLoadError(f"Data file not found: {path}")

    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            fieldnames = list(reader.fieldnames) if reader.fieldnames else []
            # Replace None values (empty trailing cells) with empty string
            rows = [
                {k: (v if v is not None else "") for k, v in row.items()}
                for row in reader
            ]
            return fieldnames, rows
    except OSError as exc:
        raise DataLoadError(f"Failed to read CSV {path}: {exc}") from exc
