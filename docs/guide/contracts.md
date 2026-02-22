# Contract Format

Contracts are YAML files with two required sections: `contract` (metadata) and `schema` (column definitions).

## Full example

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

## Contract metadata

| Field         | Required | Description               |
|---------------|----------|---------------------------|
| `name`        | Yes      | Name of the dataset       |
| `version`     | Yes      | Semantic version string   |
| `description` | No       | Free-text description     |
| `owner`       | No       | Team or individual owner  |

## Supported types

| Type       | Accepts                                                    | Rejects           |
|------------|------------------------------------------------------------|--------------------|
| `string`   | Any value                                                  | —                  |
| `integer`  | `"42"`, `"-7"`                                             | `"3.7"`, `"abc"`   |
| `float`    | `"3.14"`, `"42"`                                           | `"abc"`, `"nan"`, `"inf"` |
| `boolean`  | `true/false`, `1/0`, `yes/no`, `t/f` (case-insensitive)   | `"maybe"`          |
| `date`     | Matches `format` (default `%Y-%m-%d`)                      | Wrong format       |
| `datetime` | Matches `format` (default `%Y-%m-%dT%H:%M:%S`)            | Wrong format       |

Empty cells are always treated as null regardless of type. Use `required: true` to disallow them.

## Constraints

| Constraint       | Description                                |
|------------------|--------------------------------------------|
| `required: true` | Column cannot be empty or missing          |
| `unique: true`   | All non-empty values must be distinct      |
| `enum: [a, b]`   | Value must be one of the listed strings (string columns only) |

## Validation order

1. **Schema check** — are all declared columns present in the CSV?
2. **Type check** — can each cell's raw string be converted to the declared type?
3. **Constraint check** — do values satisfy `required`, `enum`, and `unique` rules?

All violations are collected before reporting — the validator never stops at the first error.
