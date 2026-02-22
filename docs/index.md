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

## Features

- **Declarative contracts** — define expected schema, types, and constraints in YAML
- **Comprehensive validation** — schema presence, type coercion, and constraint checks
- **All violations reported** — never stops at the first error
- **Clean output** — Rich-powered terminal tables and machine-readable JSON reports
- **CI-friendly** — exit codes (`0` pass, `1` fail, `2` bad input) and JSON output for pipelines

## Quick Example

```bash
# Install
git clone https://github.com/NoeFischer/data-contract-validator.git
cd data-contract-validator
uv venv && uv pip install -e .

# Run
validate-contract -c contracts/customers_v1.yaml -d data/customers_sample.csv
```

See [Getting Started](getting-started/installation.md) for full setup instructions.
