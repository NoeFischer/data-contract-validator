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


def load_csv(data_path: str | Path) -> list[dict[str, str]]:
    path = Path(data_path)
    if not path.exists():
        raise DataLoadError(f"Data file not found: {path}")

    try:
        with path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                return []
            # Replace None values (empty trailing cells) with empty string
            return [
                {k: (v if v is not None else "") for k, v in row.items()}
                for row in reader
            ]
    except OSError as exc:
        raise DataLoadError(f"Failed to read CSV {path}: {exc}") from exc
