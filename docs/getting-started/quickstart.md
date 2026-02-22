# Quickstart

This guide walks through validating a CSV file against a data contract.

## 1. Write a contract

Create a YAML file describing your expected data format:

```yaml
contract:
  name: my-dataset
  version: "1.0.0"
  description: Sample data contract.

schema:
  columns:
    - name: id
      type: string
      constraints:
        required: true
        unique: true

    - name: status
      type: string
      constraints:
        enum: [active, inactive]

    - name: age
      type: integer
```

## 2. Run the validator

```bash
validate-contract -c contract.yaml -d data.csv
```

The validator runs three stages:

1. **Schema check** — are all declared columns present in the CSV?
2. **Type check** — can each cell be coerced to its declared type?
3. **Constraint check** — do values satisfy `required`, `enum`, and `unique` rules?

All violations are collected before reporting — you see every problem in one pass.

## 3. Read the output

The terminal shows a summary panel and a violation table (if any). Use the `-o` flag to also write a JSON report:

```bash
validate-contract -c contract.yaml -d data.csv -o report.json
```

## Exit codes

| Code | Meaning |
|------|---------|
| `0`  | Validation passed |
| `1`  | Validation failed (violations found) |
| `2`  | Bad contract or file path |

## Try the included example

```bash
validate-contract -c contracts/customers_v1.yaml -d data/customers_sample.csv
```

The sample data includes deliberate failures to demonstrate all violation types.
