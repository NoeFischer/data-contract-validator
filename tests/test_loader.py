import textwrap
from pathlib import Path

import pytest

from data_contract_validator.loader import (
    ContractLoadError,
    DataLoadError,
    load_contract,
    load_csv,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

MINIMAL_CONTRACT = textwrap.dedent("""\
    contract:
      name: test
      version: "1.0.0"
    schema:
      columns:
        - name: id
          type: string
""")


def write_file(tmp_path: Path, filename: str, content: str | bytes, mode: str = "w") -> Path:
    p = tmp_path / filename
    if isinstance(content, bytes):
        p.write_bytes(content)
    else:
        p.write_text(content, encoding="utf-8")
    return p


# ── load_contract ─────────────────────────────────────────────────────────────

def test_load_contract_valid(tmp_path):
    p = write_file(tmp_path, "contract.yaml", MINIMAL_CONTRACT)
    contract = load_contract(p)
    assert contract.contract.name == "test"
    assert contract.contract.version == "1.0.0"
    assert contract.schema_.columns[0].name == "id"


def test_load_contract_file_not_found():
    with pytest.raises(ContractLoadError, match="not found"):
        load_contract("/nonexistent/path/contract.yaml")


def test_load_contract_invalid_yaml(tmp_path):
    p = write_file(tmp_path, "bad.yaml", "key: [unclosed bracket")
    with pytest.raises(ContractLoadError, match="YAML parse error"):
        load_contract(p)


def test_load_contract_not_a_mapping(tmp_path):
    p = write_file(tmp_path, "list.yaml", "- item1\n- item2\n")
    with pytest.raises(ContractLoadError, match="must be a YAML mapping"):
        load_contract(p)


def test_load_contract_missing_required_field(tmp_path):
    content = textwrap.dedent("""\
        contract:
          name: test
        schema:
          columns:
            - name: id
              type: string
    """)
    p = write_file(tmp_path, "contract.yaml", content)
    with pytest.raises(ContractLoadError, match="Contract schema invalid"):
        load_contract(p)


def test_load_contract_invalid_column_type(tmp_path):
    content = textwrap.dedent("""\
        contract:
          name: test
          version: "1.0.0"
        schema:
          columns:
            - name: id
              type: uuid
    """)
    p = write_file(tmp_path, "contract.yaml", content)
    with pytest.raises(ContractLoadError, match="Contract schema invalid"):
        load_contract(p)


def test_load_contract_duplicate_columns(tmp_path):
    content = textwrap.dedent("""\
        contract:
          name: test
          version: "1.0.0"
        schema:
          columns:
            - name: id
              type: string
            - name: id
              type: integer
    """)
    p = write_file(tmp_path, "contract.yaml", content)
    with pytest.raises(ContractLoadError, match="Contract schema invalid"):
        load_contract(p)


# ── load_csv ──────────────────────────────────────────────────────────────────

def test_load_csv_valid(tmp_path):
    p = write_file(tmp_path, "data.csv", "id,name\n1,Alice\n2,Bob\n")
    fieldnames, rows = load_csv(p)
    assert fieldnames == ["id", "name"]
    assert len(rows) == 2
    assert rows[0] == {"id": "1", "name": "Alice"}
    assert rows[1] == {"id": "2", "name": "Bob"}


def test_load_csv_all_values_are_strings(tmp_path):
    p = write_file(tmp_path, "data.csv", "count,price,active\n42,3.14,true\n")
    _, rows = load_csv(p)
    assert rows[0]["count"] == "42"
    assert rows[0]["price"] == "3.14"
    assert rows[0]["active"] == "true"


def test_load_csv_empty_cells_are_empty_string(tmp_path):
    p = write_file(tmp_path, "data.csv", "id,name\n1,\n2,Bob\n")
    _, rows = load_csv(p)
    assert rows[0]["name"] == ""


def test_load_csv_file_not_found():
    with pytest.raises(DataLoadError, match="not found"):
        load_csv("/nonexistent/path/data.csv")


def test_load_csv_empty_file(tmp_path):
    p = write_file(tmp_path, "empty.csv", "")
    fieldnames, rows = load_csv(p)
    assert fieldnames == []
    assert rows == []


def test_load_csv_header_only(tmp_path):
    p = write_file(tmp_path, "header.csv", "id,name\n")
    fieldnames, rows = load_csv(p)
    assert fieldnames == ["id", "name"]
    assert rows == []


def test_load_csv_bom_encoded(tmp_path):
    bom_content = b"\xef\xbb\xbfid,name\n1,Alice\n"
    p = write_file(tmp_path, "bom.csv", bom_content)
    fieldnames, rows = load_csv(p)
    assert fieldnames == ["id", "name"]  # no BOM prefix
    assert rows[0] == {"id": "1", "name": "Alice"}
