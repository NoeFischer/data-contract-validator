import json
import textwrap
from pathlib import Path

from click.testing import CliRunner

from data_contract_validator.cli import main


VALID_CONTRACT = textwrap.dedent("""\
    contract:
      name: customers
      version: "1.0.0"
    schema:
      columns:
        - name: id
          type: string
          constraints:
            required: true
            unique: true
        - name: age
          type: integer
        - name: tier
          type: string
          constraints:
            enum: [free, pro]
""")

VALID_CSV = "id,age,tier\nabc,30,free\ndef,25,pro\n"
INVALID_CSV = "id,age,tier\nabc,not-a-number,free\nabc,25,vip\n"  # type error + enum + unique


def write(tmp_path: Path, name: str, content: str) -> str:
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return str(p)


# ── Exit codes ────────────────────────────────────────────────────────────────

def test_exit_0_on_pass(tmp_path):
    runner = CliRunner()
    contract_path = write(tmp_path, "contract.yaml", VALID_CONTRACT)
    data_path = write(tmp_path, "data.csv", VALID_CSV)
    result = runner.invoke(main, ["-c", contract_path, "-d", data_path])
    assert result.exit_code == 0


def test_exit_1_on_validation_failure(tmp_path):
    runner = CliRunner()
    contract_path = write(tmp_path, "contract.yaml", VALID_CONTRACT)
    data_path = write(tmp_path, "data.csv", INVALID_CSV)
    result = runner.invoke(main, ["-c", contract_path, "-d", data_path])
    assert result.exit_code == 1


def test_exit_2_on_missing_contract(tmp_path):
    runner = CliRunner()
    data_path = write(tmp_path, "data.csv", VALID_CSV)
    result = runner.invoke(main, ["-c", "/no/such/file.yaml", "-d", data_path])
    assert result.exit_code == 2
    assert "Error loading contract" in result.output


def test_exit_2_on_missing_data(tmp_path):
    runner = CliRunner()
    contract_path = write(tmp_path, "contract.yaml", VALID_CONTRACT)
    result = runner.invoke(main, ["-c", contract_path, "-d", "/no/such/data.csv"])
    assert result.exit_code == 2
    assert "Error loading data" in result.output


def test_exit_2_on_bad_contract_yaml(tmp_path):
    runner = CliRunner()
    contract_path = write(tmp_path, "contract.yaml", "key: [unclosed")
    data_path = write(tmp_path, "data.csv", VALID_CSV)
    result = runner.invoke(main, ["-c", contract_path, "-d", data_path])
    assert result.exit_code == 2
    assert "Error loading contract" in result.output


# ── Output content ────────────────────────────────────────────────────────────

def test_pass_output_contains_passed(tmp_path):
    runner = CliRunner()
    contract_path = write(tmp_path, "contract.yaml", VALID_CONTRACT)
    data_path = write(tmp_path, "data.csv", VALID_CSV)
    result = runner.invoke(main, ["-c", contract_path, "-d", data_path])
    assert "PASSED" in result.output


def test_fail_output_contains_failed(tmp_path):
    runner = CliRunner()
    contract_path = write(tmp_path, "contract.yaml", VALID_CONTRACT)
    data_path = write(tmp_path, "data.csv", INVALID_CSV)
    result = runner.invoke(main, ["-c", contract_path, "-d", data_path])
    assert "FAILED" in result.output


def test_fail_output_contains_violation_rules(tmp_path):
    runner = CliRunner()
    contract_path = write(tmp_path, "contract.yaml", VALID_CONTRACT)
    data_path = write(tmp_path, "data.csv", INVALID_CSV)
    result = runner.invoke(main, ["-c", contract_path, "-d", data_path])
    assert "type_check" in result.output
    assert "enum" in result.output
    assert "unique" in result.output


# ── JSON output ───────────────────────────────────────────────────────────────

def test_json_output_written(tmp_path):
    runner = CliRunner()
    contract_path = write(tmp_path, "contract.yaml", VALID_CONTRACT)
    data_path = write(tmp_path, "data.csv", VALID_CSV)
    output_path = str(tmp_path / "report.json")
    result = runner.invoke(main, ["-c", contract_path, "-d", data_path, "-o", output_path])
    assert result.exit_code == 0
    assert Path(output_path).exists()
    report = json.loads(Path(output_path).read_text())
    assert report["passed"] is True
    assert report["contract_name"] == "customers"


def test_json_output_contains_violations(tmp_path):
    runner = CliRunner()
    contract_path = write(tmp_path, "contract.yaml", VALID_CONTRACT)
    data_path = write(tmp_path, "data.csv", INVALID_CSV)
    output_path = str(tmp_path / "report.json")
    runner.invoke(main, ["-c", contract_path, "-d", data_path, "-o", output_path])
    report = json.loads(Path(output_path).read_text())
    assert report["passed"] is False
    assert len(report["violations"]) > 0


# ── Version flag ──────────────────────────────────────────────────────────────

def test_version_flag():
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


# ── Header-only CSV ──────────────────────────────────────────────────────────

def test_header_only_csv_passes(tmp_path):
    runner = CliRunner()
    contract_path = write(tmp_path, "contract.yaml", VALID_CONTRACT)
    data_path = write(tmp_path, "data.csv", "id,age,tier\n")
    result = runner.invoke(main, ["-c", contract_path, "-d", data_path])
    assert result.exit_code == 0
    assert "PASSED" in result.output
