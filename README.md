# data-contract-validator

Validate CSV files against a declarative YAML data contract. Define what your data should look like — the validator tells you exactly where it doesn't.

```
╭────────────────────────── Data Contract Validation ──────────────────────────╮
│ Contract:  customers v1.0.0                                                  │
│ Data file: data/customers_sample.csv                                         │
│ Rows:      12                                                                │
│ Status:    FAILED                                                            │
╰──────────────────────────────────────────────────────────────────────────────╯
                                 3 violation(s)
╭────────────┬─────────────┬─────┬─────────────────────────────────────────────╮
│ Rule       │ Column      │ Row │ Message                                     │
├────────────┼─────────────┼─────┼─────────────────────────────────────────────┤
│ type_check │ age         │  12 │ Column 'age' row 12: cannot coerce          │
│            │             │     │ 'not-a-number' to integer.                  │
├────────────┼─────────────┼─────┼─────────────────────────────────────────────┤
│ unique     │ customer_id │  13 │ Column 'customer_id' row 13: 'c001' is a    │
│            │             │     │ duplicate (first seen at row 2).            │
├────────────┼─────────────┼─────┼─────────────────────────────────────────────┤
│ enum       │ tier        │  13 │ Column 'tier' row 13: 'vip' is not in       │
│            │             │     │ allowed values ['free', 'starter', ...].    │
╰────────────┴─────────────┴─────┴─────────────────────────────────────────────╯
```

## Installation

Requires Python 3.11+. Using [uv](https://github.com/astral-sh/uv):

```bash
git clone https://github.com/NoeFischer/data-contract-validator.git
cd data-contract-validator
uv venv && uv pip install -e .
```

## Usage

```bash
# Validate a CSV against a contract
validate-contract --contract contracts/customers_v1.yaml --data data/customers.csv

# Short flags
validate-contract -c contracts/customers_v1.yaml -d data/customers.csv

# Also write a JSON report
validate-contract -c contracts/customers_v1.yaml -d data/customers.csv -o report.json
```

**Exit codes:** `0` = passed, `1` = validation failed, `2` = bad contract or file path.

The JSON report has the same structure as the terminal output and is suitable for use in CI pipelines.

## Writing a Contract

Contracts are YAML files with two required sections: `contract` (metadata) and `schema` (column definitions).

```yaml
contract:
  name: my-dataset
  version: "1.0.0"
  description: Optional description.
  owner: team@example.com

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
        required: true
        enum: [active, inactive, pending]

    - name: age
      type: integer
      constraints:
        required: false

    - name: score
      type: float

    - name: is_verified
      type: boolean

    - name: created_on
      type: date
      format: "%Y-%m-%d"

    - name: updated_at
      type: datetime
      format: "%Y-%m-%dT%H:%M:%S"
```

### Supported Types

| Type | Accepts | Rejects |
|------|---------|---------|
| `string` | any value | — |
| `integer` | `"42"`, `"-7"` | `"3.7"`, `"abc"` |
| `float` | `"3.14"`, `"42"` | `"abc"` |
| `boolean` | `true/false`, `1/0`, `yes/no`, `t/f` (case-insensitive) | `"maybe"` |
| `date` | matches `format` (default `%Y-%m-%d`) | wrong format, non-dates |
| `datetime` | matches `format` (default `%Y-%m-%dT%H:%M:%S`) | wrong format, non-datetimes |

Empty cells are always treated as null regardless of type. Use `required: true` to disallow them.

### Constraint Rules

| Constraint | Description |
|------------|-------------|
| `required: true` | Column cannot be empty or missing |
| `unique: true` | All non-empty values must be distinct |
| `enum: [a, b, c]` | Value must be one of the listed strings |

### How Validation Works

1. **Schema check** — are all declared columns present in the CSV?
2. **Type check** — can each cell's raw string be converted to the declared type?
3. **Constraint check** — do values satisfy `required`, `enum`, and `unique` rules?

All violations are collected before reporting — the validator never stops at the first error.

## Development

```bash
# Install with dev dependencies
uv pip install -e ".[dev]"

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=src/data_contract_validator --cov-report=term-missing

# Lint
uv run ruff check src/ tests/
```

## Example

A complete example contract and sample data are included:

```bash
validate-contract -c contracts/customers_v1.yaml -d data/customers_sample.csv
```

The sample data contains 10 valid rows and 2 deliberate failures to demonstrate all violation types.
