# CLI Reference

The `validate-contract` command validates a CSV file against a YAML data contract.

## Usage

```bash
validate-contract -c CONTRACT -d DATA [-o OUTPUT]
```

## Options

| Flag                   | Short | Required | Description                          |
|------------------------|-------|----------|--------------------------------------|
| `--contract PATH`      | `-c`  | Yes      | Path to the YAML contract file       |
| `--data PATH`          | `-d`  | Yes      | Path to the CSV data file            |
| `--output PATH`        | `-o`  | No       | Path to write a JSON report          |
| `--version`            |       | No       | Show version and exit                |
| `--help`               |       | No       | Show help and exit                   |

## Exit codes

| Code | Meaning                              |
|------|--------------------------------------|
| `0`  | Validation passed — no violations    |
| `1`  | Validation failed — violations found |
| `2`  | Bad contract or file path            |

## JSON output

The `-o` flag writes a JSON report with the same information as the terminal output:

```json
{
  "contract_name": "customers",
  "contract_version": "1.0.0",
  "data_file": "data/customers.csv",
  "passed": false,
  "total_rows": 12,
  "violations": [
    {
      "rule": "type_check",
      "column": "age",
      "row": 12,
      "message": "Column 'age' row 12: cannot coerce 'not-a-number' to integer."
    }
  ]
}
```

This format is suitable for CI pipelines, dashboards, or downstream processing.

## Examples

```bash
# Basic validation
validate-contract -c contracts/customers_v1.yaml -d data/customers.csv

# With JSON report
validate-contract -c contracts/customers_v1.yaml -d data/customers.csv -o report.json

# Use in CI (non-zero exit on failure)
validate-contract -c contract.yaml -d data.csv || exit 1
```
