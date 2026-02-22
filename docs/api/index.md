# API Overview

The `data_contract_validator` package is organized into four layers:

```
┌─────────────┐
│   loader    │  Load contract (YAML) and data (CSV)
├─────────────┤
│  validator  │  Orchestrate the three-stage validation pipeline
├─────────────┤
│   checks/   │  Individual check implementations
│  ├ schema   │    Column presence
│  ├ types    │    Type coercion
│  └ constr.  │    Required, enum, unique
├─────────────┤
│  reporter   │  Terminal output (Rich) and JSON export
└─────────────┘
```

## Data flow

1. [`loader.load_contract()`](loader.md) parses YAML into a [`DataContract`](models/contract.md) model
2. [`loader.load_csv()`](loader.md) reads the CSV as raw strings
3. [`validator.validate()`](validator.md) runs all checks and returns a [`ValidationReport`](models/report.md)
4. [`reporter.print_report()`](reporter.md) renders the report to the terminal
5. [`reporter.export_json()`](reporter.md) optionally writes the report as JSON

## Models

- [`data_contract_validator.models.contract`](models/contract.md) — Pydantic models for the YAML contract
- [`data_contract_validator.models.report`](models/report.md) — Violation and report models

## Checks

- [`schema_checks`](checks/schema_checks.md) — Verify declared columns exist in the CSV
- [`type_checks`](checks/type_checks.md) — Coerce raw strings to declared types
- [`constraint_checks`](checks/constraint_checks.md) — Apply required, enum, and unique rules
