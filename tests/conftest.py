from __future__ import annotations

from pathlib import Path

import pytest

from data_contract_validator.models.contract import DataContract
from data_contract_validator.models.report import ValidationReport


@pytest.fixture()
def make_report():
    def _make(**kwargs) -> ValidationReport:
        defaults = {
            "contract_name": "test",
            "contract_version": "1.0",
            "data_file": "f.csv",
        }
        defaults.update(kwargs)
        return ValidationReport(**defaults)
    return _make


@pytest.fixture()
def make_contract():
    def _make(columns: list[dict] | None = None, **kwargs) -> DataContract:
        if columns is None:
            columns = [{"name": "id", "type": "string"}]
        data = {
            "contract": {"name": "test", "version": "1.0.0", **kwargs},
            "schema": {"columns": columns},
        }
        return DataContract.model_validate(data)
    return _make


@pytest.fixture()
def write_file(tmp_path):
    def _write(filename: str, content: str) -> Path:
        p = tmp_path / filename
        p.write_text(content, encoding="utf-8")
        return p
    return _write
